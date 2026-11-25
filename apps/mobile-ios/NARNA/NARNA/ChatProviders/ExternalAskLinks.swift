//
//  ExternalAskLinks.swift
//  NARNA
//
//  Open ChatGPT / Gemini with the user's prompt — no scraping or automation.
//

import Foundation
import UIKit

enum ExternalAskLinks {
    static func chatGPTURL(prompt: String) -> URL? {
        var components = URLComponents(string: "https://chatgpt.com/")
        components?.queryItems = [URLQueryItem(name: "q", value: prompt)]
        return components?.url
    }

    static func geminiURL() -> URL? {
        URL(string: "https://gemini.google.com/app")
    }

    @MainActor
    static func askChatGPT(prompt: String) {
        UIPasteboard.general.string = prompt
        if let url = chatGPTURL(prompt: prompt) {
            UIApplication.shared.open(url)
        }
    }

    @MainActor
    static func askGemini(prompt: String) {
        UIPasteboard.general.string = prompt
        if let url = geminiURL() {
            UIApplication.shared.open(url)
        }
    }
}
