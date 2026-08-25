from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class Metrics:
    total_requests: int = 0
    total_ingests: int = 0
    total_ingests_accepted: int = 0
    total_429: int = 0
    total_402: int = 0
    total_adqa: int = 0
    total_quota_warnings: int = 0
    total_errors: int = 0
    latency_sum_ms: float = 0.0
    latency_count: int = 0

    def inc_request(self) -> None:
        self.total_requests += 1

    def inc_ingest(self) -> None:
        self.total_ingests += 1

    def inc_ingest_accepted(self) -> None:
        self.total_ingests_accepted += 1

    def inc_429(self) -> None:
        self.total_429 += 1

    def inc_402(self) -> None:
        self.total_402 += 1

    def inc_adqa(self) -> None:
        self.total_adqa += 1

    def inc_quota_warning(self) -> None:
        self.total_quota_warnings += 1

    def inc_error(self) -> None:
        self.total_errors += 1

    def observe_latency(self, ms: float) -> None:
        self.latency_sum_ms += float(ms)
        self.latency_count += 1

    def avg_latency_ms(self) -> float | None:
        if self.latency_count <= 0:
            return None
        return round(self.latency_sum_ms / self.latency_count, 2)

    def to_slo(self) -> dict:
        req = max(1, self.total_requests)
        return {
            "requests": self.total_requests,
            "adqaChecks": self.total_adqa,
            "ingestAcceptRate": round(self.total_ingests_accepted / max(1, self.total_ingests), 4)
            if self.total_ingests
            else None,
            "errorRate": round(self.total_errors / req, 4),
            "rateLimit429": self.total_429,
            "quota402": self.total_402,
            "quotaWarnings": self.total_quota_warnings,
            "avgLatencyMs": self.avg_latency_ms(),
        }


METRICS = Metrics()

