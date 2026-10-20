#!/usr/bin/env node
/**
 * capture_screens.js — screenshot a running web app for RedesignMyApp (Pluristack).
 *
 * Requires Playwright with Chromium installed (npm i -D playwright && npx playwright install chromium,
 * or pip install playwright && python -m playwright install chromium — the Node package is needed to run this file).
 *
 * Usage:
 *   node capture_screens.js --base http://localhost:5173 --out redesign/screens \
 *   node capture_screens.js --extension <unpacked-extension-dir> --out redesign/screens   (browser extensions; routes are page files, e.g. /newtab.html)
 *     [--routes redesign/routes.txt | --inventory redesign/inventory.json] \
 *     [--viewports mobile,tablet,desktop] [--schemes light,dark] [--crawl 2] [--styles] \
 *     [--login-url /login --user U --pass P --user-sel 'input[name=email]' --pass-sel 'input[type=password]'] \
 *     [--wait 1500] [--max-routes 60]
 *
 * Output: PNGs named <route-slug>--<viewport>--<scheme>.png and a manifest.json.
 */
const fs = require('fs');
const path = require('path');

function resolvePlaywright() {
  const candidates = ['playwright', 'playwright-core'];
  for (const c of candidates) {
    try { return require(c); } catch (_) { /* try next */ }
  }
  // global npm prefix fallback
  try {
    const { execSync } = require('child_process');
    const prefix = execSync('npm root -g', { encoding: 'utf8' }).trim();
    for (const c of candidates) {
      try { return require(path.join(prefix, c)); } catch (_) { /* next */ }
    }
  } catch (_) { /* ignore */ }
  console.error('Playwright not found. Install with: npm i -D playwright && npx playwright install chromium');
  process.exit(2);
}

function parseArgs(argv) {
  const args = { viewports: 'mobile,tablet,desktop', schemes: 'light,dark', crawl: '0', wait: '1200', maxRoutes: '60' };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) continue;
    const key = a.slice(2).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
    const next = argv[i + 1];
    if (next === undefined || next.startsWith('--')) { args[key] = true; } else { args[key] = next; i++; }
  }
  return args;
}

const VIEWPORTS = {
  mobile: { width: 390, height: 844, isMobile: true, hasTouch: true, deviceScaleFactor: 2 },
  tablet: { width: 834, height: 1194, isMobile: true, hasTouch: true, deviceScaleFactor: 2 },
  desktop: { width: 1440, height: 900, isMobile: false, hasTouch: false, deviceScaleFactor: 1 },
  wide: { width: 1920, height: 1080, isMobile: false, hasTouch: false, deviceScaleFactor: 1 },
};

function slug(route) {
  const s = route.replace(/^\/+|\/+$/g, '').replace(/[^a-z0-9]+/gi, '-').replace(/^-+|-+$/g, '').toLowerCase();
  return s || 'home';
}

function loadRoutes(args) {
  let routes = [];
  if (args.routes && fs.existsSync(args.routes)) {
    routes = fs.readFileSync(args.routes, 'utf8').split('\n').map(s => s.trim()).filter(s => s && !s.startsWith('#'));
  } else if (args.inventory && fs.existsSync(args.inventory)) {
    const inv = JSON.parse(fs.readFileSync(args.inventory, 'utf8'));
    routes = (inv.screens || []).map(s => s.route).filter(r => typeof r === 'string' && r.startsWith('/'));
  }
  if (!routes.length) routes = ['/'];
  // drop dynamic segments we cannot fill
  routes = routes.filter(r => !/[:\[\]*]/.test(r));
  return [...new Set(routes)];
}

