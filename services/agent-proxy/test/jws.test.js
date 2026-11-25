import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { APPLE_ROOT_CA_G3_PEM, APPLE_ROOT_CA_G3_SHA256 } from "../src/appleRoot.js";
import { appleRootDer, parseCompactJws, verifyStoreKitJws } from "../src/jws.js";
import { pemToDer, sha256Hex, parseCertificate } from "../src/x509.js";
import { mintTestChain, samplePayload, signTestJws, signerFromPkcs8 } from "./helpers.js";

describe("Apple root bundle", () => {
  it("matches the official SHA-256 fingerprint and parses", async () => {
    const der = await appleRootDer();
    assert.equal(await sha256Hex(der), APPLE_ROOT_CA_G3_SHA256);
    const cert = parseCertificate(der);
    assert.ok(cert.notAfter > Date.now());
    assert.equal(await sha256Hex(pemToDer(APPLE_ROOT_CA_G3_PEM)), APPLE_ROOT_CA_G3_SHA256);
  });
});

describe("JWS verify", () => {
  it("rejects malformed tokens", async () => {
    await assert.rejects(() => verifyStoreKitJws("not-a-jws", {}), /invalid_jws/);
    await assert.rejects(() => verifyStoreKitJws("a.b", {}), /invalid_jws/);
  });

  it("rejects unsigned payload without DEV_ALLOW_UNVERIFIED", async () => {
    const keyPair = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]);
    const jws = await signTestJws(samplePayload(), { key: keyPair.privateKey });
    await assert.rejects(() => verifyStoreKitJws(jws, {}), /missing_x5c/);
  });

  it("accepts a payload only when DEV_ALLOW_UNVERIFIED=1 (tests)", async () => {
    const keyPair = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]);
    const jws = await signTestJws(samplePayload(), { key: keyPair.privateKey });
    const tx = await verifyStoreKitJws(jws, { DEV_ALLOW_UNVERIFIED: "1" });
    assert.equal(tx.productId, "nana.agent.basic.monthly");
    assert.equal(tx.originalTransactionId, "orig-1");
  });

  it("rejects expired or unknown products even in unverified mode", async () => {
    const keyPair = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]);
    const expired = await signTestJws(samplePayload({ expiresDate: Date.now() - 1000 }), { key: keyPair.privateKey });
    await assert.rejects(
      () => verifyStoreKitJws(expired, { DEV_ALLOW_UNVERIFIED: "1" }),
      /subscription_expired/
    );
    const unknown = await signTestJws(samplePayload({ productId: "other.sku" }), { key: keyPair.privateKey });
    await assert.rejects(
      () => verifyStoreKitJws(unknown, { DEV_ALLOW_UNVERIFIED: "1" }),
      /unknown_product/
    );
  });

  it("verifies x5c against a test root", async () => {
    const chain = mintTestChain();
    const key = await signerFromPkcs8(chain.leafKeyPem);
    const jws = await signTestJws(samplePayload(), { key, x5c: chain.x5c });
    const parsed = parseCompactJws(jws);
    assert.ok(parsed.header.x5c);
    const tx = await verifyStoreKitJws(jws, { testRootDer: chain.rootDer });
    assert.equal(tx.productId, "nana.agent.basic.monthly");
  });

  it("rejects a JWS whose x5c chain does not reach the Apple (or test) root", async () => {
    const a = mintTestChain();
    const b = mintTestChain();
    const key = await signerFromPkcs8(a.leafKeyPem);
    const jws = await signTestJws(samplePayload(), { key, x5c: a.x5c });
    await assert.rejects(() => verifyStoreKitJws(jws, { testRootDer: b.rootDer }), /mismatch|terminate|signature/i);
  });
});
