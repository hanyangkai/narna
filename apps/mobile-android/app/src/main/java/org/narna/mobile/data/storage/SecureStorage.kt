package org.narna.mobile.data.storage

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SecureStorage @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    private val sharedPreferences = EncryptedSharedPreferences.create(
        context,
        "narna_secure_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    companion object {
        private const val KEY_MOBILE_TOKEN = "mobile_token"
        private const val KEY_AGENT_NAME = "agent_name"
        private const val KEY_ORG_ID = "org_id"
        private const val KEY_DESKTOP_API_KEY = "desktop_api_key"
        private const val KEY_OPENAI_API_KEY = "openai_api_key"
        private const val KEY_ANTHROPIC_API_KEY = "anthropic_api_key"
        private const val KEY_OPENAI_VOICE_KEY = "openai_voice_key"
    }

    // ──────────────────────────────────────────────────────────────
    // Mobile Token
    // ──────────────────────────────────────────────────────────────

    fun saveMobileToken(token: String) {
        sharedPreferences.edit().putString(KEY_MOBILE_TOKEN, token).apply()
    }

    fun getMobileToken(): String? {
        return sharedPreferences.getString(KEY_MOBILE_TOKEN, null)
    }

    fun clearMobileToken() {
        sharedPreferences.edit().remove(KEY_MOBILE_TOKEN).apply()
    }

    // ──────────────────────────────────────────────────────────────
    // Agent Info
    // ──────────────────────────────────────────────────────────────

    fun saveAgentName(name: String) {
        sharedPreferences.edit().putString(KEY_AGENT_NAME, name).apply()
    }

    fun getAgentName(): String? {
        return sharedPreferences.getString(KEY_AGENT_NAME, null)
    }

    fun saveOrgId(id: Int) {
        sharedPreferences.edit().putInt(KEY_ORG_ID, id).apply()
    }

    fun getOrgId(): Int {
        return sharedPreferences.getInt(KEY_ORG_ID, -1)
    }

    // ──────────────────────────────────────────────────────────────
    // Desktop API Key
    // ──────────────────────────────────────────────────────────────

    fun saveDesktopApiKey(key: String) {
        sharedPreferences.edit().putString(KEY_DESKTOP_API_KEY, key).apply()
    }

    fun getDesktopApiKey(): String? {
        return sharedPreferences.getString(KEY_DESKTOP_API_KEY, null)
    }

    // ──────────────────────────────────────────────────────────────
    // AI Provider API Keys
    // ──────────────────────────────────────────────────────────────

    fun saveOpenAIKey(key: String) {
        sharedPreferences.edit().putString(KEY_OPENAI_API_KEY, key).apply()
    }

    fun getOpenAIKey(): String? {
        return sharedPreferences.getString(KEY_OPENAI_API_KEY, null)
    }

    fun saveAnthropicKey(key: String) {
        sharedPreferences.edit().putString(KEY_ANTHROPIC_API_KEY, key).apply()
    }

    fun getAnthropicKey(): String? {
        return sharedPreferences.getString(KEY_ANTHROPIC_API_KEY, null)
    }

    fun saveOpenAIVoiceKey(key: String) {
        sharedPreferences.edit().putString(KEY_OPENAI_VOICE_KEY, key).apply()
    }

    fun getOpenAIVoiceKey(): String? {
        return sharedPreferences.getString(KEY_OPENAI_VOICE_KEY, null)
            ?: getOpenAIKey()
    }

    // ──────────────────────────────────────────────────────────────
    // Pairing Status
    // ──────────────────────────────────────────────────────────────

    fun isPaired(): Boolean {
        return getMobileToken() != null
    }

    // ──────────────────────────────────────────────────────────────
    // Clear All Data
    // ──────────────────────────────────────────────────────────────

    fun clearAll() {
        sharedPreferences.edit().clear().apply()
    }
}
