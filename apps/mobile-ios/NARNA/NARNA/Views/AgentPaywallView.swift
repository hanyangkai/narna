//
//  AgentPaywallView.swift
//  NARNA
//
//  App Review 3.1.2 — clear subscription terms, Restore, Manage Subscription.
//

import SwiftUI
import StoreKit

struct AgentPaywallView: View {
    @ObservedObject var store: AgentStoreKitService
    @Environment(\.dismiss) private var dismiss
    var onSubscribed: (() -> Void)?

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Text(String(localized: "agent_paywall_title"))
                        .font(.title2.weight(.semibold))
                    Text(String(localized: "agent_paywall_body"))
                        .font(.body)
                        .foregroundStyle(.secondary)
                }

                Section {
                    if store.isLoading && store.products.isEmpty {
                        ProgressView()
                    }
                    ForEach(store.products, id: \.id) { product in
                        Button {
                            Task {
                                if await store.purchase(product) {
                                    onSubscribed?()
                                    dismiss()
                                }
                            }
                        } label: {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(product.displayName)
                                    .font(.headline)
                                Text(product.description)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                Text(product.displayPrice + " / " + periodLabel(product))
                                    .font(.subheadline.weight(.semibold))
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                    if store.products.isEmpty && !store.isLoading {
                        Text(String(localized: "agent_products_unavailable"))
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }
                } header: {
                    Text(String(localized: "agent_plans_header"))
                } footer: {
                    Text(String(localized: "agent_subscription_legal"))
                        .font(.caption2)
                }

                Section {
                    Button(String(localized: "agent_restore_purchases")) {
                        Task { await store.restore() }
                    }
                    Button(String(localized: "agent_manage_subscription")) {
                        Task { await store.manageSubscriptions() }
                    }
                    if store.isSubscribed {
                        LabeledContent(
                            String(localized: "agent_credits"),
                            value: "\(store.creditsRemaining) / \(store.creditsPerPeriod)"
                        )
                    }
                }

                if let err = store.lastError, !err.isEmpty {
                    Section {
                        Text(err).font(.footnote).foregroundStyle(.red)
                    }
                }
            }
            .navigationTitle(String(localized: "upgrade_to_agent"))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(String(localized: "done")) { dismiss() }
                }
            }
            .task {
                await store.loadProducts()
                await store.refreshEntitlements()
            }
        }
    }

    private func periodLabel(_ product: Product) -> String {
        if let sub = product.subscription {
            switch sub.subscriptionPeriod.unit {
            case .month: return String(localized: "agent_period_month")
            case .year: return String(localized: "agent_period_year")
            case .week: return "week"
            case .day: return "day"
            @unknown default: return "period"
            }
        }
        return String(localized: "agent_period_month")
    }
}
