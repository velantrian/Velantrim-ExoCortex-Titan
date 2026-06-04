const fs = require("fs");
const path = require("path");
const acorn = require("acorn");
const html = fs.readFileSync(path.join(__dirname, "../static/console/index.html"), "utf8");
const js = html.match(/<script>\s*([\s\S]*?)<\/script>\s*<\/body>/)[1];
try {
  acorn.parse(js, { ecmaVersion: 2022, sourceType: "script" });
  console.log("OK");
} catch (e) {
  console.error(e.message);
  console.error("line", e.loc.line, "col", e.loc.column);
  const lines = js.split("\n");
  for (let i = e.loc.line - 3; i <= e.loc.line + 1; i++) {
    if (i >= 0 && i < lines.length) console.error(String(i + 1) + "| " + lines[i]);
  }
}
