//
//  AIChatViewModel.swift
//  NARNA
//

import Foundation
import Combine

enum MainTab: Hashable {
    case chat, history, desktop, settings
}

@MainActor
final class AppState: ObservableObject {
    static let shared = AppState()
    @Published var selectedTab: MainTab = .chat
    @Published var currentConversationID: UUID?
    @Published var isPaired: Bool = KeychainService.shared.getMobileToken() != nil

    func refreshPairing() {
        isPaired = KeychainService.shared.getMobileToken() != nil
    }

    func unpair() {
        KeychainService.shared.clearAll()
        isPaired = false
        if selectedTab == .desktop { selectedTab = .settings }
    }
}

@MainActor
final class AIChatViewModel: ObservableObject {
    @Published var input: String = ""
    @Published var isSending = false
    @Published var scoringIDs: Set<UUID> = []

    private let store = ConversationStore.shared
    private let settings = LLMSettings.shared
    private let app = AppState.shared

    static let systemPrompt = """
    You are NaNa Bot, a helpful, concise AI assistant running on the user's iPhone with the user's own API key. \
    Answer clearly. Use short paragraphs, bullet points and **bold** for key points when helpful. \
    When you give a recommendation or decision, state your assumptions and the main risks. \
    For medical, legal or financial topics, remind the user to verify with a qualified professional.
    """

    var conversation: Conversation? { store.conversation(app.currentConversationID) }

    var canSend: Bool {
        !input.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !isSending
    }

    func newChat() {
        app.currentConversationID = nil
        input = ""
    }

    private func config() throws -> LLMRequestConfig {
        guard let key = settings.apiKey ?? (LLMService.shared.isMockMode ? "mock" : nil) else { throw LLMError.missingKey }
        if settings.provider == .openaiCompatible, URL(string: settings.baseURL)?.scheme?.hasPrefix("http") != true {
            throw LLMError.invalidBaseURL
        }
        return LLMRequestConfig(provider: settings.provider, model: settings.model.trimmingCharacters(in: .whitespaces),
                                baseURL: settings.baseURL, apiKey: key)
    }

    func send() {
        let text = input.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !isSending else { return }
        input = ""

        var convo = conversation ?? store.create(provider: settings.provider.rawValue, model: settings.model)
        app.currentConversationID = convo.id
        if convo.messages.isEmpty {
            convo.title = String(text.prefix(60))
        }
        convo.messages.append(AIMessage(role: .user, content: text))
        convo.updatedAt = Date()
        store.update(convo)
        Task { await respond(conversationID: convo.id, question: text) }
    }

    func retry(errorMessageID: UUID) {
        guard var convo = conversation,
              let idx = convo.messages.firstIndex(where: { $0.id == errorMessageID }) else { return }
        convo.messages.remove(at: idx)
        store.update(convo)
        guard let q = convo.messages.last(where: { $0.role == .user })?.content else { return }
        Task { await respond(conversationID: convo.id, question: q) }
    }

    func rescore(messageID: UUID) {
        guard let convo = conversation,
              let idx = convo.messages.firstIndex(where: { $0.id == messageID }) else { return }
        let answer = convo.messages[idx].content
        let q = convo.messages[..<idx].last(where: { $0.role == .user })?.content ?? ""
        let history = turns(Array(convo.messages[..<idx]))
        Task { await score(conversationID: convo.id, messageID: messageID, question: q, answer: answer, history: history) }
    }

    private func turns(_ msgs: [AIMessage]) -> [LLMTurn] {
        msgs.filter { !$0.isError }.suffix(20).map { LLMTurn(role: $0.role, content: $0.content) }
    }

    private func respond(conversationID: UUID, question: String) async {
        isSending = true
        defer { isSending = false }
        guard let convo = store.conversation(conversationID) else { return }
        let history = turns(convo.messages)
        do {
            let cfg = try config()
            let answer = try await LLMService.shared.complete(config: cfg, system: Self.systemPrompt, turns: history)
            guard var c = store.conversation(conversationID) else { return }
            let msg = AIMessage(role: .assistant, content: answer)
            c.messages.append(msg)
            c.updatedAt = Date()
            store.update(c)
            if settings.adqaEnabled {
                await score(conversationID: conversationID, messageID: msg.id, question: question,
                            answer: answer, history: Array(history.dropLast()))
            }
        } catch {
            guard var c = store.conversation(conversationID) else { return }
            c.messages.append(AIMessage(role: .assistant, content: error.localizedDescription, isError: true))
            c.updatedAt = Date()
            store.update(c)
        }
    }

    private func score(conversationID: UUID, messageID: UUID, question: String, answer: String, history: [LLMTurn]) async {
        guard let cfg = try? config() else { return }
        scoringIDs.insert(messageID)
        let result = await ADQA.assess(question: question, answer: answer, history: history, config: cfg)
        scoringIDs.remove(messageID)
        guard var c = store.conversation(conversationID),
              let i = c.messages.firstIndex(where: { $0.id == messageID }) else { return }
        c.messages[i].adqa = result
        store.update(c)
    }
}
