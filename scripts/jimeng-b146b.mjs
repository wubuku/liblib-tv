// 批次 146 b 轮 —— 把「拖到空白松手 ⇒ 源节点变选中」**连续复现 3 次**，给未决项定案。
//
// 📌 a 轮（1 次）已复现的三条，与批次 72 逐字一致：
//   ✅ 菜单**在松手瞬间**弹出（不是松手后再点 +），出现在**松手点**，`200×316`、aria `添加节点`
//   ✅ 菜单内容：视频源**只有「视频」可点**，其余「无法连接这些节点」等禁用逐字一致
//   ✅ **边数 0**、源节点 canvas 位移 **`[0,0]`**
// 🔴 a 轮**第四次**没复现「源节点变选中」（状态行 `0 selected`）。
//   而 AUDIT 记：历史三次里唯一那次 `1 selected`，**预览线压根没出现**（不是一次成功的拖拽），
//   **被选中的还是另一个节点**。
//
// ⇒ 本轮做 3 次连续独立复现（同一个自建视频节点，每次拖完关菜单 + 点空白清回 0 选中），
//   判据只判**互斥性**（「源节点有没有被选中」），不预设结论。
//
// 🔴 顺带修两个判据缺陷：
//   ① **预览线**：a 轮按 `className` 匹配 `/connection|preview|draft/i` 读出 0，
//      但菜单是在松手后才弹的、边数全程 0 ⇒ **0 很可能不代表「没有」**。改扫 SVG 下的 path。
//   ② **菜单可点性**：批次 72 的硬证据是「只有视频可点、其余 `aria-disabled` + `cursor: not-allowed`」，
//      a 轮只读了 `innerText` 逐字。改逐项读 `aria-disabled` / `data-disabled` / `cursor`。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, selIds, selCount, idsOf, canvasPos, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 146, 轮: 'b', 目的: '「源节点变选中」连续复现 3 次以定案' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };

