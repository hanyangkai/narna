package org.narna.mobile.data.websocket

import android.util.Log
import io.ktor.client.*
import io.ktor.client.plugins.websocket.*
import io.ktor.websocket.*
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.narna.mobile.data.model.*
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class WebSocketManager @Inject constructor(
    private val baseUrl: String
) {
    private val TAG = "WebSocketManager"
    
    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
    }

    private val client = HttpClient {
        install(WebSockets) {
            pingInterval = 30_000
            maxFrameSize = Long.MAX_VALUE
        }
    }

    private var currentSession: DefaultClientWebSocketSession? = null
    private var connectionJob: Job? = null
    
    private val _events = MutableSharedFlow<WebSocketEvent>(
        replay = 0,
        extraBufferCapacity = 64,
        onBufferOverflow = kotlinx.coroutines.channels.BufferOverflow.DROP_OLDEST
    )
    val events: SharedFlow<WebSocketEvent> = _events.asSharedFlow()

    private val _connectionState = MutableStateFlow<ConnectionState>(ConnectionState.Disconnected)
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()

    sealed class ConnectionState {
        object Disconnected : ConnectionState()
        object Connecting : ConnectionState()
        data class Connected(val botId: String) : ConnectionState()
        data class Error(val message: String) : ConnectionState()
    }

    fun connect(botId: String, mobileToken: String, scope: CoroutineScope) {
        if (connectionJob?.isActive == true) {
            Log.d(TAG, "Already connected or connecting")
            return
        }

        connectionJob = scope.launch {
            connectWithRetry(botId, mobileToken)
        }
    }

    private suspend fun connectWithRetry(botId: String, mobileToken: String) {
        var retryCount = 0
        val maxRetries = 5
        val baseDelay = 2000L

        while (retryCount < maxRetries) {
            try {
                _connectionState.value = ConnectionState.Connecting
                
                val wsUrl = baseUrl
                    .replace("http://", "ws://")
                    .replace("https://", "wss://")
                
                Log.d(TAG, "Connecting to: $wsUrl/v1/mobile/bots/$botId/stream")

                client.webSocket(
                    urlString = "$wsUrl/v1/mobile/bots/$botId/stream?mobile_token=$mobileToken"
                ) {
                    currentSession = this
                    _connectionState.value = ConnectionState.Connected(botId)
                    Log.d(TAG, "WebSocket connected")

                    try {
                        for (frame in incoming) {
                            when (frame) {
                                is Frame.Text -> {
                                    val text = frame.readText()
                                    Log.d(TAG, "Received: $text")
                                    handleMessage(text)
                                }
                                is Frame.Close -> {
                                    Log.d(TAG, "WebSocket closed")
                                    _connectionState.value = ConnectionState.Disconnected
                                    break
                                }
                                else -> {
                                    // Ignore binary, ping, pong frames
                                }
                            }
                        }
                    } catch (e: Exception) {
                        Log.e(TAG, "Error reading frames", e)
                        throw e
                    }
                }
                
                // Connection closed normally
                break
                
            } catch (e: Exception) {
                Log.e(TAG, "WebSocket error (attempt ${retryCount + 1})", e)
                _connectionState.value = ConnectionState.Error(e.message ?: "Connection failed")
                
                retryCount++
                if (retryCount < maxRetries) {
                    val delay = baseDelay * (1 shl retryCount) // Exponential backoff
                    Log.d(TAG, "Retrying in ${delay}ms...")
                    delay(delay)
                } else {
                    Log.e(TAG, "Max retries reached")
                    _connectionState.value = ConnectionState.Disconnected
                    break
                }
            } finally {
                currentSession = null
            }
        }
    }

    private suspend fun handleMessage(text: String) {
        try {
            // Parse the event type first
            val jsonElement = json.parseToJsonElement(text)
            val eventType = jsonElement.jsonObject["type"]?.jsonPrimitive?.content

            val event: WebSocketEvent? = when (eventType) {
                "connected" -> json.decodeFromString<ConnectedEvent>(text)
                "status" -> json.decodeFromString<StatusEvent>(text)
                "message" -> json.decodeFromString<MessageEvent>(text)
                "approval_required" -> json.decodeFromString<ApprovalRequiredEvent>(text)
                "tool_execution" -> json.decodeFromString<ToolExecutionEvent>(text)
                "error" -> json.decodeFromString<ErrorEvent>(text)
                "pong" -> null // Ignore pong responses
                else -> {
                    Log.w(TAG, "Unknown event type: $eventType")
                    null
                }
            }

            event?.let { _events.emit(it) }
            
        } catch (e: Exception) {
            Log.e(TAG, "Error parsing message: $text", e)
        }
    }

    suspend fun send(message: String) {
        try {
            currentSession?.send(Frame.Text(message))
        } catch (e: Exception) {
            Log.e(TAG, "Error sending message", e)
        }
    }

    fun disconnect() {
        connectionJob?.cancel()
        connectionJob = null
        currentSession = null
        _connectionState.value = ConnectionState.Disconnected
        Log.d(TAG, "WebSocket disconnected")
    }

    fun close() {
        disconnect()
        client.close()
    }
}
