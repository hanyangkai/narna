//
//  ChatViewModel.swift
//  NARNA
//
//  Created by NARNA Team on 11/10/2026.
//

import Foundation
import Combine

@MainActor
class ChatViewModel: ObservableObject {
    @Published var messages: [ChatMessage] = []
    @Published var inputText: String = ""
    @Published var isLoading = false
    @Published var isSending = false
    @Published var errorMessage: String?
    @Published var showError = false
    @Published var botStatus: String = "idle"
    
    let bot: BotInfo
    private var threadId: String?
    
    private let apiService = NARNAAPIService.shared
    private let webSocketService = WebSocketService()
    private var cancellables = Set<AnyCancellable>()
    
    init(bot: BotInfo) {
        self.bot = bot
        setupWebSocket()
    }
    
    func loadMessages() {
        isLoading = true
        errorMessage = nil
        
        Task {
            do {
                let thread = try await apiService.getBotThread(botId: bot.botId)
                messages = thread.messages
                threadId = thread.threadId
                isLoading = false
            } catch {
                isLoading = false
                showErrorMessage(error.localizedDescription)
            }
        }
    }
    
    func sendMessage() {
        guard !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return
        }
        
        let messageText = inputText
        inputText = ""
        isSending = true
        
        let userMessage = ChatMessage(
            messageId: "temp_\(UUID().uuidString)",
            role: "user",
            content: messageText,
            createdAt: ISO8601DateFormatter().string(from: Date())
        )
        messages.append(userMessage)
        
        Task {
            do {
                let response = try await apiService.sendMessage(
                    botId: bot.botId,
                    message: messageText,
                    threadId: threadId
                )
                
                threadId = response.threadId
                isSending = false
                
                print("✅ Message sent: \(response.messageId)")
            } catch {
                isSending = false
                showErrorMessage(error.localizedDescription)
            }
        }
    }
    
    private func setupWebSocket() {
        webSocketService.connect(botId: bot.botId)
        
        webSocketService.$lastEvent
            .compactMap { $0 }
            .sink { [weak self] event in
                self?.handleWebSocketEvent(event)
            }
            .store(in: &cancellables)
        
        webSocketService.$isConnected
            .sink { isConnected in
                print(isConnected ? "🟢 WebSocket connected" : "🔴 WebSocket disconnected")
            }
            .store(in: &cancellables)
    }
    
    private func handleWebSocketEvent(_ event: WebSocketEvent) {
        switch event.type {
        case "connected":
            print("✅ WebSocket connected to bot: \(event.botId ?? "unknown")")
            
        case "status":
            if let status = event.status {
                botStatus = status
                print("📊 Bot status: \(status)")
            }
            
        case "message":
            if let messageId = event.messageId,
               let role = event.role,
               let content = event.content {
                let message = ChatMessage(
                    messageId: messageId,
                    role: role,
                    content: content,
                    createdAt: event.timestamp
                )
                
                if !messages.contains(where: { $0.messageId == messageId }) {
                    messages.append(message)
                }
            }
            
        case "approval_required":
            print("⚠️ Approval required: \(event.description ?? "unknown")")
            
        case "tool_execution":
            print("🔧 Tool execution: \(event.description ?? "unknown")")
            
        case "error":
            if let error = event.error {
                showErrorMessage("Bot error: \(error)")
            }
            
        default:
            print("❓ Unknown event type: \(event.type)")
        }
    }
    
    func disconnect() {
        webSocketService.disconnect()
    }
    
    private func showErrorMessage(_ message: String) {
        errorMessage = message
        showError = true
    }
    
    deinit {
        webSocketService.disconnect()
    }
}
