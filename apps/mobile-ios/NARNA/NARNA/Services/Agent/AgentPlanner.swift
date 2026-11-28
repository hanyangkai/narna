//
//  AgentPlanner.swift
//  NARNA
//
//  Turns a user request into an AgentPlanDraft using the free-model pool
//  (JSON-prompted tool use) with a deterministic heuristic fallback so the
//  agent still works when the model returns prose only.
//

import Foundation

protocol AgentLLMCompleting: Sendable {
    func complete(system: String, user: String) async throws -> String
}

struct AgentPlanner {
    var registry: SkillRegistry
    var llm: AgentLLMCompleting?
    /// Max steps a single user message may expand into.
    var maxSteps: Int = 8

    init(registry: SkillRegistry = .shared, llm: AgentLLMCompleting? = nil, maxSteps: Int = 8) {
        self.registry = registry
        self.llm = llm
        self.maxSteps = maxSteps
    }

    func plan(userMessage: String) async -> AgentPlanDraft {
        let trimmed = userMessage.trimmingCharacters(in: .whitespacesAndNewlines)
        if let llm {
            let system = Self.plannerSystemPrompt(skills: registry.allDefinitions)
            if let reply = try? await llm.complete(system: system, user: trimmed) {
                if let draft = ToolCallParser.parsePlan(reply), !draft.steps.isEmpty {
                    return clamp(draft)
                }
                // Model may have emitted tool_calls without a steps wrapper.
                let calls = ToolCallParser.parse(reply)
                if !calls.isEmpty {
                    return clamp(AgentPlanDraft(steps: calls.map {
                        .init(skill: $0.name, arguments: $0.arguments, parallelGroup: 0)
                    }, finalAnswerHint: nil))
                }
            }
        }
        return clamp(Self.heuristicPlan(for: trimmed, registry: registry))
    }

    /// Whether the message looks like multi-step / tool work (vs pure chat).
    static func shouldUseAgent(for message: String) -> Bool {
        let m = message.lowercased()
        let triggers = [
            "research", "summarize", "summary", "translate", "draft", "calculate", "compute",
            "remind", "calendar", "schedule", "todo", "to-do", "to do", "plan", "note",
            "look up", "lookup", "search", "wikipedia", "pdf", "document", "describe",
            "image", "and then", "then also", "multi", "queue", "several",
        ]
        if triggers.contains(where: { m.contains($0) }) { return true }
        // Multiple sentences / numbered tasks often mean a queue.
        let lines = message.split(whereSeparator: \.isNewline).filter { !$0.trimmingCharacters(in: .whitespaces).isEmpty }
        if lines.count >= 2 { return true }
        if message.contains("1.") && message.contains("2.") { return true }
        return false
    }

    static func plannerSystemPrompt(skills: [SkillDefinition]) -> String {
        """
        You are Nana AI's planner. Break the user request into skill steps.
        Reply with ONLY minified JSON:
        {"steps":[{"skill":"name","arguments":{…},"parallel_group":0}],"final_answer":"optional hint"}
        Independent skills share the same parallel_group; sequential work increments it.
        \(ToolCallParser.jsonToolPrompt(skills: skills))
        """
    }

    // MARK: - Heuristic fallback (no LLM / parse failure)

    static func heuristicPlan(for message: String, registry: SkillRegistry) -> AgentPlanDraft {
        var steps: [AgentPlanDraft.Step] = []
        let lower = message.lowercased()

        // Split on newlines / " and then " / numbered lists for a simple queue.
        let chunks = splitTasks(message)
        if chunks.count >= 2 {
            for (idx, chunk) in chunks.enumerated() {
                if let step = singleHeuristic(chunk, registry: registry) {
                    steps.append(.init(skill: step.skill, arguments: step.arguments, parallelGroup: idx))
                }
            }
            if !steps.isEmpty { return AgentPlanDraft(steps: steps, finalAnswerHint: nil) }
        }

        if let step = singleHeuristic(message, registry: registry) {
            return AgentPlanDraft(steps: [step], finalAnswerHint: nil)
        }

        // Research-ish prose without an explicit verb.
        if lower.split(separator: " ").count >= 4, registry.definition(named: "research") != nil {
            return AgentPlanDraft(steps: [
                .init(skill: "research", arguments: ["topic": .string(message)], parallelGroup: 0),
            ], finalAnswerHint: nil)
        }
        return AgentPlanDraft(steps: [], finalAnswerHint: nil)
    }

