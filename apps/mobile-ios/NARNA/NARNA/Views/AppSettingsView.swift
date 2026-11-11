//
//  AppSettingsView.swift
//  NARNA
//

import SwiftUI

struct AppSettingsView: View {
    @EnvironmentObject var app: AppState
    @EnvironmentObject var settings: LLMSettings
    @State private var showPairing = false
    @State private var showDesktopSettings = false
    @State private var confirmUnpair = false

    // Draft of the single AI configuration (saved with one tap).
    @State private var draftProvider: LLMProvider = .openai
    @State private var draftKey = ""
    @State private var draftModel = ""
    @State private var draftBaseURL = ""
    @State private var showAdvanced = false
    @State private var detectedNote: String?
    @State private var savedFlash = false
    @State private var loaded = false
    @State private var suppressProviderReset = false
    @State private var autoOpenModels = false

    private var version: String {
        let v = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
        let b = Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "1"
        return "\(v) (\(b))"
    }

    private var effectiveKey: String {
        let k = draftKey.trimmingCharacters(in: .whitespacesAndNewlines)
        return k.isEmpty ? (settings.apiKey ?? "") : k
    }

    private var effectiveBaseURL: String {
        let o = draftBaseURL.trimmingCharacters(in: .whitespacesAndNewlines)
        return o.isEmpty ? draftProvider.defaultBaseURL : o
    }

    private var canSave: Bool {
        !effectiveKey.isEmpty
            && !draftModel.trimmingCharacters(in: .whitespaces).isEmpty
            && URL(string: effectiveBaseURL)?.scheme?.hasPrefix("http") == true
    }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Picker("Provider", selection: $draftProvider) {
                        ForEach(LLMProvider.allCases) { p in Text(p.displayName).tag(p) }
                    }
                    SecureField(keyPlaceholder, text: $draftKey)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .textContentType(.password)
                    if let note = detectedNote {
                        Label(note, systemImage: "wand.and.stars").font(.caption).foregroundStyle(.secondary)
                    }
                    NavigationLink {
                        ModelPickerView(provider: draftProvider, baseURL: effectiveBaseURL,
                                        apiKey: effectiveKey, selection: $draftModel)
                    } label: {
                        LabeledContent("Model") {
                            Text(draftModel.isEmpty ? "Choose" : draftModel)
                                .font(.callout.monospaced()).lineLimit(1)
                        }
                    }
                    if draftProvider == .custom {
                        TextField("Base URL, e.g. https://api.example.com/v1", text: $draftBaseURL)
                            .textInputAutocapitalization(.never).autocorrectionDisabled().keyboardType(.URL)
                    } else {
                        DisclosureGroup("Advanced", isExpanded: $showAdvanced) {
                            TextField(draftProvider.defaultBaseURL, text: $draftBaseURL)
                                .textInputAutocapitalization(.never).autocorrectionDisabled().keyboardType(.URL)
                                .font(.callout.monospaced())
                            Text("Base URL override. Leave empty to use the \(draftProvider.displayName) default.")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    Button {
                        saveConfig()
                    } label: {
                        HStack {
                            Text("Save")
                            Spacer()
                            if savedFlash { Image(systemName: "checkmark.circle.fill").foregroundStyle(.green) }
                        }
                    }
                    .disabled(!canSave)
                } header: {
                    Text("AI Provider & API Key")
                } footer: {
                    Text("Pick a provider and paste its API key; the provider is detected from the key when possible. The key is stored only in this iPhone's Keychain (this device only, not synced) and is sent only to the provider you choose. Usage is billed by your provider.")
                }

                if let c = settings.config {
                    Section("In use") {
                        LabeledContent("Provider", value: c.provider.displayName)
                        LabeledContent("Model") { Text(c.model).font(.callout.monospaced()).lineLimit(1) }
                        LabeledContent("API key", value: "••••" + String(c.apiKey.suffix(4)))
                        Button("Remove saved key", role: .destructive) {
                            settings.clear()
                            draftKey = ""
                        }
                    }
                }

                Section {
                    Toggle("Score answers with ADQA", isOn: $settings.adqaEnabled)
                } header: {
                    Text("ADQA Decision Quality")
                } footer: {
                    Text("ADQA (NGS-0024) rates each answer on 10 attributes — evidence, policy, context, memory, risk, alignment, capability, compliance, confidence, explanation — and gives a Decision Quality Score with a verdict: Approve, Revise, Escalate or Reject. The assessment is AI-generated by your model (one extra request per answer).")
                }

                Section {
                    if app.isPaired {
                        LabeledContent("Paired agent", value: KeychainService.shared.getAgentName() ?? "Desktop agent")
                        Button { app.selectedTab = .desktop } label: { Label("Open Desktop bots", systemImage: "desktopcomputer") }
                        Button { showDesktopSettings = true } label: { Label("Desktop connection settings", systemImage: "network") }
                        Button("Unpair desktop", role: .destructive) { confirmUnpair = true }
                    } else {
                        Button { showPairing = true } label: {
                            Label("Pair with desktop (optional)", systemImage: "qrcode.viewfinder")
                        }
                    }
                } header: {
                    Text("NARNA Desktop")
                } footer: {
                    Text("Optional. If you run the NARNA desktop agent, pair to monitor its bots and approve actions from your phone. Not needed to use NaNa Bot.")
                }

                Section {
                    Label("We don't collect any data. No account, no analytics, no tracking.", systemImage: "hand.raised.fill")
                    Label("API keys and chat history stay on this iPhone.", systemImage: "iphone")
                    Label("Messages go directly from your iPhone to the AI provider you choose, under that provider's terms.", systemImage: "arrow.up.right.circle")
                } header: {
                    Text("Privacy")
                }
                .font(.callout)

                Section("About") {
                    LabeledContent("App", value: "NaNa Bot")
                    LabeledContent("Version", value: version)
                }
            }
            .navigationTitle("Settings")
            .sheet(isPresented: $showPairing) {
                PairingView(isPaired: $app.isPaired)
            }
            .sheet(isPresented: $showDesktopSettings) {
                SettingsView()
            }
            .onChange(of: app.isPaired) { _, paired in
                if paired { showPairing = false }
            }
            .onAppear {
                loadDraft()
                #if DEBUG
                if ProcessInfo.processInfo.arguments.contains("-NARNA_OPEN_MODELS") { autoOpenModels = true }
                #endif
            }
            .navigationDestination(isPresented: $autoOpenModels) {
                ModelPickerView(provider: draftProvider, baseURL: effectiveBaseURL,
                                apiKey: effectiveKey, selection: $draftModel)
            }
            .onChange(of: draftProvider) { _, newValue in
                if suppressProviderReset { suppressProviderReset = false; return }
                draftModel = newValue.defaultModel
                draftBaseURL = ""
                detectedNote = nil
            }
            .onChange(of: draftKey) { _, newValue in detectProvider(newValue) }
            .alert("Unpair desktop?", isPresented: $confirmUnpair) {
                Button("Cancel", role: .cancel) {}
                Button("Unpair", role: .destructive) { app.unpair() }
            } message: {
                Text("Chat keeps working. You can pair again any time.")
            }
        }
    }

    private var keyPlaceholder: String {
        if let c = settings.config, draftKey.isEmpty {
            return "Saved key ••••\(c.apiKey.suffix(4)) — paste to replace"
        }
        return "Paste API key (\(draftProvider.keyPlaceholder))"
    }

    private func loadDraft() {
        guard !loaded else { return }
        loaded = true
        suppressProviderReset = true
        let c = settings.config
        draftProvider = c?.provider ?? .openai
        draftModel = c?.model ?? draftProvider.defaultModel
        draftBaseURL = c?.baseURLOverride ?? ""
        showAdvanced = !(c?.baseURLOverride.isEmpty ?? true) && c?.provider != .custom
        if c?.provider == nil || c?.provider == .openai { suppressProviderReset = false }
    }

    private func detectProvider(_ key: String) {
        guard let (p, strong) = LLMProvider.detect(fromKey: key) else { detectedNote = nil; return }
        let sharesSkPrefix: Set<LLMProvider> = [.openai, .ckey, .deepseek, .together, .mistral, .custom]
        if strong {
            if p != draftProvider { draftProvider = p }
            detectedNote = "Detected a \(p.displayName) key"
        } else if !sharesSkPrefix.contains(draftProvider) {
            draftProvider = .openai
            detectedNote = "Looks like an OpenAI-style key (sk-). Pick ckey.vn or DeepSeek above if it's from them."
        } else {
            detectedNote = nil
        }
    }

    private func saveConfig() {
        settings.save(LLMConfig(provider: draftProvider, model: draftModel,
                                baseURLOverride: draftBaseURL, apiKey: effectiveKey))
        draftKey = ""
        detectedNote = nil
        savedFlash = true
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) { savedFlash = false }
    }

}

