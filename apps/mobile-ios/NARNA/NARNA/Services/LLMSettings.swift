//
//  LLMSettings.swift
//  NARNA
//
//  User-chosen provider / model. API keys live only in the Keychain.
//

import Foundation
import Combine

@MainActor
final class LLMSettings: ObservableObject {
    static let shared = LLMSettings()

    private let defaults = UserDefaults.standard

    @Published var provider: LLMProvider {
        didSet { defaults.set(provider.rawValue, forKey: "llm_provider"); refreshKeyState() }
    }
    @Published var model: String {
        didSet { defaults.set(model, forKey: "llm_model_\(provider.rawValue)") }
    }
    @Published var compatibleBaseURL: String {
        didSet { defaults.set(compatibleBaseURL, forKey: "llm_compat_base_url") }
    }
    @Published var adqaEnabled: Bool {
        didSet { defaults.set(adqaEnabled, forKey: "adqa_enabled") }
    }
    @Published private(set) var hasKey: Bool = false

    private init() {
        let p = LLMProvider(rawValue: defaults.string(forKey: "llm_provider") ?? "") ?? .openai
        provider = p
        model = defaults.string(forKey: "llm_model_\(p.rawValue)") ?? p.defaultModel
        compatibleBaseURL = defaults.string(forKey: "llm_compat_base_url") ?? ""
        adqaEnabled = defaults.object(forKey: "adqa_enabled") as? Bool ?? true
        #if DEBUG
        // Simulator test hook: exercises the same Keychain save path as the Settings "Save key" button.
        let args = ProcessInfo.processInfo.arguments
        if let k = ProcessInfo.processInfo.environment["NARNA_TEST_KEY"], !k.isEmpty {
            KeychainService.shared.saveAPIKey(k, account: provider.keychainAccount)
        }
        if args.contains("-NARNA_TEST_CLEARKEY") {
            KeychainService.shared.deleteAPIKey(account: provider.keychainAccount)
        }
        #endif
        refreshKeyState()
    }

    func selectProvider(_ p: LLMProvider) {
        provider = p
        model = defaults.string(forKey: "llm_model_\(p.rawValue)") ?? p.defaultModel
    }

    var baseURL: String {
        provider == .openaiCompatible ? compatibleBaseURL : provider.defaultBaseURL
    }

    var apiKey: String? { KeychainService.shared.getAPIKey(account: provider.keychainAccount) }

    var isReady: Bool {
        guard hasKey, !model.trimmingCharacters(in: .whitespaces).isEmpty else { return false }
        if provider == .openaiCompatible { return URL(string: compatibleBaseURL)?.scheme?.hasPrefix("http") == true }
        return true
    }

    func saveKey(_ key: String) {
        let trimmed = key.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        KeychainService.shared.saveAPIKey(trimmed, account: provider.keychainAccount)
        refreshKeyState()
    }

    func removeKey() {
        KeychainService.shared.deleteAPIKey(account: provider.keychainAccount)
        refreshKeyState()
    }

    func refreshKeyState() {
        #if DEBUG
        if ProcessInfo.processInfo.arguments.contains("-NARNA_DEMO_MOCK") { hasKey = true; return }
        #endif
        hasKey = KeychainService.shared.getAPIKey(account: provider.keychainAccount) != nil
    }
}
