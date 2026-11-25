//
//  KeychainService.swift
//  NARNA
//

import Foundation
import Security

class KeychainService {
    static let shared = KeychainService()

    private let service = "org.narna.mobile"
    private let mobileTokenKey = "mobile_token"
    private let agentNameKey = "agent_name"
    private let deviceIdKey = "anonymous_device_id"
    private let openRouterKey = "byo_openrouter_api_key"
    private let openAIKey = "byo_openai_api_key"

    private init() {}

    // MARK: - Mobile Token

    func saveMobileToken(_ token: String) {
        save(key: mobileTokenKey, value: token)
    }

    func getMobileToken() -> String? {
        get(key: mobileTokenKey)
    }

    func deleteMobileToken() {
        delete(key: mobileTokenKey)
    }

    // MARK: - Agent Name

    func saveAgentName(_ name: String) {
        save(key: agentNameKey, value: name)
    }

    func getAgentName() -> String? {
        get(key: agentNameKey)
    }

    func deleteAgentName() {
        delete(key: agentNameKey)
    }

    // MARK: - Anonymous device id (free pool)

    func getOrCreateDeviceId() -> String {
        if let existing = get(key: deviceIdKey), !existing.isEmpty {
            return existing
        }
        let id = UUID().uuidString.lowercased()
        save(key: deviceIdKey, value: id)
        return id
    }

    // MARK: - BYOK (Advanced)

    func saveOpenRouterKey(_ value: String) {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty {
            delete(key: openRouterKey)
        } else {
            save(key: openRouterKey, value: trimmed)
        }
    }

    func getOpenRouterKey() -> String? {
        get(key: openRouterKey)
    }

    func saveOpenAIKey(_ value: String) {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty {
            delete(key: openAIKey)
        } else {
            save(key: openAIKey, value: trimmed)
        }
    }

    func getOpenAIKey() -> String? {
        get(key: openAIKey)
    }

    var hasAnyBYOKey: Bool {
        !(getOpenRouterKey() ?? "").isEmpty || !(getOpenAIKey() ?? "").isEmpty
    }

    // MARK: - Generic

    private func save(key: String, value: String) {
        guard let data = value.data(using: .utf8) else { return }
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
        ]
        SecItemDelete(query as CFDictionary)
        SecItemAdd(query as CFDictionary, nil)
    }

    private func get(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        guard status == errSecSuccess,
              let data = result as? Data,
              let value = String(data: data, encoding: .utf8) else {
            return nil
        }
        return value
    }

    private func delete(key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
        ]
        SecItemDelete(query as CFDictionary)
    }

    func clearAll() {
        deleteMobileToken()
        deleteAgentName()
        // Keep anonymous device id + BYOK keys across unpair of desktop agent
    }

    func clearBYOKeys() {
        delete(key: openRouterKey)
        delete(key: openAIKey)
    }
}
