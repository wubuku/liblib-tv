// 批次 143 c 轮 —— 验一件具体的事：**新节点建完能不能拖开？**（b 轮已定位可拖动面）
//
// b 轮像素普查结论：文本节点 192×192 盒内 2106/2256 个采样点命中同一个
//   `DIV`（类名字面量 `data-[connection-receiving=true]:border-transparent …`，
//   父链 `group/canvas-panel-scrollbar` → `react-flow__node`）—— 这就是**可拖动面**。
//   正文只有 123 个采样点在 `P.text-octo-ui-copy` 上（点它会进编辑态）。
//
// 🔑 本轮要回答的是 142 遗留的另一半：叠放**能不能**靠拖开解决。
//   a 轮已证：叠放时框选必失败（`isFree` 要求四角不在**任何**节点内）。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, 组数, idsOf, canvasPos, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 143, 轮: 'c', 目的: '验新节点能否拖开' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };

/** 在指定节点的「可拖动面」上找一个落点：命中那个大面积 DIV、且不落在正文/把手上。 */
const 找可拖落点 = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'not-found' };
  const r = n.getBoundingClientRect();
  const 好 = [];
  for (let y = Math.ceil(r.y) + 6; y <= r.y + r.height - 6; y += 3)
    for (let x = Math.ceil(r.x) + 6; x <= r.x + r.width - 6; x += 3) {
      const h = document.elementFromPoint(x, y);
      if (!h || !(n === h || n.contains(h))) continue;
      // 排除正文与把手：只看 tag DIV、且自身不是 controls 容器
      if (h.tagName !== 'DIV') continue;
      if (h.closest('.octo-text-node-resize-controls')) continue;
      if (h.closest('[contenteditable]')) continue;
      if (h.tagName === 'DIV' && /text-octo-ui-copy/.test(String(h.className || ''))) continue;
      好.push({ x, y });
    }
  if (!好.length) return { __err: 'no-drag-surface' };
  const cx = Math.round(好.reduce((a, b2) => a + b2.x, 0) / 好.length);
  const cy = Math.round(好.reduce((a, b2) => a + b2.y, 0) / 好.length);
  const 中心 = 好.find((q) => q.x === cx && q.y === cy) || 好[Math.floor(好.length / 2)];
  return { x: 中心.x, y: 中心.y, 可拖像素数: 好.length, 节点盒: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) } };
}, id);

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom() };

  const 建 = await 建N个(p, '文本', 2, 断言, 76);
  rec.建 = 建;
  if (!(建.ids && 建.ids.length === 2)) { rec.中止 = '建节点未成'; }
  else {
    const [A, B] = 建.ids;
    rec.建后canvas = await canvasPos(p);
    rec.建后几何 = await p.evaluate((W) => Array.from(document.querySelectorAll('.react-flow__node'))
      .filter((n) => W.includes(n.getAttribute('data-id')))
      .map((n) => { const r = n.getBoundingClientRect();
        return { id: n.getAttribute('data-id'), 屏上: { x: Math.round(r.x), y: Math.round(r.y) }, 逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12) }; }), 建.ids);
    const dA = { dx: rec.建后canvas[A][0] - rec.建后canvas[B][0], dy: rec.建后canvas[A][1] - rec.建后canvas[B][1] };
    rec.叠放偏移 = { canvas: dA, 屏上: [Math.round(dA.dx * 0.6), Math.round(dA.dy * 0.6)] };

    // ---- 先拖**后建**的那个（B 在上层，能直接点到）——
    rec.拖 = [];
    for (const [id, 目标] of [[建.ids[1], [-360, -240]], [建.ids[0], [360, 240]]]) {
      // 拖之前必须先单选它（叠放时下面那个点不到）
      await p.keyboard.press('Escape');
      await p.waitForTimeout(700);
      const 前选 = await selCount(p);
      const 落 = await 找可拖落点(id);
      rec['落点_' + id] = 落;
      if (落.__err) { rec.拖.push({ id, __err: 落.__err }); continue; }
      await p.mouse.click(落.x, 落.y);
      await p.waitForTimeout(1200);
      const 已选 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); return !!(n && n.classList.contains('selected')); }, id);
      断言('拖前单选 ' + id.slice(-6), 已选, { 前选, 已选, 落 });
      const 前canvas = (await canvasPos(p))[id];
      // 🔴 每次拖动前重新断言前置：目标仍选中、落点命中的是该节点
      const 前置 = await p.evaluate(([i, x, y]) => {
        const h = document.elementFromPoint(x, y);
        const nn = h ? h.closest('.react-flow__node') : null;
        return { 命中节点id: nn ? nn.getAttribute('data-id') : null, 目标仍选中: !!document.querySelector(`.react-flow__node[data-id="${i}"].selected`) };
      }, [id, 落.x, 落.y]);
      rec['拖前置_' + id] = 前置;
      if (前置.命中节点id === id && 前置.目标仍选中) {
        await p.mouse.move(落.x, 落.y);
        await p.mouse.down();
        for (let i2 = 1; i2 <= 14; i2++) {
          await p.mouse.move(Math.round(落.x + (目标[0] * i2) / 14), Math.round(落.y + (目标[1] * i2) / 14));
          await p.waitForTimeout(30);
        }
        await p.mouse.up();
        await p.waitForTimeout(1500);
      }
      const 后canvas = (await canvasPos(p))[id];
      rec.拖.push({ id, 前置, 前canvas, 后canvas, 位移: [Math.round((后canvas[0] - 前canvas[0]) * 10) / 10, Math.round((后canvas[1] - 前canvas[1]) * 10) / 10] });
    }
    rec.拖后 = { 状态行: await R.status(), 选中数: await selCount(p) };
    rec.拖后几何 = await p.evaluate((W) => Array.from(document.querySelectorAll('.react-flow__node'))
      .filter((n) => W.includes(n.getAttribute('data-id')))
      .map((n) => { const r = n.getBoundingClientRect();
        return { id: n.getAttribute('data-id'), 屏上: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) } }; }), 建.ids);
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 800); }

// ---- 清理
try {
  const 自建 = (rec.建 && rec.建.ids) || [];
  rec.删除 = [];
  for (const id of 自建) {
    await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    const 落 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
    if (落.__err) { rec.删除.push({ id, __err: 'no-point' }); continue; }
    await p.mouse.click(落.x, 落.y);
    await p.waitForTimeout(1000);
    const 前 = await idsOf(p);
    const 落2 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
    if (落2.__err) { rec.删除.push({ id, __err: 'no-point-2' }); continue; }
    await p.mouse.click(落2.x, 落2.y, { button: 'right' });
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
    const 后 = await idsOf(p);
    rec.删除.push({ id, 消失: 前.filter((x) => !后.includes(x)) });
  }
} catch (e) { rec.删除异常 = String(e).slice(0, 300); }

await settle(p, R);
const 末 = await idsOf(p);
rec.收尾 = { 状态行: await R.status(), 节点数: 末.length, 组数: await 组数(p), 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), 剩余自建: 末.filter((x) => ((rec.建 && rec.建.ids) || []).includes(x)) };
rec.断言全过 = 断言过;
fs.writeFileSync(new URL('./_tmp-b143c.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log('\n===== 收尾 =====\n' + JSON.stringify(rec.收尾, null, 1));
console.log('===== 拖 =====\n' + JSON.stringify(rec.拖, null, 1));
await b.close();
