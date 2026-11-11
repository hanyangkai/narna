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
    case openaiCompatible

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .openai: return "OpenAI"
        case .anthropic: return "Anthropic"
        case .openaiCompatible: return "OpenAI-compatible"
        }
    }

    var defaultModels: [String] {
        switch self {
        case .openai: return ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini", "gpt-4o", "gpt-5-mini", "gpt-5"]
        case .anthropic: return ["claude-sonnet-4-5", "claude-haiku-4-5", "claude-opus-4-1"]
        case .openaiCompatible: return []
        }
    }

    var defaultModel: String {
        switch self {
        case .openai: return "gpt-4.1-mini"
        case .anthropic: return "claude-sonnet-4-5"
        case .openaiCompatible: return ""
        }
    }

    var defaultBaseURL: String {
        switch self {
        case .openai: return "https://api.openai.com/v1"
        case .anthropic: return "https://api.anthropic.com/v1"
        case .openaiCompatible: return ""
        }
    }

    var keyPlaceholder: String {
        switch self {
        case .openai: return "sk-..."
        case .anthropic: return "sk-ant-..."
        case .openaiCompatible: return "API key"
        }
    }

    var keychainAccount: String { "llm_api_key_\(rawValue)" }
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
