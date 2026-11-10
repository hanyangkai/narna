package org.narna.mobile.di

import android.content.Context
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import org.narna.mobile.BuildConfig
import org.narna.mobile.data.api.NARNAApiService
import org.narna.mobile.data.preferences.UserPreferences
import org.narna.mobile.data.storage.SecureStorage
import org.narna.mobile.data.websocket.WebSocketManager
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideBaseUrl(): String = BuildConfig.BASE_URL

    @Provides
    @Singleton
    fun provideNARNAApiService(baseUrl: String): NARNAApiService {
        return NARNAApiService(baseUrl)
    }

    @Provides
    @Singleton
    fun provideWebSocketManager(baseUrl: String): WebSocketManager {
        return WebSocketManager(baseUrl)
    }

    @Provides
    @Singleton
    fun provideSecureStorage(@ApplicationContext context: Context): SecureStorage {
        return SecureStorage(context)
    }

    @Provides
    @Singleton
    fun provideUserPreferences(@ApplicationContext context: Context): UserPreferences {
        return UserPreferences(context)
    }
}
