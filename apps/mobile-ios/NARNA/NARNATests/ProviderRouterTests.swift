import XCTest
@testable import NARNA

final class ProviderRouterTests: XCTestCase {

    private func input(
        onDevice: Bool = false,
        freePool: Bool = true,
        useBYOK: Bool = false,
        hasBYOK: Bool = false,
        agent: Bool = false,
        subscribed: Bool = false,
        credits: Int = 0
    ) -> ChatProviderRouteInput {
        ChatProviderRouteInput(
            onDeviceAvailable: onDevice,
            freePoolConfigured: freePool,
            useOwnAPIKey: useBYOK,
            hasBYOK: hasBYOK,
            agentModeEnabled: agent,
            isSubscribed: subscribed,
            agentCreditsRemaining: credits
        )
    }

    func testOnDeviceWinsOverFreePool() {
        XCTAssertEqual(ChatProviderRouter.resolve(input(onDevice: true, freePool: true)), .onDevice)
    }

    func testFreePoolWhenOnDeviceUnavailable() {
        XCTAssertEqual(ChatProviderRouter.resolve(input(onDevice: false, freePool: true)), .freePool)
    }

    func testBYOKOnlyWhenEnabledAndKeyPresent() {
        XCTAssertEqual(ChatProviderRouter.resolve(input(onDevice: true, useBYOK: true, hasBYOK: true)), .byok)
        XCTAssertEqual(ChatProviderRouter.resolve(input(onDevice: true, useBYOK: true, hasBYOK: false)), .onDevice)
        XCTAssertEqual(ChatProviderRouter.resolve(input(onDevice: false, freePool: true, useBYOK: false, hasBYOK: true)), .freePool)
    }

    func testAgentRequiresSubscriptionAndCredits() {
        XCTAssertEqual(ChatProviderRouter.resolve(input(agent: true, subscribed: false, credits: 10)), .paywall)
        XCTAssertEqual(ChatProviderRouter.resolve(input(agent: true, subscribed: true, credits: 0)), .paywall)
        XCTAssertEqual(ChatProviderRouter.resolve(input(agent: true, subscribed: true, credits: 5)), .agent)
    }

    func testUnavailableWhenNothingConfigured() {
        XCTAssertEqual(ChatProviderRouter.resolve(input(onDevice: false, freePool: false)), .unavailable)
    }

    func testDefaultGeminiModelIsConfigurableFlash38() {
        XCTAssertEqual(FreePoolModelCatalog.defaultGeminiModelID, "gemini-3.8-flash")
        XCTAssertTrue(FreePoolModelCatalog.googleEntries.contains(where: { $0.id == "gemini-3.8-flash" }))
        XCTAssertFalse(FreePoolModelCatalog.routePriority.contains(where: { $0.id == "gemini-2.5-flash" }))
    }

    func testDisplayNames() {
        XCTAssertEqual(FreePoolModelCatalog.displayName(forModelId: "gemini-3.8-flash"), "Gemini Flash")
        XCTAssertEqual(FreePoolModelCatalog.displayName(forModelId: "openai/gpt-oss-120b"), "GPT-OSS")
        XCTAssertEqual(FreePoolModelCatalog.displayName(forModelId: "@cf/meta/llama-3.1-8b-instruct-fp8-fast"), "Llama")
        XCTAssertEqual(FreePoolModelCatalog.displayName(forModelId: "@cf/qwen/qwen3.8-27b"), "Qwen")
        XCTAssertEqual(FreePoolModelCatalog.displayName(forModelId: "google/gemma-4-31b-it:free"), "Gemma")
        XCTAssertEqual(FreePoolModelCatalog.displayName(forModelId: "glm-4.7-flash"), "GLM")
        XCTAssertEqual(ChatProviderRouter.displayName(for: .onDevice, modelDisplayName: nil), "On-device")
        XCTAssertEqual(ChatProviderRouter.displayName(for: .freePool, modelDisplayName: "GPT-OSS"), "GPT-OSS")
    }

