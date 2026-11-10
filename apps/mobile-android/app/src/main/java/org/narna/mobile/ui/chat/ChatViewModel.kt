package org.narna.mobile.ui.chat

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import org.narna.mobile.data.api.NARNAApiService
import org.narna.mobile.data.model.*
import org.narna.mobile.data.storage.SecureStorage
import org.narna.mobile.data.websocket.WebSocketManager
import javax.inject.Inject

data class ChatUiState(
    val messages: List<Message> = emptyList(),
    val isLoading: Boolean = false,
    val isSending: Boolean = false,
    val connectionState: WebSocketManager.ConnectionState = WebSocketManager.ConnectionState.Disconnected,
    val error: String? = null,
    val threadId: String? = null,
    val botInfo: BotInfo? = null
)

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val apiService: NARNAApiService,
    private val webSocketManager: WebSocketManager,
    private val secureStorage: SecureStorage,
    savedStateHandle: SavedStateHandle
) : ViewModel() {

    private val botId: String = checkNotNull(savedStateHandle.get<String>("botId"))

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    init {
        loadChatHistory()
        connectWebSocket()
        observeWebSocketEvents()
    }

    private fun loadChatHistory() {
        val mobileToken = secureStorage.getMobileToken() ?: return

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)

            apiService.getBotThread(mobileToken, botId)
                .onSuccess { thread ->
                    _uiState.value = _uiState.value.copy(
                        messages = thread.messages,
                        threadId = thread.threadId,
                        isLoading = false
                    )
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = error.message ?: "Failed to load chat"
                    )
                }
        }
    }

    private fun connectWebSocket() {
        val mobileToken = secureStorage.getMobileToken() ?: return
        webSocketManager.connect(botId, mobileToken, viewModelScope)
    }

    private fun observeWebSocketEvents() {
        viewModelScope.launch {
            webSocketManager.connectionState.collect { state ->
                _uiState.value = _uiState.value.copy(connectionState = state)
            }
        }

        viewModelScope.launch {
            webSocketManager.events.collect { event ->
                handleWebSocketEvent(event)
            }
        }
    }

    private fun handleWebSocketEvent(event: WebSocketEvent) {
        when (event) {
            is MessageEvent -> {
                val newMessage = Message(
                    messageId = event.messageId,
                    role = event.role,
                    content = event.content,
                    createdAt = event.timestamp
                )
                _uiState.value = _uiState.value.copy(
                    messages = _uiState.value.messages + newMessage
                )
            }
            is StatusEvent -> {
                // Update bot status if needed
            }
            is ErrorEvent -> {
                _uiState.value = _uiState.value.copy(
                    error = event.error
                )
            }
            else -> {
                // Handle other events
            }
        }
    }

    fun sendMessage(content: String) {
        if (content.isBlank()) return

        val mobileToken = secureStorage.getMobileToken() ?: return

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSending = true)

            // Optimistically add user message
            val userMessage = Message(
                messageId = "temp_${System.currentTimeMillis()}",
                role = MessageRole.USER,
                content = content,
                createdAt = java.time.Instant.now().toString()
            )
            _uiState.value = _uiState.value.copy(
                messages = _uiState.value.messages + userMessage
            )

            apiService.sendMessage(
                mobileToken = mobileToken,
                botId = botId,
                message = content,
                threadId = _uiState.value.threadId
            )
                .onSuccess { response ->
                    _uiState.value = _uiState.value.copy(
                        threadId = response.threadId,
                        isSending = false
                    )
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        isSending = false,
                        error = error.message ?: "Failed to send message"
                    )
                }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    override fun onCleared() {
        super.onCleared()
        webSocketManager.disconnect()
    }
}
