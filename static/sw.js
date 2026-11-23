// SkillSum ResultSetu - Privacy-Preserving Service Worker
// CACHES ONLY STATIC APPLICATION SHELL. NEVER CACHES STUDENT DATA OR RESULT RESPONSES.

const CACHE_NAME = 'skillsum-resultsetu-shell-v2';
const STATIC_SHELL_ASSETS = [
  '/',
  '/static/css/style.css',
  '/static/js/app.js',
  '/static/js/translations.js',
  '/static/js/vendor/xlsx.full.min.js',
  '/static/manifest.json',
  '/static/icons/icon-192.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_SHELL_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // STRICT PRIVACY RULE: Never intercept or cache API requests, processing jobs, or file downloads
  if (url.pathname.startsWith('/api/') || request.method !== 'GET') {
    return; // Pass through to network directly without caching
  }

  // Network-first with cache fallback for static app shell
  event.respondWith(
    fetch(request)
      .then((networkResponse) => {
        // Cache valid static responses
        if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseToCache);
          });
        }
        return networkResponse;
      })
      .catch(() => {
        return caches.match(request);
      })
  );
});
