package org.narna.mobile.data.api

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import org.narna.mobile.BuildConfig
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Holds the active API base URL so Remote Access settings can switch between
 * local, Tailscale, and custom HTTPS without recreating the whole DI graph.
 */
@Singleton
class ServerConfig @Inject constructor() {
    private val _baseUrl = MutableStateFlow(normalize(BuildConfig.BASE_URL))
    val baseUrl: StateFlow<String> = _baseUrl.asStateFlow()

    fun currentBaseUrl(): String = _baseUrl.value

    fun setBaseUrl(url: String) {
        val normalized = normalize(url)
        if (normalized.isNotBlank()) {
            _baseUrl.value = normalized
        }
    }

    companion object {
        fun normalize(url: String): String = url.trim().trimEnd('/')
    }
}
