# 时间存证 / Timestamp proof

**中文** · [English](#english)

> **状态（2026-10-20 01:06 / 01:22 UTC+8）：** RFC 3161 已签发（三份，`granted`；
> 发布包与封存源码包 01:06，清单因为改了发布名在 01:22 重签一次）；
> **比特币已锚定（block 972187）**，明细见 [`锚定信息.txt`](锚定信息.txt)。
> 复核时在 `proof/` 目录执行
> `ots upgrade OurNotes-Namecard-v1.0.1.zip` 即可把它升级成「已锚定」。
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

```powershell
ots upgrade OurNotes-Namecard-v1.0.1.zip   # 等 1~2 小时后，把「待确认」升级为「已锚定」
ots verify  OurNotes-Namecard-v1.0.1.zip   # 打印区块高度与区块时间
ots info    OurNotes-Namecard-v1.0.1.zip.ots
```

不想装工具：把文件与 `.ots` 一起上传到 <https://opentimestamps.org> 在线校验。

也可以完全不信这两个工具，自己从区块头验：

```powershell
python ots_verify_independent.py OurNotes-Namecard-v1.0.1.zip OurNotes-Namecard-v1.0.1.zip.ots
```

它会从 mempool.space 取区块头，在本地重算 Merkle 路径，打印
「本文件的 SHA-256 确实被写进了这个区块」。

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

# 3. Bitcoin (after ~1-2 hours, once the block is mined)
ots upgrade OurNotes-Namecard-v1.0.1.zip
ots verify  OurNotes-Namecard-v1.0.1.zip
```

`Verification: OK` and a block height are the whole answer. No trust in the
author and no trust in GitHub is required — only in the TSA and in Bitcoin.

**What this proves:** the work existed on that date.
**What it does not prove:** that nobody did it earlier. See the README's
"prior art" section — we state what we searched, and when.
