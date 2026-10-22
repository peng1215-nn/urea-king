
// ── Card Deal Engine ──
const CardDealEngine = (function() {
  const SUITS = ['♠','♥','♦','♣'];
  const RANKS = ['A','2','3','4','5','6','7','8','9','10','J','Q','K'];
  const RED   = new Set(['♥','♦']);

  function cryptoRandInt(n) {
    const buf = new Uint32Array(1);
    window.crypto.getRandomValues(buf);
    return buf[0] % n;
  }

  function randTwo() {
    const deck = [];
    for (const s of SUITS) for (const r of RANKS) deck.push({s, r});
    const i = cryptoRandInt(52);
    let j; do { j = cryptoRandInt(52); } while (j === i);
    return [deck[i], deck[j]];
  }

  // Build the overlay once
  let overlay = null;
  function ensureDOM() {
    if (overlay) return;
    overlay = document.createElement('div');
    Object.assign(overlay.style, {
      position: 'fixed', inset: '0', zIndex: '600',
      display: 'none', alignItems: 'center', justifyContent: 'center',
      gap: 'clamp(16px, 5vw, 40px)',
      background: 'rgba(0,0,0,0.92)',
      backdropFilter: 'blur(4px)',
    });
    document.body.appendChild(overlay);
  }

  function makeCardEl(card) {
    const el = document.createElement('div');
    const isRed = RED.has(card.s);
    // Responsive sizing: card width = 22vw, clamped between 90px and 150px
    // Height = width * 1.5 (standard card ratio)
    Object.assign(el.style, {
      width: 'clamp(90px, 22vw, 150px)',
      height: 'clamp(135px, 33vw, 225px)',
      borderRadius: 'clamp(8px, 1.5vw, 14px)',
      background: '#fff',
      boxShadow: '0 8px 40px rgba(0,0,0,0.7), 0 2px 8px rgba(0,0,0,0.5)',
      display: 'flex', flexDirection: 'column',
      padding: 'clamp(6px, 1.2vw, 12px)',
      color: isRed ? '#d32f2f' : '#111',
      fontFamily: 'Georgia, serif',
      position: 'relative',
      opacity: '0',
      transform: 'translateX(140vw) rotate(25deg) scale(0.9)',
      transition: 'opacity 0.35s ease, transform 0.45s cubic-bezier(0.22,1,0.36,1)',
    });

    // top-left corner
    const tl = document.createElement('div');
    Object.assign(tl.style, {
      lineHeight: '1.1',
      fontSize: 'clamp(14px, 3.5vw, 22px)',
      fontWeight: 'bold',
    });
    tl.innerHTML = `<div>${card.r}</div><div style="font-size:0.8em">${card.s}</div>`;

    // center suit large
    const ctr = document.createElement('div');
    Object.assign(ctr.style, {
      flex: '1', display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: 'clamp(36px, 10vw, 72px)', lineHeight: '1',
    });
    ctr.textContent = card.s;

    // bottom-right (rotated)
    const br = document.createElement('div');
    Object.assign(br.style, {
      lineHeight: '1.1',
      fontSize: 'clamp(14px, 3.5vw, 22px)',
      fontWeight: 'bold',
      transform: 'rotate(180deg)', alignSelf: 'flex-end',
    });
    br.innerHTML = `<div>${card.r}</div><div style="font-size:0.8em">${card.s}</div>`;

    el.append(tl, ctr, br);
    return el;
  }

  let busy = false;
  let preloadIframe = null;

  function preload(dest) {
    if (preloadIframe) return;
    preloadIframe = document.createElement('iframe');
    Object.assign(preloadIframe.style, {
      position: 'fixed', inset: '0', width: '100%', height: '100%',
      border: 'none', zIndex: '599',   // just below card overlay (600)
      opacity: '0', pointerEvents: 'none',
    });
    preloadIframe.src = dest;
    document.body.appendChild(preloadIframe);
  }

  function revealIframe() {
    if (!preloadIframe) return;
    // Slide card overlay away, reveal iframe underneath
    overlay.style.transition = 'opacity 0.35s ease';
    overlay.style.opacity = '0';
    preloadIframe.style.transition = 'opacity 0.35s ease';
    preloadIframe.style.opacity = '1';
    preloadIframe.style.pointerEvents = 'auto';
    // After transition, do a real navigation so URL bar updates
    setTimeout(() => {
      window.location.href = preloadIframe.src;
    }, 360);
  }

  function deal(dest) {
    if (busy) return;
    busy = true;
    ensureDOM();

    // Start preloading the destination immediately
    preload(dest);

    const [c1, c2] = randTwo();
    overlay.innerHTML = '';
    overlay.style.display = 'flex';
    overlay.style.opacity = '1';

    const el1 = makeCardEl(c1);
    const el2 = makeCardEl(c2);
    overlay.append(el1, el2);

    // Cards fly in from the right with stagger
    const dealIn = (el, delay) => {
      setTimeout(() => {
        el.style.opacity = '1';
        el.style.transform = 'translateY(0) rotate(0deg) scale(1)';
      }, delay);
    };
    dealIn(el1, 80);
    dealIn(el2, 320);

    // After 2.4s, crossfade to the preloaded page
    setTimeout(revealIframe, 2400);
  }

  return { deal };
})();

// ── Enter button: deal cards then navigate ──
(function() {
  const btn = document.getElementById('enter-btn');
  if (!btn) return;
  btn.addEventListener('click', function(e) {
    if (SupernovaEngine.isPaused()) return; // FX off → navigate directly
    e.preventDefault();
    CardDealEngine.deal(btn.getAttribute('href'));
  });
})();
