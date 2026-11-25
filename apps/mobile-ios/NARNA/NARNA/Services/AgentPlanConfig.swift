//
//  AgentPlanConfig.swift
//  NARNA
//
//  StoreKit product IDs, credit caps, and paywall gating.
//  Prices are set in App Store Connect (proposed: 99.000đ and 249.000đ / month)
//  and must not be hardcoded as the charged amount.
//  Caps are chosen so API cost per subscriber stays below plan revenue
//  after Apple's 15% Small Business commission.
//

import Foundation

enum AgentPlan: String, CaseIterable, Identifiable, Equatable {
    case basic = "nana.agent.basic.monthly"
    case pro = "nana.agent.pro.monthly"

    var id: String { rawValue }
    var productID: String { rawValue }

    var displayName: String {
        switch self {
        case .basic: return "Agent Basic"
        case .pro: return "Agent Pro"
        }
    }

    /// Suggested list price for review notes / local StoreKit config only.
    /// The paywall always shows the StoreKit-localized price.
    var proposedPriceVND: Int {
        switch self {
        case .basic: return 99_000
        case .pro: return 249_000
        }
    }

    var periodLabel: String { "month" }

    /// Monthly credit cap. One Agent request (multi-step / file / web / strong model) costs >= 1 credit.
    var monthlyCredits: Int {
        AgentPlanConfig.credits(for: self)
    }
}

enum AgentPlanConfig {
    static let subscriptionGroupID = "Nana Agent"
    static let productIDs: [String] = AgentPlan.allCases.map(\.productID)

    /// Conservative caps so token spend stays under net revenue (price * 0.85).
    static func credits(for plan: AgentPlan) -> Int {
        switch plan {
        case .basic: return 200
        case .pro: return 800
        }
    }

    static func plan(forProductID id: String) -> AgentPlan? {
        AgentPlan(rawValue: id)
    }
}

enum PaywallGating {
    enum Decision: Equatable {
        case allowed(remaining: Int)
        case needsSubscription
        case creditsExhausted
    }

    /// Whether an Agent request may be sent.
    static func evaluate(isSubscribed: Bool, plan: AgentPlan?, creditsRemaining: Int) -> Decision {
        guard isSubscribed, plan != nil else { return .needsSubscription }
        guard creditsRemaining > 0 else { return .creditsExhausted }
        return .allowed(remaining: creditsRemaining)
    }

    static func canUseAgent(isSubscribed: Bool, creditsRemaining: Int) -> Bool {
        switch evaluate(isSubscribed: isSubscribed, plan: isSubscribed ? .basic : nil, creditsRemaining: creditsRemaining) {
        case .allowed: return true
        default: return false
        }
    }

    /// Net revenue after Apple's 15% fee, in VND, for a monthly plan.
    static func netRevenueVND(for plan: AgentPlan) -> Int {
        Int((Double(plan.proposedPriceVND) * 0.85).rounded(.down))
    }
}
