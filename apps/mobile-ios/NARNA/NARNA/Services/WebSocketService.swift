//
//  WebSocketService.swift
//  NARNA
//
//  Created by NARNA Team on 11/10/2026.
//

import Foundation
import Combine

class WebSocketService: ObservableObject {
    @Published var isConnected = false
    @Published var lastEvent: WebSocketEvent?
    
    private var webSocketTask: URLSessionWebSocketTask?
    private var cancellables = Set<AnyCancellable>()
    private let decoder = JSONDecoder()
    
    private var baseURL: String {
        NARNAAPIService.shared.baseURL
    }
    
    func connect(botId: String) {
        guard let token = KeychainService.shared.getMobileToken() else {
            print("❌ No mobile token found")
            return
        }
        
        let wsURL = baseURL
            .replacingOccurrences(of: "http://", with: "ws://")
            .replacingOccurrences(of: "https://", with: "wss://")
        
        guard let url = URL(string: "\(wsURL)/v1/mobile/bots/\(botId)/stream?mobile_token=\(token)") else {
            print("❌ Invalid WebSocket URL")
            return
        }
        
        disconnect()
        
        let session = URLSession(configuration: .default)
        webSocketTask = session.webSocketTask(with: url)
        webSocketTask?.resume()
        
        isConnected = true
        receiveMessage()
        
        print("✅ WebSocket connected to bot: \(botId)")
    }
    
    func disconnect() {
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
        isConnected = false
        print("🔌 WebSocket disconnected")
    }
    
    func sendPing() {
        guard isConnected else { return }
        
        webSocketTask?.send(.string("ping")) { [weak self] error in
            if let error = error {
                print("❌ WebSocket ping error: \(error)")
                self?.isConnected = false
            }
        }
    }
    
    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            guard let self = self else { return }
            
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    self.handleMessage(text)
                case .data(let data):
                    if let text = String(data: data, encoding: .utf8) {
                        self.handleMessage(text)
                    }
                @unknown default:
                    break
                }
                
                self.receiveMessage()
                
            case .failure(let error):
                print("❌ WebSocket receive error: \(error)")
                self.isConnected = false
            }
        }
    }
    
    private func handleMessage(_ text: String) {
        guard let data = text.data(using: .utf8) else { return }
        
        do {
            let event = try decoder.decode(WebSocketEvent.self, from: data)
            DispatchQueue.main.async {
                self.lastEvent = event
            }
            print("📨 WebSocket event: \(event.type)")
        } catch {
            print("❌ Failed to decode WebSocket message: \(error)")
        }
    }
}
