#!/usr/bin/env python3
"""Render a `script` typescript into a readable transcript.

First-pass granularity per VISION.md: dump the final screen state only,
using pyte as a real terminal emulator so redraws (top, progress bars,
tab-completion menus) resolve the way a real terminal would, instead of
leaving garbled duplicate lines behind like naive ANSI-stripping would.
"""

import argparse
import re
import sys
from pathlib import Path

import pyte

COLUMNS = 200
ROWS = 500

# `script` writes its own start/end banner lines directly to the log file,
# bypassing the pty, so they use a bare \n instead of \r\n. Feeding them
# through pyte misaligns the line right after. Strip them out and render
# them as plain metadata instead.


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

    screen = pyte.Screen(COLUMNS, ROWS)
    stream = pyte.Stream(screen)
    stream.feed(text)

    lines = screen.display
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
