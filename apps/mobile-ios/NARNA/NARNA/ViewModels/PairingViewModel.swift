//
//  PairingViewModel.swift
//  NARNA
//
//  Created by NARNA Team on 11/10/2026.
//

import Foundation
import Combine

@MainActor
class PairingViewModel: ObservableObject {
    @Published var pairingCode: String = ""
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var showError = false
    
    private let apiService = NARNAAPIService.shared
    private let keychainService = KeychainService.shared
    
    var isCodeValid: Bool {
        pairingCode.count == 6 && pairingCode.allSatisfy { $0.isNumber }
    }
    
    func verifyPairingCode(completion: @escaping (Bool) -> Void) {
        guard isCodeValid else {
            showErrorMessage("Please enter a valid 6-digit pairing code")
            completion(false)
            return
        }
        
        isLoading = true
        errorMessage = nil
        
        Task {
            do {
                let response = try await apiService.verifyPairingCode(pairingCode)
                
                keychainService.saveMobileToken(response.mobileToken)
                keychainService.saveAgentName(response.agentName)
                
                isLoading = false
                completion(true)
                
                print("✅ Paired successfully with agent: \(response.agentName)")
            } catch {
                isLoading = false
                showErrorMessage(error.localizedDescription)
                completion(false)
            }
        }
    }
    
    func handleQRCode(_ qrData: String) -> Bool {
        // Parse QR code: narna://pair?code=123456&org=dev
        guard let url = URL(string: qrData),
              url.scheme == "narna",
              url.host == "pair" else {
            showErrorMessage("Invalid QR code format")
            return false
        }
        
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
              let code = components.queryItems?.first(where: { $0.name == "code" })?.value else {
            showErrorMessage("Could not extract pairing code from QR")
            return false
        }
        
        pairingCode = code
        return true
    }
    
    private func showErrorMessage(_ message: String) {
        errorMessage = message
        showError = true
    }
}
