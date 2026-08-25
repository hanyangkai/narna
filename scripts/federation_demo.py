#!/usr/bin/env python3
"""Federation 2-peer demo — Org A publishes threat signature → Org B pulls & applies.

Usage (no network peers required — two local workspaces):
  python scripts/federation_demo.py

Optional live peers:
  python scripts/federation_demo.py --peer-a http://127.0.0.1:8100 --peer-b http://127.0.0.1:8100
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

# Allow running from repo root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def demo_local() -> dict:
    from uap.capability_gov import CapabilityGovernor
    from uap.collective import CollectiveDefense

    with tempfile.TemporaryDirectory() as ta, tempfile.TemporaryDirectory() as tb:
        org_a = Path(ta)
        org_b = Path(tb)
        a = CollectiveDefense(org_a)
        b = CollectiveDefense(org_b)
        a.set_opt_in(True)
        b.set_opt_in(True)

        sig = a.publish_from_threat(
            {
                "patterns": ["spawn_storm", "bulk_exfiltration"],
                "riskScore": 0.95,
                "riskBand": "critical",
                "recommendation": "kill",
            }
        )
        bundle = a.export_bundle()
        imported = b.import_bundle(bundle)
        applied = b.apply(sig["signatureId"], agent_id="agent_suspect", auto_kill=True)
        gov = CapabilityGovernor(org_b).evaluate(
            capability="create.agent", agent_id="agent_suspect", profile="guardian"
        )
        return {
            "mode": "local-two-workspace",
            "orgA": {"published": sig["signatureId"], "outbox": len(a.list_signatures(source="outbox"))},
            "orgB": {
                "imported": imported["imported"],
                "applied": applied["ok"],
                "capabilityDecision": gov["decision"],
                "reasons": gov["reasons"],
            },
            "ok": gov["decision"] == "deny",
            "standard": "NGS-0020",
        }


def demo_http(peer_a: str, peer_b: str) -> dict:
    import urllib.request

    def post(url: str, body: dict | None = None):
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())

    # Opt-in both (same host ok for demo)
    post(f"{peer_a.rstrip('/')}/v1/guardian/collective/opt-in", {"optIn": True})
    post(f"{peer_b.rstrip('/')}/v1/guardian/collective/opt-in", {"optIn": True})
    # Point B at A as peer then pull
    post(f"{peer_b.rstrip('/')}/v1/guardian/collective/peers", {"peers": [peer_a.rstrip("/")]})
    # Publish from A via session-less report path
    pub = post(
        f"{peer_a.rstrip('/')}/v1/guardian/collective/publish",
        {
            "report": {
                "patterns": ["spawn_storm"],
                "riskScore": 0.9,
                "riskBand": "critical",
                "recommendation": "restrict",
            }
        },
    )
    pull = post(f"{peer_b.rstrip('/')}/v1/guardian/collective/pull")
    return {"mode": "http-peers", "publish": pub, "pull": pull, "ok": True, "standard": "NGS-0020"}


def main() -> int:
    p = argparse.ArgumentParser(description="NARNA Collective Defense 2-peer demo")
    p.add_argument("--peer-a", default=None)
    p.add_argument("--peer-b", default=None)
    args = p.parse_args()
    if args.peer_a and args.peer_b:
        out = demo_http(args.peer_a, args.peer_b)
    else:
        out = demo_local()
    print(json.dumps(out, indent=2))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
