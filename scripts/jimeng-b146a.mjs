// 批次 146 a 轮 —— 侦察：能不能复现「从 source 手柄拖到 (140,150) 松手 ⇒ 源节点变选中」这个条件。
//
// 📌 靶子（`10-tasks/connect-nodes.md:104`）：「拖完**源节点变成选中态**（状态行出现
//   `1 selected`），但**节点自身没有被拖走**（canvas 坐标位移实测 `[0,0]`），也没有建出连线。」
//   而 AUDIT 记「**三次未复现**」（三个落点、边数全 0、源节点都没被选中；唯一那次
//   `1 selected` 的那一轮**预览线压根没出现**、被选中的还是**另一个节点**），
//   PROGRESS 明写「要定案得**同落点重测**，本批未做」。
//
// 🔑 批次 72 当年用的是**视频源** + 松手点 **`(140,150)`**。画布上那个视频节点在
//   **视口外**（`video-node-empty` 屏上 `-535,-713`），而**平移会改共享画布视图**（批次 129 明确不做）。
//   ⇒ 本轮**自建一个视频节点**（批次 143 已证：护栏建出的节点落在视口中央）。
//
// ⚠️ 两条纪律：
//   ① **不先选中源节点** —— 批次 91：`.react-flow__handle` 本体 `pointer-events` 永远 `none`，
//      带 `auto` 的是它的 **`::before` 伪元素**（批次 136 实测 `40×80`）。
//   ② **区分两件事**（批次 137 立的认识）：「状态行出现 `1 selected`」≠「**源节点**变成选中态」，
//      必须**逐字读被选中者的 id**。
//
// 本轮只做侦察：落点 `(140,150)` 是否可用、source 热区在哪、拖一次读全部现象。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, canvasPos, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 146, 轮: 'a', 目的: '侦察 (140,150) 松手能否复现「源节点变选中」' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };

// 🔴 a 轮第一版把落点写死 `(140,150)`，实测该点**已被别人的节点占用**
//   （`elementFromPoint(140,150)` 命中 `node_qe1kf9ywek` 内部）—— 共享画布被别人改过。
//   ⇒ **严格意义的「同落点重测」在今天做不到**。本轮改为「**同条件重测**」：
//   当年的机制条件是「**落点是空白**」，`(140,150)` 只是当年那块空白恰好的坐标。
//   于是先扫一块**当下真空白**的落点，并把它**逐字记进证据**，不冒充「同落点」。
let 落点 = null;

/** 落点归属体检：不在任何节点内、不在 dock 内、不是按钮。 */
const 体检落点 = (pt) => p.evaluate((q) => {
  if (!q) return { __err: '未选落点（第一版把落点写死 (140,150)，现已改为扫真空白）' };
  const [x, y] = q;
  const h = document.elementFromPoint(x, y);
  if (!h) return { 命中: 'null（越界或被挡）' };
  const 链 = []; for (let n = h; n && n !== document.body; n = n.parentElement) {
    链.push((String(n.className || '').split(' ')[0] || n.tagName).slice(0, 40)); }
  const nn = h.closest('.react-flow__node');
  return { 命中: h.tagName + '.' + String(h.className || '').split(' ')[0].slice(0, 40),
    是pane: !!(h.classList && h.classList.contains('react-flow__pane')),
    在节点内: !!nn, 所属节点: nn ? nn.getAttribute('data-id') : null,
    在dock内: !!h.closest('nav,aside,[class*=dock],[class*=sidebar]'),
    是按钮: h.tagName === 'BUTTON' || !!h.closest('button,[role=button]'),
    链: 链.slice(0, 6) };
}, pt);

