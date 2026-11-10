//
//  RoutinesView.swift
//  NARNA
//

import SwiftUI

struct RoutinesView: View {
    @StateObject private var viewModel = RoutinesViewModel()
    @State private var showCreate = false
    
    var body: some View {
        NavigationView {
            ZStack {
                Color(.systemGroupedBackground).ignoresSafeArea()
                
                if viewModel.isLoading {
                    ProgressView("Loading routines…")
                } else if viewModel.routines.isEmpty {
                    EmptyRoutinesView {
                        showCreate = true
                    }
                } else {
                    ScrollView {
                        LazyVStack(spacing: 12) {
                            ForEach(viewModel.routines) { routine in
                                RoutineCard(routine: routine) {
                                    viewModel.toggle(routine)
                                }
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
            .navigationTitle("Routines")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showCreate = true
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showCreate) {
                CreateRoutineSheet(viewModel: viewModel)
            }
            .alert("Error", isPresented: $viewModel.showError) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(viewModel.errorMessage ?? "Unknown error")
            }
            .onAppear {
                viewModel.load()
            }
        }
        .navigationViewStyle(.stack)
    }
}

struct RoutineCard: View {
    let routine: RoutineInfo
    let onToggle: () -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(routine.name)
                        .font(.headline)
                    
                    Text(routine.prompt)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                        .lineLimit(2)
                }
                
                Spacer()
                
                Toggle("", isOn: Binding(
                    get: { routine.enabled },
                    set: { _ in onToggle() }
                ))
                .labelsHidden()
            }
            
            HStack(spacing: 8) {
                StatusChip(
                    text: routine.enabled ? "Enabled" : "Paused",
                    colorName: routine.enabled ? "green" : "gray"
                )
                
                StatusChip(text: routine.cron, colorName: "blue")
                
                StatusChip(text: routine.botId, colorName: "gray")
            }
        }
        .padding(16)
        .background(Color(.secondarySystemGroupedBackground))
        .cornerRadius(16)
        .shadow(color: Color.black.opacity(0.04), radius: 8, y: 2)
    }
}

struct EmptyRoutinesView: View {
    let onCreate: () -> Void
    
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "clock.arrow.2.circlepath")
                .font(.system(size: 52, weight: .light))
                .foregroundColor(.secondary)
            
            Text("No routines yet")
                .font(.title3.weight(.semibold))
            
            Text("Schedule digests, standups, or nightly cleanup runs.")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
            
            Button(action: onCreate) {
                Text("Create routine")
                    .font(.subheadline.weight(.semibold))
                    .padding(.horizontal, 20)
                    .padding(.vertical, 10)
            }
            .buttonStyle(.borderedProminent)
        }
    }
}

struct CreateRoutineSheet: View {
    @ObservedObject var viewModel: RoutinesViewModel
    @Environment(\.dismiss) private var dismiss
    
    @State private var name = ""
    @State private var cron = "0 9 * * *"
    @State private var botId = "bot_1"
    @State private var prompt = "Run morning digest"
    
    var body: some View {
        NavigationView {
            Form {
                Section("Schedule") {
                    TextField("Name", text: $name)
                    TextField("Cron", text: $cron)
                        .autocapitalization(.none)
                    TextField("Bot ID", text: $botId)
                        .autocapitalization(.none)
                }
                
                Section("Prompt") {
                    TextEditor(text: $prompt)
                        .frame(minHeight: 88)
                }
            }
            .navigationTitle("New Routine")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Create") {
                        Task {
                            let ok = await viewModel.create(
                                name: name.trimmingCharacters(in: .whitespacesAndNewlines),
                                cron: cron.trimmingCharacters(in: .whitespacesAndNewlines),
                                botId: botId.trimmingCharacters(in: .whitespacesAndNewlines),
                                prompt: prompt.trimmingCharacters(in: .whitespacesAndNewlines)
                            )
                            if ok { dismiss() }
                        }
                    }
                    .disabled(name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || viewModel.isSaving)
                }
            }
        }
    }
}

#Preview {
    RoutinesView()
}
