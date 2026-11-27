//
//  ImageDescribeSkill.swift
//  NARNA
//
//  On-device image description via Vision (classification + OCR).
//  Accepts a local file path or base64 payload the user already shared in-app.
//

import Foundation
import Vision
#if canImport(UIKit)
import UIKit
#endif

protocol ImageAnalyzing: Sendable {
    func describe(imageData: Data) async throws -> (labels: [String], text: String)
}

struct VisionImageAnalyzer: ImageAnalyzing {
    func describe(imageData: Data) async throws -> (labels: [String], text: String) {
        #if canImport(UIKit)
        guard let image = UIImage(data: imageData), let cg = image.cgImage else {
            throw NSError(domain: "ImageDescribe", code: 1, userInfo: [NSLocalizedDescriptionKey: "Could not decode image."])
        }
        let labels = try await classify(cg)
        let text = try await ocr(cg)
        return (labels, text)
        #else
        return ([], "")
        #endif
    }

    #if canImport(UIKit)
    private func classify(_ cg: CGImage) async throws -> [String] {
        try await withCheckedThrowingContinuation { cont in
            let req = VNClassifyImageRequest { request, error in
                if let error { cont.resume(throwing: error); return }
                let results = (request.results as? [VNClassificationObservation]) ?? []
                let top = results.prefix(5).filter { $0.confidence > 0.15 }.map {
                    "\($0.identifier) (\(Int($0.confidence * 100))%)"
                }
                cont.resume(returning: Array(top))
            }
            let handler = VNImageRequestHandler(cgImage: cg, options: [:])
            do { try handler.perform([req]) } catch { cont.resume(throwing: error) }
        }
    }

    private func ocr(_ cg: CGImage) async throws -> String {
        try await withCheckedThrowingContinuation { cont in
            let req = VNRecognizeTextRequest { request, error in
                if let error { cont.resume(throwing: error); return }
                let observations = (request.results as? [VNRecognizedTextObservation]) ?? []
                let lines = observations.compactMap { $0.topCandidates(1).first?.string }
                cont.resume(returning: lines.joined(separator: "\n"))
            }
            req.recognitionLevel = .accurate
            let handler = VNImageRequestHandler(cgImage: cg, options: [:])
            do { try handler.perform([req]) } catch { cont.resume(throwing: error) }
        }
    }
    #endif
}

struct ImageDescribeSkill: SkillHandler {
    let analyzer: ImageAnalyzing

    init(analyzer: ImageAnalyzing = VisionImageAnalyzer()) {
        self.analyzer = analyzer
    }

    var definition: SkillDefinition {
        SkillDefinition(
            name: "describe_image",
            description: "Describe an on-device image using Apple Vision (labels + OCR). Provide file_path under the app sandbox or base64 image data. May need Photos permission if loading from the library via the UI.",
            parameters: SkillJSONSchema(
                properties: [
                    "file_path": SkillJSONProperty(type: "string", description: "Absolute local path to an image file"),
                    "base64": SkillJSONProperty(type: "string", description: "Base64-encoded image bytes"),
                ],
                required: []
            ),
            location: .onDevice,
            permission: .photoLibrary,
            displayName: "Describe image"
        )
    }

    func run(arguments: [String: SkillJSONValue]) async -> SkillResult {
        let data: Data?
        if let b64 = arguments["base64"]?.stringValue, !b64.isEmpty {
            data = Data(base64Encoded: b64)
        } else if let path = arguments["file_path"]?.stringValue, !path.isEmpty {
            data = try? Data(contentsOf: URL(fileURLWithPath: path))
        } else {
            data = nil
        }
        guard let data, !data.isEmpty else {
            return .failure("Provide file_path or base64 image data.")
        }
        do {
            let result = try await analyzer.describe(imageData: data)
            var parts: [String] = []
            if !result.labels.isEmpty {
                parts.append("Labels: " + result.labels.joined(separator: ", "))
            }
            if !result.text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                parts.append("Text in image:\n\(result.text)")
            }
            if parts.isEmpty {
                return .success("No strong labels or text were detected in this image.")
            }
            return .success(parts.joined(separator: "\n\n"), data: [
                "label_count": .number(Double(result.labels.count)),
            ])
        } catch {
            return .failure("Image analysis failed: \(error.localizedDescription)")
        }
    }
}
