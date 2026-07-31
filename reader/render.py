#!/usr/bin/env python3
"""Render a `script` typescript into a readable transcript.

Uses pyte as a real terminal emulator so redraws (top, progress bars,
tab-completion menus) resolve the way a real terminal would, instead of
leaving garbled duplicate lines behind like naive ANSI-stripping would.

Renders full scrollback (pyte.HistoryScreen), not just the final screen.
The original first-pass choice (2026-07-12, VISION.md) was final-screen-
state only, dumping plain pyte.Screen.display after feeding the whole
typescript -- correct for the short session it was reviewed against, but
it silently discards everything that scrolled off screen. Measured against
real long-running captures (2026-07-30): a 39MB capture rendered to about
1KB of output, because pyte.Screen has no history at all -- the final
screen just happened to be `htop`. Fixed by switching to HistoryScreen and
concatenating its retained scrollback ahead of the current viewport.
"""

import argparse
import re
import sys
from pathlib import Path

import pyte
from wcwidth import wcwidth

COLUMNS = 200
ROWS = 500
HISTORY_LINES = 200_000  # generous: this is a disaster-recovery record, not a UI viewport

# `script` writes its own start/end banner lines directly to the log file,
# bypassing the pty, so they use a bare \n instead of \r\n. Feeding them
# through pyte misaligns the line right after. Strip them out and render
# them as plain metadata instead.


def _row_to_str(row, columns: int) -> str:
    """Convert one pyte row buffer (a dict of column -> Char, the same
    format used internally by Screen.buffer and HistoryScreen.history.top/
    bottom) to a plain string. Mirrors pyte.Screen.display's own
    (private) rendering logic so history rows and viewport rows render
    identically."""
    chars = []
    is_wide_char = False
    for x in range(columns):
        if is_wide_char:
            is_wide_char = False
            continue
        char = row[x].data
        is_wide_char = wcwidth(char[0]) == 2
        chars.append(char)
    return "".join(chars)


def render(typescript_path: Path) -> str:
    text = typescript_path.read_bytes().decode("utf-8", errors="replace")

    header = ""
    start_match = re.match(r"Script started on.*?\]\n", text)
    if start_match:
        header = start_match.group(0).strip()
        text = text[start_match.end():]

    footer = ""
    end_match = re.search(r"\n?Script done on.*?\]\n?\Z", text)
    if end_match:
        footer = end_match.group(0).strip()
        text = text[:end_match.start()]

    screen = pyte.HistoryScreen(COLUMNS, ROWS, history=HISTORY_LINES)
    stream = pyte.Stream(screen)
    stream.feed(text)

    history_lines = [_row_to_str(row, COLUMNS) for row in screen.history.top]
    lines = history_lines + screen.display + [
        _row_to_str(row, COLUMNS) for row in screen.history.bottom
    ]
    while lines and lines[-1].strip() == "":
        lines.pop()
    body = "\n".join(line.rstrip() for line in lines)

    parts = [p for p in (header, body, footer) if p]
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("typescript", type=Path, help="path to a script(1) typescript file")
    parser.add_argument(
        "-o", "--output", type=Path, default=None,
        help="write transcript here instead of stdout",
    )
    args = parser.parse_args()

    if not args.typescript.exists():
        print(f"error: {args.typescript} not found", file=sys.stderr)
        sys.exit(1)

    transcript = render(args.typescript)

    if args.output:
        args.output.write_text(transcript)
    else:
        sys.stdout.write(transcript)


if __name__ == "__main__":
    main()
