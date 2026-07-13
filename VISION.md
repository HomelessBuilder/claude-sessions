# VISION — claude-sessions

*Captured from an overseer conversation on 2026-07-11. This is the founding
design discussion, preserved so the building instance doesn't have to
re-derive it.*

## The Problem

`~/claude-sessions` existed as an empty placeholder since 2026-07-04:
"Raw terminal output capture — an observability feature planned alongside
`monitor`." No implementation, no owner, no design decided. Diego asked,
in general terms, how to enable automatic terminal capture on BunsenLabs
Linux, and the conversation turned into scoping this project properly.

## Options Considered for Capture

**Option 1 — `script` (util-linux)**
Wrap every interactive shell in `script`, auto-started from `.bashrc`:

```bash
if [ -z "$SCRIPT_ACTIVE" ]; then
    export SCRIPT_ACTIVE=1
    mkdir -p ~/claude-sessions/raw
    exec script -qefc "$SHELL" ~/claude-sessions/raw/$(date +%Y%m%d-%H%M%S)-$$.typescript
fi
```

- Benefit: zero dependencies, already installed, plain-ish text output,
  low overhead, easy to feed into other tooling as raw bytes.
- Drawback: the raw file is full of ANSI escape sequences — cursor moves,
  redraws, colors — so `cat`-ing it directly is ugly and misleading for
  anything that redraws in place.
- Drawback: no timing info in the basic form (fixed by `-t`, see below).

**Option 2 — `asciinema`**
Purpose-built session recorder; `.cast` output is structured JSON with
timing, replayable via `asciinema play`.

- Benefit: faithful replay out of the box, clean separation of raw bytes
  from presentation.
- Drawback: external dependency; `.cast` isn't human-readable directly;
  more friction if something later needs to parse it programmatically.

## The Replay vs. Read Distinction

A key realization mid-conversation: `script` already has a built-in
equivalent to asciinema's replay, via the `-t` timing flag plus
`scriptreplay`:

```bash
script -t2 timing.log -a typescript.log
scriptreplay -t timing.log typescript.log -s /bin/bash
```

So **faithful replay was never actually the hard part** — it's free, no
code needed, either via `script -t`/`scriptreplay` or asciinema. The real
gap is the other direction: a **static, readable transcript** for browsing
and grepping closed sessions, which neither tool gives you directly.

## Two Tiers of "Clean"

1. **Naive ANSI stripping** (regex like `s/\x1b\[[0-9;]*[a-zA-Z]//g`, or
   tools like `col -b`): handles color codes fine, but breaks on anything
   that redraws in place — `top`, progress bars, `less`, tab-completion
   menus all turn into garbled duplicate lines because the escape codes
   that would have told a real terminal "overwrite this line" get stripped
   instead of interpreted.
2. **Real terminal emulation** via `pyte` (pure-Python VT100/xterm
   emulator library): feed it the raw byte stream, it maintains an actual
   virtual screen buffer the way a real terminal would, resolving cursor
   movement and redraws correctly. Dumping that buffer's state gives a
   genuinely accurate "what was actually on screen" transcript.

## Decision

Build the **reader**, using **tier 2 (pyte)**. Diego's own framing:
*"having something test and review would need to occur before I can really
know what feels best to me"* — meaning don't over-plan the exact output
format on paper; get a first working version in front of him and iterate.
That's why the granularity question (per-command snapshot vs. periodic vs.
final-state-only) is left open in `CLAUDE.md` rather than decided here.

## Handoff

Diego will open a terminal and run Claude Code inside `~/claude-sessions`
to actually start development. This document plus `CLAUDE.md` are the full
context that instance needs — it shouldn't need to ask the overseer to
re-explain any of the above.

## Immediate Build Steps (suggested starting point, not gospel)

1. `.gitignore` first — exclude `raw/` before anything else, since captured
   sessions can contain secrets typed at a prompt.
2. Write the `.bashrc` capture wrapper (see Option 1 above, using `-t` so
   timing data exists even though replay isn't the immediate goal — it's
   nearly free and keeps the door open).
3. Set up a venv, add `pyte` to `requirements.txt`.
4. Write `reader/render.py`: read a typescript + timing file pair, step
   pyte's screen through the byte stream, emit a readable transcript.
   Start with the simplest possible granularity (e.g. dump final screen
   state only) to get something in front of Diego fast, per his explicit
   "test and review" preference — don't polish the format before he's seen
   one real example.
5. Show Diego a real example before building anything more elaborate.
