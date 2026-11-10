package org.narna.mobile.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// ── Onboarding status ──

@Serializable
data class OnboardingStatusResponse(
    val ok: Boolean = true,
    val paired: Boolean = false,
    val plan: String = "free",
    @SerialName("org_id") val orgId: Int? = null,
    @SerialName("ai_ready") val aiReady: Boolean = false,
    @SerialName("needs_onboarding") val needsOnboarding: Boolean = true,
    val paths: List<OnboardingPath> = emptyList(),
    val providers: List<AiProviderInfo> = emptyList(),
    val pairing: OnboardingPairingHint? = null,
    @SerialName("billing_policy") val billingPolicy: BillingPolicyHint? = null
)

@Serializable
data class OnboardingPath(
    val id: String,
    val title: String,
    val subtitle: String,
    val recommended: Boolean = false,
    val steps: List<String> = emptyList(),
    val cta: String,
    val products: List<OnboardingPathProduct> = emptyList()
)

@Serializable
data class OnboardingPathProduct(
    @SerialName("product_id") val productId: String,
    val plan: String,
    val price: String,
    val period: String
)

@Serializable
data class OnboardingPairingHint(
    val how: String? = null,
    @SerialName("desktop_command") val desktopCommand: String? = null
)

@Serializable
data class BillingPolicyHint(
    val mobile: String? = null,
    val web: String? = null,
    @SerialName("model_tokens") val modelTokens: String? = null
)

// ── AI providers ──

@Serializable
data class AiProvidersResponse(
    val ok: Boolean = true,
    @SerialName("default_provider") val defaultProvider: String? = null,
    val providers: List<AiProviderInfo> = emptyList(),
    val note: String? = null
)

@Serializable
data class AiProviderInfo(
    val id: String,
    val name: String,
    val modes: List<String> = emptyList(),
    val hint: String? = null,
    val env: String? = null,
    val connected: Boolean = false,
    @SerialName("masked_key") val maskedKey: String? = null
)

@Serializable
data class AiProviderConfigureRequest(
    @SerialName("api_key") val apiKey: String,
    @SerialName("set_as_default") val setAsDefault: Boolean = true,
    val model: String? = null
)

@Serializable
data class AiProviderConfigureResponse(
    val ok: Boolean = true,
    val provider: String? = null,
    val connected: Boolean = false,
    @SerialName("masked_key") val maskedKey: String? = null,
    @SerialName("default_provider") val defaultProvider: String? = null,
    val message: String? = null
)

@Serializable
data class AiProviderClearResponse(
    val ok: Boolean = true,
    val provider: String? = null,
    val connected: Boolean = false
)

// ── Subscription products ──

@Serializable
data class SubscriptionProductsResponse(
    val ok: Boolean = true,
    @SerialName("store_only") val storeOnly: Boolean = true,
    @SerialName("crypto_in_app") val cryptoInApp: Boolean = false,
    val products: List<SubscriptionProduct> = emptyList(),
    @SerialName("manage_urls") val manageUrls: ManageSubscriptionUrls? = null
)

@Serializable
data class SubscriptionProduct(
    @SerialName("product_id") val productId: String,
    val plan: String,
    val title: String,
    val price: String,
    val period: String,
    val includes: List<String> = emptyList()
)

@Serializable
data class ManageSubscriptionUrls(
    val ios: String? = null,
    val android: String? = null
)

// ── Store verify ──

@Serializable
data class StoreVerifyRequest(
    val platform: String = "android",
    @SerialName("product_id") val productId: String,
    @SerialName("transaction_id") val transactionId: String,
    @SerialName("receipt_data") val receiptData: String? = null,
    @SerialName("purchase_token") val purchaseToken: String? = null
)

@Serializable
data class StoreVerifyResponse(
    val ok: Boolean = true,
    val plan: String? = null,
    @SerialName("plan_expires_at") val planExpiresAt: String? = null,
    @SerialName("product_id") val productId: String? = null,
    val verified: Boolean = false,
    @SerialName("verification_mode") val verificationMode: String? = null,
    val message: String? = null
)
