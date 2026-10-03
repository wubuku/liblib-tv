// 批次 143 diag —— 查两件反直觉的事：
//
//   ❶ **叠放下「后建（在上层）」的节点反而点不到**：c 轮它的落点前置断言读到
//      `命中节点id: null`（落点处 `closest('.react-flow__node')` 为 null），
//      而**先建（被压住）的那个**反而能选中、能拖。
//      两种可能：(a) click 让它进了「编辑态 / 全屏编辑器」，DOM 换了祖先；
//                (b) 落点其实落在了别的元素上（我的「质心」算法没验证质心自身合格）。
//   ❷ **拖动位移与鼠标位移差 7.2%**：c 轮目标屏上 (360,240)，实测 canvas 位移
//      (556.6, 371.2) ⇒ 屏上 (334.0, 222.7)，比值 0.9277 —— 恰好等于 13/14。
//      怀疑：`mouse.up()` 之前最后一次 `mouse.move` 还没被 React 提交。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, canvasPos, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 143, 轮: 'diag' };

/** 一枚像素的完整归属链。 */
const 链 = ([x, y]) => p.evaluate(([a, b2]) => {
  const h = document.elementFromPoint(a, b2);
  if (!h) return { 命中: 'null' };
  const c = []; for (let n = h; n && n !== document.body; n = n.parentElement) {
    c.push({ tag: n.tagName, cls: String(n.className || '').split(' ').slice(0, 3).join(' ').slice(0, 70),
      nodeid: n.getAttribute ? n.getAttribute('data-id') : null, testid: n.getAttribute ? n.getAttribute('data-testid') : null });
  }
  return { 命中: h.tagName, 链: c.slice(0, 8) };
}, [x, y]);

