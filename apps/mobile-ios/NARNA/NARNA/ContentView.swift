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
    @State private var showOnboarding = true
    @State private var onboardingStatus: OnboardingStatusResponse?
    @State private var showAISetupSheet = false
    @State private var dismissAIBanner = false
    
    private var needsAISetup: Bool {
        guard isPaired, let status = onboardingStatus else { return false }
        return status.needsOnboarding || !status.aiReady
    }
    
    var body: some View {
        Group {
            if isPaired {
                pairedShell
            } else if showOnboarding {
                OnboardingView(
                    isPaired: $isPaired,
                    onSkipToPairing: {
                        showOnboarding = false
                    }
                )
            } else {
                PairingView(isPaired: $isPaired, onBack: {
                    showOnboarding = true
                })
            }
        }
        .onAppear {
            checkPairingStatus()
            refreshOnboardingStatus()
        }
        .onChange(of: isPaired) { paired in
            if paired {
                showOnboarding = false
                dismissAIBanner = false
                refreshInboxBadge()
                refreshOnboardingStatus()
            } else {
                apiService.inboxPendingCount = 0
                selectedTab = 0
                showOnboarding = true
                onboardingStatus = nil
                dismissAIBanner = false
            }
        }
    }
    
    private var pairedShell: some View {
        TabView(selection: $selectedTab) {
            VStack(spacing: 0) {
                if needsAISetup && !dismissAIBanner {
                    aiSetupBanner
                }
                BotListView()
            }
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
            refreshOnboardingStatus()
        }
        .sheet(isPresented: $showAISetupSheet, onDismiss: {
            refreshOnboardingStatus()
        }) {
            OnboardingView(
                isPaired: $isPaired,
                onSkipToPairing: {
                    showAISetupSheet = false
                },
                embedded: true
            )
            .environmentObject(apiService)
        }
    }
    
    private var aiSetupBanner: some View {
        HStack(alignment: .center, spacing: 12) {
            Image(systemName: "sparkles")
                .foregroundStyle(.orange)
            
            VStack(alignment: .leading, spacing: 2) {
                Text("Kết nối AI để bắt đầu")
                    .font(.subheadline.weight(.semibold))
                Text("Pair Desktop (Claude/ChatGPT) hoặc mua Pro + gắn API key")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            
            Spacer(minLength: 0)
            
            Button("Setup") {
                showAISetupSheet = true
            }
            .font(.caption.weight(.bold))
            .buttonStyle(.borderedProminent)
            .controlSize(.small)
            
            Button {
                dismissAIBanner = true
            } label: {
                Image(systemName: "xmark")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.secondary)
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Dismiss")
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
        .background(Color.orange.opacity(0.12))
    }
    
    private func checkPairingStatus() {
        isPaired = KeychainService.shared.getMobileToken() != nil
        if isPaired {
            showOnboarding = false
        }
    }
    
    private func refreshInboxBadge() {
        Task {
            _ = try? await apiService.getInbox()
        }
    }
    
    private func refreshOnboardingStatus() {
        guard KeychainService.shared.getMobileToken() != nil else {
            onboardingStatus = nil
            return
        }
        Task {
            if let status = try? await apiService.getOnboardingStatus() {
                onboardingStatus = status
                if status.aiReady {
                    dismissAIBanner = false
                }
            }
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(NARNAAPIService.shared)
}
