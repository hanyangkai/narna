package org.narna.mobile.ui.settings

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import org.narna.mobile.BuildConfig
import org.narna.mobile.data.model.ConnectedApp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    onUnpaired: () -> Unit,
    showBack: Boolean = false,
    onNavigateBack: (() -> Unit)? = null,
    viewModel: SettingsViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val snackbarHostState = remember { SnackbarHostState() }

    var openAIKey by remember(uiState.openAIKey) { mutableStateOf(uiState.openAIKey.orEmpty()) }
    var anthropicKey by remember(uiState.anthropicKey) { mutableStateOf(uiState.anthropicKey.orEmpty()) }
    var voiceKey by remember(uiState.openAIVoiceKey) { mutableStateOf(uiState.openAIVoiceKey.orEmpty()) }
    var remoteHost by remember(uiState.remoteHost) { mutableStateOf(uiState.remoteHost) }
    var remoteBaseUrl by remember(uiState.remoteBaseUrl) { mutableStateOf(uiState.remoteBaseUrl) }

    LaunchedEffect(uiState.message, uiState.error) {
        (uiState.message ?: uiState.error)?.let {
            snackbarHostState.showSnackbar(it)
            viewModel.clearMessage()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Settings") },
                navigationIcon = {
                    if (showBack && onNavigateBack != null) {
                        TextButton(onClick = onNavigateBack) { Text("Back") }
                    }
                }
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(24.dp)
        ) {
            SettingsSection(title = "Agent") {
                SettingsInfoItem(
                    label = "Connected to",
                    value = uiState.agentName ?: "Unknown"
                )
            }

            Divider()

            SettingsSection(title = "Remote Access") {
                Text(
                    text = "Choose how the phone reaches your desktop agent.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(8.dp))
                Column(modifier = Modifier.selectableGroup()) {
                    RemoteModeOption(
                        label = "Local",
                        selected = uiState.remoteMode == "local",
                        onClick = {
                            viewModel.updateRemoteDraft(mode = "local")
                        }
                    )
                    RemoteModeOption(
                        label = "Tailscale hostname",
                        selected = uiState.remoteMode == "tailscale",
                        onClick = {
                            viewModel.updateRemoteDraft(mode = "tailscale")
                        }
                    )
                    RemoteModeOption(
                        label = "Custom HTTPS base URL",
                        selected = uiState.remoteMode == "custom",
                        onClick = {
                            viewModel.updateRemoteDraft(mode = "custom")
                        }
                    )
                }

                if (uiState.remoteMode == "tailscale") {
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = remoteHost,
                        onValueChange = {
                            remoteHost = it
                            viewModel.updateRemoteDraft(host = it)
                        },
                        label = { Text("Tailscale hostname") },
                        placeholder = { Text("narna-desktop.tailnet.ts.net") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true
                    )
                }

                if (uiState.remoteMode == "custom" || uiState.remoteMode == "tailscale") {
                    Spacer(modifier = Modifier.height(8.dp))
                    OutlinedTextField(
                        value = remoteBaseUrl,
                        onValueChange = {
                            remoteBaseUrl = it
                            viewModel.updateRemoteDraft(baseUrl = it)
                        },
                        label = { Text("Base URL") },
                        placeholder = { Text("https://…") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true
                    )
                }

                uiState.remoteHint?.let {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = it,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }

                Spacer(modifier = Modifier.height(12.dp))
                Button(
                    onClick = { viewModel.saveRemoteAccess() },
                    enabled = !uiState.isSavingRemote,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    if (uiState.isSavingRemote) {
                        CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                    } else {
                        Text("Save remote access")
                    }
                }
            }

            Divider()

            SettingsSection(title = "Connected Apps") {
                if (uiState.isLoadingApps && uiState.connectedApps.isEmpty()) {
                    LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                } else {
                    uiState.connectedApps.forEach { app ->
                        ConnectedAppRow(
                            app = app,
                            isActing = uiState.actingApp == app.app,
                            onToggle = { viewModel.toggleConnectedApp(app) }
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                    }
                }
            }

            Divider()

            SettingsSection(title = "API Keys") {
                OutlinedTextField(
                    value = openAIKey,
                    onValueChange = { openAIKey = it },
                    label = { Text("OpenAI API Key") },
                    placeholder = { Text("sk-…") },
                    visualTransformation = PasswordVisualTransformation(),
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                Spacer(modifier = Modifier.height(12.dp))
                Button(
                    onClick = { viewModel.saveOpenAIKey(openAIKey) },
                    enabled = openAIKey.isNotBlank(),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Save OpenAI Key")
                }

                Spacer(modifier = Modifier.height(16.dp))

                OutlinedTextField(
                    value = anthropicKey,
                    onValueChange = { anthropicKey = it },
                    label = { Text("Anthropic API Key") },
                    placeholder = { Text("sk-ant-…") },
                    visualTransformation = PasswordVisualTransformation(),
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                Spacer(modifier = Modifier.height(12.dp))
                Button(
                    onClick = { viewModel.saveAnthropicKey(anthropicKey) },
                    enabled = anthropicKey.isNotBlank(),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Save Anthropic Key")
                }

                Spacer(modifier = Modifier.height(16.dp))

                OutlinedTextField(
                    value = voiceKey,
                    onValueChange = { voiceKey = it },
                    label = { Text("OpenAI Voice Key") },
                    placeholder = { Text("sk-… for Realtime voice") },
                    visualTransformation = PasswordVisualTransformation(),
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                Spacer(modifier = Modifier.height(12.dp))
                Button(
                    onClick = { viewModel.saveOpenAIVoiceKey(voiceKey) },
                    enabled = voiceKey.isNotBlank(),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Save Voice Key")
                }
            }

            Divider()

            SettingsSection(title = "Preferences") {
                SettingsSwitchItem(
                    label = "Dark Theme",
                    checked = uiState.darkTheme,
                    onCheckedChange = { viewModel.setDarkTheme(it) }
                )
                Spacer(modifier = Modifier.height(12.dp))
                SettingsSwitchItem(
                    label = "Push notifications",
                    checked = uiState.notificationsEnabled,
                    onCheckedChange = { viewModel.setNotificationsEnabled(it) }
                )
            }

            Divider()

            SettingsSection(title = "Device") {
                Button(
                    onClick = { viewModel.showUnpairDialog() },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.error
                    ),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Unpair Device")
                }
            }

            Text(
                text = "Version ${BuildConfig.VERSION_NAME}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.align(Alignment.CenterHorizontally)
            )
        }
    }

    if (uiState.showUnpairDialog) {
        AlertDialog(
            onDismissRequest = { viewModel.hideUnpairDialog() },
            title = { Text("Unpair Device") },
            text = { Text("Are you sure you want to unpair this device? You'll need to pair again to use the app.") },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.unpairDevice()
                        viewModel.hideUnpairDialog()
                        onUnpaired()
                    },
                    colors = ButtonDefaults.textButtonColors(
                        contentColor = MaterialTheme.colorScheme.error
                    )
                ) {
                    Text("Unpair")
                }
            },
            dismissButton = {
                TextButton(onClick = { viewModel.hideUnpairDialog() }) {
                    Text("Cancel")
                }
            }
        )
    }
}

@Composable
private fun RemoteModeOption(
    label: String,
    selected: Boolean,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .selectable(
                selected = selected,
                onClick = onClick,
                role = Role.RadioButton
            )
            .padding(vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        RadioButton(selected = selected, onClick = null)
        Spacer(modifier = Modifier.width(8.dp))
        Text(label, style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
private fun ConnectedAppRow(
    app: ConnectedApp,
    isActing: Boolean,
    onToggle: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.45f)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 14.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(app.displayName, style = MaterialTheme.typography.titleSmall)
                Text(
                    text = if (app.connected) {
                        app.accountLabel ?: "Connected"
                    } else {
                        "Not connected"
                    },
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            if (isActing) {
                CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
            } else {
                TextButton(onClick = onToggle) {
                    Text(if (app.connected) "Disconnect" else "Connect")
                }
            }
        }
    }
}

@Composable
private fun SettingsSection(
    title: String,
    content: @Composable ColumnScope.() -> Unit
) {
    Column {
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.primary
        )
        Spacer(modifier = Modifier.height(12.dp))
        content()
    }
}

@Composable
private fun SettingsInfoItem(
    label: String,
    value: String
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Text(
            text = value,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface
        )
    }
}

@Composable
private fun SettingsSwitchItem(
    label: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium
        )
        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange
        )
    }
}
