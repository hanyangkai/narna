//
//  ChatProviderRouter.swift
//  NARNA
//
//  Pure routing for Nana AI 1.1: on-device Foundation Models first,
//  then the free-pool Worker, optional BYOK, or paid Agent mode.
//  No provider keys live in this type.
//

import Foundation

enum ChatProviderKind: String, Equatable {
    case onDevice
    case freePool
    case byok
    case agent
    case paywall
    case unavailable
}

struct ChatProviderRouteInput: Equatable {
    var onDeviceAvailable: Bool
    var freePoolConfigured: Bool
    var useOwnAPIKey: Bool
    var hasBYOK: Bool
    var agentModeEnabled: Bool
    var isSubscribed: Bool
    var agentCreditsRemaining: Int
}

enum ChatProviderRouter {
    /// Resolve which chat backend should handle the next message.
    static func resolve(_ input: ChatProviderRouteInput) -> ChatProviderKind {
        if input.agentModeEnabled {
            guard input.isSubscribed else { return .paywall }
            guard input.agentCreditsRemaining > 0 else { return .paywall }
            return .agent
        }
        if input.useOwnAPIKey && input.hasBYOK {
            return .byok
        }
        if input.onDeviceAvailable {
            return .onDevice
        }
        if input.freePoolConfigured {
            return .freePool
        }
        return .unavailable
    }

    /// Human-readable label for the nav bar / bubble caption.
    static func displayName(for kind: ChatProviderKind, modelDisplayName: String?) -> String {
        if let modelDisplayName, !modelDisplayName.isEmpty { return modelDisplayName }
        switch kind {
        case .onDevice: return "On-device"
        case .freePool: return "Free"
        case .byok: return "Your API key"
        case .agent: return "Agent"
        case .paywall, .unavailable: return ""
        }
    }
}

/// Canonical free-pool model ids and the names shown in the chat UI.
/// Mirrors services/free-pool-worker routing. On-device Apple FM is chosen
/// in ChatProviderRouter *before* this pool is contacted.
///
/// Worker order (429/503 failover), all ids configurable via Worker env:
///   1. Cloudflare Workers AI gpt-oss-120b / 20b (no external key; primary gpt-oss path)
///   2. Groq gpt-oss-120b / 20b — optional, skipped when GROQ_API_KEY is unset
///   3. Google AI Studio Gemini 3.8 Flash / Flash-Lite / Gemma 4
///      (skipped for EEA / UK / CH users)
///   4. Cloudflare Workers AI Llama / Gemma / Qwen
///   5. OpenRouter :free
///   6. Z.AI GLM-4.7-Flash
enum FreePoolModelCatalog {
    struct Entry: Equatable {
        let id: String
        let displayName: String
        let family: Family
        let provider: Provider
        var isGoogle: Bool { provider == .google }
    }

    enum Provider: String, Equatable {
        case groq, google, workersAI, openRouter, zai
    }

    enum Family: String, Equatable {
        case geminiFlash = "Gemini Flash"
        case gptOss = "GPT-OSS"
        case gemma = "Gemma"
        case llama = "Llama"
        case qwen = "Qwen"
        case glm = "GLM"
    }

    /// Default Gemini Flash model id. The Worker may override via env GEMINI_MODEL.
    /// gemini-2.5-flash is closed to new users; gemini-3.8-flash is the default.
    static let defaultGeminiModelID = "gemini-3.8-flash"

    static let defaultGLMModelID = "glm-4.7-flash"

    /// Priority order used when every provider is enabled and Google is allowed.
    static let routePriority: [Entry] = workersAIGptOssEntries + groqEntries + googleEntries + workersAIOtherEntries + openRouterEntries + zaiEntries

    static let groqEntries: [Entry] = [
        Entry(id: "openai/gpt-oss-120b", displayName: "GPT-OSS", family: .gptOss, provider: .groq),
        Entry(id: "openai/gpt-oss-20b", displayName: "GPT-OSS", family: .gptOss, provider: .groq),
    ]

    static let googleEntries: [Entry] = [
        Entry(id: defaultGeminiModelID, displayName: "Gemini Flash", family: .geminiFlash, provider: .google),
        Entry(id: "gemini-3.8-flash-lite", displayName: "Gemini Flash", family: .geminiFlash, provider: .google),
        Entry(id: "gemini-3.6-flash", displayName: "Gemini Flash", family: .geminiFlash, provider: .google),
        Entry(id: "gemma-4-31b-it", displayName: "Gemma", family: .gemma, provider: .google),
        Entry(id: "gemma-4-26b-it", displayName: "Gemma", family: .gemma, provider: .google),
    ]

