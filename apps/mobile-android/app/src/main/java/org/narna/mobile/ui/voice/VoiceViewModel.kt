package org.narna.mobile.ui.voice

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import org.narna.mobile.data.api.NARNAApiService
import org.narna.mobile.data.model.VoiceStartRequest
import org.narna.mobile.data.storage.SecureStorage
import javax.inject.Inject

data class TranscriptLine(
    val id: String,
    val speaker: String,
    val text: String
)

data class VoiceUiState(
    val isLive: Boolean = false,
    val isBusy: Boolean = false,
    val sessionId: String? = null,
    val botId: String = "bot_1",
    val note: String? = null,
    val micEnabled: Boolean = true,
    val transcript: List<TranscriptLine> = emptyList(),
    val error: String? = null
)

@HiltViewModel
class VoiceViewModel @Inject constructor(
    private val apiService: NARNAApiService,
    private val secureStorage: SecureStorage
) : ViewModel() {

    private val _uiState = MutableStateFlow(VoiceUiState())
    val uiState: StateFlow<VoiceUiState> = _uiState.asStateFlow()

    fun setBotId(botId: String) {
        _uiState.value = _uiState.value.copy(botId = botId)
    }

    fun toggleMic() {
        _uiState.value = _uiState.value.copy(micEnabled = !_uiState.value.micEnabled)
    }

    fun startCall() {
        val token = secureStorage.getMobileToken() ?: return
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isBusy = true, error = null)
            val voiceKey = secureStorage.getOpenAIVoiceKey()
            apiService.startVoice(
                token,
                VoiceStartRequest(
                    botId = _uiState.value.botId.ifBlank { "bot_1" },
                    openaiApiKey = voiceKey
                )
            )
                .onSuccess { session ->
                    _uiState.value = _uiState.value.copy(
                        isBusy = false,
                        isLive = true,
                        sessionId = session.sessionId,
                        note = session.note,
                        transcript = listOf(
                            TranscriptLine(
                                id = "sys_1",
                                speaker = "System",
                                text = session.note
                            ),
                            TranscriptLine(
                                id = "placeholder_1",
                                speaker = "Bot",
                                text = "Listening… (transcript placeholder — wire OpenAI Realtime next)"
                            )
                        )
                    )
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        isBusy = false,
                        error = error.message ?: "Failed to start voice session"
                    )
                }
        }
    }

    fun endCall() {
        val token = secureStorage.getMobileToken() ?: return
        val sessionId = _uiState.value.sessionId ?: run {
            _uiState.value = VoiceUiState(botId = _uiState.value.botId)
            return
        }
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isBusy = true, error = null)
            apiService.stopVoice(token, sessionId)
                .onSuccess {
                    _uiState.value = VoiceUiState(
                        botId = _uiState.value.botId,
                        note = "Call ended",
                        transcript = _uiState.value.transcript + TranscriptLine(
                            id = "sys_end",
                            speaker = "System",
                            text = "Call ended"
                        )
                    )
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        isBusy = false,
                        isLive = false,
                        sessionId = null,
                        error = error.message ?: "Failed to stop voice session"
                    )
                }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}
