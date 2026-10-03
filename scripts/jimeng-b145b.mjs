// 批次 145 b 轮 —— 复测 `image-node-empty`，并验一条**方法论假设**。
//
// 🔑 a 轮三族对照给出：
//   video-node-empty  1 个   屏上 190.8×340.1   canvas 318×567   aria 逐字**只有「暂无视频」四个字**
//   audio-node-empty  68 个  屏上 192×192        canvas 320×320   aria 完整三段式
//   image-node-empty  **0 个**（画布上唯一的图片节点有内容）
//
// ⚠️ 批次 134（2026-10-03）在 20-reference.md 记的 `image-node-empty` 矩形是 **182×182**，
//   而 60% 下同族的 audio 读 **192×192**。`320 × 0.568 = 181.8 ≈ 182` ——
//   而 **0.568 正是批次 134 自己记过的「新建节点会自动把画布从 60% 适配到 57%」**。
//   ⇒ 假设：批次 134 的 `182×182` **不是错的**，只是**它记的矩形是在适配后的缩放下测的，
//     却没有把缩放一并记下来**。同一张 canvas 恒 320 的节点于是给出 `182` 与 `192` 两个读数。
//
// 本轮要验的正是这条：**屏上矩形 = 320 × 实测 scale**，且**必须同时记 scale 才可复现**。
// 📌 与 AUDIT 批次「换算基准写死 0.6 被当成方法写进了手册」同族：
//   **记录矩形必须同时记缩放**，否则两个都对���数无法分辨。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, canvasPos, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 145, 轮: 'b', 目的: '复测 image-node-empty + 验「矩形必须连 scale 一起记」' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };

const 独占像素 = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'not-found' };
  const r = n.getBoundingClientRect(); const 好 = [];
  for (let y = Math.ceil(r.y) + 4; y <= r.y + r.height - 4; y += 2)
    for (let x = Math.ceil(r.x) + 4; x <= r.x + r.width - 4; x += 2) {
      const h = document.elementFromPoint(x, y); if (!h) continue;
      const nn = h.closest('.react-flow__node');
      if (!nn || nn.getAttribute('data-id') !== i) continue;
      if (h.tagName !== 'DIV' || h.closest('.octo-text-node-resize-controls') || h.closest('[contenteditable]')) continue;
      if (/text-octo-ui-copy/.test(String(h.className || ''))) continue;
      好.push([x, y]);
    }
  if (!好.length) return { __err: 'no-exclusive-point' };
  const cx = 好.reduce((a, q) => a + q[0], 0) / 好.length, cy = 好.reduce((a, q) => a + q[1], 0) / 好.length;
  好.sort((u, v) => Math.hypot(u[0] - cx, u[1] - cy) - Math.hypot(v[0] - cx, v[1] - cy));
  return { 总数: 好.length, 落点: 好[0] };
}, id);

const 找真空白 = () => p.evaluate(() => {
  const 坏 = (x, y) => { const h = document.elementFromPoint(x, y);
    if (!h) return 1;
    if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button]')) return 1;
    if (h.closest('.react-flow__node') || h.closest('[data-testid="text-editor-node-overlay"]') || h.closest('.react-flow__node-toolbar')) return 1;
    return !(h.classList && h.classList.contains('react-flow__pane')); };
  for (let y = 90; y < innerHeight - 90; y += 8) for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
  return { __err: 'no-free-pane' };
});

