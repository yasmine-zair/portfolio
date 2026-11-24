"""Tests Playwright du portfolio : rendu, responsive, accessibilité, interactions."""
import asyncio, json, sys, pathlib
from playwright.async_api import async_playwright

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent)
URL = (ROOT / "index.html").resolve().as_uri()
SHOTS = ROOT / "tests" / "screenshots"; SHOTS.mkdir(exist_ok=True)
VIEWPORTS = [("mobile-320", 320, 640, True), ("mobile-375", 375, 812, True), ("tablet-768", 768, 1024, True),
             ("laptop-1366", 1366, 768, False), ("desktop-1920", 1920, 1080, False)]
issues = []

def issue(vp, kind, msg):
    issues.append({"viewport": vp, "type": kind, "detail": msg})

CHECKS_JS = r"""
() => {
  const out = {};
  const vw = innerWidth;
  out.overflowX = document.documentElement.scrollWidth - vw;
  // éléments qui dépassent à droite
  out.overflowing = [...document.querySelectorAll('body *')].filter(e => {
    const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.right > vw + 1 && cs.position !== 'fixed' && !e.closest('[aria-hidden="true"]') && !e.closest('pre');
  }).slice(0, 8).map(e => e.tagName + '.' + e.className + ' right=' + Math.round(e.getBoundingClientRect().right));
  // images cassées
  out.brokenImages = [...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.currentSrc || i.src);
  // images sans alt
  out.imgNoAlt = [...document.images].filter(i => !i.hasAttribute('alt')).map(i => i.src.slice(0, 60));
  // ancres internes
  out.badAnchors = [...document.querySelectorAll('a[href^="#"]')].map(a => a.getAttribute('href'))
     .filter(h => h.length > 1 && !document.querySelector(h));
  // liens externes
  out.extLinks = [...document.querySelectorAll('a[href^="http"]')].map(a => ({href: a.href, rel: a.rel, target: a.target}));
  // cibles tactiles (visibles) < 44px
  out.smallTargets = [...document.querySelectorAll('a, button')].filter(e => {
    const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    if (!r.width || cs.visibility === 'hidden' || e.classList.contains('skip-link')) return false;
    return r.height < 44 || r.width < 44;
  }).map(e => (e.textContent.trim() || e.getAttribute('aria-label') || e.className).slice(0, 40) + ` ${Math.round(e.getBoundingClientRect().width)}x${Math.round(e.getBoundingClientRect().height)}`);
  // hiérarchie des titres
  const hs = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h => +h.tagName[1]);
  out.h1count = hs.filter(x => x === 1).length;
  out.headingSkips = hs.map((h, i) => i && h - hs[i - 1] > 1 ? `h${hs[i-1]}→h${h}` : null).filter(Boolean);
  // textes trop petits (<12px) visibles hors svg décoratif
  out.tinyText = [...document.querySelectorAll('body *')].filter(e => {
    if (!e.childNodes.length || ![...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) return false;
    if (e.closest('svg') || e.closest('[aria-hidden="true"]')) return false;
    const r = e.getBoundingClientRect(); if (!r.width) return false;
    return parseFloat(getComputedStyle(e).fontSize) < 12;
  }).slice(0, 8).map(e => e.textContent.trim().slice(0, 30) + ' ' + getComputedStyle(e).fontSize);
  // contraste simple (texte sur fond opaque le plus proche)
  const parse = c => (c.match(/[\d.]+/g) || []).map(Number);
  const lum = ([r, g, b]) => { const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }; return .2126*f(r) + .7152*f(g) + .0722*f(b); };
  const bgOf = e => { while (e) { const c = parse(getComputedStyle(e).backgroundColor); if (c.length >= 3 && (c[3] === undefined || c[3] > .9)) return c; e = e.parentElement; } return [11, 11, 16]; };
  out.lowContrast = [...document.querySelectorAll('p, li, a, span, dt, dd, h1, h2, h3, h4, code, em')].filter(e => {
    if (e.closest('[aria-hidden="true"]') || e.closest('.accent-grad')) return false;
    const own = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()); if (!own) return false;
    const r = e.getBoundingClientRect(); if (!r.width) return false;
    const fg = parse(getComputedStyle(e).color); if (fg[3] === 0) return false;
    const L1 = lum(fg), L2 = lum(bgOf(e)); const ratio = (Math.max(L1, L2) + .05) / (Math.min(L1, L2) + .05);
    const big = parseFloat(getComputedStyle(e).fontSize) >= 24;
    return ratio < (big ? 3 : 4.5);
  }).slice(0, 10).map(e => e.textContent.trim().slice(0, 30));
  // chevauchements des étiquettes HUD avec la photo / bords
  out.readoutsOut = [...document.querySelectorAll('.readout')].filter(e => getComputedStyle(e).display !== 'none').filter(e => {
    const r = e.getBoundingClientRect(); return r.left < 0 || r.right > vw;
  }).map(e => e.textContent.trim());
  // boutons sans nom accessible
  out.unnamedButtons = [...document.querySelectorAll('button, a')].filter(e => !(e.textContent.trim() || e.getAttribute('aria-label'))).length;
  out.lang = document.documentElement.lang;
  out.title = document.title;
  out.metaDesc = !!document.querySelector('meta[name=description]');
  return out;
}
"""

