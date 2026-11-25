// Minimal X.509 + Web Crypto helpers for StoreKit JWS chain checks.
// Supports ECDSA P-256 / P-384 and RSA PKCS#1 SHA-256.

const OID = {
  sha256: "2.16.840.1.101.3.4.2.1",
  sha384: "2.16.840.1.101.3.4.2.2",
  ecdsaSha256: "1.2.840.10045.4.3.2",
  ecdsaSha384: "1.2.840.10045.4.3.3",
  sha256WithRSA: "1.2.840.113549.1.1.11",
  ecPublicKey: "1.2.840.10045.2.1",
  p256: "1.2.840.10045.3.1.7",
  p384: "1.3.132.0.34",
  rsaEncryption: "1.2.840.113549.1.1.1",
};

export function pemToDer(pem) {
  const b64 = String(pem)
    .replace(/-----BEGIN [^-]+-----/g, "")
    .replace(/-----END [^-]+-----/g, "")
    .replace(/\s+/g, "");
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

export function derToPem(der, label = "CERTIFICATE") {
  const b64 = btoa(String.fromCharCode(...derToBytes(der)));
  const lines = b64.match(/.{1,64}/g) || [];
  return `-----BEGIN ${label}-----\n${lines.join("\n")}\n-----END ${label}-----\n`;
}

function derToBytes(der) {
  return der instanceof Uint8Array ? der : new Uint8Array(der);
}

export async function sha256Hex(data) {
  const buf = await crypto.subtle.digest("SHA-256", derToBytes(data));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function readLen(bytes, i) {
  const first = bytes[i];
  if (first < 0x80) return { len: first, off: i + 1 };
  const n = first & 0x7f;
  let len = 0;
  for (let k = 0; k < n; k++) len = (len << 8) | bytes[i + 1 + k];
  return { len, off: i + 1 + n };
}

function readTLV(bytes, i) {
  const tag = bytes[i];
  const { len, off } = readLen(bytes, i + 1);
  const start = off;
  const end = off + len;
  return { tag, start, end, headerStart: i, value: bytes.subarray(start, end), next: end };
}

function expectSeq(bytes, i = 0) {
  const t = readTLV(bytes, i);
  if (t.tag !== 0x30) throw new Error("expected SEQUENCE");
  return t;
}

function decodeOid(bytes) {
  if (!bytes.length) return "";
  const first = bytes[0];
  const parts = [Math.floor(first / 40), first % 40];
  let acc = 0;
  for (let i = 1; i < bytes.length; i++) {
    acc = (acc << 7) | (bytes[i] & 0x7f);
    if ((bytes[i] & 0x80) === 0) {
      parts.push(acc);
      acc = 0;
    }
  }
  return parts.join(".");
}

function parseAlgoOid(bytes) {
  // Accept a full AlgorithmIdentifier SEQUENCE or its already-unwrapped value.
  let view = bytes;
  if (bytes[0] === 0x30) {
    view = expectSeq(bytes, 0).value;
  }
  const oid = readTLV(view, 0);
  if (oid.tag !== 0x06) throw new Error("expected OID");
  return decodeOid(oid.value);
}

function findSpki(tbsValue) {
  // TBSCertificate: version? serial signature issuer validity subject subjectPublicKeyInfo ...
  let i = 0;
  const first = readTLV(tbsValue, 0);
  // optional version [0]
  if (first.tag === 0xa0) i = first.next;
  // serial
  i = readTLV(tbsValue, i).next;
  // signature algo
  i = readTLV(tbsValue, i).next;
  // issuer
  i = readTLV(tbsValue, i).next;
  // validity
  i = readTLV(tbsValue, i).next;
  // subject
  i = readTLV(tbsValue, i).next;
  // spki
  const spki = readTLV(tbsValue, i);
  if (spki.tag !== 0x30) throw new Error("expected SPKI SEQUENCE");
  return { spkiDer: tbsValue.subarray(spki.headerStart, spki.end), next: spki.next };
}

function parseValidity(tbsValue) {
  let i = 0;
  const first = readTLV(tbsValue, 0);
  if (first.tag === 0xa0) i = first.next;
  i = readTLV(tbsValue, i).next; // serial
  i = readTLV(tbsValue, i).next; // sig
  i = readTLV(tbsValue, i).next; // issuer
  const validity = readTLV(tbsValue, i);
  const notBefore = readTLV(validity.value, 0);
  const notAfter = readTLV(validity.value, notBefore.next);
  return { notBefore: parseTime(notBefore), notAfter: parseTime(notAfter) };
}

function parseTime(tlv) {
  const s = new TextDecoder("ascii").decode(tlv.value);
  if (tlv.tag === 0x17) {
    // UTCTime YYMMDDHHMMSSZ
    const yy = Number(s.slice(0, 2));
    const year = yy >= 50 ? 1900 + yy : 2000 + yy;
    return Date.UTC(year, Number(s.slice(2, 4)) - 1, Number(s.slice(4, 6)), Number(s.slice(6, 8)), Number(s.slice(8, 10)), Number(s.slice(10, 12)));
  }
  if (tlv.tag === 0x18) {
    const year = Number(s.slice(0, 4));
    return Date.UTC(year, Number(s.slice(4, 6)) - 1, Number(s.slice(6, 8)), Number(s.slice(8, 10)), Number(s.slice(10, 12)), Number(s.slice(12, 14)));
  }
  throw new Error("unsupported time tag");
}

function issuerSubjectDer(tbsValue, which) {
  let i = 0;
  const first = readTLV(tbsValue, 0);
  if (first.tag === 0xa0) i = first.next;
  i = readTLV(tbsValue, i).next; // serial
  i = readTLV(tbsValue, i).next; // sig
  const issuer = readTLV(tbsValue, i);
  i = issuer.next;
  i = readTLV(tbsValue, i).next; // validity
  const subject = readTLV(tbsValue, i);
  const node = which === "issuer" ? issuer : subject;
  return tbsValue.subarray(node.headerStart, node.end);
}

export function parseCertificate(der) {
  const bytes = derToBytes(der);
  const cert = expectSeq(bytes, 0);
  const tbs = readTLV(cert.value, 0);
  if (tbs.tag !== 0x30) throw new Error("expected tbs SEQUENCE");
  const sigAlg = readTLV(cert.value, tbs.next);
  const sigBit = readTLV(cert.value, sigAlg.next);
  if (sigBit.tag !== 0x03) throw new Error("expected BIT STRING signature");
  // BIT STRING: first byte is unused bits (usually 0)
  const unused = sigBit.value[0];
  const signature = sigBit.value.subarray(1);
  if (unused !== 0) {
    // still usable for ECDSA DER
  }
  const tbsDer = cert.value.subarray(tbs.headerStart, tbs.end);
  const { spkiDer } = findSpki(tbs.value);
  const { notBefore, notAfter } = parseValidity(tbs.value);
  return {
    der: bytes.subarray(cert.headerStart, cert.end),
    tbsDer,
    signature,
    signatureOid: parseAlgoOid(sigAlg.value),
    spkiDer,
    notBefore,
    notAfter,
    issuerDer: issuerSubjectDer(tbs.value, "issuer"),
    subjectDer: issuerSubjectDer(tbs.value, "subject"),
  };
}

function sameDer(a, b) {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
  return true;
}

function parseSpkiMeta(spkiDer) {
  const seq = expectSeq(spkiDer, 0);
  const alg = readTLV(seq.value, 0);
  const algView = alg.tag === 0x30 ? alg.value : alg.value;
  const algOid = parseAlgoOid(algView);
  let curve = null;
  const view = algView[0] === 0x30 ? expectSeq(algView, 0).value : algView;
  const oidTlv = readTLV(view, 0);
  if (oidTlv.next < view.length) {
    const maybeParams = readTLV(view, oidTlv.next);
    if (maybeParams.tag === 0x06) curve = decodeOid(maybeParams.value);
  }
  return { algOid, curve };
}

function derEcdsaToRaw(sig, size) {
  // SEQUENCE { INTEGER r, INTEGER s } → raw r||s
  const seq = expectSeq(sig, 0);
  const r = readTLV(seq.value, 0);
  const s = readTLV(seq.value, r.next);
  if (r.tag !== 0x02 || s.tag !== 0x02) throw new Error("bad ECDSA sig");
  const pad = (intBytes) => {
    let v = intBytes;
    // strip leading zeros, then left-pad
    while (v.length > size && v[0] === 0) v = v.subarray(1);
    if (v.length > size) throw new Error("ECDSA integer too large");
    const out = new Uint8Array(size);
    out.set(v, size - v.length);
    return out;
  };
  const raw = new Uint8Array(size * 2);
  raw.set(pad(r.value), 0);
  raw.set(pad(s.value), size);
  return raw;
}

async function importSpki(spkiDer, usage = ["verify"]) {
  const meta = parseSpkiMeta(spkiDer);
  if (meta.algOid === OID.ecPublicKey || meta.curve === OID.p256 || meta.curve === OID.p384) {
    const namedCurve = meta.curve === OID.p384 ? "P-384" : "P-256";
    const algo = { name: "ECDSA", namedCurve };
    const key = await crypto.subtle.importKey("spki", spkiDer, algo, false, usage);
    return { key, kind: "ecdsa", namedCurve };
  }
  if (meta.algOid === OID.rsaEncryption || meta.algOid === OID.sha256WithRSA) {
    const key = await crypto.subtle.importKey(
      "spki",
      spkiDer,
      { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
      false,
      usage
    );
    return { key, kind: "rsa" };
  }
  throw new Error(`unsupported SPKI ${meta.algOid} curve=${meta.curve}`);
}

export async function importPublicKeyFromSpki(spkiDer, jwsAlg = "ES256") {
  if (jwsAlg === "ES256") {
    return crypto.subtle.importKey("spki", spkiDer, { name: "ECDSA", namedCurve: "P-256" }, false, ["verify"]);
  }
  if (jwsAlg === "ES384") {
    return crypto.subtle.importKey("spki", spkiDer, { name: "ECDSA", namedCurve: "P-384" }, false, ["verify"]);
  }
  throw new Error(`unsupported JWS alg ${jwsAlg}`);
}

export async function verifyCertificateSignature(cert, issuerSpkiDer, now = Date.now()) {
  if (now < cert.notBefore - 60_000 || now > cert.notAfter + 60_000) {
    throw new Error("certificate expired or not yet valid");
  }
  const imported = await importSpki(issuerSpkiDer);
  let ok = false;
  if (cert.signatureOid === OID.ecdsaSha256 || cert.signatureOid === OID.ecdsaSha384) {
    const hash = cert.signatureOid === OID.ecdsaSha384 ? "SHA-384" : "SHA-256";
    const size = hash === "SHA-384" ? 48 : 32;
    // P-384 signatures are 48-byte integers even if hash is sha384; size follows curve
    const sigSize = imported.namedCurve === "P-384" ? 48 : 32;
    const raw = derEcdsaToRaw(cert.signature, sigSize);
    ok = await crypto.subtle.verify({ name: "ECDSA", hash }, imported.key, raw, cert.tbsDer);
  } else if (cert.signatureOid === OID.sha256WithRSA) {
    ok = await crypto.subtle.verify({ name: "RSASSA-PKCS1-v1_5" }, imported.key, cert.signature, cert.tbsDer);
  } else {
    throw new Error(`unsupported cert signature OID ${cert.signatureOid}`);
  }
  if (!ok) throw new Error("certificate signature mismatch");
}

export async function verifyChainToRoot(x5cDers, rootDer, now = Date.now()) {
  if (!x5cDers.length) throw new Error("empty x5c");
  const certs = x5cDers.map(parseCertificate);
  const root = parseCertificate(rootDer);
  // Append root if the chain does not already include it.
  const last = certs[certs.length - 1];
  const lastIsRoot = sameDer(last.subjectDer, root.subjectDer) && sameDer(last.der, root.der);
  const chain = lastIsRoot ? certs : certs.concat([root]);
  // Walk leaf → … → root
  for (let i = 0; i < chain.length - 1; i++) {
    const child = chain[i];
    const issuer = chain[i + 1];
    if (!sameDer(child.issuerDer, issuer.subjectDer)) {
      throw new Error("certificate chain issuer/subject mismatch");
    }
    await verifyCertificateSignature(child, issuer.spkiDer, now);
  }
  // Root must be self-signed and match the bundled Apple root DER (or a test root).
  const chainRoot = chain[chain.length - 1];
  if (!sameDer(chainRoot.der, root.der)) {
    throw new Error("chain does not terminate at the expected root");
  }
  if (now < root.notBefore - 60_000 || now > root.notAfter + 60_000) {
    throw new Error("root certificate expired or not yet valid");
  }
  return certs[0];
}

export { OID };