/// Searchable model list fetched live from GET {base}/models, with typed-ID fallback.
struct ModelPickerView: View {
    let provider: LLMProvider
    let baseURL: String
    let apiKey: String
    @Binding var selection: String
    @Environment(\.dismiss) private var dismiss
    @State private var models: [String] = []
    @State private var loading = false
    @State private var errorText: String?
    @State private var query = ""
    @State private var typed = ""

    private var filtered: [String] {
        let list = models.isEmpty ? provider.suggestedModels : models
        guard !query.isEmpty else { return list }
        return list.filter { $0.localizedCaseInsensitiveContains(query) }
    }

    var body: some View {
        List {
            Section {
                HStack {
                    TextField("Type a model ID", text: $typed)
                        .textInputAutocapitalization(.never).autocorrectionDisabled()
                        .font(.callout.monospaced())
                    Button("Use") { selection = typed.trimmingCharacters(in: .whitespaces); dismiss() }
                        .disabled(typed.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            } footer: {
                if let e = errorText {
                    Text("Couldn't load the model list: \(e)\nShowing suggested models; you can also type any model ID.")
                        .foregroundStyle(.orange)
                }
            }

            Section(models.isEmpty ? "Suggested" : "\(provider.displayName) models (\(models.count))") {
                if loading {
                    HStack { ProgressView(); Text("Loading models…").foregroundStyle(.secondary) }
                }
                ForEach(filtered, id: \.self) { m in
                    Button {
                        selection = m
                        dismiss()
                    } label: {
                        HStack {
                            Text(m).font(.callout.monospaced()).foregroundStyle(.primary)
                            Spacer()
                            if m == selection { Image(systemName: "checkmark").foregroundStyle(Color.accentColor) }
                        }
                    }
                }
            }
        }
        .searchable(text: $query, prompt: "Search models")
        .navigationTitle("Model")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button { Task { await load() } } label: { Image(systemName: "arrow.clockwise") }
                    .disabled(loading)
            }
        }
        .task { typed = selection; await load() }
    }

    private func load() async {
        loading = true
        errorText = nil
        defer { loading = false }
        do {
            models = try await LLMService.shared.listModels(provider: provider, baseURL: baseURL, apiKey: apiKey)
            if models.isEmpty { errorText = "the provider returned no models" }
        } catch {
            models = []
            errorText = error.localizedDescription
        }
    }
}
