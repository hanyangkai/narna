package org.narna.mobile.data.preferences

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "user_preferences")

@Singleton
class UserPreferences @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val dataStore = context.dataStore

    companion object {
        val KEY_DARK_THEME = booleanPreferencesKey("dark_theme")
        val KEY_NOTIFICATIONS_ENABLED = booleanPreferencesKey("notifications_enabled")
        val KEY_AUTO_CONNECT = booleanPreferencesKey("auto_connect")
        val KEY_REMOTE_MODE = stringPreferencesKey("remote_mode")
        val KEY_REMOTE_HOST = stringPreferencesKey("remote_host")
        val KEY_REMOTE_BASE_URL = stringPreferencesKey("remote_base_url")
        val KEY_PUSH_DEVICE_TOKEN = stringPreferencesKey("push_device_token")
        val KEY_ONBOARDING_PATH = stringPreferencesKey("onboarding_path")
        val KEY_ONBOARDING_COMPLETED = booleanPreferencesKey("onboarding_completed")
    }

    // ──────────────────────────────────────────────────────────────
    // Dark Theme
    // ──────────────────────────────────────────────────────────────

    val darkTheme: Flow<Boolean> = dataStore.data.map { prefs ->
        prefs[KEY_DARK_THEME] ?: false
    }

    suspend fun setDarkTheme(enabled: Boolean) {
        dataStore.edit { prefs ->
            prefs[KEY_DARK_THEME] = enabled
        }
    }

    // ──────────────────────────────────────────────────────────────
    // Notifications
    // ──────────────────────────────────────────────────────────────

    val notificationsEnabled: Flow<Boolean> = dataStore.data.map { prefs ->
        prefs[KEY_NOTIFICATIONS_ENABLED] ?: true
    }

    suspend fun setNotificationsEnabled(enabled: Boolean) {
        dataStore.edit { prefs ->
            prefs[KEY_NOTIFICATIONS_ENABLED] = enabled
        }
    }

    // ──────────────────────────────────────────────────────────────
    // Auto Connect
    // ──────────────────────────────────────────────────────────────

    val autoConnect: Flow<Boolean> = dataStore.data.map { prefs ->
        prefs[KEY_AUTO_CONNECT] ?: true
    }

    suspend fun setAutoConnect(enabled: Boolean) {
        dataStore.edit { prefs ->
            prefs[KEY_AUTO_CONNECT] = enabled
        }
    }

    // ──────────────────────────────────────────────────────────────
    // Remote Access
    // ──────────────────────────────────────────────────────────────

    val remoteMode: Flow<String> = dataStore.data.map { prefs ->
        prefs[KEY_REMOTE_MODE] ?: "local"
    }

    val remoteHost: Flow<String> = dataStore.data.map { prefs ->
        prefs[KEY_REMOTE_HOST] ?: ""
    }

    val remoteBaseUrl: Flow<String> = dataStore.data.map { prefs ->
        prefs[KEY_REMOTE_BASE_URL] ?: ""
    }

    suspend fun setRemoteAccess(mode: String, host: String, baseUrl: String) {
        dataStore.edit { prefs ->
            prefs[KEY_REMOTE_MODE] = mode
            prefs[KEY_REMOTE_HOST] = host
            prefs[KEY_REMOTE_BASE_URL] = baseUrl
        }
    }

    // ──────────────────────────────────────────────────────────────
    // Push device token (local placeholder until FCM is wired)
    // ──────────────────────────────────────────────────────────────

    val pushDeviceToken: Flow<String?> = dataStore.data.map { prefs ->
        prefs[KEY_PUSH_DEVICE_TOKEN]
    }

    suspend fun setPushDeviceToken(token: String) {
        dataStore.edit { prefs ->
            prefs[KEY_PUSH_DEVICE_TOKEN] = token
        }
    }

    // ──────────────────────────────────────────────────────────────
    // Onboarding path (external_ai | narna_pro)
    // ──────────────────────────────────────────────────────────────

    val onboardingPath: Flow<String?> = dataStore.data.map { prefs ->
        prefs[KEY_ONBOARDING_PATH]
    }

    val onboardingCompleted: Flow<Boolean> = dataStore.data.map { prefs ->
        prefs[KEY_ONBOARDING_COMPLETED] ?: false
    }

    suspend fun setOnboardingPath(pathId: String) {
        dataStore.edit { prefs ->
            prefs[KEY_ONBOARDING_PATH] = pathId
            prefs[KEY_ONBOARDING_COMPLETED] = true
        }
    }

    suspend fun clearOnboarding() {
        dataStore.edit { prefs ->
            prefs.remove(KEY_ONBOARDING_PATH)
            prefs.remove(KEY_ONBOARDING_COMPLETED)
        }
    }
}
