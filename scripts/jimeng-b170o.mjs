// 批次 170 —— 截图取证。
// 四张图：空白右键菜单 / 节点右键菜单 / 「新建节点」子菜单 / 窄窗夹取。
// ⛔ 只右键，不点任何菜单条目；不点生成/上传/删除。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const DIR = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url).pathname;
const rec = { 批次: '170', 目的: '右键菜单的四个面：宽 240/200 两档、高度累加公式、贴边 8px 翻转、视口 16px 夹取' };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b170-shots.json', import.meta.url), JSON.stringify(rec, null, 1));

/** 在目标元素外框处画一个橙色高亮框（截图后再撤掉）。 */
const 框 = (page, sel) => page.evaluate((s) => {
  document.querySelectorAll('.__b170hl').forEach((e) => e.remove());
  const e = document.querySelector(s);
  if (!e) return null;
  const r = e.getBoundingClientRect();
  const d = document.createElement('div');
  d.className = '__b170hl';
  d.style.cssText = `position:fixed;left:${r.x - 4}px;top:${r.y - 4}px;` +
    `width:${r.width + 8}px;height:${r.height + 8}px;` +
    `border:3px solid #ff8c00;border-radius:14px;pointer-events:none;z-index:2147483646`;
  document.body.appendChild(d);
  return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
}, sel);
const 撤框 = (page) => page.evaluate(() => document.querySelectorAll('.__b170hl').forEach((e) => e.remove()));

const 读菜单 = (page) => page.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-context-menu"]');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  const items = Array.from(e.querySelectorAll('[role=menuitem]')).map((x) => ({
    t: (x.innerText || '').trim().split('\n')[0].slice(0, 14),
    禁用: x.getAttribute('aria-disabled') === 'true',
    h: Math.round(x.getBoundingClientRect().height),
  }));
  return {
    盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    右下距视口: [Math.round(innerWidth - (r.x + r.width)), Math.round(innerHeight - (r.y + r.height))],
    sizeAttr: e.getAttribute('data-context-menu-size'),
    scrollable: e.getAttribute('data-context-menu-scrollable'),
    分隔线: e.querySelectorAll('[role=separator]').length,
    entries: items,
    文字: (e.innerText || '').trim().split('\n').filter(Boolean),
  };
});

const blank = (page) => page.evaluate(() => {
  for (let y = 30; y < innerHeight - 30; y += 10)
    for (let x = 30; x < innerWidth - 30; x += 10) {
      const e = document.elementFromPoint(x, y);
      if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) return [x, y];
    }
  return null;
});
const nodePt = (page) => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node [data-testid="audio-node-empty"]');
  if (!n) return null;
  const node = n.closest('.react-flow__node');
  const r = node.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
});

const { b, p } = await openCanvas();
const R = readers(p);
await pinViewport(p);
rec.基线 = { status: await R.status(), credits: await R.credits() };
console.log('基线', JSON.stringify(rec.基线));

// —— 图 128：空白画布右键 ——
{
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
  const pt = await blank(p);
  await p.mouse.click(pt[0], pt[1], { button: 'right' });
  await p.waitForTimeout(900);
  rec.图128 = { 锚点: pt, ...(await 读菜单(p)) };
  console.log('128:', JSON.stringify(rec.图128));
  const bx = await 框(p, '[data-testid="canvas-context-menu"]');
  await p.waitForTimeout(250);
  await p.screenshot({ path: DIR + '128-canvas-rightclick-blank-240x172.png' });
  await 撤框(p);
}
// —— 图 129：节点右键 ——
{
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
  const pt = await nodePt(p);
  await p.mouse.click(pt[0], pt[1], { button: 'right' });
  await p.waitForTimeout(900);
  rec.图129 = { 锚点: pt, ...(await 读菜单(p)) };
  console.log('129:', JSON.stringify(rec.图129));
  await 框(p, '[data-testid="canvas-context-menu"]');
  await p.waitForTimeout(250);
  await p.screenshot({ path: DIR + '129-canvas-rightclick-node-200x292.png' });
  await 撤框(p);
}
// —— 图 130：「新建节点」子菜单展开 ——
{
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  const pt = await blank(p);
  await p.mouse.click(pt[0], pt[1], { button: 'right' });
  await p.waitForTimeout(900);
  const trig = await p.evaluate(() => {
    const t = document.querySelector('[data-testid="canvas-context-menu"]').firstElementChild.firstElementChild;
    const r = t.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  await p.mouse.move(trig[0], trig[1]);
  await p.waitForTimeout(1100);
  rec.图130 = await p.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-context-menu"]');
    for (const c of e.querySelectorAll('div')) {
      const cs = getComputedStyle(c);
      if (cs.position === 'absolute' && cs.visibility === 'visible' && c.getBoundingClientRect().height > 50) {
        const r = c.getBoundingClientRect();
        return {
          盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          className: c.getAttribute('class'), style: c.getAttribute('style'),
          条目: Array.from(c.querySelectorAll('[role=menuitem]'))
            .map((x) => (x.innerText || '').trim().split('\n')[0].slice(0, 14)),
        };
      }
    }
    return null;
  });
  console.log('130:', JSON.stringify(rec.图130));
  const subSel = await p.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-context-menu"]');
    for (const c of e.querySelectorAll('div')) {
      const cs = getComputedStyle(c);
      if (cs.position === 'absolute' && cs.visibility === 'visible' && c.getBoundingClientRect().height > 50) {
        c.setAttribute('data-b170-sub', '1'); return '1';
      }
    }
    return null;
  });
  await 框(p, '[data-b170-sub="1"]');
  await p.waitForTimeout(250);
  await p.screenshot({ path: DIR + '130-canvas-new-node-submenu-212x404.png' });
  await 撤框(p);
  await p.evaluate(() => document.querySelectorAll('[data-b170-sub]').forEach((e) => e.removeAttribute('data-b170-sub')));
}
// —— 图 131：窄窗夹取（新页签做，收尾 pinViewport 复位共享页签）——
{
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  const bp = await blank(p);
  if (bp) { await p.mouse.click(bp[0], bp[1]); await p.waitForTimeout(400); }
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);

  const tab = await b.contexts()[0].newPage();
  await tab.goto(p.url(), { waitUntil: 'domcontentloaded' });
  await tab.waitForSelector('.react-flow__node', { timeout: 60000 });
  await tab.waitForTimeout(3500);
  await tab.context().newCDPSession(tab).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride', { width: 250, height: 720, deviceScaleFactor: 2, mobile: false });
  });
  await tab.waitForTimeout(1500);
  const pt = await blank(tab);
  await tab.mouse.click(pt[0], pt[1], { button: 'right' });
  await tab.waitForTimeout(1000);
  rec.图131 = { 视口: [250, 720], 锚点: pt, ...(await 读菜单(tab)) };
  console.log('131:', JSON.stringify(rec.图131));
  await 框(tab, '[data-testid="canvas-context-menu"]');
  await tab.waitForTimeout(250);
  await tab.screenshot({ path: DIR + '131-canvas-rightmenu-clamped-250px.png' });
  await 撤框(tab);
  await tab.keyboard.press('Escape');
  await tab.waitForTimeout(300);
  await tab.close();
}

const vp = await pinViewport(p);
rec.收尾 = { 视口: vp, status: await R.status(), sel: await R.selCount(), credits: await R.credits(),
  残留菜单: await p.evaluate(() => document.querySelectorAll('[data-testid="canvas-context-menu"]').length) };
console.log('收尾', JSON.stringify(rec.收尾));
落盘();
await b.close();
