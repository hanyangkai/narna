//
//  LLMService.swift
//  NARNA
//
//  Calls the provider the user picked directly from the device (URLSession).
//  No NARNA server in between. The API key is only sent to that provider.
//

import Foundation

struct LLMTurn {
    let role: AIRole
    let content: String
}

struct LLMRequestConfig {
    let provider: LLMProvider
    let model: String
    let baseURL: String
    let apiKey: String
}

enum LLMError: LocalizedError {
    case missingKey
    case invalidBaseURL
    case invalidKey(String?)
    case rateLimited(String?)
    case network(String)
    case server(Int, String?)
    case emptyResponse

    var errorDescription: String? {
        switch self {
        case .missingKey:
            return "Add your API key in Settings to start chatting."
        case .invalidBaseURL:
            return "The provider base URL is not valid. Check it in Settings."
        case .invalidKey(let m):
            return "Your API key was rejected by the provider. Check it in Settings." + (m.map { "\n(\($0))" } ?? "")
        case .rateLimited(let m):
            return "Rate limit or quota reached at your provider. Wait a moment or check your plan." + (m.map { "\n(\($0))" } ?? "")
        case .network(let m):
            return "Network problem: \(m)"
        case .server(let code, let m):
            return "Provider error \(code)" + (m.map { ": \($0)" } ?? ".")
        case .emptyResponse:
            return "The provider returned an empty answer."
        }
    }
}

final class LLMService {
    static let shared = LLMService()

    private let session: URLSession = {
        let c = URLSessionConfiguration.ephemeral   // no cache / cookies on disk
        c.timeoutIntervalForRequest = 120
        c.urlCache = nil
        return URLSession(configuration: c)
    }()

    private init() {}

    var isMockMode: Bool {
        #if DEBUG
        return ProcessInfo.processInfo.arguments.contains("-NARNA_DEMO_MOCK")
        #else
        return false
        #endif
    }

    func complete(config: LLMRequestConfig, system: String, turns: [LLMTurn], maxTokens: Int = 1500) async throws -> String {
        if isMockMode { return try await MockLLM.reply(system: system, turns: turns) }
        guard !config.apiKey.isEmpty else { throw LLMError.missingKey }
        switch config.provider {
        case .anthropic:
            return try await anthropic(config: config, system: system, turns: turns, maxTokens: maxTokens)
        case .openai, .openaiCompatible:
            return try await openAI(config: config, system: system, turns: turns)
        }
    }

    // MARK: OpenAI chat completions (also OpenAI-compatible servers)

    private func openAI(config: LLMRequestConfig, system: String, turns: [LLMTurn]) async throws -> String {
        let base = config.baseURL.trimmingCharacters(in: CharacterSet(charactersIn: "/ "))
        guard let url = URL(string: base + "/chat/completions"), url.scheme?.hasPrefix("http") == true else {
            throw LLMError.invalidBaseURL
        }
        var msgs: [[String: String]] = [["role": "system", "content": system]]
        msgs += turns.map { ["role": $0.role.rawValue, "content": $0.content] }
        let body: [String: Any] = ["model": config.model, "messages": msgs]

        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue("Bearer \(config.apiKey)", forHTTPHeaderField: "Authorization")
        req.httpBody = try JSONSerialization.data(withJSONObject: body)

        let json = try await send(req)
        guard let choices = json["choices"] as? [[String: Any]],
              let message = choices.first?["message"] as? [String: Any],
              let content = message["content"] as? String,
              !content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            throw LLMError.emptyResponse
        }
        return content
    }

    // MARK: Anthropic messages API

    private func anthropic(config: LLMRequestConfig, system: String, turns: [LLMTurn], maxTokens: Int) async throws -> String {
        guard let url = URL(string: config.baseURL + "/messages") else { throw LLMError.invalidBaseURL }
        let body: [String: Any] = [
            "model": config.model,
            "max_tokens": maxTokens,
            "system": system,
            "messages": turns.map { ["role": $0.role.rawValue, "content": $0.content] }
        ]
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.setValue(config.apiKey, forHTTPHeaderField: "x-api-key")
        req.setValue("2023-06-01", forHTTPHeaderField: "anthropic-version")
        req.httpBody = try JSONSerialization.data(withJSONObject: body)

        let json = try await send(req)
        guard let blocks = json["content"] as? [[String: Any]] else { throw LLMError.emptyResponse }
        let text = blocks.compactMap { $0["type"] as? String == "text" ? $0["text"] as? String : nil }.joined()
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { throw LLMError.emptyResponse }
        return text
    }

    // MARK: Transport + error mapping

    private func send(_ req: URLRequest) async throws -> [String: Any] {
        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: req)
        } catch let e as URLError {
            throw LLMError.network(e.localizedDescription)
        } catch {
            throw LLMError.network(error.localizedDescription)
        }
        let code = (response as? HTTPURLResponse)?.statusCode ?? 0
        let json = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] ?? [:]
        guard (200..<300).contains(code) else {
            let msg = Self.providerMessage(json)
            switch code {
            case 401, 403: throw LLMError.invalidKey(msg)
            case 429: throw LLMError.rateLimited(msg)
            default: throw LLMError.server(code, msg)
            }
        }
        return json
    }

    private static func providerMessage(_ json: [String: Any]) -> String? {
        if let err = json["error"] as? [String: Any], let m = err["message"] as? String {
            return String(m.prefix(200))
        }
        if let m = json["message"] as? String { return String(m.prefix(200)) }
        return nil
    }
}

/// Canned replies used only in DEBUG builds launched with -NARNA_DEMO_MOCK
/// (simulator screenshots). Never active in release builds.
enum MockLLM {
    static func reply(system: String, turns: [LLMTurn]) async throws -> String {
        try await Task.sleep(nanoseconds: 300_000_000)
        if system.contains("ADQA") {
            return """
            {"attributes":{"evidence":78,"policy":92,"context":85,"memory":70,"risk":74,"alignment":93,"capability":95,"compliance":88,"confidence":80,"explanation":90},
             "riskBand":"medium",
             "constitution":{"truth":"pass","logic":"pass","alignment":"pass","safety":"pass","authority":"pass","accountability":"warn"},
             "needsHumanReview":false,
             "reasons":["Clear, staged plan with a measurable checkpoint","Cost figures are estimates, not sourced quotes","Reversible: pilot first, full rollout later"],
             "recommendation":"Confirm vendor pricing before committing budget."}
            """
        }
        return """
        **Short answer:** run a 2-week pilot before switching the whole team.

        **Why**
        - Migration cost is low if you start with **one squad** (≈5 people).
        - You get real numbers on build time and review speed instead of guesses.
        - Rolling back after a pilot is cheap; rolling back after a full switch is not.

        **Plan**
        1. Pick one active repo and one squad.
        2. Track lead time, failed builds and weekly cost for 2 weeks.
        3. Go / no-go meeting with those numbers.

        _Estimate only — check current vendor pricing before you commit budget._
        """
    }
}
