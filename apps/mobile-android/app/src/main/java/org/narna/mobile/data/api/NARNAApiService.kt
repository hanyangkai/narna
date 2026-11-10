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
    private val baseUrl: String
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
            url(baseUrl)
            contentType(ContentType.Application.Json)
        }
    }

    // ──────────────────────────────────────────────────────────────
    // Health Check
    // ──────────────────────────────────────────────────────────────

    suspend fun healthCheck(): Result<Map<String, Any>> = runCatching {
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

    fun close() {
        client.close()
    }
}
