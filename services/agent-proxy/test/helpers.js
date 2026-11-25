import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pemToDer } from "../src/x509.js";
import { b64url, signEs256, importPkcs8P256 } from "../src/jws.js";

export function memoryKv() {
  const m = new Map();
  return {
    async get(k) {
      return m.has(k) ? m.get(k) : null;
    },
    async put(k, v) {
      m.set(k, typeof v === "string" ? v : JSON.stringify(v));
    },
    raw: m,
  };
}

export function agentEnv(overrides = {}) {
  return {
    APPLE_BUNDLE_ID: "org.narna.mobile",
    BASIC_MONTHLY_CREDITS: "200",
    PRO_MONTHLY_CREDITS: "800",
    CREDITS: memoryKv(),
    ...overrides,
  };
}

export async function signTestJws(payload, { key, x5c } = {}) {
  const header = { alg: "ES256", typ: "JWS" };
  if (x5c) header.x5c = x5c;
  return signEs256(header, payload, key);
}

export function samplePayload(over = {}) {
  const now = Date.now();
  return {
    bundleId: "org.narna.mobile",
    productId: "nana.agent.basic.monthly",
    transactionId: "txn-1",
    originalTransactionId: "orig-1",
    environment: "Sandbox",
    purchaseDate: now,
    expiresDate: now + 28 * 24 * 60 * 60 * 1000,
    ...over,
  };
}

/** Mint a P-256 test root + leaf and a WebCrypto signer for the leaf. */
export function mintTestChain() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "nana-jws-"));
  const rootKey = path.join(dir, "root.key");
  const rootCrt = path.join(dir, "root.crt");
  const leafKey = path.join(dir, "leaf.key");
  const leafCrt = path.join(dir, "leaf.crt");
  const leafCsr = path.join(dir, "leaf.csr");
  execFileSync("openssl", ["ecparam", "-name", "prime256v1", "-genkey", "-noout", "-out", rootKey], { stdio: "pipe" });
  execFileSync("openssl", [
    "req", "-new", "-x509", "-key", rootKey, "-out", rootCrt, "-days", "2",
    "-subj", "/CN=Nana Test Root",
  ], { stdio: "pipe" });
  const leafRaw = path.join(dir, "leaf-raw.key");
  execFileSync("openssl", ["ecparam", "-name", "prime256v1", "-genkey", "-noout", "-out", leafRaw], { stdio: "pipe" });
  execFileSync("openssl", ["pkcs8", "-topk8", "-nocrypt", "-in", leafRaw, "-out", leafKey], { stdio: "pipe" });
  execFileSync("openssl", ["req", "-new", "-key", leafKey, "-out", leafCsr, "-subj", "/CN=Nana Test Leaf"], { stdio: "pipe" });
  execFileSync("openssl", [
    "x509", "-req", "-in", leafCsr, "-CA", rootCrt, "-CAkey", rootKey,
    "-CAcreateserial", "-out", leafCrt, "-days", "1",
  ], { stdio: "pipe" });
  const rootPem = fs.readFileSync(rootCrt, "utf8");
  const leafPem = fs.readFileSync(leafCrt, "utf8");
  const leafKeyPem = fs.readFileSync(leafKey, "utf8");
  const leafDer = pemToDer(leafPem);
  const x5c = [btoa(String.fromCharCode(...leafDer))];
  return { dir, rootPem, leafPem, leafKeyPem, rootDer: pemToDer(rootPem), x5c };
}

export async function signerFromPkcs8(pem) {
  return importPkcs8P256(pem);
}

export { b64url };
