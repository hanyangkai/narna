package org.narna.mobile.ui.bots

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import org.narna.mobile.data.api.NARNAApiService
import org.narna.mobile.data.model.BotInfo
import org.narna.mobile.data.storage.SecureStorage
import javax.inject.Inject

data class BotListUiState(
    val bots: List<BotInfo> = emptyList(),
    val isLoading: Boolean = false,
    val isRefreshing: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class BotListViewModel @Inject constructor(
    private val apiService: NARNAApiService,
    private val secureStorage: SecureStorage
) : ViewModel() {

    private val _uiState = MutableStateFlow(BotListUiState())
    val uiState: StateFlow<BotListUiState> = _uiState.asStateFlow()

    init {
        loadBots()
    }

    fun loadBots() {
        val mobileToken = secureStorage.getMobileToken() ?: return

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            apiService.listBots(mobileToken)
                .onSuccess { bots ->
                    _uiState.value = _uiState.value.copy(
                        bots = bots,
                        isLoading = false,
                        error = null
                    )
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = error.message ?: "Failed to load bots"
                    )
                }
        }
    }

    fun refresh() {
        val mobileToken = secureStorage.getMobileToken() ?: return

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isRefreshing = true, error = null)

            apiService.listBots(mobileToken)
                .onSuccess { bots ->
                    _uiState.value = _uiState.value.copy(
                        bots = bots,
                        isRefreshing = false,
                        error = null
                    )
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        isRefreshing = false,
                        error = error.message ?: "Failed to refresh"
                    )
                }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}