async def run():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, w, h, mobile in VIEWPORTS:
            ctx = await b.new_context(viewport={"width": w, "height": h}, is_mobile=mobile, has_touch=mobile)
            pg = await ctx.new_page()
            errors, failed = [], []
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.on("console", lambda m: m.type == "error" and errors.append(m.text))
            pg.on("requestfailed", lambda r: failed.append(r.url))
            await pg.goto(URL, wait_until="load")
            await pg.wait_for_timeout(600)
            # faire défiler pour déclencher les apparitions
            H = await pg.evaluate("document.body.scrollHeight")
            for y in range(0, H, h // 2):
                await pg.evaluate(f"scrollTo(0,{y})"); await pg.wait_for_timeout(60)
            await pg.wait_for_timeout(800)
            hidden = await pg.evaluate("[...document.querySelectorAll('.reveal')].filter(e=>!e.classList.contains('is-visible')).length")
            if hidden: issue(name, "reveal", f"{hidden} blocs restent invisibles après défilement")
            await pg.evaluate("scrollTo(0,0)"); await pg.wait_for_timeout(300)
            r = await pg.evaluate(CHECKS_JS)
            if r["overflowX"] > 0: issue(name, "overflow", f"défilement horizontal {r['overflowX']}px : {r['overflowing']}")
            for k, label in [("brokenImages", "image cassée"), ("imgNoAlt", "img sans alt"), ("badAnchors", "ancre cassée"),
                             ("smallTargets", "cible tactile < 44px"), ("headingSkips", "saut de titre"),
                             ("tinyText", "texte < 12px"), ("lowContrast", "contraste insuffisant"), ("readoutsOut", "étiquette HUD hors écran")]:
                if r[k]: issue(name, label, r[k])
            if r["h1count"] != 1: issue(name, "h1", f"{r['h1count']} h1")
            if r["unnamedButtons"]: issue(name, "a11y", f"{r['unnamedButtons']} liens/boutons sans nom")
            for l in r["extLinks"]:
                if l["target"] == "_blank" and "noopener" not in l["rel"]: issue(name, "lien", f"{l['href']} sans noopener")
            local_failed = [u for u in failed if u.startswith("file:")]
            if local_failed: issue(name, "ressource", local_failed)
            if errors: issue(name, "console", errors[:5])

            # menu mobile
            if w < 760:
                t = pg.locator(".nav-toggle")
                if not await t.is_visible(): issue(name, "menu", "bouton menu invisible")
                else:
                    await t.click(); await pg.wait_for_timeout(200)
                    if await t.get_attribute("aria-expanded") != "true" or not await pg.locator("#nav-menu").is_visible():
                        issue(name, "menu", "le menu ne s'ouvre pas")
                    await pg.keyboard.press("Escape"); await pg.wait_for_timeout(150)
                    if await pg.locator("#nav-menu").is_visible(): issue(name, "menu", "Échap ne ferme pas le menu")
                    await t.click(); await pg.locator('#nav-menu a[href="#projets"]').click(); await pg.wait_for_timeout(900)
                    if await pg.locator("#nav-menu").is_visible(): issue(name, "menu", "le menu reste ouvert après un clic sur un lien")
                    top = await pg.evaluate("document.querySelector('#projets').getBoundingClientRect().top")
                    if not (0 <= top <= 140): issue(name, "navigation", f"#projets mal positionné après clic (top={top:.0f})")
            else:
                await pg.locator('.nav-menu a[href="#competences"]').click(); await pg.wait_for_timeout(1800)
                top = await pg.evaluate("document.querySelector('#competences').getBoundingClientRect().top")
                atBottom = await pg.evaluate("Math.ceil(scrollY + innerHeight) >= document.documentElement.scrollHeight - 2")
                if not (0 <= top <= 140) and not atBottom: issue(name, "navigation", f"#competences mal positionné (top={top:.0f})")
                head = await pg.evaluate("getComputedStyle(document.querySelector('.site-header')).position")
                if head != "sticky": issue(name, "header", "en-tête non collant")

            # focus clavier visible
            await pg.goto(URL, wait_until="load"); await pg.keyboard.press("Tab")
            skip = await pg.evaluate("document.activeElement.className")
            if "skip-link" not in skip: issue(name, "clavier", f"1er Tab ne cible pas le lien d'évitement ({skip})")
            # hauteur du premier écran (le hero tient-il ?)
            hero_h = await pg.evaluate("document.querySelector('.hero-cta').getBoundingClientRect().bottom")
            if not mobile and hero_h > h: issue(name, "hero", f"boutons de l'accueil sous la ligne de flottaison ({hero_h:.0f}px > {h}px)")
            await pg.screenshot(path=str(SHOTS / f"qa-{name}.png"), full_page=False)
            await ctx.close()

        # mouvement réduit
        ctx = await b.new_context(viewport={"width": 1366, "height": 768}, reduced_motion="reduce")
        pg = await ctx.new_page(); await pg.goto(URL); await pg.wait_for_timeout(500)
        vis = await pg.evaluate("[...document.querySelectorAll('.reveal')].every(e=>getComputedStyle(e).opacity==='1')")
        if not vis: issue("reduced-motion", "animation", "contenu masqué avec prefers-reduced-motion")
        anim = await pg.evaluate("getComputedStyle(document.querySelector('.ring-outer')).animationName")
        if anim != "none": issue("reduced-motion", "animation", "anneaux encore animés")
        await ctx.close()

        # sans JavaScript
        ctx = await b.new_context(viewport={"width": 1366, "height": 768}, java_script_enabled=False)
        pg = await ctx.new_page(); await pg.goto(URL); await pg.wait_for_timeout(300)
        vis = await pg.evaluate("[...document.querySelectorAll('.reveal')].every(e=>getComputedStyle(e).opacity==='1')")
        if not vis: issue("no-js", "contenu", "contenu invisible sans JavaScript")
        await ctx.close()
        await b.close()

asyncio.run(run())
print(json.dumps(issues, ensure_ascii=False, indent=1))
print(f"\n== {len(issues)} problème(s) ==")
sys.exit(1 if issues else 0)
