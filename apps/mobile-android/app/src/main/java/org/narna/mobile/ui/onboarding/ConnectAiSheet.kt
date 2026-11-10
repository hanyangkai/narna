package org.narna.mobile.ui.onboarding

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import org.narna.mobile.data.model.AiProviderInfo
import org.narna.mobile.data.model.OnboardingPath
import org.narna.mobile.data.model.SubscriptionProduct

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ConnectAiSheet(
    paths: List<OnboardingPath>,
    providers: List<AiProviderInfo>,
    products: List<SubscriptionProduct>,
    onDismiss: () -> Unit,
    onOpenSettingsProviders: () -> Unit,
    onOpenSubscription: () -> Unit,
    sheetState: SheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
) {
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp)
                .padding(bottom = 32.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = "Connect AI to continue",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.SemiBold
            )
            Text(
                text = "You're paired, but no model provider is ready yet. Use Desktop CLI/BYOK or attach a cloud API key after NARNA Pro.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            paths.forEach { path ->
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Text(path.title, style = MaterialTheme.typography.titleSmall)
                        Text(
                            path.subtitle,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }

            if (providers.isNotEmpty()) {
                Text("Providers", style = MaterialTheme.typography.titleMedium)
                providers.forEach { provider ->
                    ListItem(
                        headlineContent = { Text(provider.name) },
                        supportingContent = {
                            Text(
                                if (provider.connected) {
                                    provider.maskedKey ?: "Connected"
                                } else {
                                    provider.hint ?: "Not connected"
                                }
                            )
                        },
                        trailingContent = {
                            Text(
                                if (provider.connected) "Ready" else "Needed",
                                color = if (provider.connected) {
                                    MaterialTheme.colorScheme.primary
                                } else {
                                    MaterialTheme.colorScheme.error
                                }
                            )
                        }
                    )
                }
            }

            Button(
                onClick = onOpenSettingsProviders,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Configure AI providers")
            }

            if (products.isNotEmpty()) {
                OutlinedButton(
                    onClick = onOpenSubscription,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("View NARNA Pro on Google Play")
                }
            }

            TextButton(
                onClick = onDismiss,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Not now")
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ConnectAiBanner(
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        color = MaterialTheme.colorScheme.tertiaryContainer,
        onClick = onClick
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "AI not connected",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    text = "Pair Desktop CLI or attach an API key for cloud agent",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onTertiaryContainer
                )
            }
            TextButton(onClick = onClick) {
                Text("Connect")
            }
        }
    }
}
