package org.narna.mobile.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ── Inbox ──

@Serializable
data class InboxResponse(
    val ok: Boolean = true,
    @SerialName("pending_count") val pendingCount: Int = 0,
    val items: List<InboxItem> = emptyList()
)

@Serializable
data class InboxItem(
    @SerialName("item_id") val itemId: String,
    val kind: String,
    @SerialName("bot_id") val botId: String,
    val title: String,
    val body: String,
    @SerialName("action_type") val actionType: String? = null,
    @SerialName("created_at") val createdAt: String,
    val status: String = "pending"
)

// ── Routines ──

@Serializable
data class RoutinesResponse(
    val ok: Boolean = true,
    val routines: List<RoutineInfo> = emptyList()
)

@Serializable
data class RoutineCreateRequest(
    val name: String,
    val cron: String = "0 9 * * *",
    @SerialName("bot_id") val botId: String = "bot_1",
    val prompt: String = "Run morning digest",
    val enabled: Boolean = true
)

@Serializable
data class RoutineInfo(
    @SerialName("routine_id") val routineId: String,
    val name: String,
    val cron: String,
    @SerialName("bot_id") val botId: String,
    val prompt: String,
    val enabled: Boolean,
    @SerialName("last_run_at") val lastRunAt: String? = null,
    @SerialName("created_at") val createdAt: String
)

@Serializable
data class RoutineDeleteResponse(
    val ok: Boolean = true,
    val deleted: String? = null
)

// ── Voice ──

@Serializable
data class VoiceStartRequest(
    @SerialName("bot_id") val botId: String = "bot_1",
    @SerialName("openai_api_key") val openaiApiKey: String? = null
)

@Serializable
data class VoiceSession(
    @SerialName("session_id") val sessionId: String,
    @SerialName("bot_id") val botId: String,
    val status: String,
    @SerialName("started_at") val startedAt: String,
    val note: String
)

@Serializable
data class VoiceStopResponse(
    val ok: Boolean = true,
    @SerialName("session_id") val sessionId: String? = null,
    val status: String? = null
)

// ── Remote access ──

@Serializable
data class RemoteStatusResponse(
    val ok: Boolean = true,
    val remote: RemoteConfig
)

@Serializable
data class RemoteConfig(
    val mode: String = "local",
    val host: String? = null,
    @SerialName("base_url") val baseUrl: String? = null,
    @SerialName("updated_at") val updatedAt: String? = null,
    @SerialName("tailscale_hint") val tailscaleHint: String? = null
)

@Serializable
data class RemoteConfigUpdate(
    val mode: String = "local",
    val host: String? = null,
    @SerialName("base_url") val baseUrl: String? = null
)

// ── Connected apps ──

@Serializable
data class ConnectedAppsResponse(
    val ok: Boolean = true,
    val apps: List<ConnectedApp> = emptyList()
)

@Serializable
data class ConnectedApp(
    val app: String,
    @SerialName("display_name") val displayName: String,
    val connected: Boolean = false,
    @SerialName("account_label") val accountLabel: String? = null
)

@Serializable
data class ConnectedAppAction(
    @SerialName("account_label") val accountLabel: String? = null
)

@Serializable
data class ConnectedAppMutationResponse(
    val ok: Boolean = true,
    val app: String? = null,
    val connected: Boolean? = null,
    @SerialName("account_label") val accountLabel: String? = null
)

// ── Push ──

@Serializable
data class PushRegisterRequest(
    val platform: String = "android",
    @SerialName("device_token") val deviceToken: String,
    @SerialName("device_name") val deviceName: String? = null
)

@Serializable
data class PushRegisterResponse(
    val ok: Boolean = true,
    val registered: Boolean = false,
    val note: String? = null
)

// ── Parity feature flags ──

@Serializable
data class ParityStatusResponse(
    val ok: Boolean = true,
    val version: String? = null,
    val features: Map<String, Boolean> = emptyMap()
)
