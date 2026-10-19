# 技术细节：怎么在不碰屏幕的情况下读写名片

> English abstract: the profile card is part of the normal `GetPlayerData` payload;
> writing it is five small gRPC calls you can build with a hand-rolled protobuf encoder.
> This document describes the data model, the auth metadata, the three regional servers,
> the credential extraction, the share-code design and the mistakes we made on the way.

本文只讲**原理和设计**，不含账号、凭据或任何个人信息。

---

## 1. 数据模型

一个账号的名片是 **10 个槽位（slot 1..10）**，每个槽位最多 **9 个对象（index 1..9）**。
槽位可以改名（游戏默认 `Set1`…`Set10`），其中之一是「使用中」的展示槽。

对象的结构（读回来时）：

```
ProfileCardSlot                     (GetPlayerData 里的重复字段)
  1 = 槽位号        1..10
  2 = 槽位名        字符串
  4 = 对象（重复）
        1 = 序号          1..9
        2 = body          名片 JSON 字符串   ← 内容本体
        3 = 缩略图 URL    服务器渲染的 PNG
        4 = 显示顺序
```

`body` 是游戏自己定义的一段 JSON：

```json
{"items":[
  {"itemType":"Image",
   "thumbnailAddress":"",
   "contentData":"Stamp/text/stamp_text_001",
   "position":{"x":0.0,"y":0.0},
   "scale":1.0,"scaleY":1.0,"rotation":0.0,
   "siblingIndex":1,"isLocked":false,"isVisible":true,
   "preserveAspectRatio":true,"aspectRatio":0.0,
   "sizeDeltaX":375.0,"sizeDeltaY":300.0,
   "meta":{"masterType":4,"masterId":51}}
]}
```

两个细节值得单独说：

* **`contentData` + `meta.masterType/masterId` 指向资源，不是文字。**
  名片上看到的一切（图章、立绘、背景）都是 master data 里的条目。
  这意味着「分享一张名片」只需要存这些 id，不需要识别画面 ——
  也不会有简繁日文、字体、渲染差异的问题。
* **空对象是合法的**：`{"items":[]}`。所以「这个位置有没有东西」要按
  `items` 是否为空来判断，不能只看对象存不存在。

序列化回去时用 `json.dumps(obj, separators=(",", ":"))`（UTF-8、不转义非 ASCII），
和游戏原始字符串**逐字节相同**。这条是往返测试的判据，也是为什么导入时不会
在服务器上留下「看起来一样但内容不同」的数据。

---

## 2. 传输与鉴权

客户端是 **gRPC over HTTP/2 + TLS**。没有公开的 `.proto`，也没开 reflection，
所以请求体是手写的 protobuf wire format（varint + length-delimited）。

每次调用带这些 metadata：

| 头 | 值 | 来源 |
| --- | --- | --- |
| `x-player-id` | 玩家 UUID | 存档 `_certification._playerId` |
| `x-player-credential` | 登录凭据 | 存档 `_certification._authorizationKey` |
| `x-platform` | `android` | 常量 |
| `x-client-version` | `1.0.6` | 常量 |
| `x-request-id` | 随机 UUID | 每次生成 |

**不要带 `x-device-id`**：值和服务器记录不一致会直接 `CONCURRENT_DEVICE`。

服务器的错误信息分两层：gRPC 的 status 通常是笼统的 `UNKNOWN`，
真正的原因在 trailer `x-sirius-error-code` 和 `details()` 里，例如：

```
UNKNOWN / TOKEN_ILLEGAL          authentication failed
UNKNOWN / PLAYER_NOT_EXISTS      查无此人（区服不对）
UNKNOWN / CONCURRENT_DEVICE      别处登录 / 设备不匹配
UNAVAILABLE                      HTTP/2 被 GOAWAY（写太快）
```

这三个 `UNKNOWN` 的处理方式完全不同 —— 把它们混成一个「网络错误」，
排查会彻底失去方向。

### 三个区服

匿名的 `/app.playerlogin.PlayerLoginService/GetServerList`（空请求）返回：

| 区服 | areaID | API 节点 |
| --- | --- | --- |
| TW/HK/MO | 2 | `l12-prod-hk-all-gs-sirius.gamerfusiontech.com` / `l14-…` |
| EN Region | 3 | `l14-prod-va-all-gs-sirius.bilibiligame.net` / `l17-…` |
| Korea | 4 | `l14-prod-kr-all-gs-sirius.bilibiligame.net` / `l17-…` |

