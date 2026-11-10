//
//  VoiceCallViewModel.swift
//  NARNA
//

import Foundation

@MainActor
class VoiceCallViewModel: ObservableObject {
    @Published var isLive = false
    @Published var isBusy = false
    @Published var session: VoiceSession?
    @Published var transcriptLines: [String] = []
    @Published var selectedBotId: String = "bot_1"
    @Published var bots: [BotInfo] = []
    @Published var errorMessage: String?
    @Published var showError = false
    @Published var statusNote: String = "Tap the mic to start a live call."
    
    private let apiService = NARNAAPIService.shared
    
    func loadBots() {
        Task {
            do {
                let list = try await apiService.listBots()
                bots = list
                if let first = list.first {
                    selectedBotId = first.botId
                }
            } catch {
                // Keep default bot_1 when offline / unpaired mid-session
            }
        }
    }
    
    func toggleCall() {
        if isLive {
            stopCall()
        } else {
            startCall()
        }
    }
    
    func startCall() {
        isBusy = true
        let key = UserDefaults.standard.string(forKey: "openai_voice_api_key")
        let apiKey = (key?.isEmpty == false) ? key : nil
        
        Task {
            do {
                let session = try await apiService.startVoice(botId: selectedBotId, openaiApiKey: apiKey)
                self.session = session
                self.isLive = true
                self.statusNote = session.note
                self.transcriptLines = [
                    "Call connected · \(session.botId)",
                    "Listening… (Voice beta — Realtime audio landing next)"
                ]
                isBusy = false
            } catch {
                isBusy = false
                errorMessage = error.localizedDescription
                showError = true
            }
        }
    }
    
    func stopCall() {
        guard let session else {
            isLive = false
            return
        }
        isBusy = true
        Task {
            do {
                _ = try await apiService.stopVoice(sessionId: session.sessionId)
                transcriptLines.append("Call ended")
                statusNote = "Call ended. Tap the mic to start again."
                isLive = false
                self.session = nil
                isBusy = false
            } catch {
                isBusy = false
                isLive = false
                self.session = nil
                errorMessage = error.localizedDescription
                showError = true
            }
        }
    }
}
