"""Decision Replay — re-evaluate a past Decision Trace with today's knowledge."""

from __future__ import annotations

from typing import Any, Callable

AskFn = Callable[..., dict[str, Any]]


def replay_trace(
    trace: dict[str, Any],
    *,
    ask_fn: AskFn,
    extra_context: str | None = None,
) -> dict[str, Any]:
    """Replay a decision: re-ask with original goal + current lessons."""
    goal = str(trace.get("goal") or "").strip()
    if not goal:
        raise ValueError("trace has no goal")

    lesson = str(trace.get("lesson") or "").strip()
    outcome = trace.get("outcome") or {}
    prior_answer = str(trace.get("answerPreview") or trace.get("rationale") or "")[:800]
    evidence = trace.get("evidence") or []
    evidence_lines = [
        f"- {e.get('type')}: {e.get('ref') or e.get('name') or e}"
        for e in evidence[:12]
        if isinstance(e, dict)
    ]

    prompt = (
        "DECISION REPLAY — you are re-evaluating a past decision with today's knowledge.\n\n"
        f"Original goal:\n{goal}\n\n"
        f"Original choice: {trace.get('chosen')}\n"
        f"Original DQS: {(trace.get('adqa') or {}).get('dqs')}\n"
        f"Original rationale (truncated):\n{prior_answer}\n\n"
        f"Evidence at the time:\n{chr(10).join(evidence_lines) if evidence_lines else '(none)'}\n\n"
        f"Recorded outcome: {outcome.get('status') or 'unknown'}"
        + (f" — {outcome.get('detail')}" if outcome.get("detail") else "")
        + "\n"
        + (f"Lesson learned: {lesson}\n" if lesson else "")
        + (f"\nAdditional context:\n{extra_context}\n" if extra_context else "")
        + "\nWould you choose differently today? State: SAME or CHANGED, then your recommendation "
        "with risks and what evidence you would require."
    )

    out = ask_fn(
        prompt,
        channel="replay",
        use_tools=True,
        capture_skill=False,
        challenge=False,
    )
    answer = str(out.get("answer") or "")
    changed = "CHANGED" in answer.upper()[:200] and "SAME" not in answer.upper()[:80]
    # Heuristic: if both words, prefer CHANGED if it appears first
    upper = answer.upper()
    i_changed = upper.find("CHANGED")
    i_same = upper.find("SAME")
    if i_changed >= 0 and (i_same < 0 or i_changed < i_same):
        changed = True
    elif i_same >= 0:
        changed = False

    return {
        "ok": True,
        "originalTraceId": trace.get("traceId"),
        "originalDecisionId": trace.get("decisionId"),
        "originalChosen": trace.get("chosen"),
        "originalDqs": (trace.get("adqa") or {}).get("dqs"),
        "replayed": {
            "answer": answer,
            "dqs": out.get("dqs"),
            "guardian": out.get("guardian"),
            "decisionId": out.get("decisionId"),
            "traceId": out.get("traceId"),
            "modelsUsed": out.get("modelsUsed"),
        },
        "changed": changed,
        "delta": {
            "dqs": (out.get("dqs") or 0) - ((trace.get("adqa") or {}).get("dqs") or 0),
        },
        "standard": "NGS-0030-replay",
    }
