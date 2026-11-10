package org.narna.mobile.ui.main

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import org.narna.mobile.data.api.NARNAApiService
import org.narna.mobile.data.inbox.InboxBadgeStore
import org.narna.mobile.data.storage.SecureStorage
import javax.inject.Inject

@HiltViewModel
class MainTabsViewModel @Inject constructor(
    private val apiService: NARNAApiService,
    private val secureStorage: SecureStorage,
    private val inboxBadgeStore: InboxBadgeStore
) : ViewModel() {

    val pendingCount: StateFlow<Int> = inboxBadgeStore.pendingCount

    fun refreshInboxBadge() {
        val token = secureStorage.getMobileToken() ?: return
        viewModelScope.launch {
            apiService.getInbox(token)
                .onSuccess { response ->
                    inboxBadgeStore.setPendingCount(response.pendingCount)
                }
        }
    }
}
