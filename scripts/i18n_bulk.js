const fs = require("fs");
const path = require("path");
const p = path.join(__dirname, "../static/console/index.html");
let s = fs.readFileSync(p, "utf8");
const reps = [
  ['showCopyToast("Скопировано")', 'showCopyToast(t("toast.copied"))'],
  ['showCopyToast("Не удалось скопировать")', 'showCopyToast(t("toast.copyFail"))'],
  ['btn.title = show ? "Скрыть ключ" : "Показать ключ"', 'btn.title = show ? t("btn.hideKey") : t("btn.showKey")'],
  ['testBtn.textContent = "Подтвердить ключ"', 'testBtn.textContent = t("btn.confirmKey")'],
  ['setLlmTestStatus("Сначала нажмите «Подтвердить ключ» — без успешной проверки LLM не включится.", "err")', 'setLlmTestStatus(t("err.llmConfirmFirst"), "err")'],
  ['addMsg("bot", "⚠️ Вставьте API ключ LLM (поле ниже провайдера).")', 'addMsg("bot", t("err.llmKeyMissing"))'],
  ['addMsg("bot", "⚠️ Ключ не проверен. Нажмите «Подтвердить ключ» и дождитесь ✓.")', 'addMsg("bot", t("err.llmNotVerified"))'],
  ['fillBtn.textContent = label || "Подставить ключ Velantrim из .env (localhost)"', 'fillBtn.textContent = label || t("btn.fillVelantrim")'],
  ['showCopyToast("Ключ Velantrim подставлен")', 'showCopyToast(t("toast.velantrimFilled"))'],
  ['useQuick ? "Сверяем с сервером…" : "Запрос к API (память + чат)…"', 'useQuick ? t("auth.checking") : t("auth.probing")'],
  ['data = { valid: false, hint: "Некорректный ответ сервера." }', 'data = { valid: false, hint: t("auth.badResponse") }'],
  ['data.hint = "Сервер не принял проверку (HTTP " + r.status + ")."', 'data.hint = t("auth.httpFail", { code: r.status })'],
  ['hint: "Нет связи с сервером. Запустите scripts\\\\start_console.ps1"', 'hint: t("auth.noServer")'],
  ['"В верхнем поле был ключ LLM — перенесите его в блок «API LLM»."', 't("auth.llmInTop")'],
  ['check.hint || "Ключ Velantrim не прошёл проверку API."', 'check.hint || t("auth.fail")'],
  ['check.hint || "Ключ проверен — чат доступен."', 'check.hint || t("auth.ok")'],
  ['check.hint || "Ключ подставлен и проверен."', 'check.hint || t("auth.filledOk")'],
  ['check.hint || "Не удалось проверить ключ с сервера."', 'check.hint || t("auth.filledFail")'],
  ['setVelantrimKeyStatus("Вставьте VELANTRIM_API_KEY из .env в верхнее поле.", "err")', 'setVelantrimKeyStatus(t("auth.insertKey"), "err")'],
  ['(check.hint || "Ключ проверен.") + ms', '(check.hint || t("auth.verifiedShort")) + ms'],
  ['check.hint || "Ключ не прошёл проверку API."', 'check.hint || t("auth.notVerified")'],
  ['"Подставить ключ Velantrim с сервера (localhost)"', 't("btn.fillVelantrimServer")'],
  ['el("llmHint").textContent = "Ошибка загрузки LLM: " + e.message', 'el("llmHint").textContent = t("hint.llmLoadErr", { msg: e.message })'],
  ['setLlmTestStatus("Вставьте API ключ LLM (не путайте с ключом Velantrim).", "err")', 'setLlmTestStatus(t("err.llmKeyInChat"), "err")'],
  ['addMsg("bot", "Вставьте API ключ LLM (не путайте с ключом Velantrim).")', 'addMsg("bot", t("err.llmKeyInChat"))'],
  ['el("llmTestBtn").textContent = "Подтвердить ключ"', 'el("llmTestBtn").textContent = t("btn.confirmKey")'],
  ['setVelantrimKeyStatus("Проверяем ключ перед отправкой…", "")', 'setVelantrimKeyStatus(t("auth.beforeSend"), "")'],
  ['check.hint || "Ключ не прошёл проверку."', 'check.hint || t("auth.notVerifiedShort")'],
  ['addMsg("bot", "⚠️ LLM включён: вставьте ключ LLM во второе поле (OpenAI / DeepSeek / …).")', 'addMsg("bot", t("err.llmOnNoKeyShort"))'],
  ['addMsg("bot", "⚠️ Ключ LLM не подтверждён — нажмите «Подтвердить ключ».")', 'addMsg("bot", t("err.llmNotConfirmedShort"))'],
  ['let meta = "Проверьте: 1) Velantrim key 2) LLM key 3) провайдер 4) перезапуск сервера"', 'let meta = t("err.sendMeta")'],
  ['let msg = "Ошибка: " + e.message', 'let msg = t("err.sendPrefix", { msg: e.message })'],
  ['meta = "Ключ сервера ≠ ключ LLM"', 'meta = t("err.keyMeta")'],
  ['btn.textContent = "Проверить ключ голоса (API)"', 'btn.textContent = t("voice.testKey")'],
  ['setVoiceSttTestStatus("Режим без API — проверка ключа не требуется.", "ok")', 'setVoiceSttTestStatus(t("voice.noApiNeeded"), "ok")'],
  ['? "Вставьте ключ OpenAI sk-… выше."', '? t("voice.insertOpenai")'],
  [': "Вставьте ключ Gemini AIza… выше."', ': t("voice.insertGemini")'],
  ['(data.hint || "Ключ проверен.") +', '(data.hint || t("voice.keyOk")) +'],
  ['showCopyToast("Голос " + mode + " — API подключён")', 'showCopyToast(t("toast.voiceConnected", { mode }))'],
  ['opt.textContent = saved + " (сохранённая)"', 'opt.textContent = saved + t("llm.modelSaved")'],
  ['if (verified) tag += " · ключ ✓ проверен"', 'if (verified) tag += t("llm.keyVerifiedTag")'],
  ['else if (hasKey) tag += " · ключ (не проверен)"', 'else if (hasKey) tag += t("llm.keyUnverifiedTag")'],
  ['addMsg("bot", "⚠️ Сервер без LLM API. Остановите старый uvicorn и запустите:\\nscripts\\\\start_console.ps1")', 'addMsg("bot", t("boot.noLlm"))'],
  ['addMsg("bot", "⚠️ Нет /chat — перезапустите scripts\\\\start_console.ps1")', 'addMsg("bot", t("boot.noChat"))'],
  ['setLlmTestStatus(`Проверяем ${state.llmProvider} / ${model}…`, "pending")', 'setLlmTestStatus(t("err.llmTestPending", { provider: state.llmProvider, model }), "pending")'],
  ['addMsg("bot", "❌ Проверка LLM: " + e.message + hint)', 'addMsg("bot", t("err.llmTestFailPrefix", { msg: e.message + hint }))'],
  ['setVoiceStatus("Нет доступа к микрофону", "error")', 'setVoiceStatus(t("voice.noMic"), "error")'],
  ['showCopyToast("Готово (голос браузера)")', 'showCopyToast(t("voice.doneBrowser"))'],
  ['setVoiceStatus("Речь не распознана", "error")', 'setVoiceStatus(t("voice.notRecognized"), "error")'],
  ['showCopyToast("Скажите что-нибудь ещё раз")', 'showCopyToast(t("voice.tryAgain"))'],
  ['showCopyToast("Не удалось распознать речь")', 'showCopyToast(t("voice.failRecognize"))'],
  ['showCopyToast("Текст с микрофона")', 'showCopyToast(t("voice.fromMic"))'],
  ['fillBtn.dataset.fillSource = "server"', 'fillBtn.dataset.fillSource = "server"'],
];
for (const [a, b] of reps) {
  if (s.includes(a)) s = s.split(a).join(b);
}
// velantrimKeyMissingMessage function body
s = s.replace(
  /function velantrimKeyMissingMessage\(\) \{[\s\S]*?return \([\s\S]*?\);\s*\}/,
  `function velantrimKeyMissingMessage() {
      const dev = serverBootstrap.is_local ? t("auth.missingKeyLocal") : "";
      return t("auth.missingKey") + t("auth.missingKeySuffix") + dev;
    }`
);
s = s.replace(
  /function apiKey401Help\(\) \{[\s\S]*?return \([\s\S]*?\);\s*\}/,
  `function apiKey401Help() {
      return t("auth.help401");
    }`
);
// loadLlmStatus fallback hint
s = s.replace(
  'el("llmHint").innerHTML =\n            `⚠️ Список с сервера недоступен (${e.message}). Используем встроенный список провайдеров.`;',
  'el("llmHint").innerHTML = t("hint.llmFallback", { msg: e.message });'
);
// setupVelantrimKeyFillButton - set dataset
s = s.replace(
  'fillBtn.style.display = "block";\n      fillBtn.textContent = label || t("btn.fillVelantrim");',
  'fillBtn.style.display = "block";\n      fillBtn.dataset.fillSource = label && label.includes("сервера") || label && label.includes("server") ? "server" : "env";\n      fillBtn.textContent = label || t("btn.fillVelantrim");'
);
fs.writeFileSync(p, s);
console.log("i18n bulk replace done");
