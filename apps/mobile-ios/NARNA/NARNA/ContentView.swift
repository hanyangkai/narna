//
//  ContentView.swift
//  NARNA
//
//  Created by NARNA Team on 11/10/2026.
//

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var apiService: NARNAAPIService
    @State private var isPaired = false
    
    var body: some View {
        Group {
            if isPaired {
                BotListView()
            } else {
                PairingView(isPaired: $isPaired)
            }
        }
        .onAppear {
            checkPairingStatus()
        }
    }
    
    private func checkPairingStatus() {
        isPaired = KeychainService.shared.getMobileToken() != nil
    }
}

#Preview {
    ContentView()
        .environmentObject(NARNAAPIService.shared)
}
