import XCTest
@testable import NARNA

private final class FakeEventKit: EventKitGateway, @unchecked Sendable {
    var allowCal = true
    var allowRem = true
    var events: [(title: String, start: Date, end: Date)] = []
    var reminders: [(title: String, completed: Bool, due: Date?)] = []

    func requestCalendarAccess() async -> Bool { allowCal }
    func requestRemindersAccess() async -> Bool { allowRem }
    func createEvent(title: String, start: Date, end: Date, notes: String?) throws -> String {
        events.append((title, start, end))
        return "evt-\(events.count)"
    }
    func listEvents(from: Date, to: Date) throws -> [(title: String, start: Date, end: Date)] { events }
    func createReminder(title: String, due: Date?) throws -> String {
        reminders.append((title, false, due))
        return "rem-\(reminders.count)"
    }
    func listReminders() async throws -> [(title: String, completed: Bool, due: Date?)] { reminders }
}

private struct FakeImageAnalyzer: ImageAnalyzing {
    func describe(imageData: Data) async throws -> (labels: [String], text: String) {
        ("cat (90%)", "hello")
    }
}

private struct FakeDocExtractor: DocumentTextExtracting {
    let text: String
    func extractText(fromFilePath path: String, maxChars: Int) throws -> String {
        String(text.prefix(maxChars))
    }
}

final class SkillHandlerTests: XCTestCase {

    // MARK: calculate

    func testCalculateBasicAndSafety() async {
        let skill = CalculateSkill()
        let ok = await skill.run(arguments: ["expression": .string("(12.5 + 3) * 2")])
        XCTAssertTrue(ok.ok)
        XCTAssertEqual(ok.summary, "31")

        let bad = await skill.run(arguments: ["expression": .string("2 + system('rm')")])
        XCTAssertFalse(bad.ok)

        let div0 = await skill.run(arguments: ["expression": .string("1/0")])
        XCTAssertFalse(div0.ok)

        XCTAssertEqual(try CalculateSkill.evaluate("2^3"), 8, accuracy: 0.0001)
        XCTAssertTrue(CalculateSkill.isSafeExpression("1+2*3"))
        XCTAssertFalse(CalculateSkill.isSafeExpression("1+abc"))
    }

    // MARK: notes

    func testNotesCRUD() async {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("notes-\(UUID().uuidString).json")
        let store = NotesStore(fileURL: url)
        let skill = NotesSkill(store: store)
        let saved = await skill.run(arguments: [
            "action": .string("save"),
            "title": .string("Idea"),
            "body": .string("Ship skills"),
        ])
        XCTAssertTrue(saved.ok)
        let id = saved.data?["id"]?.stringValue
        XCTAssertNotNil(id)

        let listed = await skill.run(arguments: ["action": .string("list")])
        XCTAssertTrue(listed.summary.contains("Idea"))

        let got = await skill.run(arguments: ["action": .string("get"), "id": .string(id!)])
        XCTAssertTrue(got.ok)
        XCTAssertEqual(got.detail, "Ship skills")

        let deleted = await skill.run(arguments: ["action": .string("delete"), "id": .string(id!)])
        XCTAssertTrue(deleted.ok)
    }

    // MARK: plan_todo

    func testPlanTodoAddManyAndComplete() async {
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("todos-\(UUID().uuidString).json")
        let store = TodoStore(fileURL: url)
        let skill = PlanTodoSkill(store: store)
        let added = await skill.run(arguments: [
            "action": .string("add_many"),
            "titles": .string("Research|Draft|Send"),
        ])
        XCTAssertTrue(added.ok)
        XCTAssertTrue(added.summary.contains("Research"))

        let listed = await skill.run(arguments: ["action": .string("list")])
        XCTAssertTrue(listed.summary.contains("○"))
        // complete first via id from add
        let one = await store.add("Solo")
        let done = await skill.run(arguments: ["action": .string("complete"), "id": .string(one.id.uuidString)])
        XCTAssertTrue(done.ok)
        let cleared = await skill.run(arguments: ["action": .string("clear_done")])
        XCTAssertTrue(cleared.ok)
    }

    // MARK: summarize / draft

