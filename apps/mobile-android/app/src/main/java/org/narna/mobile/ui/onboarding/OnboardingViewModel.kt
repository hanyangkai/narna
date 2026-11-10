package org.narna.mobile.ui.onboarding

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import org.narna.mobile.data.api.NARNAApiService
import org.narna.mobile.data.model.OnboardingPath
import org.narna.mobile.data.model.OnboardingStatusResponse
import org.narna.mobile.data.preferences.UserPreferences
import org.narna.mobile.data.storage.SecureStorage
import javax.inject.Inject

data class OnboardingUiState(
    val isLoading: Boolean = true,
    val status: OnboardingStatusResponse? = null,
    val selectedPathId: String? = null,
    val error: String? = null
)

@HiltViewModel
class OnboardingViewModel @Inject constructor(
    private val apiService: NARNAApiService,
    private val secureStorage: SecureStorage,
    private val userPreferences: UserPreferences
) : ViewModel() {

    private val _uiState = MutableStateFlow(OnboardingUiState())
    val uiState: StateFlow<OnboardingUiState> = _uiState.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            val token = secureStorage.getMobileToken()
            apiService.getOnboardingStatus(token)
                .onSuccess { status ->
                    _uiState.value = OnboardingUiState(
                        isLoading = false,
                        status = status,
                        selectedPathId = status.paths.firstOrNull { it.recommended }?.id
                            ?: status.paths.firstOrNull()?.id
                    )
                }
                .onFailure { error ->
                    _uiState.value = OnboardingUiState(
                        isLoading = false,
                        status = fallbackStatus(),
                        selectedPathId = "external_ai",
                        error = error.message
                    )
                }
        }
    }

    fun selectPath(pathId: String) {
        _uiState.value = _uiState.value.copy(selectedPathId = pathId)
    }

    fun confirmPath(onConfirmed: (OnboardingPath) -> Unit) {
        val path = _uiState.value.status?.paths
            ?.firstOrNull { it.id == _uiState.value.selectedPathId }
            ?: return
        viewModelScope.launch {
            userPreferences.setOnboardingPath(path.id)
            onConfirmed(path)
        }
    }

    private fun fallbackStatus(): OnboardingStatusResponse {
        return OnboardingStatusResponse(
            ok = true,
            paired = secureStorage.isPaired(),
            plan = "free",
            aiReady = false,
            needsOnboarding = true,
            paths = listOf(
                OnboardingPath(
                    id = "external_ai",
                    title = "Use your AI (Claude / ChatGPT)",
                    subtitle = "Desktop BYOK or CLI subscription, then pair this phone",
                    recommended = true,
                    steps = listOf(
                        "Install NARNA Desktop and sign in Claude CLI or Codex",
                        "Or paste an API key later in Settings → AI Providers",
                        "On Desktop open Pairing and scan the QR here"
                    ),
                    cta = "Connect external AI"
                ),
                OnboardingPath(
                    id = "narna_pro",
                    title = "Buy NARNA Pro",
                    subtitle = "Cloud agent features via Google Play — then attach your API key",
                    recommended = false,
                    steps = listOf(
                        "Subscribe with Google Play Billing only (no crypto in-app)",
                        "Attach Claude/OpenAI key in Settings for always-on cloud agent",
                        "Or still pair Desktop if you use a CLI subscription"
                    ),
                    cta = "See NARNA plans"
                )
            )
        )
    }
}
