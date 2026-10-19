# How it works: reading and writing a profile card without touching the screen

> 中文版见 [how-it-works.zh-CN.md](how-it-works.zh-CN.md)。

This document covers the data model, the protocol, the three regional servers, the
credential extraction, the share-code design — and the mistakes made on the way.
It contains no account data, no credentials and no personal information.

---

## 1. The data model

An account has **10 slots (1..10)** with up to **9 objects each (1..9)**.
Slots can be renamed (the defaults are `Set1`…`Set10`); one of them is the
"active" slot the game displays.

As returned by the server:

```
ProfileCardSlot                     (a repeated field in GetPlayerData)
  1 = slot number    1..10
  2 = slot name      string
  4 = object (repeated)
        1 = index         1..9
        2 = body          the card JSON   ← the content itself
        3 = thumbnail URL a PNG rendered by the server
        4 = display order
```

`body` is a JSON document defined by the game:

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

Two details matter:

* **`contentData` + `meta.masterType/masterId` point at master data, not at
  rendered text.** Every stamp, illustration and background is an entry in the
  game's master data. Sharing a card therefore only needs those IDs — no OCR, no
  font dependency, no simplified/traditional/Japanese ambiguity.
* **An empty object is legal**: `{"items":[]}`. So "is this position occupied"
  must be decided by `items`, not by the object's existence.

Serialising the body with `json.dumps(obj, separators=(",", ":"))` (UTF-8, keep
non-ASCII) reproduces the game's own string **byte for byte**. That is the
round-trip criterion, and the reason an import never leaves the server with
"looks the same but isn't" data.

---

## 2. Transport and authentication

gRPC over HTTP/2 + TLS. No public `.proto`, no reflection, so request bodies are
hand-built protobuf wire format (varint + length-delimited).

| Header | Value | Source |
| --- | --- | --- |
| `x-player-id` | player UUID | save file `_certification._playerId` |
| `x-player-credential` | login key | save file `_certification._authorizationKey` |
| `x-platform` | `android` | constant |
| `x-client-version` | `1.0.6` | constant |
| `x-request-id` | random UUID | per call |

**Do not send `x-device-id`**: a value that does not match the server's record
returns `CONCURRENT_DEVICE` immediately.

Errors arrive in two layers. The gRPC status is usually a generic `UNKNOWN`; the
real reason is in the `x-sirius-error-code` trailer and `details()`:

```
UNKNOWN / TOKEN_ILLEGAL          authentication failed
UNKNOWN / PLAYER_NOT_EXISTS      no such player (wrong region)
UNKNOWN / CONCURRENT_DEVICE      logged in elsewhere / device mismatch
UNAVAILABLE                      HTTP/2 GOAWAY (writing too fast)
```

Those three `UNKNOWN`s need completely different handling. Collapsing them into
one "network error" destroys any chance of debugging.

### Three regional servers

The anonymous `/app.playerlogin.PlayerLoginService/GetServerList` (empty request)
returns:

| Region | areaID | API roots |
| --- | --- | --- |
| TW/HK/MO | 2 | `l12-prod-hk-all-gs-sirius.gamerfusiontech.com` / `l14-…` |
| EN Region | 3 | `l14-prod-va-all-gs-sirius.bilibiligame.net` / `l17-…` |
| Korea | 4 | `l14-prod-kr-all-gs-sirius.bilibiligame.net` / `l17-…` |

The two roots inside a region are equivalent. **Players do not cross regions**:
asking region B about a region-A credential returns `PLAYER_NOT_EXISTS`, not an
authentication error.

So the tool:

1. fetches the server list (falls back to six built-in roots);
2. probes each root once with `GetPlayerData`, and keeps the one that recognises
   the account;
3. caches the choice per `playerId` in `server.json`;
4. re-probes once if a real call still reports `PLAYER_NOT_EXISTS`.

### Where credentials come from

```
/sdcard/Android/data/com.bilibili.sirius.official/files/<64-hex-dir>/
```

The save is **Rijndael-256-CBC + PKCS7** behind a 64-byte custom header, and
usually gzip + JSON after decryption. `_certification` lives in the **settings**
file while `_player._name` / `_player._profileId` live in the **main save**, so
the whole directory has to be scanned — not one file.

**The credential rotates on every game login.** That is the most common source of
errors in this tool, and the reason the *刷新* button does "pull credentials" and
"read the card" in one action.

---

## 3. The calls

| Path | Request | Purpose |
| --- | --- | --- |
| `/app.player.PlayerService/GetPlayerData` | empty | all player state (~63 KB), incl. the card |
| `/app.profilecard.ProfileCardService/SaveProfileCard` | `{1:slot, 2:index, 3:body}` | **write an object** (persisted) |
| `/app.profilecard.ProfileCardService/RemoveProfileCard` | `{1:slot, 2:index}` | delete an object |
| `/app.profilecard.ProfileCardService/EditProfileCardSlot` | `{1:slot, 2:name}` | rename a slot |
| `/app.profilecard.ProfileCardService/SettingProfileCard` | `{1:slot}` | set the active slot |
| `/app.profilecard.ProfileCardService/PutObjects` | `{1:{2:bytes}}` | upload bytes, returns a URL |
| `/app.profilecard.ProfileCardService/UpdateProfileCardDispOrder` | `{1,2}` | stacking order, semantics **unconfirmed** |

On read, the card sits at **top-level field 1 → field 51** (repeated).
The numeric ID shown in the UI is top-level field 6.

Measured behaviour:

