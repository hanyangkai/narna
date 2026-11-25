//
//  PaywallView.swift
//  NARNA
//
//  Nana Agent subscription paywall (App Review 3.1.2): price, period,
//  auto-renew terms, Restore Purchases, Manage Subscription, Terms, Privacy.
//

import SwiftUI
import StoreKit

struct PaywallView: View {
    @EnvironmentObject var subscriptions: AgentSubscriptionManager
    @Environment(\.dismiss) private var dismiss
    @State private var errorText: String?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    header
                    featureList
                    planCards
                    legal
                    if let errorText {
                        Text(errorText).font(.footnote).foregroundStyle(.red)
                    }
                    Button("Restore Purchases") {
                        Task {
                            await subscriptions.restore()
                            if subscriptions.isSubscribed { dismiss() }
                        }
                    }
                    .frame(maxWidth: .infinity)
                    if subscriptions.isSubscribed {
                        Button("Manage Subscription") {
                            Task { await subscriptions.manageSubscription() }
                        }
                        .frame(maxWidth: .infinity)
                    }
                }
                .padding(20)
            }
            .navigationTitle("Nana Agent")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Close") { dismiss() }
                }
            }
            .task { await subscriptions.refresh() }
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Do more with Agent")
                .font(.title.bold())
            Text("Chat stays free. Agent unlocks multi-step work, file and image reading, web search, and stronger models. Your subscription pays for those API calls so Nana stays free to run.")
                .font(.callout)
                .foregroundStyle(.secondary)
            if subscriptions.isSubscribed {
                Label(subscriptions.statusLabel, systemImage: "checkmark.seal.fill")
                    .foregroundStyle(.green)
                    .font(.callout.weight(.medium))
            }
        }
    }

    private var featureList: some View {
        VStack(alignment: .leading, spacing: 8) {
            Label("Multi-step tasks", systemImage: "list.bullet.rectangle")
            Label("Read files and images", systemImage: "doc.viewfinder")
            Label("Web search", systemImage: "globe")
            Label("Stronger models via our server (never a key in the app)", systemImage: "lock.shield")
        }
        .font(.callout)
    }

    private var planCards: some View {
        VStack(spacing: 12) {
            ForEach(AgentPlan.allCases) { plan in
                planCard(plan)
            }
        }
    }

    private func planCard(_ plan: AgentPlan) -> some View {
        let product = subscriptions.product(for: plan)
        let priceText = product?.displayPrice ?? Self.fallbackPrice(plan)
        let period = product?.subscription?.subscriptionPeriod.localizedDescription ?? "month"
        let selected = subscriptions.currentPlan == plan
        return VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(plan.displayName).font(.headline)
                Spacer()
                Text("\(priceText) / \(period)").font(.headline)
            }
            Text("\(plan.monthlyCredits) credits each month")
                .font(.caption)
                .foregroundStyle(.secondary)
            Button {
                Task {
                    do {
                        try await subscriptions.purchase(plan)
                        if subscriptions.isSubscribed { dismiss() }
                    } catch {
                        errorText = error.localizedDescription
                    }
                }
            } label: {
                Text(selected ? "Current plan" : "Subscribe")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .disabled(subscriptions.isPurchasing || selected)
        }
        .padding()
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .overlay {
            if selected {
                RoundedRectangle(cornerRadius: 16).stroke(Color.accentColor, lineWidth: 2)
            }
        }
    }

    private var legal: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Subscriptions auto-renew each month unless you cancel at least 24 hours before the end of the current period. Payment is charged to your Apple ID. You can manage or cancel in your Apple ID settings, or with Manage Subscription above.")
                .font(.footnote)
                .foregroundStyle(.secondary)
            HStack(spacing: 16) {
                Link("Terms of Use", destination: AppConfig.termsURL)
                Link("Privacy Policy", destination: AppConfig.privacyURL)
            }
            .font(.footnote.weight(.semibold))
        }
    }

    private static func fallbackPrice(_ plan: AgentPlan) -> String {
        // Display only when StoreKit products have not loaded yet. Not the charged amount.
        let f = NumberFormatter()
        f.numberStyle = .currency
        f.currencyCode = "VND"
        f.maximumFractionDigits = 0
        return f.string(from: NSNumber(value: plan.proposedPriceVND)) ?? "\(plan.proposedPriceVND)₫"
    }
}

private extension Product.SubscriptionPeriod {
    var localizedDescription: String {
        switch unit {
        case .day: return value == 1 ? "day" : "\(value) days"
        case .week: return value == 1 ? "week" : "\(value) weeks"
        case .month: return value == 1 ? "month" : "\(value) months"
        case .year: return value == 1 ? "year" : "\(value) years"
        @unknown default: return "period"
        }
    }
}
