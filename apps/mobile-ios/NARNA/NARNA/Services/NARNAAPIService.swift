//
//  NARNAAPIService.swift
//  NARNA
//
//  Created by NARNA Team on 11/10/2026.
//

import Foundation
import Combine

class NARNAAPIService: ObservableObject {
    static let shared = NARNAAPIService()
    
    @Published var baseURL: String = "http://localhost:8765"
    
    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        return decoder
    }()
    
    private let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        return encoder
    }()
    
    private init() {}
    
    // MARK: - Pairing
    
    func verifyPairingCode(_ code: String) async throws -> PairingVerifyResponse {
        let request = PairingVerifyRequest(pairingCode: code)
        return try await post(endpoint: "/v1/mobile/pairing/verify", body: request)
    }
    
    // MARK: - Bots
    
    func listBots() async throws -> [BotInfo] {
        guard let token = KeychainService.shared.getMobileToken() else {
            throw APIError.notAuthenticated
        }
        return try await get(endpoint: "/v1/mobile/bots?mobile_token=\(token)")
    }
    
    func getBotThread(botId: String, limit: Int = 50) async throws -> BotThreadResponse {
        guard let token = KeychainService.shared.getMobileToken() else {
            throw APIError.notAuthenticated
        }
        return try await get(endpoint: "/v1/mobile/bots/\(botId)/thread?mobile_token=\(token)&limit=\(limit)")
    }
    
    func sendMessage(botId: String, message: String, threadId: String?) async throws -> SendMessageResponse {
        guard let token = KeychainService.shared.getMobileToken() else {
            throw APIError.notAuthenticated
        }
        let request = SendMessageRequest(message: message, threadId: threadId)
        return try await post(endpoint: "/v1/mobile/bots/\(botId)/message?mobile_token=\(token)", body: request)
    }
    
    // MARK: - Approvals
    
    func listApprovals() async throws -> [ApprovalInfo] {
        guard let token = KeychainService.shared.getMobileToken() else {
            throw APIError.notAuthenticated
        }
        return try await get(endpoint: "/v1/mobile/approvals?mobile_token=\(token)")
    }
    
    func allowApproval(approvalId: String) async throws -> ApprovalResponse {
        guard let token = KeychainService.shared.getMobileToken() else {
            throw APIError.notAuthenticated
        }
        return try await post(endpoint: "/v1/mobile/approvals/\(approvalId)/allow?mobile_token=\(token)", body: EmptyRequest())
    }
    
    func denyApproval(approvalId: String) async throws -> ApprovalResponse {
        guard let token = KeychainService.shared.getMobileToken() else {
            throw APIError.notAuthenticated
        }
        return try await post(endpoint: "/v1/mobile/approvals/\(approvalId)/deny?mobile_token=\(token)", body: EmptyRequest())
    }
    
    // MARK: - Generic HTTP Methods
    
    private func get<T: Decodable>(endpoint: String) async throws -> T {
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard (200...299).contains(httpResponse.statusCode) else {
            if let errorResponse = try? decoder.decode(ErrorResponse.self, from: data) {
                throw APIError.serverError(errorResponse.detail)
            }
            throw APIError.httpError(httpResponse.statusCode)
        }
        
        return try decoder.decode(T.self, from: data)
    }
    
    private func post<T: Encodable, R: Decodable>(endpoint: String, body: T) async throws -> R {
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(body)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        
        guard (200...299).contains(httpResponse.statusCode) else {
            if let errorResponse = try? decoder.decode(ErrorResponse.self, from: data) {
                throw APIError.serverError(errorResponse.detail)
            }
            throw APIError.httpError(httpResponse.statusCode)
        }
        
        return try decoder.decode(R.self, from: data)
    }
}

// MARK: - API Errors

enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case notAuthenticated
    case httpError(Int)
    case serverError(String)
    case networkError(Error)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .notAuthenticated:
            return "Not authenticated. Please pair your device first."
        case .httpError(let code):
            return "HTTP error: \(code)"
        case .serverError(let message):
            return message
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        }
    }
}

// MARK: - Empty Request

struct EmptyRequest: Codable {}
