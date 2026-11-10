package org.narna.mobile.data.inbox

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class InboxBadgeStore @Inject constructor() {
    private val _pendingCount = MutableStateFlow(0)
    val pendingCount: StateFlow<Int> = _pendingCount.asStateFlow()

    fun setPendingCount(count: Int) {
        _pendingCount.value = count.coerceAtLeast(0)
    }
}
