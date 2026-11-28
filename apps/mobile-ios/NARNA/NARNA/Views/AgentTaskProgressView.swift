//
//  AgentTaskProgressView.swift
//  NARNA
//
//  Shows per-task progress and results for multi-step agent runs.
//

import SwiftUI

struct AgentTaskProgressView: View {
    let tasks: [AgentTaskProgress]
    var isLive: Bool = false

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 6) {
                Image(systemName: "checklist")
                    .font(.caption.weight(.semibold))
                Text(isLive ? "Working on \(tasks.count) task(s)…" : "Tasks")
                    .font(.caption.weight(.semibold))
                Spacer(minLength: 0)
            }
            .foregroundStyle(.secondary)

            ForEach(tasks) { task in
                HStack(alignment: .top, spacing: 10) {
                    statusIcon(task.status)
                        .frame(width: 18, height: 18)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(task.displayName)
                            .font(.subheadline.weight(.medium))
                        if let summary = task.summary, !summary.isEmpty {
                            Text(summary)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .lineLimit(6)
                        } else if task.status == .running {
                            Text("Running…")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        } else if task.status == .pending {
                            Text("Queued")
                                .font(.caption)
                                .foregroundStyle(.tertiary)
                        }
                    }
                    Spacer(minLength: 0)
                }
                .accessibilityElement(children: .combine)
                .accessibilityLabel("\(task.displayName), \(task.status.rawValue)")
            }
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.tertiarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    @ViewBuilder
    private func statusIcon(_ status: AgentTaskStatus) -> some View {
        switch status {
        case .pending:
            Image(systemName: "circle")
                .foregroundStyle(.tertiary)
        case .running:
            ProgressView()
                .controlSize(.mini)
        case .succeeded:
            Image(systemName: "checkmark.circle.fill")
                .foregroundStyle(.green)
        case .failed:
            Image(systemName: "xmark.circle.fill")
                .foregroundStyle(.orange)
        case .skipped:
            Image(systemName: "minus.circle")
                .foregroundStyle(.secondary)
        }
    }
}
