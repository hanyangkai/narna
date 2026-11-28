//
//  WebLookupSkill.swift
//  NARNA
//
//  Official free/keyless APIs only:
//  - Wikipedia REST summary (wikimedia.org)
//  - DuckDuckGo Instant Answer API (api.duckduckgo.com)
//  No HTML scraping, no paid search.
//

import Foundation

struct WebLookupSkill: SkillHandler {
    var session: URLSession
    var cache: RateLimitCache

    init(session: URLSession = .shared, cache: RateLimitCache = .shared) {
        self.session = session
        self.cache = cache
    }

    var definition: SkillDefinition {
        SkillDefinition(
            name: "web_lookup",
            description: "Look up a topic via Wikipedia REST summary and DuckDuckGo Instant Answer (official free APIs, no scraping).",
            parameters: SkillJSONSchema(
                properties: [
                    "query": SkillJSONProperty(type: "string", description: "Search or topic query"),
                    "source": SkillJSONProperty(type: "string", description: "auto | wikipedia | duckduckgo",
                                                enum: ["auto", "wikipedia", "duckduckgo"]),
                ],
                required: ["query"]
            ),
            location: .networkFree,
            permission: .none,
            displayName: "Web lookup"
        )
    }

    func run(arguments: [String: SkillJSONValue]) async -> SkillResult {
        guard let query = arguments["query"]?.stringValue?.trimmingCharacters(in: .whitespacesAndNewlines),
              !query.isEmpty else { return .failure("Missing query.") }
        let source = (arguments["source"]?.stringValue ?? "auto").lowercased()

        let cacheKey = "web:\(source):\(query.lowercased())"
        if let hit = await cache.get(cacheKey) {
            return .success(hit, detail: "Cached web lookup.")
        }
        guard await cache.consume(bucket: "web_lookup", capacity: 12, refillPerSecond: 0.25) else {
            return .failure("Web lookup rate limit reached. Try again shortly.")
        }

        var parts: [String] = []
        if source == "auto" || source == "wikipedia" {
            if let wiki = await wikipedia(query) { parts.append(wiki) }
        }
        if source == "auto" || source == "duckduckgo" {
            if let ddg = await duckDuckGo(query) { parts.append(ddg) }
        }
        guard !parts.isEmpty else {
            return .failure("No results from free lookup APIs for “\(query)”.")
        }
        let joined = parts.joined(separator: "\n\n")
        await cache.set(cacheKey, value: joined, ttl: 1800)
        return .success(joined, data: ["query": .string(query), "sources": .number(Double(parts.count))])
    }

