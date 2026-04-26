const test = require("node:test");
const assert = require("node:assert/strict");

const { formatResetHint } = require("./render-utils.js");

test("formatResetHint returns null for brand-new items", () => {
  assert.equal(formatResetHint({ reset_count: 0 }), null);
});

test("formatResetHint returns a readable badge label for reset items", () => {
  assert.equal(formatResetHint({ reset_count: 1 }), "reset 1x");
  assert.equal(formatResetHint({ reset_count: 3 }), "reset 3x");
});