* **A write is one atomic call.** Unlike UI automation there is no "dragged
  halfway" state: the server either takes the new body or it does not.
* **`PutObjects` is a single upload slot.** It writes bytes to one fixed location
  and returns `.../profilecard/<id>/_<hash>`; calling it again overwrites. It
  cannot hold several different images.
* **Thumbnails are rendered by the server.** Right after `SaveProfileCard`,
  field 3 briefly points at raw data instead of a PNG; the game client redraws it
  on the next sync/save (observed: the same URL went from 42205 B to 17329 B).
  The body is unaffected.
* **`UpdateProfileCardDispOrder` is not fully mapped.** `(1,1)` succeeds. It only
  affects stacking order, not export/import, so it is left alone.

---

## 4. Share-code design

One requirement: **paste it, get exactly the same card back.**

```
OURNOTES-CARD-v1:<base64url(zlib(utf8(json)))>
```

* the JSON stores `body` as an **object**, not a string, so it is readable and
  editable by hand;
* on import the body is re-serialised compactly — byte-identical to the game's string;
* only master IDs are stored, so the code is independent of language, font and
  resolution;
* `from.name` is the only free text (a player name) and is never written to the card.

A deliberate trade-off: **no thumbnail in the code.** A thumbnail is a *result*
rendered per (player, slot, index); including it would only make the code longer
and it goes stale immediately.

---

## 5. UI architecture

pywebview (WebView2) plus a local HTTP bridge — not Tkinter:

```
┌──────────────────────────────┐
│ pywebview window (WebView2)  │
│   HTML/CSS/JS  ← the UI      │
└──────────────┬───────────────┘
               │ POST /api/invoke
┌──────────────▼───────────────┐
│ ThreadingHTTPServer 127.0.0.1│
│   NamecardApi (plain Python) │
└──────────────┬───────────────┘
               │ gRPC
        ┌──────▼──────┐
        │ game server │
        └─────────────┘
```

Why: the UI can be done properly once in CSS (dark shell, cards, motion), while
the logic stays ordinary Python, and the two sides exchange one JSON action table.
Every action returns `{ok, error?, state?, toast?, effect?}` — `state` redraws the
page, `effect` is a one-shot dialog / context menu / copy / close.

One trap worth recording: **pywebview reflects the public attributes of the
`js_api` object.** A single public attribute holding the Window is enough to make
the reflection recurse forever and freeze the app. All `NamecardApi` attributes
are underscore-prefixed; `JsBridge.invoke` is the only entry point.

---

## 6. Packaging

PyInstaller `--onefile --windowed` → one 36 MB exe.

| Bundled | Why |
| --- | --- |
| Python runtime | no Python needed on the target machine |
| webview + pythonnet + clr_loader | the UI renders through the system WebView2 |
| grpcio | game API |
| numpy + save-decryption library | decrypt the phone save |
| adb.exe + 2 dlls | no separate adb install |
| icons / brand image | window icon + UI logo |

Three required flags for the UI: `--collect-all webview clr_loader pythonnet`,
`--hidden-import clr`, and `--add-data` for the brand image. Miss one and the exe
whitens or reports missing modules.

The cost of `--onefile` is unpacking to `%TEMP%` on every launch (2–5 s the first
time). The exe also writes next to itself (`cred.json`, `server.json`), so it must
not live in a read-only directory such as `C:\Program Files`.

---

## 7. Safety design

* **Three confirmations** before any write in the GUI;
* **CLI is dry-run by default**, `--yes` to actually write;
* **0.8 s between writes** — bursts get GOAWAY'd;
* **read-only self-test** (`--selftest`) checks the environment without writing;
* **credentials never leave the machine** — `cred.json` sits next to the exe and
  is never committed or uploaded.

---

## 8. Mistakes (all real)

**① A brute-force scan wrote 9 garbage objects.**
To confirm field semantics we tried every combination of 10 slots × 11 indices ×
3 fields. It wrote 9 junk objects into every slot. Lesson: writes must be single
and confirmable; probe read-only, or with one clearly-bounded write.

**② A thumbnail URL was written as the body.**
`SaveProfileCard` field 2 is the body and field 3 is the thumbnail — both strings.
The card content became a URL. Lesson: same type does not mean same meaning;
verify by round-trip, not by "it did not error".

**③ A 137-element card collapsed the 3×3 grid.**
A card with 137 items made the summary several thousand characters long; the
layout is `grid-template-rows: auto minmax(0,1fr) auto`, so the hint area grew and
squeezed the grid to **zero height** — the whole warehouse disappeared.
Three layers of defence now: summaries take at most 4 items plus "… (N items)",
the text is hard-clipped at 220 chars, and the hint area gets
`-webkit-line-clamp` while the grid rows have a fixed minimum.

**④ The server root was hard-coded to one region.**
Every EN / Korean account reported "no such player". See section 2.

---

## 9. Verification record

| Item | Result |
| --- | --- |
| Body round-trip (export → import → read back) | **byte-identical** to the original |
| Card capacity | 10 slots × 9 objects; a single object with 137 elements was seen in the wild |
| One player read | ~63 KB |
| Write | one `SaveProfileCard` call, persisted and read back |
| Region probing | the three regions answer differently; the right root is selected |
| Packaged self-test | imports / adb / UI HTML / backend API all OK |
| Release package | single-file exe; the zip contains exactly one entry |
| Data model | matches the field layout of the community's `entity/profilecard.proto` (derived independently) |

Timestamp proof (FreeTSA + Bitcoin): [`../proof/README.md`](../proof/README.md).
