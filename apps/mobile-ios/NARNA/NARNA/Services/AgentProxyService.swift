//
//  AgentProxyService.swift
//  NARNA
//
//  Paid Agent mode: multi-step tasks, files/images, web search, strong models.
//  Requests go only to our backend (AGENT_PROXY_URL). The proxy verifies the
//  StoreKit JWS and enforces per-plan credit caps. No provider keys in the app.
//

import Foundation

struct AgentRequest {
    var system: String
    var turns: [LLMTurn]
    var webSearch: Bool
    var transactionJWS: String
    var fileName: String?
    var fileMIME: String?
    var fileBase64: String?
}

struct AgentReply: Equatable {
    var content: String
    var modelDisplayName: String
    var creditsRemaining: Int
}

enum AgentProxyService {
    static var isConfigured: Bool { AppConfig.isAgentProxyConfigured }

    private static let session: URLSession = {
        let c = URLSessionConfiguration.ephemeral
        c.timeoutIntervalForRequest = 180
        c.urlCache = nil
        return URLSession(configuration: c)
    }()

    static func complete(_ request: AgentRequest) async throws -> AgentReply {
        if LLMService.shared.isMockMode {
            return AgentReply(content: try await MockLLM.reply(system: request.system, turns: request.turns),
                              modelDisplayName: "Agent",
                              creditsRemaining: 199)
        }
        guard let base = AppConfig.agentProxyURL else { throw LLMError.agentNotConfigured }
        let url = base.appendingPathComponent("v1/agent")
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue(request.transactionJWS, forHTTPHeaderField: "X-StoreKit-JWS")

        struct Body: Encodable {
            let system: String
            let messages: [Msg]
            let webSearch: Bool
            let fileName: String?
            let fileMIME: String?
            let fileBase64: String?
            struct Msg: Encodable { let role: String; let content: String }
        }
        let messages = request.turns.map { Body.Msg(role: $0.role == .user ? "user" : "assistant", content: $0.content) }
        req.httpBody = try JSONEncoder().encode(Body(system: request.system, messages: messages,
                                                     webSearch: request.webSearch,
                                                     fileName: request.fileName, fileMIME: request.fileMIME,
                                                     fileBase64: request.fileBase64))
        let data: Data
        let resp: URLResponse
        do {
            (data, resp) = try await session.data(for: req)
        } catch {
            throw LLMError.network(error.localizedDescription)
        }
        let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
        let parsed = (try? JSONSerialization.jsonObject(with: data) as? [String: Any]) ?? [:]
        let errMsg = (parsed["error"] as? String) ?? (parsed["message"] as? String)
        if code == 402 || code == 403 {
            throw LLMError.notSubscribed
        }
        if code == 429 {
            throw LLMError.creditsExhausted(errMsg)
        }
        if code >= 400 {
            throw LLMError.server(code, errMsg)
        }
        let content = (parsed["content"] as? String)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        guard !content.isEmpty else { throw LLMError.emptyResponse }
        let display = (parsed["modelDisplayName"] as? String).flatMap { $0.isEmpty ? nil : $0 } ?? "Agent"
        let remaining = parsed["creditsRemaining"] as? Int ?? 0
        return AgentReply(content: content, modelDisplayName: display, creditsRemaining: remaining)
    }
}
