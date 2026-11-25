//
//  ChatBot.swift
//  NARNA
//
//  Local Nana AI chat models (on-device / free pool / BYOK).
//

import Foundation

enum ChatEngineKind: String, Codable, CaseIterable, Identifiable {
    case auto
    case onDevice
    case freePool
    case byoOpenRouter
    case byoOpenAI

    var id: String { rawValue }

    var settingsLabel: String {
        switch self {
        case .auto: return "Auto (recommended)"
        case .onDevice: return "On-device"
        case .freePool: return "Free cloud"
        case .byoOpenRouter: return "My OpenRouter key"
        case .byoOpenAI: return "My OpenAI key"
        }
    }
}

struct ChatTurn: Identifiable, Equatable, Codable {
    let id: String
    var role: String // user | assistant | system
    var content: String
    var engineLabel: String?
    var createdAt: Date

    init(
        id: String = UUID().uuidString,
        role: String,
        content: String,
        engineLabel: String? = nil,
        createdAt: Date = Date()
    ) {
        self.id = id
        self.role = role
        self.content = content
        self.engineLabel = engineLabel
        self.createdAt = createdAt
    }
}

struct ChatProviderMessage: Equatable {
    let role: String
    let content: String
}

enum ChatProviderError: LocalizedError, Equatable {
    case unavailable(String)
    case dailyLimitReached
    case network(String)
    case invalidKey
    case cancelled

    var errorDescription: String? {
        switch self {
        case .unavailable(let msg): return msg
        case .dailyLimitReached:
            return String(localized: "free_daily_limit_reached")
        case .network(let msg): return msg
        case .invalidKey: return String(localized: "byo_invalid_key")
        case .cancelled: return nil
        }
    }
}

enum AppleModelAvailabilityReason: Equatable {
    case available
    case deviceNotEligible
    case appleIntelligenceNotEnabled
    case modelNotReady
    case unsupportedOS
    case unknown(String)

    var friendlyMessage: String {
        switch self {
        case .available:
            return String(localized: "apple_model_available")
        case .deviceNotEligible:
            return String(localized: "apple_model_device_not_eligible")
        case .appleIntelligenceNotEnabled:
            return String(localized: "apple_model_intelligence_off")
        case .modelNotReady:
            return String(localized: "apple_model_not_ready")
        case .unsupportedOS:
            return String(localized: "apple_model_unsupported_os")
        case .unknown(let detail):
            return detail
        }
    }

    var suggestsOpenSettings: Bool {
        self == .appleIntelligenceNotEnabled
    }
}

enum NanaSystemPrompt {
    static let value = """
    You are Nana AI, a helpful, concise assistant on the user's iPhone. \
    Be clear and practical. If unsure, say so. Do not claim to browse the live web unless tools are available.
    """
}

enum PinnedBot {
    static let name = "Nana AI"
}
