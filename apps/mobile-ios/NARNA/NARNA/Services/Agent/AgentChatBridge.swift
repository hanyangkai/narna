//
//  AgentChatBridge.swift
//  NARNA
//
//  Bridges chat providers (on-device / free pool / BYOK) into AgentPlanner's LLM port,
//  and runs plan → execute → final answer for AIChatViewModel.
//

import Foundation

struct FreePoolAgentLLM: AgentLLMCompleting {
    func complete(system: String, user: String) async throws -> String {
        let reply = try await FreePoolProvider.complete(
            system: system,
            turns: [LLMTurn(role: .user, content: user)]
        )
        return reply.content
    }
}

struct OnDeviceAgentLLM: AgentLLMCompleting {
    func complete(system: String, user: String) async throws -> String {
        try await OnDeviceFoundationProvider.complete(
            system: system,
            turns: [LLMTurn(role: .user, content: user)]
        )
    }
}

struct BYOKAgentLLM: AgentLLMCompleting {
    let config: LLMRequestConfig
    func complete(system: String, user: String) async throws -> String {
        try await LLMService.shared.complete(
            config: config,
            system: system,
            turns: [LLMTurn(role: .user, content: user)]
        )
    }
}

enum AgentChatBridge {
    static func llm(for route: ChatProviderKind, byokConfig: LLMRequestConfig?) -> AgentLLMCompleting? {
        switch route {
        case .onDevice: return OnDeviceAgentLLM()
        case .freePool: return FreePoolAgentLLM()
        case .byok:
            guard let byokConfig else { return nil }
            return BYOKAgentLLM(config: byokConfig)
        case .agent, .paywall, .unavailable:
            return nil
        }
    }

    /// Run planner + executor, streaming task progress.
    static func runAgent(
        message: String,
        route: ChatProviderKind,
        byokConfig: LLMRequestConfig?,
        registry: SkillRegistry = .shared,
        maxConcurrent: Int = 3
    ) -> AsyncStream<AgentRunSnapshot> {
        AsyncStream { continuation in
            let task = Task {
                let llm = llm(for: route, byokConfig: byokConfig)
                let planner = AgentPlanner(registry: registry, llm: llm)
                let draft = await planner.plan(userMessage: message)
                if draft.steps.isEmpty {
                    continuation.yield(AgentRunSnapshot(tasks: [], isComplete: true, finalAnswer: nil))
                    continuation.finish()
                    return
                }
                let executor = AgentExecutor(registry: registry, maxConcurrent: maxConcurrent)
                for await snap in executor.run(draft) {
                    continuation.yield(snap)
                    if snap.isComplete { break }
                }
                continuation.finish()
            }
            continuation.onTermination = { _ in task.cancel() }
        }
    }
}
