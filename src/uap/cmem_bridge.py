"""CMEM bridge — recall continuity memory; NARNA scores decisions (never replace CMEM).

Env:
  NARNA_CMEM_URL / CMEM_MCP_URL / CMEM_URL — private MCP or HTTP recall endpoint
  NARNA_CMEM_TOKEN / CMEM_TOKEN — optional bearer
  NARNA_CMEM_MODE — http | local | off (default: http if URL set else local)
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def _env(*names: str, default: str = "") -> str:
    for n in names:
        v = os.environ.get(n)
        if v:
            return v.strip()
    return default


class CmemBridge:
    """Read-only bridge into CMEM / claude-mem style observations."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.url = _env("NARNA_CMEM_URL", "CMEM_MCP_URL", "CMEM_URL")
        self.token = _env("NARNA_CMEM_TOKEN", "CMEM_TOKEN", "CMEM_API_KEY")
        mode = _env("NARNA_CMEM_MODE").lower()
        if mode:
            self.mode = mode
        elif self.url:
            self.mode = "http"
        else:
            self.mode = "local"

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "mode": self.mode,
            "urlConfigured": bool(self.url),
            "standard": "NGS-0025-cmem-bridge",
            "role": "memory_feedstock",
            "narnaRole": "decision_quality",
        }

    def search(self, query: str, *, limit: int = 8) -> list[dict[str, Any]]:
        query = str(query or "").strip()
        if not query or self.mode == "off":
            return []
        if self.mode == "http" and self.url:
            try:
                return self._http_search(query, limit=limit)
            except Exception:
                return self._local_search(query, limit=limit)
        return self._local_search(query, limit=limit)

    def enrich_context(
        self,
        action: str,
        context: dict[str, Any] | None = None,
        *,
        limit: int = 8,
    ) -> dict[str, Any]:
        """Merge CMEM hits into Decision/ADQA context (feedstock only)."""
        ctx = dict(context or {})
        hits = self.search(action, limit=limit)
        if not hits and ctx.get("question"):
            hits = self.search(str(ctx["question"]), limit=limit)
        cmem = {
            "source": "cmem",
            "mode": self.mode,
            "query": action,
            "hits": hits,
            "count": len(hits),
        }
        ctx["_cmem"] = cmem
        # Surface into durable-memory shaped slices so ADQA memory attr rises
        mem = dict(ctx.get("_memory") or {})
        slices = list(mem.get("slices") or [])
        for h in hits[:limit]:
            slices.append(
                {
                    "scope": "cmem",
                    "id": h.get("id") or h.get("observationId") or "cmem",
                    "summary": h.get("summary") or h.get("text") or h.get("title") or "",
                    "score": h.get("score"),
                }
            )
        if slices:
            mem["slices"] = slices
            mem["cmemHits"] = len(hits)
            ctx["_memory"] = mem
        # Soft decisionMemory lessons from CMEM titles
        if hits:
            dmem = dict(ctx.get("decisionMemory") or {})
            lessons = list(dmem.get("lessons") or [])
            for h in hits[:3]:
                text = str(h.get("summary") or h.get("text") or h.get("title") or "").strip()
                if text and text not in lessons:
                    lessons.append(f"cmem: {text[:200]}")
            dmem["lessons"] = lessons[:8]
            dmem["cmem"] = True
            ctx["decisionMemory"] = dmem
        return ctx

    def ingest_local(self, observation: dict[str, Any]) -> dict[str, Any]:
        """Write a local observation stub (offline / tests — not a CMEM fork)."""
        root = self.workspace / ".uap" / "cmem-bridge"
        root.mkdir(parents=True, exist_ok=True)
        path = root / "observations.jsonl"
        row = {
            "id": observation.get("id") or f"local-{path.stat().st_size if path.exists() else 0}",
            "summary": observation.get("summary") or observation.get("text") or "",
            "tags": observation.get("tags") or [],
            "action": observation.get("action"),
            "source": observation.get("source") or "local",
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return {"ok": True, "observation": row}

    def _local_path(self) -> Path:
        return self.workspace / ".uap" / "cmem-bridge" / "observations.jsonl"

    def _local_search(self, query: str, *, limit: int) -> list[dict[str, Any]]:
        path = self._local_path()
        if not path.exists():
            return []
        q = query.lower()
        tokens = [t for t in q.replace(".", " ").split() if len(t) > 2]
        hits: list[dict[str, Any]] = []
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                blob = " ".join(
                    str(row.get(k) or "") for k in ("summary", "text", "title", "action", "tags")
                ).lower()
                score = 0.0
                if q in blob:
                    score = 0.95
                else:
                    score = sum(1.0 for t in tokens if t in blob) / max(1, len(tokens))
                if score >= 0.3:
                    hits.append({**row, "score": round(score, 3), "source": row.get("source") or "local"})
        hits.sort(key=lambda x: float(x.get("score") or 0), reverse=True)
        return hits[:limit]

    def _http_search(self, query: str, *, limit: int) -> list[dict[str, Any]]:
        """Best-effort HTTP recall against CMEM Cloud / MCP HTTP gateway."""
        base = self.url.rstrip("/")
        # Common shapes: /search?q= · /v1/search · /mcp/search
        candidates = [
            f"{base}/search?q={urllib.parse.quote(query)}&limit={limit}",
            f"{base}/v1/search?q={urllib.parse.quote(query)}&limit={limit}",
            f"{base}?q={urllib.parse.quote(query)}&limit={limit}",
        ]
        headers = {"Accept": "application/json", "User-Agent": "narna-cmem-bridge/0.1"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        last_err: Exception | None = None
        for url in candidates:
            try:
                req = urllib.request.Request(url, headers=headers, method="GET")
                with urllib.request.urlopen(req, timeout=8) as resp:
                    raw = resp.read().decode("utf-8", errors="replace")
                data = json.loads(raw) if raw else {}
                return self._normalize_hits(data, limit=limit)
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as e:
                last_err = e
                continue
        # POST JSON body fallback
        for path in ("/search", "/v1/search", "/tools/search"):
            try:
                body = json.dumps({"query": query, "q": query, "limit": limit}).encode()
                req = urllib.request.Request(
                    f"{base}{path}",
                    data=body,
                    headers={**headers, "Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=8) as resp:
                    raw = resp.read().decode("utf-8", errors="replace")
                return self._normalize_hits(json.loads(raw) if raw else {}, limit=limit)
            except Exception as e:
                last_err = e
                continue
        if last_err:
            raise last_err
        return []

    @staticmethod
    def _normalize_hits(data: Any, *, limit: int) -> list[dict[str, Any]]:
        if isinstance(data, list):
            rows = data
        elif isinstance(data, dict):
            rows = (
                data.get("hits")
                or data.get("results")
                or data.get("observations")
                or data.get("memories")
                or data.get("items")
                or []
            )
        else:
            rows = []
        out: list[dict[str, Any]] = []
        for row in rows[:limit]:
            if isinstance(row, str):
                out.append({"summary": row, "score": 0.7, "source": "cmem"})
            elif isinstance(row, dict):
                out.append(
                    {
                        "id": row.get("id") or row.get("observationId"),
                        "summary": row.get("summary")
                        or row.get("text")
                        or row.get("title")
                        or row.get("content")
                        or "",
                        "score": row.get("score") or row.get("relevance") or 0.8,
                        "source": "cmem",
                        "tags": row.get("tags") or [],
                    }
                )
        return out
