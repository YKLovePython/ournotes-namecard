# FAQ

> 中文版见 [faq.zh-CN.md](faq.zh-CN.md)。

## Will I get banned?

**We do not know, and we cannot promise anything.** The tool does exactly what the
game client does: authenticated calls to the game's own API. No modified client,
no injection, no simulated taps. But "automation / third-party tools" may still
violate the terms of service. **Use it on an account you are willing to lose**,
never for ranking, never commercially.

## Do I need root?

No. No emulator, no Xposed, no accessibility service. Only USB debugging.

## Do I have to press *刷新* every time?

Yes, after every game login: the game re-issues the credential on each login. The
button first pulls the new credential from the phone, then reads the card. It also
works without a phone connected — it then uses the existing `cred.json`.

## "TOKEN_ILLEGAL" / credentials expired

The game logged in again and the old `_authorizationKey` is dead. Connect the
phone, check USB debugging, press *刷新*. The credential is refreshed automatically.

## "PLAYER_NOT_EXISTS" / no such player

Not a credential problem — the **wrong region**. The tool probes all three regions
(TW/HK/MO, EN, Korea), keeps the one that recognises the account and remembers it.
If none of them do, send the log to the group: a new node is missing.

## "CONCURRENT_DEVICE" / the session drops

The game and the tool fight over the session. **Fully quit the game** before using
the tool.

## The thumbnail looks wrong / blank after an import

Normal. Thumbnails are rendered by the server; it is redrawn when the game client
next syncs or saves. The card body itself is correct from the moment it is written.

## iOS / emulator / other regions?

**Windows + a real Android phone only.** iOS and emulators are untested.
All three regions are supported (auto-detected).

## Is my card uploaded anywhere?

No. The tool talks only to your PC and the game server; there is no third-party
service. `cred.json` is the **key to your account** — it lives next to the exe and
must never be shared.

## Why only an exe, no source code?

This repository carries documentation, timestamp proof and the ready-to-run build.
The implementation is not published and is not licensed for redistribution. The
build is complete — nothing has to be compiled.

## Can I import a whole SET at once?

The GUI handles one object at a time on purpose (it prevents accidents). The CLI
supports whole-slot / multi-slot imports but is not part of the release package;
ask in the group if you need it.

## Why does the UI look like another tool?

The shell (dark theme, brand card, motion) comes from our other tool *谛听 1.0*;
the structure (SET list on the left, 3×3 warehouse on the right) is what the
namecard tool has always looked like.
