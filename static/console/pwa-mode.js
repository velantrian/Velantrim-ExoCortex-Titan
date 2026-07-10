/**
 * VELANTRIM PWA Mode — детектор и мост.
 * Внедряется в index.html при сборке для GitHub Pages.
 * На localhost самоотключается.
 */
;(function () {
  if (typeof window === "undefined") return;

  var host = window.location.hostname || "";
  var isPWA = host.endsWith("github.io") || host === "velantrian.github.io";
  var isLocal = host === "127.0.0.1" || host === "localhost" || host.startsWith("192.168.") || host.startsWith("10.");

  // ── Загрузка pwa-core.js (только в PWA-режиме) ──
  if (isPWA) {
    var script = document.createElement("script");
    script.src = "./pwa-core.js?v=3";
    script.onload = function () { initPWAMode(); };
    script.onerror = function () {
      console.warn("VELANTRIM PWA: не удалось загрузить pwa-core.js — работаем как статическая витрина");
    };
    document.head.appendChild(script);
  }

  function initPWAMode() {
    var PWA = window.VELANTRIM_PWA;
    if (!PWA) return;

    // ── Сохраняем оригинальные функции ──
    var _origApi = window.api;
    var _origFetch = window.fetch;

    // ── PWA API proxy ──
    window.api = function (path, opts) {
      opts = opts || {};

      // Проксируем запросы к LLM напрямую
      if (path === "/chat/stream" || path === "/console/chat/stream") {
        return pwaChatStreamProxy(opts);
      }

      // Заметки → IndexedDB
      if (path.startsWith("/console/notes")) {
        return PWA.api(path, opts);
      }

      // LLM провайдеры → локальный каталог
      if (path.startsWith("/console/llm/")) {
        return PWA.api(path, opts);
      }

      // Авторизация → всегда ok
      if (path.startsWith("/console/auth/")) {
        return Promise.resolve({ ok: true, mode: "pwa" });
      }

      // Bootstrap
      if (path === "/console/bootstrap") {
        return PWA.api(path, opts).then(function (r) { return r.json(); });
      }

      // Debug
      if (path === "/debug/console") {
        return PWA.api(path, opts).then(function (r) { return r.json(); });
      }

      // /query → локальный поиск
      if (path === "/query") {
        return pwaQueryProxy(opts);
      }

      // /health
      if (path === "/health") {
        return Promise.resolve({ status: "ok", mode: "pwa" });
      }

      // /profiles
      if (path === "/profiles") {
        return Promise.resolve({ profiles: [], current: { id: "pwa" }, mode: "pwa" });
      }

      // Всё остальное → заглушка
      return Promise.reject(new Error("PWA: эндпоинт " + path + " недоступен без сервера"));
    };

    // ── PWA Chat Stream ──
    function pwaChatStreamProxy(opts) {
      var body = JSON.parse(opts.body || "{}");
      var query = body.query || body.message || "";
      var history = body.history || body.messages || [];
      var provider = body.provider || "deepseek";

      return new Promise(function (resolve, reject) {
        var fullText = "";
        PWA.chatStream(query, history, provider,
          function (delta) {
            fullText += delta;
            // Отправляем событие в UI для стриминга
            var ev = new CustomEvent("velantrim:pwa:delta", { detail: { text: delta, full: fullText } });
            window.dispatchEvent(ev);
          },
          function () {
            resolve({ answer: fullText, ok: true });
          },
          function (err) {
            reject(err);
          }
        );
      });
    }

    // ── PWA Query (локальный поиск по фактам + LLM) ──
    function pwaQueryProxy(opts) {
      var body = JSON.parse(opts.body || "{}");
      var query = body.query || body.q || "";

      return PWA.searchFacts(query).then(function (facts) {
        // Если есть факты — возвращаем их
        if (facts && facts.length > 0) {
          var results = facts.slice(0, 10).map(function (f) {
            return {
              claim: f.claim || "",
              layer: f.layer || "L1",
              state: f.state || "Observed",
              confidence: f.confidence || 0.5,
              memory_store: "pwa_indexeddb",
            };
          });
          return { results: results, count: results.length, mode: "pwa" };
        }
        return { results: [], count: 0, mode: "pwa", hint: "Память пуста. Добавьте факты через Research App или чат." };
      });
    }

    // ── Патч fetch: чат, TTS/STT, LLM-провайдеры и тест ключа ──
    var _realFetch = window.fetch;
    window.fetch = function (url, opts) {
      var urlStr = String(url);
      opts = opts || {};

      if (urlStr.indexOf("/chat/stream") >= 0 || urlStr.indexOf("/console/chat") >= 0) {
        return pwaChatFetch(urlStr, opts);
      }

      if (urlStr.indexOf("/console/llm/providers") >= 0 || urlStr.indexOf("/llm/providers") >= 0) {
        var provs = PWA.getProvidersForConsole();
        return Promise.resolve(new Response(
          JSON.stringify({ providers: provs, catalog_build_id: "pwa-v2", mode: "pwa" }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        ));
      }

      if (urlStr.indexOf("/console/llm/test") >= 0 || urlStr.indexOf("/llm/test") >= 0) {
        try {
          var body = JSON.parse(opts.body || "{}");
          return PWA.testLLMKey(body.provider, body.api_key, body.model).then(function (res) {
            return new Response(JSON.stringify(res), {
              status: 200,
              headers: { "Content-Type": "application/json" },
            });
          }).catch(function (err) {
            return new Response(JSON.stringify({ error: err.message }), {
              status: 400,
              headers: { "Content-Type": "application/json" },
            });
          });
        } catch (e) {
          return Promise.resolve(new Response(
            JSON.stringify({ error: e.message }),
            { status: 400, headers: { "Content-Type": "application/json" } }
          ));
        }
      }

      if (urlStr.indexOf("/console/bootstrap") >= 0) {
        return Promise.resolve(new Response(
          JSON.stringify({
            auth_required: false,
            allow_open: true,
            mode: "pwa",
            hint: "PWA: ключ LLM — в блоке слева «API LLM».",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        ));
      }

      if (urlStr.indexOf("/debug/console") >= 0) {
        return Promise.resolve(new Response(
          JSON.stringify({
            mode: "pwa",
            features: { chat_endpoint: true },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        ));
      }

      if (urlStr.indexOf("/console/tts/") >= 0) {
        return pwaTtsFetch(urlStr, opts);
      }

      if (urlStr.indexOf("/console/stt/") >= 0) {
        return pwaSttFetch(urlStr, opts);
      }

      return _realFetch.call(window, url, opts);
    };

    function pwaChatFetch(url, opts) {
      var body = JSON.parse(opts.body || "{}");
      var query = body.message || body.query || "";
      var history = body.chat_history || body.history || body.messages || [];
      var provider = body.llm_provider || body.provider || "deepseek";
      var apiKey = body.llm_api_key || body.api_key || "";
      var model = body.llm_model || body.model || "";

      // Нормализуем историю в формат {role, content}
      var msgs = [];
      for (var i = 0; i < history.length; i++) {
        var h = history[i];
        if (!h) continue;
        var role = h.role || (h.from === "user" ? "user" : "assistant");
        var content = h.content || h.text || h.message || "";
        if (content) msgs.push({ role: role, content: content });
      }

      var stream = new ReadableStream({
        start: function (controller) {
          var encoder = new TextEncoder();
          var fullText = "";

          function push(ev) {
            controller.enqueue(encoder.encode("data: " + JSON.stringify(ev) + "\n\n"));
          }

          PWA.chatStream(
            query,
            msgs,
            provider,
            function (delta) {
              fullText += delta;
              push({ type: "token", text: delta });
            },
            function () {
              push({ type: "done", reply: fullText });
              push({
                type: "final",
                reply: fullText,
                from_llm: true,
                llm_provider: provider,
                llm_model: model,
              });
              controller.close();
            },
            function (err) {
              push({ type: "error", message: err.message || String(err) });
              controller.close();
            },
            apiKey,
            model
          );
        },
      });

      return Promise.resolve(new Response(stream, {
        status: 200,
        headers: { "Content-Type": "text/event-stream" },
      }));
    }

    function pwaTtsFetch(url, opts) {
      var body = JSON.parse(opts.body || "{}");
      var text = body.text || body.message || "";
      var lang = body.lang || "ru-RU";
      var rate = parseFloat(body.rate) || 1.0;

      // Используем Web Speech API
      try {
        var u = new SpeechSynthesisUtterance(text);
        u.lang = lang;
        u.rate = rate;
        window.speechSynthesis.speak(u);
        return Promise.resolve(new Response(
          '{"ok":true,"mode":"pwa_webspeech"}',
          { status: 200, headers: { "Content-Type": "application/json" } }
        ));
      } catch (_) {
        return Promise.resolve(new Response(
          '{"ok":false,"error":"Web Speech API не поддерживается"}',
          { status: 200, headers: { "Content-Type": "application/json" } }
        ));
      }
    }

    function pwaSttFetch(url, opts) {
      return new Promise(function (resolve) {
        var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) {
          resolve(new Response(
            '{"text":"","ok":false,"error":"not_supported"}',
            { status: 200, headers: { "Content-Type": "application/json" } }
          ));
          return;
        }
        var rec = new SR();
        rec.lang = "ru-RU";
        rec.interimResults = false;
        rec.onresult = function (e) {
          var text = e.results[0][0].transcript;
          resolve(new Response(
            JSON.stringify({ text: text, ok: true }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          ));
        };
        rec.onerror = function () {
          resolve(new Response(
            JSON.stringify({ text: "", ok: false, error: "recognition_failed" }),
            { status: 200, headers: { "Content-Type": "application/json" } }
          ));
        };
        rec.start();
      });
    }

    // ── UI: левая панель (без верхней полосы) ──
    function adaptSidebarForPWA() {
      document.documentElement.setAttribute("data-pwa-mode", "1");

      var serverBlock = document.getElementById("serverKeyBlock");
      if (serverBlock) serverBlock.style.display = "none";

      var llmBlock = document.getElementById("llmSettingsBlock");
      if (llmBlock) {
        var title = llmBlock.querySelector(".section-title");
        if (title) title.textContent = "🤖 2. API LLM (DeepSeek, Gemini, …)";
      }

      var hint = document.getElementById("llmHint");
      if (hint) {
        hint.innerHTML =
          "Ключ хранится в браузере. Выберите провайдера, вставьте API-ключ ниже, нажмите «Подтвердить ключ», затем «LLM включён». " +
          "Полная консоль с SQLite — через <code>scripts\\start_console.ps1</code> на ПК.";
      }

      // Синхронизация ключей: при сохранении в форме консоли → PWA storage
      var llmKeyInput = document.getElementById("llmApiKey");
      if (llmKeyInput) {
        llmKeyInput.addEventListener("change", function () {
          var provSel = document.getElementById("llmProviderSelect");
          var pid = provSel ? provSel.value : "deepseek";
          var key = llmKeyInput.value.trim();
          if (key) {
            var all = PWA.getLLMKeys();
            all[pid] = key;
            PWA.saveLLMKeys(all);
          }
        });
      }
    }

    function showToast(msg) {
      var t = document.createElement("div");
      t.style.cssText =
        "position:fixed;bottom:1rem;left:50%;transform:translateX(-50%);z-index:99999;" +
        "background:var(--panel,#1a2332);border:1px solid var(--accent,#3d8bfd);" +
        "color:var(--text,#e7ecf3);padding:.5rem 1rem;border-radius:8px;" +
        "font:13px Segoe UI,system-ui,sans-serif";
      t.textContent = msg;
      document.body.appendChild(t);
      setTimeout(function () { t.remove(); }, 2500);
    }

    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", adaptSidebarForPWA);
    } else {
      adaptSidebarForPWA();
    }
  }
})();