(async () => {
  const args = parseArgs(process.argv);
  if ((!args.base && !args.extension) || !args.out) {
    console.error('Required: --base <url> (or --extension <unpacked-dir>) and --out <dir>');
    process.exit(1);
  }
  const { chromium } = resolvePlaywright();
  let base = (args.base || '').replace(/\/+$/, '');
  const outDir = path.resolve(args.out);
  fs.mkdirSync(outDir, { recursive: true });
  const viewports = args.viewports.split(',').map(s => s.trim()).filter(v => VIEWPORTS[v]);
  const schemes = args.schemes.split(',').map(s => s.trim()).filter(s => s === 'light' || s === 'dark');
  const waitMs = parseInt(args.wait, 10);
  const crawlDepth = parseInt(args.crawl, 10);
  const maxRoutes = parseInt(args.maxRoutes, 10);
  let routes = loadRoutes(args);

  // Browser extension mode: load the unpacked extension into a persistent Chromium profile and
  // rewrite routes to chrome-extension://<id>/<page>. Requires Playwright's `chromium` channel (new headless).
  let browser, extContext = null, extBase = null;
  if (args.extension) {
    const extDir = path.resolve(args.extension);
    const userData = fs.mkdtempSync(path.join(require('os').tmpdir(), 'rma-ext-'));
    extContext = await chromium.launchPersistentContext(userData, {
      channel: 'chromium', headless: true,
      args: [`--disable-extensions-except=${extDir}`, `--load-extension=${extDir}`],
    });
    let sw = extContext.serviceWorkers()[0];
    if (!sw) sw = await extContext.waitForEvent('serviceworker', { timeout: 20000 }).catch(() => null);
    let extId = sw ? new URL(sw.url()).host : null;
    if (!extId) {
      const bg = extContext.backgroundPages()[0];
      if (bg) extId = new URL(bg.url()).host;
    }
    if (!extId) { console.error('Could not determine the extension id (no service worker / background page). Is manifest.json valid?'); process.exit(3); }
    extBase = `chrome-extension://${extId}`;
    browser = extContext.browser();
    console.log(`Extension loaded as ${extBase}`);
  } else {
    browser = await chromium.launch({ headless: true });
  }
  const effectiveBase = extBase || base;
  base = effectiveBase;

  let storageState;
  // One page per (viewport, scheme). In extension mode the persistent context is shared, so we emulate per page.
  async function openPage(vpName, scheme) {
    const vp = VIEWPORTS[vpName];
    if (extContext) {
      const page = await extContext.newPage();
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.emulateMedia({ colorScheme: scheme, reducedMotion: 'reduce' });
      return { page, close: () => page.close() };
    }
    const ctx = await browser.newContext({ ...vp, colorScheme: scheme, storageState, reducedMotion: 'reduce' });
    const page = await ctx.newPage();
    return { page, close: () => ctx.close() };
  }
  const manifest = { base: effectiveBase, generated: new Date().toISOString(), captures: [], errors: [], discovered: [] };

  // Optional login in a shared storage state
  if (args.loginUrl && args.user && args.pass) {
    const { page, close } = await openPage('desktop', 'light');
    try {
      await page.goto(base + args.loginUrl, { waitUntil: 'networkidle', timeout: 30000 });
      await page.fill(args.userSel || 'input[type=email], input[name=email], input[name=username], input[type=text]', args.user);
      await page.fill(args.passSel || 'input[type=password]', args.pass);
      await Promise.all([
        page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {}),
        page.keyboard.press('Enter'),
      ]);
      storageState = extContext ? undefined : await page.context().storageState();
    } catch (e) {
      manifest.errors.push({ stage: 'login', message: String(e.message || e) });
    }
    await close();
  }

  // Crawl same-origin links to discover routes
  if (crawlDepth > 0) {
    const { page, close } = await openPage('desktop', 'light');
    const seen = new Set(routes);
    let frontier = [...routes];
    for (let d = 0; d < crawlDepth && frontier.length && seen.size < maxRoutes; d++) {
      const next = [];
      for (const r of frontier) {
        try {
          await page.goto(base + r, { waitUntil: 'networkidle', timeout: 30000 });
          const hrefs = await page.$$eval('a[href]', as => as.map(a => a.getAttribute('href')));
          for (const h of hrefs) {
            if (!h || h.startsWith('#') || h.startsWith('mailto:') || h.startsWith('tel:') || h.startsWith('javascript:')) continue;
            let u;
            try { u = new URL(h, base); } catch (_) { continue; }
            if (u.origin !== new URL(base).origin) continue;
            const p = u.pathname.replace(/\/+$/, '') || '/';
            if (/\.(png|jpg|jpeg|svg|pdf|zip|css|js)$/i.test(p)) continue;
            if (!seen.has(p) && seen.size < maxRoutes) { seen.add(p); next.push(p); manifest.discovered.push(p); }
          }
        } catch (e) {
          manifest.errors.push({ stage: 'crawl', route: r, message: String(e.message || e) });
        }
      }
      frontier = next;
    }
    routes = [...seen];
    await close();
  }

  for (const vp of viewports) {
    for (const scheme of schemes) {
      const { page, close } = await openPage(vp, scheme);
      const consoleErrors = [];
      page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0, 200)); });
      for (const route of routes) {
        const file = `${slug(route)}--${vp}--${scheme}.png`;
        const entry = { route, viewport: vp, scheme, file, status: null, console_errors: [] };
        try {
          const resp = await page.goto(base + route, { waitUntil: 'networkidle', timeout: 45000 });
          entry.status = resp ? resp.status() : null;
          // try to honour class-based dark mode too
          if (scheme === 'dark') {
            await page.evaluate(() => {
              document.documentElement.classList.add('dark');
              document.documentElement.setAttribute('data-theme', 'dark');
            }).catch(() => {});
          }
          await page.waitForTimeout(waitMs);
          await page.screenshot({ path: path.join(outDir, file), fullPage: true });
          entry.console_errors = consoleErrors.splice(0);
          if (args.styles && vp === 'desktop' && scheme === 'light') {
            entry.computed_styles = await page.evaluate(() => {
              const pick = (el) => {
                const cs = getComputedStyle(el);
                return { tag: el.tagName.toLowerCase(), cls: (el.className && el.className.baseVal === undefined) ? String(el.className).slice(0, 80) : '',
                  fontFamily: cs.fontFamily, fontSize: cs.fontSize, fontWeight: cs.fontWeight, lineHeight: cs.lineHeight,
                  color: cs.color, background: cs.backgroundColor, padding: cs.padding, margin: cs.margin, borderRadius: cs.borderRadius, boxShadow: cs.boxShadow };
              };
              const sel = 'h1,h2,h3,h4,p,a,button,input,select,textarea,label,nav,header,footer,main,aside,[role=button],[class*=card],[class*=btn]';
              return Array.from(document.querySelectorAll(sel)).slice(0, 120).map(pick);
            }).catch(() => null);
          }
        } catch (e) {
          entry.error = String(e.message || e);
          manifest.errors.push({ stage: 'capture', route, viewport: vp, scheme, message: entry.error });
        }
        manifest.captures.push(entry);
        process.stdout.write(`${entry.error ? 'FAIL' : ' ok '} ${file}${entry.status ? ' (' + entry.status + ')' : ''}\n`);
      }
      await close();
    }
  }
  if (extContext) await extContext.close(); else await browser.close();

  const stylesOut = {};
  for (const c of manifest.captures) if (c.computed_styles) { stylesOut[c.route] = c.computed_styles; delete c.computed_styles; }
  if (Object.keys(stylesOut).length) fs.writeFileSync(path.join(outDir, 'computed-styles.json'), JSON.stringify(stylesOut, null, 2));
  fs.writeFileSync(path.join(outDir, 'manifest.json'), JSON.stringify(manifest, null, 2));
  console.log(`\n${manifest.captures.filter(c => !c.error).length}/${manifest.captures.length} captures written to ${outDir}; ${manifest.errors.length} errors; manifest.json saved.`);
})();
