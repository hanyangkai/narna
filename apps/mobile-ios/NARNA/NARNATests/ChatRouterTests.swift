//
//  ChatRouterTests.swift
//  NARNATests
//

import XCTest
@testable import NARNA

final class MockAppleAvailability: AppleAvailabilityChecking, @unchecked Sendable {
    var reason: AppleModelAvailabilityReason
    init(_ reason: AppleModelAvailabilityReason) { self.reason = reason }
    func availability() -> AppleModelAvailabilityReason { reason }
}

final class ProviderRouterTests: XCTestCase {
    func testAutoPicksAppleWhenAvailable() {
        let (kind, note) = ProviderRouter.resolve(
            preference: .auto,
            appleChecker: MockAppleAvailability(.available),
            hasBYOKey: false
        )
        XCTAssertEqual(kind, .onDevice)
        XCTAssertEqual(note, .available)
    }

    func testAutoFallsBackToFreePool() {
        let (kind, note) = ProviderRouter.resolve(
            preference: .auto,
            appleChecker: MockAppleAvailability(.deviceNotEligible),
            hasBYOKey: false
        )
        XCTAssertEqual(kind, .freePool)
        XCTAssertEqual(note, .deviceNotEligible)
    }

    func testExplicitAgentPreference() {
        let (kind, _) = ProviderRouter.resolve(
            preference: .agent,
            appleChecker: MockAppleAvailability(.unsupportedOS),
            hasBYOKey: false
        )
        XCTAssertEqual(kind, .agent)
    }

    func testFriendlyModelLabels() {
        XCTAssertEqual(ProviderRouter.friendlyModelLabel("workers-ai:gpt-oss"), "GPT-OSS")
        XCTAssertEqual(ProviderRouter.friendlyModelLabel("gemini:flash"), "Gemini Flash")
        XCTAssertEqual(ProviderRouter.friendlyModelLabel("Apple on-device"), "Apple on-device")
        XCTAssertEqual(ProviderRouter.friendlyModelLabel("zai:glm-4.7-flash"), "GLM Flash")
    }

    func testIntelligenceOffSuggestsSettings() {
        XCTAssertTrue(AppleModelAvailabilityReason.appleIntelligenceNotEnabled.suggestsOpenSettings)
    }

    func testDisplayNameIsNanaAI() {
        XCTAssertEqual(PinnedBot.name, "Nana AI")
        XCTAssertTrue(NanaSystemPrompt.value.contains("Nana AI"))
        XCTAssertFalse(PinnedBot.name.lowercased().contains("nana bot"))
    }
}

final class DailyLimitAndPaywallTests: XCTestCase {
    func testDailyLimitErrorEquatable() {
        XCTAssertEqual(ChatProviderError.dailyLimitReached, ChatProviderError.dailyLimitReached)
    }

    func testAgentPaywallError() {
        let err = ChatProviderError.agentPaywallRequired
        XCTAssertNotNil(err.errorDescription)
    }

    func testAgentProductIds() {
        XCTAssertEqual(AgentStoreKitService.productIds, [
            "nana.agent.basic.monthly",
            "nana.agent.pro.monthly",
        ])
    }

    func testChatRouterAlias() {
        let (kind, _) = ChatRouter.resolve(
            preference: .freePool,
            appleChecker: MockAppleAvailability(.available),
            hasBYOKey: false
        )
        XCTAssertEqual(kind, .freePool)
    }
}
