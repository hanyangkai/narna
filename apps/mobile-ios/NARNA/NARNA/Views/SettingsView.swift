//
//  SettingsView.swift
//  NARNA
//
//  Created by NARNA Team on 11/10/2026.
//

import SwiftUI

struct SettingsView: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var apiService: NARNAAPIService
    @AppStorage("api_base_url") private var apiBaseURL = "http://localhost:8765"
    @State private var showUnpairAlert = false
    @State private var agentName: String = ""
    
    var body: some View {
        NavigationView {
            Form {
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
                    }
                    
                    Button("Save URL") {
                        apiService.baseURL = apiBaseURL
                    }
                    .disabled(apiBaseURL.isEmpty)
                }
                
                Section("Device") {
                    LabeledContent("Device", value: UIDevice.current.name)
                    LabeledContent("Platform", value: "iOS \(UIDevice.current.systemVersion)")
                }
                
                Section("About") {
                    LabeledContent("Version", value: Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0")
                    LabeledContent("Build", value: Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "1")
                    
                    Link("Documentation", destination: URL(string: "https://github.com/narna/narna")!)
                }
                
                Section {
                    Button(role: .destructive, action: {
                        showUnpairAlert = true
                    }) {
                        HStack {
                            Image(systemName: "link.badge.minus")
                            Text("Unpair Device")
                        }
                    }
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
            .alert("Unpair Device", isPresented: $showUnpairAlert) {
                Button("Cancel", role: .cancel) {}
                Button("Unpair", role: .destructive) {
                    unpairDevice()
                }
            } message: {
                Text("Are you sure you want to unpair this device? Chat keeps working; pair again any time to see desktop bots.")
            }
            .onAppear {
                agentName = KeychainService.shared.getAgentName() ?? "Unknown"
                apiBaseURL = apiService.baseURL
            }
        }
    }
    
    private func unpairDevice() {
        AppState.shared.unpair()
        dismiss()
    }
}

#Preview {
    SettingsView()
        .environmentObject(NARNAAPIService.shared)
}
