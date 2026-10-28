// ── SupernovaEngine: WebGL-based 5-phase supernova + 3D starfield ──
const SupernovaEngine = (() => {
  let renderer, scene, camera;
  let novaCanvas, W2, H2;
  let THREE_loaded = false;

  // ── 3D Starfield state ──
  let starPoints, starGeo, starPositions, starCount;
  let starOrigPositions;   // rest positions for push-back
  let starVelocities;      // for shockwave displacement
  let cameraTarget = new THREE.Vector3(0, 0, 0); // smooth parallax target
  let mouseNorm   = { x: 0, y: 0 };              // -1..1

  // Per-planet state
  const planets = new Map(); // key: "x,y" → { phase, animT, animating, mesh refs... }

  // ── Starfield: build 3000 stars in a 3D sphere shell ──
  function initStarfield() {
    starCount = 3000;
    starPositions    = new Float32Array(starCount * 3);
    starOrigPositions = new Float32Array(starCount * 3);
    starVelocities   = new Float32Array(starCount * 3);
    const sizes      = new Float32Array(starCount);
    const alphas     = new Float32Array(starCount);

    for (let i = 0; i < starCount; i++) {
      // Distribute evenly on a sphere shell, varying depth in Z
      const theta = Math.random() * Math.PI * 2;
      const phi   = Math.acos(2 * Math.random() - 1);
      const r     = 800 + Math.random() * 1200; // 800–2000 units deep
      const x = r * Math.sin(phi) * Math.cos(theta);
      const y = r * Math.sin(phi) * Math.sin(theta);
      const z = -r * 0.45 + Math.random() * r * 0.25 - 600; // keep behind camera

      starPositions[i*3]    = x;
      starPositions[i*3+1]  = y;
      starPositions[i*3+2]  = z;
      starOrigPositions[i*3]   = x;
      starOrigPositions[i*3+1] = y;
      starOrigPositions[i*3+2] = z;
      starVelocities[i*3] = starVelocities[i*3+1] = starVelocities[i*3+2] = 0;

      // Bigger/brighter for closer stars
      const depthFactor = 1 - Math.abs(z) / 2600;
      sizes[i]  = 1.0 + depthFactor * 3.5 + Math.random() * 1.5;
      alphas[i] = 0.25 + depthFactor * 0.65 + Math.random() * 0.1;
    }

    starGeo = new THREE.BufferGeometry();
    starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
    starGeo.setAttribute('size',     new THREE.BufferAttribute(sizes, 1));
    starGeo.setAttribute('alpha',    new THREE.BufferAttribute(alphas, 1));

    // Custom shader: per-star size + alpha, soft round disc
    const starMat = new THREE.ShaderMaterial({
      uniforms: { globalAlpha: { value: 1.0 } },
      vertexShader: `
        attribute float size;
        attribute float alpha;
        varying float vAlpha;
        void main() {
          vAlpha = alpha;
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = size * (900.0 / -mvPosition.z);
          gl_Position  = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        uniform float globalAlpha;
        varying float vAlpha;
        void main() {
          float d = length(gl_PointCoord - vec2(0.5));
          if (d > 0.5) discard;
          float soft = 1.0 - smoothstep(0.2, 0.5, d);
          gl_FragColor = vec4(1.0, 1.0, 1.0, soft * vAlpha * globalAlpha);
        }
      `,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });

    starPoints = new THREE.Points(starGeo, starMat);
    scene.add(starPoints);
  }

  // Push stars outward from a screen position when shockwave hits
  function shockwaveStars(sx, sy, strength) {
    const world = toWorldPerspective(sx, sy);
    for (let i = 0; i < starCount; i++) {
      const dx = starOrigPositions[i*3]   - world.x;
      const dy = starOrigPositions[i*3+1] - world.y;
      const dist = Math.sqrt(dx*dx + dy*dy) + 1;
      const force = (strength * 12000) / (dist * dist + 4000);
      starVelocities[i*3]   += (dx / dist) * force;
      starVelocities[i*3+1] += (dy / dist) * force;
    }
  }

  function updateStarfield(novaActive) {
    if (!starPoints) return;
    const pos = starGeo.attributes.position.array;
    let anyMoved = false;
    for (let i = 0; i < starCount; i++) {
      const vx = starVelocities[i*3], vy = starVelocities[i*3+1];
      if (Math.abs(vx) < 0.001 && Math.abs(vy) < 0.001) continue;
      anyMoved = true;
      pos[i*3]   += vx;
      pos[i*3+1] += vy;
      // spring back + dampen
      pos[i*3]   += (starOrigPositions[i*3]   - pos[i*3])   * 0.04;
      pos[i*3+1] += (starOrigPositions[i*3+1] - pos[i*3+1]) * 0.04;
      starVelocities[i*3]   *= 0.88;
      starVelocities[i*3+1] *= 0.88;
    }
    if (anyMoved) starGeo.attributes.position.needsUpdate = true;

    // Dim stars during whiteout
    let targetAlpha = 1.0;
    for (const [, state] of planets) {
      if (state.phase === 3 && state._p3) {
        const elapsed = performance.now() - state.animStart - pauseOffset;
        const { VEIL_IN_MS, REVEAL_MS } = state._p3;
        if (elapsed > VEIL_IN_MS - 300 && elapsed < REVEAL_MS + 1200) {
          const ramp = Math.min((elapsed - (VEIL_IN_MS-300)) / 500, 1);
          const fade = elapsed < REVEAL_MS ? ramp : 1 - (elapsed - REVEAL_MS) / 1200;
          targetAlpha = Math.max(0, 1 - fade * 0.85);
        }
      }
    }
    starPoints.material.uniforms.globalAlpha.value +=
      (targetAlpha - starPoints.material.uniforms.globalAlpha.value) * 0.06;
  }

  // Smooth parallax: nudge camera toward mouse
  function updateParallax() {
    if (!camera) return;
    const targetX = mouseNorm.x * 38;
    const targetY = mouseNorm.y * 22;
    camera.position.x += (targetX - camera.position.x) * 0.025;
    camera.position.y += (targetY - camera.position.y) * 0.025;
    camera.lookAt(0, 0, -600);
  }

  function init() {
    novaCanvas = document.getElementById('nova-canvas');
    W2 = novaCanvas.width  = window.innerWidth;
    H2 = novaCanvas.height = window.innerHeight;

    renderer = new THREE.WebGLRenderer({ canvas: novaCanvas, alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(W2, H2);
    renderer.setClearColor(0x000000, 0);
    renderer.outputEncoding = THREE.sRGBEncoding;

    scene  = new THREE.Scene();
    // Perspective camera: FOV 60, near 0.1, far 3000
    camera = new THREE.PerspectiveCamera(60, W2 / H2, 0.1, 3000);
    camera.position.set(0, 0, 0);

    initStarfield();

    // Mouse parallax
    window.addEventListener('mousemove', e => {
      mouseNorm.x =  (e.clientX / W2 - 0.5) * 2;
      mouseNorm.y = -(e.clientY / H2 - 0.5) * 2;
    });
    // Gyroscope on mobile
    if (window.DeviceOrientationEvent) {
      window.addEventListener('deviceorientation', e => {
        if (e.gamma != null) mouseNorm.x =  Math.max(-1, Math.min(1, e.gamma / 20));
        if (e.beta  != null) mouseNorm.y = -Math.max(-1, Math.min(1, (e.beta - 45) / 20));
      });
    }

    THREE_loaded = true;
    animate();
  }

  function resize() {
    if (!THREE_loaded) return;
    W2 = novaCanvas.width  = window.innerWidth;
    H2 = novaCanvas.height = window.innerHeight;
    renderer.setSize(W2, H2);
    camera.aspect = W2 / H2;
    camera.updateProjectionMatrix();
  }

  // Convert screen coords to Three.js world coords at z=0 plane (perspective)
  function toWorld(sx, sy) {
    // For supernova effects, keep them at z=0 relative to camera look-at
    const fovRad = (60 * Math.PI) / 180;
    const h = 2 * Math.tan(fovRad / 2) * 600; // at z=-600 from camera
    const w = h * (W2 / H2);
    return new THREE.Vector2(
      (sx / W2 - 0.5) * w,
      -(sy / H2 - 0.5) * h
    );
  }

  // Same but returns THREE.Vector3 for shockwave use
  function toWorldPerspective(sx, sy) {
    const v = toWorld(sx, sy);
    return v;
  }

  // ── Phase objects pool ──
  function makePlanetState(sx, sy) {
    const key = sx + ',' + sy;
    if (planets.has(key)) return planets.get(key);
    const state = {
      sx, sy,
      phase: 0,        // 0=idle, 1-5=phases
      animStart: 0,
      group: new THREE.Group(),
      meshes: [],      // disposable meshes per phase
      nebulaParts: [], // for phase 4
      shockwaves: [],  // rings for phase 3
    };
    const wp = toWorld(sx, sy);
    // Place effects at z=-600 (same plane used in toWorld)
    state.group.position.set(wp.x, wp.y, -600);
    scene.add(state.group);
    planets.set(key, state);
    return state;
  }

  // dispose all phase meshes
  function clearMeshes(state) {
    flashVeil.style.opacity = 0; // always reset veil when switching phase
    for (const m of state.meshes) {
      if (m.geometry) m.geometry.dispose();
      if (m.material) m.material.dispose();
      state.group.remove(m);
    }
    state.meshes = [];
    state.nebulaParts = [];
    state.shockwaves = [];
  }

  // ────────────────────────────────
  // PHASE 1: Energy accumulation — blue-white corona + inward particles
  // ────────────────────────────────
  function startPhase1(state) {
    clearMeshes(state);
    // Soft outer corona halo
    const coronaGeo = new THREE.CircleGeometry(120, 64);
    const coronaMat = new THREE.MeshBasicMaterial({
      color: 0x88ccff,
      transparent: true, opacity: 0,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const corona = new THREE.Mesh(coronaGeo, coronaMat);
    state.group.add(corona); state.meshes.push(corona);

    // Sparse inward energy motes — subtle, not chaotic
    const count = 48;
    const positions = new Float32Array(count * 3);
    const progArr   = new Float32Array(count);
    const angArr    = new Float32Array(count);
    const radArr    = new Float32Array(count);
    for (let i = 0; i < count; i++) {
      angArr[i] = Math.random() * Math.PI * 2;
      radArr[i] = 38 + Math.random() * 42;
      progArr[i] = Math.random();
      positions[i*3]   = Math.cos(angArr[i]) * radArr[i] * (1 - progArr[i]);
      positions[i*3+1] = Math.sin(angArr[i]) * radArr[i] * (1 - progArr[i]);
      positions[i*3+2] = 0;
    }
    const ptGeo = new THREE.BufferGeometry();
    ptGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const ptMat = new THREE.PointsMaterial({
      color: 0xaaccff, size: 1.6,
      transparent: true, opacity: 0,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    const pts = new THREE.Points(ptGeo, ptMat);
    state.group.add(pts); state.meshes.push(pts);

    state._p1 = { corona, coronaMat, pts, ptGeo, positions, progArr, angArr, radArr, count };
  }

  function updatePhase1(state, t) {
    const p = state._p1; if (!p) return;
    // Slow, gentle pulse — 0.5 cycle per second
    const pulse = 0.5 + 0.5 * Math.sin(t * 3.2);
    const fadeIn = Math.min(t / 2, 1); // ease in over 2 seconds
    // Very subtle corona shimmer
    p.coronaMat.opacity = (0.04 + 0.025 * pulse) * fadeIn;
    p.corona.scale.setScalar(0.9 + 0.12 * pulse);
    // Particles slowly spiral inward
    const pos = p.positions;
    for (let i = 0; i < p.count; i++) {
      p.progArr[i] = (p.progArr[i] + 0.0008) % 1;
      const r = p.radArr[i] * (1 - p.progArr[i]);
      p.angArr[i] += 0.008;
      pos[i*3]   = Math.cos(p.angArr[i]) * r;
      pos[i*3+1] = Math.sin(p.angArr[i]) * r;
    }
    p.ptGeo.attributes.position.needsUpdate = true;
    p.pts.material.opacity = (0.3 + 0.2 * pulse) * fadeIn;
  }

  // ────────────────────────────────
  // PHASE 2: Core collapse — star shrinks to white point, space darkens
  // ────────────────────────────────
  function startPhase2(state) {
    clearMeshes(state);
    // Dark veil (darken surroundings)
    const veilGeo = new THREE.CircleGeometry(200, 64);
    const veilMat = new THREE.MeshBasicMaterial({
      color: 0x000008, transparent: true, opacity: 0,
      blending: THREE.NormalBlending, depthWrite: false,
    });
    const veil = new THREE.Mesh(veilGeo, veilMat);
    state.group.add(veil); state.meshes.push(veil);

    // Core contracting sphere
    const coreGeo = new THREE.CircleGeometry(1, 32);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0xffffff, transparent: true, opacity: 0,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    const core = new THREE.Mesh(coreGeo, coreMat);
    state.group.add(core); state.meshes.push(core);

    // Outer glow around contracting core
    const glowGeo = new THREE.CircleGeometry(1, 32);
    const glowMat = new THREE.MeshBasicMaterial({
      color: 0x4488ff, transparent: true, opacity: 0,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    const glow = new THREE.Mesh(glowGeo, glowMat);
    state.group.add(glow); state.meshes.push(glow);

    state._p2 = { veil, veilMat, core, coreMat, glow, glowMat };
  }

  function updatePhase2(state, t) {
    const p = state._p2; if (!p) return;
    // First 0.6: collapse inward
    const collapse = Math.min(t / 0.6, 1);
    const ease = 1 - Math.pow(1 - collapse, 3);
    // Core goes from planet size (34px) to tiny white dot
    const coreR = 34 * (1 - ease) + 2;
    p.coreMat.opacity = Math.min(t * 4, 1);
    p.core.scale.setScalar(coreR);
    // Glow around core
    p.glowMat.opacity = ease * 0.6;
    p.glow.scale.setScalar(coreR * 3);
    // Dark veil builds up
    p.veilMat.opacity = ease * 0.55;
    p.veil.scale.setScalar(1 + ease * 0.5);
  }

  // ────────────────────────────────
  // PHASE 3: Explosion — shockwaves + bloom flash + particle jets
  // ────────────────────────────────
  // DOM full-screen white veil element
  const flashVeil = document.getElementById('flash-veil');

  function startPhase3(state) {
    clearMeshes(state);

    // Timeline (ms):
    //   0 – 1600  : inward-spiralling suction particles (energy charging)
    //   0 – 1600  : radial glow builds slowly outward
    //   1600–2000 : glow pulses bright, suction stops, core flares
    //   2000–2500 : white veil slams in
    //   2500–4000 : pure white whiteout holds (1.5s)
    //   4000–5500 : veil fades revealing shockwaves + jets
    //   4000+     : shockwaves expand

    const CHARGE_MS  = 1600; // suction phase duration
    const VEIL_IN_MS = 2000; // veil starts rising
    const VEIL_HOLD  = 2500; // veil fully opaque
    const REVEAL_MS  = 4800; // veil starts fading / shockwaves start (2.3s whiteout)

    // ── Radial glow layers ──
    const flashLayers = [
      { r: 100, color: 0xffffff, peakOp: 1.0  },
      { r: 280, color: 0xaaccff, peakOp: 0.85 },
      { r: 550, color: 0x7744dd, peakOp: 0.45 },
      { r: 860, color: 0x441188, peakOp: 0.20 },
    ];
    const flashMeshes = [];
    for (const fl of flashLayers) {
      const g = new THREE.CircleGeometry(fl.r, 64);
      const m = new THREE.MeshBasicMaterial({
        color: fl.color, transparent: true, opacity: 0,
        blending: THREE.AdditiveBlending, depthWrite: false,
      });
      const mesh = new THREE.Mesh(g, m);
      mesh.userData.peakOp = fl.peakOp;
      state.group.add(mesh); state.meshes.push(mesh);
      flashMeshes.push(mesh);
    }

    // ── Inward suction particles (energy charging toward core) ──
    const sCount = 220;
    const sPos   = new Float32Array(sCount * 3);
    const sAngle = new Float32Array(sCount);   // initial angle
    const sDist  = new Float32Array(sCount);   // initial distance from centre
    const sSpeed = new Float32Array(sCount);   // inward speed (px/s)
    for (let i = 0; i < sCount; i++) {
      sAngle[i] = Math.random() * Math.PI * 2;
      sDist[i]  = 120 + Math.random() * 280;   // spawn 120–400px out
      sSpeed[i] = 80 + Math.random() * 120;    // 80–200 px/s inward
      sPos[i*3] = sPos[i*3+1] = sPos[i*3+2] = 0;
    }
    const sGeo = new THREE.BufferGeometry();
    sGeo.setAttribute('position', new THREE.BufferAttribute(sPos, 3));
    const sMat = new THREE.PointsMaterial({
      color: 0x88ccff, size: 2.5, transparent: true, opacity: 0,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    const suction = new THREE.Points(sGeo, sMat);
    state.group.add(suction); state.meshes.push(suction);

    // ── Shockwave rings ──
    const rings = [];
    const ringColors = [0xeef5ff, 0xaaddff, 0xff9944, 0xff5511, 0xcc2200];
    for (let i = 0; i < 5; i++) {
      const rGeo = new THREE.RingGeometry(1, 1.055, 96);
      const rMat = new THREE.MeshBasicMaterial({
        color: ringColors[i], transparent: true, opacity: 0,
        blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide,
      });
      const ring = new THREE.Mesh(rGeo, rMat);
      ring.userData.delay  = i * 0.14;
      ring.userData.speed  = 190 + i * 36;
      ring.userData.peakR  = 30 + i * 12;
      ring.userData.peakOp = [0.9, 0.8, 0.7, 0.6, 0.5][i];
      state.group.add(ring); state.meshes.push(ring);
      rings.push(ring); state.shockwaves.push(ring);
    }

    // ── Particle jets ──
    const jCount = 400;
    const jPos  = new Float32Array(jCount * 3);
    const jVel  = new Float32Array(jCount * 3);
    const jLife = new Float32Array(jCount);
    const jDel  = new Float32Array(jCount);
    for (let i = 0; i < jCount; i++) {
      const a = Math.random() * Math.PI * 2;
      const sp = 2.5 + Math.random() * 5.5;
      jVel[i*3] = Math.cos(a) * sp; jVel[i*3+1] = Math.sin(a) * sp; jVel[i*3+2] = 0;
      jPos[i*3] = jPos[i*3+1] = jPos[i*3+2] = 0;
      jLife[i] = 0; jDel[i] = Math.random() * 0.25;
    }
    const jGeo = new THREE.BufferGeometry();
    jGeo.setAttribute('position', new THREE.BufferAttribute(jPos, 3));
    const jMat = new THREE.PointsMaterial({
      color: 0xffffff, size: 3, transparent: true, opacity: 0,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    const jets = new THREE.Points(jGeo, jMat);
    state.group.add(jets); state.meshes.push(jets);

    state._p3 = {
      flashMeshes, rings, jets, jGeo, jPos, jVel, jLife, jDel, jCount,
      suction, sGeo, sPos, sAngle, sDist, sSpeed, sCount,
      CHARGE_MS, VEIL_IN_MS, VEIL_HOLD, REVEAL_MS,
    };
  }

  function updatePhase3(state, ms) {
    const p = state._p3; if (!p) return;
    const { CHARGE_MS, VEIL_IN_MS, VEIL_HOLD, REVEAL_MS } = p;

    // ── 1. Inward suction particles (0 → CHARGE_MS) ──
    if (ms < VEIL_IN_MS) {
      const chargeT = Math.min(ms / CHARGE_MS, 1); // 0→1 during charge
      const sPos = p.sPos;
      for (let i = 0; i < p.sCount; i++) {
        // each particle travels inward; when it reaches centre, respawn at edge
        const elapsed = ms / 1000;
        const travelFrac = (elapsed * p.sSpeed[i] / p.sDist[i]) % 1;
        const dist = p.sDist[i] * (1 - travelFrac); // shrinks toward 0
        // add slight spiral drift
        const a = p.sAngle[i] + travelFrac * 1.2;
        sPos[i*3]   = Math.cos(a) * dist;
        sPos[i*3+1] = Math.sin(a) * dist;
        sPos[i*3+2] = 0;
      }
      p.sGeo.attributes.position.needsUpdate = true;
      // fade in quickly then out as veil rises
      const sOp = ms < CHARGE_MS
        ? Math.min(ms / 300, 1) * 0.7                       // fade in over 300ms
        : Math.max(0, 1 - (ms - CHARGE_MS) / (VEIL_IN_MS - CHARGE_MS)) * 0.7;
      p.suction.material.opacity = sOp;
      // colour shifts blue→white as charge builds
      const blue = Math.max(0, 1 - chargeT);
      p.suction.material.color.setRGB(blue * 0.5 + 0.5, blue * 0.8 + 0.2, 1);
    } else {
      p.suction.material.opacity = 0;
    }

    // ── 2. Radial glow ──
    const glowRatio = ms < CHARGE_MS
      ? Math.pow(ms / CHARGE_MS, 0.55)                      // ease-in charge build
      : ms < VEIL_IN_MS ? 1.0 + (ms - CHARGE_MS) / (VEIL_IN_MS - CHARGE_MS) * 0.4 // flare up extra
      : ms < VEIL_HOLD  ? 1.4                               // hold flare while veil rises
      : Math.max(0, 1 - (ms - VEIL_HOLD) / 1200);          // fade behind veil
    for (const fm of p.flashMeshes) {
      fm.material.opacity = Math.min(1, glowRatio) * fm.userData.peakOp;
    }

    // ── 3. Full-screen DOM veil ──
    let veilOp = 0;
    if (ms >= VEIL_IN_MS && ms < VEIL_HOLD)       veilOp = (ms - VEIL_IN_MS) / (VEIL_HOLD - VEIL_IN_MS);
    else if (ms >= VEIL_HOLD && ms < REVEAL_MS)   veilOp = 1.0;
    else if (ms >= REVEAL_MS && ms < REVEAL_MS + 1600) veilOp = 1 - (ms - REVEAL_MS) / 1600;
    flashVeil.style.opacity = veilOp;

    // ── 4. Shockwave rings ──
    for (const ring of p.rings) {
      const ringStartMs = REVEAL_MS + ring.userData.delay * 1000;
      if (ms < ringStartMs) { ring.material.opacity = 0; continue; }
      const localMs = ms - ringStartMs;
      const r = Math.max(1, localMs / 1000 * ring.userData.speed);
      ring.scale.setScalar(r);
      const riseR    = ring.userData.peakR;
      const maxFadeR = ring.userData.speed * 4.5;
      const opacity  = r < riseR
        ? (r / riseR) * ring.userData.peakOp
        : ring.userData.peakOp * Math.max(0, 1 - (r - riseR) / (maxFadeR - riseR));
      ring.material.opacity = opacity;
    }

    // ── 5. Jet particles ──
    const jetLocalMs = ms - REVEAL_MS;
    if (jetLocalMs > 0) {
      const t = jetLocalMs / 1000;
      const pos = p.jPos; const vel = p.jVel;
      for (let i = 0; i < p.jCount; i++) {
        if (t < p.jDel[i]) continue;
        p.jLife[i] += 0.018;
        pos[i*3]   += vel[i*3];
        pos[i*3+1] += vel[i*3+1];
      }
      p.jGeo.attributes.position.needsUpdate = true;
      const jetFade = jetLocalMs < 400
        ? jetLocalMs / 400
        : Math.max(0, 1 - (jetLocalMs - 400) / 3000);
      p.jets.material.opacity = jetFade * 0.85;
      if (jetLocalMs < 1000)      p.jets.material.color.setHex(0xffffff);
      else if (jetLocalMs < 2500) p.jets.material.color.setHex(0x88aaff);
      else                        p.jets.material.color.setHex(0xaa66ff);
    } else {
      p.jets.material.opacity = 0;
    }
  }

  // ────────────────────────────────
  // PHASE 4: Nebula expansion — rolling gas clouds
  // ────────────────────────────────
  function startPhase4(state) {
    clearMeshes(state);
    const partCount = 300;
    const parts = [];
    const colors = [
      0x3366ff, 0x6633ff, 0xff6633, 0xff3366,
      0xaa44ff, 0xff9944, 0x44aaff,
    ];
    for (let i = 0; i < partCount; i++) {
      const a   = Math.random() * Math.PI * 2;
      const spd = 0.18 + Math.random() * 0.55;
      const geo = new THREE.CircleGeometry(6 + Math.random() * 18, 16);
      const mat = new THREE.MeshBasicMaterial({
        color: colors[Math.floor(Math.random() * colors.length)],
        transparent: true, opacity: 0,
        blending: THREE.AdditiveBlending, depthWrite: false,
      });
      const m = new THREE.Mesh(geo, mat);
      m.userData = {
        vx: Math.cos(a) * spd, vy: Math.sin(a) * spd,
        rot: (Math.random() - 0.5) * 0.04,
        delay: Math.random() * 0.35,
        maxOpacity: 0.08 + Math.random() * 0.18,
        spin: (Math.random() - 0.5) * 0.02,
      };
      state.group.add(m); state.meshes.push(m);
      state.nebulaParts.push(m); parts.push(m);
    }
    state._p4 = { parts };
  }

  function updatePhase4(state, t) {
    const p = state._p4; if (!p) return;
    for (const m of p.parts) {
      const d = m.userData.delay;
      if (t < d) continue;
      const local = (t - d) / (1 - d);
      m.position.x += m.userData.vx * 1.8;
      m.position.y += m.userData.vy * 1.8;
      m.rotation.z += m.userData.spin;
      // fade in then plateau
      const fadeIn = Math.min(local / 0.2, 1);
      m.material.opacity = fadeIn * m.userData.maxOpacity;
    }
  }

  function sustainPhase4(state) {
    // Very slow drift while sustained (between sweeps)
    for (const m of state.nebulaParts) {
      m.position.x += m.userData.vx * 0.12;
      m.position.y += m.userData.vy * 0.12;
      m.rotation.z += m.userData.spin * 0.3;
    }
  }

  // ────────────────────────────────
  // PHASE 5: Fade out — nebula disperses, star returns
  // ────────────────────────────────
  function startPhase5(state) {
    // Don't clear — fade out existing nebula + shockwave remnants
    state._p5 = { startOpacities: state.nebulaParts.map(m => m.material.opacity) };
  }

  function updatePhase5(state, t) {
    const p = state._p5; if (!p) return;
    const fade = 1 - t;
    for (let i = 0; i < state.nebulaParts.length; i++) {
      const m = state.nebulaParts[i];
      m.material.opacity = (p.startOpacities[i] || 0) * fade;
      m.position.x += m.userData.vx * 0.08;
      m.position.y += m.userData.vy * 0.08;
    }
  }

  // ────────────────────────────────
  // Main animation loop
  // ────────────────────────────────
  const PHASE_DURATION = {
    1: 99999, // sustained until next sweep
    2: 99999,
    3: 5500,  // ms — rings need time to fully expand and fade
    4: 99999,
    5: 3000,
  };

  // ── Pause state ──
  let fxPaused    = false;
  let pauseOffset = 0;    // accumulated paused time
  let pausedAt    = null; // timestamp when paused

  // Is the explosion in whiteout phase? (lock pause during this window)
  function isExplosionLocked() {
    for (const [, state] of planets) {
      if (state.phase !== 3 || !state._p3) continue;
      const { VEIL_IN_MS, REVEAL_MS } = state._p3;
      const elapsed = performance.now() - state.animStart - pauseOffset;
      if (elapsed >= VEIL_IN_MS && elapsed <= REVEAL_MS + 1600) return true;
    }
    return false;
  }

  function animate() {
    requestAnimationFrame(animate);
    if (!THREE_loaded) return;

    updateParallax();
    updateStarfield();

    if (fxPaused) { renderer.render(scene, camera); return; } // frozen frame

    const now = performance.now();

    for (const [, state] of planets) {
      if (state.phase === 0) continue;
      // elapsed excludes time spent paused
      const elapsed = now - state.animStart - pauseOffset;
      const t = Math.min(elapsed / PHASE_DURATION[state.phase], 1);

      switch (state.phase) {
        case 1: updatePhase1(state, elapsed / 1000); break;
        case 2: updatePhase2(state, t); break;
        case 3: {
          updatePhase3(state, elapsed);
          // Trigger star shockwave at the moment of explosion reveal
          if (!state._shockwaveFired && elapsed > state._p3?.REVEAL_MS) {
            state._shockwaveFired = true;
            shockwaveStars(state.sx, state.sy, 1.0);
          }
          break;
        }
        case 4:
          if (t < 1) updatePhase4(state, t);
          else sustainPhase4(state);
          break;
        case 5:
          updatePhase5(state, t);
          if (t >= 1) { clearMeshes(state); state.phase = 0; }
          break;
      }
    }

    renderer.render(scene, camera);
  }

  // ────────────────────────────────
  // Public API
  // ────────────────────────────────
  function onSweep(sx, sy) {
    if (!THREE_loaded) return;
    const state = makePlanetState(sx, sy);
    const nextPhase = state.phase === 0 ? 1 : (state.phase % 5) + 1;
    // animStart accounts for any paused time already accumulated
    state.animStart = performance.now() - pauseOffset;
    state.phase = nextPhase;
    state._shockwaveFired = false; // reset for phase 3

    switch (nextPhase) {
      case 1: startPhase1(state); break;
      case 2: startPhase2(state); break;
      case 3: startPhase3(state); break;
      case 4: startPhase4(state); break;
      case 5: startPhase5(state); break;
    }
  }

  function resetPlanet(sx, sy) {
    const key = sx + ',' + sy;
    const state = planets.get(key);
    if (state) { clearMeshes(state); state.phase = 0; }
  }

  function pause() {
    if (fxPaused || isExplosionLocked()) return false; // locked during whiteout
    fxPaused  = true;
    pausedAt  = performance.now();
    return true;
  }

  function resume() {
    if (!fxPaused) return;
    fxPaused     = false;
    pauseOffset += performance.now() - pausedAt;
    pausedAt     = null;
  }

  function isPaused() { return fxPaused; }

  function onResize() { resize(); }

  // Wait for THREE to load then init
  function tryInit() {
    if (typeof THREE !== 'undefined') { init(); }
    else { setTimeout(tryInit, 50); }
  }
  setTimeout(tryInit, 0);

  return { onSweep, resetPlanet, onResize, pause, resume, isPaused };
})();

// ── FX Registry: all effect engines register here ──
const FXRegistry = [SupernovaEngine];
// Future: FXRegistry.push(NewModuleEngine);
