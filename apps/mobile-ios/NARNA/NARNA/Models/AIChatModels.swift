//
//  AIChatModels.swift
//  NARNA
//
//  Standalone on-device AI chat (bring your own key) + ADQA assessment models.
//

import Foundation

enum LLMProvider: String, Codable, CaseIterable, Identifiable {
    case openai
    case anthropic
    case openrouter
    case ckey
    case groq
    case deepseek
    case gemini
    case xai
    case together
    case mistral
    case custom = "openaiCompatible"

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .openai: return "OpenAI"
        case .anthropic: return "Anthropic (Claude)"
        case .openrouter: return "OpenRouter"
        case .ckey: return "ckey.vn"
        case .groq: return "Groq"
        case .deepseek: return "DeepSeek"
        case .gemini: return "Google Gemini"
        case .xai: return "xAI (Grok)"
        case .together: return "Together AI"
        case .mistral: return "Mistral"
        case .custom: return "Custom (OpenAI-compatible)"
        }
    }

    /// Anthropic uses its Messages API; every other preset speaks the OpenAI chat-completions format.
    var usesAnthropicAPI: Bool { self == .anthropic }

    var defaultBaseURL: String {
        switch self {
        case .openai: return "https://api.openai.com/v1"
        case .anthropic: return "https://api.anthropic.com/v1"
        case .openrouter: return "https://openrouter.ai/api/v1"
        case .ckey: return "https://api.xah.io/v1"          // per ckey.vn/llm-api/setup
        case .groq: return "https://api.groq.com/openai/v1"
        case .deepseek: return "https://api.deepseek.com/v1"
        case .gemini: return "https://generativelanguage.googleapis.com/v1beta/openai"
        case .xai: return "https://api.x.ai/v1"
        case .together: return "https://api.together.xyz/v1"
        case .mistral: return "https://api.mistral.ai/v1"
        case .custom: return ""
        }
    }

    var defaultModel: String {
        switch self {
        case .openai: return "gpt-4.1-mini"
        case .anthropic: return "claude-sonnet-4-5"
        case .openrouter: return "openrouter/auto"
        case .ckey: return "gpt-4o-mini"
        case .groq: return "llama-3.3-70b-versatile"
        case .deepseek: return "deepseek-chat"
        case .gemini: return "gemini-2.5-flash"
        case .xai: return "grok-3-mini"
        case .together: return "meta-llama/Llama-3.3-70B-Instruct-Turbo"
        case .mistral: return "mistral-small-latest"
        case .custom: return ""
        }
    }

    /// Shown when the model list can't be fetched.
    var suggestedModels: [String] {
        switch self {
        case .openai: return ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini", "gpt-4o", "gpt-5-mini", "gpt-5"]
        case .anthropic: return ["claude-sonnet-4-5", "claude-haiku-4-5", "claude-opus-4-1"]
        case .openrouter: return ["openrouter/auto", "openai/gpt-4o-mini", "anthropic/claude-sonnet-4.5", "google/gemini-2.5-flash"]
        case .ckey: return ["gpt-4o-mini", "gpt-5.4", "claude-sonnet-4.6"]
        case .groq: return ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
        case .deepseek: return ["deepseek-chat", "deepseek-reasoner"]
        case .gemini: return ["gemini-2.5-flash", "gemini-2.5-pro"]
        case .xai: return ["grok-3-mini", "grok-4"]
        case .together: return ["meta-llama/Llama-3.3-70B-Instruct-Turbo"]
        case .mistral: return ["mistral-small-latest", "mistral-large-latest"]
        case .custom: return []
        }
    }

    var keyPlaceholder: String {
        switch self {
        case .openai, .ckey, .deepseek: return "sk-..."
        case .anthropic: return "sk-ant-..."
        case .openrouter: return "sk-or-..."
        case .groq: return "gsk_..."
        case .gemini: return "AIza..."
        case .xai: return "xai-..."
        default: return "API key"
        }
    }

    /// Guess the provider from a pasted key. Plain "sk-" is shared by several
    /// providers (OpenAI, ckey.vn, DeepSeek...), so it is a weak signal.
    static func detect(fromKey key: String) -> (provider: LLMProvider, strong: Bool)? {
        let k = key.trimmingCharacters(in: .whitespacesAndNewlines)
        if k.hasPrefix("sk-or-") { return (.openrouter, true) }
        if k.hasPrefix("sk-ant-") { return (.anthropic, true) }
        if k.hasPrefix("gsk_") { return (.groq, true) }
        if k.hasPrefix("xai-") { return (.xai, true) }
        if k.hasPrefix("AIza") { return (.gemini, true) }
        if k.hasPrefix("sk-") { return (.openai, false) }
        return nil
    }
}

/// The single saved AI configuration (stored as one Keychain item).
struct LLMConfig: Codable, Equatable {
    var provider: LLMProvider
    var model: String
    var baseURLOverride: String = ""
    var apiKey: String

    var baseURL: String {
        let o = baseURLOverride.trimmingCharacters(in: .whitespacesAndNewlines)
        return o.isEmpty ? provider.defaultBaseURL : o
    }
}

enum AIRole: String, Codable {
    case user
    case assistant
}

enum ADQAGuardian: String, Codable {
    case approve, revise, escalate, reject

    var label: String {
        switch self {
        case .approve: return "Approve"
        case .revise: return "Revise"
        case .escalate: return "Escalate"
        case .reject: return "Reject"
        }
    }

    var symbol: String {
        switch self {
        case .approve: return "checkmark.seal.fill"
        case .revise: return "pencil.circle.fill"
        case .escalate: return "person.crop.circle.badge.exclamationmark"
        case .reject: return "xmark.octagon.fill"
        }
    }
}

/// ADQA (NGS-0024) result: 10 attributes -> DQS -> Decision Guardian.
struct ADQAAssessment: Codable, Equatable {
    var attributes: [String: Int]
    var dqs: Int
    var guardian: ADQAGuardian
    var constitution: [String: String]
    var riskBand: String
    var reasons: [String]
    var recommendation: String?
    var source: String          // "model" or "heuristic"
    var model: String?
    var scoredAt: Date
    var standard: String = "NGS-0024"
}

struct AIMessage: Codable, Identifiable, Equatable {
    var id: UUID = UUID()
    var role: AIRole
    var content: String
    var createdAt: Date = Date()
    var isError: Bool = false
    var adqa: ADQAAssessment?
    var adqaFailed: Bool = false
}

struct Conversation: Codable, Identifiable, Equatable {
    var id: UUID = UUID()
    var title: String = "New chat"
    var createdAt: Date = Date()
    var updatedAt: Date = Date()
    var messages: [AIMessage] = []
    var provider: String?
    var model: String?

    var preview: String {
        messages.last(where: { !$0.isError })?.content ?? "No messages yet"
    }
}