    func testSummarizeAndDraft() async {
        let text = "First sentence is important. Second provides detail. Third is filler. Fourth wraps up."
        let sum = await SummarizeSkill().run(arguments: ["text": .string(text), "max_sentences": .number(2)])
        XCTAssertTrue(sum.ok)
        XCTAssertTrue(sum.summary.contains("•"))

        let draft = await DraftTextSkill().run(arguments: [
            "brief": .string("Please send the invoice."),
            "style": .string("email"),
            "recipient": .string("Alex"),
        ])
        XCTAssertTrue(draft.summary.contains("Hi Alex,"))
        XCTAssertTrue(draft.summary.contains("Best regards"))
    }

    // MARK: translate (validation / rate limit without network success required)

    func testTranslateValidation() async {
        let skill = TranslateSkill()
        let missing = await skill.run(arguments: ["text": .string("hi")])
        XCTAssertFalse(missing.ok)
        let badPair = await skill.run(arguments: ["text": .string("hi"), "langpair": .string("enes")])
        XCTAssertFalse(badPair.ok)
    }

    // MARK: web_lookup / research validation

    func testWebLookupRequiresQuery() async {
        let miss = await WebLookupSkill().run(arguments: [:])
        XCTAssertFalse(miss.ok)
        let researchMiss = await ResearchSkill().run(arguments: [:])
        XCTAssertFalse(researchMiss.ok)
    }

    // MARK: calendar / reminder

    func testCalendarAndReminderWithFakeGateway() async {
        let gate = FakeEventKit()
        let cal = CalendarEventSkill(gateway: gate)
        let start = ISO8601DateFormatter().string(from: Date())
        let end = ISO8601DateFormatter().string(from: Date().addingTimeInterval(3600))
        let created = await cal.run(arguments: [
            "action": .string("create"),
            "title": .string("Standup"),
            "start": .string(start),
            "end": .string(end),
        ])
        XCTAssertTrue(created.ok)

        let listed = await cal.run(arguments: ["action": .string("list")])
        XCTAssertTrue(listed.summary.contains("Standup"))

        let rem = ReminderSkill(gateway: gate)
        let r = await rem.run(arguments: ["action": .string("create"), "title": .string("Buy milk")])
        XCTAssertTrue(r.ok)
        let rList = await rem.run(arguments: ["action": .string("list")])
        XCTAssertTrue(rList.summary.contains("Buy milk"))

        gate.allowCal = false
        let denied = await cal.run(arguments: ["action": .string("list")])
        XCTAssertFalse(denied.ok)
    }

    // MARK: image

    func testDescribeImageWithAnalyzer() async {
        let skill = ImageDescribeSkill(analyzer: FakeImageAnalyzer())
        let miss = await skill.run(arguments: [:])
        XCTAssertFalse(miss.ok)
        let ok = await skill.run(arguments: ["base64": .string(Data("fake".utf8).base64EncodedString())])
        XCTAssertTrue(ok.ok)
        XCTAssertTrue(ok.summary.contains("cat"))
        XCTAssertTrue(ok.summary.contains("hello"))
    }

    // MARK: document_qa

    func testDocumentQAKeywordAnswer() async {
        let doc = """
        NARNA ships ADQA for decision quality.

        The mobile app runs Nana AI on iPhone with a free model pool.
        """
        let skill = DocumentQASkill(extractor: FakeDocExtractor(text: doc))
        let ans = await skill.run(arguments: [
            "file_path": .string("/tmp/fake.pdf"),
            "question": .string("What does the mobile app run?"),
        ])
        XCTAssertTrue(ans.ok)
        XCTAssertTrue(ans.summary.lowercased().contains("nana") || ans.summary.lowercased().contains("iphone") || ans.summary.lowercased().contains("mobile"))

        let scored = DocumentQASkill.answer(question: "decision quality", document: doc)
        XCTAssertTrue(scored.lowercased().contains("adqa") || scored.lowercased().contains("decision"))
    }

    // MARK: rate limit cache

    func testRateLimitCache() async {
        let cache = RateLimitCache()
        await cache.resetForTests()
        XCTAssertTrue(await cache.consume(bucket: "t", cost: 5, capacity: 5, refillPerSecond: 0))
        XCTAssertFalse(await cache.consume(bucket: "t", cost: 1, capacity: 5, refillPerSecond: 0))
        await cache.set("k", value: "v", ttl: 60)
        XCTAssertEqual(await cache.get("k"), "v")
    }
}
