//
//  FreePoolProvider.swift
//  NARNA
//
//  Talks to our Cloudflare Worker (FREE_POOL_URL). The Worker holds provider
//  keys and routes Gemini Flash → GPT-OSS → Gemma with 429 fallback.
//  The app never embeds provider keys. Cap: 100 messages per device per day (Worker DAILY_LIMIT).
//

import Foundation

struct FreePoolReply: Equatable {
    var content: String
    var modelID: String
    var modelDisplayName: String
    var remaining: Int
}

enum FreePoolProvider {
    static let dailyLimit = 100
    static var isConfigured: Bool { AppConfig.isFreePoolConfigured }

    private static let session: URLSession = {
        let c = URLSessionConfiguration.ephemeral
        c.timeoutIntervalForRequest = 120
        c.urlCache = nil
        return URLSession(configuration: c)
    }()

    static func complete(system: String, turns: [LLMTurn]) async throws -> FreePoolReply {
        if LLMService.shared.isMockMode {
            return FreePoolReply(content: try await MockLLM.reply(system: system, turns: turns),
                                 modelID: "mock-gemini-flash",
                                 modelDisplayName: "Gemini Flash",
                                 remaining: 9)
        }
        guard let base = AppConfig.freePoolURL else { throw LLMError.freePoolNotConfigured }
        let url = base.appendingPathComponent("v1/chat")
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let attest = await DeviceAttestation.payload()
        for (k, v) in attest.asHeaders { req.setValue(v, forHTTPHeaderField: k) }

        struct Body: Encodable {
            let system: String
            let messages: [Msg]
            let region: String
            struct Msg: Encodable { let role: String; let content: String }
        }
        let messages = turns.map { Body.Msg(role: $0.role == .user ? "user" : "assistant", content: $0.content) }
        req.setValue(DeviceRegion.isoCode, forHTTPHeaderField: "X-Device-Region")
        req.httpBody = try JSONEncoder().encode(Body(system: system, messages: messages, region: DeviceRegion.isoCode))

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
        if code == 429 {
            throw LLMError.dailyLimit((parsed["remaining"] as? Int) ?? 0, errMsg)
        }
        if code == 401 || code == 403 {
            throw LLMError.server(code, errMsg ?? "The free pool could not verify this device.")
        }
        if code >= 400 {
            throw LLMError.server(code, errMsg)
        }
        let content = (parsed["content"] as? String)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        guard !content.isEmpty else { throw LLMError.emptyResponse }
        let modelID = (parsed["model"] as? String) ?? ""
        let display = (parsed["modelDisplayName"] as? String).flatMap { $0.isEmpty ? nil : $0 }
            ?? FreePoolModelCatalog.displayName(forModelId: modelID)
        let remaining = parsed["remaining"] as? Int ?? -1
        if remaining >= 0 {
            await MainActor.run { FreePoolRemainingHint.set(remaining) }
        }
        return FreePoolReply(content: content, modelID: modelID, modelDisplayName: display, remaining: remaining)
    }
}
