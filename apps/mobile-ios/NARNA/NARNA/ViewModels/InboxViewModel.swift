//
//  InboxViewModel.swift
//  NARNA
//

import Foundation

@MainActor
class InboxViewModel: ObservableObject {
    @Published var items: [InboxItem] = []
    @Published var pendingCount: Int = 0
    @Published var isLoading = false
    @Published var processingIds: Set<String> = []
    @Published var errorMessage: String?
    @Published var showError = false
    
    private let apiService = NARNAAPIService.shared
    
    func load() {
        isLoading = items.isEmpty
        Task {
            await refresh()
        }
    }
    
    func refresh() async {
        do {
            let response = try await apiService.getInbox()
            items = response.items
            pendingCount = response.pendingCount
            isLoading = false
        } catch {
            isLoading = false
            errorMessage = error.localizedDescription
            showError = true
        }
    }
    
    func allow(_ item: InboxItem) {
        guard item.isApproval else { return }
        processingIds.insert(item.id)
        Task {
            do {
                _ = try await apiService.allowApproval(approvalId: item.itemId)
                processingIds.remove(item.id)
                await refresh()
            } catch {
                processingIds.remove(item.id)
                errorMessage = error.localizedDescription
                showError = true
            }
        }
    }
    
    func deny(_ item: InboxItem) {
        guard item.isApproval else { return }
        processingIds.insert(item.id)
        Task {
            do {
                _ = try await apiService.denyApproval(approvalId: item.itemId)
                processingIds.remove(item.id)
                await refresh()
            } catch {
                processingIds.remove(item.id)
                errorMessage = error.localizedDescription
                showError = true
            }
        }
    }
}
