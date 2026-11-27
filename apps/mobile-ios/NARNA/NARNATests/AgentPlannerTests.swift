import XCTest
@testable import NARNA

private struct ScriptedLLM: AgentLLMCompleting {
    let reply: String
    func complete(system: String, user: String) async throws -> String { reply }
}

final class AgentPlannerTests: XCTestCase {
    private var registry: SkillRegistry!

    override func setUp() {
        registry = SkillRegistry.makeDefault()
    }

    func testShouldUseAgentTriggers() {
        XCTAssertTrue(AgentPlanner.shouldUseAgent(for: "Research decision quality"))
        XCTAssertTrue(AgentPlanner.shouldUseAgent(for: "Calculate 2+2"))
        XCTAssertTrue(AgentPlanner.shouldUseAgent(for: "1. Translate hi\n2. Save a note"))
        XCTAssertFalse(AgentPlanner.shouldUseAgent(for: "Hi"))
    }

    func testHeuristicCalculate() async {
        let planner = AgentPlanner(registry: registry, llm: nil)
        let plan = await planner.plan(userMessage: "Calculate (10 + 2) * 3")
        XCTAssertEqual(plan.steps.count, 1)
        XCTAssertEqual(plan.steps[0].skill, "calculate")
    }

    func testHeuristicMultiStepQueue() async {
        let planner = AgentPlanner(registry: registry, llm: nil)
        let plan = await planner.plan(userMessage: """
        1. Calculate 2+2
        2. Add a to-do to review the answer
        """)
        XCTAssertGreaterThanOrEqual(plan.steps.count, 2)
        XCTAssertEqual(plan.steps[0].skill, "calculate")
        XCTAssertTrue(plan.steps.contains(where: { $0.skill == "plan_todo" }))
        // Different parallel groups for sequential numbered tasks
        XCTAssertNotEqual(plan.steps[0].parallelGroup, plan.steps[1].parallelGroup)
    }

    func testLLMPlanPreferredOverHeuristic() async {
        let scripted = ScriptedLLM(reply: #"{"steps":[{"skill":"summarize","arguments":{"text":"abc"},"parallel_group":0}]}"#)
        let planner = AgentPlanner(registry: registry, llm: scripted)
        let plan = await planner.plan(userMessage: "Calculate 1+1")
        XCTAssertEqual(plan.steps.count, 1)
        XCTAssertEqual(plan.steps[0].skill, "summarize")
    }

    func testUnknownSkillsDropped() async {
        let scripted = ScriptedLLM(reply: #"{"steps":[{"skill":"hack_the_planet","arguments":{},"parallel_group":0},{"skill":"calculate","arguments":{"expression":"1"},"parallel_group":0}]}"#)
        let planner = AgentPlanner(registry: registry, llm: scripted)
        let plan = await planner.plan(userMessage: "do stuff")
        XCTAssertEqual(plan.steps.map(\.skill), ["calculate"])
    }

    func testMaxStepsClamp() async {
        let steps = (0..<20).map { i in
            #"{"skill":"calculate","arguments":{"expression":"\#(i)"},"parallel_group":\#(i)}"#
        }.joined(separator: ",")
        let scripted = ScriptedLLM(reply: "{\"steps\":[\(steps)]}")
        let planner = AgentPlanner(registry: registry, llm: scripted, maxSteps: 5)
        let plan = await planner.plan(userMessage: "many")
        XCTAssertEqual(plan.steps.count, 5)
    }

    func testSplitTasks() {
        let parts = AgentPlanner.splitTasks("1. Alpha\n2. Beta\n3. Gamma")
        XCTAssertEqual(parts.count, 3)
        XCTAssertEqual(parts[0], "Alpha")
    }
}
