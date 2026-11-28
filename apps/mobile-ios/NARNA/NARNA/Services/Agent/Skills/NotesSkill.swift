//
//  NotesSkill.swift
//  NARNA
//
//  Local on-device notes store (Application Support). No cloud sync, no keys.
//

import Foundation

actor NotesStore {
    static let shared = NotesStore()

    struct Note: Codable, Equatable, Identifiable {
        var id: UUID = UUID()
        var title: String
        var body: String
        var updatedAt: Date = Date()
    }

    private var notes: [Note] = []
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
            url = folder.appendingPathComponent("notes.json")
        }
    }

    private func ensureLoaded() {
        guard !loaded else { return }
        loaded = true
        guard let data = try? Data(contentsOf: url),
              let decoded = try? JSONDecoder().decode([Note].self, from: data) else { return }
        notes = decoded
    }

    private func persist() {
        guard let data = try? JSONEncoder().encode(notes) else { return }
        try? data.write(to: url, options: .atomic)
    }

    func list() -> [Note] {
        ensureLoaded()
        return notes.sorted { $0.updatedAt > $1.updatedAt }
    }

    func save(title: String, body: String, id: UUID? = nil) -> Note {
        ensureLoaded()
        if let id, let idx = notes.firstIndex(where: { $0.id == id }) {
            notes[idx].title = title
            notes[idx].body = body
            notes[idx].updatedAt = Date()
            persist()
            return notes[idx]
        }
        let note = Note(title: title, body: body)
        notes.append(note)
        persist()
        return note
    }

    func get(id: UUID) -> Note? {
        ensureLoaded()
        return notes.first { $0.id == id }
    }

    func delete(id: UUID) -> Bool {
        ensureLoaded()
        let before = notes.count
        notes.removeAll { $0.id == id }
        persist()
        return notes.count < before
    }

    func resetForTests() {
        notes = []
        loaded = true
        persist()
    }
}

struct NotesSkill: SkillHandler {
    let store: NotesStore

    init(store: NotesStore = .shared) {
        self.store = store
    }

    var definition: SkillDefinition {
        SkillDefinition(
            name: "notes",
            description: "Create, list, read, or delete private on-device notes. Actions: list, save, get, delete.",
            parameters: SkillJSONSchema(
                properties: [
                    "action": SkillJSONProperty(type: "string", description: "list | save | get | delete", enum: ["list", "save", "get", "delete"]),
                    "title": SkillJSONProperty(type: "string", description: "Note title (save)"),
                    "body": SkillJSONProperty(type: "string", description: "Note body (save)"),
                    "id": SkillJSONProperty(type: "string", description: "Note UUID (get/delete)"),
                ],
                required: ["action"]
            ),
            location: .onDevice,
            permission: .none,
            displayName: "Notes"
        )
    }

    func run(arguments: [String: SkillJSONValue]) async -> SkillResult {
        let action = (arguments["action"]?.stringValue ?? "list").lowercased()
        switch action {
        case "list":
            let items = await store.list()
            if items.isEmpty { return .success("No notes yet.") }
            let lines = items.prefix(20).map { "• \($0.title) (\($0.id.uuidString.prefix(8)))" }
            return .success(lines.joined(separator: "\n"), data: [
                "count": .number(Double(items.count)),
            ])
        case "save":
            let title = arguments["title"]?.stringValue?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            let body = arguments["body"]?.stringValue ?? ""
            guard !title.isEmpty || !body.isEmpty else { return .failure("Provide title or body.") }
            let id = arguments["id"]?.stringValue.flatMap(UUID.init(uuidString:))
            let note = await store.save(title: title.isEmpty ? String(body.prefix(40)) : title, body: body, id: id)
            return .success("Saved note “\(note.title)”.", detail: note.body, data: [
                "id": .string(note.id.uuidString),
            ])
        case "get":
            guard let id = arguments["id"]?.stringValue.flatMap(UUID.init(uuidString:)),
                  let note = await store.get(id: id) else {
                return .failure("Note not found.")
            }
            return .success(note.title, detail: note.body, data: ["id": .string(note.id.uuidString)])
        case "delete":
            guard let id = arguments["id"]?.stringValue.flatMap(UUID.init(uuidString:)) else {
                return .failure("Missing note id.")
            }
            let ok = await store.delete(id: id)
            return ok ? .success("Deleted note.") : .failure("Note not found.")
        default:
            return .failure("Unknown action. Use list, save, get, or delete.")
        }
    }
}
