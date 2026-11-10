package org.narna.mobile.ui.settings

import android.app.Activity
import android.os.Build
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.android.billingclient.api.ProductDetails
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import org.narna.mobile.BuildConfig
import org.narna.mobile.data.api.NARNAApiService
import org.narna.mobile.data.api.ServerConfig
import org.narna.mobile.data.billing.PlayBillingManager
import org.narna.mobile.data.model.AiProviderConfigureRequest
import org.narna.mobile.data.model.AiProviderInfo
import org.narna.mobile.data.model.ConnectedApp
import org.narna.mobile.data.model.PushRegisterRequest
import org.narna.mobile.data.model.RemoteConfigUpdate
import org.narna.mobile.data.model.StoreVerifyRequest
import org.narna.mobile.data.model.SubscriptionProduct
import org.narna.mobile.data.preferences.UserPreferences
import org.narna.mobile.data.storage.SecureStorage
import java.util.UUID
import javax.inject.Inject

data class SettingsUiState(
    val agentName: String? = null,
    val darkTheme: Boolean = false,
    val notificationsEnabled: Boolean = true,
    val openAIVoiceKey: String? = null,
    val remoteMode: String = "local",
    val remoteHost: String = "",
    val remoteBaseUrl: String = "",
    val remoteHint: String? = null,
    val connectedApps: List<ConnectedApp> = emptyList(),
    val aiProviders: List<AiProviderInfo> = emptyList(),
    val aiProvidersNote: String? = null,
    val defaultProvider: String? = null,
    val subscriptionProducts: List<SubscriptionProduct> = emptyList(),
    val playProductDetails: Map<String, ProductDetails> = emptyMap(),
    val playBillingReady: Boolean = false,
    val plan: String = "free",
    val aiReady: Boolean = false,
    val manageSubscriptionUrl: String? = null,
    val configuringProviderId: String? = null,
    val purchasingProductId: String? = null,
    val isSavingRemote: Boolean = false,
    val isLoadingApps: Boolean = false,
    val isLoadingProviders: Boolean = false,
    val isLoadingProducts: Boolean = false,
    val actingApp: String? = null,
    val showUnpairDialog: Boolean = false,
    val message: String? = null,
    val error: String? = null
)

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val secureStorage: SecureStorage,
    private val userPreferences: UserPreferences,
    private val apiService: NARNAApiService,
    private val serverConfig: ServerConfig,
    private val playBillingManager: PlayBillingManager
) : ViewModel() {

    private val _uiState = MutableStateFlow(SettingsUiState())
    val uiState: StateFlow<SettingsUiState> = _uiState.asStateFlow()

    init {
        playBillingManager.startConnection()
        loadSettings()
        loadConnectedApps()
        syncRemoteFromServer()
        loadAiProviders()
        loadSubscriptionProducts()
        viewModelScope.launch {
            playBillingManager.ready.collect { ready ->
                _uiState.value = _uiState.value.copy(playBillingReady = ready)
                if (ready) {
                    refreshPlayProductDetails()
                }
            }
        }
    }

    private fun loadSettings() {
        viewModelScope.launch {
            combine(
                userPreferences.darkTheme,
                userPreferences.notificationsEnabled,
                userPreferences.remoteMode,
                userPreferences.remoteHost,
                userPreferences.remoteBaseUrl
            ) { darkTheme, notificationsEnabled, remoteMode, remoteHost, remoteBaseUrl ->
                _uiState.value.copy(
                    agentName = secureStorage.getAgentName(),
                    darkTheme = darkTheme,
                    notificationsEnabled = notificationsEnabled,
                    openAIVoiceKey = secureStorage.getOpenAIVoiceKey(),
                    remoteMode = remoteMode,
                    remoteHost = remoteHost,
                    remoteBaseUrl = remoteBaseUrl.ifBlank { serverConfig.currentBaseUrl() }
                )
            }.collect { state ->
                _uiState.value = state
                applyLocalBaseUrl(state.remoteMode, state.remoteHost, state.remoteBaseUrl)
            }
        }
    }

    private fun applyLocalBaseUrl(mode: String, host: String, baseUrl: String) {
        val resolved = when (mode) {
            "tailscale" -> {
                if (baseUrl.isNotBlank()) baseUrl
                else if (host.isNotBlank()) "https://$host:8765"
                else BuildConfig.BASE_URL
            }
            "custom" -> baseUrl.ifBlank { BuildConfig.BASE_URL }
            else -> BuildConfig.BASE_URL
        }
        serverConfig.setBaseUrl(resolved)
    }

    private fun syncRemoteFromServer() {
        val token = secureStorage.getMobileToken() ?: return
        viewModelScope.launch {
            apiService.getRemoteStatus(token)
                .onSuccess { response ->
                    val remote = response.remote
                    userPreferences.setRemoteAccess(
                        mode = remote.mode,
                        host = remote.host.orEmpty(),
                        baseUrl = remote.baseUrl.orEmpty()
                    )
                    _uiState.value = _uiState.value.copy(remoteHint = remote.tailscaleHint)
                    remote.baseUrl?.let { serverConfig.setBaseUrl(it) }
                }
        }
    }

    fun loadAiProviders() {
        val token = secureStorage.getMobileToken() ?: return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoadingProviders = true)
            val status = apiService.getOnboardingStatus(token).getOrNull()
            apiService.listAiProviders(token)
                .onSuccess { response ->
                    _uiState.value = _uiState.value.copy(
                        aiProviders = response.providers,
                        aiProvidersNote = response.note,
                        defaultProvider = response.defaultProvider,
                        plan = status?.plan ?: _uiState.value.plan,
                        aiReady = status?.aiReady ?: false,
                        isLoadingProviders = false
                    )
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        isLoadingProviders = false,
                        error = error.message ?: "Failed to load AI providers"
                    )
                }
        }
    }

    fun configureProvider(providerId: String, apiKey: String) {
        val token = secureStorage.getMobileToken() ?: return
        if (apiKey.trim().length < 8) {
            _uiState.value = _uiState.value.copy(error = "API key looks too short")
            return
        }
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(configuringProviderId = providerId, error = null)
            apiService.configureAiProvider(
                token,
                providerId,
                AiProviderConfigureRequest(apiKey = apiKey.trim())
            ).onSuccess { response ->
                when (providerId) {
                    "openai" -> secureStorage.saveOpenAIKey(apiKey.trim())
                    "anthropic" -> secureStorage.saveAnthropicKey(apiKey.trim())
                }
                _uiState.value = _uiState.value.copy(
                    configuringProviderId = null,
                    message = response.message ?: "${response.provider} connected",
                    aiReady = true
                )
                loadAiProviders()
            }.onFailure { error ->
                _uiState.value = _uiState.value.copy(
                    configuringProviderId = null,
                    error = error.message ?: "Failed to save provider key"
                )
            }
        }
    }

    fun clearProvider(providerId: String) {
        val token = secureStorage.getMobileToken() ?: return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(configuringProviderId = providerId)
            apiService.clearAiProvider(token, providerId)
                .onSuccess {
                    _uiState.value = _uiState.value.copy(
                        configuringProviderId = null,
                        message = "$providerId disconnected"
                    )
                    loadAiProviders()
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        configuringProviderId = null,
                        error = error.message ?: "Failed to clear provider"
                    )
                }
        }
    }

    fun loadSubscriptionProducts() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoadingProducts = true)
            apiService.getSubscriptionProducts()
                .onSuccess { response ->
                    _uiState.value = _uiState.value.copy(
                        subscriptionProducts = response.products,
                        manageSubscriptionUrl = response.manageUrls?.android,
                        isLoadingProducts = false
                    )
                    refreshPlayProductDetails()
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        isLoadingProducts = false,
                        error = error.message ?: "Failed to load subscription products"
                    )
                }
        }
    }

    private suspend fun refreshPlayProductDetails() {
        val ids = _uiState.value.subscriptionProducts.map { it.productId }
        if (ids.isEmpty() || !_uiState.value.playBillingReady) return
        val details = playBillingManager.querySubscriptionDetails(ids)
        _uiState.value = _uiState.value.copy(
            playProductDetails = details.associateBy { it.productId }
        )
    }

    fun purchaseProduct(activity: Activity, productId: String) {
        val token = secureStorage.getMobileToken()
        if (token == null) {
            _uiState.value = _uiState.value.copy(error = "Pair a device before purchasing")
            return
        }
        val details = _uiState.value.playProductDetails[productId]
        if (details == null) {
            _uiState.value = _uiState.value.copy(
                error = "Google Play product unavailable. Install from Play Store and try again."
            )
            return
        }
        _uiState.value = _uiState.value.copy(purchasingProductId = productId, error = null)
        playBillingManager.launchSubscriptionPurchase(activity, details) { result ->
            viewModelScope.launch {
                result
                    .onSuccess { purchase ->
                        apiService.verifyStorePurchase(
                            token,
                            StoreVerifyRequest(
                                platform = "android",
                                productId = purchase.productId.ifBlank { productId },
                                transactionId = purchase.orderId ?: purchase.purchaseToken,
                                purchaseToken = purchase.purchaseToken
                            )
                        ).onSuccess { verify ->
                            _uiState.value = _uiState.value.copy(
                                purchasingProductId = null,
                                plan = verify.plan ?: "cloud",
                                message = verify.message ?: "NARNA Pro activated via Google Play"
                            )
                            loadAiProviders()
                        }.onFailure { error ->
                            _uiState.value = _uiState.value.copy(
                                purchasingProductId = null,
                                error = error.message ?: "Purchase verify failed"
                            )
                        }
                    }
                    .onFailure { error ->
                        _uiState.value = _uiState.value.copy(
                            purchasingProductId = null,
                            error = error.message ?: "Purchase failed"
                        )
                    }
            }
        }
    }

    fun setDarkTheme(enabled: Boolean) {
        viewModelScope.launch {
            userPreferences.setDarkTheme(enabled)
        }
    }

    fun setNotificationsEnabled(enabled: Boolean) {
        viewModelScope.launch {
            userPreferences.setNotificationsEnabled(enabled)
            if (enabled) {
                registerPush()
            }
        }
    }

    private suspend fun registerPush() {
        val token = secureStorage.getMobileToken() ?: return
        val existing = userPreferences.pushDeviceToken.first()
        val deviceToken = existing ?: UUID.randomUUID().toString().also {
            userPreferences.setPushDeviceToken(it)
        }
        apiService.registerPush(
            token,
            PushRegisterRequest(
                platform = "android",
                deviceToken = deviceToken,
                deviceName = Build.MODEL
            )
        ).onSuccess {
            _uiState.value = _uiState.value.copy(message = "Push notifications enabled")
        }.onFailure { error ->
            _uiState.value = _uiState.value.copy(
                error = error.message ?: "Failed to register for push"
            )
        }
    }

    fun saveOpenAIVoiceKey(key: String) {
        secureStorage.saveOpenAIVoiceKey(key)
        _uiState.value = _uiState.value.copy(openAIVoiceKey = key, message = "Voice key saved locally")
    }

    fun updateRemoteDraft(mode: String? = null, host: String? = null, baseUrl: String? = null) {
        _uiState.value = _uiState.value.copy(
            remoteMode = mode ?: _uiState.value.remoteMode,
            remoteHost = host ?: _uiState.value.remoteHost,
            remoteBaseUrl = baseUrl ?: _uiState.value.remoteBaseUrl
        )
    }

    fun saveRemoteAccess() {
        val token = secureStorage.getMobileToken() ?: return
        val state = _uiState.value
        viewModelScope.launch {
            _uiState.value = state.copy(isSavingRemote = true, error = null)
            apiService.updateRemoteConfig(
                token,
                RemoteConfigUpdate(
                    mode = state.remoteMode,
                    host = state.remoteHost.ifBlank { null },
                    baseUrl = state.remoteBaseUrl.ifBlank { null }
                )
            ).onSuccess { response ->
                val remote = response.remote
                userPreferences.setRemoteAccess(
                    mode = remote.mode,
                    host = remote.host.orEmpty(),
                    baseUrl = remote.baseUrl.orEmpty()
                )
                remote.baseUrl?.let { serverConfig.setBaseUrl(it) }
                _uiState.value = _uiState.value.copy(
                    isSavingRemote = false,
                    remoteMode = remote.mode,
                    remoteHost = remote.host.orEmpty(),
                    remoteBaseUrl = remote.baseUrl.orEmpty(),
                    remoteHint = remote.tailscaleHint,
                    message = "Remote access updated"
                )
            }.onFailure { error ->
                _uiState.value = _uiState.value.copy(
                    isSavingRemote = false,
                    error = error.message ?: "Failed to update remote access"
                )
            }
        }
    }

    fun loadConnectedApps() {
        val token = secureStorage.getMobileToken() ?: return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoadingApps = true)
            apiService.listConnectedApps(token)
                .onSuccess { response ->
                    _uiState.value = _uiState.value.copy(
                        connectedApps = response.apps,
                        isLoadingApps = false
                    )
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        isLoadingApps = false,
                        error = error.message ?: "Failed to load connected apps"
                    )
                }
        }
    }

    fun toggleConnectedApp(app: ConnectedApp) {
        val token = secureStorage.getMobileToken() ?: return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(actingApp = app.app)
            val result = if (app.connected) {
                apiService.disconnectApp(token, app.app)
            } else {
                apiService.connectApp(token, app.app)
            }
            result
                .onSuccess {
                    _uiState.value = _uiState.value.copy(
                        actingApp = null,
                        message = if (app.connected) {
                            "${app.displayName} disconnected"
                        } else {
                            "${app.displayName} connected"
                        }
                    )
                    loadConnectedApps()
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        actingApp = null,
                        error = error.message ?: "Failed to update ${app.displayName}"
                    )
                }
        }
    }

    fun showUnpairDialog() {
        _uiState.value = _uiState.value.copy(showUnpairDialog = true)
    }

    fun hideUnpairDialog() {
        _uiState.value = _uiState.value.copy(showUnpairDialog = false)
    }

    fun unpairDevice() {
        viewModelScope.launch {
            userPreferences.clearOnboarding()
            secureStorage.clearAll()
            _uiState.value = SettingsUiState()
        }
    }

    fun clearMessage() {
        _uiState.value = _uiState.value.copy(message = null, error = null)
    }
}
