# Disclaimer

This project is the product of **personal research and learning**: game protocol
analysis, protobuf without a `.proto`, and desktop UI engineering. It is **not
affiliated with the game's publisher or developer** and is not an official tool.

## Risk

* **It changes real account data.** Cards are stored on the server, not locally.
* **Automating a live-service game may violate its terms of service.** We cannot
  promise your account will not be actioned. **Use it on an account you are
  willing to lose.**
* Never use it for ranking, boosting, commercial purposes, or to affect others.
* No warranty of any kind: not against data loss, not against account action, not
  against the server API changing.

## Data and privacy

* The tool talks only to your machine and the game server. **There is no
  third-party server.**
* `cred.json` is a **live credential** (a login key). It stays next to the exe and
  is never uploaded. **Never share it** and never post a screenshot of it.
* This repository collects nothing and contains no telemetry.

## Distribution

* This repository contains documentation, screenshots, timestamp proof and a link
  to the ready-to-run build.
* **The implementation is not here** and is not licensed for redistribution or
  commercial use.
* If you got the tool from somewhere else, check the release SHA-256
  (see [`../proof/archive-sha256.txt`](../proof/archive-sha256.txt)) — a modified
  exe could steal your credential.

## Liability

By using this tool you accept the risks above. The author is not responsible for
account loss, data loss or terms-of-service disputes.

If you disagree with any of the above, do not use it.
