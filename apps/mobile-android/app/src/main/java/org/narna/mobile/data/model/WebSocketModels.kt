package org.narna.mobile.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement

@Serializable
sealed class WebSocketEvent {
    abstract val type: String
    abstract val timestamp: String
}

@Serializable
@SerialName("connected")
data class ConnectedEvent(
    override val type: String = "connected",
    @SerialName("bot_id") val botId: String,
    override val timestamp: String
) : WebSocketEvent()

@Serializable
@SerialName("status")
data class StatusEvent(
    override val type: String = "status",
    @SerialName("bot_id") val botId: String,
    val status: BotStatus,
    override val timestamp: String
) : WebSocketEvent()

@Serializable
@SerialName("message")
data class MessageEvent(
    override val type: String = "message",
    @SerialName("bot_id") val botId: String,
    @SerialName("message_id") val messageId: String,
    val role: MessageRole,
    val content: String,
    override val timestamp: String
) : WebSocketEvent()

@Serializable
@SerialName("approval_required")
data class ApprovalRequiredEvent(
    override val type: String = "approval_required",
    @SerialName("approval_id") val approvalId: String,
    @SerialName("bot_id") val botId: String,
    @SerialName("action_type") val actionType: ApprovalActionType,
    val description: String,
    val details: JsonElement,
    override val timestamp: String
) : WebSocketEvent()

@Serializable
@SerialName("tool_execution")
data class ToolExecutionEvent(
    override val type: String = "tool_execution",
    @SerialName("bot_id") val botId: String,
    @SerialName("tool_name") val toolName: String,
    val status: String,
    val details: JsonElement,
    override val timestamp: String
) : WebSocketEvent()

@Serializable
@SerialName("error")
data class ErrorEvent(
    override val type: String = "error",
    @SerialName("bot_id") val botId: String,
    val error: String,
    val details: JsonElement,
    override val timestamp: String
) : WebSocketEvent()
