import { launch, closePromos, ORIGIN } from './lib.mjs';
const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const 浏览器 = await launch();
const page = 浏览器.page;
try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  await page.mouse.move(676, 773);
  await page.waitForTimeout(400);
  console.log('自证=', await page.evaluate(() => document.elementFromPoint(676, 773)?.closest('button')?.getAttribute('aria-label')));
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(1200);
  for (const p of [[720, 300], [700, 250]]) {
    await page.mouse.move(p[0], p[1]);
    await page.waitForTimeout(500);
    const cands = await page.evaluate(() => [...document.querySelectorAll('div')]
      .map((e) => { const r = e.getBoundingClientRect(); return { e, r, cs: getComputedStyle(e) }; })
      .filter((o) => o.r.width >= 100 && o.r.height >= 15 && o.r.height <= 80 && o.r.left > 500 && o.r.left < 850 && o.r.top > 480 && o.r.top < 760 && o.cs.cursor !== 'auto' && o.cs.visibility === 'hidden' === false)
      .map((o) => ({ t: (o.e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 24), w: Math.round(o.r.width), h: Math.round(o.r.height), l: Math.round(o.r.left), tp: Math.round(o.r.top), cur: o.cs.cursor, vis: o.cs.visibility, op: o.cs.opacity, cls: (o.e.getAttribute('class') || '').slice(0, 40) })));
    console.log('--- 指针在', p, '---');
    for (const c of cands) console.log(JSON.stringify(c));
  }
} catch (e) { console.log('ERR', e.message); } finally { await 浏览器.browser.close(); }