    /// Primary gpt-oss path: Workers AI binding, no Groq key required.
    static let workersAIGptOssEntries: [Entry] = [
        Entry(id: "@cf/openai/gpt-oss-120b", displayName: "GPT-OSS", family: .gptOss, provider: .workersAI),
        Entry(id: "@cf/openai/gpt-oss-20b", displayName: "GPT-OSS", family: .gptOss, provider: .workersAI),
    ]

    static let workersAIOtherEntries: [Entry] = [
        Entry(id: "@cf/meta/llama-3.1-8b-instruct-fp8-fast", displayName: "Llama", family: .llama, provider: .workersAI),
        Entry(id: "@cf/google/gemma-4-26b-a4b-it", displayName: "Gemma", family: .gemma, provider: .workersAI),
        Entry(id: "@cf/qwen/qwen3.8-27b", displayName: "Qwen", family: .qwen, provider: .workersAI),
    ]

    static var workersAIEntries: [Entry] { workersAIGptOssEntries + workersAIOtherEntries }

    static let openRouterEntries: [Entry] = [
        Entry(id: "google/gemma-4-31b-it:free", displayName: "Gemma", family: .gemma, provider: .openRouter),
        Entry(id: "google/gemma-4-26b-a4b-it:free", displayName: "Gemma", family: .gemma, provider: .openRouter),
        Entry(id: "openrouter/free", displayName: "Gemma", family: .gemma, provider: .openRouter),
    ]

    static let zaiEntries: [Entry] = [
        Entry(id: defaultGLMModelID, displayName: "GLM", family: .glm, provider: .zai),
    ]

    /// EEA (EU27 + IS, LI, NO) plus the United Kingdom and Switzerland.
    /// Google unpaid Gemini/Gemma API must not be used for these users.
    static let googleRestrictedRegions: Set<String> = [
        "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
        "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
        "SI", "ES", "SE", "IS", "LI", "NO", "GB", "UK", "CH",
    ]

    static func shouldSkipGoogle(regionCode: String?) -> Bool {
        guard let raw = regionCode?.trimmingCharacters(in: .whitespacesAndNewlines), !raw.isEmpty else {
            return false
        }
        return googleRestrictedRegions.contains(raw.uppercased())
    }

    static func routes(skipGoogle: Bool) -> [Entry] {
        skipGoogle ? routePriority.filter { !$0.isGoogle } : routePriority
    }

    static func displayName(forModelId id: String) -> String {
        if let exact = routePriority.first(where: { $0.id == id }) {
            return exact.displayName
        }
        let lower = id.lowercased()
        if lower.contains("gemini") { return Family.geminiFlash.rawValue }
        if lower.contains("gpt-oss") || lower.contains("gpt_oss") { return Family.gptOss.rawValue }
        if lower.contains("gemma") { return Family.gemma.rawValue }
        if lower.contains("llama") { return Family.llama.rawValue }
        if lower.contains("qwen") { return Family.qwen.rawValue }
        if lower.contains("glm") { return Family.glm.rawValue }
        if lower.contains("foundation") || lower.contains("on-device") { return "On-device" }
        return id
    }

    /// 429 rate limits and 503 "high demand" both fall through to the next provider.
    static func isRetryableStatus(_ code: Int, message: String? = nil) -> Bool {
        if code == 429 { return true }
        if code == 503 {
            // Gemini free tier often returns 503 "high demand"; treat like 429.
            return true
        }
        return false
    }

    /// Next model to try after a retryable failure from `currentId`. Nil means the pool is exhausted.
    static func nextAfterRateLimit(currentId: String, skipGoogle: Bool = false) -> Entry? {
        let routes = Self.routes(skipGoogle: skipGoogle)
        guard let idx = routes.firstIndex(where: { $0.id == currentId }) else {
            return routes.first
        }
        let next = routes.index(after: idx)
        return next < routes.endIndex ? routes[next] : nil
    }
}

enum DeviceRegion {
    /// ISO region used to skip Google's unpaid API in the EEA, UK and Switzerland.
    /// Prefers the App Store storefront when StoreKit can see it; otherwise Locale.
    static var isoCode: String {
        (Locale.current.region?.identifier ?? "").uppercased()
    }
}
