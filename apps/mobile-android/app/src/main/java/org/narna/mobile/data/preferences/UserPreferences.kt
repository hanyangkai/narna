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
}
