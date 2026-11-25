import { APPLE_ROOT_CA_G3_PEM, APPLE_ROOT_CA_G3_SHA256 } from "./appleRoot.js";
import { bundleId, productConfig } from "./config.js";
import {
  pemToDer,
  sha256Hex,
  parseCertificate,
  importPublicKeyFromSpki,
  verifyChainToRoot,
} from "./x509.js";

function b64urlToBytes(s) {
  const pad = "=".repeat((4 - (s.length % 4)) % 4);
  const b64 = s.replace(/-/g, "+").replace(/_/g, "/") + pad;
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function b64urlToJson(s) {
  const text = new TextDecoder().decode(b64urlToBytes(s));
  return JSON.parse(text);
}

export function parseCompactJws(jws) {
  const raw = String(jws || "").trim();
  const parts = raw.split(".");
  if (parts.length !== 3 || !parts[0] || !parts[1] || !parts[2]) {
    const err = new Error("invalid_jws");
    err.status = 401;
    throw err;
  }
  let header;
  let payload;
  try {
    header = b64urlToJson(parts[0]);
    payload = b64urlToJson(parts[1]);
  } catch {
    const err = new Error("invalid_jws");
    err.status = 401;
    throw err;
  }
  return { raw, parts, header, payload, signingInput: `${parts[0]}.${parts[1]}`, signature: b64urlToBytes(parts[2]) };
}

export async function appleRootDer() {
  const der = pemToDer(APPLE_ROOT_CA_G3_PEM);
  const digest = await sha256Hex(der);
  if (digest !== APPLE_ROOT_CA_G3_SHA256) {
    throw new Error("bundled Apple Root CA - G3 fingerprint mismatch");
  }
  return der;
}

async function verifyX5cAndSignature(parsed, rootDer, now) {
  const x5c = parsed.header.x5c;
  if (!Array.isArray(x5c) || x5c.length === 0) {
    const err = new Error("missing_x5c");
    err.status = 401;
    throw err;
  }
  const ders = x5c.map((b64) => {
    const bin = atob(b64.replace(/\s+/g, ""));
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  });
  const leaf = await verifyChainToRoot(ders, rootDer, now);
  const alg = parsed.header.alg || "ES256";
  const key = await importPublicKeyFromSpki(leaf.spkiDer, alg);
  const hash = alg === "ES384" ? "SHA-384" : "SHA-256";
  const ok = await crypto.subtle.verify(
    { name: "ECDSA", hash },
    key,
    parsed.signature,
    new TextEncoder().encode(parsed.signingInput)
  );
  if (!ok) {
    const err = new Error("jws_signature_invalid");
    err.status = 401;
    throw err;
  }
  return leaf;
}

export function transactionFromPayload(payload, env = {}) {
  const productId = String(payload.productId || payload.product_id || "");
  const bundle = String(payload.bundleId || payload.bundle_id || "");
  const environment = String(payload.environment || "");
  const transactionId = String(payload.transactionId || payload.transaction_id || "");
  const originalTransactionId = String(
    payload.originalTransactionId || payload.original_transaction_id || transactionId
  );
  const expiresDate = payload.expiresDate ?? payload.expires_date ?? null;
  const purchaseDate = payload.purchaseDate ?? payload.purchase_date ?? null;
  const revocationDate = payload.revocationDate ?? payload.revocation_date ?? null;
  expectedBundleCheck(bundle, env);
  if (revocationDate) {
    const err = new Error("subscription_revoked");
    err.status = 403;
    throw err;
  }
  if (!productId || !productConfig(productId, env)) {
    const err = new Error("unknown_product");
    err.status = 403;
    throw err;
  }
  if (expiresDate != null) {
    const exp = Number(expiresDate);
    if (Number.isFinite(exp) && exp < Date.now()) {
      const err = new Error("subscription_expired");
      err.status = 403;
      throw err;
    }
  }
  return {
    productId,
    bundleId: bundle,
    environment,
    transactionId,
    originalTransactionId,
    expiresDate: expiresDate != null ? Number(expiresDate) : null,
    purchaseDate: purchaseDate != null ? Number(purchaseDate) : null,
    raw: payload,
  };
}

function expectedBundleCheck(bundle, env) {
  const expected = bundleId(env);
  if (bundle && bundle !== expected) {
    const err = new Error("bundle_id_mismatch");
    err.status = 401;
    throw err;
  }
}

/**
 * Verify a StoreKit 2 transaction JWS.
 * - Always checks compact JWS shape and payload fields.
 * - Unless env.DEV_ALLOW_UNVERIFIED=1 (local tests only), requires a valid
 *   x5c chain to Apple Root CA - G3 (or env.testRootPem) and a valid signature.
 * - If APPLE_IAP_* secrets are set, also looks up the transaction via the
 *   App Store Server API (production then sandbox).
 */
export async function verifyStoreKitJws(jws, env = {}, now = Date.now()) {
  const parsed = parseCompactJws(jws);
  const unverified = env.DEV_ALLOW_UNVERIFIED === "1";
  if (!unverified) {
    const rootDer = env.testRootDer || (await appleRootDer());
    await verifyX5cAndSignature(parsed, rootDer, now);
  }
  const tx = transactionFromPayload(parsed.payload, env);
  if (env.APPLE_IAP_PRIVATE_KEY && env.APPLE_IAP_KEY_ID && env.APPLE_IAP_ISSUER_ID) {
    const online = await lookupTransaction(tx.transactionId, env);
    if (online) {
      return transactionFromPayload({ ...parsed.payload, ...online }, env);
    }
    // Lookup failed after a valid local JWS: still accept the local payload
    // (App Store Server API may lag for a brand-new purchase).
  }
  return tx;
}

async function lookupTransaction(transactionId, env) {
  if (!transactionId) return null;
  const jwt = await appStoreServerToken(env);
  const hosts = [
    "https://api.storekit.itunes.apple.com",
    "https://api.storekit-sandbox.itunes.apple.com",
  ];
  for (const host of hosts) {
    const res = await fetch(`${host}/inApps/v1/transactions/${encodeURIComponent(transactionId)}`, {
      headers: { Authorization: `Bearer ${jwt}` },
    });
    if (res.status === 404) continue;
    if (!res.ok) continue;
    const body = await res.json().catch(() => null);
    const signed = body && body.signedTransactionInfo;
    if (typeof signed === "string") {
      const inner = parseCompactJws(signed);
      return inner.payload;
    }
  }
  return null;
}

async function appStoreServerToken(env) {
  // ES256 JWT. The .p8 is supplied as a secret PEM; never log it.
  const { SignJWT, importPKCS8 } = await importJoseLite();
  // Avoid a jose dependency: sign with Web Crypto if we can import the PKCS8 key.
  const key = await importPkcs8P256(env.APPLE_IAP_PRIVATE_KEY);
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: "ES256", kid: env.APPLE_IAP_KEY_ID, typ: "JWT" };
  const payload = {
    iss: env.APPLE_IAP_ISSUER_ID,
    iat: now,
    exp: now + 1100,
    aud: "appstoreconnect-v1",
    bid: bundleId(env),
  };
  return signEs256(header, payload, key);
}

// placeholder so a static import of jose is not required
async function importJoseLite() {
  return {};
}

function b64url(bytesOrJson, isJson = false) {
  const bytes = isJson
    ? new TextEncoder().encode(JSON.stringify(bytesOrJson))
    : bytesOrJson instanceof Uint8Array
      ? bytesOrJson
      : new TextEncoder().encode(String(bytesOrJson));
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

async function importPkcs8P256(pem) {
  const der = pemToDer(pem);
  return crypto.subtle.importKey("pkcs8", der, { name: "ECDSA", namedCurve: "P-256" }, false, ["sign"]);
}

async function signEs256(header, payload, key) {
  const data = `${b64url(header, true)}.${b64url(payload, true)}`;
  const sig = new Uint8Array(
    await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, key, new TextEncoder().encode(data))
  );
  return `${data}.${b64url(sig)}`;
}

export { b64url, signEs256, importPkcs8P256, parseCertificate };
