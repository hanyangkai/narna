//
//  AppSettingsView.swift
//  NARNA
//
//  Nana AI settings: Engine Auto, Advanced BYOK, privacy, desktop pairing link.
//

import SwiftUI

struct AppSettingsView: View {
    @ObservedObject var chatViewModel: AIChatViewModel
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject var apiService: NARNAAPIService

    @State private var openRouterDraft = ""
    @State private var openAIDraft = ""
    @State private var showPairing = false
    @State private var isPaired = false

    private let keychain = KeychainService.shared

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    LabeledContent(String(localized: "settings_app_row"), value: PinnedBot.name)
                    LabeledContent(
                        String(localized: "settings_version"),
                        value: Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.1"
                    )
                    LabeledContent(
                        "Build",
                        value: Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "—"
                    )
                } header: {
                    Text(String(localized: "settings_about"))
                }

                Section {
                    Picker(String(localized: "settings_engine"), selection: Binding(
                        get: { chatViewModel.enginePreference },
                        set: { chatViewModel.setEnginePreference($0) }
                    )) {
                        Text(ChatEngineKind.auto.settingsLabel).tag(ChatEngineKind.auto)
                        Text(ChatEngineKind.onDevice.settingsLabel).tag(ChatEngineKind.onDevice)
                        Text(ChatEngineKind.freePool.settingsLabel).tag(ChatEngineKind.freePool)
                        if keychain.getOpenRouterKey() != nil {
                            Text(ChatEngineKind.byoOpenRouter.settingsLabel).tag(ChatEngineKind.byoOpenRouter)
                        }
                        if keychain.getOpenAIKey() != nil {
                            Text(ChatEngineKind.byoOpenAI.settingsLabel).tag(ChatEngineKind.byoOpenAI)
                        }
                    }
                    Text(chatViewModel.appleAvailability.friendlyMessage)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                    if chatViewModel.appleAvailability.suggestsOpenSettings {
                        Button(String(localized: "open_settings")) {
                            chatViewModel.openAppleIntelligenceSettings()
                        }
                    }
                } header: {
                    Text(String(localized: "settings_engine"))
                } footer: {
                    Text(String(localized: "settings_engine_footer"))
                }

                DisclosureGroup(String(localized: "settings_advanced")) {
                    SecureField("OpenRouter sk-or-…", text: $openRouterDraft)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                    Button(String(localized: "save_openrouter_key")) {
                        keychain.saveOpenRouterKey(openRouterDraft)
                        openRouterDraft = ""
                        chatViewModel.setEnginePreference(.byoOpenRouter)
                    }
                    .disabled(openRouterDraft.trimmingCharacters(in: .whitespacesAndNewlines).count < 8)

                    SecureField("OpenAI sk-…", text: $openAIDraft)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                    Button(String(localized: "save_openai_key")) {
                        keychain.saveOpenAIKey(openAIDraft)
                        openAIDraft = ""
                        chatViewModel.setEnginePreference(.byoOpenAI)
                    }
                    .disabled(openAIDraft.trimmingCharacters(in: .whitespacesAndNewlines).count < 8)

                    if keychain.hasAnyBYOKey {
                        Button(String(localized: "clear_byo_keys"), role: .destructive) {
                            keychain.clearBYOKeys()
                            chatViewModel.setEnginePreference(.auto)
                        }
                    }
                }

                Section {
                    Text(String(localized: "privacy_on_device"))
                        .font(.footnote)
                    Text(String(localized: "privacy_free_cloud"))
                        .font(.footnote)
                    Link(String(localized: "privacy_policy"), destination: URL(string: "https://narna.org/privacy")!)
                } header: {
                    Text(String(localized: "privacy_section"))
                }

                Section {
                    Button(String(localized: "pair_desktop_agent")) {
                        showPairing = true
                    }
                } footer: {
                    Text(String(localized: "pair_desktop_footer"))
                }
            }
            .navigationTitle(String(localized: "settings_title"))
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button(String(localized: "done")) { dismiss() }
                }
            }
            .sheet(isPresented: $showPairing) {
                NavigationStack {
                    PairingView(isPaired: $isPaired, onBack: { showPairing = false })
                }
            }
            .onAppear {
                isPaired = keychain.getMobileToken() != nil
            }
        }
    }
}
