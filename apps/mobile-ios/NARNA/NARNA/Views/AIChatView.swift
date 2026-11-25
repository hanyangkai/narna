//
//  AIChatView.swift
//  NARNA
//

import SwiftUI

struct AIChatView: View {
    @StateObject private var viewModel = AIChatViewModel()
    @State private var showSettings = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if viewModel.enginePreference == .auto,
                   viewModel.appleAvailability != .available,
                   viewModel.appleAvailability != .unsupportedOS {
                    availabilityBanner
                }

                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(alignment: .leading, spacing: 14) {
                            ForEach(viewModel.turns) { turn in
                                chatBubble(turn)
                                    .id(turn.id)
                            }
                            if viewModel.isStreaming {
                                HStack {
                                    ProgressView()
                                    Text(String(localized: "nana_thinking"))
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                    Spacer()
                                }
                                .padding(.horizontal)
                            }
                        }
                        .padding()
                    }
                    .onChange(of: viewModel.turns.count) { _, _ in
                        if let last = viewModel.turns.last {
                            withAnimation { proxy.scrollTo(last.id, anchor: .bottom) }
                        }
                    }
                }

                Divider()
                inputBar
            }
            .navigationTitle(PinnedBot.name)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        showSettings = true
                    } label: {
                        Image(systemName: "gearshape")
                    }
                    .accessibilityLabel(String(localized: "settings_title"))
                }
            }
            .sheet(isPresented: $showSettings) {
                AppSettingsView(chatViewModel: viewModel)
            }
            .alert(String(localized: "error_title"), isPresented: $viewModel.showError) {
                Button(String(localized: "ok"), role: .cancel) {}
            } message: {
                Text(viewModel.errorMessage ?? "")
            }
            .onAppear { viewModel.refreshAvailability() }
        }
    }

    private var availabilityBanner: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(viewModel.appleAvailability.friendlyMessage)
                .font(.footnote)
            if viewModel.appleAvailability.suggestsOpenSettings {
                Button(String(localized: "open_settings")) {
                    viewModel.openAppleIntelligenceSettings()
                }
                .font(.footnote.weight(.semibold))
            }
            Text(String(localized: "falling_back_free_cloud"))
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(Color.orange.opacity(0.12))
    }

    private func chatBubble(_ turn: ChatTurn) -> some View {
        let isUser = turn.role == "user"
        return HStack {
            if isUser { Spacer(minLength: 40) }
            VStack(alignment: isUser ? .trailing : .leading, spacing: 4) {
                Text(turn.content)
                    .padding(12)
                    .background(isUser ? Color.accentColor.opacity(0.25) : Color.secondary.opacity(0.12))
                    .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                if !isUser, let label = turn.engineLabel, !label.isEmpty {
                    Text(label)
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                }
            }
            if !isUser { Spacer(minLength: 40) }
        }
    }

    private var inputBar: some View {
        HStack(spacing: 10) {
            TextField(String(localized: "chat_placeholder"), text: $viewModel.inputText, axis: .vertical)
                .lineLimit(1...5)
                .textFieldStyle(.roundedBorder)
            Button {
                viewModel.sendMessage()
            } label: {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.system(size: 28))
            }
            .disabled(viewModel.isStreaming || viewModel.inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
        }
        .padding(.horizontal)
        .padding(.vertical, 10)
    }
}
