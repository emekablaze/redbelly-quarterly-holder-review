// Render report.html to PDF (A4) and PNG previews of each page with the pre-installed Chromium.
const { chromium } = require('playwright');
(async () => {
  const [html, pdf, prev] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto('file://' + html, { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: pdf, format: 'A4', printBackground: true, preferCSSPageSize: true,
    displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: '<div style="width:100%;font-size:7pt;color:#596975;padding:0 16mm;display:flex;justify-content:space-between;font-family:sans-serif"><span>RBNT holder report · Q3 2026 · on-chain data, blocks 3025809 to 3209414</span><span class="pageNumber"></span></div>' });
  if (prev) { await p.setViewportSize({ width: 900, height: 1200 }); await p.screenshot({ path: prev, fullPage: true }); }
  await b.close();
})();
