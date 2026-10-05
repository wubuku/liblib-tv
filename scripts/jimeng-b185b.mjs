// 批次 185 b 轮：**把「进入导演台」这一click 到底有没有生效量清楚。**
//
// 185 主探针的读数自相矛盾：点了「进入导演台」，然后
//   URL 不变、标签页数 1、节点数 76、`在画布上: true`，
//   而「进导演台后所有视口内控件」**全是画布自己的控件**（顶栏、左栏、节点内的
//   Rename / Add tags / 进入导演台），**一个导演台界面的控件都没有**。
// ⇒ 两种解释必须分开：① **click 没落到那个按钮上**；② 落了，但**界面还没出来 / 没出来**。
//   主探针两样都没验 —— 这正是手册自己那条铁律（截图/点击前先验 DOM 与几何）。
//
// 本轮：① 逐字验 `elementFromPoint` 是不是那个 BUTTON；② 点完**轮询 25 秒**，
// 每秒记一次「URL / 标签页数 / dialog 数 / 新增 testid 数 / 全屏遮罩数」；
// ③ 无论成败都**截图**，把当时的画面固定成证据。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';
import fs from 'node:fs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '185b' };
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
/** 页面「形状」指纹：用来判「有没有多出什么东西」。 */
const 形状 = () => p.evaluate(() => ({
  URL: location.href, 标题: document.title,
  dialog: document.querySelectorAll('[role=dialog]').length,
  全屏遮罩: Array.from(document.querySelectorAll('div')).filter((e) => { const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e); return r.width >= innerWidth * 0.95 && r.height >= innerHeight * 0.95 && cs.position === 'fixed' && cs.zIndex !== 'auto' && +cs.zIndex > 100; }).length,
  节点数: document.querySelectorAll('.react-flow__node').length,
  testid数: new Set(Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid'))).size,
  body直接子节点: document.body.children.length,
  控制点数: document.querySelectorAll('button,[role=button],a[href]').length,
}));
const 前id = await id集();
rec.起点 = { 节点数: 前id.length, 积分: await R.credits(), 缩放: await R.zoom(), 标签页数: b.contexts()[0].pages().length };
const 导演 = await p.evaluate(() => { const n = document.querySelector('.react-flow__node-external'); if (!n) return null;
  const t = n.querySelector('[data-testid="flow-node-title"]');
  return { id: n.getAttribute('data-id'), 标题: t ? (t.innerText || '').trim().split('\n')[0] : null }; });
rec.导演台节点 = 导演;
try {
  const S = await 搜索选中(导演.标题); rec.选中 = S;
  if (!(S.成功 && S.选中集.includes(导演.id))) { rec.结论 = '没选中导演台节点'; }
  else {
    const 前形状 = await 形状(); rec.点前形状 = 前形状;
    const 钮 = await p.evaluate((i) => {
      const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
      const b = Array.from(n.querySelectorAll('button')).find((x) => (x.innerText || '').trim().includes('进入导演台')); if (!b) return null;
      const r = b.getBoundingClientRect();
      const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
      const 落 = document.elementFromPoint(cx, cy);
      return { 逐字: (b.innerText || '').trim(), 屏上: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
        中心: [cx, cy], 落点标签: 落 ? 落.tagName : null, 落点逐字: 落 ? (落.innerText || '').trim().slice(0, 20) : null,
        落点就是这个按钮吗: !!(落 && (落 === b || b.contains(落))) };
    }, 导演.id);
    rec.按钮几何与落点 = 钮;
    if (钮 && 钮.落点就是这个按钮吗) {
      await p.mouse.click(钮.中心[0], 钮.中心[1]);
      rec.轮询 = [];
      for (let t = 1; t <= 25; t++) {
        await p.waitForTimeout(1000);
        const s = await 形状();
        rec.轮询.push({ 秒: t, dialog: s.dialog, 全屏遮罩: s.全屏遮罩, testid数: s.testid数, 控制点数: s.控制点数, 节点数: s.节点数,
          URL变了: s.URL !== 前形状.URL, body子节点变了: s.body直接子节点 !== 前形状.body直接子节点 });
        if (s.URL !== 前形状.URL || s.dialog > 前形状.dialog || s.全屏遮罩 > 前形状.全屏遮罩 || s.testid数 !== 前形状.testid数) { rec.变化出现在第几秒 = t; break; }
      }
      rec.点后形状 = await 形状();
      rec.标签页数 = b.contexts()[0].pages().length;
      rec.新出现的testid = await p.evaluate((前) => {
        const 前集 = new Set(前);
        return Array.from(new Set(Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))).filter((t) => !前集.has(t)).slice(0, 40);
      }, await p.evaluate(() => Array.from(new Set(Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid'))))).slice(0, 0));
      await p.screenshot({ path: 'docs/user-manual/jimeng-canvas/screenshots/_tmp-185b-after-enter.png' });
      rec.已截图 = true;
    } else rec.结论 = '落点不是那个按钮，没有点（不盲点）';
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
const f = 'docs/user-manual/jimeng-canvas/screenshots/_tmp-185b-after-enter.png';
rec.截图 = fs.existsSync(f) ? fs.statSync(f).size + ' 字节' : '没拍到';
console.log(JSON.stringify(rec, null, 1));
process.exit(0);
