//
//  Models.swift
//  NARNA
//
//  Created by NARNA Team on 11/10/2026.
//

import Foundation

// MARK: - Pairing Models

struct PairingVerifyRequest: Codable {
    let pairingCode: String
    
    enum CodingKeys: String, CodingKey {
        case pairingCode = "pairing_code"
    }
}

struct PairingVerifyResponse: Codable {
    let mobileToken: String
    let agentName: String
    let orgId: Int
    
    enum CodingKeys: String, CodingKey {
        case mobileToken = "mobile_token"
        case agentName = "agent_name"
        case orgId = "org_id"
    }
}

// MARK: - Bot Models

struct BotInfo: Codable, Identifiable {
    let botId: String
    let name: String
    let model: String
    let status: String
    let lastMessageAt: String?
    
    var id: String { botId }
    
    enum CodingKeys: String, CodingKey {
        case botId = "bot_id"
        case name
        case model
        case status
        case lastMessageAt = "last_message_at"
    }
    
    var statusColor: String {
        switch status {
        case "idle":
            return "green"
        case "working":
            return "blue"
        case "waiting_approval":
            return "orange"
        default:
            return "gray"
        }
    }
    
    var statusText: String {
        switch status {
        case "idle":
            return "Idle"
        case "working":
            return "Working"
        case "waiting_approval":
            return "Waiting Approval"
        default:
            return "Unknown"
        }
    }
}

// MARK: - Message Models

struct ChatMessage: Codable, Identifiable {
    let messageId: String
    let role: String
    let content: String
    let createdAt: String
    
    var id: String { messageId }
    
    enum CodingKeys: String, CodingKey {
        case messageId = "message_id"
        case role
        case content
        case createdAt = "created_at"
    }
    
    var isUser: Bool {
        role == "user"
    }
}

struct BotThreadResponse: Codable {
    let botId: String
    let threadId: String
    let messages: [ChatMessage]
    
    enum CodingKeys: String, CodingKey {
        case botId = "bot_id"
        case threadId = "thread_id"
        case messages
    }
}

struct SendMessageRequest: Codable {
    let message: String
    let threadId: String?
    
    enum CodingKeys: String, CodingKey {
        case message
        case threadId = "thread_id"
    }
}

struct SendMessageResponse: Codable {
    let threadId: String
    let messageId: String
    let status: String
    
    enum CodingKeys: String, CodingKey {
        case threadId = "thread_id"
        case messageId = "message_id"
        case status
    }
}

// MARK: - Approval Models

struct ApprovalInfo: Codable, Identifiable {
    let approvalId: String
    let botId: String
    let actionType: String
    let description: String
    let details: [String: AnyCodable]
    let createdAt: String
    
    var id: String { approvalId }
    
    enum CodingKeys: String, CodingKey {
        case approvalId = "approval_id"
        case botId = "bot_id"
        case actionType = "action_type"
        case description
        case details
        case createdAt = "created_at"
    }
    
    var actionTypeIcon: String {
        switch actionType {
        case "shell_command":
            return "terminal.fill"
        case "file_edit":
            return "doc.text.fill"
        case "web_action":
            return "globe"
        default:
            return "questionmark.circle.fill"
        }
    }
    
    var actionTypeColor: String {
        switch actionType {
        case "shell_command":
            return "blue"
        case "file_edit":
            return "green"
        case "web_action":
            return "purple"
        default:
            return "gray"
        }
    }
}

struct ApprovalResponse: Codable {
    let approvalId: String
    let decision: String
    
    enum CodingKeys: String, CodingKey {
        case approvalId = "approval_id"
        case decision
    }
}

// MARK: - WebSocket Events

struct WebSocketEvent: Codable {
    let type: String
    let botId: String?
    let status: String?
    let messageId: String?
    let role: String?
    let content: String?
    let approvalId: String?
    let actionType: String?
    let description: String?
    let details: [String: AnyCodable]?
    let error: String?
    let timestamp: String
    
    enum CodingKeys: String, CodingKey {
        case type
        case botId = "bot_id"
        case status
        case messageId = "message_id"
        case role
        case content
        case approvalId = "approval_id"
        case actionType = "action_type"
        case description
        case details
        case error
        case timestamp
    }
}

// MARK: - Helper for dynamic JSON

struct AnyCodable: Codable {
    let value: Any
    
    init(_ value: Any) {
        self.value = value
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        
        if let bool = try? container.decode(Bool.self) {
            value = bool
        } else if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let string = try? container.decode(String.self) {
            value = string
        } else if let array = try? container.decode([AnyCodable].self) {
            value = array.map { $0.value }
        } else if let dictionary = try? container.decode([String: AnyCodable].self) {
            value = dictionary.mapValues { $0.value }
        } else {
            value = NSNull()
        }
    }
    
    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        
        switch value {
        case let bool as Bool:
            try container.encode(bool)
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            try container.encode(double)
        case let string as String:
            try container.encode(string)
        case let array as [Any]:
            try container.encode(array.map { AnyCodable($0) })
        case let dictionary as [String: Any]:
            try container.encode(dictionary.mapValues { AnyCodable($0) })
        default:
            try container.encodeNil()
        }
    }
}

// MARK: - Error Response

struct ErrorResponse: Codable {
    let detail: String
}