    func testRetryableStatusIncludes429And503() {
        XCTAssertTrue(FreePoolModelCatalog.isRetryableStatus(429))
        XCTAssertTrue(FreePoolModelCatalog.isRetryableStatus(503, message: "high demand"))
        XCTAssertTrue(FreePoolModelCatalog.isRetryableStatus(503, message: "UNAVAILABLE"))
        XCTAssertFalse(FreePoolModelCatalog.isRetryableStatus(400))
        XCTAssertFalse(FreePoolModelCatalog.isRetryableStatus(401))
        XCTAssertFalse(FreePoolModelCatalog.isRetryableStatus(500))
    }

    func testWorkerOrderStartsWithCloudflareGptOssThenOptionalGroq() {
        let ids = FreePoolModelCatalog.routePriority.map(\.id)
        XCTAssertEqual(Array(ids.prefix(2)), ["@cf/openai/gpt-oss-120b", "@cf/openai/gpt-oss-20b"])
        let providers = FreePoolModelCatalog.routePriority.map(\.provider)
        let firstCF = providers.firstIndex(of: .workersAI)!
        let firstGroq = providers.firstIndex(of: .groq)!
        let firstGoogle = providers.firstIndex(of: .google)!
        let firstOR = providers.firstIndex(of: .openRouter)!
        let firstZ = providers.firstIndex(of: .zai)!
        XCTAssertEqual(firstCF, 0)
        XCTAssertLessThan(firstCF, firstGroq)
        XCTAssertLessThan(firstGroq, firstGoogle)
        // Other Workers AI models (Llama/Gemma/Qwen) come after Google, before OpenRouter.
        let llamaIdx = ids.firstIndex(of: "@cf/meta/llama-3.1-8b-instruct-fp8-fast")!
        XCTAssertLessThan(firstGoogle, llamaIdx)
        XCTAssertLessThan(llamaIdx, firstOR)
        XCTAssertLessThan(firstOR, firstZ)
        XCTAssertEqual(FreePoolModelCatalog.routePriority.last?.id, "glm-4.7-flash")
    }

    func testFallbackSkipsGoogleForEEAUKCH() {
        XCTAssertTrue(FreePoolModelCatalog.shouldSkipGoogle(regionCode: "DE"))
        XCTAssertTrue(FreePoolModelCatalog.shouldSkipGoogle(regionCode: "GB"))
        XCTAssertTrue(FreePoolModelCatalog.shouldSkipGoogle(regionCode: "CH"))
        XCTAssertTrue(FreePoolModelCatalog.shouldSkipGoogle(regionCode: "NO"))
        XCTAssertFalse(FreePoolModelCatalog.shouldSkipGoogle(regionCode: "US"))
        XCTAssertFalse(FreePoolModelCatalog.shouldSkipGoogle(regionCode: "SG"))
        XCTAssertFalse(FreePoolModelCatalog.shouldSkipGoogle(regionCode: nil))

        let afterCF20 = FreePoolModelCatalog.nextAfterRateLimit(currentId: "@cf/openai/gpt-oss-20b", skipGoogle: false)
        XCTAssertEqual(afterCF20?.provider, .groq)
        let afterGroq20 = FreePoolModelCatalog.nextAfterRateLimit(currentId: "openai/gpt-oss-20b", skipGoogle: false)
        XCTAssertEqual(afterGroq20?.id, "gemini-3.8-flash")
        let afterGroq20EEA = FreePoolModelCatalog.nextAfterRateLimit(currentId: "openai/gpt-oss-20b", skipGoogle: true)
        XCTAssertEqual(afterGroq20EEA?.provider, .workersAI)
        XCTAssertEqual(afterGroq20EEA?.id, "@cf/meta/llama-3.1-8b-instruct-fp8-fast")
        XCTAssertFalse(FreePoolModelCatalog.routes(skipGoogle: true).contains(where: { $0.isGoogle }))
        XCTAssertNil(FreePoolModelCatalog.nextAfterRateLimit(currentId: "glm-4.7-flash"))
    }
}
