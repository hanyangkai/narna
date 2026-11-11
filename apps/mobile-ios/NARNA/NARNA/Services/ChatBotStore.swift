//
//  ChatBotStore.swift
//  NARNA
//
//  Bot definitions and optional per-bot API keys stay only on this iPhone
//  (Application Support JSON + Keychain). No server.
//

import Foundation
import Combine

@MainActor
final class ChatBotStore: ObservableObject {
    static let shared = ChatBotStore()

    @Published private(set) var bots: [ChatBot] = []

    private let fileURL: URL
    private static let keyPrefix = "chatbot_api_key_"
    static let demoResearchID = UUID(uuidString: "A11A0000-0000-4000-8000-000000000002")!

    func seedDemoBots() {
        #if DEBUG
        if !bots.contains(where: { $0.id == Self.demoResearchID }) {
            upsert(ChatBot(
                id: Self.demoResearchID,
                name: "Research",
                role: "Researcher",
                emoji: "🧪",
                hue: 0.12,
                persona: "You are a careful research assistant. Cite assumptions and flag uncertainty.",
                useGlobalKey: true,
                providerRaw: nil,
                model: nil,
                baseURLOverride: "",
                createdAt: Date(),
                updatedAt: Date(),
                lastViewedAt: nil
            ))
        }
        #endif
    }

    private init() {
        let dir = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("NaNaBot", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        fileURL = dir.appendingPathComponent("chatbots.json")
        load()
    }

    /// Chief of Staff is always first and is never missing.
    var listed: [ChatBot] {
        let users = bots.filter { !$0.isChiefOfStaff }.sorted { $0.updatedAt > $1.updatedAt }
        return [chief] + users
    }

    var chief: ChatBot {
        bots.first(where: { $0.isChiefOfStaff }) ?? ChatBot.chiefOfStaff()
    }

    func bot(_ id: UUID?) -> ChatBot {
        guard let id, let b = bots.first(where: { $0.id == id }) else { return chief }
        return b
    }

    func filtered(query: String) -> [ChatBot] {
        let q = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !q.isEmpty else { return listed }
        return listed.filter {
            $0.name.localizedCaseInsensitiveContains(q)
                || $0.role.localizedCaseInsensitiveContains(q)
                || $0.persona.localizedCaseInsensitiveContains(q)
        }
    }

    @discardableResult
    func upsert(_ bot: ChatBot) -> ChatBot {
        var bot = bot
        bot.updatedAt = Date()
        if let i = bots.firstIndex(where: { $0.id == bot.id }) {
            bots[i] = bot
        } else {
            bots.append(bot)
        }
        save()
        return bot
    }

    func delete(_ id: UUID) {
        guard id != ChatBot.chiefOfStaffID else { return }
        bots.removeAll { $0.id == id }
        KeychainService.shared.deleteAPIKey(account: Self.keyPrefix + id.uuidString)
        save()
        ConversationStore.shared.deleteAll(for: id)
        if AppState.shared.currentBotID == id {
            AppState.shared.currentBotID = ChatBot.chiefOfStaffID
            AppState.shared.currentConversationID = nil
        }
    }

    func markViewed(_ id: UUID) {
        // Don't bump updatedAt: that would reorder the home list on every open.
        guard let i = bots.firstIndex(where: { $0.id == id }) else { return }
        bots[i].lastViewedAt = Date()
        save()
    }

    func setAPIKey(_ key: String?, for id: UUID) {
        let account = Self.keyPrefix + id.uuidString
        if let key, !key.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            KeychainService.shared.saveAPIKey(key.trimmingCharacters(in: .whitespacesAndNewlines), account: account)
        } else {
            KeychainService.shared.deleteAPIKey(account: account)
        }
    }

    func apiKey(for id: UUID) -> String? {
        KeychainService.shared.getAPIKey(account: Self.keyPrefix + id.uuidString)
    }

    private func load() {
        let dec = JSONDecoder()
        dec.dateDecodingStrategy = .iso8601
        if let data = try? Data(contentsOf: fileURL),
           let saved = try? dec.decode([ChatBot].self, from: data) {
            bots = saved.filter { !$0.isChiefOfStaff }
        }
        if !bots.contains(where: { $0.isChiefOfStaff }) {
            bots.insert(ChatBot.chiefOfStaff(), at: 0)
            save()
        }
    }

    private func save() {
        let enc = JSONEncoder()
        enc.dateEncodingStrategy = .iso8601
        // Persist user bots; the Chief of Staff is always re-injected on load.
        let users = bots.filter { !$0.isChiefOfStaff }
        guard let data = try? enc.encode(users) else { return }
        try? data.write(to: fileURL, options: [.atomic, .completeFileProtectionUntilFirstUserAuthentication])
    }
}
