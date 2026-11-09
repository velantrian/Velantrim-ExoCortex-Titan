// VELANTRIM console i18n — вставляется в index.html
    const LANG_KEY = "velantrim_console_lang";
    const VALID_LANGS = ["ru", "en"];
    const LANG_CATALOG = [
      { id: "ru", flag: "🇷🇺", code: "RU", title: "Русский" },
      { id: "en", flag: "🇬🇧", code: "EN", title: "English" },
    ];

    const I18N = {
      ru: {
        pageTitle: "VELANTRIM — консоль",
        "header.subtitle": "Память + LLM · настройте API и общайтесь в чате",
        "lang.label": "Язык",
        "theme.label": "Тема",
        "tts.toggle": "Озвучка",
        "tts.toggleTitle": "Озвучивать ответы бота (Web Speech API)",
        "tts.autoOn": "Автоозвучка ответов включена (язык по тексту)",
        "tts.autoOff": "Автоозвучка выключена — кнопка 🔊 у каждого ответа",
        "tts.unavailable": "Web Speech API недоступен",
        "tts.speak": "Озвучить",
        "tts.stop": "Стоп",
        "tts.unavailBrowser": "Озвучка недоступна в этом браузере",
        "theme.darkShort": "тёмн", "theme.darkTitle": "Тёмная — классическая тёмная",
        "theme.lightShort": "свет", "theme.lightTitle": "Светлая — минимализм",
        "theme.skeuShort": "скев", "theme.skeuTitle": "Скевоморфизм — объёмные кнопки",
        "theme.volShort": "3d", "theme.volTitle": "Объёмная 3D (тёмная)",
        "theme.volLightShort": "3d+", "theme.volLightTitle": "Объёмная 3D (светлая)",
        "theme.bookShort": "книга", "theme.bookTitle": "Книжная — тёплая бумага, serif",
        "theme.neonShort": "неон", "theme.neonTitle": "Неон — тёмный с подсветкой",
        "section.velantrim": "🔑 1. Ключ Velantrim (сервер)",
        "section.llm": "🤖 2. API LLM (DeepSeek, Gemini, …)",
        "section.voice": "🎤 Голосовой ввод (речь → текст)",
        "section.profile": "👤 Профиль запроса",
        "section.fact": "📝 Запомнить факт",
        "label.apiUrl": "Базовый URL (для внешних клиентов)",
        "label.velantrimKey": "VELANTRIM_API_KEY из .env — не путать с DeepSeek/Gemini",
        "placeholder.velantrimKey": "например dev-change-me (из .env)",
        "hint.apiExternal": 'Подключение с другого приложения: заголовок <code>X-Api-Key: &lt;ваш ключ&gt;</code>. Эндпоинты: <code>POST /query</code>, <code>POST /chat</code>, <code>GET /health</code>. <a href="/docs" target="_blank" rel="noopener">OpenAPI (/docs)</a>.',
        "hint.velantrim": "Сначала заполните это поле (ключ из файла <code>.env</code>), затем ниже — ключ LLM. Хранится только в браузере (localStorage).",
        "hint.storageOnly": " Хранится только в браузере.",
        "btn.fillVelantrim": "Подставить ключ Velantrim из .env (localhost)",
        "btn.fillVelantrimServer": "Подставить ключ Velantrim с сервера (localhost)",
        "btn.verifyVelantrim": "Проверить ключ (запрос к API и чату)",
        "btn.verifyVelantrimShort": "Проверить ключ Velantrim",
        "btn.verifiedVelantrim": "✓ Ключ проверен (API + чат)",
        "label.llmProvider": "1. Выберите провайдера",
        "label.llmQuick": "Быстрый выбор (карточки)",
        "label.llmCustomModel": "Своя модель (если нет в списке)",
        "placeholder.llmKey": "вставьте ключ",
        "placeholder.customModel": "например deepseek-v4-pro",
        "placeholder.apiKeyGeneric": "API ключ",
        "banner.provider": "Провайдер: …",
        "banner.subline": "Нажмите карточку или список выше",
        "banner.defaultModel": "Модель по умолчанию: {model}",
        "label.llmKeyFor": "2. API ключ для {name}",
        "label.llmModelFor": "3. Модель ({name})",
        "label.llmModel": "3. Модель",
        "btn.llmOff": "LLM выключен",
        "btn.llmOn": "✅ LLM включён",
        "btn.confirmKey": "Подтвердить ключ",
        "btn.keyConfirmed": "✓ Ключ подтверждён",
        "btn.confirmKeyTitle": "Отправит тестовый запрос к API выбранного провайдера",
        "hint.llmLoading": "Загрузка провайдеров…",
        "hint.llmBase": "💡 У каждого провайдера свой ключ — вставьте ключ и нажмите «Подтвердить ключ», затем включите LLM.",
        "hint.llmServer": "🖥️ На сервере также настроен LLM из .env: <b>{provider}</b>.",
        "hint.llmCurrent": "<br>✅ Сейчас: <b>{name}</b> / {model}",
        "hint.llmFallback": "⚠️ Список с сервера недоступен ({msg}). Используем встроенный список провайдеров.",
        "hint.llmLoadErr": "Ошибка загрузки LLM: {msg}",
        "hint.geminiSetup": '✨ <b>Google Gemini</b> — ключ AIza… с <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener">AI Studio</a>. В <a href="https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com" target="_blank" rel="noopener">Google Cloud</a> включите <b>Generative Language API</b> для проекта ключа. В ограничениях ключа разрешите этот API; для сервера не задавайте HTTP referrer. При HTTP 403 из региона: <b>OpenRouter</b> → модель <code>google/gemini-2.5-flash</code>.',
        "voice.modeLabel": "Режим распознавания",
        "voice.modeBrowser": "① Без API — браузер (бесплатно, Google в Chrome/Edge)",
        "voice.modeGemini": "② Google Gemini API — ключ AIza…",
        "voice.modeOpenai": "③ OpenAI API — ключ sk-… (Whisper)",
        "voice.keyLabel": "API-ключ для голоса",
        "voice.keyGemini": "Ключ Google Gemini (AIza…) для голоса",
        "voice.keyOpenai": "Ключ OpenAI (sk-…) для голоса (Whisper)",
        "voice.placeholderKey": "Вставьте ключ API",
        "voice.placeholderGemini": "AIza… с aistudio.google.com/apikey",
        "voice.placeholderOpenai": "sk-… с platform.openai.com",
        "voice.browserOk": "✓ Режим без API — ключ не нужен, можно сразу нажимать 🎤 внизу",
        "voice.testKey": "Проверить ключ голоса (API)",
        "voice.testOk": "✓ Голос API проверен",
        "voice.hintPick": "Выберите режим. Для бесплатного ввода оставьте «Без API». Кнопка 🎤 — внизу у поля чата.",
        "voice.hintBrowser": "<b>Без API:</b> бесплатно в Chrome/Edge. Внизу нажмите 🎤 → говорите → снова 🎤. <b>Отмена</b> — сброс.",
        "voice.hintBrowserNo": "<b>Без API</b> недоступен в этом браузере. Выберите Gemini или OpenAI и вставьте ключ выше.",
        "voice.hintGemini": "<b>Gemini API:</b> вставьте ключ AIza… в поле выше (или тот же ключ, что в блоке LLM при провайдере Gemini). Затем 🎤 внизу.",
        "voice.hintOpenai": "<b>OpenAI Whisper:</b> вставьте ключ sk-… в поле выше. Затем 🎤 внизу у чата.",
        "voice.micBrowser": "Голос без API (бrowser)",
        "voice.micGemini": "Голос через Gemini API",
        "voice.micOpenai": "Голос через OpenAI Whisper",
        "voice.listening": "Слушаю…",
        "voice.noMic": "Нет доступа к микрофону",
        "voice.notRecognized": "Речь не распознана",
        "voice.processing": "{api} распознаёт речь…",
        "voice.doneBrowser": "Готово (голос браузера)",
        "voice.tryAgain": "Скажите что-нибудь ещё раз",
        "voice.doneApi": "Готово ({api})",
        "voice.fromMic": "Текст с микрофона",
        "voice.shortRecording": "Текст с микрофона (запись слишком короткая для API)",
        "voice.failRecognize": "Не удалось распознать речь",
        "profile.loading": "Загрузка…",
        "profile.server": "Сервер: <b>{emoji} {title}</b>. В чате можно выбрать другой профиль.",
        "profile.none": "Профиль сервера не задан — выберите карточку выше.",
        "fact.placeholder": "Текст факта…",
        "btn.saveFact": "Сохранить в память",
        "chat.placeholder": "Напишите или нажмите 🎤… Enter — отправить",
        "btn.send": "Отправить",
        "btn.cancel": "Отмена",
        "btn.copy": "Копировать",
        "btn.edit": "Изменить",
        "btn.save": "Сохранить",
        "btn.resend": "Переслать",
        "btn.clear": "Очистить",
        "btn.showKey": "Показать ключ",
        "btn.hideKey": "Скрыть ключ",
        "copy.url": "Копировать URL",
        "copy.key": "Копировать ключ",
        "copy.llmKey": "Копировать ключ LLM",
        "toast.nothing": "Нечего копировать",
        "toast.copied": "Скопировано",
        "toast.copyFail": "Не удалось скопировать",
        "toast.msgCopied": "Текст скопирован",
        "toast.velantrimFilled": "Ключ Velantrim подставлен",
        "toast.voiceConnected": "Голос {mode} — API подключён",
        "status.velUnknown": "Velantrim ?",
        "status.velOk": "Velantrim ✓ API+чат",
        "status.velBad": "Velantrim не проверен",
        "status.llmOn": "{name} вкл",
        "status.llmOff": "LLM выкл",
        "status.llmOk": "LLM ✓",
        "status.llmMaybe": "LLM ?",
        "status.llmDash": "LLM —",
        "status.voiceDash": "Голос —",
        "status.voiceBrowser": "Голос ✓ браузер",
        "status.voiceGemini": "Голос ✓ Gemini",
        "status.voiceOpenai": "Голос ✓ OpenAI",
        "status.voiceMaybe": "Голос ?",
        "llm.keyVerifiedTag": " · ключ ✓ проверен",
        "llm.keyUnverifiedTag": " · ключ (не проверен)",
        "llm.modelSaved": " (сохранённая)",
        "llm.alreadyVerified": "Ключ {name} уже проверен для текущего значения.",
        "meta.profile": "профиль: {name}",
        "meta.memory": "📚 память",
        "meta.facts": "{n} фактов · {ms} ms",
        "meta.empty": "(пусто)",
        "meta.emptyAnswer": "(пустой ответ)",
        "auth.checking": "Сверяем с сервером…",
        "auth.probing": "Запрос к API (память + чат)…",
        "auth.badResponse": "Некорректный ответ сервера.",
        "auth.httpFail": "Сервер не принял проверку (HTTP {code}).",
        "auth.noServer": "Нет связи с сервером. Запустите scripts\\start_console.ps1",
        "auth.fail": "Ключ Velantrim не прошёл проверку API.",
        "auth.ok": "Ключ проверен — чат доступен.",
        "auth.filledOk": "Ключ подставлен и проверен.",
        "auth.filledFail": "Не удалось проверить ключ с сервера.",
        "auth.insertKey": "Вставьте VELANTRIM_API_KEY из .env в верхнее поле.",
        "auth.notVerified": "Ключ не прошёл проверку API.",
        "auth.beforeSend": "Проверяем ключ перед отправкой…",
        "auth.notVerifiedShort": "Ключ не прошёл проверку.",
        "auth.llmInTop": "В верхнем поле был ключ LLM — перенесите его в блок «API LLM».",
        "auth.missingKey": "⚠️ Нужен ключ Velantrim в верхнем блоке «1. Ключ Velantrim (сервер)» — это VELANTRIM_API_KEY из .env.\n\nКлючи DeepSeek / Gemini / OpenAI вставляются ниже, в блок «2. API LLM» — это другой ключ.",
        "auth.missingKeyLocal": "\n\nНажмите «Подставить ключ Velantrim с сервера» или «Проверить ключ Velantrim» (при запуске через start_console.ps1 ключ часто dev-console-key, не dev-change-me).",
        "auth.help401": "Неверный ключ Velantrim (X-Api-Key).\n\nВерхнее поле = VELANTRIM_API_KEY из .env (не DeepSeek/Gemini).\nНажмите «Проверить ключ Velantrim» или «Подставить ключ из .env».",
        "err.llmKeyMissing": "⚠️ Вставьте API ключ LLM (поле ниже провайдера).",
        "err.llmConfirmFirst": "Сначала нажмите «Подтвердить ключ» — без успешной проверки LLM не включится.",
        "err.llmNotVerified": "⚠️ Ключ не проверен. Нажмите «Подтвердить ключ» и дождитесь ✓.",
        "err.llmKeyInChat": "Вставьте API ключ LLM (не путайте с ключом Velantrim).",
        "err.llmOnNoKey": "⚠️ LLM включён: вставьте ключ LLM во второе поле (OpenAI / DeepSeek / …).",
        "err.llmNotConfirmed": "⚠️ Ключ LLM не подтверждён — нажмите «Подтвердить ключ».",
        "err.llmInTopField": "⚠️ Похоже, в верхнее поле вставлен ключ LLM (sk-… / AIza…).\n\nПеренесите его в блок «2. API LLM», а вверху укажите VELANTRIM_API_KEY из .env.",
        "err.verifyVelantrimBtn": "\n\nНажмите «Проверить ключ Velantrim» — должен пройти тест API и чата.",
        "err.sendMeta": "Проверьте: 1) Velantrim key 2) LLM key 3) провайдер 4) перезапуск сервера",
        "err.sendPrefix": "Ошибка: {msg}",
        "err.keyMeta": "Ключ сервера ≠ ключ LLM",
        "err.llmTestPending": "Проверяем {provider} / {model}…",
        "err.llmTestOk": "✅ Ключ проверен: {provider} / {model}. Ответ: {preview}",
        "err.llmTestBotOk": "✅ Ключ LLM подтверждён: {provider} / {model}\n{preview}",
        "err.llmTestFail": "❌ Проверка LLM: {msg}",
        "fact.saved": "Запомнил: {text}",
        "fact.fail": "Не сохранил: {msg}",
        "voice.noApiNeeded": "Режим без API — проверка ключа не требуется.",
        "voice.insertOpenai": "Вставьте ключ OpenAI sk-… выше.",
        "voice.insertGemini": "Вставьте ключ Gemini AIza… выше.",
        "voice.testingStt": "Проверяем STT {api}…",
        "voice.keyOk": "Ключ проверен.",
        "voice.response": " Ответ: «{text}»",
        "voice.needOpenaiKey": "Укажите ключ OpenAI sk-… в блоке «Голосовой ввод» слева.",
        "voice.needGeminiKey": "Укажите ключ Gemini AIza… в блоке «Голосовой ввод» слева.",
        "boot.noLlm": "⚠️ Сервер без LLM API. Остановите старый uvicorn и запустите:\nscripts\\start_console.ps1",
        "boot.noChat": "⚠️ Нет /chat — перезапустите scripts\\start_console.ps1",
        "welcome.bot": "Привет! 🔱\n\nДва ключа:\n1) Вверху — VELANTRIM_API_KEY из .env (ключ сервера)\n2) Ниже — ключ LLM (DeepSeek, Gemini, OpenAI…)\n\nЗатем: провайдер → «Подтвердить ключ» → «LLM включён» → чат\n\n🎤 Слева блок «Голосовой ввод»: без API (бесплатно) или ключ Gemini/OpenAI. Кнопка 🎤 — внизу у чата.",
        "boot.serverDown": "Сервер недоступен: {msg}\nЗапустите: scripts\\start_console.ps1",
      },
      en: {
        pageTitle: "VELANTRIM — console",
        "header.subtitle": "Memory + LLM · configure API and chat",
        "lang.label": "Lang",
        "theme.label": "Theme",
        "tts.toggle": "TTS",
        "tts.toggleTitle": "Read bot replies aloud (Web Speech API)",
        "tts.autoOn": "Auto-read replies on (language from text)",
        "tts.autoOff": "Auto-read off — use 🔊 on each reply",
        "tts.unavailable": "Web Speech API unavailable",
        "tts.speak": "Speak",
        "tts.stop": "Stop",
        "tts.unavailBrowser": "Speech unavailable in this browser",
        "theme.darkShort": "dark", "theme.darkTitle": "Dark — classic dark theme",
        "theme.lightShort": "lite", "theme.lightTitle": "Light — minimal",
        "theme.skeuShort": "skeu", "theme.skeuTitle": "Skeuomorphism — raised buttons",
        "theme.volShort": "3d", "theme.volTitle": "Volumetric 3D (dark)",
        "theme.volLightShort": "3d+", "theme.volLightTitle": "Volumetric 3D (light)",
        "theme.bookShort": "book", "theme.bookTitle": "Book — warm paper, serif",
        "theme.neonShort": "neon", "theme.neonTitle": "Neon — dark with glow",
        "section.velantrim": "🔑 1. Velantrim key (server)",
        "section.llm": "🤖 2. LLM API (DeepSeek, Gemini, …)",
        "section.voice": "🎤 Voice input (speech → text)",
        "section.profile": "👤 Query profile",
        "section.fact": "📝 Remember a fact",
        "label.apiUrl": "Base URL (for external clients)",
        "label.velantrimKey": "VELANTRIM_API_KEY from .env — not DeepSeek/Gemini",
        "placeholder.velantrimKey": "e.g. dev-change-me (from .env)",
        "hint.apiExternal": 'External apps: header <code>X-Api-Key: &lt;your key&gt;</code>. Endpoints: <code>POST /query</code>, <code>POST /chat</code>, <code>GET /health</code>. <a href="/docs" target="_blank" rel="noopener">OpenAPI (/docs)</a>.',
        "hint.velantrim": "Fill this field first (.env key), then LLM key below. Stored in browser only (localStorage).",
        "hint.storageOnly": " Stored in browser only.",
        "btn.fillVelantrim": "Use Velantrim key from .env (localhost)",
        "btn.fillVelantrimServer": "Use Velantrim key from server (localhost)",
        "btn.verifyVelantrim": "Verify key (API + chat test)",
        "btn.verifyVelantrimShort": "Verify Velantrim key",
        "btn.verifiedVelantrim": "✓ Key verified (API + chat)",
        "label.llmProvider": "1. Choose provider",
        "label.llmQuick": "Quick pick (cards)",
        "label.llmCustomModel": "Custom model (if not in list)",
        "placeholder.llmKey": "paste key",
        "placeholder.customModel": "e.g. deepseek-v4-pro",
        "placeholder.apiKeyGeneric": "API key",
        "banner.provider": "Provider: …",
        "banner.subline": "Click a card or pick from the list",
        "banner.defaultModel": "Default model: {model}",
        "label.llmKeyFor": "2. API key for {name}",
        "label.llmModelFor": "3. Model ({name})",
        "label.llmModel": "3. Model",
        "btn.llmOff": "LLM off",
        "btn.llmOn": "✅ LLM on",
        "btn.confirmKey": "Confirm key",
        "btn.keyConfirmed": "✓ Key confirmed",
        "btn.confirmKeyTitle": "Sends a test request to the selected provider",
        "hint.llmLoading": "Loading providers…",
        "hint.llmBase": "💡 Each provider needs its own key — paste key, click «Confirm key», then enable LLM.",
        "hint.llmServer": "🖥️ Server also has LLM from .env: <b>{provider}</b>.",
        "hint.llmCurrent": "<br>✅ Active: <b>{name}</b> / {model}",
        "hint.llmFallback": "⚠️ Server list unavailable ({msg}). Using built-in providers.",
        "hint.llmLoadErr": "LLM load error: {msg}",
        "hint.geminiSetup": '✨ <b>Google Gemini</b> — AIza… key from <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener">AI Studio</a>. Enable <b>Generative Language API</b> in <a href="https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com" target="_blank" rel="noopener">Google Cloud</a>. Allow this API in key restrictions; no HTTP referrer for server use. HTTP 403 in your region: <b>OpenRouter</b> → <code>google/gemini-2.5-flash</code>.',
        "voice.modeLabel": "Recognition mode",
        "voice.modeBrowser": "① No API — browser (free, Google in Chrome/Edge)",
        "voice.modeGemini": "② Google Gemini API — AIza… key",
        "voice.modeOpenai": "③ OpenAI API — sk-… key (Whisper)",
        "voice.keyLabel": "Voice API key",
        "voice.keyGemini": "Google Gemini key (AIza…) for voice",
        "voice.keyOpenai": "OpenAI key (sk-…) for voice (Whisper)",
        "voice.placeholderKey": "Paste API key",
        "voice.placeholderGemini": "AIza… from aistudio.google.com/apikey",
        "voice.placeholderOpenai": "sk-… from platform.openai.com",
        "voice.browserOk": "✓ No API — no key needed, press 🎤 below",
        "voice.testKey": "Verify voice key (API)",
        "voice.testOk": "✓ Voice API verified",
        "voice.hintPick": "Pick a mode. For free input keep «No API». 🎤 is below the chat field.",
        "voice.hintBrowser": "<b>No API:</b> free in Chrome/Edge. Press 🎤 below → speak → 🎤 again. <b>Cancel</b> resets.",
        "voice.hintBrowserNo": "<b>No API</b> unavailable in this browser. Choose Gemini or OpenAI and paste a key above.",
        "voice.hintGemini": "<b>Gemini API:</b> paste AIza… above (or same key as LLM block when Gemini is selected). Then 🎤 below.",
        "voice.hintOpenai": "<b>OpenAI Whisper:</b> paste sk-… above. Then 🎤 at the bottom.",
        "voice.micBrowser": "Voice without API (browser)",
        "voice.micGemini": "Voice via Gemini API",
        "voice.micOpenai": "Voice via OpenAI Whisper",
        "voice.listening": "Listening…",
        "voice.noMic": "Microphone access denied",
        "voice.notRecognized": "Speech not recognized",
        "voice.processing": "{api} transcribing…",
        "voice.doneBrowser": "Done (browser voice)",
        "voice.tryAgain": "Try speaking again",
        "voice.doneApi": "Done ({api})",
        "voice.fromMic": "Text from microphone",
        "voice.shortRecording": "Text from mic (recording too short for API)",
        "voice.failRecognize": "Could not recognize speech",
        "profile.loading": "Loading…",
        "profile.server": "Server: <b>{emoji} {title}</b>. You can pick another profile in chat.",
        "profile.none": "No server profile — pick a card above.",
        "fact.placeholder": "Fact text…",
        "btn.saveFact": "Save to memory",
        "chat.placeholder": "Type or press 🎤… Enter to send",
        "btn.send": "Send",
        "btn.cancel": "Cancel",
        "btn.copy": "Copy",
        "btn.edit": "Edit",
        "btn.save": "Save",
        "btn.resend": "Resend",
        "btn.clear": "Clear",
        "btn.showKey": "Show key",
        "btn.hideKey": "Hide key",
        "copy.url": "Copy URL",
        "copy.key": "Copy key",
        "copy.llmKey": "Copy LLM key",
        "toast.nothing": "Nothing to copy",
        "toast.copied": "Copied",
        "toast.copyFail": "Copy failed",
        "toast.msgCopied": "Text copied",
        "toast.velantrimFilled": "Velantrim key applied",
        "toast.voiceConnected": "Voice {mode} — API connected",
        "status.velUnknown": "Velantrim ?",
        "status.velOk": "Velantrim ✓ API+chat",
        "status.velBad": "Velantrim unverified",
        "status.llmOn": "{name} on",
        "status.llmOff": "LLM off",
        "status.llmOk": "LLM ✓",
        "status.llmMaybe": "LLM ?",
        "status.llmDash": "LLM —",
        "status.voiceDash": "Voice —",
        "status.voiceBrowser": "Voice ✓ browser",
        "status.voiceGemini": "Voice ✓ Gemini",
        "status.voiceOpenai": "Voice ✓ OpenAI",
        "status.voiceMaybe": "Voice ?",
        "llm.keyVerifiedTag": " · key ✓ verified",
        "llm.keyUnverifiedTag": " · key (unverified)",
        "llm.modelSaved": " (saved)",
        "llm.alreadyVerified": "Key {name} already verified for current value.",
        "meta.profile": "profile: {name}",
        "meta.memory": "📚 memory",
        "meta.facts": "{n} facts · {ms} ms",
        "meta.empty": "(empty)",
        "meta.emptyAnswer": "(empty reply)",
        "auth.checking": "Checking with server…",
        "auth.probing": "API request (memory + chat)…",
        "auth.badResponse": "Invalid server response.",
        "auth.httpFail": "Server rejected check (HTTP {code}).",
        "auth.noServer": "Cannot reach server. Run scripts\\start_console.ps1",
        "auth.fail": "Velantrim key failed API check.",
        "auth.ok": "Key verified — chat available.",
        "auth.filledOk": "Key applied and verified.",
        "auth.filledFail": "Could not verify key from server.",
        "auth.insertKey": "Paste VELANTRIM_API_KEY from .env in the top field.",
        "auth.notVerified": "Key failed API verification.",
        "auth.beforeSend": "Verifying key before send…",
        "auth.notVerifiedShort": "Key verification failed.",
        "auth.llmInTop": "Top field had an LLM key — move it to «LLM API» block.",
        "auth.missingKey": "⚠️ Velantrim key required in «1. Velantrim key (server)» — VELANTRIM_API_KEY from .env.\n\nDeepSeek / Gemini / OpenAI keys go in «2. LLM API» — a different key.",
        "auth.missingKeyLocal": "\n\nClick «Use Velantrim key from server» or «Verify Velantrim key» (with start_console.ps1 the key is often dev-console-key, not dev-change-me).",
        "auth.help401": "Invalid Velantrim key (X-Api-Key).\n\nTop field = VELANTRIM_API_KEY from .env (not DeepSeek/Gemini).\nClick «Verify Velantrim key» or «Use key from .env».",
        "err.llmKeyMissing": "⚠️ Paste LLM API key (field below provider).",
        "err.llmConfirmFirst": "Click «Confirm key» first — LLM won't enable without a successful test.",
        "err.llmNotVerified": "⚠️ Key not verified. Click «Confirm key» and wait for ✓.",
        "err.llmKeyInChat": "Paste LLM API key (not the Velantrim key).",
        "err.llmOnNoKey": "⚠️ LLM is on: paste LLM key in the second field (OpenAI / DeepSeek / …).",
        "err.llmNotConfirmed": "⚠️ LLM key not confirmed — click «Confirm key».",
        "err.llmInTopField": "⚠️ Top field looks like an LLM key (sk-… / AIza…).\n\nMove it to «2. LLM API», use VELANTRIM_API_KEY from .env on top.",
        "err.verifyVelantrimBtn": "\n\nClick «Verify Velantrim key» — API and chat test must pass.",
        "err.sendMeta": "Check: 1) Velantrim key 2) LLM key 3) provider 4) restart server",
        "err.sendPrefix": "Error: {msg}",
        "err.keyMeta": "Server key ≠ LLM key",
        "err.llmTestPending": "Testing {provider} / {model}…",
        "err.llmTestOk": "✅ Key verified: {provider} / {model}. Reply: {preview}",
        "err.llmTestBotOk": "✅ LLM key confirmed: {provider} / {model}\n{preview}",
        "err.llmTestFail": "❌ LLM test: {msg}",
        "fact.saved": "Remembered: {text}",
        "fact.fail": "Not saved: {msg}",
        "voice.noApiNeeded": "No API mode — key check not required.",
        "voice.insertOpenai": "Paste OpenAI sk-… key above.",
        "voice.insertGemini": "Paste Gemini AIza… key above.",
        "voice.testingStt": "Testing STT {api}…",
        "voice.keyOk": "Key verified.",
        "voice.response": " Reply: «{text}»",
        "voice.needOpenaiKey": "Set OpenAI sk-… key in «Voice input» on the left.",
        "voice.needGeminiKey": "Set Gemini AIza… key in «Voice input» on the left.",
        "boot.noLlm": "⚠️ Server without LLM API. Stop old uvicorn and run:\nscripts\\start_console.ps1",
        "boot.noChat": "⚠️ No /chat — restart scripts\\start_console.ps1",
        "welcome.bot": "Hello! 🔱\n\nTwo keys:\n1) Top — VELANTRIM_API_KEY from .env (server key)\n2) Below — LLM key (DeepSeek, Gemini, OpenAI…)\n\nThen: provider → «Confirm key» → «LLM on» → chat\n\n🎤 Voice block on the left: no API (free) or Gemini/OpenAI key. 🎤 button is below the chat.",
        "boot.serverDown": "Server unavailable: {msg}\nRun: scripts\\start_console.ps1",
      },
    };

    let currentLang = (() => {
      const saved = localStorage.getItem(LANG_KEY);
      if (VALID_LANGS.includes(saved)) return saved;
      const attr = document.documentElement.getAttribute("data-ui-lang");
      if (VALID_LANGS.includes(attr)) return attr;
      return (navigator.language || "ru").slice(0, 2) === "en" ? "en" : "ru";
    })();

    function t(key, vars) {
      let s = (I18N[currentLang] && I18N[currentLang][key]) || (I18N.ru && I18N.ru[key]) || key;
      if (vars) {
        for (const [k, v] of Object.entries(vars)) {
          s = s.split("{" + k + "}").join(String(v));
        }
      }
      return s;
    }

    function applyStaticI18n() {
      document.title = t("pageTitle");
      document.documentElement.lang = currentLang === "en" ? "en" : "ru";
      document.documentElement.setAttribute("data-ui-lang", currentLang);
      document.querySelectorAll("[data-i18n]").forEach((node) => {
        node.textContent = t(node.dataset.i18n);
      });
      document.querySelectorAll("[data-i18n-html]").forEach((node) => {
        node.innerHTML = t(node.dataset.i18nHtml);
      });
      document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
        node.placeholder = t(node.dataset.i18nPlaceholder);
      });
      document.querySelectorAll("[data-i18n-title]").forEach((node) => {
        node.title = t(node.dataset.i18nTitle);
      });
      document.querySelectorAll("[data-i18n-aria]").forEach((node) => {
        node.setAttribute("aria-label", t(node.dataset.i18nAria));
      });
      const vsel = el("voiceModeSelect");
      if (vsel && vsel.options.length >= 3) {
        vsel.options[0].textContent = t("voice.modeBrowser");
        vsel.options[1].textContent = t("voice.modeGemini");
        vsel.options[2].textContent = t("voice.modeOpenai");
      }
      applySidebarI18n();
    }

    function applySidebarI18n() {
      const map = [
        ["section.velantrim", ".section-block:nth-of-type(1) .section-title"],
        ["section.llm", ".section-block:nth-of-type(2) .section-title"],
        ["section.voice", "#voiceSettingsBlock .section-title"],
        ["section.profile", ".section-block:nth-of-type(4) .section-title"],
      ];
      map.forEach(([key, sel]) => {
        const node = document.querySelector("aside " + sel);
        if (node) node.textContent = t(key);
      });
      const factSum = document.querySelector("aside details summary");
      if (factSum) factSum.textContent = t("section.fact");
      const labels = [
        ["label.apiUrl", "aside .section-block:nth-of-type(1) label"],
        ["label.velantrimKey", "aside .section-block:nth-of-type(1) .field:nth-of-type(2) label"],
        ["label.llmProvider", "#llmProviderSelect", "prev"],
        ["label.llmQuick", "aside .section-block:nth-of-type(2) label[style]"],
        ["label.llmCustomModel", "aside .section-block:nth-of-type(2) .field:nth-of-type(4) label"],
        ["voice.modeLabel", "label[for='voiceModeSelect']"],
      ];
      labels.forEach((item) => {
        if (item[2] === "prev") {
          const sel = el("llmProviderSelect");
          const lab = sel && sel.previousElementSibling;
          if (lab && lab.tagName === "LABEL") lab.textContent = t(item[0]);
          return;
        }
        const node = document.querySelector(item[1]);
        if (node) node.textContent = t(item[0]);
      });
      const extHint = el("apiExternalHint");
      if (extHint) extHint.innerHTML = t("hint.apiExternal");
      const velHint = el("apiVelantrimHint");
      if (velHint && !(typeof serverBootstrap !== "undefined" && serverBootstrap && serverBootstrap.hint)) {
        velHint.innerHTML = t("hint.velantrim");
      }
      const ak = el("apiKey");
      if (ak) ak.placeholder = t("placeholder.velantrimKey");
      const lk = el("llmApiKey");
      if (lk) lk.placeholder = t("placeholder.llmKey");
      const cm = el("llmModelCustom");
      if (cm) cm.placeholder = t("placeholder.customModel");
      const vsk = el("voiceSttApiKey");
      if (vsk && getVoiceMode && getVoiceMode() === "browser") vsk.placeholder = t("voice.placeholderKey");
      const qi = el("queryInput");
      if (qi) qi.placeholder = t("chat.placeholder");
      const fc = el("factClaim");
      if (fc) fc.placeholder = t("fact.placeholder");
      const vst = el("voiceStatusText");
      if (vst && !voiceState.active) vst.textContent = t("voice.listening");
      el("sendBtn") && (el("sendBtn").textContent = t("btn.send"));
      el("saveFactBtn") && (el("saveFactBtn").textContent = t("btn.saveFact"));
      el("voiceCancelBtn") && (el("voiceCancelBtn").textContent = t("btn.cancel"));
      el("verifyVelantrimKeyBtn") && !isVelantrimKeyVerified() && (el("verifyVelantrimKeyBtn").textContent = t("btn.verifyVelantrim"));
      el("voiceSttTestBtn") && !isVoiceSttVerified() && getVoiceMode() !== "browser" && (el("voiceSttTestBtn").textContent = t("voice.testKey"));
      el("llmTestBtn") && !isProviderVerified(state.llmProvider) && (el("llmTestBtn").textContent = t("btn.confirmKey"));
      el("llmTestBtn") && (el("llmTestBtn").title = t("btn.confirmKeyTitle"));
      document.querySelectorAll("[data-copy-for='apiBaseUrl']").forEach((b) => {
        b.title = t("copy.url");
        b.setAttribute("aria-label", t("copy.url"));
      });
      document.querySelectorAll("[data-copy-for='apiKey']").forEach((b) => {
        b.title = t("copy.key");
        b.setAttribute("aria-label", t("copy.key"));
      });
      document.querySelectorAll("[data-copy-for='llmApiKey']").forEach((b) => {
        b.title = t("copy.llmKey");
        b.setAttribute("aria-label", t("copy.llmKey"));
      });
      document.querySelectorAll(".clear-field-btn").forEach((b) => {
        b.title = t("btn.clear");
        b.setAttribute("aria-label", t("btn.clear"));
      });
      const banner = el("llmActiveBanner");
      if (banner && banner.textContent.trim().startsWith("П") || banner && banner.textContent.trim().startsWith("P")) {
        /* refreshed in applyProviderToForm */
      }
    }

    function getThemeCatalog() {
      return [
        { id: "dark", icon: "🌙", short: t("theme.darkShort"), title: t("theme.darkTitle") },
        { id: "light", icon: "☀️", short: t("theme.lightShort"), title: t("theme.lightTitle") },
        { id: "skeu", icon: "🧱", short: t("theme.skeuShort"), title: t("theme.skeuTitle") },
        { id: "volumetric", icon: "🧊", short: t("theme.volShort"), title: t("theme.volTitle") },
        { id: "volumetric-light", icon: "💎", short: t("theme.volLightShort"), title: t("theme.volLightTitle") },
        { id: "book", icon: "📖", short: t("theme.bookShort"), title: t("theme.bookTitle") },
        { id: "neon", icon: "⚡", short: t("theme.neonShort"), title: t("theme.neonTitle") },
      ];
    }

    function getLlmHintBase() {
      return t("hint.llmBase");
    }

    function getGeminiSetupHint() {
      return t("hint.geminiSetup");
    }

    function setLanguage(lang) {
      if (!VALID_LANGS.includes(lang)) return;
      currentLang = lang;
      localStorage.setItem(LANG_KEY, lang);
      applyStaticI18n();
      renderLangPicker();
      renderThemeGrid();
      updateTtsToggleUi();
      updateLlmToggleUi();
      updateVoiceModeUi();
      refreshLlmProviderHint();
      if (lastLlmProviders && lastLlmProviders.length) {
        renderLlmGrid(lastLlmProviders);
        const cur = getProviderById(state.llmProvider);
        if (cur) applyProviderToForm(cur);
      }
      if (lastProfiles && lastProfiles.length) {
        renderProfileGrid(lastProfiles);
        refreshProfileHint();
      }
      refreshStatusPills();
    }

    function renderLangPicker() {
      const grid = el("langGrid");
      if (!grid) return;
      grid.innerHTML = "";
      LANG_CATALOG.forEach((L) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "lang-icon-btn" + (currentLang === L.id ? " active" : "");
        btn.dataset.langPick = L.id;
        btn.title = L.title;
        btn.setAttribute("aria-label", L.title);
        btn.setAttribute("aria-pressed", currentLang === L.id ? "true" : "false");
        btn.innerHTML = `<span class="lang-flag" aria-hidden="true">${L.flag}</span><span class="lang-code">${L.code}</span>`;
        btn.addEventListener("click", () => setLanguage(L.id));
        grid.appendChild(btn);
      });
    }

    function refreshProfileHint() {
      const cur = lastProfiles.find((p) => p.id === state.profile) || null;
      const box = el("serverProfileHint");
      if (!box) return;
      if (cur) {
        box.innerHTML = t("profile.server", { emoji: cur.emoji || "", title: cur.title || cur.id });
      } else {
        box.textContent = t("profile.none");
      }
    }
