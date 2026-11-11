//
//  MainTabView.swift
//  NARNA
//
//  Home is the bot list (like the Grok Bot app): NaNa Bot (Chief of Staff) on top,
//  user bots below. Tapping a bot pushes its chat. Settings, History and the
//  optional Desktop monitor are sheets, so there is no tab bar to cover the
//  chat input or block keyboard dismissal.
//

import SwiftUI

extension View {
    /// Kept for the screens that used to be tab roots. No bottom padding anymore
    /// (there is no floating tab bar).
    func narnaTabRoot() -> some View {
        self.background(Color(.systemBackground))
    }
}

/// Dismiss the keyboard from anywhere.
@MainActor func narnaEndEditing() {
    UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil)
}

struct MainTabView: View {
    @StateObject private var app = AppState.shared
    @StateObject private var settings = LLMSettings.shared
    @StateObject private var store = ConversationStore.shared
    @StateObject private var bots = ChatBotStore.shared

    var body: some View {
        NavigationStack(path: $app.path) {
            BotsHomeView()
                .navigationDestination(for: HomeRoute.self) { route in
                    switch route {
                    case .chat: AIChatView()
                    }
                }
        }
        .sheet(isPresented: $app.showSettings) {
            AppSettingsView()
                .environmentObject(app)
                .environmentObject(settings)
                .environmentObject(store)
                .environmentObject(bots)
                .presentationDragIndicator(.visible)
        }
        .sheet(isPresented: $app.showHistory) {
            HistoryView()
                .environmentObject(app)
                .environmentObject(settings)
                .environmentObject(store)
                .environmentObject(bots)
                .presentationDragIndicator(.visible)
        }
        .sheet(isPresented: $app.showDesktop) {
            BotListView()
                .presentationDragIndicator(.visible)
        }
        .environmentObject(app)
        .environmentObject(settings)
        .environmentObject(store)
        .environmentObject(bots)
        .onAppear {
            app.refreshPairing()
            #if DEBUG
            let args = ProcessInfo.processInfo.arguments
            if args.contains("-NARNA_DEMO_BOTS") || args.contains("-NARNA_OPEN_BOTS") {
                bots.seedDemoBots()
            }
            if args.contains("-NARNA_OPEN_USER_BOT") {
                bots.seedDemoBots()
                app.openBot(ChatBotStore.demoResearchID,
                            conversation: store.sorted(for: ChatBotStore.demoResearchID).first?.id)
            } else if args.contains("-NARNA_OPEN_CHAT") || args.contains("-NARNA_DEMO_AUTOSEND") {
                app.openBot(ChatBot.chiefOfStaffID,
                            conversation: store.sorted(for: ChatBot.chiefOfStaffID).first?.id)
            }
            if let i = args.firstIndex(of: "-NARNA_TAB"), i + 1 < args.count {
                switch args[i + 1] {
                case "history":
                    app.openBot(app.currentBotID, conversation: app.currentConversationID)
                    app.showHistory = true
                case "settings": app.showSettings = true
                case "chat": app.openBot(app.currentBotID, conversation: app.currentConversationID)
                default: break
                }
            }
            #endif
        }
    }
}
