package org.narna.mobile.ui.inbox

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import org.narna.mobile.data.api.NARNAApiService
import org.narna.mobile.data.inbox.InboxBadgeStore
import org.narna.mobile.data.model.InboxItem
import org.narna.mobile.data.storage.SecureStorage
import javax.inject.Inject

data class InboxUiState(
    val items: List<InboxItem> = emptyList(),
    val pendingCount: Int = 0,
    val isLoading: Boolean = false,
    val isRefreshing: Boolean = false,
    val actingItemId: String? = null,
    val error: String? = null,
    val message: String? = null
)

@HiltViewModel
class InboxViewModel @Inject constructor(
    private val apiService: NARNAApiService,
    private val secureStorage: SecureStorage,
    private val inboxBadgeStore: InboxBadgeStore
) : ViewModel() {

    private val _uiState = MutableStateFlow(InboxUiState())
    val uiState: StateFlow<InboxUiState> = _uiState.asStateFlow()

    init {
        loadInbox()
    }

    fun loadInbox() {
        val token = secureStorage.getMobileToken() ?: return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            apiService.getInbox(token)
                .onSuccess { response ->
                    inboxBadgeStore.setPendingCount(response.pendingCount)
                    _uiState.value = _uiState.value.copy(
                        items = response.items,
                        pendingCount = response.pendingCount,
                        isLoading = false,
                        error = null
                    )
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = error.message ?: "Failed to load inbox"
                    )
                }
        }
    }

    fun refresh() {
        val token = secureStorage.getMobileToken() ?: return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isRefreshing = true, error = null)
            apiService.getInbox(token)
                .onSuccess { response ->
                    inboxBadgeStore.setPendingCount(response.pendingCount)
                    _uiState.value = _uiState.value.copy(
                        items = response.items,
                        pendingCount = response.pendingCount,
                        isRefreshing = false
                    )
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        isRefreshing = false,
                        error = error.message ?: "Failed to refresh inbox"
                    )
                }
        }
    }

    fun allow(item: InboxItem) {
        decide(item, allow = true)
    }

    fun deny(item: InboxItem) {
        decide(item, allow = false)
    }

    private fun decide(item: InboxItem, allow: Boolean) {
        if (item.kind != "approval") return
        val token = secureStorage.getMobileToken() ?: return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(actingItemId = item.itemId, error = null)
            val result = if (allow) {
                apiService.allowApproval(token, item.itemId)
            } else {
                apiService.denyApproval(token, item.itemId)
            }
            result
                .onSuccess {
                    _uiState.value = _uiState.value.copy(
                        actingItemId = null,
                        message = if (allow) "Allowed" else "Denied"
                    )
                    refresh()
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        actingItemId = null,
                        error = error.message ?: "Decision failed"
                    )
                }
        }
    }

    fun clearMessage() {
        _uiState.value = _uiState.value.copy(message = null)
    }
}
