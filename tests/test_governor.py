from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from uap.execution_graph import ExecutionGraph, GraphNode
from uap.governor import Governor, GovernorConfig, GovernorError
from uap.metering import MeteringStore
from uap.session import SessionStore


class GovernorMeteringTest(unittest.TestCase):
    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.ws = Path(self.td.name)
        self.governor = Governor(self.ws, config=GovernorConfig(recursion_depth_limit=3))

    def tearDown(self) -> None:
        self.td.cleanup()

    def test_spawn_tree_inflates_gu(self) -> None:
        session = self.governor.open_session("ceo-agent")
        kinds = ["agent", "sub_agent", "tool", "tool", "llm", "tool"]
        parent = None
        for kind in kinds:
            result = self.governor.begin_unit(
                session,
                logical_agent_id="ceo-agent",
                unit_kind=kind,
                parent_unit_id=parent,
            )
            session = result.session
            parent = result.unit.unit_id
        self.assertEqual(session.total_gu, len(kinds))
        self.assertEqual(MeteringStore(self.ws).org_used_gu(), len(kinds))

    def test_loop_detection_terminates(self) -> None:
        session = self.governor.open_session("agent-a")
        root = self.governor.begin_unit(session, logical_agent_id="agent-a", unit_kind="agent")
        mid = self.governor.begin_unit(
            root.session,
            logical_agent_id="agent-b",
            unit_kind="sub_agent",
            parent_unit_id=root.unit.unit_id,
        )
        with self.assertRaises(GovernorError):
            self.governor.begin_unit(
                mid.session,
                logical_agent_id="agent-a",
                unit_kind="sub_agent",
                parent_unit_id=mid.unit.unit_id,
            )

    def test_recursion_depth_limit(self) -> None:
        session = self.governor.open_session("planner")
        parent = None
        for _ in range(2):
            result = self.governor.begin_unit(
                session,
                logical_agent_id="planner",
                unit_kind="workflow_step",
                parent_unit_id=parent,
                label="planner",
            )
            session = result.session
            parent = result.unit.unit_id
        with self.assertRaises(GovernorError):
            self.governor.begin_unit(
                session,
                logical_agent_id="planner",
                unit_kind="workflow_step",
                parent_unit_id=parent,
            )

    def test_monthly_budget_cost_guard(self) -> None:
        budget_path = self.ws / ".uap" / "budget.json"
        budget_path.parent.mkdir(parents=True, exist_ok=True)
        budget_path.write_text('{"monthlyLimitGu": 2}', encoding="utf-8")
        session = self.governor.open_session("a")
        self.governor.begin_unit(session, logical_agent_id="a", unit_kind="tool")
        self.governor.begin_unit(session, logical_agent_id="a", unit_kind="tool")
        with self.assertRaises(GovernorError):
            self.governor.open_session("b")

    def test_execution_graph_persistence(self) -> None:
        store = SessionStore(self.ws)
        session = store.create("x")
        graph = ExecutionGraph(store.path(session.session_id))
        graph.add_node(GraphNode("eu_1", "agent", "x", None))
        graph.add_node(GraphNode("eu_2", "tool", "x", "eu_1"))
        reloaded = ExecutionGraph(store.path(session.session_id))
        self.assertEqual(len(reloaded.nodes), 2)


class BillingGuCountTest(unittest.TestCase):
    def test_count_governance_units_from_events(self) -> None:
        import sys

        repo = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(repo / "web" / "backend"))
        from app.billing import count_governance_units

        events = [
            {
                "eventType": "ExecutionUnitStarted",
                "payload": {"executionUnit": {"guCost": 1}},
            },
            {
                "eventType": "ExecutionUnitStarted",
                "payload": {"executionUnit": {"guCost": 3}},
            },
            {"eventType": "Completed", "payload": {}},
        ]
        self.assertEqual(count_governance_units(events), 4)


if __name__ == "__main__":
    unittest.main()
