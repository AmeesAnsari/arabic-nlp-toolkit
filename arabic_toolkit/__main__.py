"""Command line: normalise or transliterate text from arguments or stdin.

    python -m arabic_toolkit normalize "أَهْلاً وَسَهْلاً"
    echo "كتاب" | python -m arabic_toolkit buckwalter
"""

from __future__ import annotations

import argparse
import sys

from . import from_buckwalter, normalize, normalize_loose, to_buckwalter, tokenize


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="arabic_toolkit")
    parser.add_argument("command", choices=["normalize", "loose", "tokens", "buckwalter", "unbuckwalter"])
    parser.add_argument("text", nargs="*", help="text to process; reads stdin if omitted")
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    text = " ".join(args.text) if args.text else sys.stdin.read()
    run = {
        "normalize": normalize,
        "loose": normalize_loose,
        "tokens": lambda t: "\n".join(tokenize(t)),
        "buckwalter": to_buckwalter,
        "unbuckwalter": from_buckwalter,
    }[args.command]
    print(run(text.rstrip("\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
