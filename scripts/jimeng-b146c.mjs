// 批次 146 c 轮 —— 钉死「预览线」这个元件的 DOM 真身，并查「松手后 connection-path 残留」是什么。
//
// 🔑 b 轮新发现（3 次拖拽逐字相同）：
//   拖中：class 计数出现 `react-flow__connectionline` ×1、`react-flow__connection` ×1、
//         `react-flow__connection-path` ×1，**而 `.react-flow__edge` 恒为 0**。
//   ⇒ **预览线不是 `.react-flow__edge`**。批次 136 手册写的「边数 +1」只在**落到节点**时成立；
//      拖拽途中若用 `.react-flow__edge` 计数，会得出「什么都没发生」的错误结论。
//   松手后：`connectionline` / `connection` 消失，但 `react-flow__connection-path` **仍留 1 个**。
//   🔴 这个残留是「没回收干净」还是「另有一个常驻元素」，本轮不猜，做实验定案。
//
// 本轮四问，全部只读、零风险（不建连线、不点任何生成/扣费按钮）：
//   Q1 预览线的**完整 class 链 + tagName + 挂在哪个 svg + path 的 d 是否随鼠标变**（取两个采样）
//   Q2 松手后 `react-flow__connection-path` 那个元素**还在不在**（0.3s / 2.5s / 关菜单后 三个时点）
//      它是什么（tagName / 逐字 outerHTML 前 200 / 是否可见 / 盒）
//   Q3 预览线的 path **是否可见**、盒多大、颜色
//   Q4 菜单弹出与预览线残留**谁先谁后**（松手后立刻 150ms 采一次）
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, selIds, selCount, idsOf, canvasPos, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 146, 轮: 'c', 目的: '钉死预览线 DOM 真身 + 查松手后 connection-path 残留' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };

/** 逐个列出所有 className 里带 connection 的元素（不止取首个 token，要全链）。 */
const 读连接元素 = () => p.evaluate(() => {
  const 出 = [];
  for (const e of document.querySelectorAll('*')) {
    const cls = e.getAttribute('class');
    if (!cls || !/connection/i.test(cls)) continue;
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    const svg = e.ownerSVGElement || (e.closest('svg') || null);
    let svgCls = null;
    if (svg) svgCls = String(svg.getAttribute('class') || '');
    const d = e.getAttribute && e.getAttribute('d');
    出.push({
      tag: e.tagName.toLowerCase(), cls: cls.slice(0, 120),
      可见: cs.display !== 'none' && cs.visibility !== 'hidden' && Number(cs.opacity) > 0 && r.width > 0.01,
      盒: [Math.round(r.x * 10) / 10, Math.round(r.y * 10) / 10, Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
      描边: cs.stroke, 描边宽: cs.strokeWidth, 填充: cs.fill, opacity: cs.opacity, pe: cs.pointerEvents,
      d长度: d ? d.length : null, d前80: d ? d.slice(0, 80) : null,
      父svg: svgCls === null ? null : svgCls.slice(0, 60),
      在edge内: !!e.closest('.react-flow__edge'),
      outer前160: e.outerHTML.slice(0, 160),
    });
  }
  return { edge元素数: document.querySelectorAll('.react-flow__edge').length, 元素: 出 };
});

const 找source = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'not-found' };
  const h = n.querySelector('[data-testid="flow-node-source-handle"]');
  if (!h) return { __err: 'no-source-handle' };
  const r = h.getBoundingClientRect();
  const 外扩 = 24; const 好 = [];
  for (let y = Math.ceil(r.y) - 外扩; y <= r.y + r.height + 外扩 - 1; y += 2)
    for (let x = Math.ceil(r.x) - 外扩; x <= r.x + r.width + 外扩 - 1; x += 2) {
      if (x < 1 || y < 1) continue;
      const e = document.elementFromPoint(x, y);
      if (e && e.closest('[data-testid="flow-node-source-handle"]') === h) 好.push([x, y]);
    }
  if (!好.length) return { __err: 'no-drag-pixel' };
  const gx = 好.reduce((s, q) => s + q[0], 0) / 好.length, gy = 好.reduce((s, q) => s + q[1], 0) / 好.length;
  好.sort((a, b) => Math.hypot(a[0] - gx, a[1] - gy) - Math.hypot(b[0] - gx, b[1] - gy));
  return { 手柄屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10], 可拖像素数: 好.length, 起: 好[0] };
}, id);

