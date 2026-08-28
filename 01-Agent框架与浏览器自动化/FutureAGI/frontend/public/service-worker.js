// @ts-nocheck
/* eslint-disable no-restricted-globals */
/* eslint-env serviceworker */
/* eslint-disable no-undef */

// Service Worker for Future AGI
//
// Strategy:
//   HTML        → network-first (always get latest index.html after deploys)
//   JS/CSS/etc  → network-first with cache fallback (prevents stale chunk errors)
//   Fonts/imgs  → cache-first (immutable, never change)
//
// Why NOT cache-first for JS:
//   After a deploy, chunk filenames change (e.g. TraceGrid-abc123.js → TraceGrid-def456.js).
//   If the SW serves a cached old index.html that references old chunks, or the browser
//   has a stale index.html, it requests old chunk URLs that no longer exist on the server.
//   Network-first ensures we always try the server first, falling back to cache only offline.

const CACHE_NAME = "futureagi-v2";

// Install — skip waiting to activate immediately
self.addEventListener("install", (event) => {
  self.skipWaiting();
});

// Activate — claim clients and clean old caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((names) =>
        Promise.all(
          names
            .filter((name) => name !== CACHE_NAME)
            .map((name) => caches.delete(name)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

// Fetch
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle GET requests from our origin
  if (request.method !== "GET") return;
  if (url.origin !== self.location.origin) return;

  // Skip chrome extensions, hot module replacement, API calls
  if (url.protocol === "chrome-extension:") return;
  if (url.pathname.startsWith("/api/")) return;
  if (url.pathname.includes("__vite")) return;

  event.respondWith(handleFetch(request, url));
});

async function handleFetch(request, url) {
  // Immutable assets (fonts, images) — cache-first
  if (url.pathname.match(/\.(woff2?|ttf|eot|png|jpg|jpeg|gif|svg|ico)$/)) {
    return cacheFirst(request);
  }

  // Everything else (HTML, JS, CSS) — network-first
  // This prevents stale chunk errors after deploys
  return networkFirst(request);
}

async function networkFirst(request) {
  try {
    const response = await fetch(request);
    // Cache successful responses for offline fallback
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    // Network failed — try cache (offline support)
    const cached = await caches.match(request);
    return cached || new Response("Offline", { status: 503 });
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response("Offline", { status: 503 });
  }
}
