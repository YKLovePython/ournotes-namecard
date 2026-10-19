## 名片助手 v1.0.1 —— 第一次，名片可以被复制

**这是《BanG Dream! Our Notes》里第一个能读写名片的工具。**
名片第一次从「游戏里手摆的一张图」变成了**可以复制、粘贴、交换的数据**。

### 这一版是什么

* 直接调用游戏自己的 gRPC 接口读写名片 —— **不模拟点击、不截图、不 OCR**；
* 界面：左边 SET1~SET10，右边该 SET 的 3×3 仓库，和游戏里一一对应；
* 右键格子：编辑编码 / 复制编码 / 删除；
* **分享码**：`OURNOTES-CARD-v1:…` 一行文本，导入后与原名片**逐字节一致**；
* **三个区服自动识别**：港台 / EN / 韩服，谁认这个号就用谁。

### 这一版修掉的

| 问题 | 现象 | 原因 |
| --- | --- | --- |
| 大名片把界面压塌 | 137 个元素的名片让 3×3 仓库整个消失 | 摘要不截断，把 `1fr` 的格子区挤成 0 高 |
| EN / 韩服报「查无此人」 | `PLAYER_NOT_EXISTS`，名字都读出来了却读不到名片 | 服务器地址写死成港台服 |

### 用法

1. 下载下面的 zip，**解压**（里面只有一个 exe）；
2. 手机上打开 **USB 调试**，插线，弹窗勾「始终允许」；
3. **先把游戏完全退出**；
4. 双击 `OurNotes名片助手.exe` → 点右上角 **刷新**；
5. 选 SET → 点方块 → 改/贴编码 → **确认更改** 连点 3 次。

不用装 Python；adb 也打包在里面。别放进 `C:\Program Files`（它会在自己旁边写文件）。

### 校验与时间存证

* 发布包 SHA-256：`094f681f455c3e4a3d9c252d712a358b8e17bbe193ba887745143ba1caf797c7`
* RFC 3161 可信时间戳（FreeTSA）：`proof/OurNotes-Namecard-v1.0.1.zip.tsr`
* 比特币时间戳（OpenTimestamps）：`proof/OurNotes-Namecard-v1.0.1.zip.ots`
* 封存源码包（不公开，只公开哈希）：见 `proof/archive-sha256.txt`
* 独立验证方法：[`proof/README.md`](https://github.com/YKLovePython/ournotes-namecard/blob/main/proof/README.md)

### 说明

2026-10-20 我们检索过，没有找到更早的同类公开工具。这是检索结论。
如果你知道更早的实现，请在 Issues 里给链接，我们会补进「先行工作」。

交流群 **227897560** ｜ B站 **作业快没了**

---

## Namecard v1.0.1 — for the first time, a card can be copied

**The first tool for *BanG Dream! Our Notes* that reads and writes profile cards.**
A card stops being a hand-arranged picture inside the game and becomes **data you
can copy, paste and trade.**

* Talks to the game's own gRPC API — **no taps, no screenshots, no OCR**;
* SET1…SET10 on the left, the 3×3 warehouse of the active SET on the right;
* share code `OURNOTES-CARD-v1:…`, **byte-identical** after import;
* **three regions auto-detected**: TW/HK/MO, EN, Korea.

### Fixed in this build

| Problem | Symptom | Cause |
| --- | --- | --- |
| Large cards collapsed the UI | a 137-element card made the 3×3 warehouse disappear | the summary was not truncated and squeezed the `1fr` grid row to zero |
| EN / Korea reported "no such player" | `PLAYER_NOT_EXISTS` although the name was read fine | the API root was hard-coded to the HK region |

### Usage

1. Download the zip below and extract it (one exe inside).
2. Enable **USB debugging**, connect the phone, accept "always allow".
3. **Quit the game completely.**
4. Double-click `OurNotes名片助手.exe` → press **刷新** (top right).
5. Pick a SET → click a cell → edit or paste a code → confirm **three times**.

No Python needed; adb is bundled. Do not put it in `C:\Program Files`.

### Verification

Release SHA-256:
`094f681f455c3e4a3d9c252d712a358b8e17bbe193ba887745143ba1caf797c7`
(RFC 3161 + Bitcoin timestamp proofs under `proof/`.)

For study and technical research only. Automation may violate the game's terms of
service — use at your own risk, never on your main account.
