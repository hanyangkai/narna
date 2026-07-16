from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class Metrics:
    total_requests: int = 0
    total_ingests: int = 0
    total_ingests_accepted: int = 0
    total_429: int = 0

    def inc_request(self) -> None:
        self.total_requests += 1

    def inc_ingest(self) -> None:
        self.total_ingests += 1

    def inc_ingest_accepted(self) -> None:
        self.total_ingests_accepted += 1

    def inc_429(self) -> None:
        self.total_429 += 1


METRICS = Metrics()

