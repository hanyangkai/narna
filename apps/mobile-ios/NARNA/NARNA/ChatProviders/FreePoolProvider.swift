//
//  FreePoolProvider.swift
//  NARNA
//
//  Calls our Cloudflare free-pool proxy only — no provider API keys in the app.
//

import Foundation

final class FreePoolProvider: LLMProvider, @unchecked Sendable {
    private(set) var engineDisplayName = "Free cloud"
    private let baseURL: URL
    private let deviceId: String
    private let deviceToken: String?
    private let regionHint: String?
    private let session: URLSession

    init(
        baseURL: URL = FreePoolConfig.baseURL,
        deviceId: String,
        deviceToken: String? = nil,
        regionHint: String? = Locale.current.region?.identifier,
        session: URLSession = .shared
    ) {
        self.baseURL = baseURL
        self.deviceId = deviceId
        self.deviceToken = deviceToken
        self.regionHint = regionHint
        self.session = session
    }

    func stream(messages: [ChatProviderMessage]) async throws -> AsyncStream<String> {
        let url = baseURL.appendingPathComponent("v1/chat")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 60
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("text/event-stream", forHTTPHeaderField: "Accept")
        request.setValue(deviceId, forHTTPHeaderField: "X-Device-Id")
        if let deviceToken, !deviceToken.isEmpty {
            request.setValue(deviceToken, forHTTPHeaderField: "X-Device-Check-Token")
        }
        if let regionHint, !regionHint.isEmpty {
            request.setValue(regionHint, forHTTPHeaderField: "X-Region-Hint")
        }

        let body: [String: Any] = [
            "deviceId": deviceId,
            "stream": true,
            "messages": messages.map { ["role": $0.role, "content": $0.content] },
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (bytes, response): (URLSession.AsyncBytes, URLResponse)
        do {
            (bytes, response) = try await session.bytes(for: request)
        } catch {
            throw ChatProviderError.network("timeout_or_unreachable")
        }
        guard let http = response as? HTTPURLResponse else {
            throw ChatProviderError.network("Invalid response")
        }
        if let engine = http.value(forHTTPHeaderField: "X-Nana-Engine"), !engine.isEmpty {
            engineDisplayName = ProviderRouter.friendlyModelLabel(engine)
        }
        if http.statusCode == 429 {
            throw ChatProviderError.dailyLimitReached
        }
        if http.statusCode == 503 {
            throw ChatProviderError.network("free_pool_unavailable")
        }
        guard (200..<300).contains(http.statusCode) else {
            throw ChatProviderError.network("Free pool HTTP \(http.statusCode)")
        }

        let labelCapture = engineDisplayName
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
                            if let eng = obj["engine"] as? String, !eng.isEmpty {
                                // mid-stream label update not surfaced; header is primary
                                _ = eng
                                _ = labelCapture
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
