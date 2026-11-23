"use strict";
document.querySelector('#q').addEventListener('input', e => {
  const q = e.target.value.toLowerCase().trim();
  let visible = 0;
  document.querySelectorAll('.entry').forEach(card => { card.hidden = !card.dataset.key.includes(q); if (!card.hidden) visible++; });
  document.querySelector('#search-status').textContent = visible ? `顯示 ${visible} 個條目` : '沒有符合的條目，請試其他關鍵字。';
});
