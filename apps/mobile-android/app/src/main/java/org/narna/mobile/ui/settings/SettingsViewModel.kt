package org.narna.mobile.ui.settings

import android.os.Build
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import org.narna.mobile.BuildConfig
import org.narna.mobile.data.api.NARNAApiService
import org.narna.mobile.data.api.ServerConfig
import org.narna.mobile.data.model.ConnectedApp
import org.narna.mobile.data.model.PushRegisterRequest
import org.narna.mobile.data.model.RemoteConfigUpdate
import org.narna.mobile.data.preferences.UserPreferences
import org.narna.mobile.data.storage.SecureStorage
import java.util.UUID
import javax.inject.Inject

data class SettingsUiState(
    val agentName: String? = null,
    val darkTheme: Boolean = false,
    val notificationsEnabled: Boolean = true,
    val openAIKey: String? = null,
    val anthropicKey: String? = null,
    val openAIVoiceKey: String? = null,
    val remoteMode: String = "local",
    val remoteHost: String = "",
    val remoteBaseUrl: String = "",
    val remoteHint: String? = null,
    val connectedApps: List<ConnectedApp> = emptyList(),
    val isSavingRemote: Boolean = false,
    val isLoadingApps: Boolean = false,
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
    private val serverConfig: ServerConfig
) : ViewModel() {

    private val _uiState = MutableStateFlow(SettingsUiState())
    val uiState: StateFlow<SettingsUiState> = _uiState.asStateFlow()

    init {
        loadSettings()
        loadConnectedApps()
        syncRemoteFromServer()
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
                SettingsUiState(
                    agentName = secureStorage.getAgentName(),
                    darkTheme = darkTheme,
                    notificationsEnabled = notificationsEnabled,
                    openAIKey = secureStorage.getOpenAIKey(),
                    anthropicKey = secureStorage.getAnthropicKey(),
                    openAIVoiceKey = secureStorage.getOpenAIVoiceKey(),
                    remoteMode = remoteMode,
                    remoteHost = remoteHost,
                    remoteBaseUrl = remoteBaseUrl.ifBlank { serverConfig.currentBaseUrl() },
                    connectedApps = _uiState.value.connectedApps,
                    remoteHint = _uiState.value.remoteHint,
                    isSavingRemote = _uiState.value.isSavingRemote,
                    isLoadingApps = _uiState.value.isLoadingApps,
                    actingApp = _uiState.value.actingApp,
                    showUnpairDialog = _uiState.value.showUnpairDialog,
                    message = _uiState.value.message,
                    error = _uiState.value.error
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

    fun saveOpenAIKey(key: String) {
        secureStorage.saveOpenAIKey(key)
        _uiState.value = _uiState.value.copy(openAIKey = key, message = "OpenAI key saved")
    }

    fun saveAnthropicKey(key: String) {
        secureStorage.saveAnthropicKey(key)
        _uiState.value = _uiState.value.copy(anthropicKey = key, message = "Anthropic key saved")
    }

    fun saveOpenAIVoiceKey(key: String) {
        secureStorage.saveOpenAIVoiceKey(key)
        _uiState.value = _uiState.value.copy(openAIVoiceKey = key, message = "Voice key saved")
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
                        message = if (app.connected) "${app.displayName} disconnected" else "${app.displayName} connected"
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
        secureStorage.clearAll()
        _uiState.value = SettingsUiState()
    }

    fun clearMessage() {
        _uiState.value = _uiState.value.copy(message = null, error = null)
    }
}
