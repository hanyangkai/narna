//
//  OnboardingView.swift
//  NARNA
//
//  Dual-path AI onboarding: external Claude/ChatGPT (MausBot-style) OR NARNA Pro (App Store).
//

import SwiftUI
import UIKit

struct OnboardingView: View {
    @Binding var isPaired: Bool
    var onSkipToPairing: (() -> Void)? = nil
    var embedded: Bool = false
    
    @EnvironmentObject var apiService: NARNAAPIService
    
    @State private var status: OnboardingStatusResponse?
    @State private var products: [SubscriptionProduct] = []
    @State private var manageURL = "https://apps.apple.com/account/subscriptions"
    @State private var isLoading = true
    @State private var showPairing = false
    @State private var expandedPathId: String? = "external_ai"
    @State private var errorMessage: String?
    @State private var showError = false
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    header
                    
                    if isLoading {
                        ProgressView("Loading…")
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 40)
                    } else {
                        ForEach(status?.paths ?? defaultPaths) { path in
                            pathCard(path)
                        }
                        
                        Text("Thanh toán trong app chỉ qua App Store — không crypto.")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                            .padding(.top, 4)
                        
                        if !embedded {
                            Button("Đã có Desktop · Skip to Pair") {
                                if let onSkipToPairing {
                                    onSkipToPairing()
                                } else {
                                    showPairing = true
                                }
                            }
                            .font(.subheadline.weight(.semibold))
                            .frame(maxWidth: .infinity)
                            .padding(.top, 8)
                        }
                    }
                }
                .padding(20)
            }
            .background(Color(.systemGroupedBackground).ignoresSafeArea())
            .navigationTitle(embedded ? "Connect AI" : "Welcome")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                if embedded {
                    ToolbarItem(placement: .navigationBarTrailing) {
                        Button("Done") {
                            onSkipToPairing?()
                        }
                    }
                }
            }
            .sheet(isPresented: $showPairing) {
                PairingView(isPaired: $isPaired)
            }
            .alert("Error", isPresented: $showError) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(errorMessage ?? "Unknown error")
            }
            .onAppear {
                load()
            }
            .onChange(of: isPaired) { paired in
                if paired {
                    showPairing = false
                    load()
                }
            }
        }
        .navigationViewStyle(.stack)
    }
    
    // MARK: - Header
    
    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("NARNA")
                .font(.system(size: 34, weight: .bold, design: .rounded))
            
            Text(headerSubtitle)
                .font(.body)
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)
            
            if let status, status.paired {
                HStack(spacing: 8) {
                    Label(status.aiReady ? "AI ready" : "AI chưa sẵn sàng", systemImage: status.aiReady ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
                        .foregroundStyle(status.aiReady ? .green : .orange)
                    Text("·")
                        .foregroundStyle(.tertiary)
                    Text(status.plan.capitalized)
                        .foregroundStyle(.secondary)
                }
                .font(.caption.weight(.semibold))
                .padding(.top, 4)
            }
        }
        .padding(.bottom, 4)
    }
    
    private var headerSubtitle: String {
        if embedded || (status?.paired == true) {
            return "Chọn cách kết nối AI: dùng Claude/ChatGPT của bạn, hoặc mua NARNA Pro rồi gắn API key."
        }
        return "Sau khi cài app, chọn một đường: dùng AI subscription của bạn (Desktop + Pair), hoặc mua NARNA Pro trên App Store."
    }
    
    // MARK: - Path cards
    
    @ViewBuilder
    private func pathCard(_ path: OnboardingPath) -> some View {
        let isExternal = path.id == "external_ai"
        let isExpanded = expandedPathId == path.id
        
        VStack(alignment: .leading, spacing: 14) {
            Button {
                withAnimation(.easeInOut(duration: 0.2)) {
                    expandedPathId = isExpanded ? nil : path.id
                }
            } label: {
                HStack(alignment: .top, spacing: 14) {
                    Image(systemName: isExternal ? "desktopcomputer" : "crown.fill")
                        .font(.title2)
                        .foregroundStyle(isExternal ? Color.accentColor : Color.orange)
                        .frame(width: 36)
                    
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(path.title)
                                .font(.headline)
                                .foregroundStyle(.primary)
                                .multilineTextAlignment(.leading)
                            if path.recommended {
                                Text("Gợi ý")
                                    .font(.caption2.weight(.bold))
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 3)
                                    .background(Color.accentColor.opacity(0.15))
                                    .foregroundStyle(Color.accentColor)
                                    .clipShape(Capsule())
                            }
                        }
                        Text(path.subtitle)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.leading)
                    }
                    
                    Spacer(minLength: 0)
                    
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.tertiary)
                }
            }
            .buttonStyle(.plain)
            
            if isExpanded {
                VStack(alignment: .leading, spacing: 8) {
                    ForEach(Array(path.steps.enumerated()), id: \.offset) { index, step in
                        HStack(alignment: .top, spacing: 10) {
                            Text("\(index + 1)")
                                .font(.caption.weight(.bold))
                                .foregroundStyle(.white)
                                .frame(width: 22, height: 22)
                                .background(Circle().fill(Color.accentColor.opacity(0.85)))
                            Text(step)
                                .font(.subheadline)
                                .foregroundStyle(.primary)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                    }
                }
                
                if isExternal {
                    Button {
                        if let onSkipToPairing, !embedded {
                            onSkipToPairing()
                        } else {
                            showPairing = true
                        }
                    } label: {
                        Label("Tôi đã sẵn sàng Pair", systemImage: "qrcode.viewfinder")
                            .font(.headline)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 14)
                    }
                    .buttonStyle(.borderedProminent)
                } else {
                    proProductsBlock
                }
            }
        }
        .padding(18)
        .background(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .fill(Color(.secondarySystemGroupedBackground))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .stroke(path.recommended ? Color.accentColor.opacity(0.35) : Color.clear, lineWidth: 1.5)
        )
    }
    
    private var proProductsBlock: some View {
        VStack(alignment: .leading, spacing: 12) {
            if products.isEmpty {
                Text("Pro · $19.99/mo · $159.99/yr · Team $99.99/seat")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            } else {
                ForEach(products) { product in
                    HStack {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(product.title)
                                .font(.subheadline.weight(.semibold))
                            if let first = product.includes?.first {
                                Text(first)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        Spacer()
                        Text("\(product.price)\(product.periodLabel)")
                            .font(.subheadline.weight(.bold))
                    }
                    .padding(.vertical, 4)
                }
            }
            
            Text("Mua qua Apple. Sau khi subscribe, gắn API key Claude/OpenAI trong Settings → AI Providers.")
                .font(.caption)
                .foregroundStyle(.secondary)
            
            Button {
                openAppStoreSubscriptions()
            } label: {
                Label("Subscribe on App Store", systemImage: "apple.logo")
                    .font(.headline)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
            }
            .buttonStyle(.borderedProminent)
            .tint(.orange)
            
            Button("Manage subscriptions") {
                openAppStoreSubscriptions()
            }
            .font(.subheadline)
            .frame(maxWidth: .infinity)
        }
    }
    
    // MARK: - Actions
    
    private func load() {
        isLoading = true
        Task {
            do {
                async let statusTask = apiService.getOnboardingStatus()
                async let productsTask = apiService.getSubscriptionProducts()
                let (s, p) = try await (statusTask, productsTask)
                status = s
                products = p.products
                if let ios = p.manageUrls?.ios, !ios.isEmpty {
                    manageURL = ios
                }
                if expandedPathId == nil {
                    expandedPathId = s.paths.first(where: { $0.recommended })?.id ?? s.paths.first?.id
                }
                isLoading = false
            } catch {
                // Fallback UX when backend unreachable
                status = nil
                products = []
                isLoading = false
            }
        }
    }
    
    private func openAppStoreSubscriptions() {
        guard let url = URL(string: manageURL) else { return }
        UIApplication.shared.open(url)
    }
    
    private var defaultPaths: [OnboardingPath] {
        [
            OnboardingPath(
                id: "external_ai",
                title: "Dùng Claude / ChatGPT của bạn",
                subtitle: "MausBot-style — subscription CLI trên Desktop, rồi Pair điện thoại",
                recommended: true,
                steps: [
                    "Cài NARNA Desktop và đăng nhập Claude CLI / Codex",
                    "Hoặc dán API key trong Settings sau khi Pair",
                    "Trên Desktop mở Pair → quét QR bằng app",
                    "Chat trên phone; token model trừ tài khoản AI của bạn"
                ],
                cta: "Tôi đã sẵn sàng Pair",
                products: nil
            ),
            OnboardingPath(
                id: "narna_pro",
                title: "Mua NARNA Pro",
                subtitle: "Cloud agent always-on — thanh toán App Store only",
                recommended: false,
                steps: [
                    "Subscribe Pro trong App Store (không crypto)",
                    "Gắn API key trong Settings → AI Providers",
                    "Hoặc vẫn Pair Desktop nếu dùng CLI subscription"
                ],
                cta: "Subscribe on App Store",
                products: nil
            )
        ]
    }
}

#Preview {
    OnboardingView(isPaired: .constant(false))
        .environmentObject(NARNAAPIService.shared)
}
