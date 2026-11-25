import { productConfig, requestCost } from "./config.js";

function periodStartMs(tx, now = Date.now()) {
  const expires = tx.expiresDate != null ? Number(tx.expiresDate) : null;
  if (expires && Number.isFinite(expires)) {
    // Monthly auto-renew: period is the 31 days (or calendar month) ending at expiresDate.
    const start = expires - 31 * 24 * 60 * 60 * 1000;
    return start > 0 ? start : expires - 30 * 24 * 60 * 60 * 1000;
  }
  const purchased = tx.purchaseDate != null ? Number(tx.purchaseDate) : now;
  return purchased;
}

export function creditKey(tx, now = Date.now()) {
  const id = tx.originalTransactionId || tx.transactionId;
  const start = periodStartMs(tx, now);
  return `credits:${id}:${start}`;
}

export async function readLedger(env, key) {
  if (!env.CREDITS) return null;
  const raw = await env.CREDITS.get(key);
  if (!raw) return null;
  try {
    return typeof raw === "string" ? JSON.parse(raw) : raw;
  } catch {
    return null;
  }
}

export async function writeLedger(env, key, value) {
  if (!env.CREDITS) {
    const err = new Error("credits_store_missing");
    err.status = 503;
    throw err;
  }
  await env.CREDITS.put(key, JSON.stringify(value));
}

/**
 * Reserve credits for a request. Returns { remaining, cost, cap }.
 * Throws 403 if not a known plan, 429 if exhausted.
 */
export async function consumeCredits(env, tx, request, now = Date.now()) {
  const plan = productConfig(tx.productId, env);
  if (!plan) {
    const err = new Error("unknown_product");
    err.status = 403;
    throw err;
  }
  const cost = requestCost({
    webSearch: Boolean(request && request.webSearch),
    hasFile: Boolean(request && (request.fileBase64 || request.fileName)),
  });
  const key = creditKey(tx, now);
  const existing = await readLedger(env, key);
  const remaining = existing && Number.isFinite(existing.remaining)
    ? existing.remaining
    : plan.credits;
  if (remaining < cost) {
    const err = new Error("credits_exhausted");
    err.status = 429;
    err.creditsRemaining = remaining;
    throw err;
  }
  const next = remaining - cost;
  await writeLedger(env, key, {
    remaining: next,
    cap: plan.credits,
    productId: tx.productId,
    originalTransactionId: tx.originalTransactionId,
    updatedAt: now,
  });
  return { remaining: next, cost, cap: plan.credits, key };
}

/** Refund credits if the upstream call failed after a reserve. */
export async function refundCredits(env, key, cost, now = Date.now()) {
  const existing = await readLedger(env, key);
  if (!existing) return;
  existing.remaining = (existing.remaining || 0) + cost;
  existing.updatedAt = now;
  await writeLedger(env, key, existing);
}
