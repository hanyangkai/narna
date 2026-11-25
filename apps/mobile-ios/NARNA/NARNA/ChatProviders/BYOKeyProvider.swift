//
//  BYOKeyProvider.swift
//  NARNA
//
//  Optional Advanced mode: user's own OpenRouter / OpenAI key from Keychain.
//

import Foundation

enum BYOProviderKind: String {
    case openrouter
    case openai
}

final class BYOKeyProvider: LLMProvider, @unchecked Sendable {
    let engineDisplayName: String
    private let kind: BYOProviderKind
    private let apiKey: String
    private let model: String
    private let session: URLSession

    init(
        kind: BYOProviderKind,
        apiKey: String,
        model: String? = nil,
        session: URLSession = .shared
    ) {
        self.kind = kind
        self.apiKey = apiKey.trimmingCharacters(in: .whitespacesAndNewlines)
        switch kind {
        case .openrouter:
            self.engineDisplayName = model ?? "OpenRouter"
            self.model = model ?? "openai/gpt-4o-mini"
        case .openai:
            self.engineDisplayName = model ?? "OpenAI"
            self.model = model ?? "gpt-4o-mini"
        }
        self.session = session
    }

    func stream(messages: [ChatProviderMessage]) async throws -> AsyncStream<String> {
        guard apiKey.count >= 8 else { throw ChatProviderError.invalidKey }
        if kind == .openrouter, !apiKey.hasPrefix("sk-or-"), !apiKey.hasPrefix("sk-") {
            // Still allow; OpenRouter keys are typically sk-or-
        }

        let url: URL
        switch kind {
        case .openrouter:
            url = URL(string: "https://openrouter.ai/api/v1/chat/completions")!
        case .openai:
            url = URL(string: "https://api.openai.com/v1/chat/completions")!
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        if kind == .openrouter {
            request.setValue("https://narna.org", forHTTPHeaderField: "HTTP-Referer")
            request.setValue("Nana AI", forHTTPHeaderField: "X-Title")
        }

        var msgs: [[String: String]] = [
            ["role": "system", "content": NanaSystemPrompt.value],
        ]
        msgs.append(contentsOf: messages.map { ["role": $0.role, "content": $0.content] })

        let body: [String: Any] = [
            "model": model,
            "stream": true,
            "messages": msgs,
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (bytes, response) = try await session.bytes(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw ChatProviderError.network("Invalid response")
        }
        if http.statusCode == 401 || http.statusCode == 403 {
            throw ChatProviderError.invalidKey
        }
        guard (200..<300).contains(http.statusCode) else {
            throw ChatProviderError.network("Provider HTTP \(http.statusCode)")
        }

        return AsyncStream { continuation in
            Task {
                do {
                    for try await line in bytes.lines {
                        let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
                        guard trimmed.hasPrefix("data:") else { continue }
                        let payload = trimmed.dropFirst(5).trimmingCharacters(in: .whitespaces)
                        if payload == "[DONE]" { break }
                        guard let data = payload.data(using: .utf8),
                              let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                              let choices = obj["choices"] as? [[String: Any]],
                              let first = choices.first else { continue }
                        if let delta = first["delta"] as? [String: Any],
                           let content = delta["content"] as? String,
                           !content.isEmpty {
                            continuation.yield(content)
                        }
                    }
                    continuation.finish()
                } catch {
                    continuation.finish()
                }
            }
        }
    }
}
