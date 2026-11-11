//
//  LLMSettings.swift
//  NARNA
//
//  One saved AI configuration (provider + model + optional base URL + API key),
//  stored as a single Keychain item on this device only.
//

import Foundation
import Combine

@MainActor
final class LLMSettings: ObservableObject {
    static let shared = LLMSettings()

    private let defaults = UserDefaults.standard
    private static let configAccount = "llm_config_v1"

    @Published private(set) var config: LLMConfig?
    @Published var adqaEnabled: Bool {
        didSet { defaults.set(adqaEnabled, forKey: "adqa_enabled") }
    }

    private init() {
        adqaEnabled = defaults.object(forKey: "adqa_enabled") as? Bool ?? true
        config = Self.loadConfig()
        #if DEBUG
        // Simulator test hook: saves through the same path as the Settings "Save" button.
        if let k = ProcessInfo.processInfo.environment["NARNA_TEST_KEY"], !k.isEmpty {
            let args = ProcessInfo.processInfo.arguments
            var p = LLMProvider.detect(fromKey: k)?.provider
            if let i = args.firstIndex(of: "-NARNA_TEST_PROVIDER"), i + 1 < args.count,
               let forced = LLMProvider(rawValue: args[i + 1]) { p = forced }
            if let p {
                save(LLMConfig(provider: p, model: p.defaultModel, apiKey: k))
            }
        }
        if ProcessInfo.processInfo.arguments.contains("-NARNA_TEST_CLEARKEY") { clear() }
        #endif
    }

    // MARK: Read

    var provider: LLMProvider { config?.provider ?? .openai }
    var model: String { config?.model ?? provider.defaultModel }
    var baseURL: String { config?.baseURL ?? provider.defaultBaseURL }
    var apiKey: String? {
        guard let k = config?.apiKey, !k.isEmpty else { return nil }
        return k
    }

    var hasKey: Bool {
        #if DEBUG
        if ProcessInfo.processInfo.arguments.contains("-NARNA_DEMO_MOCK") { return true }
        #endif
        return apiKey != nil
    }

    var isReady: Bool {
        guard hasKey, !model.trimmingCharacters(in: .whitespaces).isEmpty else { return false }
        return URL(string: baseURL)?.scheme?.hasPrefix("http") == true
    }

    // MARK: Write

    func save(_ c: LLMConfig) {
        var c = c
        c.apiKey = c.apiKey.trimmingCharacters(in: .whitespacesAndNewlines)
        c.model = c.model.trimmingCharacters(in: .whitespacesAndNewlines)
        c.baseURLOverride = c.baseURLOverride.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let data = try? JSONEncoder().encode(c), let json = String(data: data, encoding: .utf8) else { return }
        KeychainService.shared.saveAPIKey(json, account: Self.configAccount)
        config = c
    }

    func clear() {
        KeychainService.shared.deleteAPIKey(account: Self.configAccount)
        config = nil
    }

    private static func loadConfig() -> LLMConfig? {
        if let json = KeychainService.shared.getAPIKey(account: configAccount),
           let data = json.data(using: .utf8),
           let c = try? JSONDecoder().decode(LLMConfig.self, from: data) {
            return c
        }
        // Migrate build-2 storage (per-provider key slot + UserDefaults provider/model).
        let d = UserDefaults.standard
        let p = LLMProvider(rawValue: d.string(forKey: "llm_provider") ?? "") ?? .openai
        guard let oldKey = KeychainService.shared.getAPIKey(account: "llm_api_key_\(p.rawValue)") else { return nil }
        let c = LLMConfig(provider: p,
                          model: d.string(forKey: "llm_model_\(p.rawValue)") ?? p.defaultModel,
                          baseURLOverride: p == .custom ? (d.string(forKey: "llm_compat_base_url") ?? "") : "",
                          apiKey: oldKey)
        if let data = try? JSONEncoder().encode(c), let json = String(data: data, encoding: .utf8) {
            KeychainService.shared.saveAPIKey(json, account: configAccount)
            for old in LLMProvider.allCases { KeychainService.shared.deleteAPIKey(account: "llm_api_key_\(old.rawValue)") }
        }
        return c
    }
}
