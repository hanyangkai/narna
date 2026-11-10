//
//  VoiceCallView.swift
//  NARNA
//

import SwiftUI

struct VoiceCallView: View {
    @StateObject private var viewModel = VoiceCallViewModel()
    
    var body: some View {
        NavigationView {
            ZStack {
                LinearGradient(
                    colors: [
                        Color(.systemBackground),
                        viewModel.isLive ? Color.blue.opacity(0.18) : Color(.systemGroupedBackground)
                    ],
                    startPoint: .top,
                    endPoint: .bottom
                )
                .ignoresSafeArea()
                
                VStack(spacing: 28) {
                    VStack(spacing: 8) {
                        Text(viewModel.isLive ? "Live call" : "Voice")
                            .font(.largeTitle.weight(.bold))
                        
                        Text(viewModel.statusNote)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 28)
                    }
                    .padding(.top, 24)
                    
                    if !viewModel.bots.isEmpty {
                        Picker("Bot", selection: $viewModel.selectedBotId) {
                            ForEach(viewModel.bots) { bot in
                                Text(bot.name).tag(bot.botId)
                            }
                        }
                        .pickerStyle(.menu)
                        .disabled(viewModel.isLive)
                        .padding(.horizontal)
                    }
                    
                    TranscriptCard(lines: viewModel.transcriptLines, isLive: viewModel.isLive)
                        .padding(.horizontal, 16)
                    
                    Spacer()
                    
                    Button {
                        viewModel.toggleCall()
                    } label: {
                        ZStack {
                            Circle()
                                .fill(viewModel.isLive ? Color.red : Color.accentColor)
                                .frame(width: 84, height: 84)
                                .shadow(color: (viewModel.isLive ? Color.red : Color.accentColor).opacity(0.35), radius: 16, y: 6)
                            
                            if viewModel.isBusy {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            } else {
                                Image(systemName: viewModel.isLive ? "stop.fill" : "mic.fill")
                                    .font(.system(size: 32, weight: .semibold))
                                    .foregroundColor(.white)
                            }
                        }
                    }
                    .disabled(viewModel.isBusy)
                    .accessibilityLabel(viewModel.isLive ? "End call" : "Start call")
                    
                    Text(viewModel.isLive ? "Tap to hang up" : "Tap to talk")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.bottom, 36)
                }
            }
            .navigationBarHidden(true)
            .alert("Error", isPresented: $viewModel.showError) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(viewModel.errorMessage ?? "Unknown error")
            }
            .onAppear {
                viewModel.loadBots()
            }
        }
        .navigationViewStyle(.stack)
    }
}

struct TranscriptCard: View {
    let lines: [String]
    let isLive: Bool
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Transcript")
                    .font(.headline)
                Spacer()
                StatusChip(text: isLive ? "Live" : "Idle", colorName: isLive ? "green" : "gray")
            }
            
            if lines.isEmpty {
                Text("Conversation text will appear here once the call starts.")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.vertical, 24)
            } else {
                ScrollView {
                    VStack(alignment: .leading, spacing: 10) {
                        ForEach(Array(lines.enumerated()), id: \.offset) { _, line in
                            Text(line)
                                .font(.subheadline)
                                .foregroundColor(.primary)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                }
                .frame(maxHeight: 220)
            }
        }
        .padding(16)
        .background(Color(.secondarySystemGroupedBackground))
        .cornerRadius(16)
        .shadow(color: Color.black.opacity(0.04), radius: 8, y: 2)
    }
}

#Preview {
    VoiceCallView()
}
