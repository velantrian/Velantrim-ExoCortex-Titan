const fs = require("fs");
const path = require("path");
const p = path.join(__dirname, "../static/console/index.html");
let s = fs.readFileSync(p, "utf8");
const reps = [
  ['"В верхнем поле ключ LLM. Перенесите его в «API LLM», вверху — VELANTRIM_API_KEY из .env."', 't("auth.llmInTopField")'],
  ['"Перенесите его в блок «2. API LLM», а вверху укажите VELANTRIM_API_KEY из .env."', 't("err.llmInTopField").split("\\n\\n")[1] || t("err.llmInTopField")'],
  ['? "Укажите ключ OpenAI sk-… в блоке «Голосовой ввод» слева."', '? t("voice.needOpenaiKey")'],
  [': "Укажите ключ Gemini AIza… в блоке «Голосовой ввод» слева."', ': t("voice.needGeminiKey")'],
  ['showCopyToast("Готово (" + (mode === "openai" ? "OpenAI" : "Gemini") + ")")', 'showCopyToast(t("voice.doneApi", { api: mode === "openai" ? "OpenAI" : "Gemini" }))'],
  ['showCopyToast(sttKey ? "Текст с микрофона (запись слишком короткая для API)" : "Текст с микрофона")', 'showCopyToast(sttKey ? t("voice.shortRecording") : t("voice.fromMic"))'],
  ['showCopyToast("Запись отменена")', 'showCopyToast(t("voice.recordCancelled"))'],
  ['mic.title = "Остановить запись (браузер)"', 'mic.title = t("voice.stopBrowser")'],
  ['setVoiceStatus("Слушаю… (браузер, бесплатно)", null)', 'setVoiceStatus(t("voice.listeningBrowser"), null)'],
  ['setVoiceSttTestStatus("Сначала нажмите «Проверить ключ голоса (API)»", "err")', 'setVoiceSttTestStatus(t("voice.verifyKeyFirst"), "err")'],
  ['setVoiceStatus("Доступ к микрофону запрещён", "error")', 'setVoiceStatus(t("voice.micDeniedUi"), "error")'],
  ['mic.title = "Остановить и отправить в Gemini"', 'mic.title = t("voice.stopApi")'],
  ['"Слушаю… (" + (mode === "openai" ? "OpenAI API" : "Gemini API") + ")"', 't("voice.listeningApi", { api: mode === "openai" ? "OpenAI API" : "Gemini API" })'],
  ['addMsg(\n            "bot",\n            "⚠️ Бесплатный голос в браузере доступен в Chrome или Edge. Либо выберите режим «Gemini API» и ключ AIza…"\n          )', 'addMsg("bot", t("voice.browserUnavailable"))'],
  ['mode === "openai"\n            ? "⚠️ Режим OpenAI: вставьте ключ sk-… в блок слева «🎤 Голосовой ввод»."\n            : "⚠️ Режим Gemini: вставьте ключ AIza… в блок слева «🎤 Голосовой ввод»."', 'mode === "openai" ? t("voice.needOpenaiBlock") : t("voice.needGeminiBlock")'],
  ['addMsg("bot", "⚠️ Сначала проверьте ключ голоса кнопкой «Проверить ключ голоса (API)» слева.")', 'addMsg("bot", t("voice.verifyKeyFirstBot"))'],
  ['addMsg("bot", "⚠️ Микрофон недоступен. Используйте Chrome/Edge или режим «Браузер».")', 'addMsg("bot", t("voice.micUnavailable"))'],
  ['addMsg("bot", "⚠️ Разрешите доступ к микрофону в браузере.")', 'addMsg("bot", t("voice.micDeniedBot"))'],
  ['addMsg("bot", "⚠️ Не удалось начать запись: " + e.message)', 'addMsg("bot", t("voice.recordingFail", { msg: e.message }))'],
  ['setVoiceStatus("Gemini: " + e.message + " (оставлен текст браузера)", "error")', 'setVoiceStatus(t("voice.geminiErrLeft", { msg: e.message }), "error")'],
  ['addMsg("bot", "⚠️ Голос (Gemini): " + e.message)', 'addMsg("bot", t("voice.geminiErrBot", { msg: e.message }))'],
  ['btn.textContent = "✓ Голос API проверен"', 'btn.textContent = t("voice.testOk")'],
  ['`Проверяем STT ${mode === "openai" ? "OpenAI Whisper" : "Google Gemini"}…`', 't("voice.testingStt", { api: mode === "openai" ? "OpenAI Whisper" : "Google Gemini" })'],
  ['addMsg("bot", "⚠️ " +\n                (check.hint || apiKey401Help()) +\n                "\\n\\nНажмите «Проверить ключ Velantrim» — должен пройти тест API и чата.")', 'addMsg("bot", t("err.verifyVelantrimSend", { hint: check.hint || apiKey401Help() }))'],
  ['addMsg(\n            "bot",\n            "⚠️ Похоже, в верхнее поле вставлен ключ LLM (sk-… / AIza…).\\n\\n" +\n              "Перенесите его в блок «2. API LLM», а вверху укажите VELANTRIM_API_KEY из .env."\n          )', 'addMsg("bot", t("err.llmInTopField"))'],
  ['addMsg("user", q, `профиль: ${state.profile}${llmTag}`)', 'addMsg("user", q, t("meta.profile", { name: state.profile }) + llmTag)'],
  ['res.from_llm ? `🤖 ${res.llm_provider} / ${res.llm_model}` : "📚 память"', 'res.from_llm ? `🤖 ${res.llm_provider} / ${res.llm_model}` : t("meta.memory")'],
  ['`${res.facts_count || 0} фактов · ${res.latency_ms || 0} ms`', 't("meta.facts", { n: res.facts_count || 0, ms: res.latency_ms || 0 })'],
  ['res.reply || "(пусто)"', 'res.reply || t("meta.empty")'],
  ['res.llm_answer || res.answer || res.error || "(пустой ответ)"', 'res.llm_answer || res.answer || res.error || t("meta.emptyAnswer")'],
  ['const viaLlm = res.llm_answer ? "🤖 LLM" : "📚 память"', 'const viaLlm = res.llm_answer ? "🤖 LLM" : t("meta.memory")'],
  ['`${res.total_facts || 0} фактов · ${res.latency_ms || 0} ms`', 't("meta.facts", { n: res.total_facts || 0, ms: res.latency_ms || 0 })'],
  ['"voice.micBrowser": "Голос без API (browser)"', '"voice.micBrowser": "Голос без API (браузер)"'],
];
for (const [a, b] of reps) {
  if (s.includes(a)) s = s.split(a).join(b);
}
// add voice.recordCancelled keys if missing
if (!s.includes('"voice.recordCancelled"')) {
  s = s.replace(
    '"voice.geminiErrBot": "⚠️ Голос (Gemini): {msg}",',
    '"voice.geminiErrBot": "⚠️ Голос (Gemini): {msg}",\n        "voice.recordCancelled": "Запись отменена",'
  );
  s = s.replace(
    '"voice.geminiErrBot": "⚠️ Voice (Gemini): {msg}",',
    '"voice.geminiErrBot": "⚠️ Voice (Gemini): {msg}",\n        "voice.recordCancelled": "Recording cancelled",'
  );
}
fs.writeFileSync(p, s);
console.log("done2");
