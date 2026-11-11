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
    @Published var currentBotID: UUID = ChatBot.chiefOfStaffID {
        didSet { UserDefaults.standard.set(currentBotID.uuidString, forKey: "current_bot_id") }
    }
    @Published var showBotsList = false
    @Published var isPaired: Bool = KeychainService.shared.getMobileToken() != nil

    private init() {
        if let s = UserDefaults.standard.string(forKey: "current_bot_id"), let id = UUID(uuidString: s) {
            currentBotID = id
        }
        isPaired = KeychainService.shared.getMobileToken() != nil
    }

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
    private let bots = ChatBotStore.shared

    static let systemPrompt = """
    You are NaNa Bot, a helpful, concise AI assistant running on the user's iPhone with the user's own API key. \
    Answer clearly. Use short paragraphs, bullet points and **bold** for key points when helpful. \
    When you give a recommendation or decision, state your assumptions and the main risks. \
    For medical, legal or financial topics, remind the user to verify with a qualified professional.
    """

    var currentBot: ChatBot { bots.bot(app.currentBotID) }

    var systemPrompt: String {
        let bot = currentBot
        if bot.isChiefOfStaff { return Self.systemPrompt }
        let persona = bot.persona.trimmingCharacters(in: .whitespacesAndNewlines)
        if !persona.isEmpty { return persona }
        return "You are \(bot.name), a helpful assistant on the user's iPhone. Be clear and concise."
    }

    var conversation: Conversation? {
        guard let c = store.conversation(app.currentConversationID), c.botID == app.currentBotID else { return nil }
        return c
    }

    var isReady: Bool {
        if LLMService.shared.isMockMode { return true }
        do { _ = try config(); return true } catch { return false }
    }

    var canSend: Bool {
        !input.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !isSending
    }

    func newChat() {
        app.currentConversationID = nil
        input = ""
    }

    private func config() throws -> LLMRequestConfig {
        let bot = currentBot
        let useGlobal = bot.useGlobalKey || bot.isChiefOfStaff
        let provider = useGlobal ? settings.provider : (bot.provider ?? settings.provider)
        let model = (useGlobal ? settings.model : (bot.model ?? settings.model)).trimmingCharacters(in: .whitespaces)
        let base: String = {
            if !useGlobal {
                let o = bot.baseURLOverride.trimmingCharacters(in: .whitespacesAndNewlines)
                if !o.isEmpty { return o }
            }
            return settings.baseURL
        }()
        let key: String? = {
            if LLMService.shared.isMockMode { return "mock" }
            if !useGlobal, let k = bots.apiKey(for: bot.id), !k.isEmpty { return k }
            return settings.apiKey
        }()
        guard let key, !key.isEmpty else { throw LLMError.missingKey }
        if URL(string: base)?.scheme?.hasPrefix("http") != true {
            throw LLMError.invalidBaseURL
        }
        return LLMRequestConfig(provider: provider, model: model, baseURL: base, apiKey: key)
    }

    var activeModel: String {
        let bot = currentBot
        if bot.useGlobalKey || bot.isChiefOfStaff { return settings.model }
        return (bot.model?.isEmpty == false ? bot.model! : settings.model)
    }

    func send() {
        let text = input.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !isSending else { return }
        input = ""

        var convo = conversation ?? store.create(provider: settings.provider.rawValue, model: activeModel, botID: app.currentBotID)
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
            let answer = try await LLMService.shared.complete(config: cfg, system: systemPrompt, turns: history)
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
