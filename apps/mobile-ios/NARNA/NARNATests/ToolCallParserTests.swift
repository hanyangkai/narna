import XCTest
@testable import NARNA

final class ToolCallParserTests: XCTestCase {

    func testParseJSONToolCalls() {
        let text = #"{"tool_calls":[{"name":"calculate","arguments":{"expression":"1+2"}}]}"#
        let calls = ToolCallParser.parse(text)
        XCTAssertEqual(calls.count, 1)
        XCTAssertEqual(calls[0].name, "calculate")
        XCTAssertEqual(calls[0].arguments["expression"]?.stringValue, "1+2")
    }

    func testParseFencedStepsPlan() {
        let text = """
        ```json
        {"steps":[{"skill":"web_lookup","arguments":{"query":"ADQA"},"parallel_group":0},{"skill":"summarize","arguments":{"text":"x"},"parallel_group":1}]}
        ```
        """
        let plan = ToolCallParser.parsePlan(text)
        XCTAssertEqual(plan?.steps.count, 2)
        XCTAssertEqual(plan?.steps[0].skill, "web_lookup")
        XCTAssertEqual(plan?.steps[1].parallelGroup, 1)
    }

    func testParseOpenAIEnvelope() {
        let text = """
        {"choices":[{"message":{"tool_calls":[{"id":"1","type":"function","function":{"name":"notes","arguments":"{\\"action\\":\\"list\\"}"}}]}}]}
        """
        let calls = ToolCallParser.parse(text)
        XCTAssertEqual(calls.count, 1)
        XCTAssertEqual(calls[0].name, "notes")
        XCTAssertEqual(calls[0].arguments["action"]?.stringValue, "list")
    }

    func testProseWithoutToolsReturnsEmpty() {
        XCTAssertTrue(ToolCallParser.parse("Hello, how can I help?").isEmpty)
        XCTAssertNil(ToolCallParser.parsePlan("Just a chat reply."))
    }

    func testJsonToolPromptIncludesCatalog() {
        let skills = SkillRegistry.makeDefault().allDefinitions
        let prompt = ToolCallParser.jsonToolPrompt(skills: skills)
        XCTAssertTrue(prompt.contains("calculate"))
        XCTAssertTrue(prompt.contains("tool_calls"))
    }
}
