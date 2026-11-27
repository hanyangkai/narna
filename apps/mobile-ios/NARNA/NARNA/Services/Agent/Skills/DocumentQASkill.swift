//
//  DocumentQASkill.swift
//  NARNA
//
//  On-device PDF / plain-text Q&A via PDFKit extraction + keyword scoring.
//  No cloud upload of the document.
//

import Foundation
import PDFKit

protocol DocumentTextExtracting: Sendable {
    func extractText(fromFilePath path: String, maxChars: Int) throws -> String
}

struct PDFKitTextExtractor: DocumentTextExtracting {
    func extractText(fromFilePath path: String, maxChars: Int) throws -> String {
        let url = URL(fileURLWithPath: path)
        if url.pathExtension.lowercased() == "pdf" {
            guard let doc = PDFDocument(url: url) else {
                throw NSError(domain: "DocumentQA", code: 1, userInfo: [NSLocalizedDescriptionKey: "Could not open PDF."])
            }
            var out = ""
            for i in 0..<doc.pageCount {
                guard let page = doc.page(at: i), let s = page.string else { continue }
                out += s + "\n"
                if out.count >= maxChars { break }
            }
            return String(out.prefix(maxChars))
        }
        let data = try Data(contentsOf: url)
        let text = String(data: data, encoding: .utf8)
            ?? String(data: data, encoding: .isoLatin1)
            ?? ""
        return String(text.prefix(maxChars))
    }
}

struct DocumentQASkill: SkillHandler {
    let extractor: DocumentTextExtracting

    init(extractor: DocumentTextExtracting = PDFKitTextExtractor()) {
        self.extractor = extractor
    }

    var definition: SkillDefinition {
        SkillDefinition(
            name: "document_qa",
            description: "Answer a question about a local PDF or text document using on-device extraction (PDFKit). Provide file_path and question. Optional raw_text skips the file.",
            parameters: SkillJSONSchema(
                properties: [
                    "file_path": SkillJSONProperty(type: "string", description: "Local PDF or text file path"),
                    "raw_text": SkillJSONProperty(type: "string", description: "Document text already in memory"),
                    "question": SkillJSONProperty(type: "string", description: "Question to answer from the document"),
                    "max_chars": SkillJSONProperty(type: "number", description: "Max characters to read (default 20000)"),
                ],
                required: ["question"]
            ),
            location: .onDevice,
            permission: .none,
            displayName: "Document Q&A"
        )
    }

    func run(arguments: [String: SkillJSONValue]) async -> SkillResult {
        guard let question = arguments["question"]?.stringValue?.trimmingCharacters(in: .whitespacesAndNewlines),
              !question.isEmpty else { return .failure("Missing question.") }
        let maxChars = Int(arguments["max_chars"]?.doubleValue ?? 20_000)
        let text: String
        if let raw = arguments["raw_text"]?.stringValue, !raw.isEmpty {
            text = String(raw.prefix(maxChars))
        } else if let path = arguments["file_path"]?.stringValue, !path.isEmpty {
            do {
                text = try extractor.extractText(fromFilePath: path, maxChars: maxChars)
            } catch {
                return .failure(error.localizedDescription)
            }
        } else {
            return .failure("Provide file_path or raw_text.")
        }
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return .failure("Document appears empty.")
        }
        let answer = Self.answer(question: question, document: text)
        return .success(answer, data: [
            "chars_read": .number(Double(text.count)),
        ])
    }

    /// Keyword overlap scoring over sentences / paragraphs.
    static func answer(question: String, document: String, maxSnippets: Int = 3) -> String {
        let qTokens = tokens(question)
        guard !qTokens.isEmpty else { return String(document.prefix(400)) }
        let chunks = chunk(document)
        let scored = chunks.map { chunk -> (Double, String) in
            let cTokens = tokens(chunk)
            let overlap = Double(qTokens.intersection(cTokens).count)
            let score = overlap / Double(max(qTokens.count, 1))
            return (score, chunk)
        }
        .filter { $0.0 > 0 }
        .sorted { $0.0 > $1.0 }
        let top = scored.prefix(maxSnippets).map(\.1)
        if top.isEmpty {
            return "I could not find a clear match. Opening excerpt:\n\n" + String(document.prefix(500))
        }
        return "Based on the document:\n\n" + top.map { "• \($0.trimmingCharacters(in: .whitespacesAndNewlines))" }.joined(separator: "\n\n")
    }

    static func tokens(_ s: String) -> Set<String> {
        let stop: Set<String> = ["the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are", "was", "what", "who", "how", "when", "where", "which", "does", "do", "did"]
        return Set(s.lowercased()
            .components(separatedBy: CharacterSet.alphanumerics.inverted)
            .filter { $0.count > 2 && !stop.contains($0) })
    }

    static func chunk(_ document: String) -> [String] {
        let paras = document.components(separatedBy: "\n\n").map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }.filter { !$0.isEmpty }
        if paras.count >= 2 { return paras }
        return SummarizeSkill.splitSentences(document)
    }
}
