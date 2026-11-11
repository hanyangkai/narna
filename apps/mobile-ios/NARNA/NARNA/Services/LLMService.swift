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
            return "The API key was rejected (401). Check that the selected provider matches this key, and that the key is valid." + (m.map { "\n(\($0))" } ?? "")
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
        if config.provider.usesAnthropicAPI {
            return try await anthropic(config: config, system: system, turns: turns, maxTokens: maxTokens)
        }
        return try await openAI(config: config, system: system, turns: turns)
    }

    // MARK: Model list (GET {base}/models)

    func listModels(provider: LLMProvider, baseURL: String, apiKey: String, session: URLSession? = nil) async throws -> [String] {
        if isMockMode { return provider.suggestedModels + ["demo-model-large", "demo-model-small"] }
        let base = baseURL.trimmingCharacters(in: CharacterSet(charactersIn: "/ "))
        guard let url = URL(string: base + "/models\(provider.usesAnthropicAPI ? "?limit=100" : "")"),
              url.scheme?.hasPrefix("http") == true else { throw LLMError.invalidBaseURL }
        var req = URLRequest(url: url)
        let key = apiKey.trimmingCharacters(in: .whitespacesAndNewlines)
        if provider.usesAnthropicAPI {
            req.setValue(key, forHTTPHeaderField: "x-api-key")
            req.setValue("2023-06-01", forHTTPHeaderField: "anthropic-version")
        } else if !key.isEmpty {
            req.setValue("Bearer \(key)", forHTTPHeaderField: "Authorization")
        }
        let json = try await send(req, session: session)
        let items = (json["data"] as? [[String: Any]]) ?? (json["models"] as? [[String: Any]]) ?? []
        var ids = items.compactMap { ($0["id"] as? String) ?? ($0["name"] as? String) }
            .map { $0.hasPrefix("models/") ? String($0.dropFirst(7)) : $0 }
        // Hide obvious non-chat models (embeddings, audio, image, moderation).
        let skip = ["embed", "whisper", "tts", "dall-e", "moderation", "transcribe", "audio", "image", "rerank", "guard"]
        ids = ids.filter { id in !skip.contains { id.lowercased().contains($0) } }
        return Array(Set(ids)).sorted()
    }

    // MARK: Paste-only key setup

    struct KeyResolution {
        let provider: LLMProvider
        let baseURL: String
        let models: [String]
    }

    /// Short-timeout session for probing providers while the user pastes a key.
    private let probeSession: URLSession = {
        let c = URLSessionConfiguration.ephemeral
        c.timeoutIntervalForRequest = 12
        c.timeoutIntervalForResource = 20
        c.urlCache = nil
        return URLSession(configuration: c)
    }()

    /// Order used when the key prefix is unknown.
    static let probeOrder: [LLMProvider] = [.ckey, .openai, .openrouter, .groq, .deepseek, .together, .xai, .gemini, .mistral]
    /// Plain "sk-" is shared by several OpenAI-compatible services.
    static let skProbeOrder: [LLMProvider] = [.ckey, .openai, .deepseek, .together, .mistral, .openrouter]

    static func candidates(forKey key: String) -> [LLMProvider] {
        guard let (p, strong) = LLMProvider.detect(fromKey: key) else { return probeOrder }
        return strong ? [p] : skProbeOrder
    }

    /// Finds which provider accepts this key: probes GET {base}/models for every candidate
    /// in parallel and returns the first one (in priority order) that answers 200 and
    /// really authenticated the key. nil if none accepted it.
    func resolveKey(_ rawKey: String) async -> KeyResolution? {
        let key = rawKey.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !key.isEmpty else { return nil }
        let order = Self.candidates(forKey: key)
        if isMockMode {
            let p = order.first ?? .openai
            return KeyResolution(provider: p, baseURL: p.defaultBaseURL, models: p.suggestedModels + ["demo-model-large", "demo-model-small"])
        }
        var found: [LLMProvider: KeyResolution] = [:]
        await withTaskGroup(of: (LLMProvider, KeyResolution?).self) { group in
            for p in order {
                group.addTask { [self] in
                    let base = p.defaultBaseURL
                    guard let models = try? await self.listModels(provider: p, baseURL: base, apiKey: key, session: self.probeSession),
                          await self.verifyAuth(provider: p, baseURL: base, apiKey: key) else { return (p, nil) }
                    return (p, KeyResolution(provider: p, baseURL: base, models: models))
                }
            }
            for await (p, r) in group { if let r { found[p] = r } }
        }
        return order.lazy.compactMap { found[$0] }.first
    }

    /// Some /models endpoints are public (CKEY, OpenRouter), so a 200 there does not prove
    /// the key is valid. Check an endpoint that needs auth for those.
    private func verifyAuth(provider: LLMProvider, baseURL: String, apiKey: String) async -> Bool {
        let base = baseURL.trimmingCharacters(in: CharacterSet(charactersIn: "/ "))
        switch provider {
        case .openrouter:
            return await status("GET", base + "/key", key: apiKey) == 200
        case .ckey:
            let code = await status("GET", base + "/dashboard/billing/subscription", key: apiKey)
            if code == 200 { return true }
            if code == 401 || code == 403 { return false }
            // Fallback: a chat call to a model that does not exist. Costs nothing;
            // a bad key gets 401, a good key gets a model error instead.
            let body = #"{"model":"narna-key-check","messages":[{"role":"user","content":"hi"}],"max_tokens":1}"#
            let chat = await status("POST", base + "/chat/completions", key: apiKey, body: body)
            return chat != 0 && chat != 401 && chat != 403
        default:
            return true
        }
    }

    private func status(_ method: String, _ urlString: String, key: String, body: String? = nil) async -> Int {
        guard let url = URL(string: urlString) else { return 0 }
        var req = URLRequest(url: url)
        req.httpMethod = method
        req.setValue("Bearer \(key)", forHTTPHeaderField: "Authorization")
        if let body {
            req.httpBody = body.data(using: .utf8)
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        guard let (_, resp) = try? await probeSession.data(for: req) else { return 0 }
        return (resp as? HTTPURLResponse)?.statusCode ?? 0
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
        let base = config.baseURL.trimmingCharacters(in: CharacterSet(charactersIn: "/ "))
        guard let url = URL(string: base + "/messages") else { throw LLMError.invalidBaseURL }
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

    private func send(_ req: URLRequest, session override: URLSession? = nil) async throws -> [String: Any] {
        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await (override ?? session).data(for: req)
        } catch let e as URLError {
            throw LLMError.network(e.localizedDescription)
        } catch {
            throw LLMError.network(error.localizedDescription)
        }
        let code = (response as? HTTPURLResponse)?.statusCode ?? 0
        let raw = try? JSONSerialization.jsonObject(with: data)
        // Some providers (e.g. Gemini) wrap errors in a top-level array.
        let json = (raw as? [String: Any]) ?? ((raw as? [[String: Any]])?.first) ?? [:]
        guard (200..<300).contains(code) else {
            let msg = Self.providerMessage(json)
            let lower = (msg ?? "").lowercased()
            let keyProblem = lower.contains("api key")
            switch code {
            case 401, 403: throw LLMError.invalidKey(msg)
            case 400 where keyProblem: throw LLMError.invalidKey(msg)
            case 429: throw LLMError.rateLimited(msg)
            default: throw LLMError.server(code, msg)
            }
        }
        return json
    }

    private static func providerMessage(_ json: [String: Any]) -> String? {
        let raw: String?
        if let err = json["error"] as? [String: Any], let m = err["message"] as? String {
            raw = m
        } else if let m = json["message"] as? String {
            raw = m
        } else {
            raw = nil
        }
        return raw.map { sanitizeProviderMessage($0) }
    }

    /// Strip anything that looks like a key so we never show or log key material.
    static func sanitizeProviderMessage(_ message: String) -> String {
        var s = message
        // Replace only values that look like secrets, never header names such as "x-api-key".
        let replacements: [(String, String)] = [
            (#"sk-[A-Za-z0-9_\-]{8,}"#, "[redacted]"),
            (#"gsk_[A-Za-z0-9_\-]{8,}"#, "[redacted]"),
            (#"xai-[A-Za-z0-9_\-]{8,}"#, "[redacted]"),
            (#"AIza[A-Za-z0-9_\-]{8,}"#, "[redacted]"),
            (#"(?i)Bearer\s+[A-Za-z0-9_\-\.]{8,}"#, "Bearer [redacted]"),
            (#"(?i)(API key provided:\s*)(\S+)"#, "$1[redacted]"),
        ]
        for (p, tmpl) in replacements {
            if let re = try? NSRegularExpression(pattern: p) {
                s = re.stringByReplacingMatches(in: s, options: [], range: NSRange(s.startIndex..., in: s), withTemplate: tmpl)
            }
        }
        return String(s.prefix(200))
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
