import XCTest
@testable import NARNA

final class AgentExecutorTests: XCTestCase {

    func testRunsIndependentTasksAndComposesAnswer() async {
        let reg = SkillRegistry(handlers: [CalculateSkill(), SummarizeSkill()])
        let draft = AgentPlanDraft(steps: [
            .init(skill: "calculate", arguments: ["expression": .string("2+3")], parallelGroup: 0),
            .init(skill: "summarize", arguments: ["text": .string("Hello world. Second sentence.")], parallelGroup: 0),
        ], finalAnswerHint: "Done.")
        let exec = AgentExecutor(registry: reg, maxConcurrent: 2)
        let snap = await exec.runToCompletion(draft)
        XCTAssertTrue(snap.isComplete)
        XCTAssertEqual(snap.tasks.count, 2)
        XCTAssertTrue(snap.tasks.allSatisfy { $0.status == .succeeded })
        XCTAssertTrue(snap.finalAnswer?.contains("Done.") == true)
        XCTAssertTrue(snap.finalAnswer?.contains("5") == true)
    }

    func testSequentialGroups() async {
        let reg = SkillRegistry(handlers: [CalculateSkill()])
        let draft = AgentPlanDraft(steps: [
            .init(skill: "calculate", arguments: ["expression": .string("1+1")], parallelGroup: 0),
            .init(skill: "calculate", arguments: ["expression": .string("3*3")], parallelGroup: 1),
        ], finalAnswerHint: nil)
        let exec = AgentExecutor(registry: reg, maxConcurrent: 1)
        var statuses: [[AgentTaskStatus]] = []
        for await snap in exec.run(draft) {
            statuses.append(snap.tasks.map(\.status))
        }
        XCTAssertFalse(statuses.isEmpty)
        let last = statuses.last!
        XCTAssertEqual(last, [.succeeded, .succeeded])
    }

    func testUnknownSkillFailsTask() async {
        let reg = SkillRegistry(handlers: [CalculateSkill()])
        let draft = AgentPlanDraft(steps: [
            .init(skill: "nope", arguments: [:], parallelGroup: 0),
        ], finalAnswerHint: nil)
        let snap = await AgentExecutor(registry: reg).runToCompletion(draft)
        XCTAssertEqual(snap.tasks.first?.status, .failed)
    }

    func testEmptyPlanCompletes() async {
        let snap = await AgentExecutor(registry: SkillRegistry(handlers: [])).runToCompletion(
            AgentPlanDraft(steps: [], finalAnswerHint: "nothing")
        )
        XCTAssertTrue(snap.isComplete)
        XCTAssertEqual(snap.finalAnswer, "nothing")
    }
}
