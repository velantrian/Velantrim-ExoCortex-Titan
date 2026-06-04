$root = Split-Path $PSScriptRoot -Parent
$htmlPath = Join-Path $root "static\console\index.html"
$snippetPath = Join-Path $root "static\console\i18n-snippet.js"
$html = [IO.File]::ReadAllText($htmlPath)
$snippet = [IO.File]::ReadAllText($snippetPath)
if ($html -notmatch "VELANTRIM I18N START") {
  $marker = "    initVoiceInput();"
  if ($html.IndexOf($marker) -lt 0) { throw "marker not found" }
  $insert = $marker + "`n`n    // --- VELANTRIM I18N START ---`n" + $snippet + "    // --- VELANTRIM I18N END ---`n"
  $html = $html.Replace($marker, $insert)
}
$html = $html.Replace("THEME_CATALOG.forEach", "getThemeCatalog().forEach")
$html = $html.Replace('let llmHintBase = "💡 У каждого провайдера свой ключ', 'let llmHintBase = ""; // set in refreshLlmProviderHint')
$html = $html.Replace(
  '    const PROVIDER_SETUP_HINTS = {
      gemini:
        "✨ <b>Google Gemini</b> — ключ AIza… с " +
        ''<a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener">AI Studio</a>. '' +
        "В " +
        ''<a href="https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com" target="_blank" rel="noopener">Google Cloud</a> '' +
        "включите <b>Generative Language API</b> для проекта ключа. " +
        "В ограничениях ключа разрешите этот API; для сервера не задавайте HTTP referrer. " +
        "При HTTP 403 из региона: <b>OpenRouter</b> → модель <code>google/gemini-2.5-flash</code>.",
    };',
  '    function getProviderSetupHint(id) {
      if (id === "gemini") return getGeminiSetupHint();
      return "";
    }'
)
$html = $html.Replace(
  '      const setup = PROVIDER_SETUP_HINTS[state.llmProvider];',
  '      const setup = getProviderSetupHint(state.llmProvider);'
)
$html = $html.Replace(
  '      let hint = llmHintBase;',
  '      let hint = llmHintBase || getLlmHintBase();'
)
$html = $html.Replace(
  '          llmHintBase = serverLlmReady && serverLlmSetup
            ? `🖥️ На сервере также настроен LLM из .env: <b>${serverLlmSetup.provider}</b>.`
            : `💡 У каждого провайдера свой ключ — вставьте ключ и нажмите «Подтвердить ключ», затем включите LLM.`;',
  '          llmHintBase = serverLlmReady && serverLlmSetup
            ? t("hint.llmServer", { provider: serverLlmSetup.provider })
            : getLlmHintBase();'
)
$html = $html.Replace(
  '    (async () => {
      initLlmProviders(PROVIDERS_FALLBACK);
      addMsg(
        "bot",
        "Привет! 🔱\n\n" +
          "Два ключа:\n" +
          "1) Вверху — VELANTRIM_API_KEY из .env (ключ сервера)\n" +
          "2) Ниже — ключ LLM (DeepSeek, Gemini, OpenAI…)\n\n" +
          "Затем: провайдер → «Подтвердить ключ» → «LLM включён» → чат\n\n" +
          "🎤 Слева блок «Голосовой ввод»: без API (бесплатно) или ключ Gemini/OpenAI. Кнопка 🎤 — внизу у чата."
      );',
  '    (async () => {
      renderLangPicker();
      applyStaticI18n();
      initLlmProviders(PROVIDERS_FALLBACK);
      addMsg("bot", t("welcome.bot"));'
)
[IO.File]::WriteAllText($htmlPath, $html)
Write-Host "i18n inserted"
