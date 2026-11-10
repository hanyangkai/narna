package org.narna.mobile.data.billing

import android.app.Activity
import android.content.Context
import com.android.billingclient.api.*
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.suspendCancellableCoroutine
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.coroutines.resume

data class PlayPurchaseResult(
    val productId: String,
    val purchaseToken: String,
    val orderId: String?,
    val acknowledged: Boolean
)

@Singleton
class PlayBillingManager @Inject constructor(
    @ApplicationContext private val context: Context
) : PurchasesUpdatedListener {

    private var billingClient: BillingClient? = null

    private val _ready = MutableStateFlow(false)
    val ready: StateFlow<Boolean> = _ready.asStateFlow()

    private val _lastError = MutableStateFlow<String?>(null)
    val lastError: StateFlow<String?> = _lastError.asStateFlow()

    private var pendingPurchaseCallback: ((Result<PlayPurchaseResult>) -> Unit)? = null

    fun startConnection() {
        if (billingClient?.isReady == true) {
            _ready.value = true
            return
        }
        val client = BillingClient.newBuilder(context)
            .setListener(this)
            .enablePendingPurchases()
            .build()
        billingClient = client
        client.startConnection(object : BillingClientStateListener {
            override fun onBillingSetupFinished(billingResult: BillingResult) {
                if (billingResult.responseCode == BillingClient.BillingResponseCode.OK) {
                    _ready.value = true
                    _lastError.value = null
                } else {
                    _ready.value = false
                    _lastError.value = billingResult.debugMessage.ifBlank {
                        "Play Billing unavailable (${billingResult.responseCode})"
                    }
                }
            }

            override fun onBillingServiceDisconnected() {
                _ready.value = false
            }
        })
    }

    suspend fun querySubscriptionDetails(productIds: List<String>): List<ProductDetails> {
        val client = billingClient ?: return emptyList()
        if (!client.isReady || productIds.isEmpty()) return emptyList()

        val productList = productIds.map { id ->
            QueryProductDetailsParams.Product.newBuilder()
                .setProductId(id)
                .setProductType(BillingClient.ProductType.SUBS)
                .build()
        }
        val params = QueryProductDetailsParams.newBuilder()
            .setProductList(productList)
            .build()

        return suspendCancellableCoroutine { cont ->
            client.queryProductDetailsAsync(params) { billingResult, detailsList ->
                if (billingResult.responseCode == BillingClient.BillingResponseCode.OK) {
                    cont.resume(detailsList.orEmpty())
                } else {
                    _lastError.value = billingResult.debugMessage
                    cont.resume(emptyList())
                }
            }
        }
    }

    fun launchSubscriptionPurchase(
        activity: Activity,
        productDetails: ProductDetails,
        onResult: (Result<PlayPurchaseResult>) -> Unit
    ) {
        val client = billingClient
        if (client == null || !client.isReady) {
            onResult(Result.failure(IllegalStateException("Google Play Billing is not available")))
            return
        }
        val offerToken = productDetails.subscriptionOfferDetails
            ?.firstOrNull()
            ?.offerToken
        if (offerToken.isNullOrBlank()) {
            onResult(Result.failure(IllegalStateException("No Play subscription offer for ${productDetails.productId}")))
            return
        }

        pendingPurchaseCallback = onResult
        val productParams = BillingFlowParams.ProductDetailsParams.newBuilder()
            .setProductDetails(productDetails)
            .setOfferToken(offerToken)
            .build()
        val flowParams = BillingFlowParams.newBuilder()
            .setProductDetailsParamsList(listOf(productParams))
            .build()
        val result = client.launchBillingFlow(activity, flowParams)
        if (result.responseCode != BillingClient.BillingResponseCode.OK) {
            pendingPurchaseCallback = null
            onResult(Result.failure(IllegalStateException(result.debugMessage.ifBlank {
                "Unable to open Google Play purchase sheet"
            })))
        }
    }

    override fun onPurchasesUpdated(billingResult: BillingResult, purchases: MutableList<Purchase>?) {
        val callback = pendingPurchaseCallback
        pendingPurchaseCallback = null
        when (billingResult.responseCode) {
            BillingClient.BillingResponseCode.OK -> {
                val purchase = purchases?.firstOrNull()
                if (purchase == null) {
                    callback?.invoke(Result.failure(IllegalStateException("No purchase returned")))
                    return
                }
                callback?.invoke(
                    Result.success(
                        PlayPurchaseResult(
                            productId = purchase.products.firstOrNull().orEmpty(),
                            purchaseToken = purchase.purchaseToken,
                            orderId = purchase.orderId,
                            acknowledged = purchase.isAcknowledged
                        )
                    )
                )
            }
            BillingClient.BillingResponseCode.USER_CANCELED -> {
                callback?.invoke(Result.failure(IllegalStateException("Purchase canceled")))
            }
            else -> {
                callback?.invoke(
                    Result.failure(
                        IllegalStateException(
                            billingResult.debugMessage.ifBlank {
                                "Purchase failed (${billingResult.responseCode})"
                            }
                        )
                    )
                )
            }
        }
    }

    fun endConnection() {
        billingClient?.endConnection()
        billingClient = null
        _ready.value = false
    }
}
