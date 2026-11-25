//
//  AgentSubscriptionManager.swift
//  NARNA
//
//  StoreKit 2 auto-renewable subscriptions for Nana Agent.
//

import Foundation
import UIKit
import StoreKit
import Combine

@MainActor
final class AgentSubscriptionManager: ObservableObject {
    static let shared = AgentSubscriptionManager()

    @Published private(set) var products: [Product] = []
    @Published private(set) var purchasedProductID: String?
    @Published private(set) var currentPlan: AgentPlan?
    @Published private(set) var creditsRemaining: Int
    @Published private(set) var lastTransactionJWS: String?
    @Published var loadError: String?
    @Published var isPurchasing = false

    private var updatesTask: Task<Void, Never>?
    private let defaults = UserDefaults.standard
    private static let creditsKey = "nana_agent_credits_remaining"
    private static let creditsMonthKey = "nana_agent_credits_month"

    var isSubscribed: Bool { currentPlan != nil }
    var statusLabel: String {
        if let currentPlan {
            return "\(currentPlan.displayName) · \(creditsRemaining) credits left"
        }
        return "Not subscribed"
    }

    private init() {
        creditsRemaining = defaults.integer(forKey: Self.creditsKey)
        updatesTask = Task { [weak self] in
            await self?.listenForUpdates()
        }
        Task { await refresh() }
    }

    deinit { updatesTask?.cancel() }

    func refresh() async {
        do {
            let ids = AgentPlanConfig.productIDs
            products = try await Product.products(for: ids).sorted { $0.id < $1.id }
            loadError = nil
        } catch {
            loadError = error.localizedDescription
        }
        await syncEntitlements()
    }

    func product(for plan: AgentPlan) -> Product? {
        products.first { $0.id == plan.productID }
    }

    func purchase(_ plan: AgentPlan) async throws {
        guard let product = product(for: plan) else {
            throw LLMError.server(0, "This subscription is not available yet. Try again later.")
        }
        isPurchasing = true
        defer { isPurchasing = false }
        let result = try await product.purchase()
        switch result {
        case .success(let verification):
            let transaction = try checkVerified(verification)
            await transaction.finish()
            await syncEntitlements()
        case .userCancelled, .pending:
            break
        @unknown default:
            break
        }
    }

    func restore() async {
        try? await AppStore.sync()
        await syncEntitlements()
    }

    func manageSubscription() async {
        guard let scene = UIApplication.shared.connectedScenes.first as? UIWindowScene else { return }
        try? await AppStore.showManageSubscriptions(in: scene)
    }

    func consumeCredit() {
        guard isSubscribed, creditsRemaining > 0 else { return }
        creditsRemaining -= 1
        defaults.set(creditsRemaining, forKey: Self.creditsKey)
    }

    func applyServerCredits(_ remaining: Int) {
        creditsRemaining = max(0, remaining)
        defaults.set(creditsRemaining, forKey: Self.creditsKey)
    }

    private func syncEntitlements() async {
        var latest: Transaction?
        var latestJWS: String?
        for await entitlement in Transaction.currentEntitlements {
            guard case .verified(let transaction) = entitlement else { continue }
            guard AgentPlanConfig.productIDs.contains(transaction.productID) else { continue }
            if transaction.revocationDate != nil { continue }
            if let exp = transaction.expirationDate, exp < Date() { continue }
            if latest == nil || transaction.purchaseDate > latest!.purchaseDate {
                latest = transaction
                latestJWS = entitlement.jwsRepresentation
            }
        }
        purchasedProductID = latest?.productID
        currentPlan = latest.flatMap { AgentPlanConfig.plan(forProductID: $0.productID) }
        lastTransactionJWS = latestJWS
        resetCreditsIfNewPeriod()
    }

    private func resetCreditsIfNewPeriod() {
        let month = Self.yearMonth(Date())
        let stored = defaults.string(forKey: Self.creditsMonthKey)
        if let plan = currentPlan {
            if stored != month {
                creditsRemaining = plan.monthlyCredits
                defaults.set(month, forKey: Self.creditsMonthKey)
                defaults.set(creditsRemaining, forKey: Self.creditsKey)
            }
        } else {
            creditsRemaining = 0
            defaults.set(0, forKey: Self.creditsKey)
        }
    }

    private func checkVerified<T>(_ result: VerificationResult<T>) throws -> T {
        switch result {
        case .unverified(_, let error):
            throw error
        case .verified(let safe):
            return safe
        }
    }

    private static func yearMonth(_ date: Date) -> String {
        let c = Calendar.current
        return String(format: "%04d-%02d", c.component(.year, from: date), c.component(.month, from: date))
    }

    private func listenForUpdates() async {
        for await _ in Transaction.updates {
            await syncEntitlements()
        }
    }
}
