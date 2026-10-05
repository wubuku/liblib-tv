// 诊断：底栏「+」点开的面板里到底有什么（FI-1 的入口定位失败了）
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const R = { 步骤: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'dbg-fi.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;
try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);

  记('—— 底栏所有可见按钮 ——');
  const 底栏 = await page.evaluate(() => {
    const 可见 = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    return [...document.querySelectorAll('button')].filter(可见)
      .map((b) => { const r = b.getBoundingClientRect(); return { 文字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16), aria: b.getAttribute('aria-label'), 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }; })
      .filter((b) => b.框[1] > 700);
  });
  for (const b of 底栏) 记('   ' + JSON.stringify(b));

  记('—— 点最左那枚「+」——');
  const 加 = 底栏.find((b) => b.框[0] < 100 && b.框[1] > 700);
  记('   目标 ' + JSON.stringify(加));
  if (!加) throw new Error('底栏左端没有按钮');
  await page.mouse.click(加.框[0] + 加.框[2] / 2, 加.框[1] + 加.框[3] / 2);
  await page.waitForTimeout(2200);

  记('—— 点开后面板里所有可见条目 ——');
  const 面板 = await page.evaluate(() => {
    const 可见 = (el) => { const r = el.getBoundingClientRect(); return r.width > 4 && r.height > 4; };
    const out = [];
    for (const el of document.querySelectorAll('button,[role="menuitem"],[role="option"],li,div,span')) {
      const r = el.getBoundingClientRect();
      if (!可见(el) || r.width < 80 || r.height < 24 || r.height > 90) continue;
      const t = (el.innerText || '').replace(/\s+/g, ' ').trim();
      if (!t || t.length > 40) continue;
      if (el.children.length > 3) continue;
      out.push({ 文字: t, 标签: el.tagName, role: el.getAttribute('role'), 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
    }
    // 去重：同一个框只留一条
    const seen = new Set();
    return out.filter((x) => { const k = x.框.join(','); if (seen.has(k)) return false; seen.add(k); return true; });
  });
  for (const b of 面板) 记('   ' + JSON.stringify(b));
  await page.screenshot({ path: HERE + '.evidence/dbg-fi-面板.png' });
  记('⛔ 截图 dbg-fi-面板.png');
} catch (e) {
  记('❌ ' + (e && e.message ? e.message : String(e)));
} finally {
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}