const 读选中 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected'))
  .map((n) => ({ id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label') })));

/** 菜单逐项可点性（批次 72 的硬证据口径）。 */
const 读菜单 = () => p.evaluate(() => {
  const m = Array.from(document.querySelectorAll('[role=menu]')).find((q) => q.getBoundingClientRect().width > 1);
  if (!m) return null;
  const r = m.getBoundingClientRect();
  const 项 = Array.from(m.querySelectorAll('[role=menuitem]')).map((e) => { const q = e.getBoundingClientRect();
    return { 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
      盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      ariaDisabled: e.getAttribute('aria-disabled'), dataDisabled: e.getAttribute('data-disabled'),
      cursor: getComputedStyle(e).cursor }; });
  return { testid: m.getAttribute('data-testid'), aria: m.getAttribute('aria-label'),
    盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    逐字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120), 项 };
});

/** 🔴 修好的预览线判据：扫 SVG 下的 path 与全部 class 里带 connection 的元素。 */
const 读连线态 = () => p.evaluate(() => {
  const cls = [];
  for (const e of document.querySelectorAll('svg path, svg g, .react-flow__edge, [class*="connection"]')) {
    const c = String(e.getAttribute('class') || '');
    if (c) cls.push(c.slice(0, 60));
  }
  const 计数 = {};
  for (const c of cls) { const k = c.split(' ')[0]; 计数[k] = (计数[k] || 0) + 1; }
  return { 边元素数: document.querySelectorAll('.react-flow__edge').length,
    path总数: document.querySelectorAll('svg path').length,
    connection类计数: 计数,
    画布内所有svg: Array.from(document.querySelectorAll('.react-flow__renderer > svg')).map((s) => {
      const r = s.getBoundingClientRect(); return { cls: String(s.className.baseVal || s.className || '').slice(0, 50),
        盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }) };
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
      if (!e) continue;
      if (e.closest('[data-testid="flow-node-source-handle"]') === h) 好.push([x, y]);
    }
  // 🔴 不取质心（像素集不连续时质心会落到别的元素上）——按「到几何中心的距离」排序取第 0 个
  const gx = 好.reduce((s, q) => s + q[0], 0) / 好.length, gy = 好.reduce((s, q) => s + q[1], 0) / 好.length;
  const 排 = 好.slice().sort((a, b) => Math.hypot(a[0] - gx, a[1] - gy) - Math.hypot(b[0] - gx, b[1] - gy));
  return { 手柄屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
    可拖像素数: 好.length, 可拖中心: 排.length ? 排[0] : null, 几何中心: [Math.round(gx), Math.round(gy)] };
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
  const 起 = await R.zoom();
  if (起 !== 'Zoom options, 60%') { rec.起步归位 = await setZoom(p, 60); await p.waitForTimeout(900); }
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits() };

  const 建 = await 建N个(p, '视频', 1, null, 76);
  rec.建 = 建;
  const SELF = 建.ids && 建.ids[0];
  if (!SELF) { rec.中止 = '建节点未成'; }
  else {
    await p.waitForTimeout(2000); await settle(p, R);
    for (let k = 0; k < 3 && (await R.overlays()) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
    rec.建后 = { 状态行: await R.status(), 位置: await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      const r = n.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; }, SELF) };

    rec.三次 = [];
    for (let 次 = 1; 次 <= 3; 次++) {
      const 残留选中 = await 清零选中();
      const nb = rec.建后.位置;
      await p.mouse.move(nb[0] + Math.round(nb[2] / 2), nb[1] + Math.round(nb[3] / 2));
      await p.waitForTimeout(1200);
      const src = await 找source(SELF);
      const 落点 = await 找真空白落点();
      if (src.__err || !src.可拖中心 || 落点.__err) {
        rec.三次.push({ 次, __err: 'source ' + (src.__err || src.可拖像素数) + ' / 落点 ' + (落点.__err || 'ok') });
        break;
      }
      const 起 = src.可拖中心, 到 = 落点.落点;
      const 真前置 = await p.evaluate(([sx, sy, tx, ty, i]) => {
        const hs = document.elementFromPoint(sx, sy);
        const ht = document.elementFromPoint(tx, ty);
        return { 起点在手柄内: !!(hs && hs.closest('[data-testid="flow-node-source-handle"]')),
          落点命中: ht ? ht.tagName + '.' + String(ht.className || '').split(' ')[0].slice(0, 26) : null,
          落点在节点内: !!(ht && ht.closest('.react-flow__node')),
          落点是按钮: !!(ht && (ht.tagName === 'BUTTON' || ht.closest('button,[role=button]'))),
          选中数: document.querySelectorAll('.react-flow__node.selected').length,
          目标存在: !!document.querySelector(`.react-flow__node[data-id="${i}"]`) };
      }, [起[0], 起[1], 到[0], 到[1], SELF]);
      const 前canvas = (await canvasPos(p))[SELF];
      const 前连线 = await 读连线态();
      if (真前置.起点在手柄内 && !真前置.落点在节点内 && !真前置.落点是按钮 && 真前置.选中数 === 0) {
        await p.mouse.move(起[0], 起[1]);
        await p.mouse.down();
        for (let i2 = 1; i2 <= 12; i2++) {
          await p.mouse.move(Math.round(起[0] + ((到[0] - 起[0]) * i2) / 12), Math.round(起[1] + ((到[1] - 起[1]) * i2) / 12));
          await p.waitForTimeout(35);
        }
        const 拖中 = await 读连线态();
        await p.mouse.up();
        await p.waitForTimeout(1800);
        rec.三次.push({ 次, 残留选中, 落点: 到, 距当年落点: 落点.距当年,
          source可拖像素: src.可拖像素数, 手柄屏上: src.手柄屏上, 前置: 真前置,
          拖中连线态: 拖中, 前连线态: 前连线,
          松手后: { 选中: await 读选中(), 选中数: await selCount(p), 状态行: await R.status(),
            菜单: await 读菜单(), 连线态: await 读连线态() } });
        const 后c = (await canvasPos(p))[SELF];
        rec.三次[rec.三次.length - 1].源位移 = [Math.round((后c[0] - 前canvas[0]) * 100) / 100, Math.round((后c[1] - 前canvas[1]) * 100) / 100];
      } else {
        rec.三次.push({ 次, 残留选中, 前置: 真前置, __未拖: true });
      }
      // 关菜单 + 清选中，为下一次做准备
      for (let k = 0; k < 3 && (await R.overlays()) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
      rec['次' + 次 + '收'] = { 浮层: await R.overlays(), 选中: await selIds(p) };
    }

    // ---- 出表（先出表，最后才判「哪种解释对」）
    rec.表 = rec.三次.filter((q) => q.松手后).map((q) => ({
      次: q.次, 落点: q.落点, 距当年落点: q.距当年落点,
      菜单弹在落点: !!(q.松手后.菜单 && q.松手后.菜单.盒[0] === q.落点[0] && q.松手后.菜单.盒[1] === q.落点[1]),
      菜单盒: q.松手后.菜单 && q.松手后.菜单.盒, 菜单aria: q.松手后.菜单 && q.松手后.菜单.aria,
      状态行: q.松手后.状态行, 选中数: q.松手后.选中数,
      源被选中: q.松手后.选中.some((z) => z.id === SELF),
      被选中的id: q.松手后.选中.map((z) => z.id),
      边元素数: q.松手后.连线态.边元素数, 源位移: q.源位移,
      拖中path数: q.拖中连线态 && q.拖中连线态.path总数,
      拖中边元素: q.拖中连线态 && q.拖中连线态.边元素数,
    }));
    // 🔴 `.every()` 之前必须有非空断言
    断言('① 三次拖动至少完成 2 次（防空集通过）', rec.表.length >= 2, { 实到: rec.表.length });
    if (rec.表.length >= 2) {
      断言('② 每次菜单都弹在**松手点**上', rec.表.every((q) => q.菜单弹在落点), rec.表.map((q) => [q.次, q.落点, q.菜单盒]));
      断言('③ 每次边元素数都是 0（没建出连线）', rec.表.every((q) => q.边元素数 === 0), rec.表.map((q) => [q.次, q.边元素数]));
      断言('④ 每次源节点 canvas 零位移', rec.表.every((q) => q.源位移[0] === 0 && q.源位移[1] === 0), rec.表.map((q) => [q.次, q.源位移]));
      断言('⑤ 🔑 每次**源节点都没有被选中**', rec.表.every((q) => q.源被选中 === false), rec.表.map((q) => [q.次, q.被选中的id]));
      rec.菜单项口径 = rec.三次.find((q) => q.松手后 && q.松手后.菜单) && rec.三次.find((q) => q.松手后 && q.松手后.菜单).松手后.菜单.项;
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

try { rec.删除 = []; for (const id of ((rec.建 && rec.建.ids) || [])) rec.删除.push(await 删一个(id));
} catch (e) { rec.删除异常 = String(e).slice(0, 300); }
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
  zoom: await R.zoom(), 积分: await R.credits(), 剩余自建: 末.filter((x) => ((rec.建 && rec.建.ids) || []).includes(x)) };
rec.断言全过 = 断言过;
fs.writeFileSync(new URL('./_tmp-b146b.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 起点: rec.起点, 建后: rec.建后, 表: rec.表, 菜单项口径: rec.菜单项口径,
  异常: rec.异常, 删除: rec.删除, 收尾: rec.收尾 }, null, 1));
await b.close();