const 找真空白落点 = () => p.evaluate(() => {
  const 坏 = (x, y) => { const h = document.elementFromPoint(x, y);
    if (!h) return 1;
    if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button]')) return 1;
    if (h.closest('.react-flow__node') || h.closest('.react-flow__node-toolbar')) return 1;
    if (h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
    return !(h.classList && h.classList.contains('react-flow__pane')); };
  const 候选 = [];
  for (let y = 110; y < 560; y += 10) for (let x = 110; x < 700; x += 10) if (!坏(x, y)) 候选.push([x, y]);
  if (!候选.length) return { __err: 'no-blank' };
  候选.sort((a, b) => Math.hypot(a[0] - 140, a[1] - 150) - Math.hypot(b[0] - 140, b[1] - 150));
  return { 落点: 候选[0], 空白块数: 候选.length, 距当年: Math.round(Math.hypot(候选[0][0] - 140, 候选[0][1] - 150)) };
});

const 清零选中 = async () => {
  for (let k = 0; k < 4 && (await selCount(p)) > 0; k++) {
    const 空 = await p.evaluate(() => {
      const 坏 = (x, y) => { const h = document.elementFromPoint(x, y);
        if (!h) return 1;
        if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button]')) return 1;
        if (h.closest('.react-flow__node') || h.closest('.react-flow__node-toolbar') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
        return !(h.classList && h.classList.contains('react-flow__pane')); };
      for (let y = 90; y < innerHeight - 90; y += 8) for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
      return { __err: 'no-free-pane' };
    });
    if (空.__err) break;
    await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1100);
  }
  return selCount(p);
};

