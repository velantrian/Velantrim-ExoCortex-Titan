/**
 * VELANTRIM PWA Core — IndexedDB + прямые LLM API без Python-сервера.
 * Подключается только на GitHub Pages; на localhost работает стандартный API.
 */
;(function () {
  if (typeof window === "undefined") return;

  const KEY = {
    db: "velantrim_pwa_v1",
    chatArchive: "velantrim_titan_console_chatArchive",
    llmKeys: "velantrim_titan_console_llmKeys",
    settings: "velantrim_titan_console_settings",
    latestChat: "velantrim_titan_console_latestChat",
  };

  // ──────────────────────────── IndexedDB ────────────────────────────

  function openDB() {
    return new Promise(function (resolve, reject) {
      var req = indexedDB.open(KEY.db, 1);
      req.onerror = function () { reject(req.error); };
      req.onupgradeneeded = function () {
        var db = req.result;
        if (!db.objectStoreNames.contains("chats")) db.createObjectStore("chats", { keyPath: "id" });
        if (!db.objectStoreNames.contains("facts")) db.createObjectStore("facts", { keyPath: "id", autoIncrement: true });
        if (!db.objectStoreNames.contains("notes")) db.createObjectStore("notes", { keyPath: "id" });
        if (!db.objectStoreNames.contains("settings")) db.createObjectStore("settings", { keyPath: "key" });
      };
      req.onsuccess = function () { resolve(req.result); };
    });
  }

  function dbPut(storeName, value) {
    return openDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var tx = db.transaction(storeName, "readwrite");
        tx.objectStore(storeName).put(value);
        tx.oncomplete = function () { db.close(); resolve(); };
        tx.onerror = function () { db.close(); reject(tx.error); };
      });
    });
  }

  function dbGet(storeName, key) {
    return openDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var tx = db.transaction(storeName, "readonly");
        var req = tx.objectStore(storeName).get(key);
        req.onsuccess = function () { db.close(); resolve(req.result); };
        req.onerror = function () { db.close(); reject(req.error); };
      });
    });
  }

  function dbGetAll(storeName) {
    return openDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var tx = db.transaction(storeName, "readonly");
        var req = tx.objectStore(storeName).getAll();
        req.onsuccess = function () { db.close(); resolve(req.result); };
        req.onerror = function () { db.close(); reject(req.error); };
      });
    });
  }

  function dbDelete(storeName, key) {
    return openDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var tx = db.transaction(storeName, "readwrite");
        tx.objectStore(storeName).delete(key);
        tx.oncomplete = function () { db.close(); resolve(); };
        tx.onerror = function () { db.close(); reject(tx.error); };
      });
    });
  }

  // ──────────────────────── LLM Providers ────────────────────────────

  function getLLMKeys() {
    try {
      return JSON.parse(localStorage.getItem(KEY.llmKeys) || "{}");
    } catch (_) {
      return {};
    }
  }

  function saveLLMKeys(keys) {
    localStorage.setItem(KEY.llmKeys, JSON.stringify(keys));
  }

  var PROVIDERS = {
    deepseek: {
      id: "deepseek",
      name: "DeepSeek",
      models: ["deepseek-chat", "deepseek-v4-pro", "deepseek-v4-flash"],
      endpoint: "https://api.deepseek.com/v1/chat/completions",
      authHeader: function (key) { return "Bearer " + key; },
    },
    openai: {
      id: "openai",
      name: "OpenAI",
      models: ["gpt-4o", "gpt-5.5", "gpt-4o-mini"],
      endpoint: "https://api.openai.com/v1/chat/completions",
      authHeader: function (key) { return "Bearer " + key; },
    },
    gemini: {
      id: "gemini",
      name: "Gemini (Google)",
      models: ["gemini-2.5-flash", "gemini-2.5-pro"],
      endpoint: function (model) {
        return "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent?key={KEY}";
      },
      authHeader: function () { return ""; },
      bodyTransform: function (body) {
        var msgs = body.messages || [];
        var contents = msgs.map(function (m) {
          return {
            role: m.role === "assistant" ? "model" : "user",
            parts: [{ text: m.content || "" }],
          };
        });
        return {
          contents: contents,
          generationConfig: {
            temperature: body.temperature || 0.7,
            maxOutputTokens: body.max_tokens || 2048,
          },
        };
      },
      responseTransform: function (data) {
        var text = "";
        try {
          var parts = data.candidates[0].content.parts;
          for (var i = 0; i < parts.length; i++) {
            text += parts[i].text || "";
          }
        } catch (_) {}
        return { choices: [{ message: { content: text } }] };
      },
    },
  };

  function getActiveProvider() {
    var keys = getLLMKeys();
    for (var pid in PROVIDERS) {
      if (keys[pid]) return pid;
    }
    return "deepseek";
  }

  /** Список провайдеров в формате консоли (для левой панели). */
  function getProvidersForConsole() {
    var keys = getLLMKeys();
    return Object.keys(PROVIDERS).map(function (pid) {
      var p = PROVIDERS[pid];
      return {
        id: p.id,
        title: p.name,
        default_model: p.models[0],
        models: p.models.slice(),
        configured: !!keys[pid],
      };
    });
  }

  /** Тест ключа LLM (как /console/llm/test на сервере). */
  function testLLMKey(provider, apiKey, model) {
    var msgs = [{ role: "user", content: "Ответь одним словом: OK" }];
    return callLLM(msgs, { provider: provider, api_key: apiKey, model: model || undefined }).then(function (data) {
      var preview = "";
      try { preview = (data.choices[0].message.content || "").slice(0, 120); } catch (_) {}
      return {
        provider: provider,
        model: model || PROVIDERS[provider].models[0],
        reply_preview: preview || "OK",
        mode: "pwa",
      };
    });
  }

  function callLLM(messages, opts) {
    opts = opts || {};
    var pid = opts.provider || getActiveProvider();
    var prov = PROVIDERS[pid];
    var keys = getLLMKeys();
    var key = opts.api_key || keys[pid] || "";
    if (!key) {
      return Promise.reject(new Error("API-ключ для " + (prov ? prov.name : pid) + " не задан. Нажмите ⚙️ → Ключи LLM."));
    }

    var model = opts.model || prov.models[0];
    var body = {
      model: model,
      messages: messages,
      temperature: opts.temperature || 0.7,
      max_tokens: opts.max_tokens || 2048,
      stream: false,
    };

    var url = typeof prov.endpoint === "function" ? prov.endpoint(model) : prov.endpoint;
    url = url.replace("{KEY}", encodeURIComponent(key));

    if (prov.bodyTransform && typeof prov.bodyTransform === "function") {
      body = prov.bodyTransform(body);
    }

    var headers = { "Content-Type": "application/json" };
    var auth = prov.authHeader(key);
    if (auth) headers["Authorization"] = auth;

    return fetch(url, {
      method: "POST",
      headers: headers,
      body: JSON.stringify(body),
    }).then(function (r) {
      if (!r.ok) {
        return r.json().then(function (e) {
          throw new Error(pid + ": " + (e.error ? e.error.message || JSON.stringify(e.error) : r.status + " " + r.statusText));
        });
      }
      return r.json();
    }).then(function (data) {
      if (prov.responseTransform) data = prov.responseTransform(data);
      return data;
    });
  }

  function callLLMStream(messages, opts, onDelta, onDone, onError) {
    opts = opts || {};
    var pid = opts.provider || getActiveProvider();
    var prov = PROVIDERS[pid];
    var keys = getLLMKeys();
    var key = opts.api_key || keys[pid] || "";
    if (!key) {
      if (onError) onError(new Error("API-ключ для " + (prov ? prov.name : pid) + " не задан. Вставьте ключ в блок «API LLM» слева."));
      return;
    }

    var model = opts.model || prov.models[0];
    var body = {
      model: model,
      messages: messages,
      temperature: opts.temperature || 0.7,
      max_tokens: opts.max_tokens || 2048,
      stream: true,
    };

    if (pid === "gemini") {
      // Gemini streaming differs — fallback to non-streaming
      callLLM(messages, opts).then(function (data) {
        var text = "";
        try { text = data.choices[0].message.content; } catch (_) {}
        if (onDelta) onDelta(text);
        if (onDone) onDone(text);
      }).catch(function (e) { if (onError) onError(e); });
      return;
    }

    var url = typeof prov.endpoint === "function" ? prov.endpoint(model).replace(":generateContent", ":streamGenerateContent") : prov.endpoint;
    url = url.replace("{KEY}", encodeURIComponent(key));

    var headers = { "Content-Type": "application/json" };
    var auth = prov.authHeader(key);
    if (auth) headers["Authorization"] = auth;

    fetch(url, { method: "POST", headers: headers, body: JSON.stringify(body) }).then(function (r) {
      if (!r.ok) {
        return r.json().then(function (e) {
          throw new Error(pid + ": " + (e.error ? e.error.message || JSON.stringify(e.error) : r.status + " " + r.statusText));
        });
      }
      var reader = r.body.getReader();
      var decoder = new TextDecoder();
      var buffer = "";

      function pump() {
        reader.read().then(function (_a) {
          var done = _a.done;
          var chunk = _a.value;
          if (done) {
            if (onDone) onDone(buffer);
            return;
          }
          var text = decoder.decode(chunk, { stream: true });
          var lines = text.split("\n");
          for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim();
            if (!line || !line.startsWith("data: ")) continue;
            var payload = line.slice(6);
            if (payload === "[DONE]") { if (onDone) onDone(buffer); return; }
            try {
              var js = JSON.parse(payload);
              var delta = "";
              if (js.choices && js.choices[0] && js.choices[0].delta && js.choices[0].delta.content) {
                delta = js.choices[0].delta.content;
              }
              if (delta) {
                buffer += delta;
                if (onDelta) onDelta(delta);
              }
            } catch (_) {}
          }
          pump();
        }).catch(function (e) { if (onError) onError(e); });
      }
      pump();
    }).catch(function (e) { if (onError) onError(e); });
  }

  // ──────────────────────── Chat Archive ─────────────────────────────

  function saveChat(chatId, messages, title) {
    var archive = JSON.parse(localStorage.getItem(KEY.chatArchive) || "[]");
    var existing = -1;
    for (var i = 0; i < archive.length; i++) {
      if (archive[i].id === chatId) { existing = i; break; }
    }
    var entry = {
      id: chatId,
      title: title || "Чат " + new Date().toLocaleString(),
      updated_at: new Date().toISOString(),
      messages: messages.slice(-200),
    };
    if (existing >= 0) archive[existing] = entry;
    else archive.unshift(entry);
    if (archive.length > 50) archive = archive.slice(0, 50);
    localStorage.setItem(KEY.chatArchive, JSON.stringify(archive));
    // Also save latest
    localStorage.setItem(KEY.latestChat, JSON.stringify({ id: chatId, messages: messages }));
  }

  function loadChat(chatId) {
    var archive = JSON.parse(localStorage.getItem(KEY.chatArchive) || "[]");
    for (var i = 0; i < archive.length; i++) {
      if (archive[i].id === chatId) return archive[i];
    }
    return null;
  }

  function listChats() {
    return JSON.parse(localStorage.getItem(KEY.chatArchive) || "[]");
  }

  function deleteChat(chatId) {
    var archive = JSON.parse(localStorage.getItem(KEY.chatArchive) || "[]");
    archive = archive.filter(function (c) { return c.id !== chatId; });
    localStorage.setItem(KEY.chatArchive, JSON.stringify(archive));
  }

  // ──────────────────────── Fact Memory ──────────────────────────────

  function saveFact(fact) {
    return dbPut("facts", fact);
  }

  function getFacts() {
    return dbGetAll("facts");
  }

  function searchFacts(query) {
    var qs = String(query).toLowerCase();
    return getFacts().then(function (facts) {
      return facts.filter(function (f) {
        return (f.claim || "").toLowerCase().indexOf(qs) >= 0 ||
               (f.layer || "").toLowerCase().indexOf(qs) >= 0 ||
               (f.state || "").toLowerCase().indexOf(qs) >= 0;
      });
    });
  }

  // ──────────────────────── Notes ────────────────────────────────────

  function saveNote(note) {
    note.id = note.id || "note_" + Date.now();
    note.updated_at = new Date().toISOString();
    return dbPut("notes", note).then(function () { return note; });
  }

  function getNotes(limit) {
    limit = limit || 50;
    return dbGetAll("notes").then(function (notes) {
      return notes.sort(function (a, b) {
        return (b.updated_at || "").localeCompare(a.updated_at || "");
      }).slice(0, limit);
    });
  }

  function deleteNote(noteId) {
    return dbDelete("notes", noteId);
  }

  // ──────────────────────── Settings ─────────────────────────────────

  function saveSetting(key, value) {
    return dbPut("settings", { key: key, value: value });
  }

  function getSetting(key) {
    return dbGet("settings", key).then(function (row) {
      return row ? row.value : undefined;
    });
  }

  // ──────────────────────── PWA Mock API ─────────────────────────────

  function pwaApi(path, opts) {
    opts = opts || {};

    // /console/notes
    if (path === "/console/notes" && opts.method === "POST") {
      return saveNote(JSON.parse(opts.body)).then(function (n) {
        return { json: function () { return Promise.resolve(n); }, ok: true, status: 201 };
      });
    }
    if (path.startsWith("/console/notes/") && path.endsWith("/edit") && opts.method === "POST") {
      var nid = path.split("/")[3];
      var data = JSON.parse(opts.body);
      return dbGet("notes", nid).then(function (note) {
        note.content = data.content || note.content;
        note.title = data.title || note.title;
        note.updated_at = new Date().toISOString();
        return dbPut("notes", note).then(function () {
          return { json: function () { return Promise.resolve(note); }, ok: true, status: 200 };
        });
      });
    }
    if (path.startsWith("/console/notes/") && opts.method === "DELETE") {
      var did = path.split("/")[3];
      return deleteNote(did).then(function () {
        return { json: function () { return Promise.resolve({ ok: true }); }, ok: true, status: 200 };
      });
    }
    if (path.startsWith("/console/notes") && (opts.method === "GET" || !opts.method)) {
      var lim = parseInt(path.split("limit=")[1] || "50");
      return getNotes(lim).then(function (notes) {
        return { json: function () { return Promise.resolve(notes); }, ok: true, status: 200 };
      });
    }

    // /console/bootstrap
    if (path === "/console/bootstrap") {
      return Promise.resolve({
        json: function () {
          return Promise.resolve({
            console_index: "pwa",
            auth_required: false,
            velantrim_key_analysis: { auth_required: false, allow_open: true },
            server_status: "pwa_standalone",
            mode: "pwa",
          });
        },
        ok: true, status: 200,
      });
    }

    // /console/llm/providers
    if (path === "/console/llm/providers") {
      var keys = getLLMKeys();
      var provs = [];
      for (var pid in PROVIDERS) {
        provs.push({
          id: PROVIDERS[pid].id,
          name: PROVIDERS[pid].name,
          models: PROVIDERS[pid].models,
          configured: !!keys[pid],
        });
      }
      return Promise.resolve({
        json: function () { return Promise.resolve({ providers: provs, catalog_build_id: "pwa-" + Date.now(), mode: "pwa" }); },
        ok: true, status: 200,
      });
    }

    // /console/auth/check, /console/auth/verify
    if (path.startsWith("/console/auth/")) {
      return Promise.resolve({
        json: function () { return Promise.resolve({ ok: true, mode: "pwa" }); },
        ok: true, status: 200,
      });
    }

    // /health
    if (path === "/health") {
      return Promise.resolve({
        json: function () { return Promise.resolve({ status: "ok", mode: "pwa" }); },
        ok: true, status: 200,
      });
    }

    // /debug/console
    if (path === "/debug/console") {
      return getFacts().then(function (facts) {
        return {
          json: function () { return Promise.resolve({ mode: "pwa", facts_count: facts.length, providers: Object.keys(PROVIDERS) }); },
          ok: true, status: 200,
        };
      });
    }

    return Promise.reject(new Error("PWA: неизвестный эндпоинт " + path));
  }

  // ──────────────────────── PWA Chat Handler ─────────────────────────

  function pwaChat(query, history, provider) {
    provider = provider || getActiveProvider();
    var msgs = history || [];
    msgs = msgs.concat([{ role: "user", content: query }]);
    return callLLM(msgs, { provider: provider }).then(function (data) {
      var answer = "";
      try { answer = data.choices[0].message.content; } catch (_) {}
      return { answer: answer, messages: msgs.concat([{ role: "assistant", content: answer }]) };
    });
  }

  function pwaChatStream(query, history, provider, onDelta, onDone, onError, apiKey, model) {
    provider = provider || getActiveProvider();
    var msgs = history || [];
    msgs = msgs.concat([{ role: "user", content: query }]);
    callLLMStream(msgs, { provider: provider, api_key: apiKey, model: model }, onDelta, onDone, onError);
  }

  // ──────────────────────── TTS (Web Speech API) ─────────────────────

  function pwaTtsSpeak(text, lang, rate) {
    return new Promise(function (resolve, reject) {
      if (!window.speechSynthesis) return reject(new Error("Web Speech API не поддерживается"));
      var u = new SpeechSynthesisUtterance(text);
      u.lang = lang || "ru-RU";
      u.rate = rate || 1.0;
      u.onend = resolve;
      u.onerror = reject;
      window.speechSynthesis.speak(u);
    });
  }

  // ──────────────────────── STT (Web Speech API) ─────────────────────

  function pwaSttListen(lang) {
    return new Promise(function (resolve, reject) {
      if (!window.SpeechRecognition && !window.webkitSpeechRecognition) {
        return reject(new Error("Speech Recognition не поддерживается"));
      }
      var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      var rec = new SR();
      rec.lang = lang || "ru-RU";
      rec.interimResults = false;
      rec.continuous = false;
      rec.onresult = function (e) { resolve(e.results[0][0].transcript); };
      rec.onerror = function (e) { reject(e.error); };
      rec.start();
    });
  }

  // ──────────────────────── Export ────────────────────────────────────

  window.VELANTRIM_PWA = {
    mode: "pwa",
    api: pwaApi,
    chat: pwaChat,
    chatStream: pwaChatStream,
    saveChat: saveChat,
    loadChat: loadChat,
    listChats: listChats,
    deleteChat: deleteChat,
    saveFact: saveFact,
    getFacts: getFacts,
    searchFacts: searchFacts,
    saveNote: saveNote,
    getNotes: getNotes,
    deleteNote: deleteNote,
    getLLMKeys: getLLMKeys,
    saveLLMKeys: saveLLMKeys,
    getProvidersForConsole: getProvidersForConsole,
    testLLMKey: testLLMKey,
    providers: PROVIDERS,
    ttsSpeak: pwaTtsSpeak,
    sttListen: pwaSttListen,
    openDB: openDB,
    dbPut: dbPut,
    dbGet: dbGet,
    dbGetAll: dbGetAll,
  };
})();
