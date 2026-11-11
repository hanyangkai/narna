//
//  ContentView.swift
//  NARNA
//
//  Created by NARNA Team on 11/10/2026.
//

import SwiftUI

/// Root view. The app opens straight into the standalone AI chat;
/// pairing with the NARNA desktop agent is optional (Settings → NARNA Desktop).
struct ContentView: View {
    var body: some View {
        MainTabView()
    }
}

#Preview {
    ContentView()
        .environmentObject(NARNAAPIService.shared)
}
