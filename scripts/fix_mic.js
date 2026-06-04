const fs = require("fs");
const path = require("path");
const p = path.join(__dirname, "../static/console/index.html");
let s = fs.readFileSync(p, "utf8");
s = s.replace(
  '"voice.micBrowser": "Голос без API (browser)"',
  '"voice.micBrowser": "Голос без API (браузер)"'
);
fs.writeFileSync(p, s);
