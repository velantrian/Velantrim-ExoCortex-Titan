const CACHE = "velantrim-pwa-v2";
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icon.svg",
  "./console/index.html",
  "./console/pwa-core.js",
  "./console/pwa-mode.js",
  "./console/research-app.html",
  "./console/research-app.js",
  "./console/research-roadmap.html",
  "./console/research.html",
  "./console/research-mode.html",
  "./console/roadmap.html",
  "./console/i18n-snippet.js",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => {
      return Promise.allSettled(
        ASSETS.map((url) =>
          cache.add(url).catch((err) => console.warn("SW: cache miss", url, err.message))
        )
      );
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;

  // Для API-запросов (LLM) — не кэшируем, пропускаем напрямую
  const url = event.request.url;
  if (
    url.includes("api.deepseek.com") ||
    url.includes("api.openai.com") ||
    url.includes("generativelanguage.googleapis.com") ||
    url.includes("/chat/stream") ||
    url.includes("/query")
  ) {
    return; // network-only
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      // Возвращаем из кэша; одновременно обновляем кэш из сети
      const fetchPromise = fetch(event.request)
        .then((response) => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE).then((cache) => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => null);

      return cached || fetchPromise;
    })
  );
});
