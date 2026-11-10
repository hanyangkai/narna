package org.narna.mobile.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement

@Serializable
data class ApprovalInfo(
    @SerialName("approval_id") val approvalId: String,
    @SerialName("bot_id") val botId: String,
    @SerialName("action_type") val actionType: ApprovalActionType,
    val description: String,
    val details: JsonElement,
    @SerialName("created_at") val createdAt: String
)

@Serializable
enum class ApprovalActionType {
    @SerialName("shell_command")
    SHELL_COMMAND,
    
    @SerialName("file_edit")
    FILE_EDIT,
    
    @SerialName("web_action")
    WEB_ACTION
}

@Serializable
data class ShellCommandDetails(
    val command: String,
    @SerialName("working_dir") val workingDir: String
)

@Serializable
data class FileEditDetails(
    @SerialName("file_path") val filePath: String,
    @SerialName("old_content") val oldContent: String,
    @SerialName("new_content") val newContent: String
)

@Serializable
data class ApprovalDecisionResponse(
    @SerialName("approval_id") val approvalId: String,
    val decision: String
)
