//
//  SettingsView.swift
//  NARNA
//
//  Created by NARNA Team on 11/10/2026.
//

import SwiftUI
import UIKit

struct SettingsView: View {
    @Binding var isPaired: Bool
    @EnvironmentObject var apiService: NARNAAPIService
    
    @AppStorage("api_base_url") private var apiBaseURL = "http://localhost:8765"
    @AppStorage("openai_voice_api_key") private var voiceAPIKey = ""
    @AppStorage("push_notifications_enabled") private var pushEnabled = false
    
    @State private var showUnpairAlert = false
    @State private var remoteMode = "local"
    @State private var remoteHost = ""
    @State private var customBaseURL = ""
    @State private var connectedApps: [ConnectedApp] = []
    @State private var isLoadingApps = false
    @State private var mutatingApp: String?
    @State private var isSavingRemote = false
    @State private var statusMessage: String?
    @State private var showStatus = false
    @State private var errorMessage: String?
    @State private var showError = false
    
    var body: some View {
        NavigationView {
            Form {
                connectionSection
                subscriptionSection
                remoteAccessSection
                connectedAppsSection
                notificationsSection
                voiceSection
                deviceSection
                aboutSection
                unpairSection
            }
            .navigationTitle("Settings")
            .alert("Unpair Device", isPresented: $showUnpairAlert) {
                Button("Cancel", role: .cancel) {}
                Button("Unpair", role: .destructive) {
                    unpairDevice()
                }
            } message: {
                Text("Are you sure you want to unpair this device? You'll need to pair again to use NARNA.")
            }
            .alert("Updated", isPresented: $showStatus) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(statusMessage ?? "Saved")
            }
            .alert("Error", isPresented: $showError) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(errorMessage ?? "Unknown error")
            }
            .onAppear {
                apiBaseURL = apiService.baseURL
                loadRemoteStatus()
                loadConnectedApps()
            }
        }
        .navigationViewStyle(.stack)
    }
    
    // MARK: - Sections

    private var subscriptionSection: some View {
        Section {
            LabeledContent("Pro", value: "$19.99/mo · $159.99/yr")
            LabeledContent("Team", value: "$99.99/seat/mo")
            Text("Subscriptions are billed only through the App Store. Crypto and web USDC/USDT checkout are not available in this app.")
                .font(.footnote)
                .foregroundStyle(.secondary)
            Button("Manage in App Store") {
                if let url = URL(string: "https://apps.apple.com/account/subscriptions") {
                    UIApplication.shared.open(url)
                }
            }
        } header: {
            Text("Subscription")
        }
    }
    
    private var connectionSection: some View {
        Section("Connection") {
            if let name = KeychainService.shared.getAgentName() {
                LabeledContent("Agent", value: name)
            }
            
            HStack {
                Text("Base URL")
                Spacer()
                TextField("http://localhost:8765", text: $apiBaseURL)
                    .multilineTextAlignment(.trailing)
                    .autocapitalization(.none)
                    .keyboardType(.URL)
                    .disableAutocorrection(true)
            }
            
            Button("Save URL") {
                saveBaseURL(apiBaseURL)
            }
            .disabled(apiBaseURL.isEmpty)
        }
    }
    
    private var remoteAccessSection: some View {
        Section {
            Picker("Mode", selection: $remoteMode) {
                Text("Local").tag("local")
                Text("Tailscale").tag("tailscale")
                Text("Custom HTTPS").tag("custom")
            }
            .pickerStyle(.segmented)
            
            if remoteMode == "tailscale" {
                TextField("Tailscale host (MagicDNS)", text: $remoteHost)
                    .autocapitalization(.none)
                    .disableAutocorrection(true)
                    .keyboardType(.URL)
            }
            
            if remoteMode == "custom" {
                TextField("https://your-host.example", text: $customBaseURL)
                    .autocapitalization(.none)
                    .disableAutocorrection(true)
                    .keyboardType(.URL)
            }
            
            Button {
                saveRemoteConfig()
            } label: {
                if isSavingRemote {
                    ProgressView()
                } else {
                    Text("Save remote access")
                }
            }
            .disabled(isSavingRemote)
        } header: {
            Text("Remote Access")
        } footer: {
            Text("Use Local on the same network, Tailscale MagicDNS for mesh access, or a custom HTTPS tunnel.")
        }
    }
    
    private var connectedAppsSection: some View {
        Section("Connected Apps") {
            if isLoadingApps && connectedApps.isEmpty {
                ProgressView()
            } else {
                ForEach(connectedApps) { app in
                    HStack(spacing: 12) {
                        Image(systemName: app.systemIcon)
                            .foregroundColor(.accentColor)
                            .frame(width: 24)
                        
                        VStack(alignment: .leading, spacing: 2) {
                            Text(app.displayName)
                            Text(app.connected ? (app.accountLabel ?? "Connected") : "Disconnected")
                                .font(.caption)
                                .foregroundColor(app.connected ? .green : .secondary)
                        }
                        
                        Spacer()
                        
                        Button {
                            toggleApp(app)
                        } label: {
                            if mutatingApp == app.app {
                                ProgressView()
                            } else {
                                Text(app.connected ? "Disconnect" : "Connect")
                                    .font(.subheadline.weight(.semibold))
                            }
                        }
                        .buttonStyle(.bordered)
                        .disabled(mutatingApp != nil)
                    }
                }
            }
        }
    }
    
    private var notificationsSection: some View {
        Section {
            Toggle("Push Notifications", isOn: $pushEnabled)
                .onChange(of: pushEnabled) { enabled in
                    if enabled {
                        registerPushStub()
                    }
                }
        } header: {
            Text("Notifications")
        } footer: {
            Text("Registers a device token stub with the backend so approval pushes can be wired to APNs.")
        }
    }
    
    private var voiceSection: some View {
        Section {
            SecureField("OpenAI API key", text: $voiceAPIKey)
                .autocapitalization(.none)
                .disableAutocorrection(true)
                .textContentType(.password)
        } header: {
            Text("Voice")
        } footer: {
            Text("Stored on-device for live voice calls. Never logged or printed.")
        }
    }
    
    private var deviceSection: some View {
        Section("Device") {
            LabeledContent("Device", value: UIDevice.current.name)
            LabeledContent("Platform", value: "iOS \(UIDevice.current.systemVersion)")
        }
    }
    
    private var aboutSection: some View {
        Section("About") {
            LabeledContent("Version", value: "1.0.0")
            LabeledContent("Build", value: "1")
            Link("Documentation", destination: URL(string: "https://github.com/narna/narna")!)
        }
    }
    
    private var unpairSection: some View {
        Section {
            Button(role: .destructive) {
                showUnpairAlert = true
            } label: {
                HStack {
                    Image(systemName: "link.badge.minus")
                    Text("Unpair Device")
                }
            }
        }
    }
    
    // MARK: - Actions
    
    private func saveBaseURL(_ url: String) {
        let trimmed = url.trimmingCharacters(in: .whitespacesAndNewlines)
        apiBaseURL = trimmed
        apiService.baseURL = trimmed
        UserDefaults.standard.set(trimmed, forKey: "api_base_url")
        statusMessage = "Base URL saved"
        showStatus = true
    }
    
    private func loadRemoteStatus() {
        Task {
            do {
                let remote = try await apiService.getRemoteStatus()
                remoteMode = remote.mode
                remoteHost = remote.host ?? ""
                if remote.mode == "custom" {
                    customBaseURL = remote.baseUrl ?? ""
                }
            } catch {
                // Keep local defaults when status is unavailable
            }
        }
    }
    
    private func saveRemoteConfig() {
        isSavingRemote = true
        Task {
            do {
                let host = remoteMode == "tailscale" ? remoteHost : nil
                let base = remoteMode == "custom" ? customBaseURL : nil
                let remote = try await apiService.updateRemoteConfig(
                    mode: remoteMode,
                    host: host,
                    baseUrl: base
                )
                if let url = remote.baseUrl, !url.isEmpty {
                    saveBaseURL(url)
                }
                isSavingRemote = false
                statusMessage = "Remote access updated (\(remote.mode))"
                showStatus = true
            } catch {
                isSavingRemote = false
                errorMessage = error.localizedDescription
                showError = true
            }
        }
    }
    
    private func loadConnectedApps() {
        isLoadingApps = true
        Task {
            do {
                connectedApps = try await apiService.listConnectedApps()
                isLoadingApps = false
            } catch {
                isLoadingApps = false
            }
        }
    }
    
    private func toggleApp(_ app: ConnectedApp) {
        mutatingApp = app.app
        Task {
            do {
                if app.connected {
                    _ = try await apiService.disconnectApp(app.app)
                } else {
                    _ = try await apiService.connectApp(app.app)
                }
                connectedApps = try await apiService.listConnectedApps()
                mutatingApp = nil
            } catch {
                mutatingApp = nil
                errorMessage = error.localizedDescription
                showError = true
            }
        }
    }
    
    private func registerPushStub() {
        let stubToken = "ios-stub-\(UIDevice.current.identifierForVendor?.uuidString ?? UUID().uuidString)"
        Task {
            do {
                let response = try await apiService.registerPushDevice(
                    deviceToken: stubToken,
                    deviceName: UIDevice.current.name
                )
                statusMessage = response.note ?? "Device registered for push"
                showStatus = true
            } catch {
                pushEnabled = false
                errorMessage = error.localizedDescription
                showError = true
            }
        }
    }
    
    private func unpairDevice() {
        KeychainService.shared.clearAll()
        apiService.inboxPendingCount = 0
        isPaired = false
    }
}

#Preview {
    SettingsView(isPaired: .constant(true))
        .environmentObject(NARNAAPIService.shared)
}
