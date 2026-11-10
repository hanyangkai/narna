//
//  InboxView.swift
//  NARNA
//

import SwiftUI

struct InboxView: View {
    @StateObject private var viewModel = InboxViewModel()
    @EnvironmentObject var apiService: NARNAAPIService
    
    var body: some View {
        NavigationView {
            ZStack {
                Color(.systemGroupedBackground).ignoresSafeArea()
                
                if viewModel.isLoading {
                    ProgressView("Loading inbox…")
                } else if actionableItems.isEmpty && infoOnly {
                    EmptyInboxView()
                } else {
                    ScrollView {
                        LazyVStack(spacing: 12) {
                            ForEach(viewModel.items) { item in
                                InboxCard(
                                    item: item,
                                    isProcessing: viewModel.processingIds.contains(item.id),
                                    onAllow: { viewModel.allow(item) },
                                    onDeny: { viewModel.deny(item) }
                                )
                            }
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 12)
                    }
                    .refreshable {
                        await viewModel.refresh()
                    }
                }
            }
            .navigationTitle("Inbox")
            .alert("Error", isPresented: $viewModel.showError) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(viewModel.errorMessage ?? "Unknown error")
            }
            .onAppear {
                viewModel.load()
            }
            .onChange(of: viewModel.pendingCount) { newValue in
                apiService.inboxPendingCount = newValue
            }
        }
        .navigationViewStyle(.stack)
    }
    
    private var actionableItems: [InboxItem] {
        viewModel.items.filter { $0.status == "pending" }
    }
    
    private var infoOnly: Bool {
        viewModel.items.allSatisfy { $0.status == "info" || !$0.isApproval }
            && viewModel.items.contains(where: { $0.itemId == "inbox_demo_empty" })
    }
}

struct InboxCard: View {
    let item: InboxItem
    let isProcessing: Bool
    let onAllow: () -> Void
    let onDeny: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(alignment: .top, spacing: 12) {
                Image(systemName: item.kindIcon)
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(chipColor)
                    .frame(width: 36, height: 36)
                    .background(chipColor.opacity(0.15))
                    .cornerRadius(10)
                
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(item.title)
                            .font(.headline)
                            .lineLimit(2)
                        Spacer(minLength: 8)
                        StatusChip(text: item.status.capitalized, colorName: item.kindChipColor)
                    }
                    
                    Text(item.botId)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
            
            Text(item.body)
                .font(.subheadline)
                .foregroundColor(.primary)
                .fixedSize(horizontal: false, vertical: true)
            
            if item.isApproval && item.status == "pending" {
                HStack(spacing: 10) {
                    Button(action: onAllow) {
                        Label("Allow", systemImage: "checkmark.circle.fill")
                            .font(.subheadline.weight(.semibold))
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 10)
                    }
                    .buttonStyle(.plain)
                    .foregroundColor(.white)
                    .background(Color.green)
                    .cornerRadius(10)
                    .disabled(isProcessing)
                    
                    Button(action: onDeny) {
                        Label("Deny", systemImage: "xmark.circle.fill")
                            .font(.subheadline.weight(.semibold))
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 10)
                    }
                    .buttonStyle(.plain)
                    .foregroundColor(.white)
                    .background(Color.red)
                    .cornerRadius(10)
                    .disabled(isProcessing)
                }
                .opacity(isProcessing ? 0.6 : 1)
            }
        }
        .padding(16)
        .background(Color(.secondarySystemGroupedBackground))
        .cornerRadius(16)
        .shadow(color: Color.black.opacity(0.04), radius: 8, y: 2)
    }
    
    private var chipColor: Color {
        switch item.kindChipColor {
        case "orange": return .orange
        case "blue": return .blue
        case "green": return .green
        default: return .gray
        }
    }
}

struct StatusChip: View {
    let text: String
    let colorName: String
    
    var body: some View {
        Text(text)
            .font(.caption2.weight(.semibold))
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .foregroundColor(color)
            .background(color.opacity(0.15))
            .cornerRadius(8)
    }
    
    private var color: Color {
        switch colorName {
        case "orange": return .orange
        case "blue": return .blue
        case "green": return .green
        case "red": return .red
        default: return .gray
        }
    }
}

struct EmptyInboxView: View {
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "tray")
                .font(.system(size: 52, weight: .light))
                .foregroundColor(.secondary)
            
            Text("Inbox is clear")
                .font(.title3.weight(.semibold))
            
            Text("Approvals and bot questions from every bot show up here.")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
        }
    }
}

#Preview {
    InboxView()
        .environmentObject(NARNAAPIService.shared)
}