/** 找指定节点的 source 热区（`::before` 伪元素带 pe:auto 的那个）。 */
const 找source = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'not-found' };
  // 🔴 a 轮第一版按 class 查 `.flow-node-source-handle` ⇒ 恒扑空（`no-source-handle`），
  //   而 `节点内testid` 里明明列着它 —— **它是 data-testid，不是 class**。
  const h = n.querySelector('[data-testid="flow-node-source-handle"]');
  if (!h) return { __err: 'no-source-handle', 节点内testid: Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')) };
  const r = h.getBoundingClientRect();
  const cs = getComputedStyle(h);
  const bef = getComputedStyle(h, '::before');
  // 📌 扫描范围**向外扩 24px**，且 `closest` 必须按 **data-testid** 查
  //   （a 轮第二版这里还写着 class 版 `.flow-node-source-handle`，恒扑空 ⇒ 可拖像素 0；
  //    而带 `pointer-events:auto` 的是 `::before`（canvas 40×80），它会溢出手柄盒）
  const 外扩 = 24;
  const 好 = [];
  for (let y = Math.ceil(r.y) - 外扩; y <= r.y + r.height + 外扩 - 1; y += 2)
    for (let x = Math.ceil(r.x) - 外扩; x <= r.x + r.width + 外扩 - 1; x += 2) {
      if (x < 1 || y < 1) continue;
      const e = document.elementFromPoint(x, y);
      if (!e) continue;
      const eh = e.closest('[data-testid="flow-node-source-handle"]');
      if (eh === h) 好.push([x, y]);
    }
  const 盒 = 好.length ? [Math.min(...好.map((q) => q[0])), Math.min(...好.map((q) => q[1])),
    Math.max(...好.map((q) => q[0])) - Math.min(...好.map((q) => q[0])),
    Math.max(...好.map((q) => q[1])) - Math.min(...好.map((q) => q[1]))] : null;
  return { 节点id: i, 节点aria: n.getAttribute('aria-label'),
    手柄屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
    手柄canvas: [h.offsetWidth, h.offsetHeight],
    本体pe: cs.pointerEvents, before背景: bef.backgroundColor, before内容: bef.content,
    before盒: [bef.width, bef.height], beforePe: bef.pointerEvents,
    可拖像素数: 好.length, 可拖盒: 盒, 可拖中心: 好.length ? 好[Math.floor(好.length / 2)] : null };
}, id);

const 读选中 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected'))
  .map((n) => ({ id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
    cls: String(n.className || '').split(' ').slice(0, 3).join(' ') })));

