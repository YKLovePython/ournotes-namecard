# 时间存证 / Timestamp proof

**中文** · [English](#english)

> **状态（2026-10-20 01:06 / 01:22 UTC+8）：** RFC 3161 已签发（三份，`granted`；
> 发布包与封存源码包 01:06，清单因为改了发布名在 01:22 重签一次）；
> **比特币已锚定：block 972187（2026-10-19 17:49:13 UTC）**，
> 明细见 [`锚定信息.txt`](锚定信息.txt)。
> 结果汇总：[`存证结果_v1.0.1.txt`](存证结果_v1.0.1.txt)

这个目录是一份**公开的时间承诺**：它证明下面这些东西在 **2026-10-20**
（UTC+8；UTC 2026-10-19 17:06，清单 17:22）**已经存在**，而且此后没有被改过。

| 被存证对象 | 公开吗 | SHA-256 |
| --- | --- | --- |
| `OurNotes-Namecard-v1.0.1.zip`（发布包） | 是，Release 附件 | `094f681f…797c7` |
| `OurNotes-Namecard-v1.0.1-src.zip`（封存源码包） | **否**，只公开哈希 | `6a4f2e76…ca27c` |
| `发布包校验.txt`（把前两个钉在一起的清单） | 是 | `36edfbca…41bcb` |

为什么是三个：发布包是给别人用的，源码包是「我们确实写了这些」的证据，
清单则把两者的哈希绑在同一次签发里，免得有人拿一个旧包配一个新的时间戳。

谁都不需要相信作者，也不需要相信 GitHub —— 只需要相信 TSA 和比特币。

---

## 1. 先验证「文件没被动过」

```powershell
certutil -hashfile OurNotes-Namecard-v1.0.1.zip SHA256
```

去掉空格、转小写后应当等于：

```
094f681f455c3e4a3d9c252d712a358b8e17bbe193ba887745143ba1caf797c7
```

这一步是全部时间证明的前提：时间戳只对**这一串哈希**有效，所以 zip 改一个字节，
整套证明就和它无关了。

## 2. 验证 RFC 3161 时间戳（`.tsr`）

需要 openssl（Windows 上 Git for Windows 自带）：

```powershell
openssl ts -verify -in OurNotes-Namecard-v1.0.1.zip.tsr `
                   -data OurNotes-Namecard-v1.0.1.zip `
                   -CAfile freetsa_cacert.pem -untrusted freetsa_tsa.crt
```

看到 `Verification: OK` 即通过。想看签发时间和哈希：

```powershell
openssl ts -reply -in OurNotes-Namecard-v1.0.1.zip.tsr -text
```

`genTime` 是 **2026-10-19 17:06:14 UTC**（= 2026-10-20 01:06:14 UTC+8），
`Status: Granted`。清单那一份是 **17:22:53 UTC**（01:22:53 UTC+8）。

## 3. 验证比特币时间戳（`.ots`）

三份证明都锚定在 **比特币区块 972187**（区块时间 2026-10-19 17:49:13 UTC）。
只看证明本身，离线就行、也不需要节点：

```powershell
ots info OurNotes-Namecard-v1.0.1.zip.ots     # 文件摘要 + 证明路径 + 区块高度
```

要**重算一遍**，下面两种任选一种：

```powershell
# A. 本地有 Bitcoin Core 节点时（ots verify 会向节点要区块头）
ots verify OurNotes-Namecard-v1.0.1.zip.ots

# B. 没有节点（大多数人）—— 用本目录的脚本，它从 mempool.space 取区块头
python ots_verify_independent.py OurNotes-Namecard-v1.0.1.zip OurNotes-Namecard-v1.0.1.zip.ots
```

完全不想装东西：把 `<文件>` 和 `<文件>.ots` 一起上传到
<https://opentimestamps.org> 在线校验。

脚本做的事：从 `.ots` 读出摘要和证明路径 → 回溯到 Merkle 根 →
从 mempool.space 取对应高度的区块头（80 字节）→ 确认根确实在这个区块里；
并且先核对 `.ots` 里的摘要与本地文件的 SHA-256 一致（证明这份证明不是配别的文件的）。

## 4. 为什么两种都做

| | RFC 3161（FreeTSA） | 比特币（OpenTimestamps） |
| --- | --- | --- |
| 性质 | 权威机构签发，带 CA 链 | 去中心化，写进比特币区块 |
| 出证速度 | 秒级 | 1~2 小时（等区块） |
| 能被撤回吗 | 理论上依赖 TSA 的存续 | 不能 —— 只要比特币还在 |

两者互相独立：任何一方被质疑，另一方仍然成立。

---

## English

This folder is a **public time commitment**. It proves that the files below
existed on **2026-10-20 01:06 UTC+8** (2026-10-19 17:06 UTC) and have not changed
since.

| Object | Published | SHA-256 |
| --- | --- | --- |
| `OurNotes-Namecard-v1.0.1.zip` (release) | yes — Release asset | `094f681f…797c7` |
| `OurNotes-Namecard-v1.0.1-src.zip` (sealed source) | **no** — hash only | `6a4f2e76…ca27c` |
| `发布包校验.txt` (manifest binding the two) | yes | `36edfbca…41bcb` |

Three objects on purpose: the release is what people use, the source archive is
the evidence that the work was actually written, and the manifest binds both
hashes into the same signing event so a new proof cannot be paired with an old
build.

### Verify

```bash
# 1. the file itself
sha256sum OurNotes-Namecard-v1.0.1.zip

# 2. the TSA token
openssl ts -verify -in OurNotes-Namecard-v1.0.1.zip.tsr \
                   -data OurNotes-Namecard-v1.0.1.zip \
                   -CAfile freetsa_cacert.pem -untrusted freetsa_tsa.crt

# 3. Bitcoin — anchored in block 972187 (2026-10-19 17:49:13 UTC)
ots info OurNotes-Namecard-v1.0.1.zip.ots      # offline: digest, path, block height
ots verify OurNotes-Namecard-v1.0.1.zip.ots    # needs a LOCAL Bitcoin Core node
python ots_verify_independent.py OurNotes-Namecard-v1.0.1.zip OurNotes-Namecard-v1.0.1.zip.ots
```

`ots verify` asks a local Bitcoin Core node for the block header; without one it
stops with `Could not connect to Bitcoin node`. The small script in this folder
does the same arithmetic over a public API (mempool.space) — that is what we ran,
and it printed `区块高度 972187: OK 验证通过`. Uploading both files to
<https://opentimestamps.org> is the no-install route.

**What this proves:** the work existed on that date.
**What it does not prove:** that nobody did it earlier. See the README's
"prior art" section — we state what we searched, and when.
