package org.narna.mobile.data.api

import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.plugins.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.plugins.logging.*
import io.ktor.client.plugins.websocket.*
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.serialization.json.Json
import org.narna.mobile.data.model.*
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class NARNAApiService @Inject constructor(
    private val serverConfig: ServerConfig
) {
    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
    }

    private val client = HttpClient {
        install(ContentNegotiation) {
            json(json)
        }

        install(Logging) {
            logger = Logger.DEFAULT
            level = LogLevel.INFO
        }

        install(WebSockets) {
            pingInterval = 30_000
        }

        install(HttpTimeout) {
            requestTimeoutMillis = 30_000
            connectTimeoutMillis = 10_000
            socketTimeoutMillis = 30_000
        }

        defaultRequest {
            url(serverConfig.currentBaseUrl())
            contentType(ContentType.Application.Json)
        }
    }

    // ──────────────────────────────────────────────────────────────
    // Health Check
    // ──────────────────────────────────────────────────────────────

    suspend fun healthCheck(): Result<Map<String, String>> = runCatching {
        client.get("/v1/mobile/health").body()
    }

    // ──────────────────────────────────────────────────────────────
    // Pairing
    // ──────────────────────────────────────────────────────────────

    suspend fun startPairing(
        apiKey: String,
        deviceName: String?
    ): Result<PairingStartResponse> = runCatching {
        client.post("/v1/mobile/pairing/start") {
            header("Authorization", "Bearer $apiKey")
            setBody(PairingStartRequest(deviceName = deviceName))
        }.body()
    }

    suspend fun verifyPairing(code: String): Result<PairingVerifyResponse> = runCatching {
        client.post("/v1/mobile/pairing/verify") {
            setBody(PairingVerifyRequest(pairingCode = code))
        }.body()
    }

    suspend fun revokePairing(
        apiKey: String,
        mobileToken: String
    ): Result<PairingRevokeResponse> = runCatching {
        client.delete("/v1/mobile/pairing/revoke") {
            header("Authorization", "Bearer $apiKey")
            setBody(PairingRevokeRequest(mobileToken = mobileToken))
        }.body()
    }

    // ──────────────────────────────────────────────────────────────
    // Bots
    // ──────────────────────────────────────────────────────────────

    suspend fun listBots(mobileToken: String): Result<List<BotInfo>> = runCatching {
        client.get("/v1/mobile/bots") {
            parameter("mobile_token", mobileToken)
        }.body()
    }

    suspend fun getBotThread(
        mobileToken: String,
        botId: String,
        limit: Int = 50
    ): Result<BotThread> = runCatching {
        client.get("/v1/mobile/bots/$botId/thread") {
            parameter("mobile_token", mobileToken)
            parameter("limit", limit)
        }.body()
    }

    suspend fun sendMessage(
        mobileToken: String,
        botId: String,
        message: String,
        threadId: String? = null
    ): Result<SendMessageResponse> = runCatching {
        client.post("/v1/mobile/bots/$botId/message") {
            parameter("mobile_token", mobileToken)
            setBody(SendMessageRequest(message = message, threadId = threadId))
        }.body()
    }

    // ──────────────────────────────────────────────────────────────
    // Approvals
    // ──────────────────────────────────────────────────────────────

    suspend fun listApprovals(mobileToken: String): Result<List<ApprovalInfo>> = runCatching {
        client.get("/v1/mobile/approvals") {
            parameter("mobile_token", mobileToken)
        }.body()
    }

    suspend fun allowApproval(
        mobileToken: String,
        approvalId: String
    ): Result<ApprovalDecisionResponse> = runCatching {
        client.post("/v1/mobile/approvals/$approvalId/allow") {
            parameter("mobile_token", mobileToken)
        }.body()
    }

    suspend fun denyApproval(
        mobileToken: String,
        approvalId: String
    ): Result<ApprovalDecisionResponse> = runCatching {
        client.post("/v1/mobile/approvals/$approvalId/deny") {
            parameter("mobile_token", mobileToken)
        }.body()
    }

    // ──────────────────────────────────────────────────────────────
    // Inbox
    // ──────────────────────────────────────────────────────────────

    suspend fun getInbox(mobileToken: String): Result<InboxResponse> = runCatching {
        client.get("/v1/mobile/inbox") {
            parameter("mobile_token", mobileToken)
        }.body()
    }

    // ──────────────────────────────────────────────────────────────
    // Routines
    // ──────────────────────────────────────────────────────────────

    suspend fun listRoutines(mobileToken: String): Result<RoutinesResponse> = runCatching {
        client.get("/v1/mobile/routines") {
            parameter("mobile_token", mobileToken)
        }.body()
    }

    suspend fun createRoutine(
        mobileToken: String,
        request: RoutineCreateRequest
    ): Result<RoutineInfo> = runCatching {
        client.post("/v1/mobile/routines") {
            parameter("mobile_token", mobileToken)
            setBody(request)
        }.body()
    }

    suspend fun toggleRoutine(
        mobileToken: String,
        routineId: String
    ): Result<RoutineInfo> = runCatching {
        client.post("/v1/mobile/routines/$routineId/toggle") {
            parameter("mobile_token", mobileToken)
        }.body()
    }

    suspend fun deleteRoutine(
        mobileToken: String,
        routineId: String
    ): Result<RoutineDeleteResponse> = runCatching {
        client.delete("/v1/mobile/routines/$routineId") {
            parameter("mobile_token", mobileToken)
        }.body()
    }

    // ──────────────────────────────────────────────────────────────
    // Voice
    // ──────────────────────────────────────────────────────────────

    suspend fun startVoice(
        mobileToken: String,
        request: VoiceStartRequest
    ): Result<VoiceSession> = runCatching {
        client.post("/v1/mobile/voice/start") {
            parameter("mobile_token", mobileToken)
            setBody(request)
        }.body()
    }

    suspend fun stopVoice(
        mobileToken: String,
        sessionId: String
    ): Result<VoiceStopResponse> = runCatching {
        client.post("/v1/mobile/voice/stop") {
            parameter("mobile_token", mobileToken)
            parameter("session_id", sessionId)
        }.body()
    }

    // ──────────────────────────────────────────────────────────────
    // Remote access
    // ──────────────────────────────────────────────────────────────

    suspend fun getRemoteStatus(mobileToken: String): Result<RemoteStatusResponse> = runCatching {
        client.get("/v1/mobile/remote/status") {
            parameter("mobile_token", mobileToken)
        }.body()
    }

    suspend fun updateRemoteConfig(
        mobileToken: String,
        update: RemoteConfigUpdate
    ): Result<RemoteStatusResponse> = runCatching {
        client.put("/v1/mobile/remote/config") {
            parameter("mobile_token", mobileToken)
            setBody(update)
        }.body()
    }

    // ──────────────────────────────────────────────────────────────
    // Connected apps
    // ──────────────────────────────────────────────────────────────

    suspend fun listConnectedApps(mobileToken: String): Result<ConnectedAppsResponse> = runCatching {
        client.get("/v1/mobile/connected-apps") {
            parameter("mobile_token", mobileToken)
        }.body()
    }

    suspend fun connectApp(
        mobileToken: String,
        app: String,
        accountLabel: String? = null
    ): Result<ConnectedAppMutationResponse> = runCatching {
        client.post("/v1/mobile/connected-apps/$app/connect") {
            parameter("mobile_token", mobileToken)
            setBody(ConnectedAppAction(accountLabel = accountLabel))
        }.body()
    }

    suspend fun disconnectApp(
        mobileToken: String,
        app: String
    ): Result<ConnectedAppMutationResponse> = runCatching {
        client.post("/v1/mobile/connected-apps/$app/disconnect") {
            parameter("mobile_token", mobileToken)
        }.body()
    }

    // ──────────────────────────────────────────────────────────────
    // Push
    // ──────────────────────────────────────────────────────────────

    suspend fun registerPush(
        mobileToken: String,
        request: PushRegisterRequest
    ): Result<PushRegisterResponse> = runCatching {
        client.post("/v1/mobile/push/register") {
            parameter("mobile_token", mobileToken)
            setBody(request)
        }.body()
    }

    // ──────────────────────────────────────────────────────────────
    // Parity
    // ──────────────────────────────────────────────────────────────

    suspend fun getParityStatus(mobileToken: String): Result<ParityStatusResponse> = runCatching {
        client.get("/v1/mobile/parity") {
            parameter("mobile_token", mobileToken)
        }.body()
    }

    // ──────────────────────────────────────────────────────────────
    // Onboarding / AI providers / subscription
    // ──────────────────────────────────────────────────────────────

    suspend fun getOnboardingStatus(mobileToken: String? = null): Result<OnboardingStatusResponse> =
        runCatching {
            client.get("/v1/mobile/onboarding/status") {
                if (!mobileToken.isNullOrBlank()) {
                    parameter("mobile_token", mobileToken)
                }
            }.body()
        }

    suspend fun listAiProviders(mobileToken: String): Result<AiProvidersResponse> = runCatching {
        client.get("/v1/mobile/ai/providers") {
            parameter("mobile_token", mobileToken)
        }.body()
    }

    suspend fun configureAiProvider(
        mobileToken: String,
        providerId: String,
        request: AiProviderConfigureRequest
    ): Result<AiProviderConfigureResponse> = runCatching {
        client.post("/v1/mobile/ai/providers/$providerId/configure") {
            parameter("mobile_token", mobileToken)
            setBody(request)
        }.body()
    }

    suspend fun clearAiProvider(
        mobileToken: String,
        providerId: String
    ): Result<AiProviderClearResponse> = runCatching {
        client.delete("/v1/mobile/ai/providers/$providerId") {
            parameter("mobile_token", mobileToken)
        }.body()
    }

    suspend fun getSubscriptionProducts(): Result<SubscriptionProductsResponse> = runCatching {
        client.get("/v1/mobile/subscription/products").body()
    }

    suspend fun verifyStorePurchase(
        mobileToken: String,
        request: StoreVerifyRequest
    ): Result<StoreVerifyResponse> = runCatching {
        client.post("/v1/billing/store/verify") {
            parameter("mobile_token", mobileToken)
            setBody(request)
        }.body()
    }

    fun close() {
        client.close()
    }
}