const 删一个 = async (id) => {
  await 清零选中();
  const 前 = await idsOf(p);
  const 落 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
  if (落.__err) return { id, __err: 'no-point' };
  await p.mouse.click(落.x, 落.y, { button: 'right' });
  await p.waitForTimeout(1800);
  const del = await p.evaluate(() => {
    const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button')).filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
    if (!els.length) return { __err: 'no-delete-item' };
    const e = els[0]; const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2) for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
      const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
    return { __err: 'no-point' };
  });
  if (del.__err) return { id, __err: del.__err };
  await p.mouse.click(del.x, del.y); await p.waitForTimeout(2500); await settle(p, R);
  const 后 = await idsOf(p);
  return { id, 消失: 前.filter((x) => !后.includes(x)) };
};

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p);
  await settle(p, R);
  const 起z = await R.zoom();
  if (起z !== 'Zoom options, 60%') { rec.起步归位 = await setZoom(p, 60); await p.waitForTimeout(900); }
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom() };

  const 建 = await 建N个(p, '视频', 1, null, 76);
  rec.建 = 建;
  const SELF = 建.ids && 建.ids[0];
  if (!SELF) rec.中止 = '建节点未成';
  else {
    await p.waitForTimeout(2000); await settle(p, R);
    for (let k = 0; k < 3 && (await R.overlays()) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
    await 清零选中();
    rec.建后 = { 状态行: await R.status(), 选中数: await selCount(p) };

    const nb = await p.evaluate((i) => { const r = document.querySelector(`.react-flow__node[data-id="${i}"]`).getBoundingClientRect();
      return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; }, SELF);
    await p.mouse.move(nb[0] + Math.round(nb[2] / 2), nb[1] + Math.round(nb[3] / 2));
    await p.waitForTimeout(1200);

    const src = await 找source(SELF);
    const 落点 = await 找真空白落点();
    rec.前置件 = { src, 落点, 节点盒: nb };
    if (src.__err || src.起.__err) rec.中止 = 'source: ' + (src.__err || src.起.__err);
    else {
      const 起 = src.起, 到 = 落点.落点;
      const 真前置 = await p.evaluate(([sx, sy, tx, ty, i]) => {
        const hs = document.elementFromPoint(sx, sy); const ht = document.elementFromPoint(tx, ty);
        return { 起点在手柄内: !!(hs && hs.closest('[data-testid="flow-node-source-handle"]')),
          落点命中: ht ? ht.tagName + '.' + String(ht.className || '').split(' ')[0].slice(0, 26) : null,
          落点在节点内: !!(ht && ht.closest('.react-flow__node')),
          落点是按钮: !!(ht && (ht.tagName === 'BUTTON' || ht.closest('button,[role=button]'))),
          选中数: document.querySelectorAll('.react-flow__node.selected').length,
          目标存在: !!document.querySelector(`.react-flow__node[data-id="${i}"]`) };
      }, [起[0], 起[1], 到[0], 到[1], SELF]);
      rec.真前置 = 真前置;
      const 前canvas = (await canvasPos(p))[SELF];
      rec.拖前连接 = await 读连接元素();

      if (真前置.起点在手柄内 && !真前置.落点在节点内 && !真前置.落点是按钮 && 真前置.选中数 === 0) {
        await p.mouse.move(起[0], 起[1]);
        await p.mouse.down();
        // 拖到半程
        const 半 = [Math.round(起[0] + (到[0] - 起[0]) * 0.5), Math.round(起[1] + (到[1] - 起[1]) * 0.5)];
        for (let i2 = 1; i2 <= 6; i2++) {
          await p.mouse.move(Math.round(起[0] + ((半[0] - 起[0]) * i2) / 6), Math.round(起[1] + ((半[1] - 起[1]) * i2) / 6));
          await p.waitForTimeout(40);
        }
        await p.waitForTimeout(400);
        rec.采样A = await 读连接元素();      // 半程
        // 再拖到 3/4 程
        const 三四 = [Math.round(起[0] + (到[0] - 起[0]) * 0.75), Math.round(起[1] + (到[1] - 起[1]) * 0.75)];
        for (let i2 = 1; i2 <= 6; i2++) {
          await p.mouse.move(Math.round(半[0] + ((三四[0] - 半[0]) * i2) / 6), Math.round(半[1] + ((三四[1] - 半[1]) * i2) / 6));
          await p.waitForTimeout(40);
        }
        await p.waitForTimeout(400);
        rec.采样B = await 读连接元素();      // 3/4 程 —— 与 A 比，d 若变则「跟着鼠标走」得证
        for (let i2 = 1; i2 <= 6; i2++) {
          await p.mouse.move(Math.round(三四[0] + ((到[0] - 三四[0]) * i2) / 6), Math.round(三四[1] + ((到[1] - 三四[1]) * i2) / 6));
          await p.waitForTimeout(40);
        }
        await p.waitForTimeout(300);
        rec.采样C_松手前 = await 读连接元素();
        await p.mouse.up();
        await p.waitForTimeout(150);
        rec.松后150ms = await 读连接元素();   // Q4 谁先谁后
        await p.waitForTimeout(2350);
        rec.松后2500ms = await 读连接元素();
        rec.松手后 = { 状态行: await R.status(), 选中数: await selCount(p), 选中: await 读选中缺省(), 浮层: await R.overlays() };
        // 关菜单
        for (let k = 0; k < 3 && (await R.overlays()) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
        await p.waitForTimeout(1200);
        rec.关菜单后 = await 读连接元素();
        const 后c = (await canvasPos(p))[SELF];
        rec.源位移 = [Math.round((后c[0] - 前canvas[0]) * 100) / 100, Math.round((后c[1] - 前canvas[1]) * 100) / 100];
      } else rec.未拖 = '前置不满足';
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

function 读选中缺省() { return p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id'))); }

try { rec.删除 = []; for (const id of ((rec.建 && rec.建.ids) || [])) rec.删除.push(await 删一个(id)); }
catch (e) { rec.删除异常 = String(e).slice(0, 300); }
rec.归位 = await setZoom(p, 60);
await p.waitForTimeout(900);
const 小地图前 = await R.minimap();
if (!小地图前 || 小地图前.ariaPressed !== 'true') {
  const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3);
  if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); }
}
rec.小地图后 = await R.minimap();
await settle(p, R);
const 末 = await idsOf(p);
rec.收尾 = { 状态行: await R.status(), 节点数: 末.length, 选中: await selCount(p), 浮层: await R.overlays(),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length),
  剩余connection元素: await 读连接元素(), zoom: await R.zoom(), 积分: await R.credits() };
rec.断言全过 = 断言过;
fs.writeFileSync(new URL('./_tmp-b146c.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 起点: rec.起点, 建后: rec.建后, 真前置: rec.真前置, 松手后: rec.松手后,
  源位移: rec.源位移, 收尾: { 状态行: rec.收尾.状态行, 节点数: rec.收尾.节点数, 边数: rec.收尾.边数, zoom: rec.收尾.zoom, 积分: rec.收尾.积分 },
  异常: rec.异常, 中止: rec.中止, 未拖: rec.未拖, 删除: rec.删除 }, null, 1));
console.log('--- 各时点 connection 元素数 ---');
for (const k of ['拖前连接', '采样A', '采样B', '采样C_松手前', '松后150ms', '松后2500ms', '关菜单后'])
  console.log(k, rec[k] ? JSON.stringify({ edge: rec[k].edge元素数, 数: rec[k].元素.length, cls: rec[k].元素.map((e) => e.tag + '|' + e.cls.split(' ').slice(0, 3).join('.') + '|vis=' + e.可见 + '|d=' + e.d长度) }) : '—');
await b.close();