    func wikipedia(_ query: String) async -> String? {
        let title = query.replacingOccurrences(of: " ", with: "_")
        var comps = URLComponents(string: "https://en.wikipedia.org/api/rest_v1/page/summary/\(title.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? title)")!
        // Also try search if direct title fails — use the opensearch-free REST: page/summary often 404s.
        guard var url = comps.url else { return nil }
        do {
            var (data, resp) = try await session.data(from: url)
            var code = (resp as? HTTPURLResponse)?.statusCode ?? 0
            if code == 404 {
                // Resolve via Wikipedia Action API search (official, keyless).
                if let resolved = await wikipediaSearchTitle(query) {
                    comps = URLComponents(string: "https://en.wikipedia.org/api/rest_v1/page/summary/\(resolved.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? resolved)")!
                    guard let u2 = comps.url else { return nil }
                    url = u2
                    (data, resp) = try await session.data(from: url)
                    code = (resp as? HTTPURLResponse)?.statusCode ?? 0
                }
            }
            guard (200..<300).contains(code),
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return nil }
            let titleOut = (json["title"] as? String) ?? query
            let extract = (json["extract"] as? String)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            let pageURL = ((json["content_urls"] as? [String: Any])?["desktop"] as? [String: Any])?["page"] as? String
            guard !extract.isEmpty else { return nil }
            var out = "**Wikipedia — \(titleOut)**\n\(extract)"
            if let pageURL { out += "\nSource: \(pageURL)" }
            return out
        } catch {
            return nil
        }
    }

    func wikipediaSearchTitle(_ query: String) async -> String? {
        var comps = URLComponents(string: "https://en.wikipedia.org/w/api.php")!
        comps.queryItems = [
            URLQueryItem(name: "action", value: "opensearch"),
            URLQueryItem(name: "search", value: query),
            URLQueryItem(name: "limit", value: "1"),
            URLQueryItem(name: "namespace", value: "0"),
            URLQueryItem(name: "format", value: "json"),
        ]
        guard let url = comps.url else { return nil }
        do {
            let (data, resp) = try await session.data(from: url)
            guard (resp as? HTTPURLResponse)?.statusCode == 200,
                  let arr = try? JSONSerialization.jsonObject(with: data) as? [Any],
                  arr.count >= 2,
                  let titles = arr[1] as? [String],
                  let first = titles.first else { return nil }
            return first.replacingOccurrences(of: " ", with: "_")
        } catch {
            return nil
        }
    }

    func duckDuckGo(_ query: String) async -> String? {
        var comps = URLComponents(string: "https://api.duckduckgo.com/")!
        comps.queryItems = [
            URLQueryItem(name: "q", value: query),
            URLQueryItem(name: "format", value: "json"),
            URLQueryItem(name: "no_html", value: "1"),
            URLQueryItem(name: "skip_disambig", value: "1"),
        ]
        guard let url = comps.url else { return nil }
        do {
            let (data, resp) = try await session.data(from: url)
            guard (resp as? HTTPURLResponse)?.statusCode == 200,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return nil }
            let heading = (json["Heading"] as? String) ?? ""
            let abstract = (json["AbstractText"] as? String)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
            let abstractURL = (json["AbstractURL"] as? String) ?? ""
            var lines: [String] = []
            if !abstract.isEmpty {
                lines.append("**DuckDuckGo — \(heading.isEmpty ? query : heading)**\n\(abstract)")
                if !abstractURL.isEmpty { lines.append("Source: \(abstractURL)") }
            }
            if let related = json["RelatedTopics"] as? [[String: Any]] {
                let texts = related.compactMap { $0["Text"] as? String }.prefix(3)
                if !texts.isEmpty {
                    lines.append("Related:\n" + texts.map { "• \($0)" }.joined(separator: "\n"))
                }
            }
            let out = lines.joined(separator: "\n").trimmingCharacters(in: .whitespacesAndNewlines)
            return out.isEmpty ? nil : out
        } catch {
            return nil
        }
    }
}

struct ResearchSkill: SkillHandler {
    let web: WebLookupSkill
    let summarize: SummarizeSkill

    init(web: WebLookupSkill = WebLookupSkill(), summarize: SummarizeSkill = SummarizeSkill()) {
        self.web = web
        self.summarize = summarize
    }

    var definition: SkillDefinition {
        SkillDefinition(
            name: "research",
            description: "Research a topic: free web lookup then a short digest of findings.",
            parameters: SkillJSONSchema(
                properties: [
                    "topic": SkillJSONProperty(type: "string", description: "Research topic"),
                ],
                required: ["topic"]
            ),
            location: .networkFree,
            permission: .none,
            displayName: "Research"
        )
    }

    func run(arguments: [String: SkillJSONValue]) async -> SkillResult {
        guard let topic = arguments["topic"]?.stringValue?.trimmingCharacters(in: .whitespacesAndNewlines),
              !topic.isEmpty else { return .failure("Missing topic.") }
        let lookup = await web.run(arguments: ["query": .string(topic), "source": .string("auto")])
        guard lookup.ok else { return lookup }
        let digest = SummarizeSkill.summarize(lookup.summary, maxSentences: 4)
        let body = """
        Research: \(topic)

        \(digest)

        ---
        Sources (free APIs):
        \(lookup.summary)
        """
        return .success(body, detail: lookup.detail, data: ["topic": .string(topic)])
    }
}
