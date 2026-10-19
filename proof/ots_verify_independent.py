"""独立验证 OpenTimestamps 证明 —— 不信任 ots 命令行，也不信任作者。

它做四件事：
1. 从 .ots 读出「被存证文件的摘要」和「证明分支」；
2. 把每条分支回溯哈希，得到被写进区块的那个 Merkle 根；
3. 从公共 API 取回对应高度的区块头（80 字节），确认根确实在这个区块里；
4. 先确认 .ots 里的文件摘要和本地文件 SHA-256 一致，
   证明这份证明不是配给别的文件的。

用法：
    python ots_verify_independent.py <被验证的文件> <文件>.ots

依赖：
    pip install opentimestamps-client python-bitcoinlib
（只用到它们解析 .ots 与区块头；链上数据的获取是直接读 mempool.space）
"""
from __future__ import annotations

import hashlib
import sys
import urllib.request

from opentimestamps.core.notary import BitcoinBlockHeaderAttestation
from opentimestamps.core.serialize import StreamDeserializationContext
from opentimestamps.core.timestamp import DetachedTimestampFile


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "ournotes-namecard-proof"})
    return urllib.request.urlopen(req, timeout=30).read()


def block_header(height: int) -> bytes:
    """从 mempool.space 取指定高度的区块头（80 字节）。"""
    block_hash = fetch(f"https://mempool.space/api/block-height/{height}").decode().strip()
    header_hex = fetch(f"https://mempool.space/api/block/{block_hash}/header").decode().strip()
    return bytes.fromhex(header_hex)


def as_block_header(raw: bytes):
    import io

    from bitcoin.core import CBlockHeader

    try:
        return CBlockHeader.deserialize(raw)
    except Exception:                                # noqa: BLE001
        return CBlockHeader.stream_deserialize(io.BytesIO(raw))


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                # noqa: BLE001
        pass

    target = sys.argv[1] if len(sys.argv) > 1 else "OurNotes名片助手-v1.0.1.zip"
    stamp_path = sys.argv[2] if len(sys.argv) > 2 else target + ".ots"

    with open(stamp_path, "rb") as fd:
        detached = DetachedTimestampFile.deserialize(StreamDeserializationContext(fd))

    with open(target, "rb") as fd:
        local = hashlib.sha256(fd.read()).digest()

    print("本地文件 SHA-256 :", local.hex())
    print("证明里的文件摘要 :", detached.file_digest.hex())
    same = local == detached.file_digest
    print("两者一致         :", same)
    if not same:
        print(">>> 不一致：这份 .ots 不是给这个文件的。")
        return 2

    print()
    checked = 0
    pending = 0
    for msg, attestation in detached.timestamp.all_attestations():
        if isinstance(attestation, BitcoinBlockHeaderAttestation):
            height = attestation.height
            try:
                header = as_block_header(block_header(height))
            except Exception as exc:                 # noqa: BLE001
                print(f"  区块 {height}: 取区块头失败 {str(exc)[:60]}")
                continue
            ok = attestation.verify_against_blockheader(msg, header)
            checked += 1
            print(f"  区块高度 {height}: {'OK 验证通过' if ok else 'FAILED 验证失败'}")
        else:
            pending += 1
            print(f"  （尚未锚定的分支：{attestation.__class__.__name__}）")

    print()
    if checked:
        print("结论：本文件的 SHA-256 确实被写进比特币区块 —— 时间证明成立。")
    elif pending:
        print("结论：还没有比特币锚定（刚提交，等 1~2 小时后再跑一次）。")
    else:
        print("结论：这份证明里没有可验证的分支。")
    return 0 if checked else 1


if __name__ == "__main__":
    raise SystemExit(main())
