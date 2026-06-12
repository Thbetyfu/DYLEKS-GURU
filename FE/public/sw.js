/**
 * DyLeks Custom Service Worker
 * 
 * Alasan ('Why') Strategi Cache:
 *   Di sekolah 3T, internet = 0. Kita tidak bisa mengandalkan network sama sekali.
 *   Service Worker ini mengimplementasikan 3 strategi cache berbeda sesuai
 *   karakteristik aset:
 *
 *   1. CACHE_FIRST (Audio MP3, Font, SVG, Ikon)
 *      Aset yang tidak pernah berubah saat runtime. Selalu ambil dari cache,
 *      network hanya sebagai fallback jika belum pernah di-cache.
 *      Ini KRITIS untuk audio Listen Card — tanpa ini, audio tidak akan berbunyi
 *      saat offline.
 *
 *   2. NETWORK_FIRST with Cache Fallback (Halaman Next.js, API calls)
 *      Coba network dulu (agar data segar), jika gagal, gunakan cache.
 *      Ini membuat transisi online-to-offline lebih mulus.
 *
 *   3. STALE_WHILE_REVALIDATE (Chunk JS/CSS Next.js)
 *      Sajikan dari cache SEGERA (cepat), sambil fetch ulang di background.
 *      Optimal untuk file static Next.js yang sering berubah antar build.
 */

const CACHE_VERSION = 'v1.2';
const CACHE_NAMES = {
  static: `dyleks-static-${CACHE_VERSION}`,
  audio: `dyleks-audio-${CACHE_VERSION}`,
  pages: `dyleks-pages-${CACHE_VERSION}`,
  api: `dyleks-api-${CACHE_VERSION}`,
};

// Aset yang WAJIB di-cache saat SW pertama kali diinstall (Pre-cache)
const PRECACHE_ASSETS = [
  '/',
  '/screening',
  '/latihan',
  '/game',
  '/result',
  '/summary',
  '/copilot',
  '/manifest.json',
  // Audio instruksi: ini adalah aset paling kritis untuk offline
  '/assets/audio/instruksi_a.mp3',
  '/assets/audio/instruksi_ba.mp3',
  '/assets/audio/instruksi_ban.mp3',
  '/assets/audio/instruksi_nyala.mp3',
  '/assets/audio/instruksi_menemani.mp3',
  // Aset visual
  '/assets/duck.svg',
  '/assets/ear.svg',
  '/assets/glowing-star.svg',
];

// ============================================================
// INSTALL: Pre-cache semua aset kritikal
// ============================================================
self.addEventListener('install', (event) => {
  console.log('[SW DyLeks] Instalasi Service Worker v' + CACHE_VERSION);
  event.waitUntil(
    (async () => {
      // Cache static assets & pages
      const staticCache = await caches.open(CACHE_NAMES.static);
      await staticCache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('[SW DyLeks] Gagal pre-cache beberapa aset:', err);
      });

      // Cache audio secara terpisah dengan error handling per file
      // (agar jika satu file gagal, file lain tetap ter-cache)
      const audioCache = await caches.open(CACHE_NAMES.audio);
      const audioFiles = PRECACHE_ASSETS.filter(url => url.endsWith('.mp3'));
      for (const audioUrl of audioFiles) {
        try {
          await audioCache.add(audioUrl);
          console.log('[SW DyLeks] Audio cached:', audioUrl);
        } catch (err) {
          console.warn('[SW DyLeks] Gagal cache audio:', audioUrl, err);
        }
      }

      // Aktifkan SW baru SEGERA tanpa menunggu tab lama ditutup
      await self.skipWaiting();
    })()
  );
});

