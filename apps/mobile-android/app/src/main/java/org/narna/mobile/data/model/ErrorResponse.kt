package org.narna.mobile.data.model

import kotlinx.serialization.Serializable

@Serializable
data class ErrorResponse(
    val detail: String
)
