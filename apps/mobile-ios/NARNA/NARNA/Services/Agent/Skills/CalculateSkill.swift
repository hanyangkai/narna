//
//  CalculateSkill.swift
//  NARNA
//
//  Safe on-device arithmetic. Rejects anything that is not a plain expression.
//

import Foundation

struct CalculateSkill: SkillHandler {
    let definition = SkillDefinition(
        name: "calculate",
        description: "Evaluate a basic arithmetic expression (+ - * / ^ % parentheses, decimals). On-device only.",
        parameters: SkillJSONSchema(
            properties: [
                "expression": SkillJSONProperty(type: "string", description: "Arithmetic expression, e.g. (12.5 + 3) * 2"),
            ],
            required: ["expression"]
        ),
        location: .onDevice,
        permission: .none,
        displayName: "Calculate"
    )

    func run(arguments: [String: SkillJSONValue]) async -> SkillResult {
        guard let expr = arguments["expression"]?.stringValue?
            .trimmingCharacters(in: .whitespacesAndNewlines),
              !expr.isEmpty else {
            return .failure("Missing expression.")
        }
        do {
            let value = try Self.evaluate(expr)
            let formatted = Self.format(value)
            return .success(formatted, detail: "\(expr) = \(formatted)", data: [
                "expression": .string(expr),
                "result": .number(value),
            ])
        } catch {
            return .failure(error.localizedDescription)
        }
    }

    enum CalcError: LocalizedError {
        case invalidCharacters
        case empty
        case divideByZero
        case parse

        var errorDescription: String? {
            switch self {
            case .invalidCharacters: return "Only numbers and + - * / ^ % ( ) . are allowed."
            case .empty: return "Expression is empty."
            case .divideByZero: return "Division by zero."
            case .parse: return "Could not parse the expression."
            }
        }
    }

    /// Allowed: digits, whitespace, operators, parentheses, decimal point, percent, caret.
    static func isSafeExpression(_ s: String) -> Bool {
        let allowed = CharacterSet(charactersIn: "0123456789+-*/^%().eE ")
        return s.unicodeScalars.allSatisfy { allowed.contains($0) }
    }

    static func evaluate(_ raw: String) throws -> Double {
        let s = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !s.isEmpty else { throw CalcError.empty }
        guard isSafeExpression(s) else { throw CalcError.invalidCharacters }
        // Rewrite ^ to ** for NSExpression? NSExpression uses ** for power in some versions;
        // use a tiny recursive-descent parser instead for predictability.
        var parser = Parser(s)
        let value = try parser.parseExpression()
        guard parser.atEnd else { throw CalcError.parse }
        return value
    }

    static func format(_ value: Double) -> String {
        if value.rounded() == value, abs(value) < 1e15 {
            return String(Int(value))
        }
        var s = String(format: "%.10g", value)
        if s == "-0" { s = "0" }
        return s
    }

    // MARK: - Parser

    private struct Parser {
        let chars: [Character]
        var i = 0

        init(_ s: String) { chars = Array(s) }

        var atEnd: Bool {
            var j = i
            while j < chars.count, chars[j].isWhitespace { j += 1 }
            return j >= chars.count
        }

        mutating func skipWS() {
            while i < chars.count, chars[i].isWhitespace { i += 1 }
        }

        mutating func peek() -> Character? {
            skipWS()
            return i < chars.count ? chars[i] : nil
        }

        mutating func consume(_ c: Character) -> Bool {
            skipWS()
            guard i < chars.count, chars[i] == c else { return false }
            i += 1
            return true
        }

        mutating func parseExpression() throws -> Double {
            var v = try parseTerm()
            while true {
                if consume("+") { v += try parseTerm() }
                else if consume("-") { v -= try parseTerm() }
                else { break }
            }
            return v
        }

        mutating func parseTerm() throws -> Double {
            var v = try parsePower()
            while true {
                if consume("*") { v *= try parsePower() }
                else if consume("/") {
                    let d = try parsePower()
                    if d == 0 { throw CalcError.divideByZero }
                    v /= d
                } else if consume("%") {
                    let d = try parsePower()
                    if d == 0 { throw CalcError.divideByZero }
                    v = v.truncatingRemainder(dividingBy: d)
                } else { break }
            }
            return v
        }

        mutating func parsePower() throws -> Double {
            let base = try parseUnary()
            if consume("^") {
                let exp = try parseUnary()
                return pow(base, exp)
            }
            return base
        }

        mutating func parseUnary() throws -> Double {
            if consume("+") { return try parseUnary() }
            if consume("-") { return try -parseUnary() }
            return try parsePrimary()
        }

        mutating func parsePrimary() throws -> Double {
            skipWS()
            if consume("(") {
                let v = try parseExpression()
                guard consume(")") else { throw CalcError.parse }
                return v
            }
            return try parseNumber()
        }

        mutating func parseNumber() throws -> Double {
            skipWS()
            let start = i
            if i < chars.count, chars[i] == "." || chars[i].isNumber {
                while i < chars.count, chars[i].isNumber { i += 1 }
                if i < chars.count, chars[i] == "." {
                    i += 1
                    while i < chars.count, chars[i].isNumber { i += 1 }
                }
                if i < chars.count, chars[i] == "e" || chars[i] == "E" {
                    i += 1
                    if i < chars.count, chars[i] == "+" || chars[i] == "-" { i += 1 }
                    while i < chars.count, chars[i].isNumber { i += 1 }
                }
            }
            let slice = String(chars[start..<i])
            guard let v = Double(slice) else { throw CalcError.parse }
            return v
        }
    }
}
