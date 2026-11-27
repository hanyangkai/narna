//
//  SkillDefinition.swift
//  NARNA
//
//  Declarative skill/tool registry types for Nana AI.
//  Skills are either on-device or call official free/keyless APIs.
//

import Foundation

/// Where a skill runs. Server-side paid tools are intentionally absent.
enum SkillLocation: String, Codable, Equatable {
    case onDevice
    /// Official free / keyless HTTP APIs called from the device (Wikipedia, DuckDuckGo IA, MyMemory, …).
    case networkFree
}

/// Runtime permission the skill may need. Purpose strings live in Info.plist.
enum SkillPermission: String, Codable, Equatable, CaseIterable {
    case none
    case calendars
    case reminders
    case photoLibrary
}

struct SkillJSONSchema: Codable, Equatable {
    var type: String = "object"
    var properties: [String: SkillJSONProperty]
    var required: [String]

    init(properties: [String: SkillJSONProperty], required: [String] = []) {
        self.properties = properties
        self.required = required
    }
}

struct SkillJSONProperty: Codable, Equatable {
    var type: String
    var description: String
    var `enum`: [String]? = nil

    init(type: String, description: String, enum values: [String]? = nil) {
        self.type = type
        self.description = description
        self.enum = values
    }
}

/// OpenAI-compatible tool descriptor used in prompts and (when supported) native tool calling.
struct SkillToolDescriptor: Codable, Equatable {
    var type: String = "function"
    var function: SkillFunctionDescriptor
}

struct SkillFunctionDescriptor: Codable, Equatable {
    var name: String
    var description: String
    var parameters: SkillJSONSchema
}

struct SkillDefinition: Equatable {
    let name: String
    let description: String
    let parameters: SkillJSONSchema
    let location: SkillLocation
    let permission: SkillPermission
    /// Human label shown in the task progress UI.
    let displayName: String

    var toolDescriptor: SkillToolDescriptor {
        SkillToolDescriptor(function: SkillFunctionDescriptor(
            name: name, description: description, parameters: parameters
        ))
    }

    static func == (lhs: SkillDefinition, rhs: SkillDefinition) -> Bool {
        lhs.name == rhs.name
            && lhs.description == rhs.description
            && lhs.parameters == rhs.parameters
            && lhs.location == rhs.location
            && lhs.permission == rhs.permission
            && lhs.displayName == rhs.displayName
    }
}

struct SkillInvocation: Equatable {
    var name: String
    var arguments: [String: SkillJSONValue]
}

/// Lightweight JSON value so skill args stay Codable/Equatable in tests.
enum SkillJSONValue: Codable, Equatable {
    case string(String)
    case number(Double)
    case bool(Bool)
    case null
    case array([SkillJSONValue])
    case object([String: SkillJSONValue])

    init(from decoder: Decoder) throws {
        let c = try decoder.singleValueContainer()
        if c.decodeNil() { self = .null; return }
        if let b = try? c.decode(Bool.self) { self = .bool(b); return }
        if let i = try? c.decode(Int.self) { self = .number(Double(i)); return }
        if let d = try? c.decode(Double.self) { self = .number(d); return }
        if let s = try? c.decode(String.self) { self = .string(s); return }
        if let a = try? c.decode([SkillJSONValue].self) { self = .array(a); return }
        if let o = try? c.decode([String: SkillJSONValue].self) { self = .object(o); return }
        throw DecodingError.dataCorruptedError(in: c, debugDescription: "Unsupported JSON value")
    }

    func encode(to encoder: Encoder) throws {
        var c = encoder.singleValueContainer()
        switch self {
        case .null: try c.encodeNil()
        case .bool(let v): try c.encode(v)
        case .number(let v): try c.encode(v)
        case .string(let v): try c.encode(v)
        case .array(let v): try c.encode(v)
        case .object(let v): try c.encode(v)
        }
    }

    var stringValue: String? {
        switch self {
        case .string(let s): return s
        case .number(let n): return String(n)
        case .bool(let b): return b ? "true" : "false"
        default: return nil
        }
    }

    var doubleValue: Double? {
        switch self {
        case .number(let n): return n
        case .string(let s): return Double(s)
        default: return nil
        }
    }

    var boolValue: Bool? {
        switch self {
        case .bool(let b): return b
        case .string(let s): return ["true", "1", "yes"].contains(s.lowercased())
        default: return nil
        }
    }

    static func fromAny(_ any: Any?) -> SkillJSONValue {
        switch any {
        case nil: return .null
        case let b as Bool: return .bool(b)
        case let i as Int: return .number(Double(i))
        case let d as Double: return .number(d)
        case let s as String: return .string(s)
        case let a as [Any]: return .array(a.map { fromAny($0) })
        case let o as [String: Any]: return .object(o.mapValues { fromAny($0) })
        default: return .string(String(describing: any!))
        }
    }

    func asAny() -> Any? {
        switch self {
        case .null: return nil
        case .bool(let v): return v
        case .number(let v): return v
        case .string(let v): return v
        case .array(let v): return v.map { $0.asAny() as Any }
        case .object(let v): return v.mapValues { $0.asAny() as Any }
        }
    }
}

struct SkillResult: Equatable {
    var ok: Bool
    var summary: String
    var detail: String?
    var data: [String: SkillJSONValue]?

    static func success(_ summary: String, detail: String? = nil, data: [String: SkillJSONValue]? = nil) -> SkillResult {
        SkillResult(ok: true, summary: summary, detail: detail, data: data)
    }

    static func failure(_ message: String) -> SkillResult {
        SkillResult(ok: false, summary: message, detail: nil, data: nil)
    }
}

protocol SkillHandler: Sendable {
    var definition: SkillDefinition { get }
    func run(arguments: [String: SkillJSONValue]) async -> SkillResult
}
