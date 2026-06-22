const CACHE_NAME = 'prontuario-clinica-v1';
const ASSETS_TO_CACHE = [
  '/static/style.css',
  '/static/logo.png',
  '/static/icon-192.png',
  '/static/icon-512.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((nomes) =>
      Promise.all(nomes.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n)))
    )
  );
});

// Só intercepta arquivos estáticos (CSS, ícones). Páginas HTML nunca passam por
// aqui — têm dados de paciente/sessão por tenant e não podem ser cacheadas
// genericamente, sob risco de um usuário ver tela cacheada de outra conta.
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || !url.pathname.startsWith('/static/')) {
    return;
  }
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});
