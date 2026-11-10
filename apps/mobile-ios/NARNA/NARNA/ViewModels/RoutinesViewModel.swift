//
//  RoutinesViewModel.swift
//  NARNA
//

import Foundation

@MainActor
class RoutinesViewModel: ObservableObject {
    @Published var routines: [RoutineInfo] = []
    @Published var isLoading = false
    @Published var isSaving = false
    @Published var errorMessage: String?
    @Published var showError = false
    
    private let apiService = NARNAAPIService.shared
    
    func load() {
        isLoading = routines.isEmpty
        Task {
            await refresh()
        }
    }
    
    func refresh() async {
        do {
            routines = try await apiService.listRoutines()
            isLoading = false
        } catch {
            isLoading = false
            errorMessage = error.localizedDescription
            showError = true
        }
    }
    
    func toggle(_ routine: RoutineInfo) {
        Task {
            do {
                let updated = try await apiService.toggleRoutine(routineId: routine.routineId)
                if let idx = routines.firstIndex(where: { $0.id == updated.id }) {
                    routines[idx] = updated
                } else {
                    await refresh()
                }
            } catch {
                errorMessage = error.localizedDescription
                showError = true
            }
        }
    }
    
    func create(name: String, cron: String, botId: String, prompt: String) async -> Bool {
        isSaving = true
        defer { isSaving = false }
        do {
            let created = try await apiService.createRoutine(
                name: name,
                cron: cron,
                botId: botId,
                prompt: prompt
            )
            routines.insert(created, at: 0)
            return true
        } catch {
            errorMessage = error.localizedDescription
            showError = true
            return false
        }
    }
}
