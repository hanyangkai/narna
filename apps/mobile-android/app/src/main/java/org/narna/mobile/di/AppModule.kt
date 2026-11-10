package org.narna.mobile.di

import android.content.Context
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import org.narna.mobile.data.api.ServerConfig
import org.narna.mobile.data.preferences.UserPreferences
import org.narna.mobile.data.storage.SecureStorage
import org.narna.mobile.data.websocket.WebSocketManager
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideWebSocketManager(serverConfig: ServerConfig): WebSocketManager {
        return WebSocketManager(serverConfig.currentBaseUrl())
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
