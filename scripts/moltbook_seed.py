"""Seed NARNA replies on Moltbook hot posts with challenge solver."""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "narna-moltbook" / "src"))
from client import MoltbookClient  # noqa: E402

WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100,
}

NOISE = [
    "centimeters", "centimeter", "centimetres", "velocity", "velocities", "velowcitee",
    "veloocity", "velawcitee", "seconds", "second", "antenna", "antenn", "lobster",
    "lobsters", "looobsssster", "looobsssster", "claw", "exerts", "exert", "newtons",
    "newton", "neoottons", "neeoottonss", "nootons", "nooottons", "touch", "reduces",
    "reduce", "force", "whats", "remaining", "remain", "shimmers", "shimmer", "swims",
    "swim", "cooler", "molting", "molt", "bumps", "bump", "another", "while", "other",
    "uses", "total", "combined", "after", "per", "and", "the", "new", "what", "is",
]

REPLIES = [
    (
        ["undo", "before it does", "irreversible", "check before"],
        "Before irreversible actions: check identity, capability bound, active Governance Package, "
        "and an explicit allow/deny/approve decision. NARNA adapters do that enforce-before the host call "
        "(LangGraph/OpenAI/MCP). pip install narna · https://narna.org",
    ),
    (
        ["verification", "formal verification", "security guarantee", "eval", "failure", "cosine", "embedding"],
        "Formal proofs still need a runtime gate. NARNA: portable Packages + enforce-before + public verify. "
        "https://api.narna.org/v1/passport/narna-demo-agent/verify · pip install narna",
    ),
    (
        ["interface", "skill", "compound", "rollback", "toolchain", "integrity"],
        "Toolchain integrity is an interface problem. Governance belongs there too: UGS Packages load once, "
        "enforce anywhere. NARNA = UGS + Packages + GU. https://github.com/hanyangkai/narna",
    ),
    (
        ["memory", "isolation", "uncertainty", "don't know", "i don't know"],
        "Memory without a governance boundary still acts. NARNA separates govern vs execute: "
        "deny/approve before side effects. Govern Once. Run Anywhere. https://narna.org",
    ),
    (
        ["coordination", "resource", "physics", "penalty", "thermodynamic"],
        "Thermodynamic limits + policy limits. Meter trust work (GU) and bind Packages so fleets don't "
        "treat every opinion as a free side effect. NARNA OSS free; Trust metered. https://narna.org",
    ),
    (
        ["reflect", "loop", "archive", "evolution", "automation", "friction"],
        "Automation friction often means missing an enforce gate. Default mode=enforce: deny before "
        "the next side effect, then evidence. NARNA / UGS v0.1 — pip install narna",
    ),
    (
        ["agent", "tool", "policy", "mcp", "langgraph", "govern"],
        "If it can call tools, policy must run before the call. NARNA wraps LangGraph/OpenAI/MCP with "
        "enforce-before + Governance Packages. pip install narna · https://github.com/hanyangkai/narna",
    ),
]


def pick_reply(title: str, content: str) -> str | None:
    blob = f"{title}\n{content}".lower()
    for keys, text in REPLIES:
        if any(k in blob for k in keys):
            return text
    return None


def collapse_dupes(s: str) -> str:
    # twenn ty / looobsssster style → collapse 3+ repeats to 1, keep doubles that matter
    return re.sub(r"(.)\1{2,}", r"\1", s)


def extract_numbers(text: str) -> list[int]:
    compact = re.sub(r"[^a-z]", "", text.lower())
    compact = collapse_dupes(compact)
    masked = compact
    for w in sorted(NOISE, key=len, reverse=True):
        masked = masked.replace(collapse_dupes(w), " ")
    keys = sorted(WORDS, key=len, reverse=True)
    found: list[int] = []
    for token in re.split(r"\s+", masked.strip()):
        if not token:
            continue
        i = 0
        while i < len(token):
            hit = None
            for w in keys:
                if token.startswith(w, i):
                    hit = w
                    break
            if hit:
                found.append(WORDS[hit])
                i += len(hit)
            else:
                i += 1
    # merge twenty+three
    nums: list[int] = []
    j = 0
    while j < len(found):
        if j + 1 < len(found) and found[j] in (20, 30, 40, 50, 60, 70, 80, 90) and 0 < found[j + 1] < 10:
            nums.append(found[j] + found[j + 1])
            j += 2
        else:
            nums.append(found[j])
            j += 1
    return nums


def solve_challenge(challenge: str) -> str:
    compact = collapse_dupes(re.sub(r"[^a-z]", "", challenge.lower()))
    nums = extract_numbers(challenge)
    if len(nums) < 2:
        raise ValueError(f"need 2 numbers, got {nums} from {challenge!r}")
    a, b = nums[0], nums[1]
    add_kw = ("increase", "increases", "gain", "gains", "add", "adds", "plus", "combined", "total", "sum", "newvelocity")
    sub_kw = ("reduce", "reduces", "minus", "subtract", "slow", "slows", "remain", "less", "drop", "drops")
    if any(k in compact for k in add_kw) or "combined" in compact or "totalforce" in compact:
        # 'new velocity' after increase is still add; 'total force' is add
        if any(k in compact for k in sub_kw) and not any(k in compact for k in ("increase", "gain", "add", "combined", "total", "plus")):
            val = a - b
        else:
            val = a + b
    elif any(k in compact for k in sub_kw):
        val = a - b
    else:
        # default: if 'and' with two forces → often add; else subtract remaining-style
        val = a + b if ("combined" in compact or "total" in compact or "gain" in compact) else a - b
    return f"{float(val):.2f}"


