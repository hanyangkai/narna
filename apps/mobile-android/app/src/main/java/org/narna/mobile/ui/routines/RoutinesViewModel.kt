package org.narna.mobile.ui.routines

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import org.narna.mobile.data.api.NARNAApiService
import org.narna.mobile.data.model.RoutineCreateRequest
import org.narna.mobile.data.model.RoutineInfo
import org.narna.mobile.data.storage.SecureStorage
import javax.inject.Inject

data class RoutinesUiState(
    val routines: List<RoutineInfo> = emptyList(),
    val isLoading: Boolean = false,
    val isRefreshing: Boolean = false,
    val isSaving: Boolean = false,
    val showCreateDialog: Boolean = false,
    val error: String? = null,
    val message: String? = null
)

@HiltViewModel
class RoutinesViewModel @Inject constructor(
    private val apiService: NARNAApiService,
    private val secureStorage: SecureStorage
) : ViewModel() {

    private val _uiState = MutableStateFlow(RoutinesUiState())
    val uiState: StateFlow<RoutinesUiState> = _uiState.asStateFlow()

    init {
        loadRoutines()
    }

    fun loadRoutines() {
        val token = secureStorage.getMobileToken() ?: return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            apiService.listRoutines(token)
                .onSuccess { response ->
                    _uiState.value = _uiState.value.copy(
                        routines = response.routines,
                        isLoading = false
                    )
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = error.message ?: "Failed to load routines"
                    )
                }
        }
    }

    fun refresh() {
        val token = secureStorage.getMobileToken() ?: return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isRefreshing = true, error = null)
            apiService.listRoutines(token)
                .onSuccess { response ->
                    _uiState.value = _uiState.value.copy(
                        routines = response.routines,
                        isRefreshing = false
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

    fun showCreateDialog() {
        _uiState.value = _uiState.value.copy(showCreateDialog = true)
    }

    fun hideCreateDialog() {
        _uiState.value = _uiState.value.copy(showCreateDialog = false)
    }

    fun createRoutine(name: String, cron: String, botId: String, prompt: String) {
        val token = secureStorage.getMobileToken() ?: return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSaving = true, error = null)
            apiService.createRoutine(
                token,
                RoutineCreateRequest(
                    name = name.trim(),
                    cron = cron.trim().ifBlank { "0 9 * * *" },
                    botId = botId.trim().ifBlank { "bot_1" },
                    prompt = prompt.trim().ifBlank { "Run morning digest" }
                )
            )
                .onSuccess {
                    _uiState.value = _uiState.value.copy(
                        isSaving = false,
                        showCreateDialog = false,
                        message = "Routine created"
                    )
                    refresh()
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        isSaving = false,
                        error = error.message ?: "Failed to create routine"
                    )
                }
        }
    }

    fun toggleRoutine(routine: RoutineInfo) {
        val token = secureStorage.getMobileToken() ?: return
        viewModelScope.launch {
            apiService.toggleRoutine(token, routine.routineId)
                .onSuccess { updated ->
                    _uiState.value = _uiState.value.copy(
                        routines = _uiState.value.routines.map {
                            if (it.routineId == updated.routineId) updated else it
                        }
                    )
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        error = error.message ?: "Failed to toggle routine"
                    )
                }
        }
    }

    fun deleteRoutine(routine: RoutineInfo) {
        val token = secureStorage.getMobileToken() ?: return
        viewModelScope.launch {
            apiService.deleteRoutine(token, routine.routineId)
                .onSuccess {
                    _uiState.value = _uiState.value.copy(message = "Routine deleted")
                    refresh()
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        error = error.message ?: "Failed to delete routine"
                    )
                }
        }
    }

    fun clearMessage() {
        _uiState.value = _uiState.value.copy(message = null, error = null)
    }
}
