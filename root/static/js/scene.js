
function checkSweep() {
  const diff = norm(tAngle) - norm(angle);
  const hit  = diff > -0.08 && diff < 0.15;
  if (!hit) return;
  // guard: only count once per revolution (require ≥80% of 2π between counts)
  const canCount = lastCountedAngle === null ||
                   Math.abs(angle - lastCountedAngle) > Math.PI * 1.6;

  if (!tRevealed) {
    tRevealed = true;
    sweepPassCount = 1;
    lastCountedAngle = angle;
    stampBlip();
    radarTarget.style.display = 'flex';
    radarTarget.style.pointerEvents = 'none';
    // Show POKER on first scan — no supernova yet
    if (!btnShown) {
      btnShown = true;
      planetWrap.style.transition = 'opacity 1.4s ease';
      planetWrap.style.opacity = '1';
      radarTarget.style.pointerEvents = 'auto';
    }
  } else if (canCount) {
    sweepPassCount++;
    lastCountedAngle = angle;
    stampBlip();
    if (btnShown) {
      // flash planet and label
      const el = document.getElementById('enter-btn');
      const lbl = document.querySelector('.planet-label');
      el.style.transition = 'none';
      lbl.style.transition = 'none';
      el.style.filter = 'brightness(3) drop-shadow(0 0 20px rgba(210,150,255,1))';
      lbl.style.color = '#fff';
      lbl.style.textShadow = '0 0 20px rgba(220,180,255,1), 0 0 40px rgba(180,120,255,0.9)';
      lbl.style.letterSpacing = '5px';
      setTimeout(() => {
        el.style.transition = 'filter 0.6s ease-out';
        lbl.style.transition = 'all 0.6s ease-out';
        el.style.filter = 'brightness(1) drop-shadow(0 0 4px rgba(140,80,230,0.3))';
        lbl.style.color = 'rgba(255,255,255,0.9)';
        lbl.style.textShadow = '0 0 8px rgba(180,120,255,0.9)';
        lbl.style.letterSpacing = '3px';
      }, 60);

      // trigger supernova phase advance on every sweep after planet shown
      // (skip when FX is paused — don't advance phase while frozen)
      if (!SupernovaEngine.isPaused()) SupernovaEngine.onSweep(tX, tY);
    }
  }
}

