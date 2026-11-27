//
//  TextSkills.swift
//  NARNA
//
//  summarize, draft_text, translate — local heuristics + free MyMemory API.
//  No paid services. Translate uses the official MyMemory free endpoint (keyless).
//

import Foundation

// MARK: - Summarize

struct SummarizeSkill: SkillHandler {
    var definition: SkillDefinition {
        SkillDefinition(
            name: "summarize",
            description: "Summarize long text into a short digest with key bullets. On-device extractive summary.",
            parameters: SkillJSONSchema(
                properties: [
                    "text": SkillJSONProperty(type: "string", description: "Text to summarize"),
                    "max_sentences": SkillJSONProperty(type: "number", description: "Max sentences in the digest (default 3)"),
                ],
                required: ["text"]
            ),
            location: .onDevice,
            permission: .none,
            displayName: "Summarize"
        )
    }

    func run(arguments: [String: SkillJSONValue]) async -> SkillResult {
        guard let text = arguments["text"]?.stringValue?.trimmingCharacters(in: .whitespacesAndNewlines),
              !text.isEmpty else { return .failure("Missing text.") }
        let max = Int(arguments["max_sentences"]?.doubleValue ?? 3)
        let summary = Self.summarize(text, maxSentences: max)
        return .success(summary, data: ["chars": .number(Double(text.count))])
    }

    static func summarize(_ text: String, maxSentences: Int = 3) -> String {
        let sentences = splitSentences(text)
        guard !sentences.isEmpty else { return text }
        let n = max(1, min(maxSentences, sentences.count))
        if sentences.count <= n {
            return sentences.joined(separator: " ")
        }
        // Keep first sentence + highest-scoring middle sentences (length + keyword hits).
        var scored = sentences.enumerated().map { idx, s -> (Int, Double, String) in
            let words = s.split(separator: " ").count
            let score = Double(min(words, 40)) + (idx == 0 ? 100 : 0)
            return (idx, score, s)
        }
        scored.sort { $0.1 > $1.1 }
        let picked = scored.prefix(n).sorted { $0.0 < $1.0 }.map(\.2)
        let bullets = picked.map { "• \($0)" }.joined(separator: "\n")
        return bullets
    }

    static func splitSentences(_ text: String) -> [String] {
        var out: [String] = []
        var current = ""
        for ch in text {
            current.append(ch)
            if ".!?".contains(ch) {
                let t = current.trimmingCharacters(in: .whitespacesAndNewlines)
                if !t.isEmpty { out.append(t) }
                current = ""
            }
        }
        let tail = current.trimmingCharacters(in: .whitespacesAndNewlines)
        if !tail.isEmpty { out.append(tail) }
        return out
    }
}

// MARK: - Draft

struct DraftTextSkill: SkillHandler {
    var definition: SkillDefinition {
        SkillDefinition(
            name: "draft_text",
            description: "Draft an email, message, or short document from a brief. Styles: email, message, formal, casual.",
            parameters: SkillJSONSchema(
                properties: [
                    "brief": SkillJSONProperty(type: "string", description: "What the draft should say"),
                    "style": SkillJSONProperty(type: "string", description: "email | message | formal | casual",
                                               enum: ["email", "message", "formal", "casual"]),
                    "recipient": SkillJSONProperty(type: "string", description: "Optional recipient name"),
                ],
                required: ["brief"]
            ),
            location: .onDevice,
            permission: .none,
            displayName: "Draft text"
        )
    }

    func run(arguments: [String: SkillJSONValue]) async -> SkillResult {
        guard let brief = arguments["brief"]?.stringValue?.trimmingCharacters(in: .whitespacesAndNewlines),
              !brief.isEmpty else { return .failure("Missing brief.") }
        let style = (arguments["style"]?.stringValue ?? "message").lowercased()
        let recipient = arguments["recipient"]?.stringValue
        let draft = Self.draft(brief: brief, style: style, recipient: recipient)
        return .success(draft)
    }

    static func draft(brief: String, style: String, recipient: String?) -> String {
        let name = (recipient?.trimmingCharacters(in: .whitespacesAndNewlines)).flatMap { $0.isEmpty ? nil : $0 }
        switch style {
        case "email", "formal":
            let hello = name.map { "Hi \($0)," } ?? "Hello,"
            return """
            \(hello)

            \(brief)

            Best regards
            """
        case "casual":
            let hello = name.map { "Hey \($0) —" } ?? "Hey —"
            return "\(hello) \(brief)"
        default:
            return brief
        }
    }
}

// MARK: - Translate (MyMemory free API)

struct TranslateSkill: SkillHandler {
    var session: URLSession
    var cache: RateLimitCache

    init(session: URLSession = .shared, cache: RateLimitCache = .shared) {
        self.session = session
        self.cache = cache
    }

    var definition: SkillDefinition {
        SkillDefinition(
            name: "translate",
            description: "Translate text between languages using the free MyMemory Translation API (keyless). langpair like en|vi or en|fr.",
            parameters: SkillJSONSchema(
                properties: [
                    "text": SkillJSONProperty(type: "string", description: "Text to translate"),
                    "langpair": SkillJSONProperty(type: "string", description: "Source|target language codes, e.g. en|es"),
                ],
                required: ["text", "langpair"]
            ),
            location: .networkFree,
            permission: .none,
            displayName: "Translate"
        )
    }

    func run(arguments: [String: SkillJSONValue]) async -> SkillResult {
        guard let text = arguments["text"]?.stringValue?.trimmingCharacters(in: .whitespacesAndNewlines),
              !text.isEmpty else { return .failure("Missing text.") }
        guard let pair = arguments["langpair"]?.stringValue?.trimmingCharacters(in: .whitespacesAndNewlines),
              pair.contains("|") else { return .failure("langpair must look like en|vi.") }

        let cacheKey = "translate:\(pair):\(text)"
        if let hit = await cache.get(cacheKey) {
            return .success(hit, detail: "Cached MyMemory translation (\(pair)).")
        }
        guard await cache.consume(bucket: "mymemory", capacity: 8, refillPerSecond: 0.15) else {
            return .failure("Translate rate limit reached. Try again in a moment.")
        }

        var comps = URLComponents(string: "https://api.mymemory.translated.net/get")!
        comps.queryItems = [
            URLQueryItem(name: "q", value: String(text.prefix(500))),
            URLQueryItem(name: "langpair", value: pair),
        ]
        guard let url = comps.url else { return .failure("Bad translate URL.") }
        do {
            let (data, resp) = try await session.data(from: url)
            let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
            guard (200..<300).contains(code) else {
                return .failure("MyMemory HTTP \(code).")
            }
            let json = (try? JSONSerialization.jsonObject(with: data) as? [String: Any]) ?? [:]
            let translated = ((json["responseData"] as? [String: Any])?["translatedText"] as? String)?
                .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            guard !translated.isEmpty else { return .failure("Empty translation.") }
            await cache.set(cacheKey, value: translated, ttl: 3600)
            return .success(translated, detail: "MyMemory (\(pair))", data: [
                "langpair": .string(pair),
                "source": .string("mymemory"),
            ])
        } catch {
            return .failure("Translate network error: \(error.localizedDescription)")
        }
    }
}