同一区服的两个节点等价。**玩家不跨区**：拿 A 区的凭据问 B 区，
返回的是 `PLAYER_NOT_EXISTS`，而不是鉴权错误。

所以工具的流程是：

1. 拉服务器列表（失败就用内置的 6 个节点）；
2. 挨个用 `GetPlayerData` 试读一次，谁认这个号就用谁；
3. 结果按 `playerId` 写进 `server.json`，下次直接用；
4. 真读到 `PLAYER_NOT_EXISTS` 时，强制重探一次再试。

### 凭据从哪来

设备路径：

```
/sdcard/Android/data/com.bilibili.sirius.official/files/<64 位 hex 目录>/
```

存档是 **Rijndael-256-CBC + PKCS7**，前面 64 字节是自定义头，解密后通常是
gzip JSON。`_certification` 在**设置文件**里，`_player._name` /
`_player._profileId` 在**主存档**里，所以要扫目录下所有文件，不能只读一个。

**凭据每次游戏重新登录都会轮换。** 这是这个工具最常见的报错来源，
也是「刷新」按钮要同时做「拉凭据 + 读名片」两件事的原因。

---

## 3. 读写接口

| 路径 | 请求 | 作用 |
| --- | --- | --- |
| `/app.player.PlayerService/GetPlayerData` | 空 | 全部玩家数据（~63 KB），含名片 |
| `/app.profilecard.ProfileCardService/SaveProfileCard` | `{1:槽, 2:序号, 3:body}` | **写对象内容**（落库） |
| `/app.profilecard.ProfileCardService/RemoveProfileCard` | `{1:槽, 2:序号}` | 删对象 |
| `/app.profilecard.ProfileCardService/EditProfileCardSlot` | `{1:槽, 2:名字}` | 改槽位名 |
| `/app.profilecard.ProfileCardService/SettingProfileCard` | `{1:槽}` | 设为「使用中」 |
| `/app.profilecard.ProfileCardService/PutObjects` | `{1:{2:内容}}` | 上传对象字节，返回 URL |
| `/app.profilecard.ProfileCardService/UpdateProfileCardDispOrder` | `{1,2}` | 叠放顺序，字段语义**未完全确认** |

读的时候，名片在 `GetPlayerData` 的**顶层字段 1 → 字段 51**（重复）。
数字 ID（显示在界面上的那串）是顶层字段 6。

几个实测结论：

* **写入是一次原子调用。** 不像 UI 自动化那样「拖到一半」，服务器要么收下新
  body，要么不收。
* **`PutObjects` 只能当上传位用。** 它往一个固定位置写字节并返回
  `.../profilecard/<id>/_<hash>`；多次调用会互相覆盖，**不能**用来放多张不同的图。
* **缩略图是服务器渲染的。** 用 `SaveProfileCard` 写完后，字段 3 会短暂指向原始
  数据而不是 PNG；游戏客户端下次同步 / 编辑保存时会自动重画成正式缩略图
  （实测同一个 URL 的 PNG 从 42205 B 变成 17329 B）。名片本体不受影响。
* **`UpdateProfileCardDispOrder` 的字段语义没完全确认**，`(1,1)` 能返回成功。
  它只影响多个对象的前后叠放，不影响导出 / 导入，所以先放着。

---

## 4. 分享码的设计

要求只有一句话：**别人贴过来，必须一模一样地还原。**

```
OURNOTES-CARD-v1:<base64url(zlib(utf8(json)))>
```

* JSON 里存 `body` 的**对象**（不是字符串），方便人看懂、手改；
* 导入时重新按紧凑格式序列化，和游戏原串逐字节一致；
* 存的是 master id，所以跟客户端语言、字体、分辨率全都无关；
* 只有 `from.name` 是自由文本（玩家名），它不参与写入。

一个刻意的取舍：**分享码不带缩略图**。缩略图是服务器按
(玩家, 槽位, 序号) 渲染的，属于「结果」而不是「内容」；
带上它只会让码变长，而且随时会过期。

---

## 5. 界面架构

界面是 **pywebview（WebView2）+ 本地 HTTP 桥**，不是 Tkinter：

```
┌──────────────────────────────┐
│ pywebview 窗口 (WebView2)    │
│   HTML/CSS/JS  ← 界面        │
└──────────────┬───────────────┘
               │ POST /api/invoke
┌──────────────▼───────────────┐
│ ThreadingHTTPServer 127.0.0.1│
│   NamecardApi（纯 Python）   │
└──────────────┬───────────────┘
               │ gRPC
        ┌──────▼──────┐
        │ 游戏服务器  │
        └─────────────┘
```

