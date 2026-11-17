'use strict';
// Somente arquivos estáticos podem funcionar via cache. Nunca armazenar dados de
// partida, saldos, chamadas administrativas, HTML dinâmico ou WebSockets.
const CACHE='blefe-color-static-2026-11-17';
const PRELOAD=['/static/icon.svg','/icons/icon-192.png','/icons/icon-512.png'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(PRELOAD)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(Promise.all([caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('blefe-color-')&&k!==CACHE).map(k=>caches.delete(k)))),self.clients.claim()])));
self.addEventListener('fetch',e=>{
  const r=e.request;if(r.method!=='GET')return;
  const u=new URL(r.url);if(u.origin!==self.location.origin||r.mode==='navigate')return;
  if(!(u.pathname.startsWith('/static/')||u.pathname.startsWith('/icons/')))return;
  e.respondWith(fetch(r).then(resp=>{if(resp.ok&&resp.type==='basic'){const clone=resp.clone();e.waitUntil(caches.open(CACHE).then(c=>c.put(r,clone)))}return resp}).catch(()=>caches.match(r).then(resp=>resp||Response.error())));
});
