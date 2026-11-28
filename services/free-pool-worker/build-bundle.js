// Assemble src/router.js + src/index.js into a single ESM module for the Workers API upload.
const fs = require("fs");
const path = require("path");
let router = fs.readFileSync(path.join(__dirname, "src/router.js"), "utf8");
const m = router.match(/module\.exports = \{([\s\S]*?)\};\s*$/);
if (!m) throw new Error("module.exports block not found");
const names = m[1].split(",").map((x) => x.trim()).filter(Boolean);
router = router.slice(0, m.index);
let index = fs.readFileSync(path.join(__dirname, "src/index.js"), "utf8");
index = index.replace('const router = require("./router.js");\n', "");
const out = "// Bundled ESM for Cloudflare Workers deploy. Source of truth: src/router.js + src/index.js (node build-bundle.js)\n" +
  router + "\nconst router = { " + names.join(", ") + " };\n\n" + index;
fs.writeFileSync(process.argv[2] || path.join(__dirname, "dist-worker.mjs"), out);
console.log("bundle bytes", out.length);
