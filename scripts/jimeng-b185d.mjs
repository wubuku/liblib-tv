// 批次 185 d 轮：**给「返回画布」按钮画橙框并拍成正式证据图。**
//
// 185c 已把往返验通：进入导演台 = 同页全屏 `role=dialog`（`director-stage-shell`，1280×720），
// 返回入口 = 右上角 `BUTTON[aria-label="返回画布"]` `32×32@1236,10`，点它 `dialog 1→0`。
// 但 185c 那张图**没有画框** —— 而本页此前**一张导演台截图都没有**，
// 用户要照着找「返回」按钮，没有框根本指不出来。
//
// 画框手法沿用批次 170–172 的老办法：注入一个 `position:fixed` 的
// `border:3px solid #ff8c00` 的 `div`，`pointer-events:none`、超大 `z-index`。
// 📌 **拍前先验框真的画上了**（读回它的几何与 border），再 shutter —— 手册铁律。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';
import fs from 'node:fs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '185d' };
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(600);
const 节点数 = () => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
const id集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const 选中集 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
const 搜索选中 = async (关键词) => {
  if (typeof 关键词 !== 'string' || !关键词.trim()) return { 成功: false, 原因: '关键词非法' };
  const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!开) return { 成功: false, 原因: '没有搜索按钮' };
  await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
  const 输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
    if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
  if (!输入) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: '搜索面板没有输入框' }; }
  await p.mouse.click(输入[0], 输入[1]); await p.waitForTimeout(400);
  await p.fill('[data-testid="canvas-search-panel"] input', 关键词); await p.waitForTimeout(1400);
  const 命中 = await p.evaluate((w) => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60),
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }).filter((x) => !w || x.文字.includes(w)), 关键词);
  if (!命中.length) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { 成功: false, 原因: `没命中「${关键词}」` }; }
  await p.mouse.click(命中[0].点[0], 命中[0].点[1]); await p.waitForTimeout(1400);
  const s = await 选中集(); await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  return { 成功: s.length >= 1, 选中集: s };
};
const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 积分: await R.credits(), 缩放: await R.zoom(), 标签页数: b.contexts()[0].pages().length };
const 导演 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-external'); if (!n) return null;
  const t = n.querySelector('[data-testid="flow-node-title"]');
  return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null }; });
rec.导演台节点 = 导演;
const 图 = 'docs/user-manual/jimeng-canvas/screenshots/173-director-stage-return-canvas.png';
try {
  const S = await 搜索选中(导演.标题); rec.选中 = S;
  const 钮 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
    const b = Array.from(n.querySelectorAll('button')).find((x) => (x.innerText || '').trim().includes('进入导演台')); if (!b) return null;
    const r = b.getBoundingClientRect(); const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const 落 = document.elementFromPoint(cx, cy);
    return { 中心: [cx, cy], 落点对: !!(落 && (落 === b || b.contains(落))) }; }, 导演.id);
  rec.进入按钮 = 钮;
  if (!(S.成功 && 钮?.落点对)) rec.结论 = '没选中或落点不对，不盲点';
  else {
    await p.mouse.click(钮.中心[0], 钮.中心[1]);
    await p.waitForTimeout(5000);
    rec.浮层在吗 = await p.evaluate(() => { const d = document.querySelector('[data-testid="director-stage-shell"]');
      if (!d) return { 有: false }; const r = d.getBoundingClientRect();
      return { 有: true, aria: d.getAttribute('aria-label'), role: d.getAttribute('role'), 屏上: { w: Math.round(r.width), h: Math.round(r.height) } }; });
    // 画框：罩住「返回画布」按钮，外扩 8px
    rec.画框 = await p.evaluate(() => {
      const btn = Array.from(document.querySelectorAll('button')).find((e) => e.getAttribute('aria-label') === '返回画布');
      if (!btn) return { 成功: false, 原因: '没找到「返回画布」按钮' };
      const r = btn.getBoundingClientRect(); const pad = 8;
      const d = document.createElement('div');
      d.id = '__b185_box';
      d.style.cssText = `position:fixed;left:${r.x - pad}px;top:${r.y - pad}px;width:${r.width + pad * 2}px;height:${r.height + pad * 2}px;`
        + `border:3px solid #ff8c00;border-radius:10px;pointer-events:none;z-index:2147483646`;
      document.body.appendChild(d);
      const b2 = d.getBoundingClientRect(); const cs = getComputedStyle(d);
      return { 成功: true, 按钮屏上: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
        框屏上: { x: Math.round(b2.x), y: Math.round(b2.y), w: Math.round(b2.width), h: Math.round(b2.height) },
        border: cs.borderTopWidth + ' ' + cs.borderTopStyle + ' ' + cs.borderTopColor, pe: cs.pointerEvents, z: cs.zIndex };
    });
    // 📌 拍前断言：框必须**真的在页面上、罩住按钮、颜色是橙色**
    rec.拍前断言 = await p.evaluate(() => { const d = document.getElementById('__b185_box');
      if (!d) return { 框在: false };
      const b = d.getBoundingClientRect(); const btn = Array.from(document.querySelectorAll('button')).find((e) => e.getAttribute('aria-label') === '返回画布');
      const r = btn.getBoundingClientRect();
      return { 框在: true, 框尺寸: { w: Math.round(b.width), h: Math.round(b.height) },
        罩住按钮: b.left <= r.left && b.top <= r.top && b.right >= r.right && b.bottom >= r.bottom,
        框颜色: getComputedStyle(d).borderTopColor }; });
    if (rec.拍前断言.框在 && rec.拍前断言.罩住按钮) {
      await p.screenshot({ path: 图 });
      rec.截图 = fs.existsSync(图) ? fs.statSync(图).size + ' 字节' : '没拍到';
      rec.截图路径 = 图;
    } else rec.结论 = '框没验过，不拍（不拍没有证据的图）';
    await p.evaluate(() => document.getElementById('__b185_box')?.remove());
    // 返回：点右上角「返回画布」
    const 返 = await p.evaluate(() => { const btn = Array.from(document.querySelectorAll('button')).find((e) => e.getAttribute('aria-label') === '返回画布');
      if (!btn) return null; const r = btn.getBoundingClientRect();
      return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 屏上: { w: Math.round(r.width), h: Math.round(r.height) } }; });
    rec.返回按钮 = 返;
    if (返) { await p.mouse.click(返.中心[0], 返.中心[1]); await p.waitForTimeout(3500);
      rec.返回后 = { dialog数: await p.evaluate(() => document.querySelectorAll('[role=dialog]').length),
        浮层还在吗: await p.evaluate(() => !!document.querySelector('[data-testid="director-stage-shell"]')),
        节点数: await 节点数(), URL: p.url(), 状态行: await R.status() }; }
  }
} catch (e) { rec.异常 = String(e).slice(0, 200); }
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
await p.reload({ waitUntil: 'domcontentloaded' }); await pinViewport(p);
const t0 = Date.now();
while (Date.now() - t0 < 60000) { if (await p.evaluate(() => document.querySelectorAll('.react-flow__node').length)) break; await p.waitForTimeout(500); }
await p.waitForTimeout(3000);
const 末 = await id集();
rec.收尾核验 = { 现在节点数: 末.length, 起点节点数: 前id.length, 残留id: 末.filter((i) => !前id.includes(i)), 丢失id: 前id.filter((i) => !末.includes(i)) };
rec.收尾 = { URL: p.url(), 状态行: await R.status(), 积分: await R.credits(), 缩放: await R.zoom(), 浮层: await R.overlays(), 标签页数: b.contexts()[0].pages().length };
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
