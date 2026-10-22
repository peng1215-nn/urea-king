const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
let W, H, cx, cy, particles;

function resize() {
  W = canvas.width  = window.innerWidth;
  H = canvas.height = window.innerHeight;
  cx = W / 2; cy = H / 2;
}

function initParticles() {
  particles = Array.from({ length: 55 }, () => ({
    x: Math.random() * W, y: Math.random() * H,
    r: Math.random() * 1.2 + 0.3,
    vx: (Math.random() - 0.5) * 0.18,
    vy: (Math.random() - 0.5) * 0.18,
    a: Math.random() * 0.5 + 0.1,
  }));
}

let angle = 0;
const SWEEP = 'rgba(74,158,255,';

// ── radar target state ──
const radarTarget = document.getElementById('radar-target');
let tAngle, tDist, tX, tY, tRevealed = false;

// safe zone: avoid center content block (ellipse) and screen edges
function placeTarget() {
  let tx, ty, attempts = 0;
  const isMobile = W < 600;
  const edgeMargin = Math.min(80, W * 0.12);
  const exW = Math.min(210, W * 0.32);
  const exH = Math.min(160, H * 0.22);
  const planetR = 40;
  do {
    if (isMobile) {
      // mobile: place in lower 55% of screen
      tx = edgeMargin + planetR + Math.random() * (W - 2 * (edgeMargin + planetR));
      ty = H * 0.45 + Math.random() * (H * 0.45);
      tAngle = Math.atan2(ty - cy, tx - cx);
      tDist  = Math.hypot(tx - cx, ty - cy);
    } else {
      tAngle = Math.random() * Math.PI * 2;
      tDist  = (0.30 + Math.random() * 0.52) * Math.min(W, H) * 0.44;
      tx = cx + Math.cos(tAngle) * tDist;
      ty = cy + Math.sin(tAngle) * tDist;
    }
    attempts++;
    const ddx = (tx - cx) / exW, ddy = (ty - cy) / exH;
    var inCenter = ddx*ddx + ddy*ddy < 1;
    var nearEdge = tx < edgeMargin + planetR || tx > W - edgeMargin - planetR ||
                   ty < edgeMargin + planetR || ty > H - edgeMargin - planetR;
  } while (attempts < 60 && (inCenter || nearEdge));
  tX = tx; tY = ty;
  radarTarget.style.left = tX + 'px';
  radarTarget.style.top  = tY + 'px';
}

function resetScene() {
  tRevealed = false;
  btnShown  = false;
  sweepPassCount = 0;
  lastCountedAngle = null;
  if (typeof tX !== 'undefined') SupernovaEngine.resetPlanet(tX, tY);
  blips.length = 0;
  radarTarget.style.display = 'none';
  radarTarget.style.pointerEvents = 'none';
  planetWrap.style.transition = 'none';
  planetWrap.style.opacity    = '0';
  radarTarget.classList.remove('lit');
  placeTarget();
}

function norm(a) { return ((a % (Math.PI*2)) + Math.PI*2) % (Math.PI*2); }

const planetWrap = document.getElementById('planet-wrap');
let btnShown = false;

// ── blip afterglow: array of { x, y, alpha } ──
// each time sweep hits target a blip is stamped; alpha decays each frame
const blips = [];
const BLIP_DECAY = 0.97; // exponential decay multiplier per frame (phosphor afterglow curve)

function stampBlip() {
  // replace any existing blip at same position (keep max 1 per target)
  const existing = blips.findIndex(b => b.x === tX && b.y === tY);
  if (existing >= 0) blips[existing].alpha = 1.0;
  else blips.push({ x: tX, y: tY, alpha: 1.0 });
}

function drawBlips(maxR) {
  for (const b of blips) {
    if (b.alpha <= 0) continue;

    // outer soft glow (purple)
    const g = ctx.createRadialGradient(b.x, b.y, 0, b.x, b.y, 20);
    g.addColorStop(0,   `rgba(160,80,255,${b.alpha * 0.75})`);
    g.addColorStop(0.4, `rgba(130,50,220,${b.alpha * 0.35})`);
    g.addColorStop(1,   `rgba(100,20,180,0)`);
    ctx.beginPath(); ctx.arc(b.x, b.y, 20, 0, Math.PI*2);
    ctx.fillStyle = g; ctx.fill();

    // bright core dot (white-violet)
    ctx.beginPath(); ctx.arc(b.x, b.y, 3, 0, Math.PI*2);
    ctx.fillStyle = `rgba(230,200,255,${b.alpha})`;
    ctx.fill();

    b.alpha = b.alpha * BLIP_DECAY;  // exponential: fast initial fade, long phosphor tail
  }
}

let sweepPassCount = 0;
let lastCountedAngle = null; // guard: only count once per revolution

