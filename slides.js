"use strict";
(() => {
  const pages = [...document.querySelectorAll('.slide')];
  const prev = document.querySelector('#prev'), next = document.querySelector('#next');
  const progress = document.querySelector('#progress'), position = document.querySelector('#position');
  let index = 0;
  function fromHash() { const m = location.hash.match(/^#slide-(\d+)$/); return m ? Number(m[1]) - 1 : 0; }
  function go(n, updateHash = true) {
    index = Math.max(0, Math.min(pages.length - 1, Number.isFinite(n) ? n : 0));
    pages.forEach((p, i) => { p.hidden = i !== index; p.setAttribute('aria-hidden', String(i !== index)); });
    prev.disabled = index === 0; next.disabled = index === pages.length - 1;
    progress.style.width = `${(index + 1) / pages.length * 100}%`;
    progress.setAttribute('aria-valuenow', String(index + 1));
    position.textContent = `${index + 1} / ${pages.length}`;
    if (updateHash && location.hash !== `#slide-${index + 1}`) location.hash = `slide-${index + 1}`;
    window.scrollTo(0, 0);
  }
  prev.addEventListener('click', () => go(index - 1));
  next.addEventListener('click', () => go(index + 1));
  window.addEventListener('hashchange', () => go(fromHash(), false));
  document.addEventListener('keydown', e => {
    if (e.altKey || e.ctrlKey || e.metaKey || /INPUT|TEXTAREA|SELECT/.test(e.target.tagName) || e.target.isContentEditable) return;
    if (e.key === ' ' && /BUTTON|A/.test(e.target.tagName)) return;
    if (['ArrowRight', 'PageDown', ' '].includes(e.key)) { e.preventDefault(); go(index + 1); }
    if (['ArrowLeft', 'PageUp'].includes(e.key)) { e.preventDefault(); go(index - 1); }
    if (e.key === 'Home') { e.preventDefault(); go(0); }
    if (e.key === 'End') { e.preventDefault(); go(pages.length - 1); }
    if (e.key.toLowerCase() === 'f') document.querySelector('#fullscreen').click();
  });
  document.querySelector('#fullscreen').addEventListener('click', async () => {
    try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); }
    catch { position.textContent = `${index + 1} / ${pages.length}（全螢幕未啟用）`; }
  });
  go(fromHash());
})();
