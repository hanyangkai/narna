import XCTest
@testable import NARNA

final class PaywallGatingTests: XCTestCase {

    func testNeedsSubscriptionWhenNotSubscribed() {
        XCTAssertEqual(PaywallGating.evaluate(isSubscribed: false, plan: nil, creditsRemaining: 10), .needsSubscription)
        XCTAssertFalse(PaywallGating.canUseAgent(isSubscribed: false, creditsRemaining: 10))
    }

    func testCreditsExhausted() {
        XCTAssertEqual(PaywallGating.evaluate(isSubscribed: true, plan: .basic, creditsRemaining: 0), .creditsExhausted)
        XCTAssertFalse(PaywallGating.canUseAgent(isSubscribed: true, creditsRemaining: 0))
    }

    func testAllowedWhenSubscribedWithCredits() {
        XCTAssertEqual(PaywallGating.evaluate(isSubscribed: true, plan: .basic, creditsRemaining: 3), .allowed(remaining: 3))
        XCTAssertTrue(PaywallGating.canUseAgent(isSubscribed: true, creditsRemaining: 3))
    }

    func testProductIdentifiersAndCreditCaps() {
        XCTAssertEqual(AgentPlan.basic.productID, "nana.agent.basic.monthly")
        XCTAssertEqual(AgentPlan.pro.productID, "nana.agent.pro.monthly")
        XCTAssertEqual(AgentPlanConfig.credits(for: .basic), 200)
        XCTAssertEqual(AgentPlanConfig.credits(for: .pro), 800)
        XCTAssertGreaterThan(AgentPlan.pro.monthlyCredits, AgentPlan.basic.monthlyCredits)
    }

    func testNetRevenueAfterAppleFeeIsBelowListPrice() {
        XCTAssertEqual(PaywallGating.netRevenueVND(for: .basic), 84_150)
        XCTAssertEqual(PaywallGating.netRevenueVND(for: .pro), 211_650)
        XCTAssertLessThan(PaywallGating.netRevenueVND(for: .basic), AgentPlan.basic.proposedPriceVND)
        // Caps stay modest relative to net revenue so API spend can remain under it.
        XCTAssertLessThan(AgentPlan.basic.monthlyCredits, PaywallGating.netRevenueVND(for: .basic))
    }
}
