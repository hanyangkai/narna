//
//  OnDeviceFoundationProvider.swift
//  NARNA
//
//  Apple Foundation Models (on-device). Zero cost to the owner, no network,
//  no login. Requires iOS 26+ and Apple Intelligence availability.
//

import Foundation

#if canImport(FoundationModels)
import FoundationModels
#endif

enum OnDeviceFoundationProvider {
    static let displayName = "On-device"

    /// Whether SystemLanguageModel.default is available on this device.
    static var isAvailable: Bool {
        #if canImport(FoundationModels)
        if #available(iOS 26.0, *) {
            return SystemLanguageModel.default.availability == .available
        }
        #endif
        return false
    }

    static var unavailabilityReason: String? {
        #if canImport(FoundationModels)
        if #available(iOS 26.0, *) {
            switch SystemLanguageModel.default.availability {
            case .available:
                return nil
            case .unavailable(let reason):
                switch reason {
                case .deviceNotEligible:
                    return "This iPhone does not support Apple Intelligence. Nana will use the free cloud pool when it is configured."
                case .appleIntelligenceNotEnabled:
                    return "Turn on Apple Intelligence in Settings to chat on-device for free."
                case .modelNotReady:
                    return "The on-device model is still downloading. Try again in a moment, or Nana will use the free cloud pool."
                @unknown default:
                    return "On-device AI is not available right now."
                }
            @unknown default:
                return "On-device AI is not available right now."
            }
        }
        #endif
        return "On-device AI needs iOS 26 and Apple Intelligence."
    }

    static func complete(system: String, turns: [LLMTurn]) async throws -> String {
        #if canImport(FoundationModels)
        if #available(iOS 26.0, *) {
            guard SystemLanguageModel.default.availability == .available else {
                throw LLMError.onDeviceUnavailable(unavailabilityReason)
            }
            let instructions = system.trimmingCharacters(in: .whitespacesAndNewlines)
            let session: LanguageModelSession
            if instructions.isEmpty {
                session = LanguageModelSession()
            } else {
                session = LanguageModelSession(instructions: instructions)
            }
            let prompt = Self.prompt(from: turns)
            let response = try await session.respond(to: prompt)
            let text = response.content.trimmingCharacters(in: .whitespacesAndNewlines)
            guard !text.isEmpty else { throw LLMError.emptyResponse }
            return text
        }
        #endif
        throw LLMError.onDeviceUnavailable(unavailabilityReason)
    }

    static func prompt(from turns: [LLMTurn]) -> String {
        // Flatten history so we do not depend on session-transcript APIs.
        let recent = turns.suffix(20)
        if recent.count == 1, let only = recent.first, only.role == .user {
            return only.content
        }
        return recent.map { turn in
            (turn.role == .user ? "User: " : "Assistant: ") + turn.content
        }.joined(separator: "\n\n")
    }
}
