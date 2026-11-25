//
//  FreePoolProvider.swift
//  NARNA
//
//  Calls our Cloudflare free-pool proxy only — no provider API keys in the app.
//

import Foundation

final class FreePoolProvider: ChatProvider, @unchecked Sendable {
    let engineDisplayName = "Free cloud"
    private let baseURL: URL
    private let deviceId: String
    private let session: URLSession

    init(
        baseURL: URL = FreePoolConfig.baseURL,
        deviceId: String,
        session: URLSession = .shared
    ) {
        self.baseURL = baseURL
        self.deviceId = deviceId
        self.session = session
    }

    func stream(messages: [ChatProviderMessage]) async throws -> AsyncStream<String> {
        let url = baseURL.appendingPathComponent("v1/chat")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("text/event-stream", forHTTPHeaderField: "Accept")
        request.setValue(deviceId, forHTTPHeaderField: "X-Device-Id")

        let body: [String: Any] = [
            "deviceId": deviceId,
            "stream": true,
            "messages": messages.map { ["role": $0.role, "content": $0.content] },
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (bytes, response) = try await session.bytes(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw ChatProviderError.network("Invalid response")
        }
        if http.statusCode == 429 {
            throw ChatProviderError.dailyLimitReached
        }
        guard (200..<300).contains(http.statusCode) else {
            throw ChatProviderError.network("Free pool HTTP \(http.statusCode)")
        }

        return AsyncStream { continuation in
            Task {
                do {
                    for try await line in bytes.lines {
                        let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
                        guard trimmed.hasPrefix("data:") else { continue }
                        let payload = trimmed.dropFirst(5).trimmingCharacters(in: .whitespaces)
                        if payload == "[DONE]" {
                            break
                        }
                        if let data = payload.data(using: .utf8),
                           let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                            if let err = obj["error"] as? String, err == "daily_limit" {
                                continuation.finish()
                                return
                            }
                            if let delta = obj["delta"] as? String, !delta.isEmpty {
                                continuation.yield(delta)
                                continue
                            }
                            if let content = obj["content"] as? String, !content.isEmpty {
                                continuation.yield(content)
                                continue
                            }
                        } else if !payload.isEmpty {
                            continuation.yield(payload)
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
