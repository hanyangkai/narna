//
//  KeychainService.swift
//  NARNA
//
//  Created by NARNA Team on 11/10/2026.
//

import Foundation
import Security

class KeychainService {
    static let shared = KeychainService()
    
    private let service = "org.narna.mobile"
    private let mobileTokenKey = "mobile_token"
    private let agentNameKey = "agent_name"
    
    private init() {}
    
    // MARK: - Mobile Token
    
    func saveMobileToken(_ token: String) {
        save(key: mobileTokenKey, value: token)
    }
    
    func getMobileToken() -> String? {
        return get(key: mobileTokenKey)
    }
    
    func deleteMobileToken() {
        delete(key: mobileTokenKey)
    }
    
    // MARK: - Agent Name
    
    func saveAgentName(_ name: String) {
        save(key: agentNameKey, value: name)
    }
    
    func getAgentName() -> String? {
        return get(key: agentNameKey)
    }
    
    func deleteAgentName() {
        delete(key: agentNameKey)
    }
    
    // MARK: - Generic Keychain Operations
    
    private func save(key: String, value: String) {
        guard let data = value.data(using: .utf8) else { return }
        
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecValueData as String: data
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
            kSecMatchLimit as String: kSecMatchLimitOne
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
            kSecAttrAccount as String: key
        ]
        
        SecItemDelete(query as CFDictionary)
    }
    
    func clearAll() {
        deleteMobileToken()
        deleteAgentName()
    }
}
