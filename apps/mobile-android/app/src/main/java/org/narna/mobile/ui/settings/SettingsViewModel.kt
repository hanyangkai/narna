package org.narna.mobile.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import org.narna.mobile.data.preferences.UserPreferences
import org.narna.mobile.data.storage.SecureStorage
import javax.inject.Inject

data class SettingsUiState(
    val agentName: String? = null,
    val darkTheme: Boolean = false,
    val notificationsEnabled: Boolean = true,
    val openAIKey: String? = null,
    val anthropicKey: String? = null,
    val showUnpairDialog: Boolean = false
)

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val secureStorage: SecureStorage,
    private val userPreferences: UserPreferences
) : ViewModel() {

    private val _uiState = MutableStateFlow(SettingsUiState())
    val uiState: StateFlow<SettingsUiState> = _uiState.asStateFlow()

    init {
        loadSettings()
    }

    private fun loadSettings() {
        viewModelScope.launch {
            combine(
                userPreferences.darkTheme,
                userPreferences.notificationsEnabled
            ) { darkTheme, notificationsEnabled ->
                _uiState.value = _uiState.value.copy(
                    agentName = secureStorage.getAgentName(),
                    darkTheme = darkTheme,
                    notificationsEnabled = notificationsEnabled,
                    openAIKey = secureStorage.getOpenAIKey(),
                    anthropicKey = secureStorage.getAnthropicKey()
                )
            }.collect()
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
        }
    }

    fun saveOpenAIKey(key: String) {
        secureStorage.saveOpenAIKey(key)
        _uiState.value = _uiState.value.copy(openAIKey = key)
    }

    fun saveAnthropicKey(key: String) {
        secureStorage.saveAnthropicKey(key)
        _uiState.value = _uiState.value.copy(anthropicKey = key)
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
}