// ============================================================
// ACTIVATE: Bersihkan cache lama dari versi sebelumnya
// ============================================================
self.addEventListener('activate', (event) => {
  console.log('[SW DyLeks] Aktivasi Service Worker v' + CACHE_VERSION);
  event.waitUntil(
    (async () => {
      const currentCacheNames = Object.values(CACHE_NAMES);
      const allCacheKeys = await caches.keys();

      await Promise.all(
        allCacheKeys
          .filter((key) => !currentCacheNames.includes(key))
          .map((key) => {
            console.log('[SW DyLeks] Menghapus cache lama:', key);
            return caches.delete(key);
          })
      );

      // Ambil alih kontrol semua tab yang sedang buka tanpa perlu refresh
      await self.clients.claim();
    })()
  );
});

// ============================================================
// FETCH: Intercept semua request dan terapkan strategi cache
// ============================================================
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Jangan intercept request ke backend API lokal (port 3004)
  // Biarkan network handle dan gagal secara natural jika offline
  if (url.port === '3004' || url.pathname.startsWith('/api/v1/')) {
    return;
  }

  // Jangan intercept non-GET requests (POST, PUT, DELETE)
  if (request.method !== 'GET') {
    return;
  }

  // Strategi 1: CACHE_FIRST untuk audio MP3
  if (url.pathname.startsWith('/assets/audio/') && url.pathname.endsWith('.mp3')) {
    event.respondWith(cacheFirst(request, CACHE_NAMES.audio));
    return;
  }

  // Strategi 2: CACHE_FIRST untuk aset statis (SVG, font, ikon)
  if (
    url.pathname.startsWith('/assets/') ||
    url.pathname.startsWith('/_next/static/') ||
    url.pathname.endsWith('.svg') ||
    url.pathname.endsWith('.png') ||
    url.pathname.endsWith('.ico') ||
    url.pathname === '/manifest.json'
  ) {
    event.respondWith(cacheFirst(request, CACHE_NAMES.static));
    return;
  }

  // Strategi 3: STALE_WHILE_REVALIDATE untuk chunk JS/CSS Next.js
  if (url.pathname.startsWith('/_next/')) {
    event.respondWith(staleWhileRevalidate(request, CACHE_NAMES.static));
    return;
  }

  // Strategi 4: NETWORK_FIRST with Fallback untuk halaman HTML
  if (request.mode === 'navigate') {
    event.respondWith(networkFirstWithFallback(request, CACHE_NAMES.pages));
    return;
  }
});

// ============================================================
// HELPER FUNCTIONS: Implementasi Strategi Cache
// ============================================================

/**
 * Cache First: Ambil dari cache, network hanya jika cache miss.
 * Ideal untuk aset yang jarang berubah (audio, font, ikon).
 */
async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      await cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (err) {
    console.warn('[SW DyLeks] Cache miss + network fail:', request.url);
    return new Response('Aset tidak tersedia secara offline.', {
      status: 503,
      statusText: 'Service Unavailable',
    });
  }
}

/**
 * Stale While Revalidate: Sajikan dari cache segera, update cache di background.
 * Ideal untuk chunk JS/CSS yang berubah antar build tapi harus cepat dimuat.
 */
async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);

  // Fetch di background (tidak di-await) untuk update cache
  const networkFetchPromise = fetch(request).then((networkResponse) => {
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  }).catch(() => null);

  return cachedResponse || (await networkFetchPromise) || offlineFallback();
}

/**
 * Network First with Fallback: Coba network, fallback ke cache jika gagal.
 * Ideal untuk halaman HTML yang ingin selalu segar jika online.
 */
async function networkFirstWithFallback(request, cacheName) {
  const cache = await caches.open(cacheName);

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      await cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (err) {
    // Network gagal: coba cache
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      console.log('[SW DyLeks] Offline fallback dari cache:', request.url);
      return cachedResponse;
    }

    // Cache juga miss: tampilkan halaman offline custom
    return offlineFallback();
  }
}

/**
 * Halaman offline fallback jika tidak ada cache sama sekali.
 * Menampilkan pesan ramah daripada browser error "No Internet".
 */
