//
//  AIChatViewModel.swift
//  NARNA
//

import Foundation
import Combine
import UIKit

@MainActor
final class AIChatViewModel: ObservableObject {
    @Published var turns: [ChatTurn] = []
    @Published var inputText = ""
    @Published var isStreaming = false
    @Published var errorMessage: String?
    @Published var showError = false
    @Published var showDailyLimitPaywall = false
    @Published var showAgentPaywall = false
    @Published var lastEngineLabel: String?
    @Published var appleAvailability: AppleModelAvailabilityReason = .unsupportedOS
    @Published var enginePreference: ChatEngineKind = .auto

    private let keychain = KeychainService.shared
    private let appleChecker: AppleAvailabilityChecking
    private var streamTask: Task<Void, Never>?

    init(appleChecker: AppleAvailabilityChecking = DefaultAppleAvailabilityChecker()) {
        self.appleChecker = appleChecker
        if let raw = UserDefaults.standard.string(forKey: "nana_engine_preference"),
           let pref = ChatEngineKind(rawValue: raw) {
            enginePreference = pref
        }
        refreshAvailability()
        if turns.isEmpty {
            turns.append(
                ChatTurn(
                    role: "assistant",
                    content: String(localized: "nana_welcome_message"),
                    engineLabel: "Nana AI"
                )
            )
        }
    }

    func refreshAvailability() {
        appleAvailability = appleChecker.availability()
    }

    func setEnginePreference(_ kind: ChatEngineKind) {
        enginePreference = kind
        UserDefaults.standard.set(kind.rawValue, forKey: "nana_engine_preference")
    }

    func openAppleIntelligenceSettings() {
        if let url = URL(string: UIApplication.openSettingsURLString) {
            UIApplication.shared.open(url)
        }
    }

    func sendMessage() {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !isStreaming else { return }
        inputText = ""
        errorMessage = nil

        turns.append(ChatTurn(role: "user", content: text))
        let assistantId = UUID().uuidString
        turns.append(ChatTurn(id: assistantId, role: "assistant", content: "", engineLabel: nil))
        isStreaming = true

        streamTask?.cancel()
        streamTask = Task { [weak self] in
            guard let self else { return }
            do {
                let (provider, label) = try await self.makeProvider()
                self.lastEngineLabel = label
                if let idx = self.turns.firstIndex(where: { $0.id == assistantId }) {
                    self.turns[idx].engineLabel = label
                }
                let history = self.turns
                    .filter { $0.id != assistantId && ($0.role == "user" || $0.role == "assistant") }
                    .filter { !($0.role == "assistant" && $0.content.isEmpty) }
                    .map { ChatProviderMessage(role: $0.role, content: $0.content) }

                let stream = try await provider.stream(messages: history)
                // Prefer live FreePool engine label after headers arrive
                if let free = provider as? FreePoolProvider {
                    let live = free.engineDisplayName
                    if let idx = self.turns.firstIndex(where: { $0.id == assistantId }) {
                        self.turns[idx].engineLabel = live
                        self.lastEngineLabel = live
                    }
                }
                for await chunk in stream {
                    if Task.isCancelled { break }
                    if let idx = self.turns.firstIndex(where: { $0.id == assistantId }) {
                        self.turns[idx].content += chunk
                        if let free = provider as? FreePoolProvider {
                            self.turns[idx].engineLabel = free.engineDisplayName
                        }
                    }
                }
                if let idx = self.turns.firstIndex(where: { $0.id == assistantId }),
                   self.turns[idx].content.isEmpty {
                    self.turns[idx].content = "…"
                }
            } catch let err as ChatProviderError {
                self.handleProviderError(err, assistantId: assistantId)
            } catch {
                self.showErrorMessage(error.localizedDescription)
                self.removeEmptyAssistant(assistantId)
            }
            self.isStreaming = false
        }
    }

    private func makeProvider() async throws -> (LLMProvider, String) {
        let (kind, note) = ProviderRouter.resolve(
            preference: enginePreference,
            appleChecker: appleChecker,
            hasBYOKey: keychain.hasAnyBYOKey
        )
        if let note, kind == .onDevice, note != .available {
            throw ChatProviderError.unavailable(note.friendlyMessage)
        }
        switch kind {
        case .onDevice, .auto:
            return (AppleOnDeviceProvider(checker: appleChecker), "Apple on-device")
        case .freePool:
            let id = keychain.getOrCreateDeviceId()
            let token = await DeviceAttestationService.deviceCheckToken()
            let p = FreePoolProvider(deviceId: id, deviceToken: token)
            return (p, p.engineDisplayName)
        case .agent:
            let store = AgentStoreKitService.shared
            guard store.isSubscribed || store.signedTransactionJWS != nil else {
                throw ChatProviderError.agentPaywallRequired
            }
            let id = keychain.getOrCreateDeviceId()
            let p = AgentProvider(
                baseURL: AgentProvider.defaultAPIBase,
                deviceId: id,
                signedTransaction: store.signedTransactionJWS
            )
            return (p, "Agent")
        case .byoOpenRouter:
            guard let key = keychain.getOpenRouterKey(), !key.isEmpty else {
                throw ChatProviderError.invalidKey
            }
            let p = BYOKeyProvider(kind: .openrouter, apiKey: key)
            return (p, p.engineDisplayName)
        case .byoOpenAI:
            guard let key = keychain.getOpenAIKey(), !key.isEmpty else {
                throw ChatProviderError.invalidKey
            }
            let p = BYOKeyProvider(kind: .openai, apiKey: key)
            return (p, p.engineDisplayName)
        }
    }

    private func handleProviderError(_ err: ChatProviderError, assistantId: String) {
        removeEmptyAssistant(assistantId)
        switch err {
        case .dailyLimitReached:
            errorMessage = String(localized: "free_daily_limit_reached")
            showDailyLimitPaywall = true
        case .agentPaywallRequired:
            errorMessage = String(localized: "agent_paywall_required")
            showAgentPaywall = true
        default:
            showErrorMessage(err.localizedDescription)
        }
    }

    private func removeEmptyAssistant(_ id: String) {
        if let idx = turns.firstIndex(where: { $0.id == id }), turns[idx].content.isEmpty {
            turns.remove(at: idx)
        }
    }

    private func showErrorMessage(_ message: String) {
        errorMessage = message
        showError = true
    }
}
