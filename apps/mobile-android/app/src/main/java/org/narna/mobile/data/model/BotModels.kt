package org.narna.mobile.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class BotInfo(
    @SerialName("bot_id") val botId: String,
    val name: String,
    val model: String,
    val status: BotStatus,
    @SerialName("last_message_at") val lastMessageAt: String? = null
)

@Serializable
enum class BotStatus {
    @SerialName("idle")
    IDLE,
    
    @SerialName("working")
    WORKING,
    
    @SerialName("waiting_approval")
    WAITING_APPROVAL
}

@Serializable
data class BotThread(
    @SerialName("bot_id") val botId: String,
    @SerialName("thread_id") val threadId: String,
    val messages: List<Message>
)

@Serializable
data class Message(
    @SerialName("message_id") val messageId: String,
    val role: MessageRole,
    val content: String,
    @SerialName("created_at") val createdAt: String
)

@Serializable
enum class MessageRole {
    @SerialName("user")
    USER,
    
    @SerialName("assistant")
    ASSISTANT,
    
    @SerialName("system")
    SYSTEM
}

@Serializable
data class SendMessageRequest(
    val message: String,
    @SerialName("thread_id") val threadId: String? = null
)

@Serializable
data class SendMessageResponse(
    @SerialName("thread_id") val threadId: String,
    @SerialName("message_id") val messageId: String,
    val status: String
)
