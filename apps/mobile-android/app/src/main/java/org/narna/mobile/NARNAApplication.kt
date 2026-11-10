package org.narna.mobile

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import androidx.hilt.work.HiltWorkerFactory
import androidx.work.Configuration
import dagger.hilt.android.HiltAndroidApp
import javax.inject.Inject

@HiltAndroidApp
class NARNAApplication : Application(), Configuration.Provider {

    @Inject
    lateinit var workerFactory: HiltWorkerFactory

    override fun onCreate() {
        super.onCreate()
        createNotificationChannels()
    }

    override fun getWorkManagerConfiguration(): Configuration {
        return Configuration.Builder()
            .setWorkerFactory(workerFactory)
            .build()
    }

    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channels = listOf(
                NotificationChannel(
                    CHANNEL_CONNECTION,
                    "Connection Status",
                    NotificationManager.IMPORTANCE_LOW
                ).apply {
                    description = "WebSocket connection status"
                    setShowBadge(false)
                },
                NotificationChannel(
                    CHANNEL_APPROVALS,
                    "Approvals",
                    NotificationManager.IMPORTANCE_HIGH
                ).apply {
                    description = "Bot approval requests"
                    setShowBadge(true)
                },
                NotificationChannel(
                    CHANNEL_MESSAGES,
                    "Messages",
                    NotificationManager.IMPORTANCE_DEFAULT
                ).apply {
                    description = "Bot messages"
                    setShowBadge(true)
                }
            )

            val notificationManager = getSystemService(NotificationManager::class.java)
            channels.forEach { notificationManager.createNotificationChannel(it) }
        }
    }

    companion object {
        const val CHANNEL_CONNECTION = "connection"
        const val CHANNEL_APPROVALS = "approvals"
        const val CHANNEL_MESSAGES = "messages"
    }
}
