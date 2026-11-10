//
//  NARNAApp.swift
//  NARNA
//
//  Created by NARNA Team on 11/10/2026.
//

import SwiftUI

@main
struct NARNAApp: App {
    @StateObject private var apiService = NARNAAPIService.shared
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(apiService)
                .preferredColorScheme(.dark)
        }
    }
}