/** 空态全套读数：实测 scale + 屏上盒 + canvas 盒 + aria。 */
const 读空态 = () => p.evaluate(() => {
  // 📌 双通道读 scale：① viewport 的 transform 正则；② 由「屏上 ÷ canvas」自算。
  //   b 轮第一版只有 ①，且那一轮读成了 null（自动适配后 transform 格式与预期不同）⇒ 断言报红。
  //   ② 不依赖任何格式假设，永远可算 —— 它才是**主判据**。
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
  const 正则scale = m ? Math.round(parseFloat(m[1]) * 1000) / 1000 : null;
  const transform原文 = vp ? vp.style.transform : null;
  const e = document.querySelector('[data-testid="image-node-empty"]');
  if (!e) return { 正则scale, transform原文, 空态: null };
  const r = e.getBoundingClientRect();
  const n = e.closest('.react-flow__node');
  const nr = n ? n.getBoundingClientRect() : null;
  const 表单 = document.querySelector('[data-testid="generation-form"]');
  const fr = 表单 ? 表单.getBoundingClientRect() : null;
  return { 正则scale, transform原文,
    空态: { tag: e.tagName, role: e.getAttribute('role'),
      屏上: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
      canvas: [e.offsetWidth, e.offsetHeight],
      aria: e.getAttribute('aria-label'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60),
      cls: String(e.className || '').slice(0, 80),
      节点盒: nr ? [Math.round(nr.width * 10) / 10, Math.round(nr.height * 10) / 10] : null,
      节点aria: n ? n.getAttribute('aria-label') : null,
      img数: n ? n.querySelectorAll('img').length : null },
    节点testid: n ? Array.from(n.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')).sort() : [],
    自动弹出表单: 表单 ? { testid: 'generation-form', 屏上: [Math.round(fr.width * 10) / 10, Math.round(fr.height * 10) / 10],
      canvas: [表单.offsetWidth, 表单.offsetHeight],
      逐字: (表单.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160),
      按钮: Array.from(表单.querySelectorAll('button,[role=button]')).map((b2) => { const q = b2.getBoundingClientRect();
        return { aria: b2.getAttribute('aria-label'), 逐字: (b2.innerText || '').replace(/\s+/g, ' ').trim(),
          盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; }) } : null };
});

const 删一个 = async (id) => {
  for (let k = 0; k < 3 && (await selCount(p)) > 0; k++) { const 空 = await 找真空白(); if (空.__err) break;
    await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1100); }
  const 落 = await 独占像素(id); if (落.__err) return { id, __err: '独占 ' + 落.__err };
  await p.mouse.click(落.落点[0], 落.落点[1]); await p.waitForTimeout(1400);
  const 前 = await idsOf(p);
  const 落2 = await 独占像素(id); if (落2.__err) return { id, __err: '右键前 ' + 落2.__err };
  await p.mouse.click(落2.落点[0], 落2.落点[1], { button: 'right' });
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
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), minimap: await R.minimap() };
  rec.建前 = await 读空态();
  rec.建前testid数 = (await R.testids()).length;

  // 🔴 建**图片**节点 —— 会**自动弹出生成表单**。⚠️ 只读表单，**绝不点「生成」**。
  const 建 = await 建N个(p, '图片', 1, 断言, 76);
  rec.建 = 建;
  const SELF = 建.ids && 建.ids[0];
  if (!SELF) { rec.中止 = '建节点未成'; }
  else {
    await p.waitForTimeout(2000);
    await settle(p, R);
    rec.建后 = await 读空态();
    rec.建后状态 = { 状态行: await R.status(), zoom: await R.zoom(), 选中: await selCount(p) };
    rec.建后testid数 = (await R.testids()).length;

    // ---- 复测断言（对照批次 134 的 20-reference.md:1743）
    const E = rec.建后.空态;
    断言('① image-node-empty 存在且恰好 1 个', !!E, rec.建后);
    if (E) {
      断言('② tag=DIV role=img（批次 134 逐字）', E.tag === 'DIV' && E.role === 'img', E);
      断言('③ aria 逐字以「暂无图片. No resources: 0 ready, 0 processing, 0 failed.」开头',
        /^暂无图片\. No resources: 0 ready, 0 processing, 0 failed\./.test(E.aria || ''), E.aria);
      断言('④ aria 结尾随选中态变化（批次 134 记 Selected.）', /Selected\.$/.test(E.aria || ''), E.aria);
      断言('⑤ 内部 img 元素 0 个（批次 134）', E.img数 === 0, E);
      // 🔑 自算 scale = 屏上 ÷ canvas（不依赖 transform 格式）—— 这才是主判据。
      //
      // 🔴 **判据不能预设具体数值**：b 轮第二版把「上一轮读到的 0.568」写成区间断言，
      //   而本轮建节点后自动适配落到了 **36%**（上轮是 57%）⇒ 断言报红。
      //   这是**批次 142 刚推翻的同一条**：「判据写死一个数量上限 = 把机制提前写进判据」。
      //   ⇒ 断言只判**双通道自洽**，不判「应该是多少」。
      const 自算 = Math.round((E.屏上[0] / E.canvas[0]) * 100000) / 100000;
      const 正则 = rec.建后.正则scale;
      const aria = await R.zoom();
      rec.屏上比 = { 自算scale: 自算, 正则scale: 正则, transform原文: rec.建后.transform原文,
        实测屏上宽: E.屏上[0], canvas宽: E.canvas[0],
        '按正则scale算': Math.round(320 * 正则 * 100) / 100,
        aria, 'aria数值': aria ? parseFloat(String(aria).match(/([\d.]+)%/)[1]) / 100 : null,
        'aria与自算的差': aria ? Math.round((parseFloat(String(aria).match(/([\d.]+)%/)[1]) / 100 - 自算) * 10000) / 10000 : null,
        '批次134记的屏上': 182, '0.568×320': Math.round(320 * 0.568 * 10) / 10 };
      断言('⑥ 双通道自洽：屏上 ÷ canvas == transform 里的 scale（±0.002）',
        正则 !== null && Math.abs(自算 - 正则) <= 0.002, rec.屏上比);
      断言('⑥b 屏上宽 == canvas 320 × 该 scale（±0.1）',
        Math.abs(E.屏上[0] - 320 * 正则) <= 0.1, rec.屏上比);
      断言('⑥c aria 百分比**不等于**实测 scale（四舍五入，只能当约数）',
        rec.屏上比['aria与自算的差'] !== 0 && Math.abs(rec.屏上比['aria与自算的差']) > 0.0001, rec.屏上比);
      rec.自动适配后zoom = aria;
      rec.建前zoom = rec.建后状态 && rec.建后状态.zoom;
      断言('⑦ canvas 恒 320×320', E.canvas[0] === 320 && E.canvas[1] === 320, E.canvas);
      断言('⑦b 新建节点后画布缩放被**自动适配**改掉了（与起点 60% 不同）',
        String(rec.建后状态.zoom) !== 'Zoom options, 60%', { 起: 'Zoom options, 60%', 后: rec.建后状态.zoom });
    }
    const F = rec.建后.自动弹出表单;
    断言('⑧ 新建图片节点自动弹出 generation-form', !!F, rec.建后.自动弹出表单);
    if (F) {
      断言('⑨ generation-form 逐字首段「上传参考图」', /^上传参考图/.test(F.逐字), F.逐字.slice(0, 40));
      rec.表单按钮数 = F.按钮.length;
      rec.表单含生成钮 = F.按钮.some((q) => q.aria === '生成' || q.逐字 === '生成');
      断言('⑩ 表单里有「生成」钮（说明必须格外小心不点它）', rec.表单含生成钮, F.按钮.map((q) => q.aria || q.逐字));
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

try { rec.删除 = []; for (const id of ((rec.建 && rec.建.ids) || [])) rec.删除.push(await 删一个(id));
} catch (e) { rec.删除异常 = String(e).slice(0, 300); }

// ⚠️ 建节点会让画布**自动适配缩放**（批次 134：60% → 57%）⇒ 收尾必须归位
rec.归位 = await setZoom(p, 60);
await p.waitForTimeout(1000);
const 空2 = await 找真空白();
if (!空2.__err) { await p.mouse.click(空2.x, 空2.y); await p.waitForTimeout(1000); }
const 小地图前 = await R.minimap();
if (!小地图前 || 小地图前.ariaPressed !== 'true') {
  const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3);
  rec.小地图落点 = t;
  if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); }
}
await settle(p, R);
const 末 = await idsOf(p);
rec.收尾 = { 状态行: await R.status(), 节点数: 末.length, 组数: await 0, 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), minimap: await R.minimap(), 积分: await R.credits(),
  剩余自建: 末.filter((x) => ((rec.建 && rec.建.ids) || []).includes(x)) };
rec.收尾.组数 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group'))
  .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || '')).length);
rec.建后testid数2 = (await R.testids()).length;
rec.断言全过 = 断言过;
fs.writeFileSync(new URL('./_tmp-b145b.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 中止: rec.中止, 异常: rec.异常, 建后: rec.建后, 建后状态: rec.建后状态,
  屏上比: rec.屏上比, 表单按钮数: rec.表单按钮数, 表单含生成钮: rec.表单含生成钮,
  删除: rec.删除, 归位: rec.归位 && rec.归位.回读, 小地图前: rec.小地图前, 小地图后: await R.minimap(),
  收尾: rec.收尾, testid数: [rec.建前testid数, rec.建后testid数, rec.建后testid数2] }, null, 1));
await b.close();
