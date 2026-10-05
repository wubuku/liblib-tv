// 批次 190 e 轮：**补拍删除三连图**（前面三轮都被各种前置问题挡住了，这一轮只干这一件事）。
//
// 要点（三条都是前几轮踩出来的）：
//   ① **先等内容稳定再拍第一张** —— 190 a 轮的 174 与 176 节点内容不同（缩略图在两张之间加载完了），
//      前后对照被内容变化吃掉；
//   ② **守卫要认 dashed** —— 175 那张是「虚线框标出节点原来在的位置」，
//      190 a 轮的守卫写死了 `3px solid` ⇒ 自己把自己的图拦掉了；
//   ③ **输出到手册目录** —— 190 a 轮用的是相对 CWD 的 `screenshots/`，图落到了**仓库根目录**。
//
// 本轮不做任何粘贴/剪贴板操作（那部分已取证完毕），只做：选中 → 拍 → ⌫ → 拍 → ⌘Z → 拍 → 核验复原。
import { openCanvas, readers, settle, endState } from './jimeng-b135-lib.mjs';
import { mkdirSync } from 'node:fs';

const SHOT_DIR = 'docs/user-manual/jimeng-canvas/screenshots';
mkdirSync(SHOT_DIR, { recursive: true });

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '190e', 目标: '删除前 / 删除后 / 撤销后 三张同裁切对照图' };
await settle(p, R);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
rec.起点 = { 节点数: 基线.ids.length, 缩放: await R.zoom(), 状态行: await R.status(), 积分: await R.credits() };
const 节点数 = async () => (await R.ids()).length;

rec.截图 = [];
rec.读数 = {};

// 选一个视频节点
const 开搜索 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
  if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
if (!开搜索) throw new Error('没有搜索按钮');
await p.mouse.click(开搜索[0], 开搜索[1]); await p.waitForTimeout(1100);
const inp = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
  if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
if (!inp) { await p.keyboard.press('Escape'); throw new Error('搜索面板没打开'); }
await p.mouse.click(inp[0], inp[1]); await p.waitForTimeout(400);
await p.fill('[data-testid="canvas-search-panel"] input', '视频 1'); await p.waitForTimeout(1600);
const 命中 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
  .map((e) => { const r = e.getBoundingClientRect(); return { id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; })
  .filter((x) => x.文字.includes('视频 1')));
if (!命中.length) { await p.keyboard.press('Escape'); throw new Error('搜索无「视频 1」'); }
const 目标id = 命中[0].id;
rec.目标 = { id: 目标id, 标题: '视频 1' };
await p.mouse.click(命中[0].点[0], 命中[0].点[1]); await p.waitForTimeout(1500);
await p.keyboard.press('Escape'); await p.waitForTimeout(700);
// 点标题行把焦点交回画布（⌫ 的前提）
const 点标题 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null; const t = n.querySelector('[data-testid="flow-node-title"]') || n;
  const r = t.getBoundingClientRect(); return [Math.round(r.x + Math.min(30, r.width / 2)), Math.round(r.y + r.height / 2)]; }, 目标id);
if (!点标题) throw new Error('目标节点不在视口内');
await p.mouse.click(点标题[0], 点标题[1]);
// ① 等内容稳定：轮询「节点内有没有 <video> 或已加载缩略图」，最多等 8 秒
rec.稳定 = { 目标: '节点内容加载完再拍', 等了ms: 0, 稳定判据: null };
{
  const t0 = Date.now();
  let ok = false;
  while (Date.now() - t0 < 8000) {
    const s = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      if (!n) return null;
      return { 有video: !!n.querySelector('video'), 有img: !!n.querySelector('img'),
        屏上: (() => { const r = n.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })() }; }, 目标id);
    if (s && (s.有video || s.有img)) { ok = true; rec.稳定.稳定判据 = s; break; }
    await p.waitForTimeout(600);
  }
  rec.稳定.等了ms = Date.now() - t0;
  rec.稳定.已稳定 = ok;
}
await p.waitForTimeout(1200);

// 三张图共用裁切
const rect = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const r = n.getBoundingClientRect(); window.__b190rect = { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
  return window.__b190rect; }, 目标id);
rec.目标屏上 = rect;
const 裁切 = { x: Math.max(0, rect.x - 30), y: Math.max(0, rect.y - 30), width: Math.min(1280, rect.w + 60), height: Math.min(720, rect.h + 60) };
rec.裁切 = 裁切;
await p.evaluate(() => window.__b190rect && (window.__b190rect.x += 0));

