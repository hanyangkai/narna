//
//  AgentTaskModels.swift
//  NARNA
//
//  Per-task progress shown in the chat UI while the agent runs a plan.
//

import Foundation

enum AgentTaskStatus: String, Codable, Equatable {
    case pending
    case running
    case succeeded
    case failed
    case skipped
}

struct AgentTaskProgress: Codable, Identifiable, Equatable {
    var id: UUID = UUID()
    var skillName: String
    var displayName: String
    var status: AgentTaskStatus
    var summary: String?
    var detail: String?
    var parallelGroup: Int
    var updatedAt: Date = Date()
}

struct AgentRunSnapshot: Codable, Equatable {
    var tasks: [AgentTaskProgress]
    var isComplete: Bool
    var finalAnswer: String?
}
