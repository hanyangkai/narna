//
//  MainTabView.swift
//  NARNA
//
//  App launches straight into Chat. Desktop pairing is optional (Settings).
//

import SwiftUI

struct MainTabView: View {
    @StateObject private var app = AppState.shared
    @StateObject private var settings = LLMSettings.shared
    @StateObject private var store = ConversationStore.shared

    var body: some View {
        TabView(selection: $app.selectedTab) {
            AIChatView()
                .tabItem { Label("Chat", systemImage: "bubble.left.and.bubble.right.fill") }
                .tag(MainTab.chat)

            HistoryView()
                .tabItem { Label("History", systemImage: "clock.arrow.circlepath") }
                .tag(MainTab.history)

            if app.isPaired {
                BotListView()
                    .tabItem { Label("Desktop", systemImage: "desktopcomputer") }
                    .tag(MainTab.desktop)
            }

            AppSettingsView()
                .tabItem { Label("Settings", systemImage: "gearshape.fill") }
                .tag(MainTab.settings)
        }
        .environmentObject(app)
        .environmentObject(settings)
        .environmentObject(store)
        .onAppear {
            app.refreshPairing()
            #if DEBUG
            let args = ProcessInfo.processInfo.arguments
            if let i = args.firstIndex(of: "-NARNA_TAB"), i + 1 < args.count {
                switch args[i + 1] {
                case "history": app.selectedTab = .history
                case "settings": app.selectedTab = .settings
                default: app.selectedTab = .chat
                }
            }
            #endif
        }
    }
}