function offlineFallback() {
  return new Response(
    `<!DOCTYPE html>
    <html lang="id">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>DyLeks - Mode Offline</title>
      <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
          font-family: 'Poppins', system-ui, sans-serif;
          background: #0f0f1a;
          color: #e2e8f0;
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 24px;
          text-align: center;
        }
        .card {
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(124,58,237,0.3);
          border-radius: 24px;
          padding: 40px 32px;
          max-width: 380px;
          width: 100%;
          backdrop-filter: blur(12px);
        }
        .icon { font-size: 64px; margin-bottom: 20px; }
        h1 { font-size: 22px; font-weight: 700; color: #a78bfa; margin-bottom: 12px; }
        p { font-size: 14px; line-height: 1.6; color: #94a3b8; margin-bottom: 24px; }
        .tip {
          background: rgba(124,58,237,0.15);
          border-radius: 12px;
          padding: 16px;
          font-size: 13px;
          color: #c4b5fd;
          text-align: left;
          line-height: 1.5;
        }
        .tip strong { display: block; margin-bottom: 6px; color: #a78bfa; }
        button {
          margin-top: 24px;
          background: #7c3aed;
          color: white;
          border: none;
          border-radius: 12px;
          padding: 14px 28px;
          font-size: 15px;
          font-weight: 600;
          cursor: pointer;
          width: 100%;
        }
      </style>
    </head>
    <body>
      <div class="card">
        <div class="icon">📡</div>
        <h1>Halaman Belum Tersedia Offline</h1>
        <p>Halaman ini belum tersimpan di cache perangkat. Hubungkan ke Wi-Fi server laptop guru terlebih dahulu.</p>
        <div class="tip">
          <strong>Cara terhubung:</strong>
          Pastikan HP kamu terhubung ke Wi-Fi hotspot laptop guru,
          lalu buka DyLeks sekali saat online agar halaman tersimpan otomatis.
        </div>
        <button onclick="window.location.href='/'">Kembali ke Beranda</button>
      </div>
    </body>
    </html>`,
    {
      status: 200,
      headers: { 'Content-Type': 'text/html; charset=utf-8' },
    }
  );
}

// ============================================================
// BACKGROUND SYNC: Antrian submit foto saat koneksi terputus
// ============================================================
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-pending-submissions') {
    event.waitUntil(syncPendingSubmissions());
  }
});

async function syncPendingSubmissions() {
  /**
   * Ketika anak submit foto tulisan tangan saat koneksi ke laptop server
   * terputus sementara (misal: HP terlalu jauh dari hotspot), request
   * akan masuk ke antrian IndexedDB. Saat koneksi kembali, SW akan
   * otomatis mencoba kirim ulang tanpa anak perlu refresh halaman.
   */
  try {
    // Buka IndexedDB dan ambil antrian yang pending
    const db = await openOfflineDB();
    const pendingItems = await getAllPending(db);

    for (const item of pendingItems) {
      try {
        const response = await fetch('/api/v1/screening/upload', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(item.payload),
        });

        if (response.ok) {
          await deleteFromDB(db, item.id);
          console.log('[SW DyLeks] Sync berhasil untuk item:', item.id);
        }
      } catch (err) {
        console.warn('[SW DyLeks] Sync gagal, akan dicoba lagi:', err);
      }
    }
  } catch (err) {
    console.error('[SW DyLeks] Background sync error:', err);
  }
}

// ============================================================
// INDEXEDDB HELPERS untuk Offline Queue
// ============================================================
function openOfflineDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('dyleks-offline-queue', 1);
    request.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains('pending')) {
        db.createObjectStore('pending', { keyPath: 'id', autoIncrement: true });
      }
    };
    request.onsuccess = (e) => resolve(e.target.result);
    request.onerror = (e) => reject(e.target.error);
  });
}

function getAllPending(db) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction('pending', 'readonly');
    const store = tx.objectStore('pending');
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function deleteFromDB(db, id) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction('pending', 'readwrite');
    const store = tx.objectStore('pending');
    const req = store.delete(id);
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
  });
}
