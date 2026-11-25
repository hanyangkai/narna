//
//  AgentProvider.swift
//  NARNA
//
//  Paid Agent Mode — calls our backend only (OpenRouter keys stay server-side).
//

import Foundation

final class AgentProvider: LLMProvider, @unchecked Sendable {
    let engineDisplayName: String
    private let baseURL: URL
    private let deviceId: String
    private let signedTransaction: String?
    private let model: String?
    private let session: URLSession

    init(
        baseURL: URL,
        deviceId: String,
        signedTransaction: String?,
        model: String? = nil,
        session: URLSession = .shared
    ) {
        self.baseURL = baseURL
        self.deviceId = deviceId
        self.signedTransaction = signedTransaction
        self.model = model
        self.session = session
        self.engineDisplayName = "Agent"
    }

    static var defaultAPIBase: URL {
        if let raw = Bundle.main.object(forInfoDictionaryKey: "NANA_AGENT_API_URL") as? String,
           let url = URL(string: raw), !raw.isEmpty {
            return url
        }
        if let raw = UserDefaults.standard.string(forKey: "api_base_url"),
           let url = URL(string: raw) {
            return url
        }
        return URL(string: "http://localhost:8765")!
    }

    func stream(messages: [ChatProviderMessage]) async throws -> AsyncStream<String> {
        // Agent endpoint is non-SSE JSON for v1.1; wrap as a single-chunk stream.
        let url = baseURL.appendingPathComponent("v1/nana/agent/chat")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(deviceId, forHTTPHeaderField: "X-Device-Id")

        var body: [String: Any] = [
            "deviceId": deviceId,
            "messages": messages.map { ["role": $0.role, "content": $0.content] },
        ]
        if let signedTransaction, !signedTransaction.isEmpty {
            body["signedTransaction"] = signedTransaction
        }
        if let model { body["model"] = model }
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw ChatProviderError.network("Invalid response")
        }
        if http.statusCode == 402 {
            throw ChatProviderError.agentPaywallRequired
        }
        guard (200..<300).contains(http.statusCode) else {
            throw ChatProviderError.network("Agent HTTP \(http.statusCode)")
        }
        let obj = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
        let content = String(obj?["content"] as? String ?? "")
        let label = String(obj?["engineLabel"] as? String ?? "Agent")
        let text = content.isEmpty ? "…" : content

        return AsyncStream { continuation in
            continuation.yield(text)
            // Stash label via a sentinel prefix consumed by view model if needed — engineDisplayName is static.
            _ = label
            continuation.finish()
        }
    }
}
