package org.narna.mobile.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import org.narna.mobile.MainActivity
import org.narna.mobile.NARNAApplication
import org.narna.mobile.R
import org.narna.mobile.data.model.*
import org.narna.mobile.data.storage.SecureStorage
import org.narna.mobile.data.websocket.WebSocketManager
import javax.inject.Inject

@AndroidEntryPoint
class WebSocketService : Service() {

    @Inject
    lateinit var webSocketManager: WebSocketManager

    @Inject
    lateinit var secureStorage: SecureStorage

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var currentBotId: String? = null

    override fun onCreate() {
        super.onCreate()
        startForeground(NOTIFICATION_ID, createNotification("Initializing..."))
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_CONNECT -> {
                val botId = intent.getStringExtra(EXTRA_BOT_ID) ?: return START_NOT_STICKY
                connectToBot(botId)
            }
            ACTION_DISCONNECT -> {
                disconnect()
                stopSelf()
            }
        }
        return START_STICKY
    }

    private fun connectToBot(botId: String) {
        currentBotId = botId
        val mobileToken = secureStorage.getMobileToken()

        if (mobileToken == null) {
            stopSelf()
            return
        }

        webSocketManager.connect(botId, mobileToken, serviceScope)

        // Observe connection state
        serviceScope.launch {
            webSocketManager.connectionState.collectLatest { state ->
                updateNotification(state)
            }
        }

        // Observe events for notifications
        serviceScope.launch {
            webSocketManager.events.collectLatest { event ->
                handleEvent(event)
            }
        }
    }

    private fun disconnect() {
        webSocketManager.disconnect()
        currentBotId = null
    }

    private fun updateNotification(state: WebSocketManager.ConnectionState) {
        val message = when (state) {
            is WebSocketManager.ConnectionState.Connected -> "Connected to ${state.botId}"
            is WebSocketManager.ConnectionState.Connecting -> "Connecting..."
            is WebSocketManager.ConnectionState.Disconnected -> "Disconnected"
            is WebSocketManager.ConnectionState.Error -> "Connection error"
        }

        val notification = createNotification(message)
        val notificationManager = getSystemService(NotificationManager::class.java)
        notificationManager.notify(NOTIFICATION_ID, notification)
    }

    private fun handleEvent(event: WebSocketEvent) {
        when (event) {
            is MessageEvent -> {
                if (event.role == MessageRole.ASSISTANT) {
                    showMessageNotification(event)
                }
            }
            is ApprovalRequiredEvent -> {
                showApprovalNotification(event)
            }
            else -> {
                // Handle other events
            }
        }
    }

    private fun showMessageNotification(event: MessageEvent) {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra("bot_id", event.botId)
        }

        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, NARNAApplication.CHANNEL_MESSAGES)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle("New message")
            .setContentText(event.content.take(100))
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .build()

        val notificationManager = getSystemService(NotificationManager::class.java)
        notificationManager.notify(event.messageId.hashCode(), notification)
    }

    private fun showApprovalNotification(event: ApprovalRequiredEvent) {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra("approval_id", event.approvalId)
        }

        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, NARNAApplication.CHANNEL_APPROVALS)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle("Approval Required")
            .setContentText(event.description)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .build()

        val notificationManager = getSystemService(NotificationManager::class.java)
        notificationManager.notify(event.approvalId.hashCode(), notification)
    }

    private fun createNotification(message: String): Notification {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }

        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, NARNAApplication.CHANNEL_CONNECTION)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle("NARNA")
            .setContentText(message)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        super.onDestroy()
        disconnect()
        serviceScope.cancel()
    }

    companion object {
        const val ACTION_CONNECT = "org.narna.mobile.ACTION_CONNECT"
        const val ACTION_DISCONNECT = "org.narna.mobile.ACTION_DISCONNECT"
        const val EXTRA_BOT_ID = "bot_id"
        private const val NOTIFICATION_ID = 1001
    }
}
