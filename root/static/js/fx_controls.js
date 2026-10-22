
// ── Pause button wiring ──
(function() {
  const btn = document.getElementById('pause-btn');
  let globalPaused = false;

  function applyPause(paused) {
    if (paused) {
      // Try to pause all engines; any might reject (e.g. during whiteout)
      const accepted = FXRegistry.every(fx => fx.pause() !== false);
      if (!accepted) return; // at least one engine refused (whiteout lockout)
    } else {
      FXRegistry.forEach(fx => fx.resume());
    }
    globalPaused = paused;
    btn.classList.toggle('paused', globalPaused);
    try { localStorage.setItem('fx-paused', globalPaused ? '1' : '0'); } catch(e) {}
  }

  btn.addEventListener('click', () => applyPause(!globalPaused));

  // Restore from localStorage
  try {
    if (localStorage.getItem('fx-paused') === '1') applyPause(true);
  } catch(e) {}
})();
