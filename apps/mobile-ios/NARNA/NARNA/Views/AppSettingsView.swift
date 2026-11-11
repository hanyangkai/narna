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

    // Paste-only key setup: the provider and model list are resolved automatically.
    @State private var draftKey = ""
    @State private var draftModel = ""
    @State private var resolving = false
    @State private var keyStatus: KeyStatus = .none
    @State private var resolveTask: Task<Void, Never>?
    @State private var loaded = false
    @State private var autoOpenModels = false
    @State private var autoOpenAdvanced = false

    enum KeyStatus: Equatable {
        case none
        case ok(String)
        case failed
    }

    private var version: String {
        let v = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
        let b = Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "1"
        return "\(v) (\(b))"
    }

    private var effectiveKey: String {
        let k = draftKey.trimmingCharacters(in: .whitespacesAndNewlines)
        return k.isEmpty ? (settings.apiKey ?? "") : k
    }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    SecureField(keyPlaceholder, text: $draftKey)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .textContentType(.password)
                        .accessibilityLabel("API key")
                    if resolving {
                        HStack(spacing: 8) {
                            ProgressView().controlSize(.small)
                            Text("Đang kiểm tra key…").font(.caption).foregroundStyle(.secondary)
                        }
                    } else {
                        switch keyStatus {
                        case .ok(let text):
                            Label(text, systemImage: "checkmark.circle.fill")
                                .font(.callout.weight(.medium))
                                .foregroundStyle(.green)
                        case .failed:
                            Label("Key không hợp lệ với các nhà cung cấp đã hỗ trợ", systemImage: "xmark.octagon.fill")
                                .font(.callout)
                                .foregroundStyle(.orange)
                        case .none:
                            EmptyView()
                        }
                    }
                    if settings.config != nil {
                        NavigationLink {
                            ModelPickerView(provider: settings.provider, baseURL: settings.baseURL,
                                            apiKey: settings.apiKey ?? "", selection: $draftModel)
                        } label: {
                            LabeledContent("Model") {
                                Text(draftModel.isEmpty ? settings.model : draftModel)
                                    .font(.callout.monospaced()).lineLimit(1)
                            }
                        }
                    }
                    NavigationLink {
                        AdvancedProviderView(apiKey: effectiveKey) { status in keyStatus = status; syncModel() }
                    } label: {
                        LabeledContent("Advanced") {
                            Text("Provider & base URL").foregroundStyle(.secondary)
                        }
                    }
                } header: {
                    Text("API Key")
                } footer: {
                    Text("Just paste your API key. NaNa Bot recognises the provider and loads its models automatically. The key is stored only in this iPhone's Keychain (this device only, not synced) and is sent only to that provider. Usage is billed by your provider.")
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
                        Button { app.navigate(.desktop) } label: { Label("Open Desktop bots", systemImage: "desktopcomputer") }
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
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") { app.showSettings = false }
                        .fontWeight(.semibold)
                        .accessibilityLabel("Close Settings")
                }
            }
            .sheet(isPresented: $showPairing) {
                PairingView(isPaired: $app.isPaired)
                    .presentationDragIndicator(.visible)
            }
            .sheet(isPresented: $showDesktopSettings) {
                SettingsView()
                    .presentationDragIndicator(.visible)
            }
            .onChange(of: app.isPaired) { _, paired in
                if paired { showPairing = false }
            }
            .onAppear {
                loadDraft()
                #if DEBUG
                let args = ProcessInfo.processInfo.arguments
                if args.contains("-NARNA_OPEN_MODELS") { autoOpenModels = true }
                if args.contains("-NARNA_OPEN_ADVANCED") { autoOpenAdvanced = true }
                // Paste a key into the field for UI tests (same path as a real paste).
                if let i = args.firstIndex(of: "-NARNA_PASTE_KEY"), i + 1 < args.count, draftKey.isEmpty {
                    draftKey = args[i + 1]
                }
                #endif
            }
            .navigationDestination(isPresented: $autoOpenModels) {
                ModelPickerView(provider: settings.provider, baseURL: settings.baseURL,
                                apiKey: settings.apiKey ?? "", selection: $draftModel)
            }
            .navigationDestination(isPresented: $autoOpenAdvanced) {
                AdvancedProviderView(apiKey: effectiveKey) { status in keyStatus = status; syncModel() }
            }
            .onChange(of: draftKey) { _, newValue in resolve(newValue) }
            .onChange(of: draftModel) { _, newValue in
                let m = newValue.trimmingCharacters(in: .whitespaces)
                guard var c = settings.config, !m.isEmpty, m != c.model else { return }
                c.model = m
                settings.save(c)
            }
            .alert("Unpair desktop?", isPresented: $confirmUnpair) {
                Button("Cancel", role: .cancel) {}
                Button("Unpair", role: .destructive) { app.unpair() }
            } message: {
                Text("Chat keeps working. You can pair again any time.")
            }
        }
        .narnaTabRoot()
    }

    private var keyPlaceholder: String {
        if let c = settings.config, draftKey.isEmpty {
            return "Key đã lưu ••••\(c.apiKey.suffix(4)) — dán key mới để thay"
        }
        return "Dán API key"
    }

    private func loadDraft() {
        guard !loaded else { return }
        loaded = true
        syncModel()
    }

    private func syncModel() {
        draftModel = settings.config?.model ?? ""
    }

    /// Paste -> detect provider (prefix or probing) -> load models -> save. No Save button.
    private func resolve(_ raw: String) {
        resolveTask?.cancel()
        let key = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !key.isEmpty else {
            resolving = false
            keyStatus = .none
            return
        }
        resolveTask = Task { @MainActor in
            try? await Task.sleep(nanoseconds: 450_000_000)   // wait for the paste/typing to settle
            guard !Task.isCancelled else { return }
            resolving = true
            let result = await LLMService.shared.resolveKey(key)
            guard !Task.isCancelled else { return }
            resolving = false
            guard let r = result else {
                keyStatus = .failed
                return
            }
            let model = Self.pickModel(provider: r.provider, models: r.models,
                                       current: settings.config?.provider == r.provider ? settings.config?.model : nil)
            let override = r.baseURL == r.provider.defaultBaseURL ? "" : r.baseURL
            settings.save(LLMConfig(provider: r.provider, model: model, baseURLOverride: override, apiKey: key))
            draftModel = model
            keyStatus = .ok("Đã nhận key: \(r.provider.displayName) · \(r.models.count) models")
        }
    }

    static func pickModel(provider: LLMProvider, models: [String], current: String?) -> String {
        if let current, !current.isEmpty, models.isEmpty || models.contains(current) { return current }
        if models.isEmpty || models.contains(provider.defaultModel) { return provider.defaultModel }
        if let s = provider.suggestedModels.first(where: { models.contains($0) }) { return s }
        let chatty = models.first { m in
            let l = m.lowercased()
            return l.contains("gpt") || l.contains("claude") || l.contains("gemini") || l.contains("llama") || l.contains("deepseek") || l.contains("grok")
        }
        return chatty ?? models[0]
    }
}

