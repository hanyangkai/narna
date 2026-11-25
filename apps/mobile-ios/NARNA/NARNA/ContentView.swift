//
//  ContentView.swift
//  NARNA
//
//  v1.1: first launch goes straight to Nana AI chat (no API key required).
//  Desktop pairing / bot remote remains available from Settings.
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var apiService: NARNAAPIService
    @State private var selectedTab = 0
    @State private var isPaired = false

    var body: some View {
        TabView(selection: $selectedTab) {
            AIChatView()
                .tabItem {
                    Label(PinnedBot.name, systemImage: "bubble.left.and.bubble.right.fill")
                }
                .tag(0)

            if isPaired {
                pairedTabs
            } else {
                NavigationStack {
                    VStack(spacing: 16) {
                        Text(String(localized: "desktop_optional_title"))
                            .font(.title2.weight(.semibold))
                        Text(String(localized: "desktop_optional_body"))
                            .font(.body)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal)
                        PairingView(isPaired: $isPaired, onBack: nil)
                    }
                }
                .tabItem {
                    Label(String(localized: "pair_tab"), systemImage: "qrcode.viewfinder")
                }
                .tag(1)
            }
        }
        .onAppear {
            isPaired = KeychainService.shared.getMobileToken() != nil
        }
        .onChange(of: isPaired) { paired in
            if paired {
                selectedTab = 0
            }
        }
    }

    @ViewBuilder
    private var pairedTabs: some View {
        BotListView()
            .tabItem { Label("Bots", systemImage: "laptopcomputer") }
            .tag(1)

        InboxView()
            .tabItem { Label("Inbox", systemImage: "tray.fill") }
            .badge(apiService.inboxPendingCount)
            .tag(2)

        SettingsView(isPaired: $isPaired)
            .tabItem { Label("Agent", systemImage: "link") }
            .tag(3)
    }
}

#Preview {
    ContentView()
        .environmentObject(NARNAAPIService.shared)
}
