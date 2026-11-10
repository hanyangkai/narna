package org.narna.mobile.ui.pairing

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import org.narna.mobile.data.api.NARNAApiService
import org.narna.mobile.data.storage.SecureStorage
import javax.inject.Inject

data class PairingUiState(
    val isLoading: Boolean = false,
    val isPaired: Boolean = false,
    val error: String? = null,
    val agentName: String? = null
)

@HiltViewModel
class PairingViewModel @Inject constructor(
    private val apiService: NARNAApiService,
    private val secureStorage: SecureStorage
) : ViewModel() {

    private val _uiState = MutableStateFlow(PairingUiState())
    val uiState: StateFlow<PairingUiState> = _uiState.asStateFlow()

    init {
        checkPairingStatus()
    }

    private fun checkPairingStatus() {
        val isPaired = secureStorage.isPaired()
        val agentName = secureStorage.getAgentName()
        _uiState.value = _uiState.value.copy(
            isPaired = isPaired,
            agentName = agentName
        )
    }

    fun verifyPairingCode(code: String) {
        if (code.length != 6) {
            _uiState.value = _uiState.value.copy(error = "Code must be 6 digits")
            return
        }

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            apiService.verifyPairing(code)
                .onSuccess { response ->
                    secureStorage.saveMobileToken(response.mobileToken)
                    secureStorage.saveAgentName(response.agentName)
                    secureStorage.saveOrgId(response.orgId)

                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        isPaired = true,
                        agentName = response.agentName,
                        error = null
                    )
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = error.message ?: "Pairing failed"
                    )
                }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}
