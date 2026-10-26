// Render the share image (assets/img/og.png, 1200x630) from og.html, and README screenshots of the site.
// Usage: node render_shots.js <site_root> <site_url>   (site_url = where the site is being served locally)
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [root, url] = process.argv.slice(2);
  const b = await chromium.launch();
  // share image
  let p = await b.newPage({ viewport: { width: 1200, height: 630 } });
  await p.goto('file://' + path.resolve('og.html'), { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);
  await p.screenshot({ path: path.join(root, 'assets/img/og.png') });
  await p.close();
  // README screenshots: desktop dark (hero), desktop light (a chart section), mobile dark
  const shots = [
    ['hero-dark.png', 1440, 900, 'dark', null],
    ['staking-light.png', 1440, 1000, 'light', '#c-staking'],
    ['named-dark.png', 1440, 1000, 'dark', '#named .card:nth-of-type(3)'],
    ['mobile-dark.png', 390, 844, 'dark', null],
  ];
  for (const [file, w, h, theme, sel] of shots) {
    const ctx = await b.newContext({ viewport: { width: w, height: h }, colorScheme: theme, deviceScaleFactor: 2 });
    const pg = await ctx.newPage();
    await pg.goto(url, { waitUntil: 'networkidle' });
    await pg.evaluate(() => document.fonts.ready);
    if (sel) {
      const el = await pg.$(sel);
      await el.scrollIntoViewIfNeeded(); await pg.waitForTimeout(1800);
      await el.screenshot({ path: path.join(root, 'docs', file) });
    } else {
      await pg.waitForTimeout(800);
      await pg.screenshot({ path: path.join(root, 'docs', file) });
    }
    await ctx.close();
  }
  await b.close();
})();
