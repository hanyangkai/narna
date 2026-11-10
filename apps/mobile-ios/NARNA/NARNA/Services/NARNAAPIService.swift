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
    @Published var inboxPendingCount: Int = 0
    
    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        return decoder
    }()
    
    private let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        return encoder
    }()
    
    private init() {
        if let saved = UserDefaults.standard.string(forKey: "api_base_url"), !saved.isEmpty {
            baseURL = saved
        }
    }
    
    private var mobileToken: String {
        get throws {
            guard let token = KeychainService.shared.getMobileToken() else {
                throw APIError.notAuthenticated
            }
            return token
        }
    }
    
    // MARK: - Pairing
    
    func verifyPairingCode(_ code: String) async throws -> PairingVerifyResponse {
        let request = PairingVerifyRequest(pairingCode: code)
        return try await post(endpoint: "/v1/mobile/pairing/verify", body: request)
    }
    
    // MARK: - Bots
    
    func listBots() async throws -> [BotInfo] {
        let token = try mobileToken
        return try await get(endpoint: "/v1/mobile/bots?mobile_token=\(token)")
    }
    
    func getBotThread(botId: String, limit: Int = 50) async throws -> BotThreadResponse {
        let token = try mobileToken
        return try await get(endpoint: "/v1/mobile/bots/\(botId)/thread?mobile_token=\(token)&limit=\(limit)")
    }
    
    func sendMessage(botId: String, message: String, threadId: String?) async throws -> SendMessageResponse {
        let token = try mobileToken
        let request = SendMessageRequest(message: message, threadId: threadId)
        return try await post(endpoint: "/v1/mobile/bots/\(botId)/message?mobile_token=\(token)", body: request)
    }
    
    // MARK: - Approvals
    
    func listApprovals() async throws -> [ApprovalInfo] {
        let token = try mobileToken
        return try await get(endpoint: "/v1/mobile/approvals?mobile_token=\(token)")
    }
    
    func allowApproval(approvalId: String) async throws -> ApprovalResponse {
        let token = try mobileToken
        return try await post(endpoint: "/v1/mobile/approvals/\(approvalId)/allow?mobile_token=\(token)", body: EmptyRequest())
    }
    
    func denyApproval(approvalId: String) async throws -> ApprovalResponse {
        let token = try mobileToken
        return try await post(endpoint: "/v1/mobile/approvals/\(approvalId)/deny?mobile_token=\(token)", body: EmptyRequest())
    }
    
    // MARK: - Inbox
    
    func getInbox() async throws -> InboxResponse {
        let token = try mobileToken
        let response: InboxResponse = try await get(endpoint: "/v1/mobile/inbox?mobile_token=\(token)")
        await MainActor.run {
            inboxPendingCount = response.pendingCount
        }
        return response
    }
    
    // MARK: - Routines
    
    func listRoutines() async throws -> [RoutineInfo] {
        let token = try mobileToken
        let response: RoutinesResponse = try await get(endpoint: "/v1/mobile/routines?mobile_token=\(token)")
        return response.routines
    }
    
    func createRoutine(
        name: String,
        cron: String,
        botId: String,
        prompt: String,
        enabled: Bool = true
    ) async throws -> RoutineInfo {
        let token = try mobileToken
        let body = RoutineCreateRequest(
            name: name,
            cron: cron,
            botId: botId,
            prompt: prompt,
            enabled: enabled
        )
        return try await post(endpoint: "/v1/mobile/routines?mobile_token=\(token)", body: body)
    }
    
    func toggleRoutine(routineId: String) async throws -> RoutineInfo {
        let token = try mobileToken
        return try await post(
            endpoint: "/v1/mobile/routines/\(routineId)/toggle?mobile_token=\(token)",
            body: EmptyRequest()
        )
    }
    
    // MARK: - Voice
    
    func startVoice(botId: String, openaiApiKey: String?) async throws -> VoiceSession {
        let token = try mobileToken
        let body = VoiceStartRequest(botId: botId, openaiApiKey: openaiApiKey)
        return try await post(endpoint: "/v1/mobile/voice/start?mobile_token=\(token)", body: body)
    }
    
    func stopVoice(sessionId: String) async throws -> VoiceStopResponse {
        let token = try mobileToken
        let encoded = sessionId.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? sessionId
        return try await post(
            endpoint: "/v1/mobile/voice/stop?session_id=\(encoded)&mobile_token=\(token)",
            body: EmptyRequest()
        )
    }
    
    // MARK: - Remote Access
    
    func getRemoteStatus() async throws -> RemoteConfig {
        let token = try mobileToken
        let response: RemoteStatusResponse = try await get(endpoint: "/v1/mobile/remote/status?mobile_token=\(token)")
        return response.remote
    }
    
    func updateRemoteConfig(mode: String, host: String?, baseUrl: String?) async throws -> RemoteConfig {
        let token = try mobileToken
        let body = RemoteConfigUpdate(mode: mode, host: host, baseUrl: baseUrl)
        let response: RemoteStatusResponse = try await put(
            endpoint: "/v1/mobile/remote/config?mobile_token=\(token)",
            body: body
        )
        return response.remote
    }
    
    // MARK: - Connected Apps
    
    func listConnectedApps() async throws -> [ConnectedApp] {
        let token = try mobileToken
        let response: ConnectedAppsResponse = try await get(endpoint: "/v1/mobile/connected-apps?mobile_token=\(token)")
        return response.apps
    }
    
    func connectApp(_ app: String, accountLabel: String? = nil) async throws -> ConnectedAppMutationResponse {
        let token = try mobileToken
        let body = ConnectedAppAction(accountLabel: accountLabel)
        return try await post(
            endpoint: "/v1/mobile/connected-apps/\(app)/connect?mobile_token=\(token)",
            body: body
        )
    }
    
    func disconnectApp(_ app: String) async throws -> ConnectedAppMutationResponse {
        let token = try mobileToken
        return try await post(
            endpoint: "/v1/mobile/connected-apps/\(app)/disconnect?mobile_token=\(token)",
            body: EmptyRequest()
        )
    }
    
    // MARK: - Push
    
    func registerPushDevice(deviceToken: String, deviceName: String?) async throws -> PushRegisterResponse {
        let token = try mobileToken
        let body = PushRegisterRequest(
            platform: "ios",
            deviceToken: deviceToken,
            deviceName: deviceName
        )
        return try await post(endpoint: "/v1/mobile/push/register?mobile_token=\(token)", body: body)
    }
    
    // MARK: - Generic HTTP Methods
    
    private func get<T: Decodable>(endpoint: String) async throws -> T {
        try await request(method: "GET", endpoint: endpoint, bodyData: nil)
    }
    
    private func post<T: Encodable, R: Decodable>(endpoint: String, body: T) async throws -> R {
        let data = try encoder.encode(body)
        return try await request(method: "POST", endpoint: endpoint, bodyData: data)
    }
    
    private func put<T: Encodable, R: Decodable>(endpoint: String, body: T) async throws -> R {
        let data = try encoder.encode(body)
        return try await request(method: "PUT", endpoint: endpoint, bodyData: data)
    }
    
    private func request<R: Decodable>(method: String, endpoint: String, bodyData: Data?) async throws -> R {
        guard let url = URL(string: baseURL + endpoint) else {
            throw APIError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = bodyData
        
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
