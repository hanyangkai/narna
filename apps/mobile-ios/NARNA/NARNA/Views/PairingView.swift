//
//  PairingView.swift
//  NARNA
//
//  Created by NARNA Team on 11/10/2026.
//

import SwiftUI

struct PairingView: View {
    @Binding var isPaired: Bool
    @StateObject private var viewModel = PairingViewModel()
    @State private var showScanner = false
    @State private var isScanning = false
    @State private var scannedCode: String?
    
    var body: some View {
        NavigationView {
            VStack(spacing: 30) {
                Spacer()
                
                Image(systemName: "qrcode.viewfinder")
                    .font(.system(size: 80))
                    .foregroundColor(.accentColor)
                
                Text("Pair with NARNA")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Text("Scan the QR code from your desktop agent or enter the 6-digit pairing code")
                    .font(.body)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 40)
                
                Spacer()
                
                VStack(spacing: 20) {
                    Button(action: {
                        showScanner = true
                        isScanning = true
                    }) {
                        HStack {
                            Image(systemName: "qrcode")
                            Text("Scan QR Code")
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.accentColor)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                    }
                    
                    Text("or")
                        .foregroundColor(.secondary)
                    
                    VStack(spacing: 12) {
                        TextField("Enter 6-digit code", text: $viewModel.pairingCode)
                            .keyboardType(.numberPad)
                            .textContentType(.oneTimeCode)
                            .multilineTextAlignment(.center)
                            .font(.title2)
                            .padding()
                            .background(Color(.systemGray6))
                            .cornerRadius(12)
                            .onChange(of: viewModel.pairingCode) { oldValue, newValue in
                                if newValue.count > 6 {
                                    viewModel.pairingCode = String(newValue.prefix(6))
                                }
                            }
                        
                        Button(action: verifyCode) {
                            if viewModel.isLoading {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                    .frame(maxWidth: .infinity)
                                    .padding()
                            } else {
                                Text("Verify Code")
                                    .frame(maxWidth: .infinity)
                                    .padding()
                            }
                        }
                        .background(viewModel.isCodeValid ? Color.green : Color.gray)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                        .disabled(!viewModel.isCodeValid || viewModel.isLoading)
                    }
                }
                .padding(.horizontal, 40)
                
                Spacer()
            }
            .navigationTitle("Pairing")
            .navigationBarTitleDisplayMode(.inline)
            .sheet(isPresented: $showScanner) {
                QRScannerSheet(
                    isScanning: $isScanning,
                    scannedCode: $scannedCode,
                    onDismiss: {
                        showScanner = false
                        isScanning = false
                    }
                )
            }
            .onChange(of: scannedCode) { oldValue, newValue in
                if let code = newValue {
                    handleScannedQR(code)
                }
            }
            .alert("Error", isPresented: $viewModel.showError) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(viewModel.errorMessage ?? "Unknown error")
            }
        }
    }
    
    private func handleScannedQR(_ qrData: String) {
        if viewModel.handleQRCode(qrData) {
            showScanner = false
            verifyCode()
        }
    }
    
    private func verifyCode() {
        viewModel.verifyPairingCode { success in
            if success {
                isPaired = true
            }
        }
    }
}

struct QRScannerSheet: View {
    @Binding var isScanning: Bool
    @Binding var scannedCode: String?
    let onDismiss: () -> Void
    
    var body: some View {
        NavigationView {
            ZStack {
                QRScannerView(scannedCode: $scannedCode, isScanning: $isScanning)
                    .edgesIgnoringSafeArea(.all)
                
                VStack {
                    Spacer()
                    
                    Text("Position QR code in the frame")
                        .padding()
                        .background(Color.black.opacity(0.7))
                        .foregroundColor(.white)
                        .cornerRadius(10)
                        .padding(.bottom, 50)
                }
            }
            .navigationTitle("Scan QR Code")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Cancel") {
                        onDismiss()
                    }
                }
            }
        }
    }
}

#Preview {
    PairingView(isPaired: .constant(false))
}