为什么这么做：界面可以用 CSS 一次做到位（深色外壳、卡片、动效），
而业务逻辑仍然是普通的 Python 函数，两边只通过一个 JSON 动作表通信。
每个动作返回 `{ok, error?, state?, toast?, effect?}`：`state` 是整页重绘，
`effect` 是弹窗 / 右键菜单 / 复制 / 关闭等一次性动作。

一个必须记住的坑：**pywebview 会反射 `js_api` 对象的公开属性**。
只要 `NamecardApi` 上有一个公开属性持有着 Window，反射就会无限递归、界面卡死。
所以它的属性全部以下划线开头，只留一个 `JsBridge.invoke` 作为入口。

---

## 6. 打包

PyInstaller `--onefile --windowed`，产出一个 36 MB 的 exe：

| 随包带的东西 | 为什么 |
| --- | --- |
| Python 运行时 | 用户不用装 Python |
| webview + pythonnet + clr_loader | 界面靠系统的 WebView2 |
| grpcio | 调游戏接口 |
| numpy + 存档解密库 | 解手机存档 |
| adb.exe + 2 个 dll | 用户不用自己装 adb |
| 图标 / 品牌图 | 窗口图标 + 界面 logo |

界面相关的三个必要开关：`--collect-all webview clr_loader pythonnet`、
`--hidden-import clr`、`--add-data`（品牌图）。少了任何一个，exe 会白屏或报缺模块。

`--onefile` 的代价是每次启动都要把运行时解到 `%TEMP%`，首次 2~5 秒。
另外，**exe 会在自己旁边写文件**（`cred.json`、`server.json`），
所以不能放进 `C:\Program Files` 这种只读目录。

---

## 7. 安全设计

* **写入前三次确认**：界面里连点 3 次「确定」才会发请求；
* **CLI 默认 dry-run**，`--yes` 才真写；
* **写入限速 0.8 s**：短时间大量写会被服务器 GOAWAY；
* **只读自检**：打包后可以跑 `--selftest`，只检查环境和接口，不写数据；
* **凭据不出本机**：`cred.json` 只在 exe 旁边，不进仓库、不上传。

---

## 8. 踩过的坑（都是真的）

**① 暴力扫描写坏了 9 个对象。**
早期为了确认字段语义，用「10 槽 × 11 序号 × 3 种字段」全排列去试写，
结果往所有槽位塞进了 9 个垃圾对象。教训：**写操作只能单点、可确认**，
探测要用只读接口或者明确的单次写入。

**② 把缩略图 URL 当成 body 写进去。**
`SaveProfileCard` 的字段 2 是 body、字段 3 是缩略图，两者都是字符串。
写错之后名片内容变成一串 URL。教训：**字段类型一样不代表语义一样**，
要用往返比对确认，而不是「能写进去不报错」。

**③ 137 个元素的名片把 3×3 布局压没了。**
群友的名片有 137 个元素，摘要把它们全拼成一行塞进提示区，
而布局是 `grid-template-rows: auto minmax(0,1fr) auto` ——
提示区按内容撑高，格子区被压成 0 高度，整个仓库消失。
现在三层保险：摘要默认只取 4 个元素 +「…（共 N 个元素）」、
文本再硬截 220 字符、提示区加 `-webkit-line-clamp`，格子行高写死最小值。

**④ 把服务器地址写死成一个区服。**
结果是 EN / 韩服的号全部报「查无此人」。教训见第 2 节。

---

## 9. 验证记录

| 项目 | 结果 |
| --- | --- |
| body 往返（导出 → 导入 → 读回） | 与原串**逐字节一致** |
| 名片规模 | 10 槽 × 9 对象，实操中见过单对象 137 个元素 |
| 读一次玩家数据 | ~63 KB |
| 写入 | `SaveProfileCard` 单次调用，实测落库并可读回 |
| 三区服探测 | 三套节点分别返回不同结果，自动选择正确节点 |
| 打包自检 | import / adb / 界面 HTML / 后端 API 全部 OK |
| 发布包 | 单文件 exe，zip 内 1 个条目 |
| 数据模型 | 与社区公开的 `entity/profilecard.proto` 字段布局一致（独立得出） |

时间存证（FreeTSA + 比特币）见 [`../proof/README.md`](../proof/README.md)。
