import XCTest
@testable import NARNA

final class SkillRegistryTests: XCTestCase {

    func testDefaultRegistryHasAtLeastTwelveSkills() {
        let reg = SkillRegistry.makeDefault()
        XCTAssertGreaterThanOrEqual(reg.count, 12)
        let names = Set(reg.allDefinitions.map(\.name))
        for required in [
            "web_lookup", "research", "summarize", "draft_text", "translate",
            "plan_todo", "calculate", "calendar_event", "reminder", "notes",
            "describe_image", "document_qa",
        ] {
            XCTAssertTrue(names.contains(required), "Missing skill \(required)")
        }
    }

    func testDefinitionsExposeToolDescriptors() {
        let reg = SkillRegistry.makeDefault()
        let tools = reg.toolDescriptors()
        XCTAssertEqual(tools.count, reg.count)
        XCTAssertTrue(tools.allSatisfy { $0.type == "function" })
        XCTAssertTrue(tools.allSatisfy { !$0.function.name.isEmpty })
        XCTAssertTrue(tools.allSatisfy { !$0.function.parameters.properties.isEmpty || $0.function.name == "describe_image" })
    }

    func testOpenAIToolsJSONSerializable() {
        let json = SkillRegistry.makeDefault().openAIToolsJSON()
        XCTAssertGreaterThanOrEqual(json.count, 12)
        XCTAssertEqual(json.first?["type"] as? String, "function")
    }

    func testRegisterOverridesHandler() {
        struct Stub: SkillHandler {
            let definition = SkillDefinition(
                name: "calculate",
                description: "stub",
                parameters: SkillJSONSchema(properties: [:]),
                location: .onDevice,
                permission: .none,
                displayName: "Stub"
            )
            func run(arguments: [String: SkillJSONValue]) async -> SkillResult {
                .success("stub")
            }
        }
        let reg = SkillRegistry(handlers: [CalculateSkill()])
        XCTAssertEqual(reg.definition(named: "calculate")?.displayName, "Calculate")
        reg.register(Stub())
        XCTAssertEqual(reg.definition(named: "calculate")?.displayName, "Stub")
    }

    func testPermissionAnnotations() {
        let reg = SkillRegistry.makeDefault()
        XCTAssertEqual(reg.definition(named: "calendar_event")?.permission, .calendars)
        XCTAssertEqual(reg.definition(named: "reminder")?.permission, .reminders)
        XCTAssertEqual(reg.definition(named: "describe_image")?.permission, .photoLibrary)
        XCTAssertEqual(reg.definition(named: "calculate")?.permission, SkillPermission.none)
        XCTAssertEqual(reg.definition(named: "web_lookup")?.location, .networkFree)
        XCTAssertEqual(reg.definition(named: "notes")?.location, .onDevice)
    }
}
