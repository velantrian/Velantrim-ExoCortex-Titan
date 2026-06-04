const fs = require("fs");
const path = require("path");
const html = fs.readFileSync(
  path.join(__dirname, "../static/console/index.html"),
  "utf8"
);
const ids = [...html.matchAll(/id="([^"]+)"/g)].map((m) => m[1]);
const js = html.slice(html.lastIndexOf("<script>") + 8, html.lastIndexOf("</script>"));
const mk = () => ({
  value: "",
  checked: true,
  hidden: false,
  classList: { add() {}, remove() {}, toggle() {} },
  style: {},
  textContent: "",
  innerHTML: "",
  options: [{ textContent: "" }],
  appendChild() {},
  addEventListener() {},
  setAttribute() {},
  getAttribute() { return null; },
  querySelector() { return null; },
  querySelectorAll() { return []; },
  focus() {},
  select() {},
  setSelectionRange() {},
  tagName: "INPUT",
  type: "text",
  defaultValue: "",
  dataset: {},
  remove() {},
  insertBefore() {},
  firstChild: null,
});
const els = {};
ids.forEach((id) => {
  els[id] = mk();
});
global.document = {
  getElementById: (id) => els[id] || null,
  createElement: () => mk(),
  querySelector: () => null,
  querySelectorAll: () => [],
  documentElement: {
    setAttribute() {},
    lang: "ru",
    getAttribute: () => "ru",
  },
};
global.localStorage = {
  _data: {},
  getItem(k) {
    return this._data[k] ?? null;
  },
  setItem(k, v) {
    this._data[k] = v;
  },
  removeItem(k) {
    delete this._data[k];
  },
};
global.navigator = { language: "ru-RU", clipboard: { writeText: async () => {} } };
global.window = {
  speechSynthesis: { cancel() {}, speak() {}, getVoices: () => [] },
  location: { origin: "http://127.0.0.1:8755" },
  requestAnimationFrame: (cb) => setTimeout(cb, 0),
};
global.speechSynthesis = {
  cancel() {},
  speak() {},
  getVoices: () => [],
  addEventListener() {},
};
global.window.speechSynthesis = global.speechSynthesis;
global.SpeechSynthesisUtterance = function () {
  this.lang = "";
  this.onend = null;
  this.onerror = null;
};
global.fetch = async (url) => {
  const u = String(url);
  if (u.includes("providers")) {
    return {
      ok: true,
      json: async () => ({
        providers: [
          {
            id: "deepseek",
            title: "DeepSeek",
            default_model: "deepseek-v4-flash",
            models: ["deepseek-v4-flash", "deepseek-v4-pro"],
          },
        ],
      }),
      text: async () => "{}",
      status: 200,
    };
  }
  if (u.includes("bootstrap")) {
    return {
      ok: true,
      json: async () => ({
        auth_required: true,
        allow_open: true,
        console_api_key: "dev",
      }),
      text: async () => "{}",
      status: 200,
    };
  }
  if (u.includes("profiles")) {
    return { ok: true, json: async () => ({ profiles: [] }), text: async () => "{}", status: 200 };
  }
  if (u.includes("debug")) {
    return {
      ok: true,
      json: async () => ({ features: { chat_endpoint: true } }),
      text: async () => "{}",
      status: 200,
    };
  }
  return { ok: true, json: async () => ({}), text: async () => "{}", status: 200 };
};

try {
  eval(js);
  setTimeout(() => {
    console.log("llmGrid children:", els.llmGrid?.innerHTML?.length ?? "missing");
    console.log("messages children:", els.messages?.innerHTML?.length ?? "missing");
    console.log("provider select options:", els.llmProviderSelect?.options?.length);
    process.exit(0);
  }, 800);
} catch (e) {
  console.error("BOOT FAIL:", e.message);
  const stack = e.stack || "";
  const m = stack.match(/<anonymous>:(\d+):/);
  if (m) {
    const line = Number(m[1]);
    const lines = js.split("\n");
    for (let i = line - 4; i <= line + 2; i++) {
      if (lines[i - 1]) console.error(String(i).padStart(5), lines[i - 1].slice(0, 120));
    }
  }
  process.exit(1);
}
