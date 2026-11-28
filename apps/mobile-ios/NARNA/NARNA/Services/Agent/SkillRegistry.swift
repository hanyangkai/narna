//
//  SkillRegistry.swift
//  NARNA
//
//  Declarative registry of Nana AI skills. Handlers are injectable for tests.
//

import Foundation

final class SkillRegistry: @unchecked Sendable {
    static let shared = SkillRegistry.makeDefault()

    private var handlers: [String: any SkillHandler]
    private let lock = NSLock()

    init(handlers: [any SkillHandler] = []) {
        var map: [String: any SkillHandler] = [:]
        for h in handlers { map[h.definition.name] = h }
        self.handlers = map
    }

    static func makeDefault() -> SkillRegistry {
        SkillRegistry(handlers: [
            WebLookupSkill(),
            ResearchSkill(),
            SummarizeSkill(),
            DraftTextSkill(),
            TranslateSkill(),
            PlanTodoSkill(),
            CalculateSkill(),
            CalendarEventSkill(),
            ReminderSkill(),
            NotesSkill(),
            ImageDescribeSkill(),
            DocumentQASkill(),
        ])
    }

    var allDefinitions: [SkillDefinition] {
        lock.lock(); defer { lock.unlock() }
        return handlers.values.map(\.definition).sorted { $0.name < $1.name }
    }

    var count: Int {
        lock.lock(); defer { lock.unlock() }
        return handlers.count
    }

    func definition(named name: String) -> SkillDefinition? {
        lock.lock(); defer { lock.unlock() }
        return handlers[name]?.definition
    }

    func handler(named name: String) -> (any SkillHandler)? {
        lock.lock(); defer { lock.unlock() }
        return handlers[name]
    }

    func register(_ handler: any SkillHandler) {
        lock.lock(); defer { lock.unlock() }
        handlers[handler.definition.name] = handler
    }

    func toolDescriptors() -> [SkillToolDescriptor] {
        allDefinitions.map(\.toolDescriptor)
    }

    /// OpenAI-compatible tools array for native tool calling when a provider supports it.
    func openAIToolsJSON() -> [[String: Any]] {
        toolDescriptors().compactMap { desc in
            guard let data = try? JSONEncoder().encode(desc),
                  let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return nil }
            return obj
        }
    }
}
