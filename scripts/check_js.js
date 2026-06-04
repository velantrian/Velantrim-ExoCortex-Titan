const fs = require("fs");
const path = require("path");
const html = fs.readFileSync(path.join(__dirname, "../static/console/index.html"), "utf8");
const bodyEnd = html.indexOf("</body>");
const chunk = html.slice(0, bodyEnd);
const start = chunk.lastIndexOf("<script>");
if (start < 0) { console.error("no script"); process.exit(1); }
const js = chunk.slice(start + 8, chunk.lastIndexOf("</script>"));
try {
  new Function(js);
  console.log("OK", js.split("\n").length, "lines");
} catch (e) {
  console.error(e.message);
  const lines = js.split("\n");
  for (let i = 0; i < lines.length; i++) {
    try { new Function(lines.slice(0, i + 1).join("\n")); }
    catch (err) {
      if (String(err.message).includes("Unexpected")) {
        console.error("fail near line", i + 1);
        for (let j = Math.max(0, i - 2); j <= Math.min(lines.length - 1, i + 2); j++)
          console.error(String(j + 1).padStart(5) + "| " + lines[j]);
        break;
      }
    }
  }
}
