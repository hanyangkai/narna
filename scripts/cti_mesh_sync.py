#!/usr/bin/env python3
"""Sync CTI mesh — push local signatures to remote hubs and pull feeds.

Examples:
  python scripts/cti_mesh_sync.py --hubs https://api.narna.org
  python scripts/cti_mesh_sync.py --hubs https://api.narna.org --pull-only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    from uap.collective import CollectiveDefense
    from uap.cti_mesh import CTIMesh

    p = argparse.ArgumentParser(description="NARNA CTI multi-hub mesh sync")
    p.add_argument("--hubs", default="", help="Comma-separated hub base URLs")
    p.add_argument("--push-only", action="store_true")
    p.add_argument("--pull-only", action="store_true")
    p.add_argument("--workspace", default=".")
    args = p.parse_args()

    ws = Path(args.workspace)
    CollectiveDefense(ws).set_opt_in(True)
    mesh = CTIMesh(ws)
    if args.hubs:
        mesh.set_hubs([u.strip() for u in args.hubs.split(",") if u.strip()])

    if args.pull_only:
        out = mesh.pull()
    elif args.push_only:
        out = mesh.push()
    else:
        out = mesh.sync()
    print(json.dumps(out, indent=2))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
