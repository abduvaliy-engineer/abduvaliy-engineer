#!/usr/bin/env python3
"""Draw every profile SVG (dark + light) from live GitHub data.

    python3 gen/build.py --out dist            # live data, what CI runs
    python3 gen/build.py --out dist --offline  # snapshot in profile.json, no network
    python3 gen/build.py --snapshot            # refresh that snapshot from live data
"""
import argparse
import datetime as dt
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import board  # noqa: E402
import cards  # noqa: E402
import fetch  # noqa: E402
from svg import THEMES  # noqa: E402

CONFIG = HERE / "profile.json"
BANNED = re.compile(r"\b(None|null|nan|NaN|Traceback|Error|undefined)\b")


def render(cfg, live, now):
    files = {}
    for name, th in THEMES.items():
        files[f"board-{name}.svg"] = board.board(cfg, live, th, now)
        files[f"key-{name}.svg"] = board.key(th)
        files[f"terminal-{name}.svg"] = cards.terminal(cfg, th, now)
        for slug, title, sub in cards.HEADINGS:
            files[f"h-{slug}-{name}.svg"] = cards.heading(title, sub, th)
        for p in cfg["projects"]:
            files[f"project-{p['id']}-{name}.svg"] = cards.project(p, live["projects"].get(p["id"]), th, now)
        for c in cfg["contributions"]:
            files[f"contrib-{c['id']}-{name}.svg"] = cards.contribution(c, live["contributions"].get(c["id"]), th)
    return files


def check(files):
    """Every drawing must be valid SVG with no leaked placeholder text."""
    for name, svg in files.items():
        root = ET.fromstring(svg)
        if root.tag != "{http://www.w3.org/2000/svg}svg":
            raise ValueError(f"{name}: not an svg")
        words = " ".join(root.itertext())
        leaked = BANNED.search(words)
        if leaked:
            raise ValueError(f"{name}: placeholder text leaked: {leaked.group()}")


def snapshot(cfg, live):
    for p in cfg["projects"]:
        if p["id"] in live["projects"]:
            p["snapshot"] = live["projects"][p["id"]]
    for c in cfg["contributions"]:
        if c["id"] in live["contributions"]:
            c["snapshot"] = live["contributions"][c["id"]]
    CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=HERE.parent / "dist")
    ap.add_argument("--offline", action="store_true", help="use the snapshot in profile.json")
    ap.add_argument("--snapshot", action="store_true", help="store live data in profile.json")
    ap.add_argument("--now", help="ISO timestamp to draw as of (tests)")
    args = ap.parse_args(argv)

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    now = (dt.datetime.fromisoformat(args.now.replace("Z", "+00:00")) if args.now
           else dt.datetime.now(dt.timezone.utc))
    if args.offline:
        live = fetch.offline(cfg)
    else:
        gh = fetch.GitHub(fetch.token())
        live = fetch.collect(cfg, gh)
        print(f"fetched live data with {gh.calls} GitHub API calls")
    if args.snapshot:
        snapshot(cfg, live)
        print(f"snapshot written to {CONFIG.name}")

    files = render(cfg, live, now)
    check(files)
    args.out.mkdir(parents=True, exist_ok=True)
    for name, svg in files.items():
        (args.out / name).write_text(svg, encoding="utf-8")
    (args.out / "manifest.json").write_text(json.dumps(sorted(files), indent=1) + "\n", encoding="utf-8")
    print(f"drew {len(files)} svgs into {args.out}")
    return files


if __name__ == "__main__":
    main()
