package org.narna.mobile.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class PairingStartRequest(
    @SerialName("device_name") val deviceName: String? = null,
    val platform: String = "android"
)

@Serializable
data class PairingStartResponse(
    @SerialName("pairing_code") val pairingCode: String,
    @SerialName("qr_data") val qrData: String,
    @SerialName("expires_at") val expiresAt: String
)

@Serializable
data class PairingVerifyRequest(
    @SerialName("pairing_code") val pairingCode: String
)

@Serializable
data class PairingVerifyResponse(
    @SerialName("mobile_token") val mobileToken: String,
    @SerialName("agent_name") val agentName: String,
    @SerialName("org_id") val orgId: Int
)

@Serializable
data class PairingRevokeRequest(
    @SerialName("mobile_token") val mobileToken: String
)

@Serializable
data class PairingRevokeResponse(
    val ok: Boolean,
    @SerialName("revoked_at") val revokedAt: String
)
