//
//  MainTabView.swift
//  NARNA
//
//  App launches straight into Chat. Desktop pairing is optional (Settings).
//

import SwiftUI

extension View {
    /// Extra scroll room so the last Form/List rows clear the custom tab bar.
    /// Apply to the NavigationStack (not the Form inside it). Pads the whole
    /// stack so Form/List cannot paint under the overlaid tab bar.
    func narnaTabRoot() -> some View {
        self
            .padding(.bottom, 100)
            .background(Color(.systemBackground))
    }

    /// Keep a tab mounted (so typed Settings / chat state survive) but untouchable when hidden.
    func narnaTabVisible(_ visible: Bool) -> some View {
        self
            .opacity(visible ? 1 : 0)
            .allowsHitTesting(visible)
            .accessibilityHidden(!visible)
            .zIndex(visible ? 1 : 0)
    }
}

/// A floating tab bar placed in a safeAreaInset so it never covers content
/// and never eats (or loses) taps the way the iOS 26 system tab bar did.
struct NarnaTabBar: View {
    @Binding var selection: MainTab
    var showDesktop: Bool

    var body: some View {
        HStack(spacing: 0) {
            tab(.chat, "Chat", "bubble.left.and.bubble.right.fill")
            tab(.history, "History", "clock.arrow.circlepath")
            if showDesktop {
                tab(.desktop, "Desktop", "desktopcomputer")
            }
            tab(.settings, "Settings", "gearshape.fill")
        }
        .padding(.vertical, 10)
        .padding(.horizontal, 10)
        .background(.ultraThinMaterial, in: Capsule())
        .overlay(Capsule().strokeBorder(Color.primary.opacity(0.12)))
        .shadow(color: .black.opacity(0.28), radius: 18, y: 6)
        .padding(.horizontal, 28)
        .padding(.top, 6)
        .padding(.bottom, 10)
        .accessibilityElement(children: .contain)
        .accessibilityLabel("Main tabs")
    }

    private func tab(_ id: MainTab, _ title: String, _ image: String) -> some View {
        Button {
            selection = id
        } label: {
            VStack(spacing: 2) {
                Image(systemName: image)
                    .font(.system(size: 20, weight: selection == id ? .semibold : .regular))
                Text(title)
                    .font(.caption2.weight(selection == id ? .semibold : .regular))
            }
            .frame(maxWidth: .infinity)
            .foregroundStyle(selection == id ? Color.accentColor : Color.secondary)
            .padding(.vertical, 4)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityLabel(title)
        .accessibilityAddTraits(selection == id ? [.isButton, .isSelected] : .isButton)
    }
}

struct MainTabView: View {
    @StateObject private var app = AppState.shared
    @StateObject private var settings = LLMSettings.shared
    @StateObject private var store = ConversationStore.shared

    var body: some View {
        // Don't use TabView: the iOS 26 system tab bar floats over Form content
        // and can steal or drop taps, so the user had to kill the app to leave Settings.
        ZStack {
            AIChatView().narnaTabVisible(app.selectedTab == .chat)
            HistoryView().narnaTabVisible(app.selectedTab == .history)
            if app.isPaired {
                BotListView().narnaTabVisible(app.selectedTab == .desktop)
            }
            AppSettingsView().narnaTabVisible(app.selectedTab == .settings)
        }
        .overlay(alignment: .bottom) {
            NarnaTabBar(selection: $app.selectedTab, showDesktop: app.isPaired)
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
