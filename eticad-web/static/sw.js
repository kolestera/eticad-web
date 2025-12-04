const CACHE_NAME = "eticad-cache-v1";
const URLS_TO_CACHE = [
  "/",
  "/download",
  "/static/LOGO.gif",
  "/static/1.png",
  "/static/2.png",
  "/static/3.png",
  "/static/icons/eticad-32.png",
  "/static/icons/eticad-192.png",
  "/static/icons/eticad-512.png"
];

// İlk kurulumda temel dosyaları cache'e al
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(URLS_TO_CACHE);
    })
  );
});

// Eski cache'leri temizle
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      )
    )
  );
});

// Ağ isteği: önce ağ, hata olursa cache'e düş
self.addEventListener("fetch", (event) => {
  const request = event.request;

  // Sadece GET istekleri için
  if (request.method !== "GET") return;

  event.respondWith(
    fetch(request)
      .then((response) => {
        // Başarılıysa cache'i güncelle
        const respClone = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(request, respClone);
        });
        return response;
      })
      .catch(() =>
        caches.match(request).then((cached) => {
          if (cached) return cached;
          // Son çare: ana sayfayı dönebiliriz
          return caches.match("/");
        })
      )
  );
});