// 画框（solid=节点在这，dashed=节点原来在这）；守卫**同时认 solid 与 dashed**
const 画框 = (id, 线型) => p.evaluate(([i, d]) => {
  document.querySelectorAll('[data-b190]').forEach((e) => e.remove());
  const n = i ? document.querySelector(`.react-flow__node[data-id="${i}"]`) : null;
  const r = n ? (() => { const b = n.getBoundingClientRect(); return { x: b.x, y: b.y, w: b.width, h: b.height }; })() : window.__b190rect;
  const o = document.createElement('div');
  o.setAttribute('data-b190', '1');
  o.style.cssText = `position:fixed;left:${r.x - 10}px;top:${r.y - 10}px;width:${r.w + 20}px;height:${r.h + 20}px;`
    + `border:3px ${d} rgb(255,140,0);border-radius:6px;pointer-events:none;z-index:2147483647;box-sizing:border-box`;
  document.body.appendChild(o);
  const ob = o.getBoundingClientRect(); const cs = getComputedStyle(o);
  return { ok: true, 线型: d, 框: { x: Math.round(ob.x), y: Math.round(ob.y), w: Math.round(ob.width), h: Math.round(ob.height) },
    border: cs.border, pointerEvents: cs.pointerEvents,
    框在视口内: ob.x >= 0 && ob.y >= 0 && ob.right <= 1280 && ob.bottom <= 720 };
}, [id, 线型]);
const 守卫 = (f) => { const g = [['框存在', !!(f && f.ok)],
  ['3px 橙框（solid 或 dashed 都算）', !!(f && /3px (solid|dashed) rgb\(255, 140, 0\)/.test(f.border || ''))],
  ['pointer-events none', !!(f && f.pointerEvents === 'none')],
  ['框在视口内', !!(f && f.框在视口内)]];
  return { 全过: g.every((x) => x[1]), 逐条: g }; };
const 拍 = async (名, 说明, 框读数) => {
  const g = 守卫(框读数);
  if (!g.全过) { rec.截图.push({ 名, 跳过: true, 守卫: g }); return; }
  const buf = await p.screenshot({ path: `${SHOT_DIR}/${名}.png`, clip: 裁切 });
  rec.截图.push({ 名, 说明, 字节: buf.length, clip: 裁切, 守卫全过: true, 线型: 框读数.线型 });
};

rec.读数.拍前 = { 状态行: await R.status(), 节点数: await 节点数(), 选中: await R.selCount() };
rec.读数.拍前.画布坐标 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  return m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null; }, 目标id);

await 拍('174-before-delete', '删除前：目标视频节点已选中，橙实线框罩住它', await 画框(目标id, 'solid'));

// ⌫ 删除
const 前 = await 节点数();
await p.keyboard.press('Backspace');
let 后 = 前;
for (let i = 0; i < 16 && 后 === 前; i++) { await p.waitForTimeout(250); 后 = await 节点数(); }
rec.读数.删除 = { 前节点数: 前, 后节点数: 后, 删掉了: 后 === 前 - 1,
  目标还在: (await R.ids()).includes(目标id), 状态行: await R.status() };
await 拍('175-after-delete', '删除后：橙虚线框标出节点原来在的位置，那里已经空了', await 画框(null, 'dashed'));

// ⌘Z 撤销
await p.keyboard.press('Meta+z');
let 复 = 后;
for (let i = 0; i < 20 && 复 === 后; i++) { await p.waitForTimeout(250); 复 = await 节点数(); }
rec.读数.撤销 = { 删除后: 后, 撤销后: 复, 复原了: 复 === 前, 同一id回来了: (await R.ids()).includes(目标id),
  回来后的画布坐标: await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return null; const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
    return m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null; }, 目标id),
  状态行: await R.status() };
await 拍('176-after-undo', '撤销后：同一个节点回到同一个位置（同一个 id）', await 画框(目标id, 'solid'));
await p.evaluate(() => document.querySelectorAll('[data-b190]').forEach((e) => e.remove()));

rec.判定 = {
  内容已稳定后才拍: rec.稳定.已稳定 === true,
  三张都拍到: rec.截图.filter((s) => s.守卫全过).length === 3,
  删除成功: rec.读数.删除.删掉了, 撤销复原: rec.读数.撤销.复原了,
  同一id同一坐标: rec.读数.撤销.同一id回来了 && JSON.stringify(rec.读数.撤销.回来后的画布坐标) === JSON.stringify(rec.读数.拍前.画布坐标),
  节点数回到基线: (await 节点数()) === 基线.ids.length,
  残留: (await R.ids()).filter((x) => !基线.ids.includes(x)),
  非空守卫: { 截图数: rec.截图.length, 通过守卫的: rec.截图.filter((s) => s.守卫全过).length },
};
rec.收尾 = await endState(p, R, 基线);
console.log(JSON.stringify(rec, null, 1));
await b.close();