/** 节点内「合格拖动像素」清单（排除正文/把手/可编辑区）。 */
const 合格像素 = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'not-found' };
  const r = n.getBoundingClientRect();
  const 好 = [];
  for (let y = Math.ceil(r.y) + 6; y <= r.y + r.height - 6; y += 3)
    for (let x = Math.ceil(r.x) + 6; x <= r.x + r.width - 6; x += 3) {
      const h = document.elementFromPoint(x, y);
      if (!h || !(n === h || n.contains(h))) continue;
      if (h.tagName !== 'DIV') continue;
      if (h.closest('.octo-text-node-resize-controls')) continue;
      if (h.closest('[contenteditable]')) continue;
      if (/text-octo-ui-copy/.test(String(h.className || ''))) continue;
      好.push([x, y]);
    }
  const cx = Math.round(好.reduce((a, q) => a + q[0], 0) / Math.max(1, 好.length));
  const cy = Math.round(好.reduce((a, q) => a + q[1], 0) / Math.max(1, 好.length));
  return { 总数: 好.length, 质心: [cx, cy], 盒: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
    首5: 好.slice(0, 5), 末5: 好.slice(-5),
    质心处命中归属: (() => { const h = document.elementFromPoint(cx, cy);
      const nn = h ? h.closest('.react-flow__node') : null;
      return { tag: h ? h.tagName : null, cls: h ? String(h.className || '').slice(0, 50) : null, 所属node: nn ? nn.getAttribute('data-id') : null }; })() };
}, id);

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length };

  const 建 = await 建N个(p, '文本', 2, null, 76);
  rec.建 = 建;
  const [A, B] = 建.ids;                 // A 先建（下），B 后建（上）
  rec.叠放 = { A, B, canvas: await canvasPos(p) };
  rec.屏幕 = await p.evaluate((W) => Object.fromEntries(W.map((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const r = n.getBoundingClientRect(); return [i, { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }]; })), 建.ids);
  rec.z序 = await p.evaluate((W) => Object.fromEntries(W.map((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    return [i, { z: n.style.zIndex, computed: getComputedStyle(n).zIndex, cls: String(n.className || '').slice(0, 60) }]; })), 建.ids);

  rec.像素 = {};
  for (const id of 建.ids) rec.像素[id] = await 合格像素(id);

  // ---- 对 B（后建、上层）走一遍：落点 → click → 再看落点处现在是谁
  const b落 = rec.像素[B].质心;
  rec.B落点前 = await 链(b落);
  await p.mouse.click(b落[0], b落[1]);
  await p.waitForTimeout(1400);
  rec.B点击后 = { 选中: await selCount(p), 选中的是谁: await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id'))),
    状态行: await R.status(), 落点处现在: await 链(b落),
    浮层: await p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).map((m) => ({ tag: m.tagName, cls: String(m.className || '').slice(0, 50), 盒: (() => { const r = m.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() }))),
    contenteditable: await p.evaluate(() => Array.from(document.querySelectorAll('[contenteditable]')).map((e) => ({ tag: e.tagName, cls: String(e.className || '').slice(0, 50), 盒: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() }))) };

  // ---- ❷ 位移标定：同一次拖动，记录每一步的实测位置
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  const 落A = rec.像素[A].质心;
  await p.mouse.click(落A[0], 落A[1]); await p.waitForTimeout(1000);
  const 前 = (await canvasPos(p))[A];
  const 轨迹 = [];
  await p.mouse.move(落A[0], 落A[1]);
  await p.mouse.down();
  const STEPS = 14, DX = 200, DY = 120;
  for (let i = 1; i <= STEPS; i++) {
    await p.mouse.move(Math.round(落A[0] + (DX * i) / STEPS), Math.round(落A[1] + (DY * i) / STEPS));
    await p.waitForTimeout(30);
    轨迹.push({ 步: i, 鼠标x: Math.round(落A[0] + (DX * i) / STEPS), 实测canvas: (await canvasPos(p))[A] });
  }
  const up前 = (await canvasPos(p))[A];
  await p.mouse.up();
  await p.waitForTimeout(1200);
  const 后 = (await canvasPos(p))[A];
  rec.拖动标定 = { 落点: 落A, 步数: STEPS, 目标屏上: [DX, DY], 目标canvas: [Math.round(DX / 0.6), Math.round(DY / 0.6)],
    前, up前, 后, 轨迹,
    位移: [Math.round((后[0] - 前[0]) * 10) / 10, Math.round((后[1] - 前[1]) * 10) / 10] };
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

// ---- 清理
try {
  const 自建 = (rec.建 && rec.建.ids) || [];
  rec.删除 = [];
  for (const id of 自建) {
    await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    const 前2 = await idsOf(p);
    const 落 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
    if (落.__err) { rec.删除.push({ id, __err: 'no-point' }); continue; }
    await p.mouse.click(落.x, 落.y, { button: 'right' });
    await p.waitForTimeout(1800);
    const del = await p.evaluate(() => {
      const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
        .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
      if (!els.length) return { __err: 'no-delete-item' };
      const e = els[0]; const r = e.getBoundingClientRect();
      for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
        for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
          const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y };
        }
      return { __err: 'no-point' };
    });
    if (del.__err) { rec.删除.push({ id, __err: del.__err }); continue; }
    await p.mouse.click(del.x, del.y);
    await p.waitForTimeout(2500);
    await settle(p, R);
    const 后2 = await idsOf(p);
    rec.删除.push({ id, 消失: 前2.filter((x) => !后2.includes(x)) });
  }
} catch (e) { rec.删除异常 = String(e).slice(0, 300); }

await settle(p, R);
const 末 = await idsOf(p);
rec.收尾 = { 状态行: await R.status(), 节点数: 末.length, 选中: await selCount(p), 浮层: await R.overlays(), zoom: await R.zoom() };
fs.writeFileSync(new URL('./_tmp-b143-diag.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 叠放: rec.叠放, 屏幕: rec.屏幕, z序: rec.z序, B点击后: rec.B点击后,
  拖动标定: rec.拖动标定, 收尾: rec.收尾 }, null, 1));
await b.close();
