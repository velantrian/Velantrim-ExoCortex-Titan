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
    script.src = "./pwa-core.js?v=2";
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

    // ── PWA Chat Handler (не-стриминг) ──
    // Патчим прямой fetch к /chat/stream для PWA
    var _realFetch = window.fetch;
    window.fetch = function (url, opts) {
      var urlStr = String(url);

      if (urlStr.indexOf("/chat/stream") >= 0 || urlStr.indexOf("/console/chat") >= 0) {
        return pwaChatFetch(urlStr, opts);
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
      var query = body.query || body.message || "";
      var history = body.history || body.messages || [];
      var provider = body.provider || "deepseek";

      return PWA.openDB().then(function () {
        return new Promise(function (resolve, reject) {
          var fullText = "";
          var aborted = false;
          var reader = {
            read: function () { return new Promise(function () {}); },
            cancel: function () { aborted = true; },
            getReader: function () { return reader; },
          };

          PWA.chatStream(query, history, provider,
            function (delta) {
              fullText += delta;
            },
            function () {
              var resp = new Response(
                'data: ' + JSON.stringify({ choices: [{ delta: { content: fullText }, finish_reason: "stop" }] }) + '\n\ndata: [DONE]\n',
                { status: 200, headers: { "Content-Type": "text/event-stream" } }
              );
              resolve(resp);
            },
            function (err) {
              var resp = new Response(
                JSON.stringify({ error: err.message }),
                { status: 500, headers: { "Content-Type": "application/json" } }
              );
              resolve(resp);
            }
          );
        });
      });
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

    // ── UI: LLM Keys Panel ──
    function injectLLMKeysUI() {
      var banner = document.createElement("div");
      banner.id = "pwa-llm-panel";
      banner.style.cssText = "position:fixed;top:0;left:0;right:0;z-index:99999;background:#1a2332;border-bottom:1px solid #3d8bfd;padding:.6rem .9rem;font:13px/1.4 Segoe UI,system-ui,sans-serif;color:#e7ecf3;display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;justify-content:center";
      banner.innerHTML =
        '<span style="color:#3d8bfd;font-weight:700">⚡ PWA</span>' +
        '<select id="pwa-provider" style="font:inherit;border:1px solid #2d3a4f;border-radius:6px;background:#0f1419;color:var(--text);padding:.35rem .5rem">' +
          '<option value="deepseek">DeepSeek</option>' +
          '<option value="openai">OpenAI</option>' +
          '<option value="google">Gemini</option>' +
        '</select>' +
        '<input id="pwa-apikey" type="password" placeholder="API-ключ LLM..." style="font:inherit;border:1px solid #2d3a4f;border-radius:6px;background:#0f1419;color:var(--text);padding:.35rem .5rem;width:260px">' +
        '<button id="pwa-save-key" style="font:inherit;border:1px solid #3d8bfd;border-radius:6px;background:#3d8bfd;color:#fff;padding:.35rem .65rem;cursor:pointer;font-weight:650">💾 Сохранить</button>' +
        '<button id="pwa-toggle-panel" style="font:inherit;border:1px solid #2d3a4f;border-radius:6px;background:transparent;color:#8b9cb3;padding:.35rem .65rem;cursor:pointer">−</button>';

      document.body.insertBefore(banner, document.body.firstChild);

      // Загрузка сохранённых ключей
      var keys = PWA.getLLMKeys();
      var activeProv = Object.keys(keys)[0] || "deepseek";
      var sel = document.getElementById("pwa-provider");
      if (sel) sel.value = activeProv;
      var inp = document.getElementById("pwa-apikey");
      if (inp) inp.value = keys[activeProv] || "";

      // Сохранение
      document.getElementById("pwa-save-key").onclick = function () {
        var prov = sel.value;
        var key = inp.value.trim();
        var allKeys = PWA.getLLMKeys();
        allKeys[prov] = key;
        PWA.saveLLMKeys(allKeys);
        showToast("Ключ " + prov + " сохранён ✓");
      };

      // Смена провайдера
      sel.onchange = function () {
        var allKeys = PWA.getLLMKeys();
        inp.value = allKeys[sel.value] || "";
      };

      // Свернуть панель
      var expanded = true;
      document.getElementById("pwa-toggle-panel").onclick = function () {
        expanded = !expanded;
        this.textContent = expanded ? "−" : "+";
        [sel, inp, document.getElementById("pwa-save-key")].forEach(function (el) {
          if (el) el.style.display = expanded ? "" : "none";
        });
      };
    }

    function showToast(msg) {
      var t = document.createElement("div");
      t.style.cssText = "position:fixed;bottom:1rem;left:50%;transform:translateX(-50%);z-index:99999;background:#1a2332;border:1px solid #3d8bfd;color:#e7ecf3;padding:.5rem 1rem;border-radius:8px;font:13px Segoe UI,system-ui,sans-serif";
      t.textContent = msg;
      document.body.appendChild(t);
      setTimeout(function () { t.remove(); }, 2500);
    }

    // Внедряем UI после загрузки DOM
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", injectLLMKeysUI);
    } else {
      injectLLMKeysUI();
    }
  }
})();
