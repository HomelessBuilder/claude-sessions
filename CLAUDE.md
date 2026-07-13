# claude-sessions — Project Manager Context

## Role of This Claude Instance

This Claude Code instance is the **project manager** for everything inside
`~/claude-sessions/`. It builds and maintains the terminal-capture-and-reader
tool described below, and hands off session summaries to the journal
(`~/claude-journal-private`) same as any other project instance. It does not
take direction from the overseer beyond what's recorded here and in
`~/CLAUDE.md`'s Active Projects entry — day-to-day build decisions belong to
this instance.

## What This Project Is

Raw terminal-session capture for Diego's ecosystem, with a **readable
transcript viewer** as the deliverable — not a session *replay* tool. The
distinction matters: the goal is a browsable, review-able record of what
happened in a closed terminal session (grep it, read it, feed it into the
journal/content pipeline), not a faithful re-enactment of the session's
pacing.

This was scoped out in an overseer conversation on 2026-07-11 (full reasoning
in `VISION.md`) that compared two capture approaches and two output tiers
before landing here. Read `VISION.md` before writing any code — it has the
tradeoffs already worked out so they don't need re-litigating.

## Design Decisions Already Made

- **Capture mechanism:** `script -t` (util-linux, already installed) run
  automatically for every interactive shell via a `.bashrc` wrapper. Produces
  a raw typescript file plus a timing file. No custom capture code needed —
  this part is off-the-shelf.
- **Reader, not player:** `scriptreplay` already gives faithful replay for
  free if that's ever wanted later, so there's no need to build toward that.
  The thing worth building is the opposite: a clean static transcript.
- **Rendering approach:** naive ANSI-stripping (regex) breaks on anything
  that redraws in place (`top`, progress bars, `less`, tab-completion
  menus) — it produces garbled duplicate lines, not a clean read. The
  chosen approach is running the raw byte stream through **`pyte`** (a
  pure-Python terminal emulator library) so cursor movement and screen
  redraws are resolved the way a real terminal would resolve them, then
  dumping the resulting screen buffer as the readable transcript.

## Decisions Made Since Founding

- **Snapshot granularity: final screen state only, resolved 2026-07-12.**
  Built `reader/render.py`, wired `capture/bashrc-snippet.sh` into
  `~/.bashrc`, and reviewed a real captured session with Diego. Final-state
  rendering (200 cols wide, dump `pyte.Screen.display` after feeding the
  whole typescript) looked right to him — no per-command or interval
  snapshotting needed for v1.
- Capture is **live**: every new interactive shell opened after 2026-07-12
  is wrapped in `script -T`. Raw pairs land in `raw/` (gitignored).

## Open Questions (still unresolved)

- Where captures live long-term and how/when they get pruned (raw
  typescripts could get large).
- Whether this feeds `claude-journal-private` / `devlog-engine` directly or
  stays a standalone viewer for now.

## Tech Stack

- **Capture:** `script` / `scriptreplay` (util-linux, already present)
- **Reader:** Python + `pyte` (needs adding — venv + requirements.txt, don't
  install system-wide)

## Project Structure (Target — adjust as the build clarifies)

```
claude-sessions/
├── CLAUDE.md              ← this file
├── VISION.md              ← full design discussion and rationale
├── capture/
│   └── bashrc-snippet.sh  ← the .bashrc wrapper that starts `script -t` per shell
├── raw/                   ← raw typescript + timing file pairs (gitignored — this is session content, not source)
├── reader/
│   └── render.py          ← pyte-based script: raw capture -> readable transcript
└── .gitignore             ← must exclude raw/ (terminal captures can contain anything typed, including secrets)
```

## Standing Rules

- No file deletions without explicit instruction from Diego.
- No permanent changes (commits, pushes, installs) without confirmation.
- Advise first — surface options and tradeoffs before acting.
- **Raw captures can contain secrets** (passwords typed at prompts, API
  keys, anything echoed to a terminal). Treat `raw/` as sensitive by
  default: gitignored, never pushed, never quoted back verbatim without
  checking what's in it first.
- Coordinate with overseer at `~/` when decisions affect the broader
  ecosystem (e.g., if this ever feeds devlog-engine).
- When uncertain whether an action is in scope, ask.

## Relationship to Existing Projects

- **monitor:** Separate tool, different purpose — monitor watches git/file
  activity across projects; this captures raw terminal I/O within a single
  session. Both are observability infrastructure but don't overlap.
- **claude-journal-private:** Possible future feed — raw session transcripts
  could become richer source material than hand-written handoffs, but that's
  not decided yet.
- **devlog-engine:** Possible future storage backend once it exists.
