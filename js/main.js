/* Portfolio Yasmine ZAIR — interactions légères, sans dépendance */
(() => {
  "use strict";
  const root = document.documentElement;
  root.classList.add("js");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  /* Année du footer */
  const year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();

  /* Menu mobile */
  const toggle = document.querySelector(".nav-toggle");
  const menu = document.getElementById("nav-menu");
  if (toggle && menu) {
    const setOpen = (open) => {
      menu.classList.toggle("open", open);
      toggle.setAttribute("aria-expanded", String(open));
      toggle.querySelector(".sr-only").textContent = open ? "Fermer le menu" : "Ouvrir le menu";
    };
    toggle.addEventListener("click", () => setOpen(!menu.classList.contains("open")));
    menu.addEventListener("click", (e) => { if (e.target.closest("a")) setOpen(false); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && menu.classList.contains("open")) { setOpen(false); toggle.focus(); } });
  }

  /* Barre de progression + lien actif */
  const bar = document.querySelector(".scroll-progress span");
  const onScroll = () => {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    if (bar) bar.style.transform = `scaleX(${max > 0 ? window.scrollY / max : 0})`;
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  const links = [...document.querySelectorAll('.nav-menu a[href^="#"]')];
  const sections = links.map((a) => document.querySelector(a.getAttribute("href"))).filter(Boolean);
  if ("IntersectionObserver" in window) {
    const spy = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (!en.isIntersecting) return;
        links.forEach((a) => a.setAttribute("aria-current", String(a.getAttribute("href") === `#${en.target.id}`)));
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    sections.forEach((s) => spy.observe(s));

    /* Apparition au scroll */
    const revealer = new IntersectionObserver((entries, obs) => {
      entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add("is-visible"); obs.unobserve(en.target); } });
    }, { threshold: 0.12 });
    document.querySelectorAll(".reveal").forEach((el, i) => {
      el.style.transitionDelay = `${(i % 4) * 60}ms`;
      revealer.observe(el);
    });
  } else {
    document.querySelectorAll(".reveal").forEach((el) => el.classList.add("is-visible"));
  }

  /* Texte qui s'écrit (hero) */
  const typer = document.getElementById("typer-text");
  const words = ["Robotique mobile", "ROS 2", "Régulation & contrôle", "Python · C · C++", "MATLAB / Simulink"];
  if (typer && !reduceMotion.matches) {
    let w = 0, c = words[0].length, deleting = true;
    const tick = () => {
      const word = words[w];
      c += deleting ? -1 : 1;
      typer.textContent = word.slice(0, c);
      let delay = deleting ? 40 : 75;
      if (!deleting && c === word.length) { deleting = true; delay = 1800; }
      else if (deleting && c === 0) { deleting = false; w = (w + 1) % words.length; delay = 300; }
      setTimeout(tick, delay);
    };
    setTimeout(tick, 2200);
  }

  /* Fond : réseau neuronal animé (canvas) */
  const canvas = document.getElementById("neural-bg");
  if (!canvas || !canvas.getContext) return;
  const ctx = canvas.getContext("2d");
  let w = 0, h = 0, dpr = 1, nodes = [], raf = 0;
  const mouse = { x: -9999, y: -9999 };

  const resize = () => {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    w = window.innerWidth; h = window.innerHeight;
    canvas.width = w * dpr; canvas.height = h * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const count = Math.round(Math.min(90, (w * h) / 18000));
    nodes = Array.from({ length: count }, () => ({
      x: Math.random() * w, y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.25, vy: (Math.random() - 0.5) * 0.25,
      r: Math.random() * 1.4 + 0.6,
    }));
    if (reduceMotion.matches) draw(false);
  };

  const draw = (move = true) => {
    ctx.clearRect(0, 0, w, h);
    const linkDist = 130;
    for (const n of nodes) {
      if (move) {
        n.x += n.vx; n.y += n.vy;
        if (n.x < 0 || n.x > w) n.vx *= -1;
        if (n.y < 0 || n.y > h) n.vy *= -1;
      }
    }
    for (let i = 0; i < nodes.length; i++) {
      const a = nodes[i];
      for (let j = i + 1; j < nodes.length; j++) {
        const b = nodes[j];
        const dx = a.x - b.x, dy = a.y - b.y, d = Math.hypot(dx, dy);
        if (d < linkDist) {
          ctx.strokeStyle = `rgba(34,211,238,${0.12 * (1 - d / linkDist)})`;
          ctx.lineWidth = 1;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        }
      }
      const md = Math.hypot(a.x - mouse.x, a.y - mouse.y);
      if (md < 160) {
        ctx.strokeStyle = `rgba(167,139,250,${0.35 * (1 - md / 160)})`;
        ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(mouse.x, mouse.y); ctx.stroke();
      }
      ctx.fillStyle = "rgba(148,220,238,.55)";
      ctx.beginPath(); ctx.arc(a.x, a.y, a.r, 0, Math.PI * 2); ctx.fill();
    }
  };

  const loop = () => { draw(true); raf = requestAnimationFrame(loop); };
  const start = () => { cancelAnimationFrame(raf); if (!reduceMotion.matches && !document.hidden) loop(); else draw(false); };

  window.addEventListener("resize", () => { resize(); start(); });
  window.addEventListener("pointermove", (e) => { mouse.x = e.clientX; mouse.y = e.clientY; }, { passive: true });
  window.addEventListener("pointerleave", () => { mouse.x = mouse.y = -9999; });
  document.addEventListener("visibilitychange", start);
  reduceMotion.addEventListener?.("change", start);
  resize(); start();
})();
