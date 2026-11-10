//
//  ContentView.swift
//  NARNA
//
//  Created by NARNA Team on 11/10/2026.
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var apiService: NARNAAPIService
    @State private var isPaired = false
    @State private var selectedTab = 0
    
    var body: some View {
        Group {
            if isPaired {
                TabView(selection: $selectedTab) {
                    BotListView()
                        .tabItem {
                            Label("Bots", systemImage: "laptopcomputer")
                        }
                        .tag(0)
                    
                    InboxView()
                        .tabItem {
                            Label("Inbox", systemImage: "tray.fill")
                        }
                        .badge(apiService.inboxPendingCount)
                        .tag(1)
                    
                    RoutinesView()
                        .tabItem {
                            Label("Routines", systemImage: "clock.arrow.2.circlepath")
                        }
                        .tag(2)
                    
                    VoiceCallView()
                        .tabItem {
                            Label("Voice", systemImage: "mic.fill")
                        }
                        .tag(3)
                    
                    SettingsView(isPaired: $isPaired)
                        .tabItem {
                            Label("Settings", systemImage: "gearshape.fill")
                        }
                        .tag(4)
                }
                .onAppear {
                    refreshInboxBadge()
                }
            } else {
                PairingView(isPaired: $isPaired)
            }
        }
        .onAppear {
            checkPairingStatus()
        }
        .onChange(of: isPaired) { paired in
            if paired {
                refreshInboxBadge()
            } else {
                apiService.inboxPendingCount = 0
                selectedTab = 0
            }
        }
    }
    
    private func checkPairingStatus() {
        isPaired = KeychainService.shared.getMobileToken() != nil
    }
    
    private func refreshInboxBadge() {
        Task {
            _ = try? await apiService.getInbox()
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(NARNAAPIService.shared)
}
