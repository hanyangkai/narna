package org.narna.mobile.ui.settings

import android.app.Activity
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import org.narna.mobile.BuildConfig
import org.narna.mobile.data.model.AiProviderInfo
import org.narna.mobile.data.model.ConnectedApp
import org.narna.mobile.data.model.SubscriptionProduct

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
    val context = LocalContext.current
    val activity = context as? Activity

    var voiceKey by remember(uiState.openAIVoiceKey) { mutableStateOf(uiState.openAIVoiceKey.orEmpty()) }
    var remoteHost by remember(uiState.remoteHost) { mutableStateOf(uiState.remoteHost) }
    var remoteBaseUrl by remember(uiState.remoteBaseUrl) { mutableStateOf(uiState.remoteBaseUrl) }
    var providerDrafts by remember { mutableStateOf<Map<String, String>>(emptyMap()) }

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
                SettingsInfoItem(
                    label = "Plan",
                    value = uiState.plan.replaceFirstChar { it.uppercase() }
                )
                SettingsInfoItem(
                    label = "AI ready",
                    value = if (uiState.aiReady) "Yes" else "No"
                )
            }

            Divider()

            SettingsSection(title = "AI Providers") {
                Text(
                    text = uiState.aiProvidersNote
                        ?: "CLI logins stay on Desktop. API keys here power the cloud agent (BYOK).",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(8.dp))
                if (uiState.isLoadingProviders && uiState.aiProviders.isEmpty()) {
                    LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                } else {
                    uiState.aiProviders.forEach { provider ->
                        AiProviderCard(
                            provider = provider,
                            draftKey = providerDrafts[provider.id].orEmpty(),
                            isBusy = uiState.configuringProviderId == provider.id,
                            onDraftChange = { value ->
                                providerDrafts = providerDrafts + (provider.id to value)
                            },
                            onSave = {
                                viewModel.configureProvider(
                                    provider.id,
                                    providerDrafts[provider.id].orEmpty()
                                )
                            },
                            onClear = { viewModel.clearProvider(provider.id) }
                        )
                        Spacer(modifier = Modifier.height(10.dp))
                    }
                }
            }

            Divider()

            SettingsSection(title = "Subscription") {
                Text(
                    text = "Billing is only through Google Play. Crypto and web USDC/USDT checkout are not available in this app.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(8.dp))
                if (uiState.isLoadingProducts && uiState.subscriptionProducts.isEmpty()) {
                    LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                } else {
                    uiState.subscriptionProducts.forEach { product ->
                        SubscriptionProductCard(
                            product = product,
                            playPrice = uiState.playProductDetails[product.productId]
                                ?.subscriptionOfferDetails
                                ?.firstOrNull()
                                ?.pricingPhases
                                ?.pricingPhaseList
                                ?.firstOrNull()
                                ?.formattedPrice,
                            isPurchasing = uiState.purchasingProductId == product.productId,
                            playReady = uiState.playBillingReady &&
                                uiState.playProductDetails.containsKey(product.productId),
                            onPurchase = {
                                activity?.let { viewModel.purchaseProduct(it, product.productId) }
                            }
                        )
                        Spacer(modifier = Modifier.height(10.dp))
                    }
                }
                if (!uiState.playBillingReady) {
                    Text(
                        text = "Google Play Billing is unavailable on this device/build. Install from Play Store to subscribe.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.error
                    )
                }
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedButton(
                    onClick = {
                        val url = uiState.manageSubscriptionUrl
                            ?: "https://play.google.com/store/account/subscriptions"
                        context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                    },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Manage in Google Play")
                }
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
                        onClick = { viewModel.updateRemoteDraft(mode = "local") }
                    )
                    RemoteModeOption(
                        label = "Tailscale hostname",
                        selected = uiState.remoteMode == "tailscale",
                        onClick = { viewModel.updateRemoteDraft(mode = "tailscale") }
                    )
                    RemoteModeOption(
                        label = "Custom HTTPS base URL",
                        selected = uiState.remoteMode == "custom",
                        onClick = { viewModel.updateRemoteDraft(mode = "custom") }
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

            SettingsSection(title = "Voice key (local)") {
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
private fun AiProviderCard(
    provider: AiProviderInfo,
    draftKey: String,
    isBusy: Boolean,
    onDraftChange: (String) -> Unit,
    onSave: () -> Unit,
    onClear: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.45f)
        )
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(provider.name, style = MaterialTheme.typography.titleSmall)
                    Text(
                        text = if (provider.connected) {
                            provider.maskedKey ?: "Connected"
                        } else {
                            provider.hint ?: "Not connected"
                        },
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        text = "Modes: ${provider.modes.joinToString()}",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                if (isBusy) {
                    CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
                }
            }

            if (provider.modes.contains("api_key")) {
                Spacer(modifier = Modifier.height(10.dp))
                OutlinedTextField(
                    value = draftKey,
                    onValueChange = onDraftChange,
                    label = { Text("${provider.name} API key") },
                    placeholder = { Text(provider.env ?: "API key") },
                    visualTransformation = PasswordVisualTransformation(),
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                Spacer(modifier = Modifier.height(8.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        onClick = onSave,
                        enabled = draftKey.isNotBlank() && !isBusy,
                        modifier = Modifier.weight(1f)
                    ) {
                        Text(if (provider.connected) "Update key" else "Save key")
                    }
                    if (provider.connected) {
                        OutlinedButton(
                            onClick = onClear,
                            enabled = !isBusy,
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("Clear")
                        }
                    }
                }
            } else {
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Use Desktop CLI subscription, then pair this phone.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
private fun SubscriptionProductCard(
    product: SubscriptionProduct,
    playPrice: String?,
    isPurchasing: Boolean,
    playReady: Boolean,
    onPurchase: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.45f)
        )
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Text(product.title, style = MaterialTheme.typography.titleSmall)
            Text(
                text = "${playPrice ?: product.price} / ${product.period}",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.primary
            )
            product.includes.forEach { item ->
                Text(
                    text = "• $item",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            Spacer(modifier = Modifier.height(10.dp))
            Button(
                onClick = onPurchase,
                enabled = playReady && !isPurchasing,
                modifier = Modifier.fillMaxWidth()
            ) {
                if (isPurchasing) {
                    CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                } else {
                    Text(if (playReady) "Subscribe with Google Play" else "Unavailable on Play")
                }
            }
        }
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
