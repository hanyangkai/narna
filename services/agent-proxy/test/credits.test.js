import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { requestCost, productConfig, BUDGET } from "../src/config.js";
import { consumeCredits, refundCredits, creditKey } from "../src/credits.js";
import { agentEnv } from "./helpers.js";

const tx = {
  productId: "nana.agent.basic.monthly",
  originalTransactionId: "orig-1",
  transactionId: "txn-1",
  expiresDate: Date.now() + 20 * 24 * 60 * 60 * 1000,
};

describe("credit caps", () => {
  it("maps plans to 200 / 800", () => {
    assert.equal(productConfig("nana.agent.basic.monthly").credits, 200);
    assert.equal(productConfig("nana.agent.pro.monthly").credits, 800);
    assert.equal(productConfig("nope"), null);
  });

  it("costs 1 credit, plus extras for search or files", () => {
    assert.equal(requestCost({}), 1);
    assert.equal(requestCost({ webSearch: true }), 2);
    assert.equal(requestCost({ hasFile: true, webSearch: true }), 3);
  });

  it("keeps worst-case spend under net proceeds", () => {
    const basicMax = BUDGET.basic.maxUSDPerCredit * BUDGET.basic.credits;
    const proMax = BUDGET.pro.maxUSDPerCredit * BUDGET.pro.credits;
    assert.ok(basicMax <= BUDGET.basic.proceedsUSD + 1e-9);
    assert.ok(proMax <= BUDGET.pro.proceedsUSD + 1e-9);
  });

  it("decrements and exhausts at the cap", async () => {
    const env = agentEnv({ BASIC_MONTHLY_CREDITS: "3" });
    const a = await consumeCredits(env, tx, {});
    assert.equal(a.remaining, 2);
    const b = await consumeCredits(env, tx, { webSearch: true });
    assert.equal(b.cost, 2);
    assert.equal(b.remaining, 0);
    await assert.rejects(() => consumeCredits(env, tx, {}), (e) => e.status === 429);
  });

  it("refunds a failed upstream reservation", async () => {
    const env = agentEnv({ BASIC_MONTHLY_CREDITS: "5" });
    const a = await consumeCredits(env, tx, {});
    await refundCredits(env, a.key, a.cost);
    const b = await consumeCredits(env, tx, {});
    assert.equal(b.remaining, 4);
    assert.equal(creditKey(tx).startsWith("credits:orig-1:"), true);
  });
});