/// Manual provider choice, only for people who need it (self-hosted / unusual endpoints).
struct AdvancedProviderView: View {
    let apiKey: String
    var onSaved: (AppSettingsView.KeyStatus) -> Void
    @EnvironmentObject var settings: LLMSettings
    @Environment(\.dismiss) private var dismiss
    @State private var provider: LLMProvider = .openai
    @State private var baseURL = ""
    @State private var checking = false
    @State private var errorText: String?

    private var effectiveBase: String {
        let o = baseURL.trimmingCharacters(in: .whitespacesAndNewlines)
        return o.isEmpty ? provider.defaultBaseURL : o
    }

    var body: some View {
        Form {
            Section {
                Picker("Provider", selection: $provider) {
                    ForEach(LLMProvider.allCases) { p in Text(p.displayName).tag(p) }
                }
                TextField(provider == .custom ? "https://api.example.com/v1" : provider.defaultBaseURL, text: $baseURL)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .keyboardType(.URL)
                    .font(.callout.monospaced())
            } header: {
                Text("Manual provider")
            } footer: {
                Text("Not needed normally: pasting a key picks the provider automatically. Use this only for a self-hosted or unusual OpenAI-compatible endpoint. Leave the URL empty to use the provider default.")
            }
            Section {
                Button {
                    Task { await apply() }
                } label: {
                    HStack {
                        Text("Use this provider")
                        Spacer()
                        if checking { ProgressView().controlSize(.small) }
                    }
                }
                .disabled(apiKey.isEmpty || checking || URL(string: effectiveBase)?.scheme?.hasPrefix("http") != true)
                if apiKey.isEmpty {
                    Text("Paste an API key first.").font(.caption).foregroundStyle(.secondary)
                }
                if let e = errorText {
                    Text(e).font(.caption).foregroundStyle(.orange)
                }
            }
        }
        .navigationTitle("Advanced")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar(.visible, for: .navigationBar)
        .onAppear {
            provider = settings.config?.provider ?? .openai
            baseURL = settings.config?.baseURLOverride ?? ""
        }
    }

    private func apply() async {
        checking = true
        errorText = nil
        defer { checking = false }
        do {
            let models = try await LLMService.shared.listModels(provider: provider, baseURL: effectiveBase, apiKey: apiKey)
            let model = AppSettingsView.pickModel(provider: provider, models: models,
                                                  current: settings.config?.provider == provider ? settings.config?.model : nil)
            let override = baseURL.trimmingCharacters(in: .whitespacesAndNewlines)
            settings.save(LLMConfig(provider: provider, model: model.isEmpty ? provider.defaultModel : model,
                                    baseURLOverride: override, apiKey: apiKey))
            onSaved(.ok("Đã nhận key: \(provider.displayName) · \(models.count) models"))
            dismiss()
        } catch {
            errorText = error.localizedDescription
        }
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
        .navigationBarBackButtonHidden(false)
        .toolbar(.visible, for: .navigationBar)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button { Task { await load() } } label: { Image(systemName: "arrow.clockwise") }
                    .disabled(loading)
                    .accessibilityLabel("Reload models")
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
