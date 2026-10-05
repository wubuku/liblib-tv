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
  await page.mouse.move(676, 773); await page.waitForTimeout(400);
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(1000);
  await page.mouse.move(720, 300); await page.waitForTimeout(500);
  const 入口 = await page.evaluate(() => {
    const all = [...document.querySelectorAll('div')].filter((e) => {
      const r = e.getBoundingClientRect();
      if (r.left < 555 || r.left > 800 || r.top < 545 || r.top > 745) return false;
      if (getComputedStyle(e).cursor !== 'pointer') return false;
      return (e.innerText || '').trim().startsWith('特效库');
    }).map((e) => ({ e, r: e.getBoundingClientRect() })).sort((a, b) => (b.r.width * b.r.height) - (a.r.width * a.r.height));
    if (!all.length) return null;
    const r = all[0].r;
    return { pt: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], 层级: all.length, 尺寸: [Math.round(r.width), Math.round(r.height)] };
  });
  console.log('入口=', JSON.stringify(入口));
  await page.mouse.move(入口.pt[0], 入口.pt[1]); await page.waitForTimeout(400);
  console.log('自证=', await page.evaluate(([x, y]) => { const e = document.elementFromPoint(x, y); return { tag: e?.tagName, t: (e?.innerText || '').trim().slice(0, 20) }; }, 入口.pt));
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(3000);
  await page.mouse.move(720, 780); await page.waitForTimeout(1000);
  const 诊断 = await page.evaluate(() => ({
    dialog: document.querySelectorAll('[role=dialog]').length,
    modalInner: document.querySelectorAll('.mantine-Modal-inner').length,
    sel1: document.querySelectorAll('.hover\\:bg-canvas-controls-hover').length,
    sel2: document.querySelectorAll('.group.relative').length,
    sel3: document.querySelectorAll('[class*="bg-canvas-controls-hover"]').length,
    任意div: document.querySelectorAll('div').length,
    卡片样本: (() => {
      const out = [];
      for (const e of document.querySelectorAll('div[class]')) {
        const c = e.getAttribute('class');
        if (!/relative/.test(c) || !/rounded/.test(c)) continue;
        const r = e.getBoundingClientRect();
        if (r.width < 120 || r.width > 260 || r.height < 150 || r.height > 320) continue;
        out.push({ cls: c.slice(0, 70), w: Math.round(r.width), h: Math.round(r.height), t: (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 26) });
        if (out.length >= 4) break;
      }
      return out;
    })(),
  }));
  console.log(JSON.stringify(诊断, null, 1));
} catch (e) { console.log('ERR', e.message); } finally { await 浏览器.browser.close(); }
