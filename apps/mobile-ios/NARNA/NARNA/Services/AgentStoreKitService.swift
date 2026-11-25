//
//  AgentStoreKitService.swift
//  NARNA
//
//  StoreKit 2 — Nana Agent subscriptions (prices from App Store Connect).
//

import Foundation
import StoreKit

@MainActor
final class AgentStoreKitService: ObservableObject {
    static let shared = AgentStoreKitService()

    static let productIds: [String] = [
        "nana.agent.basic.monthly",
        "nana.agent.pro.monthly",
    ]

    @Published var products: [Product] = []
    @Published var purchasedProductId: String?
    @Published var signedTransactionJWS: String?
    @Published var creditsRemaining: Int = 0
    @Published var creditsPerPeriod: Int = 0
    @Published var isLoading = false
    @Published var lastError: String?

    private var updatesTask: Task<Void, Never>?

    private init() {
        updatesTask = Task { await listenForTransactions() }
    }

    var isSubscribed: Bool { purchasedProductId != nil }

    func loadProducts() async {
        isLoading = true
        defer { isLoading = false }
        do {
            products = try await Product.products(for: Set(Self.productIds))
                .sorted { $0.id < $1.id }
        } catch {
            lastError = error.localizedDescription
        }
    }

    func refreshEntitlements() async {
        for await result in Transaction.currentEntitlements {
            guard case .verified(let txn) = result else { continue }
            if Self.productIds.contains(txn.productID) {
                purchasedProductId = txn.productID
                if let jws = txn.jsonRepresentation.base64EncodedString() as String? {
                    // Prefer StoreKit JWS when available via VerificationResult
                }
                await syncJWS(from: result)
                break
            }
        }
        await refreshCreditsFromServer()
    }

    private func syncJWS(from result: VerificationResult<Transaction>) async {
        // StoreKit 2 exposes jwsRepresentation on VerificationResult in recent SDKs.
        // Fallback: send product id encoded mock for local StoreKit testing when JWS unavailable.
        if let jws = Mirror(reflecting: result).children.first(where: { $0.label == "jwsRepresentation" })?.value as? String {
            signedTransactionJWS = jws
            return
        }
        // Local testing fallback — backend accepts non-strict JWS-like payload
        if case .verified(let txn) = result {
            let payload: [String: Any] = [
                "productId": txn.productID,
                "transactionId": String(txn.id),
                "expiresDate": txn.expirationDate.map { Int($0.timeIntervalSince1970 * 1000) } as Any,
            ]
            if let data = try? JSONSerialization.data(withJSONObject: payload) {
                let b64 = data.base64EncodedString()
                    .replacingOccurrences(of: "+", with: "-")
                    .replacingOccurrences(of: "/", with: "_")
                    .replacingOccurrences(of: "=", with: "")
                signedTransactionJWS = "eyJhbGciOiJub25lIn0.\(b64).x"
            }
        }
    }

    func purchase(_ product: Product) async -> Bool {
        do {
            let result = try await product.purchase()
            switch result {
            case .success(let verification):
                guard case .verified(let txn) = verification else {
                    lastError = String(localized: "agent_purchase_unverified")
                    return false
                }
                purchasedProductId = txn.productID
                await syncJWS(from: verification)
                await txn.finish()
                await verifyOnServer()
                return true
            case .userCancelled, .pending:
                return false
            @unknown default:
                return false
            }
        } catch {
            lastError = error.localizedDescription
            return false
        }
    }

    func restore() async {
        do {
            try await AppStore.sync()
            await refreshEntitlements()
            await verifyOnServer()
        } catch {
            lastError = error.localizedDescription
        }
    }

    func manageSubscriptions() async {
        guard let scene = UIApplication.shared.connectedScenes.first as? UIWindowScene else { return }
        do {
            try await AppStore.showManageSubscriptions(in: scene)
        } catch {
            if let url = URL(string: "https://apps.apple.com/account/subscriptions") {
                await UIApplication.shared.open(url)
            }
        }
    }

    func verifyOnServer() async {
        guard let jws = signedTransactionJWS else { return }
        let deviceId = KeychainService.shared.getOrCreateDeviceId()
        let url = AgentProvider.defaultAPIBase.appendingPathComponent("v1/nana/agent/verify")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = ["deviceId": deviceId, "signedTransaction": jws]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        do {
            let (data, _) = try await URLSession.shared.data(for: request)
            if let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let ent = obj["entitlement"] as? [String: Any] {
                creditsRemaining = ent["creditsRemaining"] as? Int ?? creditsRemaining
                creditsPerPeriod = ent["creditsPerPeriod"] as? Int ?? creditsPerPeriod
                purchasedProductId = ent["productId"] as? String ?? purchasedProductId
            }
        } catch {
            lastError = error.localizedDescription
        }
    }

    func refreshCreditsFromServer() async {
        let deviceId = KeychainService.shared.getOrCreateDeviceId()
        var components = URLComponents(
            url: AgentProvider.defaultAPIBase.appendingPathComponent("v1/nana/agent/entitlement"),
            resolvingAgainstBaseURL: false
        )
        components?.queryItems = [URLQueryItem(name: "device_id", value: deviceId)]
        guard let url = components?.url else { return }
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            if let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                let active = obj["active"] as? Bool ?? false
                creditsRemaining = obj["creditsRemaining"] as? Int ?? 0
                creditsPerPeriod = obj["creditsPerPeriod"] as? Int ?? 0
                if active {
                    purchasedProductId = obj["productId"] as? String ?? purchasedProductId
                }
            }
        } catch { /* ignore offline */ }
    }

    private func listenForTransactions() async {
        for await update in Transaction.updates {
            if case .verified(let txn) = update, Self.productIds.contains(txn.productID) {
                purchasedProductId = txn.productID
                await syncJWS(from: update)
                await txn.finish()
                await verifyOnServer()
            }
        }
    }
}

import UIKit
