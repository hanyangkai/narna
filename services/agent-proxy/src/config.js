// Credit caps. Keep API spend below net revenue after Apple's 15% fee.
// Basic $4.99 → $4.24 proceeds; Pro $14.99 → $12.74 proceeds (USA).
export const PRODUCTS = {
  "nana.agent.basic.monthly": { plan: "basic", credits: 200 },
  "nana.agent.pro.monthly": { plan: "pro", credits: 800 },
};

export const DEFAULT_BUNDLE_ID = "org.narna.mobile";
export const DEFAULT_APP_ID = "6832895840";

export function productConfig(productId, env = {}) {
  const base = PRODUCTS[productId];
  if (!base) return null;
  const overrideKey = base.plan === "basic" ? "BASIC_MONTHLY_CREDITS" : "PRO_MONTHLY_CREDITS";
  const raw = env[overrideKey];
  const n = raw != null && String(raw).trim() !== "" ? Number.parseInt(String(raw), 10) : base.credits;
  const credits = Number.isFinite(n) && n > 0 ? n : base.credits;
  return { ...base, credits };
}

export function bundleId(env = {}) {
  return (env.APPLE_BUNDLE_ID || DEFAULT_BUNDLE_ID).trim();
}

/** Credits charged for one Agent request. Always >= 1. */
export function requestCost({ webSearch = false, hasFile = false } = {}) {
  let cost = 1;
  if (webSearch) cost += 1;
  if (hasFile) cost += 1;
  return cost;
}

/** Max allowed spend per credit so caps stay under net proceeds. */
export const BUDGET = {
  basic: { listUSD: 4.99, proceedsUSD: 4.24, credits: 200, maxUSDPerCredit: 0.0212 },
  pro: { listUSD: 14.99, proceedsUSD: 12.74, credits: 800, maxUSDPerCredit: 0.015925 },
};
