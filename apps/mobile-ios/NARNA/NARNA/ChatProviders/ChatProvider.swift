//
//  ChatProvider.swift
//  NARNA
//
//  LLMProvider + ProviderRouter — free chat failover (on-device → free pool).
//

import Foundation

/// Official chat backends only. No scraping of chatgpt.com / gemini.google.com / claude.ai.
protocol LLMProvider: Sendable {
    var engineDisplayName: String { get }
    func stream(messages: [ChatProviderMessage]) async throws -> AsyncStream<String>
}

typealias ChatProvider = LLMProvider

protocol AppleAvailabilityChecking: Sendable {
    func availability() -> AppleModelAvailabilityReason
}

enum FreePoolConfig {
    /// Overridable via Info.plist `FREE_POOL_URL` or build setting.
    static var baseURL: URL {
        if let raw = Bundle.main.object(forInfoDictionaryKey: "FREE_POOL_URL") as? String,
           let url = URL(string: raw), !raw.isEmpty {
            return url
        }
        // Placeholder worker host — replace after deploy; no secrets here.
        return URL(string: "https://nana-free-pool.example.workers.dev")!
    }
}

/// Client-side engine selection. Upstream free-tier failover (429/503/timeout) lives in the Worker.
enum ProviderRouter {
    /// Nana Auto: Apple on-device when available, else free pool. BYOK / Agent only when user picks them.
    static func resolve(
        preference: ChatEngineKind,
        appleChecker: AppleAvailabilityChecking,
        hasBYOKey: Bool
    ) -> (providerKind: ChatEngineKind, availabilityNote: AppleModelAvailabilityReason?) {
        switch preference {
        case .auto:
            let avail = appleChecker.availability()
            if avail == .available {
                return (.onDevice, avail)
            }
            return (.freePool, avail)
        case .onDevice:
            return (.onDevice, appleChecker.availability())
        case .freePool:
            return (.freePool, nil)
        case .byoOpenRouter, .byoOpenAI, .agent:
            return (preference, nil)
        }
    }

    /// Map Worker `X-Nana-Engine` / local ids to UI labels under answers.
    static func friendlyModelLabel(_ raw: String) -> String {
        let s = raw.lowercased()
        if s.contains("on-device") || s.contains("apple") || s == "foundation" {
            return "Apple on-device"
        }
        if s.contains("gpt-oss") || s.contains("workers-ai") {
            return "GPT-OSS"
        }
        if s.contains("gemma") {
            return "Gemma"
        }
        if s.contains("gemini") {
            return "Gemini Flash"
        }
        if s.contains("groq") {
            return s.contains("gpt-oss") ? "GPT-OSS" : "Groq"
        }
        if s.contains("openrouter") {
            if s.contains("gemma") { return "Gemma" }
            if s.contains("gpt-oss") { return "GPT-OSS" }
            return "OpenRouter free"
        }
        if s.contains("zai") || s.contains("glm") {
            return "GLM Flash"
        }
        if s.contains("agent") {
            return "Agent"
        }
        if s.contains("llama") {
            return "Llama"
        }
        if s.contains("qwen") {
            return "Qwen"
        }
        return raw.isEmpty ? "Free cloud" : raw
    }
}

typealias ChatRouter = ProviderRouter
