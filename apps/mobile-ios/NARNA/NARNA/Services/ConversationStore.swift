//
//  ConversationStore.swift
//  NARNA
//
//  Conversations are stored only on this device (Application Support, JSON,
//  file protection: complete until first user authentication).
//

import Foundation
import Combine

@MainActor
final class ConversationStore: ObservableObject {
    static let shared = ConversationStore()

    @Published private(set) var conversations: [Conversation] = []

    private let fileURL: URL

    private init() {
        let dir = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("NaNaBot", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        var u = dir.appendingPathComponent("conversations.json")
        var rv = URLResourceValues()
        rv.isExcludedFromBackup = false
        try? u.setResourceValues(rv)
        fileURL = u
        load()
        #if DEBUG
        if ProcessInfo.processInfo.arguments.contains("-NARNA_DEMO_SEED") { seedDemo() }
        #endif
    }

    var sorted: [Conversation] { conversations.sorted { $0.updatedAt > $1.updatedAt } }

    func sorted(for botID: UUID) -> [Conversation] {
        conversations.filter { $0.botID == botID }.sorted { $0.updatedAt > $1.updatedAt }
    }

    func conversation(_ id: UUID?) -> Conversation? {
        guard let id else { return nil }
        return conversations.first { $0.id == id }
    }

    @discardableResult
    func create(provider: String?, model: String?, botID: UUID = ChatBot.chiefOfStaffID) -> Conversation {
        let c = Conversation(botID: botID, provider: provider, model: model)
        conversations.append(c)
        save()
        return c
    }

    func update(_ c: Conversation) {
        guard let i = conversations.firstIndex(where: { $0.id == c.id }) else {
            conversations.append(c); save(); return
        }
        conversations[i] = c
        save()
    }

    func delete(_ id: UUID) {
        conversations.removeAll { $0.id == id }
        save()
    }

    func deleteAll() {
        conversations.removeAll()
        save()
    }

    func deleteAll(for botID: UUID) {
        conversations.removeAll { $0.botID == botID }
        save()
    }

    private func load() {
        guard let data = try? Data(contentsOf: fileURL) else { return }
        let dec = JSONDecoder()
        dec.dateDecodingStrategy = .iso8601
        conversations = (try? dec.decode([Conversation].self, from: data)) ?? []
    }

    private func save() {
        let enc = JSONEncoder()
        enc.dateEncodingStrategy = .iso8601
        guard let data = try? enc.encode(conversations) else { return }
        try? data.write(to: fileURL, options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
    }

    #if DEBUG
    private func seedDemo() {
        guard conversations.isEmpty else { return }
        let now = Date()
        let samples: [(String, String, TimeInterval)] = [
            ("Should we switch CI providers?", "Run a 2-week pilot before switching the whole team.", 600),
            ("Draft a polite reply to a late invoice", "Here is a short, friendly reminder you can send…", 7200),
            ("Compare two laptop options for travel", "For travel, the lighter model wins on battery…", 86400),
            ("Summarize this contract clause", "The clause limits liability to fees paid in 12 months…", 172800)
        ]
        for (q, a, ago) in samples {
            var c = Conversation(title: q, createdAt: now.addingTimeInterval(-ago), updatedAt: now.addingTimeInterval(-ago))
            c.messages = [AIMessage(role: .user, content: q), AIMessage(role: .assistant, content: a)]
            conversations.append(c)
        }
        save()
    }
    #endif
}