const 读边与菜单 = () => p.evaluate(() => ({
  边数: document.querySelectorAll('.react-flow__edge').length,
  边state: Array.from(document.querySelectorAll('.react-flow__edge')).map((e) => e.getAttribute('data-state')),
  预览线: Array.from(document.querySelectorAll('.react-flow__connection, .react-flow__connectionline, path')).filter((e) => {
    const c = String(e.className || ''); return /connection|preview|draft/i.test(c); }).length,
  菜单: Array.from(document.querySelectorAll('[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1)
    .map((m) => { const r = m.getBoundingClientRect(); return { testid: m.getAttribute('data-testid'),
      role: m.getAttribute('role'), aria: m.getAttribute('aria-label'),
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      逐字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80) }; }),
}));

const 删一个 = async (id) => {
  for (let k = 0; k < 3 && (await selCount(p)) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
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
  // 🔴 **先把缩放归位再开始**：a 轮第一版崩在中途，把画布留在 57%，
  //   第二版的起点就成了 `Zoom options, 57%` ⇒ **基线被自己的残留污染**。
  const 起缩放 = await R.zoom();
  if (起缩放 !== 'Zoom options, 60%') {
    rec.起步归位 = await setZoom(p, 60);
    await p.waitForTimeout(900);
  }
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(),
    积分: await R.credits(), 起步前缩放: 起缩放 };
  rec.落点体检140 = await 体检落点([140, 150]);
  rec.当年落点140 = rec.落点体检140 && rec.落点体检140.在节点内 ? '🔴 已被节点 ' + rec.落点体检140.所属节点 + ' 占用' : '仍空白';
  rec.建前 = await 读边与菜单();

  const 建 = await 建N个(p, '视频', 1, 断言, 76);
  rec.建 = 建;
  const SELF = 建.ids && 建.ids[0];
  if (!SELF) { rec.中止 = '建节点未成'; }
  else {
    await p.waitForTimeout(2000);
    await settle(p, R);
    rec.建后 = { 状态行: await R.status(), zoom: await R.zoom(), 选中: await 读选中() };
    rec.建后位置 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      const r = n.getBoundingClientRect(); return { 屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }, SELF);

    // ⚠️ 生成面板会自动弹出 —— 关掉它（Esc），免得遮住画布
    rec.建后面板 = await R.overlays();
    for (let k = 0; k < 3 && (await R.overlays()) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
    rec.关面板后 = { 浮层: await R.overlays(), 选中: await 读选中(), 状态行: await R.status() };
    // ⚠️ 关面板后实测**仍剩 1 选中** ⇒ Esc 不足以清。
    //   批次 143 i 轮已定案：清选中要**点画布空白**（Esc 只在焦点在画布容器上时才有效）。
    for (let k = 0; k < 3 && (await selCount(p)) > 0; k++) {
      const 空 = await p.evaluate(() => {
        const 坏 = (x, y) => { const h = document.elementFromPoint(x, y);
          if (!h) return 1;
          if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button]')) return 1;
          if (h.closest('.react-flow__node') || h.closest('[data-testid="text-editor-node-overlay"]') || h.closest('.react-flow__node-toolbar')) return 1;
          if (h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
          return !(h.classList && h.classList.contains('react-flow__pane')); };
        for (let y = 90; y < innerHeight - 90; y += 8) for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
        return { __err: 'no-free-pane' };
      });
      if (空.__err) break;
      await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1100);
    }
    rec.拖前 = { 选中: await 读选中(), 选中数: await selCount(p), 边: await 读边与菜单() };
    rec.拖前canvas = (await canvasPos(p))[SELF];

    // 扫一块**当下真空白**的落点（优先靠近当年那块 (140,150) 的区域，便于对照）
    落点 = await p.evaluate(() => {
      const 坏 = (x, y) => { const h = document.elementFromPoint(x, y);
        if (!h) return 1;
        if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button]')) return 1;
        if (h.closest('.react-flow__node') || h.closest('.react-flow__node-toolbar')) return 1;
        if (h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
        return !(h.classList && h.classList.contains('react-flow__pane')); };
      const 候选 = [];
      for (let y = 110; y < 560; y += 10) for (let x = 110; x < 700; x += 10) if (!坏(x, y)) 候选.push([x, y]);
      if (!候选.length) return { __err: 'no-blank-in-region' };
      // 取离当年 (140,150) 最近的那一块
      候选.sort((a, b) => Math.hypot(a[0] - 140, a[1] - 150) - Math.hypot(b[0] - 140, b[1] - 150));
      return { 落点: 候选[0], 区域内空白块数: 候选.length, 距当年落点: Math.round(Math.hypot(候选[0][0] - 140, 候选[0][1] - 150)) };
    });
    rec.落点选取 = 落点;
    if (落点.__err) { rec.中止 = '区域内找不到空白落点'; }
    else { 落点 = 落点.落点; }
    // 🔴 **先把鼠标移到节点上**让手柄进入 hover 态。
    //   手柄未 hover 时不参与命中，a 轮第二/三版都在建完节点后立刻扫 ⇒ `可拖像素数: 0`。
    rec.hover前 = { 鼠标位置: [落点[0], 落点[1]], 节点盒: rec.建后位置 && rec.建后位置.屏上 };
    const nb = rec.建后位置 && rec.建后位置.屏上;
    if (nb) {
      await p.mouse.move(nb[0] + Math.round(nb[2] / 2), nb[1] + Math.round(nb[3] / 2));
      await p.waitForTimeout(1300);
    }
    rec.hover后 = { 选中数: await selCount(p), 状态行: await R.status() };
    const src = await 找source(SELF);
    rec.source = src;
    if (src.__err || !src.可拖中心) { rec.中止 = 'source 热区 ' + (src.__err || '无可拖像素'); }
    else {
      const 起 = src.可拖中心;
      // 每次拖动前重新断言：0 选中、落点归属正确、落点体检通过
      const 前置 = await p.evaluate(([sx, sy, tx, ty, i]) => {
        const h = document.elementFromPoint(sx, sy);
        const hh = h ? h.closest('[data-testid="flow-node-source-handle"]') : null;
        const th = document.elementFromPoint(tx, ty);
        return { 起点在手柄内: !!hh, 起点元素: h ? h.tagName + '.' + String(h.className || '').split(' ')[0].slice(0, 30) : null,
          落点命中: th ? th.tagName + '.' + String(th.className || '').split(' ')[0].slice(0, 30) : null,
          落点在节点内: !!(th && th.closest('.react-flow__node')),
          落点是按钮: !!(th && (th.tagName === 'BUTTON' || th.closest('button,[role=button]'))),
          选中数: document.querySelectorAll('.react-flow__node.selected').length,
          目标仍存在: !!document.querySelector(`.react-flow__node[data-id="${i}"]`) };
      }, [起[0], 起[1], 落点[0], 落点[1], SELF]);
      rec.拖前置 = 前置;
      if (前置.起点在手柄内 && !前置.落点在节点内 && !前置.落点是按钮 && 前置.选中数 === 0) {
        await p.mouse.move(起[0], 起[1]);
        await p.mouse.down();
        for (let i2 = 1; i2 <= 12; i2++) {
          await p.mouse.move(Math.round(起[0] + ((落点[0] - 起[0]) * i2) / 12), Math.round(起[1] + ((落点[1] - 起[1]) * i2) / 12));
          await p.waitForTimeout(35);
        }
        rec.拖中 = await 读边与菜单();
        await p.mouse.up();
        await p.waitForTimeout(1800);
      }
      rec.松手后 = { 选中: await 读选中(), 选中数: await selCount(p), 状态行: await R.status(),
        边与菜单: await 读边与菜单() };
      rec.松手后canvas = (await canvasPos(p))[SELF];
      rec.源节点位移 = [Math.round((rec.松手后canvas[0] - rec.拖前canvas[0]) * 100) / 100,
                       Math.round((rec.松手后canvas[1] - rec.拖前canvas[1]) * 100) / 100];
      断言('① 松手后状态行出现 1 selected', /1 selected/.test(rec.松手后.状态行 || ''), rec.松手后.状态行);
      断言('② 边数仍为 0（没有建出连线）', rec.松手后.边与菜单.边数 === 0, rec.松手后.边与菜单);
      断言('③ 源节点 canvas 零位移', rec.源节点位移[0] === 0 && rec.源节点位移[1] === 0, rec.源节点位移);
      rec.被选中的是谁 = rec.松手后.选中;
      断言('④ 若有选中，被选中的**就是源节点**', rec.松手后.选中.length === 0 || rec.松手后.选中[0].id === SELF,
        { 被选中: rec.松手后.选中, SELF });
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

try { rec.删除 = []; for (const id of ((rec.建 && rec.建.ids) || [])) rec.删除.push(await 删一个(id));
} catch (e) { rec.删除异常 = String(e).slice(0, 300); }

// ⚠️ 建节点会**自动适配缩放**（批次 145 实测落点每次都不同）⇒ 收尾必须归位
rec.归位 = await setZoom(p, 60);
await p.waitForTimeout(900);
const 小地图前 = await R.minimap();
if (!小地图前 || 小地图前.ariaPressed !== 'true') {
  const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3);
  rec.小地图落点 = t;
  if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); }
}
rec.小地图后 = await R.minimap();
await settle(p, R);
const 末 = await idsOf(p);
rec.收尾 = { 状态行: await R.status(), 节点数: 末.length, 选中: await selCount(p), 浮层: await R.overlays(),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length),
  zoom: await R.zoom(), 积分: await R.credits(), 剩余自建: 末.filter((x) => ((rec.建 && rec.建.ids) || []).includes(x)) };
rec.断言全过 = 断言过;
fs.writeFileSync(new URL('./_tmp-b146a.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 起点: rec.起点, 落点体检: rec.落点体检, 建后: rec.建后, 建后位置: rec.建后位置,
  关面板后: rec.关面板后, 拖前: rec.拖前, source: rec.source, 拖前置: rec.拖前置, 拖中: rec.拖中,
  松手后: rec.松手后, 源节点位移: rec.源节点位移, 被选中的是谁: rec.被选中的是谁,
  删除: rec.删除, 收尾: rec.收尾, 异常: rec.异常 }, null, 1));
await b.close();