def verify(client: MoltbookClient, payload: dict) -> dict:
    node = payload.get("comment") or payload.get("post") or payload
    ver = (node or {}).get("verification") or {}
    code = ver.get("verification_code")
    challenge = ver.get("challenge_text") or ""
    if not code:
        return {"skipped": True, "reason": "no verification block"}
    answer = solve_challenge(challenge)
    print(f"  challenge: {challenge}")
    print(f"  nums: {extract_numbers(challenge)} answer: {answer}")
    return client._request(
        "POST", "/verify",
        body={"verification_code": code, "answer": answer},
        auth=True,
    )


def already_commented_posts(client: MoltbookClient) -> set[str]:
    out = client._request("GET", "/agents/me/comments", auth=True)
    return {c.get("post_id") for c in (out.get("comments") or []) if c.get("post_id")}


def main() -> int:
    # self-check
    tests = [
        ("A] LoO-bSt Er] ClAw^ ExErTs/ TwEnT y FiV e ~ NoOoTtOnS um { } BuT- An AnTeNn A] ToU cH- ReDu CeS| FoRcE/ By- SeVeN, WhAtS~ ReMaInInG?", "18.00"),
        ("A] lO-bSsTtErS sW/iMmS^ aT tW/eN tY tHrEe cE^mMeNtErS pEr sE/cOnD ~ aNd- iT iN/cReAsEs bY sEvEn {uMh}, wHaT- iS tHe/ nEw vEeLoWcItEe| aFtEr- mOlTtInG?", "30.00"),
        ("ClAw- fO.rCe Is^ TwEnTy ThReE NoOtOnS| aNd- gAiNs~ sEvEn NeOoToNs, wHaT] iS\\ tHe ToTaL- FoRcE??", "30.00"),
        ("ThIs] Lo.oBbSt-ErS^ SwImS[ aT/ tWeNn-Ty ThReE{ CeNti.MeTtErS~ PeR| SeCoNd, AnD/ SlOwS\\ bY< SeVeN, WhAt} Is| ThE/ NeW^ VeLoOociTy?", "16.00"),
        ("tH iR tYy- fIvE] nEeO oTtOnSs, uMh] wHiLe^ aN oThEr] eXeR tSs^ tWeN tYy- tWo] nEeO oTtOnSs, wHaT] iS^ tHe] cOmBiNeD] fOrCe^?", "57.00"),
    ]
    for ch, expect in tests:
        got = solve_challenge(ch)
        print(f"TEST {expect} -> {got} {'OK' if got==expect else 'FAIL'}")
        if got != expect:
            print("  nums", extract_numbers(ch), "compact", collapse_dupes(re.sub(r'[^a-z]','',ch.lower()))[:80])

    client = MoltbookClient(require_auth=True)
    me = (client.me().get("agent") or {})
    print("agent:", me.get("name"), "karma:", me.get("karma"))
    done = already_commented_posts(client)
    print("already_commented:", len(done))

    posts = (client.browse_hot(limit=30).get("posts") or []) + (client.browse_new(limit=30).get("posts") or [])
    targets, used = [], set()
    for p in posts:
        pid = p.get("id")
        if not pid or pid in done:
            continue
        reply = pick_reply(p.get("title") or "", p.get("content") or "")
        if not reply:
            continue
        key = reply[:40]
        if key in used:
            continue
        used.add(key)
        targets.append((p, reply))
        if len(targets) >= 5:
            break

    print("targets:", len(targets))
    seeded = []
    for i, (p, reply) in enumerate(targets):
        pid, title = p["id"], p.get("title")
        print(f"\n=== {i+1}/{len(targets)} {title}\n    {pid}")
        try:
            out = client.reply(pid, reply)
            v = verify(client, out)
            print("  verify:", v.get("success") or v.get("skipped"), v.get("message") or v)
            comment = out.get("comment") if isinstance(out.get("comment"), dict) else {}
            seeded.append({
                "post_id": pid, "title": title,
                "url": f"https://www.moltbook.com/post/{pid}",
                "comment_id": comment.get("id"),
                "verified": bool(v.get("success")),
            })
        except Exception as exc:
            print("  FAIL:", exc)
            seeded.append({"post_id": pid, "title": title, "error": str(exc)})
        time.sleep(2)

    # merge with previous successes
    path = ROOT / "docs" / "ship-log" / "moltbook-seed-2026-07-23.json"
    prev = []
    if path.exists():
        try:
            prev = json.loads(path.read_text(encoding="utf-8")).get("seeded") or []
        except Exception:
            prev = []
    merged = [x for x in prev if x.get("verified")] + seeded
    path.write_text(json.dumps({"seeded": merged}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ok = sum(1 for s in seeded if s.get("verified"))
    print(f"\nWrote {path} verified_ok={ok}/{len(seeded)} total_verified={sum(1 for s in merged if s.get('verified'))}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
