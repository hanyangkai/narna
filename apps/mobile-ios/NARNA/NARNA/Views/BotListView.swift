//
//  BotListView.swift
//  NARNA
//
//  Created by NARNA Team on 11/10/2026.
//

import SwiftUI

struct BotListView: View {
    @StateObject private var viewModel = BotListViewModel()
    @State private var showSettings = false
    @State private var selectedBot: BotInfo?
    
    var body: some View {
        NavigationView {
            ZStack {
                if viewModel.isLoading && viewModel.bots.isEmpty {
                    ProgressView("Loading bots...")
                } else if viewModel.bots.isEmpty {
                    EmptyBotsView()
                } else {
                    ScrollView {
                        VStack(spacing: 16) {
                            if !viewModel.pendingApprovals.isEmpty {
                                ApprovalsSection(approvals: viewModel.pendingApprovals)
                                    .padding(.horizontal)
                            }
                            
                            LazyVStack(spacing: 12) {
                                ForEach(viewModel.bots) { bot in
                                    BotCard(bot: bot)
                                        .onTapGesture {
                                            selectedBot = bot
                                        }
                                }
                            }
                            .padding(.horizontal)
                        }
                        .padding(.vertical)
                    }
                    .refreshable {
                        await viewModel.refresh()
                    }
                }
            }
            .navigationTitle("NARNA Bots")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showSettings = true }) {
                        Image(systemName: "gear")
                    }
                }
            }
            .sheet(isPresented: $showSettings) {
                SettingsView()
            }
            .sheet(item: $selectedBot) { bot in
                ChatView(bot: bot)
            }
            .alert("Error", isPresented: $viewModel.showError) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(viewModel.errorMessage ?? "Unknown error")
            }
            .onAppear {
                viewModel.loadBots()
                viewModel.startAutoRefresh()
            }
            .onDisappear {
                viewModel.stopAutoRefresh()
            }
        }
    }
}

struct BotCard: View {
    let bot: BotInfo
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(bot.name)
                        .font(.headline)
                    
                    Text(bot.model)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                
                Spacer()
                
                StatusBadge(status: bot.status, text: bot.statusText, color: bot.statusColor)
            }
            
            if let lastMessageAt = bot.lastMessageAt {
                Text("Last active: \(formatDate(lastMessageAt))")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
    }
    
    private func formatDate(_ isoString: String) -> String {
        let formatter = ISO8601DateFormatter()
        guard let date = formatter.date(from: isoString) else {
            return "Unknown"
        }
        
        let timeFormatter = RelativeDateTimeFormatter()
        timeFormatter.unitsStyle = .short
        return timeFormatter.localizedString(for: date, relativeTo: Date())
    }
}

struct StatusBadge: View {
    let status: String
    let text: String
    let color: String
    
    var body: some View {
        HStack(spacing: 4) {
            Circle()
                .fill(statusColor)
                .frame(width: 8, height: 8)
            
            Text(text)
                .font(.caption)
                .fontWeight(.medium)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(statusColor.opacity(0.2))
        .cornerRadius(12)
    }
    
    private var statusColor: Color {
        switch color {
        case "green": return .green
        case "blue": return .blue
        case "orange": return .orange
        default: return .gray
        }
    }
}

struct ApprovalsSection: View {
    let approvals: [ApprovalInfo]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(.orange)
                
                Text("Pending Approvals")
                    .font(.headline)
                
                Spacer()
                
                Text("\(approvals.count)")
                    .font(.caption)
                    .fontWeight(.bold)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.orange)
                    .foregroundColor(.white)
                    .cornerRadius(8)
            }
            
            Text("Your bots are waiting for approval to perform actions")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color.orange.opacity(0.1))
        .cornerRadius(12)
    }
}

struct EmptyBotsView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "laptopcomputer")
                .font(.system(size: 60))
                .foregroundColor(.secondary)
            
            Text("No Active Bots")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text("Start a bot on your desktop to see it here")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
    }
}

#Preview {
    BotListView()
}
