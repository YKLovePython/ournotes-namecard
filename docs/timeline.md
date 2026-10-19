# Timeline

> 中文版见 [timeline.zh-CN.md](timeline.zh-CN.md)。

| Time (UTC+8) | What happened | Evidence |
| --- | --- | --- |
| 2026-10-18 20:40 | First file: hand-rolled protobuf + card model | file mtimes inside the sealed archive |
| 2026-10-18 20:44 | Auth works; first read of the author's own card (`my.bcard.json`) | same |
| 2026-10-18 20:45 | Save decryption → credential extraction works | same |
| 2026-10-18 23:01 | Share code (JSON / single line), round-trip **byte-identical** | same |
| 2026-10-18 23:06 | First UI (Tkinter): SET list left, 3×3 warehouse right | same |
| 2026-10-19 01:15 | Snapshot of the Tkinter version | directory copy |
| 2026-10-19 daytime | UI rewritten in pywebview + local HTTP bridge (shell modelled on *谛听 1.0*) | source mtimes |
| 2026-10-19 15:41 | Reproduced and fixed the "137 elements collapse the 3×3" layout failure | fake-card harness |
| 2026-10-19 16:57 | Single-file exe; **automatic region detection** (EN / Korea previously reported "no such player") | build output |
| 2026-10-20 00:5x | **v1.0.1 sealed**: source archive + release + manifest → FreeTSA + Bitcoin | `proof/` |

## Why the timeline matters

The value here is not the line count:

* before the evening of 2026-10-18, a card in this game could only be arranged by
  hand, in game;
* after 2026-10-18 23:01, it was **a line of text you can copy**;
* after 2026-10-20, that fact can be **verified by anyone** — without trusting
  the author and without trusting GitHub.

## What is inside the sealed archive

`OurNotes-Namecard-v1.0.1-src.zip` (**not published**, only its hash is) holds the
complete source, the reverse-engineering scripts, the documents and the build
scripts of that moment: 106 files. Every zip entry keeps its on-disk modification
time, so the timeline itself is inside the seal.

Its SHA-256 and both timestamps: [`../proof/`](../proof/README.md).
