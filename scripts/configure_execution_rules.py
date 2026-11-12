"""Print machine-specific Codex search rules; write them only with --install."""

import argparse
import json
import os
from pathlib import Path
import sys


def existing_file(value):
    path = Path(value).expanduser().resolve(strict=True)
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")
    return str(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--es", required=True, help="Installed es.exe path")
    parser.add_argument("--flpsearch", required=True, help="Installed flpsearch.exe path")
    parser.add_argument("--python", default=sys.executable, help="Python used for the preview helper")
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME") or str(Path.home() / ".codex"))
    parser.add_argument("--install", action="store_true", help="Write this computer's rules after reviewing them")
    args = parser.parse_args()
    try:
        es = existing_file(args.es)
        flpsearch = existing_file(args.flpsearch)
        python = existing_file(args.python)
        preview = existing_file(Path(__file__).with_name("filelocator_preview.py"))
        if Path(es).name.lower() != "es.exe" or Path(flpsearch).name.lower() != "flpsearch.exe":
            raise ValueError("Use the installed es.exe and flpsearch.exe executables")
    except (OSError, ValueError) as error:
        parser.error(str(error))

    patterns = [
        [es],
        [python, "-B", preview, "--executable", flpsearch, "--"],
    ]
    rules = "# Local File Search command exceptions for this computer.\n"
    for pattern in patterns:
        rules += "prefix_rule(pattern=" + json.dumps(pattern, ensure_ascii=False) + ', decision="allow")\n'

    if not args.install:
        print(rules, end="")
        return 0

    target = Path(args.codex_home).expanduser().resolve() / "rules" / "local-file-search.rules"
    try:
        if target.exists():
            if target.read_text(encoding="utf-8") != rules:
                parser.error(f"Existing rules differ; review them before replacing: {target}")
            print(f"Already installed: {target}")
            return 0
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8", newline="\n") as output:
            output.write(rules)
    except OSError as error:
        parser.error(str(error))
    print(f"Installed: {target}\nRestart Codex to load these rules.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
