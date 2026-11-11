//
//  ChatBot.swift
//  NARNA
//
//  On-device chat bots. The pinned Chief of Staff is NaNa Bot and cannot be deleted.
//

import SwiftUI

struct ChatBot: Codable, Identifiable, Equatable, Hashable {
    var id: UUID
    var name: String
    var role: String
    var emoji: String
    var hue: Double
    var persona: String
    var useGlobalKey: Bool
    var providerRaw: String?
    var model: String?
    var baseURLOverride: String
    var createdAt: Date
    var updatedAt: Date
    var lastViewedAt: Date?

    var isChiefOfStaff: Bool { id == ChatBot.chiefOfStaffID }

    var provider: LLMProvider? {
        guard let providerRaw else { return nil }
        return LLMProvider(rawValue: providerRaw)
    }

    var avatarColor: Color {
        Color(hue: hue, saturation: 0.55, brightness: 0.82)
    }

    static let chiefOfStaffID = UUID(uuidString: "A11A0000-0000-4000-8000-000000000001")!

    static func chiefOfStaff() -> ChatBot {
        ChatBot(
            id: chiefOfStaffID,
            name: "NaNa Bot",
            role: "Chief of Staff",
            emoji: "✨",
            hue: 0.60,
            persona: "",
            useGlobalKey: true,
            providerRaw: nil,
            model: nil,
            baseURLOverride: "",
            createdAt: Date(timeIntervalSince1970: 0),
            updatedAt: Date(timeIntervalSince1970: 0),
            lastViewedAt: nil
        )
    }
}

enum ChatBotEmoji {
    static let presets = ["✨", "🧭", "💼", "🧪", "📝", "🎓", "💡", "🔧", "🎯", "🌸", "🧠", "☕️"]
}
