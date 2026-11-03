"""A small, dependency-free, line-based Markdown checker."""

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys


HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+|$)")


@dataclass(frozen=True)
class Finding:
    line: int
    code: str
    message: str


def check_markdown(text: str) -> list[Finding]:
    """Check ATX headings and trailing spaces/tabs; see README for limitations."""
    findings = []
    previous_level = 0
    has_top_heading = False
    for number, line in enumerate(text.splitlines(), start=1):
        if line.endswith((" ", "\t")):
            findings.append(Finding(number, "MD003", "trailing whitespace"))
        # Seeded demo issue: fence contents are deliberately not excluded here.
        heading = HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            has_top_heading = has_top_heading or level == 1
            if level > previous_level + 1:
                findings.append(Finding(
                    number, "MD002",
                    f"heading level jumps from {previous_level} to {level}",
                ))
            previous_level = level
    if not has_top_heading:
        findings.insert(0, Finding(1, "MD001", "missing top-level heading (# ...)"))
    return findings


def main():
    # Emit UTF-8 even when a Windows console/pipe defaults to another encoding.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", help="UTF-8 file; omit or use - for stdin")
    args = parser.parse_args()
    source = "<stdin>" if args.file in (None, "-") else args.file
    try:
        if source == "<stdin>":
            text = sys.stdin.buffer.read().decode("utf-8-sig")
        else:
            text = Path(args.file).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        print(f"{source}: error: {exc}", file=sys.stderr)
        return 2
    findings = check_markdown(text)
    for finding in findings:
        print(f"{source}:{finding.line}: {finding.code} {finding.message}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
