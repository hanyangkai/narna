package org.narna.mobile.ui.main

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import org.narna.mobile.data.api.NARNAApiService
import org.narna.mobile.data.inbox.InboxBadgeStore
import org.narna.mobile.data.model.AiProviderInfo
import org.narna.mobile.data.model.OnboardingPath
import org.narna.mobile.data.model.SubscriptionProduct
import org.narna.mobile.data.storage.SecureStorage
import javax.inject.Inject

data class MainTabsUiState(
    val aiReady: Boolean = true,
    val needsAiConnect: Boolean = false,
    val showConnectSheet: Boolean = false,
    val paths: List<OnboardingPath> = emptyList(),
    val providers: List<AiProviderInfo> = emptyList(),
    val products: List<SubscriptionProduct> = emptyList()
)

@HiltViewModel
class MainTabsViewModel @Inject constructor(
    private val apiService: NARNAApiService,
    private val secureStorage: SecureStorage,
    private val inboxBadgeStore: InboxBadgeStore
) : ViewModel() {

    val pendingCount: StateFlow<Int> = inboxBadgeStore.pendingCount

    private val _uiState = MutableStateFlow(MainTabsUiState())
    val uiState: StateFlow<MainTabsUiState> = _uiState.asStateFlow()

    fun refreshInboxBadge() {
        val token = secureStorage.getMobileToken() ?: return
        viewModelScope.launch {
            apiService.getInbox(token)
                .onSuccess { response ->
                    inboxBadgeStore.setPendingCount(response.pendingCount)
                }
        }
    }

    fun refreshOnboardingStatus() {
        val token = secureStorage.getMobileToken() ?: return
        viewModelScope.launch {
            val statusResult = apiService.getOnboardingStatus(token)
            val productsResult = apiService.getSubscriptionProducts()
            statusResult.onSuccess { status ->
                val needs = status.paired && !status.aiReady
                val wasNeeded = _uiState.value.needsAiConnect
                _uiState.value = _uiState.value.copy(
                    aiReady = status.aiReady,
                    needsAiConnect = needs,
                    showConnectSheet = when {
                        !needs -> false
                        !wasNeeded -> true // auto-present once when AI becomes not ready
                        else -> _uiState.value.showConnectSheet
                    },
                    paths = status.paths,
                    providers = status.providers,
                    products = productsResult.getOrNull()?.products.orEmpty()
                )
            }
        }
    }

    fun openConnectSheet() {
        _uiState.value = _uiState.value.copy(showConnectSheet = true)
    }

    fun dismissConnectSheet() {
        _uiState.value = _uiState.value.copy(showConnectSheet = false)
    }
}
