//
//  ToolCallParser.swift
//  NARNA
//
//  Parses native OpenAI-style tool_calls or JSON-prompted tool use from free
//  models that do not support function calling.
//

import Foundation

enum ToolCallParser {
    /// Extract tool invocations from a model reply.
    /// Supports:
    /// 1. OpenAI `choices[0].message.tool_calls` JSON envelope
    /// 2. A fenced or bare JSON object with `tool_calls` or `steps`
    /// 3. A single `{"name":…,"arguments":…}` object
    static func parse(_ text: String) -> [SkillInvocation] {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty { return [] }

        if let fromEnvelope = parseAPIEnvelope(trimmed), !fromEnvelope.isEmpty {
            return fromEnvelope
        }
        if let json = extractJSONObject(from: trimmed) {
            if let calls = parseToolCallsObject(json), !calls.isEmpty { return calls }
            if let steps = parseStepsObject(json), !steps.isEmpty { return steps }
            if let one = parseSingleCall(json) { return [one] }
        }
        return []
    }

    /// Build the JSON-tool-use system addendum for models without native tools.
    static func jsonToolPrompt(skills: [SkillDefinition]) -> String {
        let tools = skills.map { $0.toolDescriptor }
        let data = (try? JSONEncoder().encode(tools)) ?? Data("[]".utf8)
        let catalog = String(data: data, encoding: .utf8) ?? "[]"
        return """
        You can call tools by replying with ONLY minified JSON (no markdown, no prose) in one of these shapes:
        {"tool_calls":[{"name":"skill_name","arguments":{…}}]}
        {"steps":[{"skill":"skill_name","arguments":{…},"parallel_group":0}]}
        If no tool is needed, reply with normal helpful prose (not JSON).
        Available tools:
        \(catalog)
        Prefer the fewest tools that answer the user. Independent steps may share the same parallel_group.
        """
    }

    // MARK: - Internals

    private static func parseAPIEnvelope(_ text: String) -> [SkillInvocation]? {
        guard let data = text.data(using: .utf8),
              let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return nil }
        let message = ((root["choices"] as? [[String: Any]])?.first?["message"] as? [String: Any])
            ?? (root["message"] as? [String: Any])
            ?? root
        guard let toolCalls = message["tool_calls"] as? [[String: Any]] else { return nil }
        return toolCalls.compactMap { call in
            let fn = (call["function"] as? [String: Any]) ?? call
            guard let name = fn["name"] as? String else { return nil }
            let args = decodeArguments(fn["arguments"])
            return SkillInvocation(name: name, arguments: args)
        }
    }

    private static func parseToolCallsObject(_ json: [String: Any]) -> [SkillInvocation]? {
        guard let arr = json["tool_calls"] as? [[String: Any]] else { return nil }
        return arr.compactMap { item in
            let name = (item["name"] as? String)
                ?? ((item["function"] as? [String: Any])?["name"] as? String)
            guard let name else { return nil }
            let rawArgs = item["arguments"]
                ?? (item["function"] as? [String: Any])?["arguments"]
                ?? item["parameters"]
            return SkillInvocation(name: name, arguments: decodeArguments(rawArgs))
        }
    }

    private static func parseStepsObject(_ json: [String: Any]) -> [SkillInvocation]? {
        guard let arr = json["steps"] as? [[String: Any]] else { return nil }
        return arr.compactMap { item in
            let name = (item["skill"] as? String) ?? (item["name"] as? String)
            guard let name else { return nil }
            return SkillInvocation(name: name, arguments: decodeArguments(item["arguments"] ?? item["parameters"]))
        }
    }

    private static func parseSingleCall(_ json: [String: Any]) -> SkillInvocation? {
        let name = (json["name"] as? String) ?? (json["skill"] as? String)
        guard let name, json["arguments"] != nil || json["parameters"] != nil else { return nil }
        return SkillInvocation(name: name, arguments: decodeArguments(json["arguments"] ?? json["parameters"]))
    }

    static func decodeArguments(_ raw: Any?) -> [String: SkillJSONValue] {
        if let s = raw as? String {
            if let data = s.data(using: .utf8),
               let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                return obj.mapValues { SkillJSONValue.fromAny($0) }
            }
            return [:]
        }
        if let obj = raw as? [String: Any] {
            return obj.mapValues { SkillJSONValue.fromAny($0) }
        }
        return [:]
    }

    /// Pull the first top-level `{…}` from prose / markdown fences.
    static func extractJSONObject(from text: String) -> [String: Any]? {
        var s = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if s.hasPrefix("```") {
            s = s.replacingOccurrences(of: "```json", with: "")
                .replacingOccurrences(of: "```JSON", with: "")
                .replacingOccurrences(of: "```", with: "")
                .trimmingCharacters(in: .whitespacesAndNewlines)
        }
        if let data = s.data(using: .utf8),
           let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
            return obj
        }
        guard let start = s.firstIndex(of: "{"),
              let end = s.lastIndex(of: "}"),
              start < end else { return nil }
        let slice = String(s[start...end])
        guard let data = slice.data(using: .utf8),
              let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return nil }
        return obj
    }

    /// Parse a planner plan that may include parallel_group.
    static func parsePlan(_ text: String) -> AgentPlanDraft? {
        guard let json = extractJSONObject(from: text) else {
            let calls = parse(text)
            if calls.isEmpty { return nil }
            return AgentPlanDraft(steps: calls.enumerated().map {
                AgentPlanDraft.Step(skill: $0.element.name, arguments: $0.element.arguments, parallelGroup: 0)
            }, finalAnswerHint: nil)
        }
        if let steps = json["steps"] as? [[String: Any]] {
            let mapped = steps.compactMap { item -> AgentPlanDraft.Step? in
                let name = (item["skill"] as? String) ?? (item["name"] as? String)
                guard let name else { return nil }
                let group = (item["parallel_group"] as? Int)
                    ?? (item["parallelGroup"] as? Int)
                    ?? Int((item["parallel_group"] as? Double) ?? 0)
                    ?? 0
                return AgentPlanDraft.Step(
                    skill: name,
                    arguments: decodeArguments(item["arguments"] ?? item["parameters"]),
                    parallelGroup: group
                )
            }
            if mapped.isEmpty { return nil }
            let hint = (json["final_answer"] as? String) ?? (json["answer"] as? String)
            return AgentPlanDraft(steps: mapped, finalAnswerHint: hint)
        }
        if let calls = parseToolCallsObject(json), !calls.isEmpty {
            return AgentPlanDraft(steps: calls.map {
                AgentPlanDraft.Step(skill: $0.name, arguments: $0.arguments, parallelGroup: 0)
            }, finalAnswerHint: nil)
        }
        return nil
    }
}

struct AgentPlanDraft: Equatable {
    struct Step: Equatable {
        var skill: String
        var arguments: [String: SkillJSONValue]
        var parallelGroup: Int
    }
    var steps: [Step]
    var finalAnswerHint: String?
}