    private static func singleHeuristic(_ message: String, registry: SkillRegistry) -> AgentPlanDraft.Step? {
        let lower = message.lowercased()
        func has(_ name: String) -> Bool { registry.definition(named: name) != nil }

        if (lower.contains("calculate") || lower.contains("compute") || lower.hasPrefix("what is ") && lower.contains("+"))
            && has("calculate") {
            let expr = extractExpression(message) ?? message
            return .init(skill: "calculate", arguments: ["expression": .string(expr)], parallelGroup: 0)
        }
        if (lower.contains("translate") || lower.contains("dịch")) && has("translate") {
            let pair = inferLangPair(lower)
            return .init(skill: "translate", arguments: [
                "text": .string(stripCommand(message, ["translate", "to", "into", "dịch"])),
                "langpair": .string(pair),
            ], parallelGroup: 0)
        }
        if (lower.contains("summarize") || lower.contains("summary") || lower.contains("tldr")) && has("summarize") {
            return .init(skill: "summarize", arguments: ["text": .string(message)], parallelGroup: 0)
        }
        if (lower.contains("draft") || lower.contains("write an email") || lower.contains("write a message")) && has("draft_text") {
            let style = lower.contains("email") ? "email" : (lower.contains("formal") ? "formal" : "message")
            return .init(skill: "draft_text", arguments: [
                "brief": .string(message),
                "style": .string(style),
            ], parallelGroup: 0)
        }
        if (lower.contains("todo") || lower.contains("to-do") || lower.contains("to do") || lower.contains("checklist"))
            && has("plan_todo") {
            if lower.contains("list") {
                return .init(skill: "plan_todo", arguments: ["action": .string("list")], parallelGroup: 0)
            }
            return .init(skill: "plan_todo", arguments: [
                "action": .string("add_many"),
                "titles": .string(message),
            ], parallelGroup: 0)
        }
        if (lower.contains("remind") || lower.contains("reminder")) && has("reminder") {
            return .init(skill: "reminder", arguments: [
                "action": .string("create"),
                "title": .string(stripCommand(message, ["remind me to", "remind me", "reminder", "remind"])),
            ], parallelGroup: 0)
        }
        if (lower.contains("calendar") || lower.contains("schedule") || lower.contains("event")) && has("calendar_event") {
            if lower.contains("list") || lower.contains("whats on") || lower.contains("what's on") {
                return .init(skill: "calendar_event", arguments: ["action": .string("list")], parallelGroup: 0)
            }
            return .init(skill: "calendar_event", arguments: [
                "action": .string("list"),
                "days_ahead": .number(7),
            ], parallelGroup: 0)
        }
        if (lower.contains("note") || lower.contains("notes")) && has("notes") {
            if lower.contains("list") {
                return .init(skill: "notes", arguments: ["action": .string("list")], parallelGroup: 0)
            }
            return .init(skill: "notes", arguments: [
                "action": .string("save"),
                "title": .string(String(message.prefix(40))),
                "body": .string(message),
            ], parallelGroup: 0)
        }
        // document_qa needs a file_path or raw_text supplied by the UI / prior step — skip bare heuristics.
        // describe_image needs file_path/base64 from the UI — skip bare heuristics.
        if (lower.contains("research") || lower.contains("look up") || lower.contains("lookup") || lower.contains("search for"))
            && has("research") {
            let topic = stripCommand(message, ["research", "look up", "lookup", "search for", "search"])
            return .init(skill: "research", arguments: ["topic": .string(topic.isEmpty ? message : topic)], parallelGroup: 0)
        }
        if (lower.contains("wikipedia") || lower.hasPrefix("what is ") || lower.hasPrefix("who is ")) && has("web_lookup") {
            return .init(skill: "web_lookup", arguments: ["query": .string(message)], parallelGroup: 0)
        }
        return nil
    }

    static func splitTasks(_ message: String) -> [String] {
        let byLine = message.components(separatedBy: .newlines)
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .map { line -> String in
                var s = line
                if let re = try? NSRegularExpression(pattern: #"^\d+[\.\)]\s*"#) {
                    s = re.stringByReplacingMatches(in: s, range: NSRange(s.startIndex..., in: s), withTemplate: "")
                }
                if s.hasPrefix("- ") || s.hasPrefix("• ") { s = String(s.dropFirst(2)) }
                return s.trimmingCharacters(in: .whitespacesAndNewlines)
            }
            .filter { !$0.isEmpty }
        if byLine.count >= 2 { return byLine }
        let lowered = message.components(separatedBy: " and then ")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
        if lowered.count >= 2 { return lowered }
        return [message]
    }

    private static func extractExpression(_ s: String) -> String? {
        guard let re = try? NSRegularExpression(pattern: #"[0-9(][0-9+\-*/^%(). eE]+"#) else { return nil }
        let range = NSRange(s.startIndex..., in: s)
        guard let m = re.firstMatch(in: s, range: range), let r = Range(m.range, in: s) else { return nil }
        return String(s[r]).trimmingCharacters(in: .whitespaces)
    }

    private static func inferLangPair(_ lower: String) -> String {
        let map: [(String, String)] = [
            ("vietnamese", "en|vi"), ("việt", "en|vi"), (" spanish", "en|es"), (" french", "en|fr"),
            (" german", "en|de"), (" japanese", "en|ja"), (" chinese", "en|zh-CN"), (" korean", "en|ko"),
        ]
        for (k, v) in map where lower.contains(k) { return v }
        if lower.contains(" to vi") || lower.contains("|vi") { return "en|vi" }
        return "en|es"
    }

    private static func stripCommand(_ message: String, _ verbs: [String]) -> String {
        var s = message
        for v in verbs {
            if let r = s.range(of: v, options: [.caseInsensitive, .anchored]) {
                s.removeSubrange(r)
                break
            }
            if let r = s.range(of: v, options: .caseInsensitive) {
                s.removeSubrange(r)
                break
            }
        }
        return s.trimmingCharacters(in: CharacterSet.whitespacesAndNewlines.union(CharacterSet(charactersIn: ":,-")))
    }

    private func clamp(_ draft: AgentPlanDraft) -> AgentPlanDraft {
        var d = draft
        if d.steps.count > maxSteps {
            d.steps = Array(d.steps.prefix(maxSteps))
        }
        // Drop unknown skills.
        d.steps = d.steps.filter { registry.definition(named: $0.skill) != nil }
        return d
    }
}
