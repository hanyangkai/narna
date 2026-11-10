package org.narna.mobile.ui.approvals

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.narna.mobile.data.model.ApprovalActionType
import org.narna.mobile.data.model.ApprovalInfo

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ApprovalBottomSheet(
    approval: ApprovalInfo,
    onAllow: () -> Unit,
    onDeny: () -> Unit,
    onDismiss: () -> Unit
) {
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = rememberModalBottomSheetState()
    ) {
        ApprovalContent(
            approval = approval,
            onAllow = onAllow,
            onDeny = onDeny
        )
    }
}

@Composable
private fun ApprovalContent(
    approval: ApprovalInfo,
    onAllow: () -> Unit,
    onDeny: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(24.dp)
    ) {
        Text(
            text = "Approval Required",
            style = MaterialTheme.typography.headlineSmall,
            fontWeight = FontWeight.Bold
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Action Type Badge
        Surface(
            shape = MaterialTheme.shapes.small,
            color = MaterialTheme.colorScheme.primaryContainer
        ) {
            Text(
                text = getActionTypeLabel(approval.actionType),
                modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onPrimaryContainer
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Description
        Text(
            text = approval.description,
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurface
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Details Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surfaceVariant
            )
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp)
            ) {
                Text(
                    text = "Details",
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )

                Spacer(modifier = Modifier.height(8.dp))

                ApprovalDetails(
                    actionType = approval.actionType,
                    details = approval.details
                )
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Action Buttons
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            OutlinedButton(
                onClick = onDeny,
                modifier = Modifier.weight(1f)
            ) {
                Icon(
                    Icons.Default.Close,
                    contentDescription = null,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("Deny")
            }

            Button(
                onClick = onAllow,
                modifier = Modifier.weight(1f)
            ) {
                Icon(
                    Icons.Default.Check,
                    contentDescription = null,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("Allow")
            }
        }

        Spacer(modifier = Modifier.height(16.dp))
    }
}

@Composable
private fun ApprovalDetails(
    actionType: ApprovalActionType,
    details: kotlinx.serialization.json.JsonElement
) {
    when (actionType) {
        ApprovalActionType.SHELL_COMMAND -> {
            ShellCommandDetails(details)
        }
        ApprovalActionType.FILE_EDIT -> {
            FileEditDetails(details)
        }
        ApprovalActionType.WEB_ACTION -> {
            WebActionDetails(details)
        }
    }
}

@Composable
private fun ShellCommandDetails(details: kotlinx.serialization.json.JsonElement) {
    val jsonObject = details.jsonObject
    val command = jsonObject["command"]?.jsonPrimitive?.content ?: ""
    val workingDir = jsonObject["working_dir"]?.jsonPrimitive?.content ?: ""

    DetailRow(label = "Command", value = command)
    if (workingDir.isNotBlank()) {
        DetailRow(label = "Working Directory", value = workingDir)
    }
}

@Composable
private fun FileEditDetails(details: kotlinx.serialization.json.JsonElement) {
    val jsonObject = details.jsonObject
    val filePath = jsonObject["file_path"]?.jsonPrimitive?.content ?: ""
    val oldContent = jsonObject["old_content"]?.jsonPrimitive?.content ?: ""
    val newContent = jsonObject["new_content"]?.jsonPrimitive?.content ?: ""

    DetailRow(label = "File", value = filePath)
    
    if (oldContent.isNotBlank() || newContent.isNotBlank()) {
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "Changes Preview:",
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 4.dp),
            shape = MaterialTheme.shapes.small,
            color = MaterialTheme.colorScheme.surface
        ) {
            Text(
                text = "- ${oldContent.take(100)}${if (oldContent.length > 100) "..." else ""}\n+ ${newContent.take(100)}${if (newContent.length > 100) "..." else ""}",
                modifier = Modifier.padding(8.dp),
                style = MaterialTheme.typography.bodySmall,
                fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace
            )
        }
    }
}

@Composable
private fun WebActionDetails(details: kotlinx.serialization.json.JsonElement) {
    val jsonObject = details.jsonObject
    jsonObject.entries.forEach { (key, value) ->
        DetailRow(
            label = key.replace("_", " ").capitalize(),
            value = value.jsonPrimitive.content
        )
    }
}

@Composable
private fun DetailRow(label: String, value: String) {
    Column(modifier = Modifier.fillMaxWidth()) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface,
            modifier = Modifier.padding(top = 2.dp)
        )
        Spacer(modifier = Modifier.height(8.dp))
    }
}

private fun getActionTypeLabel(type: ApprovalActionType): String {
    return when (type) {
        ApprovalActionType.SHELL_COMMAND -> "Shell Command"
        ApprovalActionType.FILE_EDIT -> "File Edit"
        ApprovalActionType.WEB_ACTION -> "Web Action"
    }
}

private fun String.capitalize(): String {
    return this.replaceFirstChar { if (it.isLowerCase()) it.titlecase() else it.toString() }
}
