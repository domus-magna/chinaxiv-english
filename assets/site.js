(() => {
  const input = document.getElementById('search-input');
  const results = document.getElementById('search-results');
  if (!input || !results) return;
  let index = [];
  fetch('search-index.json').then(r => r.json()).then(data => index = data).catch(() => {});
  let timer = null;
  input.addEventListener('input', () => {
    clearTimeout(timer);
    const q = input.value.trim().toLowerCase();
    if (!q) { results.innerHTML = ''; return; }
    timer = setTimeout(() => {
      const out = [];
      for (const it of index) {
        const hay = [it.title, it.authors, it.abstract, it.subjects].join(' ').toLowerCase();
        if (hay.includes(q)) out.push(it);
        if (out.length >= 50) break;
      }
      results.innerHTML = out.map(it => `
        <div class="res">
          <div><a href="/items/${it.id}/"><strong>${escapeHtml(it.title || '')}</strong></a></div>
          <div class="meta">${it.date || ''} — ${escapeHtml(it.authors || '')}</div>
          <div>${escapeHtml((it.abstract || '').slice(0, 280))}…</div>
        </div>
      `).join('');
    }, 120);
  });

  function escapeHtml(s) {
    return (s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
  }
})();
