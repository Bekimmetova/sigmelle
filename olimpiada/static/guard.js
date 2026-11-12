/* Halollik nazorati: boshqa tab/dasturga o'tish, to'liq ekrandan chiqish, nusxalash/joylash urinishlarini qayd etadi.
   Eslatma: brauzer ichidagi nazorat 100% kafolat bermaydi — u qoidabuzarlikni aniqlash va ogohlantirish uchun. */
(function () {
  const S = document.currentScript, SEC = S.dataset.section, FS = S.dataset.fullscreen === '1';
  const CSRF = document.querySelector('meta[name=csrf]').content;
  let last = 0, ignoreUntil = 0;
  window.__leaving = false;
  const leave = () => { window.__leaving = true; setTimeout(() => { window.__leaving = false; }, 4000); };
  addEventListener('beforeunload', () => { window.__leaving = true; });
  document.addEventListener('click', e => {
    const a = e.target.closest('a');
    if (a && a.getAttribute('href') && !a.getAttribute('href').startsWith('#') && !a.target) leave();
    if (e.target.matches && e.target.matches('input[type=file]')) ignoreUntil = Date.now() + 60000;
  }, true);
  document.addEventListener('submit', e => {
    leave();
    setTimeout(() => { if (e.defaultPrevented) window.__leaving = false; }, 0);
  }, true);

  const toastBox = document.createElement('div');
  toastBox.className = 'toast';
  document.body.appendChild(toastBox);
  function toast(msg, bad) {
    toastBox.textContent = msg; toastBox.className = 'toast show' + (bad ? ' bad' : '');
    clearTimeout(toastBox._t); toastBox._t = setTimeout(() => { toastBox.className = 'toast'; }, 6000);
  }

  async function report(kind) {
    if (window.__leaving || Date.now() < ignoreUntil) return;
    const now = Date.now();
    if (now - last < 1500) return;
    last = now;
    try {
      const r = await fetch('/api/event', {
        method: 'POST', keepalive: true,
        headers: { 'Content-Type': 'application/json', 'X-CSRF': CSRF },
        body: JSON.stringify({ section: SEC, kind })
      });
      const j = await r.json();
      if (j.finished) { toast('Qoidabuzarliklar chegarasi oshdi — bo\'lim yakunlandi.', true); window.__leaving = true; setTimeout(() => location.reload(), 2500); }
      else if (j.ok) toast('Diqqat! Qoidabuzarlik qayd etildi (' + j.count + (j.max > 0 ? ' / ' + j.max : '') + '). O\'qituvchi buni ko\'radi.', true);
    } catch (e) { /* tarmoq xatosi — e'tiborsiz */ }
  }

  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') report('tab_hidden'); });
  addEventListener('blur', () => { setTimeout(() => { if (!document.hasFocus()) report('blur'); }, 300); });

  // Nusxalash / joylash
  const blockAll = SEC === 'test';
  ['copy', 'cut'].forEach(ev => document.addEventListener(ev, e => {
    if (blockAll) { e.preventDefault(); report('copy'); }
  }));
  document.addEventListener('paste', e => {
    const t = e.target;
    if (blockAll || (t && t.dataset && t.dataset.nopaste === '1')) { e.preventDefault(); report('paste'); toast('Matn joylash taqiqlangan.', true); }
  });
  document.addEventListener('drop', e => {
    const t = e.target;
    if (t && t.dataset && t.dataset.nopaste === '1') { e.preventDefault(); report('paste'); }
  });

  // To'liq ekran (faqat test bo'limida)
  if (FS && document.fullscreenEnabled) {
    const ov = document.createElement('div');
    ov.className = 'fs-overlay';
    ov.innerHTML = '<div class="card center"><h2>To\'liq ekran rejimi</h2><p>Test faqat to\'liq ekran rejimida bajariladi. ' +
      'Undan chiqish, boshqa tab yoki dasturga o\'tish qoidabuzarlik sifatida qayd etiladi.</p>' +
      '<button class="btn">To\'liq ekranga o\'tish va davom etish</button></div>';
    document.body.appendChild(ov);
    const show = () => { ov.style.display = document.fullscreenElement ? 'none' : 'flex'; };
    ov.querySelector('button').addEventListener('click', () => {
      document.documentElement.requestFullscreen().catch(() => { ov.style.display = 'none'; });
    });
    document.addEventListener('fullscreenchange', () => {
      if (!document.fullscreenElement && !window.__leaving) report('fullscreen_exit');
      show();
    });
    show();
  }
})();
