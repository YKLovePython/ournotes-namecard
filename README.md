# BanG Dream! Our Notes — Namecard Export / Import

> **The first tool that edits this game's profile card by speaking the game's own protocol.**
> No taps, no screenshots, no OCR, no emulator.

[中文说明](README.zh-CN.md) · [How it works](docs/how-it-works.md) · [FAQ](docs/faq.md) · [Disclaimer](docs/disclaimer.md)

![Our Notes 名片助手](media/01_ui.png)

> **v1.0.1 — 2026-10-20.** Windows 10/11 x64 + an Android phone over USB.
> One 36 MB exe, nothing to install, no Python.
> → **[Download](https://github.com/YKLovePython/ournotes-namecard/releases/latest)**

---

## A first for this game — dated, sealed and timestamped

**2026-10-20.** As of this date we could not find any public tool for
*BanG Dream! Our Notes* that can read or write a profile card
(プロフィールカード). The public projects around this title are save-file
decryptors, API proxies, master-data dumps, fan databases and autoplay tools —
none of them touches the card.

What did not exist before this project:

| | Before | Here |
| --- | --- | --- |
| Editing a card | by hand, in game | **read / write through the game's own gRPC API** |
| Moving a card between accounts | retype every stamp by hand | **paste one line of text** |
| A card "share code" | — | `OURNOTES-CARD-v1:…`, round-trips **byte-identically** |
| Reaching other regions | — | auto-detects TW/HK/MO, EN, Korea |
| The write path, documented | — | [`docs/how-it-works.md`](docs/how-it-works.md) |

For the community this turns a card from **a screenshot into data**: it can be
copied, shared, re-arranged, archived and diffed. A card is no longer stuck on
the account that made it — which is exactly what a player-to-player card system
is supposed to be good for, and what the in-game UI never allowed.

**Two separate claims, kept separate:**

1. **The date.** On 2026-10-20 the sealed source archive and this release build
   were committed to **Bitcoin (OpenTimestamps)** and signed by **FreeTSA
   (RFC 3161)**. That proves the work existed on that date — see [`proof/`](proof/README.md).
2. **The novelty.** We searched on that date and found nothing comparable. That
   is a statement about our search, not a mathematical proof — if you know of an
   earlier tool, we want the link.

---

## What it does

An account holds **10 card slots × 9 card objects = 90 card objects**. The tool
shows them the way the game does:

* **left** — SET1…SET10, click to switch;
* **right** — the 3×3 warehouse of the selected SET;
* number = an existing card object, **＋** = an empty position;
* click a number to edit its **share code**, right-click for
  edit / copy / delete;
* **刷新** = pull fresh credentials from the phone (if USB is connected) and
  read the card back.

Every write is gated by **three separate confirmations**, and the CLI has
`--dry-run`. Nothing is ever written while reading.

### Share code

A card object is a JSON string. The share code is the same JSON, optionally
compressed to one line:

```
OURNOTES-CARD-v1:<base64url(zlib(json))>
```

```
{
  "format": "ournotes-namecard", "version": 1,
  "from": { "name": "示例玩家", "id": 10000000000, "exportedAt": "2026-10-18T20:44:58" },
  "slots": [ { "slot": 1, "name": "Set1", "objects": [
      { "index": 1, "body": { "items": [
          { "itemType": "Image",
            "contentData": "Stamp/text/stamp_text_001",
            "meta": { "masterType": 4, "masterId": 51 },
            "position": { "x": 0.0, "y": 0.0 },
            "scale": 1.0, "scaleY": 1.0, "rotation": 0.0,
            "siblingIndex": 1, "isLocked": false, "isVisible": true,
            "preserveAspectRatio": true, "aspectRatio": 0.0,
            "sizeDeltaX": 375.0, "sizeDeltaY": 300.0 } ] } } ] } ]
}
```

The important design choice: **a code stores master IDs, not rendered text**.
No OCR, no simplified/traditional/Japanese ambiguity, no font dependence. Only
the player name is free text. Serialising the body back with
`json.dumps(separators=(",", ":"))` reproduces the game's own string
**byte for byte** (verified by round-trip).

---

## Requirements

| | |
| --- | --- |
| OS | Windows 10 / 11 x64 (WebView2, which Edge installs) |
| Phone | Android, **USB debugging** on, connected by cable |
| Game | *BanG Dream! Our Notes* — TW/HK/MO, EN or Korea |

macOS, Linux and iOS are **not supported** and have not been tested.

## Usage

1. Download the zip from [Releases](https://github.com/YKLovePython/ournotes-namecard/releases/latest)
   and extract it — you get **one file**, `OurNotes名片助手.exe`.
   Do not put it in `C:\Program Files` (it writes next to itself).
2. Close the game on the phone.
3. Connect the phone, accept the USB-debugging prompt ("always allow").
4. Double-click the exe → **刷新** (top right). First launch takes 2–5 s.
5. Pick a SET on the left, click a card to edit, **确认更改** ×3 to write.

## Verify the download

```powershell
certutil -hashfile OurNotes-Namecard-v1.0.1.zip SHA256
```

must equal

```
094f681f455c3e4a3d9c252d712a358b8e17bbe193ba887745143ba1caf797c7
```

and then check the timestamps — [`proof/README.md`](proof/README.md).

---

## Why it needed reverse engineering

The game client is gRPC over HTTP/2. There is no public API and no reflection.
The interesting parts:

**1. The card is already part of the player payload.**
`GetPlayerData` returns ~63 KB of player state; field 51 holds the card slots.
So reading is a single authenticated call — no scraping, no screen capture.

**2. Writing is five small RPCs, not UI automation.**
`SaveProfileCard`, `RemoveProfileCard`, `EditProfileCardSlot`,
`SettingProfileCard`, `PutObjects`. The payload is a hand-built protobuf
(`{1: slot, 2: index, 3: body}` for a save). Because the write is a single
server call, it is atomic from the game's point of view: the card either has the
new body or it does not.

**3. Credentials live in the phone's save file and rotate.**
The tool pulls the save over adb, decrypts it (Rijndael-256-CBC + PKCS7 behind a
64-byte custom header, then gzip + JSON) and takes
`_certification._playerId` / `_certification._authorizationKey`. The game
re-issues that key on every login, so the tool re-pulls it on **刷新**.
A rotated key is the single most common error (`TOKEN_ILLEGAL`).

**4. Three regions, and they do not share players.**
`GetServerList` (anonymous) lists TW/HK/MO, EN and Korea with different API
roots. Asking the wrong region returns **`PLAYER_NOT_EXISTS`** — which looks
like "your credentials are broken" but is not. The tool probes each region once,
remembers the answer per account, and re-probes automatically if a call still
says the player does not exist.

Details, including the data model and the exact field layout:
[`docs/how-it-works.md`](docs/how-it-works.md).

---

## Timestamp proof

| What | Where |
| --- | --- |
| RFC 3161 token (FreeTSA) | `proof/OurNotes-Namecard-v1.0.1.zip.tsr` |
| Bitcoin attestation (OpenTimestamps) | `proof/OurNotes-Namecard-v1.0.1.zip.ots` |
| Sealed source archive (not published, hash only) | `proof/archive-sha256.txt` |
| Verification steps | [`proof/README.md`](proof/README.md) |

Two independent authorities: a CA-backed TSA that answers in seconds, and
Bitcoin, which nobody can retract. Either one alone is enough. Neither requires
trusting the author or GitHub.

---

## Prior art

We looked before writing, and we looked again on 2026-10-20. Public work on
*Our Notes*:

| Project | What it is | Reads / writes a card? |
| --- | --- | --- |
| `MetaSekaiLab/nnnotes` | save decryption + master data tools | no |
| `Srirus-Project/sirius-api-proxy` | unofficial API proxy (Rust); ships `entity/profilecard.proto` — the card **schema** — but registers only announcement / event / friend / livemusic / masterdata / player services | **no** (schema only) |
| `bandori-sirius/master-db-en` / `-kr` | master database dumps | no |
| `AwadoriProj/private-notes`, `aircookieee/Cone` | private server / RE tooling | no |
| `elfi00zt/OurNotesDataBase`, `leonorexyz/OurNotes` | fan databases and guides | no |
| chart databases, autoplay projects | charts and playing | no |
| **this project** | read / write cards, share codes, region auto-detection | **yes** |

Search log — GitHub repository search on **2026-10-20**, every query returned **0**:

```
ournotes namecard        → 0        bandori namecard        → 0
ournotes profilecard     → 0        "profile card" bandori  → 0
"our notes" namecard     → 0        sirius namecard         → 0
```

**Credit where it is due.** The `entity/profilecard.proto` in
`sirius-api-proxy` independently documents exactly the field layout this tool
reverse-engineered (`slot=1, name=2, is_setting=3, profile_objects=4`;
`index=1, profile_object_json=2, thumbnail_url=3, disp_order=4`). Two
independent derivations agreeing is a good sign for both — and it is the reason
the claim here is about a **tool**, not about the schema.

If something earlier exists that actually moves cards between players, tell us
and we will link it.

---

## Safety

* The tool only touches **your own** account, and only after three confirmations.
* Writing is rate-limited (0.8 s between writes) because the server drops
  connections (GOAWAY) on bursts.
* Do not run the game and the tool at the same time — the sessions can evict each other.
* After an import the card's thumbnail URL briefly points at the raw data; the
  game redraws the PNG the next time the client syncs or saves. The card body
  itself is unaffected.
* Credentials never leave the machine; `cred.json` sits next to the exe and is
  git-ignored. **Do not share it** — it is a live account key.

## Author & community

* **作业快没了** on Bilibili
* QQ group **227897560** — questions, bug reports, card exchange
* Report issues: [Issues](https://github.com/YKLovePython/ournotes-namecard/issues)

## Credits

`nnnotes` (MetaSekaiLab) does the save decryption; `pywebview` + WebView2 render
the interface. The visual shell is modelled on our other tool, *谛听 1.0*.

---

## Disclaimer

Published for **research and learning** — game protocol analysis, protobuf
without a schema, and desktop UI engineering. Not affiliated with the publisher.

This tool changes real account data. Automating a live-service game may violate
its terms of service. Use it on an account you are willing to lose, never for
ranking, never commercially. See [`docs/disclaimer.md`](docs/disclaimer.md).

## License

Documentation, text and screenshots: **CC BY-NC-SA 4.0**.
The implementation is **not** included in this repository and is not licensed
for redistribution. This repository contains documentation and the ready-to-run
build only.

---

<details>
<summary>Keywords / 搜索关键词</summary>

BanG Dream Our Notes namecard · バンドリ プロフィールカード · 名片 导出 导入 ·
个人名片 分享码 · 名片助手 · Our Notes 名片工具 · profile card export import ·
profile card share code · game protocol reverse engineering · gRPC protobuf
without schema · BanG Dream Our Notes tool · 音游 名片 交换 ·
namecard editor · Android save decryption · 10 slots 9 objects

</details>
