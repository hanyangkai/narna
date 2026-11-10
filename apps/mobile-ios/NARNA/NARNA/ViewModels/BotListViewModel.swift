//
//  BotListViewModel.swift
//  NARNA
//
//  Created by NARNA Team on 11/10/2026.
//

import Foundation
import Combine

@MainActor
class BotListViewModel: ObservableObject {
    @Published var bots: [BotInfo] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var showError = false
    @Published var pendingApprovals: [ApprovalInfo] = []
    
    private let apiService = NARNAAPIService.shared
    private var refreshTask: Task<Void, Never>?
    
    func loadBots() {
        isLoading = true
        errorMessage = nil
        
        Task {
            do {
                let fetchedBots = try await apiService.listBots()
                bots = fetchedBots
                isLoading = false
                
                await loadApprovals()
            } catch {
                isLoading = false
                showErrorMessage(error.localizedDescription)
            }
        }
    }
    
    func loadApprovals() async {
        do {
            let approvals = try await apiService.listApprovals()
            pendingApprovals = approvals
        } catch {
            print("⚠️ Failed to load approvals: \(error)")
        }
    }
    
    func refresh() async {
        do {
            let fetchedBots = try await apiService.listBots()
            bots = fetchedBots
            await loadApprovals()
        } catch {
            showErrorMessage(error.localizedDescription)
        }
    }
    
    func startAutoRefresh(interval: TimeInterval = 5.0) {
        stopAutoRefresh()
        
        refreshTask = Task {
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: UInt64(interval * 1_000_000_000))
                
                if !Task.isCancelled {
                    await refresh()
                }
            }
        }
    }
    
    func stopAutoRefresh() {
        refreshTask?.cancel()
        refreshTask = nil
    }
    
    func unpair() {
        KeychainService.shared.clearAll()
    }
    
    private func showErrorMessage(_ message: String) {
        errorMessage = message
        showError = true
    }
}
