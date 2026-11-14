// TejiMusic Service Worker with Full Audio Pre-Buffering & Offline Playback Support
const CACHE_NAME = 'tejimusic-cache-v3';
const AUDIO_CACHE_NAME = 'tejimusic-audio-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE).catch(() => {});
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME && key !== AUDIO_CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  const url = req.url;

  // 1. Audio Stream Request Interception (Saavncdn CDN, mp4/m4a/mp3, audio destination)
  const isAudioReq = req.destination === 'audio' ||
    url.includes('saavncdn') ||
    url.includes('.mp4') ||
    url.includes('.m4a') ||
    url.includes('.mp3') ||
    url.includes('stream');

  if (isAudioReq) {
    event.respondWith(
      (async () => {
        const audioCache = await caches.open(AUDIO_CACHE_NAME);
        const cachedResponse = await audioCache.match(req, { ignoreSearch: true });

        // If cached, serve with HTTP 206 Range slicing support for seamless media playback
        if (cachedResponse) {
          const rangeHeader = req.headers.get('Range');
          if (rangeHeader) {
            try {
              const arrayBuffer = await cachedResponse.arrayBuffer();
              const bytes = rangeHeader.replace(/bytes=/, '').split('-');
              const total = arrayBuffer.byteLength;
              const start = parseInt(bytes[0], 10) || 0;
              const end = bytes[1] ? parseInt(bytes[1], 10) : total - 1;
              const sliced = arrayBuffer.slice(start, end + 1);

              return new Response(sliced, {
                status: 206,
                statusText: 'Partial Content',
                headers: {
                  'Content-Type': cachedResponse.headers.get('Content-Type') || 'audio/mp4',
                  'Content-Range': `bytes ${start}-${end}/${total}`,
                  'Content-Length': String(sliced.byteLength),
                  'Accept-Ranges': 'bytes',
                  'Cache-Control': 'public, max-age=31536000'
                }
              });
            } catch (sliceErr) {
              return cachedResponse;
            }
          }
          return cachedResponse;
        }

        // Not in audio cache: Fetch from network and pre-buffer into cache in background
        try {
          const networkResponse = await fetch(req);
          if (networkResponse && (networkResponse.status === 200 || networkResponse.status === 206)) {
            // Clone into audio cache if complete response
            if (networkResponse.status === 200) {
              audioCache.put(req, networkResponse.clone()).catch(() => {});
            }
          }
          return networkResponse;
        } catch (networkErr) {
          // Offline fallback
          if (cachedResponse) return cachedResponse;
          return new Response('Audio not available offline yet', { status: 503, statusText: 'Offline' });
        }
      })()
    );
    return;
  }

  // 2. Bypass live search backend dynamic APIs
  if (url.includes('/api/search') || url.includes('/api/album-details')) {
    return;
  }

  // 3. App Shell: Network first, fallback to cached assets
  event.respondWith(
    fetch(req).catch(async () => {
      const match = await caches.match(req);
      if (match) return match;
      if (req.mode === 'navigate') {
        return caches.match('/index.html');
      }
      return new Response('Offline', { status: 503 });
    })
  );
});