function draw() {
  ctx.clearRect(0, 0, W, H);
  const maxR = W < 600
    ? Math.hypot(W, H) * 0.6
    : Math.hypot(cx, cy) * 0.9;

  // rings
  for (let i = 1; i <= 4; i++) {
    ctx.beginPath();
    ctx.arc(cx, cy, maxR / 4 * i, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(74,158,255,${0.04 + 0.01 * i})`;
    ctx.lineWidth = 1; ctx.stroke();
  }

  // crosshairs
  ctx.strokeStyle = 'rgba(74,158,255,0.06)'; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(cx, 0); ctx.lineTo(cx, H); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(0, cy); ctx.lineTo(W, cy); ctx.stroke();

  // afterglow blips first (below sweep line)
  drawBlips(maxR);

  // sweep wedge on top
  const isMob = W < 600;
  const sweepWidth = Math.PI * 0.18;
  const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, maxR);
  grad.addColorStop(0,   SWEEP + '0.0)');
  grad.addColorStop(0.4, SWEEP + (isMob ? '0.22)' : '0.13)'));
  grad.addColorStop(0.8, SWEEP + (isMob ? '0.10)' : '0.04)'));
  grad.addColorStop(1,   SWEEP + '0.0)');
  ctx.save();
  ctx.translate(cx, cy); ctx.rotate(angle);
  ctx.beginPath(); ctx.moveTo(0, 0);
  ctx.arc(0, 0, maxR, -sweepWidth, 0); ctx.closePath();
  ctx.fillStyle = grad; ctx.fill();
  ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(maxR, 0);
  ctx.strokeStyle = isMob ? SWEEP + '0.75)' : SWEEP + '0.55)';
  ctx.lineWidth = isMob ? 2 : 1.5; ctx.stroke();
  ctx.restore();

  // particles
  for (const p of particles) {
    const px = p.x - cx, py = p.y - cy;
    const pA = Math.atan2(py, px);
    const diff = (norm(pA) - norm(angle) + Math.PI * 2) % (Math.PI * 2);
    const lit = diff < 0.25;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r * (lit ? 2.2 : 1), 0, Math.PI * 2);
    ctx.fillStyle = lit
      ? `rgba(74,158,255,${Math.min(0.85, p.a * 3)})`
      : `rgba(255,255,255,${p.a * 0.35})`;
    ctx.fill();
    p.x += p.vx; p.y += p.vy;
    if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
    if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
  }

  checkSweep();
  angle += window.innerWidth < 600 ? 0.009 : 0.004;
  requestAnimationFrame(draw);
}

// coord readout
const coordEl = document.getElementById('coord');
function updateCoord() {
  const d = new Date();
  const lat = (d.getSeconds() * 0.0001 + 39.9938).toFixed(4);
  const lon = (d.getSeconds() * 0.0001 + 83.0089).toFixed(4);
  coordEl.textContent = `${lat} N  /  ${lon} W`;
}
setInterval(updateCoord, 1200);

// ── draw planet (shared core, used by drawPlanet and storm animator) ──
function drawPlanetOn(c, S) {
  c.clearRect(0, 0, S, S);

  c.save();
  c.beginPath(); c.arc(S/2, S/2, S/2, 0, Math.PI*2); c.clip();

  const base = c.createRadialGradient(S*0.38, S*0.32, 2, S/2, S/2, S/2);
  base.addColorStop(0,   '#2a1450');
  base.addColorStop(0.5, '#150830');
  base.addColorStop(1,   '#08030f');
  c.fillStyle = base; c.fillRect(0, 0, S, S);

  const clouds = [
    { x: 18, y: 20, rx: 16, ry: 10, a: 0.13, col: [140,60,220] },
    { x: 44, y: 14, rx: 14, ry: 8,  a: 0.09, col: [160,80,255] },
    { x: 10, y: 42, rx: 12, ry: 7,  a: 0.10, col: [100,40,180] },
    { x: 46, y: 40, rx: 13, ry: 8,  a: 0.08, col: [180,80,255] },
    { x: 26, y: 52, rx: 15, ry: 7,  a: 0.11, col: [120,50,200] },
  ];
  for (const cl of clouds) {
    const ng = c.createRadialGradient(cl.x, cl.y, 0, cl.x, cl.y, Math.max(cl.rx, cl.ry));
    ng.addColorStop(0,   `rgba(${cl.col},${cl.a})`);
    ng.addColorStop(1,   `rgba(${cl.col},0)`);
    c.save(); c.scale(1, cl.ry/cl.rx);
    c.beginPath(); c.arc(cl.x, cl.y * (cl.rx/cl.ry), cl.rx, 0, Math.PI*2);
    c.fillStyle = ng; c.fill(); c.restore();
  }

  const bands = [
    { y: 16, h: 5,  a: 0.09, col: [150,70,255] },
    { y: 30, h: 9,  a: 0.06, col: [120,50,200] },
    { y: 46, h: 7,  a: 0.07, col: [170,90,255] },
    { y: 60, h: 10, a: 0.05, col: [100,40,180] },
  ];
  for (const b of bands) {
    c.fillStyle = `rgba(${b.col},${b.a})`;
    c.fillRect(0, b.y, S, b.h);
  }

  const spec = c.createRadialGradient(S*0.3, S*0.26, 0, S*0.36, S*0.33, S*0.32);
  spec.addColorStop(0,   'rgba(230,200,255,0.22)');
  spec.addColorStop(0.5, 'rgba(200,160,255,0.06)');
  spec.addColorStop(1,   'rgba(200,160,255,0)');
  c.fillStyle = spec; c.fillRect(0, 0, S, S);

  const limb = c.createRadialGradient(S/2, S/2, S*0.3, S/2, S/2, S/2);
  limb.addColorStop(0,   'rgba(0,0,0,0)');
  limb.addColorStop(0.7, 'rgba(0,0,0,0.1)');
  limb.addColorStop(1,   'rgba(0,0,0,0.6)');
  c.fillStyle = limb; c.fillRect(0, 0, S, S);

  c.restore();

  const ring = c.createRadialGradient(S/2, S/2, S/2-1, S/2, S/2, S/2+8);
  ring.addColorStop(0,   'rgba(150,70,255,0.45)');
  ring.addColorStop(0.5, 'rgba(120,40,200,0.15)');
  ring.addColorStop(1,   'rgba(120,40,200,0)');
  c.beginPath(); c.arc(S/2, S/2, S/2+4, 0, Math.PI*2);
  c.fillStyle = ring; c.fill();
}

function drawPlanet() {
  const pc = document.getElementById('planet-canvas');
  pc.width = 68; pc.height = 68;
  drawPlanetOn(pc.getContext('2d'), 68);
}

drawPlanet();
resize(); resetScene(); initParticles(); draw();
window.addEventListener('resize', () => { resize(); resetScene(); initParticles(); SupernovaEngine.onResize(); });

// only reset on actual page load/reload, not tab switching
