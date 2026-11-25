//
//  AppleOnDeviceProvider.swift
//  NARNA
//
//  Uses Apple Foundation Models when the SDK is present (iOS 26+).
//  Compiles on older Xcode via canImport stubs.
//

import Foundation

struct DefaultAppleAvailabilityChecker: AppleAvailabilityChecking {
    func availability() -> AppleModelAvailabilityReason {
        #if canImport(FoundationModels)
        if #available(iOS 26.0, *) {
            return AppleFoundationModelsBridge.availability()
        }
        #endif
        return .unsupportedOS
    }
}

final class AppleOnDeviceProvider: LLMProvider, @unchecked Sendable {
    let engineDisplayName = "Apple on-device"
    private let checker: AppleAvailabilityChecking

    init(checker: AppleAvailabilityChecking = DefaultAppleAvailabilityChecker()) {
        self.checker = checker
    }

    func stream(messages: [ChatProviderMessage]) async throws -> AsyncStream<String> {
        let reason = checker.availability()
        guard reason == .available else {
            throw ChatProviderError.unavailable(reason.friendlyMessage)
        }

        #if canImport(FoundationModels)
        if #available(iOS 26.0, *) {
            return try await AppleFoundationModelsBridge.stream(messages: messages)
        }
        #endif
        throw ChatProviderError.unavailable(AppleModelAvailabilityReason.unsupportedOS.friendlyMessage)
    }
}

#if canImport(FoundationModels)
import FoundationModels

@available(iOS 26.0, *)
enum AppleFoundationModelsBridge {
    static func availability() -> AppleModelAvailabilityReason {
        let model = SystemLanguageModel.default
        switch model.availability {
        case .available:
            return .available
        case .unavailable(let reason):
            switch reason {
            case .deviceNotEligible:
                return .deviceNotEligible
            case .appleIntelligenceNotEnabled:
                return .appleIntelligenceNotEnabled
            case .modelNotReady:
                return .modelNotReady
            @unknown default:
                return .unknown(String(describing: reason))
            }
        @unknown default:
            return .unknown("Unknown Foundation Models state")
        }
    }

    static func stream(messages: [ChatProviderMessage]) async throws -> AsyncStream<String> {
        let trimmed = Self.trimForContext(messages)
        let prompt = trimmed.map { "\($0.role.uppercased()): \($0.content)" }.joined(separator: "\n\n")
        let session = LanguageModelSession(instructions: NanaSystemPrompt.value)

        return AsyncStream { continuation in
            Task {
                do {
                    // Foundation Models API surface may evolve; try stream then one-shot.
                    var emitted = false
                    do {
                        let stream = session.streamResponse(to: prompt)
                        for try await snapshot in stream {
                            let chunk = String(describing: snapshot)
                            if !chunk.isEmpty {
                                continuation.yield(chunk)
                                emitted = true
                            }
                        }
                    } catch {
                        emitted = false
                    }
                    if !emitted {
                        let once = try await session.respond(to: prompt)
                        let text = String(describing: once)
                        if !text.isEmpty { continuation.yield(text) }
                    }
                    continuation.finish()
                } catch {
                    continuation.finish()
                }
            }
        }
    }

    /// Keep recent turns; summarize older ones into a short system note.
    static func trimForContext(_ messages: [ChatProviderMessage], maxChars: Int = 12_000) -> [ChatProviderMessage] {
        var total = 0
        var kept: [ChatProviderMessage] = []
        for msg in messages.reversed() {
            total += msg.content.count
            if total > maxChars && !kept.isEmpty {
                break
            }
            kept.append(msg)
        }
        kept.reverse()
        if kept.count < messages.count {
            let omitted = messages.count - kept.count
            kept.insert(
                ChatProviderMessage(
                    role: "system",
                    content: "Earlier conversation summarized: \(omitted) older turns omitted for context limits."
                ),
                at: 0
            )
        }
        return kept
    }
}
#endif
