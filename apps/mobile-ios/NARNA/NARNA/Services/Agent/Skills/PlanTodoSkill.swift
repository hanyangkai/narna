//
//  PlanTodoSkill.swift
//  NARNA
//
//  On-device to-do / plan list for multi-step work.
//

import Foundation

actor TodoStore {
    static let shared = TodoStore()

    struct Item: Codable, Equatable, Identifiable {
        var id: UUID = UUID()
        var title: String
        var done: Bool = false
        var createdAt: Date = Date()
    }

    private var items: [Item] = []
    private let url: URL
    private var loaded = false

    init(fileURL: URL? = nil) {
        if let fileURL {
            url = fileURL
        } else {
            let dir = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
                ?? FileManager.default.temporaryDirectory
            let folder = dir.appendingPathComponent("NanaAI", isDirectory: true)
            try? FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
            url = folder.appendingPathComponent("todos.json")
        }
    }

    private func ensureLoaded() {
        guard !loaded else { return }
        loaded = true
        guard let data = try? Data(contentsOf: url),
              let decoded = try? JSONDecoder().decode([Item].self, from: data) else { return }
        items = decoded
    }

    private func persist() {
        guard let data = try? JSONEncoder().encode(items) else { return }
        try? data.write(to: url, options: .atomic)
    }

    func list(includeDone: Bool) -> [Item] {
        ensureLoaded()
        return items.filter { includeDone || !$0.done }
    }

    func add(_ title: String) -> Item {
        ensureLoaded()
        let item = Item(title: title)
        items.append(item)
        persist()
        return item
    }

    func addMany(_ titles: [String]) -> [Item] {
        titles.map { add($0) }
    }

    func setDone(id: UUID, done: Bool) -> Item? {
        ensureLoaded()
        guard let idx = items.firstIndex(where: { $0.id == id }) else { return nil }
        items[idx].done = done
        persist()
        return items[idx]
    }

    func clearCompleted() -> Int {
        ensureLoaded()
        let before = items.count
        items.removeAll { $0.done }
        persist()
        return before - items.count
    }

    func resetForTests() {
        items = []
        loaded = true
        persist()
    }
}

struct PlanTodoSkill: SkillHandler {
    let store: TodoStore

    init(store: TodoStore = .shared) {
        self.store = store
    }

    var definition: SkillDefinition {
        SkillDefinition(
            name: "plan_todo",
            description: "Manage an on-device to-do / plan list. Actions: list, add, add_many, complete, clear_done. Use add_many to break a goal into steps.",
            parameters: SkillJSONSchema(
                properties: [
                    "action": SkillJSONProperty(type: "string", description: "list | add | add_many | complete | clear_done",
                                                enum: ["list", "add", "add_many", "complete", "clear_done"]),
                    "title": SkillJSONProperty(type: "string", description: "Single task title (add)"),
                    "titles": SkillJSONProperty(type: "string", description: "Newline- or | -separated titles (add_many)"),
                    "id": SkillJSONProperty(type: "string", description: "Task UUID (complete)"),
                    "include_done": SkillJSONProperty(type: "boolean", description: "Include completed items when listing"),
                ],
                required: ["action"]
            ),
            location: .onDevice,
            permission: .none,
            displayName: "Plan / To-do"
        )
    }

    func run(arguments: [String: SkillJSONValue]) async -> SkillResult {
        let action = (arguments["action"]?.stringValue ?? "list").lowercased()
        switch action {
        case "list":
            let include = arguments["include_done"]?.boolValue ?? false
            let items = await store.list(includeDone: include)
            if items.isEmpty { return .success("To-do list is empty.") }
            let lines = items.map { "\($0.done ? "✓" : "○") \($0.title) (\($0.id.uuidString.prefix(8)))" }
            return .success(lines.joined(separator: "\n"), data: ["count": .number(Double(items.count))])
        case "add":
            guard let title = arguments["title"]?.stringValue?.trimmingCharacters(in: .whitespacesAndNewlines),
                  !title.isEmpty else { return .failure("Missing title.") }
            let item = await store.add(title)
            return .success("Added: \(item.title)", data: ["id": .string(item.id.uuidString)])
        case "add_many":
            let raw = arguments["titles"]?.stringValue ?? ""
            let titles = raw
                .components(separatedBy: CharacterSet(charactersIn: "|\n"))
                .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
                .filter { !$0.isEmpty }
            guard !titles.isEmpty else { return .failure("Provide titles separated by newlines or |.") }
            let items = await store.addMany(titles)
            let lines = items.map { "○ \($0.title)" }
            return .success("Added \(items.count) tasks:\n" + lines.joined(separator: "\n"))
        case "complete":
            guard let id = arguments["id"]?.stringValue.flatMap(UUID.init(uuidString:)),
                  let item = await store.setDone(id: id, done: true) else {
                return .failure("Task not found.")
            }
            return .success("Completed: \(item.title)")
        case "clear_done":
            let n = await store.clearCompleted()
            return .success("Removed \(n) completed task(s).")
        default:
            return .failure("Unknown action.")
        }
    }
}
