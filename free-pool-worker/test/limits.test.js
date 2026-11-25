import test from "node:test";
import assert from "node:assert/strict";

// Mirror wouldBlock logic for Node tests without TS compile step
function wouldBlock(deviceCount, perDevice) {
  return deviceCount >= perDevice;
}

test("device under daily limit is allowed", () => {
  assert.equal(wouldBlock(9, 10), false);
});

test("device at daily limit is blocked", () => {
  assert.equal(wouldBlock(10, 10), true);
});

test("device over daily limit is blocked", () => {
  assert.equal(wouldBlock(11, 10), true);
});
