//
//  AgentExecutor.swift
//  NARNA
//
//  Runs an AgentPlanDraft with a concurrency cap. Independent parallel_group
//  steps run together; groups execute in ascending order.
//

import Foundation

final class AgentExecutor: @unchecked Sendable {
    let registry: SkillRegistry
    let maxConcurrent: Int

    init(registry: SkillRegistry = .shared, maxConcurrent: Int = 3) {
        self.registry = registry
        self.maxConcurrent = max(1, maxConcurrent)
    }

    /// Execute the plan, yielding progress snapshots after each task update.
    func run(_ draft: AgentPlanDraft) -> AsyncStream<AgentRunSnapshot> {
        let registry = self.registry
        let maxConcurrent = self.maxConcurrent
        return AsyncStream { continuation in
            let task = Task {
                var tasks: [AgentTaskProgress] = draft.steps.map { step in
                    let def = registry.definition(named: step.skill)
                    return AgentTaskProgress(
                        skillName: step.skill,
                        displayName: def?.displayName ?? step.skill,
                        status: .pending,
                        summary: nil,
                        detail: nil,
                        parallelGroup: step.parallelGroup
                    )
                }

                func emit(complete: Bool = false, final: String? = nil) {
                    continuation.yield(AgentRunSnapshot(tasks: tasks, isComplete: complete, finalAnswer: final))
                }

                emit()

                if draft.steps.isEmpty {
                    emit(complete: true, final: draft.finalAnswerHint)
                    continuation.finish()
                    return
                }

                let groups = Dictionary(grouping: Array(draft.steps.enumerated())) { $0.element.parallelGroup }
                for key in groups.keys.sorted() {
                    guard let batch = groups[key] else { continue }
                    await Self.runBatch(
                        batch,
                        registry: registry,
                        maxConcurrent: maxConcurrent,
                        tasks: &tasks,
                        emit: { emit(complete: false, final: nil) }
                    )
                    if Task.isCancelled { break }
                }

                let final = Self.composeFinalAnswer(tasks: tasks, hint: draft.finalAnswerHint)
                emit(complete: true, final: final)
                continuation.finish()
            }
            continuation.onTermination = { _ in task.cancel() }
        }
    }

    /// Convenience: collect the final snapshot.
    func runToCompletion(_ draft: AgentPlanDraft) async -> AgentRunSnapshot {
        var last = AgentRunSnapshot(tasks: [], isComplete: false, finalAnswer: nil)
        for await snap in run(draft) {
            last = snap
        }
        return last
    }

    private static func runBatch(
        _ batch: [(offset: Int, element: AgentPlanDraft.Step)],
        registry: SkillRegistry,
        maxConcurrent: Int,
        tasks: inout [AgentTaskProgress],
        emit: () -> Void
    ) async {
        var i = 0
        while i < batch.count {
            let slice = Array(batch[i..<min(i + maxConcurrent, batch.count)])
            for item in slice {
                tasks[item.offset].status = .running
                tasks[item.offset].updatedAt = Date()
            }
            emit()

            await withTaskGroup(of: (Int, SkillResult).self) { group in
                for item in slice {
                    let step = item.element
                    let idx = item.offset
                    let handler = registry.handler(named: step.skill)
                    group.addTask {
                        guard let handler else {
                            return (idx, .failure("Unknown skill “\(step.skill)”."))
                        }
                        let result = await handler.run(arguments: step.arguments)
                        return (idx, result)
                    }
                }
                for await (idx, result) in group {
                    tasks[idx].status = result.ok ? .succeeded : .failed
                    tasks[idx].summary = result.summary
                    tasks[idx].detail = result.detail
                    tasks[idx].updatedAt = Date()
                    emit()
                }
            }
            i += maxConcurrent
        }
    }

    static func composeFinalAnswer(tasks: [AgentTaskProgress], hint: String?) -> String {
        var parts: [String] = []
        if let hint, !hint.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            parts.append(hint)
        }
        for (i, t) in tasks.enumerated() {
            let status = t.status == .succeeded ? "✓" : (t.status == .failed ? "✗" : "•")
            let body = t.summary ?? t.status.rawValue
            parts.append("\(status) **\(t.displayName)** (\(i + 1)/\(tasks.count))\n\(body)")
        }
        return parts.joined(separator: "\n\n")
    }
}
