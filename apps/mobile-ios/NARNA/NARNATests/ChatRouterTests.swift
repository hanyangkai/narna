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

final class ChatRouterTests: XCTestCase {
    func testAutoPicksAppleWhenAvailable() {
        let (kind, note) = ChatRouter.resolve(
            preference: .auto,
            appleChecker: MockAppleAvailability(.available),
            hasBYOKey: false
        )
        XCTAssertEqual(kind, .onDevice)
        XCTAssertEqual(note, .available)
    }

    func testAutoFallsBackToFreePool() {
        let (kind, note) = ChatRouter.resolve(
            preference: .auto,
            appleChecker: MockAppleAvailability(.deviceNotEligible),
            hasBYOKey: false
        )
        XCTAssertEqual(kind, .freePool)
        XCTAssertEqual(note, .deviceNotEligible)
    }

    func testIntelligenceOffSuggestsSettings() {
        XCTAssertTrue(AppleModelAvailabilityReason.appleIntelligenceNotEnabled.suggestsOpenSettings)
    }

    func testDisplayNameIsNanaAI() {
        XCTAssertEqual(PinnedBot.name, "Nana AI")
        XCTAssertTrue(NanaSystemPrompt.value.contains("Nana AI"))
    }

    func testDailyLimitErrorLocalizedKey() {
        let err = ChatProviderError.dailyLimitReached
        XCTAssertNotNil(err.errorDescription)
    }
}

final class FreePool429Tests: XCTestCase {
    func testDailyLimitErrorEquatable() {
        XCTAssertEqual(ChatProviderError.dailyLimitReached, ChatProviderError.dailyLimitReached)
    }
}
