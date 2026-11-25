/** Device + global daily counters via KV. No message content stored. */

export interface LimitEnv {
  LIMITS: KVNamespace;
  DAILY_MSG_LIMIT_PER_DEVICE?: string;
  GLOBAL_DAILY_MSG_CAP?: string;
  FREE_POOL_PAUSED?: string;
}

function dayKey(): string {
  return new Date().toISOString().slice(0, 10);
}

export async function checkAndBump(
  env: LimitEnv,
  deviceId: string,
  ip: string
): Promise<{ ok: true } | { ok: false; status: number; error: string }> {
  if ((env.FREE_POOL_PAUSED || "").toLowerCase() === "true") {
    return { ok: false, status: 503, error: "free_pool_paused" };
  }

  const day = dayKey();
  const perDevice = Number(env.DAILY_MSG_LIMIT_PER_DEVICE || "10");
  const globalCap = Number(env.GLOBAL_DAILY_MSG_CAP || "5000");

  const ipKey = `ip:${day}:${ip}`;
  const ipCount = Number((await env.LIMITS.get(ipKey)) || "0");
  if (ipCount >= perDevice * 3) {
    return { ok: false, status: 429, error: "rate_limited" };
  }

  const deviceKey = `device:${day}:${deviceId}`;
  const deviceCount = Number((await env.LIMITS.get(deviceKey)) || "0");
  if (deviceCount >= perDevice) {
    return { ok: false, status: 429, error: "daily_limit" };
  }

  const globalKey = `global:${day}`;
  const globalCount = Number((await env.LIMITS.get(globalKey)) || "0");
  if (globalCount >= globalCap) {
    return { ok: false, status: 429, error: "global_cap" };
  }

  const ttl = 60 * 60 * 36;
  await Promise.all([
    env.LIMITS.put(deviceKey, String(deviceCount + 1), { expirationTtl: ttl }),
    env.LIMITS.put(globalKey, String(globalCount + 1), { expirationTtl: ttl }),
    env.LIMITS.put(ipKey, String(ipCount + 1), { expirationTtl: ttl }),
  ]);

  return { ok: true };
}

/** Pure helper for unit tests (no KV). */
export function wouldBlock(deviceCount: number, perDevice: number): boolean {
  return deviceCount >= perDevice;
}
