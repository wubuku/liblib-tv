// 批次 143 e 轮 —— 正题：**组工具条「背景色」取一个颜色后，组卡片底色到底变没变？**
//
// 📌 手册现状：组侧只记了**色板 DOM 契约**（`organize-group-layout.md:267-297`：
//   面板 214×40、六枚 28×28 色块逐字、0/1/2 成员三态相同），
//   **从未验过「取一个颜色后组卡片底色真的变了」这个执行结果**。
//   而节点侧早就有（`SOURCE_OBSERVATIONS.md:765`）：点青绿色 → 卡片底色即时变、
//   工具条按钮图标同步变。⇒ 同一套色板，**节点侧的执行结果有、组侧没有**，本轮补这条。
//
// 🔑 取色链的前置（d 轮验通）：叠放下**框选必失败**，必须走
//   「点上层独占像素单选 → Shift 加选下层 → 编组」。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, 点编组, 点解除编组, selIds, selCount, 组数, idsOf, canvasPos, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 143, 轮: 'e', 目的: '组背景色的应用效果' };

/** 节点内「独占可点像素」—— 点它必定命中该节点。 */
const 独占像素 = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'not-found' };
  const r = n.getBoundingClientRect();
  const 好 = [];
  for (let y = Math.ceil(r.y) + 4; y <= r.y + r.height - 4; y += 2)
    for (let x = Math.ceil(r.x) + 4; x <= r.x + r.width - 4; x += 2) {
      const h = document.elementFromPoint(x, y);
      if (!h) continue;
      const nn = h.closest('.react-flow__node');
      if (!nn || nn.getAttribute('data-id') !== i) continue;
      if (h.tagName !== 'DIV' || h.closest('.octo-text-node-resize-controls') || h.closest('[contenteditable]')) continue;
      if (/text-octo-ui-copy/.test(String(h.className || ''))) continue;
      好.push([x, y]);
    }
  if (!好.length) return { __err: 'no-exclusive-point' };
  const cx = 好.reduce((a, q) => a + q[0], 0) / 好.length;
  const cy = 好.reduce((a, q) => a + q[1], 0) / 好.length;
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

/**
 * 🔑 读组卡片的**全部着色载体**。
 * 组卡片 `z-index:-2`、未选中态整卡 `pointer-events:none`、中心被自己的 `DIV.absolute` 占着
 * ⇒ 颜色**不可能**画在 `.react-flow__node-group` 本身。必须整棵子树扫，
 * 且只保留「真的带了颜色」的元素（`rgba(0,0,0,0)` 的 96% 是噪声）。
 */
const 读着色 = () => p.evaluate(() => {
  const out = [];
  for (const g of document.querySelectorAll('.react-flow__node-group')) {
    const id = g.getAttribute('data-id') || '';
    const 是影子 = /^__group-resize-chrome__/.test(id);
    const 记 = (el, 路径) => {
      const cs = getComputedStyle(el);
      const 透明 = cs.backgroundColor === 'rgba(0, 0, 0, 0)' || cs.backgroundColor === 'transparent';
      if (!透明 || cs.backgroundImage !== 'none') {
        out.push({ 组: 是影子 ? '影子' : '真身', 路径, tag: el.tagName,
          cls: String(el.className || '').slice(0, 90),
          testid: el.getAttribute('data-testid'),
          bg: cs.backgroundColor,
          bgi: cs.backgroundImage === 'none' ? 'none' : cs.backgroundImage.slice(0, 90),
          outline: cs.outlineStyle === 'none' ? 'none' : cs.outlineColor + ' ' + cs.outlineWidth,
          box: (() => { const r = el.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]; })() });
      }
    };
    const 走 = (el, 路径, d) => {
      记(el, 路径);
      if (d >= 8) return;
      Array.from(el.children).forEach((c, i) => 走(c, 路径 + '>' + c.tagName + '[' + i + ']', d + 1));
    };
    走(g, 'GROUP', 0);
  }
  return out;
});

/** 组工具条上「背景色」按钮的当前视觉（图标/类名/内联样式）。 */
const 读背景色按钮 = () => p.evaluate(() => {
  const b = document.querySelector('[data-toolbar-value="group-color"]');
  if (!b) return { __err: 'not-found' };
  const cs = getComputedStyle(b);
  const 内 = Array.from(b.querySelectorAll('*')).map((e) => { const c2 = getComputedStyle(e);
    return { tag: e.tagName, cls: String(e.className || '').slice(0, 40), bg: c2.backgroundColor }; });
  return { 逐字: (b.innerText || '').replace(/\s+/g, ' ').trim(), aria: b.getAttribute('aria-label'),
    dataState: b.getAttribute('data-state'), ariaPressed: b.getAttribute('aria-pressed'),
    cls: String(b.className || '').slice(0, 120), bg: cs.backgroundColor, 子元素: 内 };
});

/** 展开色板并返回 6 枚色块的逐字 + 各自可点落点。 */
const 开色板 = async () => {
  const 落 = await 可点落点(p, '[data-toolbar-value="group-color"]', 3, 3);
  if (落.__err) return { __err: '按钮 ' + 落.__err };
  const 前置 = await p.evaluate(() => ({
    浮层: Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length,
    组真身选中: Array.from(document.querySelectorAll('.react-flow__node-group'))
      .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || '')).filter((g) => g.classList.contains('selected')).length }));
  if (前置.浮层 > 0 || 前置.组真身选中 < 1) return { __err: '前置不满足', 前置 };
  await p.mouse.click(落.x, 落.y);
  await p.waitForTimeout(1500);
  const 板 = await p.evaluate(() => {
    const 菜单 = Array.from(document.querySelectorAll('[role=menu]')).find((m) => m.getBoundingClientRect().width > 1);
    if (!菜单) return { __err: 'no-menu' };
    const r = 菜单.getBoundingClientRect();
    const 项 = Array.from(菜单.querySelectorAll('[role=menuitemradio]')).map((e) => { const q = e.getBoundingClientRect();
      return { 逐字: (e.getAttribute('aria-label') || e.innerText || '').replace(/\s+/g, ' ').trim(),
        盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
        选中态: e.getAttribute('aria-checked'), cls: String(e.className || '').slice(0, 80) }; });
    return { 面板盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 项数: 项.length, 项 };
  });
  return { 落, 前置, 板 };
};

const 删一个 = async (id) => {
  for (let k = 0; k < 3 && (await selCount(p)) > 0; k++) {
    const 空 = await 找真空白(); if (空.__err) break;
    const 是控件 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y);
      return h ? (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button]') ? 1 : 0) : -1; }, [空.x, 空.y]);
    if (是控件 !== 0) break;
    await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1100);
  }
  const 落 = await 独占像素(id);
  if (落.__err) return { id, __err: '独占 ' + 落.__err };
  await p.mouse.click(落.落点[0], 落.落点[1]); await p.waitForTimeout(1200);
  const 前 = await idsOf(p);
  const 落2 = await 独占像素(id);
  if (落2.__err) return { id, __err: '右键前独占 ' + 落2.__err };
  await p.mouse.click(落2.落点[0], 落2.落点[1], { button: 'right' });
  await p.waitForTimeout(1800);
  const del = await p.evaluate(() => {
    const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
      .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
    if (!els.length) return { __err: 'no-delete-item' };
    const e = els[0]; const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
      for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
        const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() };
      }
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
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom() };

  const 建 = await 建N个(p, '文本', 2, null, 76);
  rec.建 = 建;
  if (!(建.ids && 建.ids.length === 2)) { rec.中止 = '建节点未成'; }
  else {
    const [A, B] = 建.ids;
    rec.独占 = Object.fromEntries(建.ids.map((i) => [i, 0]));
    for (const id of 建.ids) rec.独占[id] = (await 独占像素(id)).总数;
    const 先点 = rec.独占[B] >= rec.独占[A] ? B : A, 后点 = 先点 === A ? B : A;
    const 落1 = await 独占像素(先点);
    await p.mouse.click(落1.落点[0], 落1.落点[1]); await p.waitForTimeout(1300);
    const 落2 = await 独占像素(后点);
    await p.keyboard.down('Shift');
    await p.mouse.click(落2.落点[0], 落2.落点[1]);
    await p.keyboard.up('Shift');
    await p.waitForTimeout(1300);
    rec.选中判定 = { 期望: [...建.ids].sort(), 实际: await selIds(p), 恰好: JSON.stringify(await selIds(p)) === JSON.stringify([...建.ids].sort()) };
    if (!rec.选中判定.恰好) { rec.中止 = 'Shift 加选失败'; }
    else {
      rec.编组 = await 点编组(p);
      rec.编组后 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p), 选中: await selIds(p) };

      // ---- 🔑 before
      rec.before = { 着色: await 读着色(), 按钮: await 读背景色按钮() };
      rec.before.着色数 = rec.before.着色.length;
      if (rec.before.着色数 === 0) rec.空集风险 = '🔴 before 着色读数为空，后面所有 diff 都会假绿';

      // ---- 展开色板
      const 板 = await 开色板();
      rec.色板 = 板;
      if (板.板 && !板.板.__err && 板.板.项数 > 0) {
        const 青 = 板.板.项.find((q) => q.逐字 === '青绿色');
        rec.青绿项 = 青;
        // 每次点击前重新断言：色板还开着、目标色块逐字命中、落点归属正确
        const 前置 = await p.evaluate(([x, y, 逐字]) => {
          const h = document.elementFromPoint(x, y);
          const m = h ? h.closest('[role=menuitemradio]') : null;
          return { 逐字命中: !!m && (m.getAttribute('aria-label') || m.innerText || '').replace(/\s+/g, ' ').trim() === 逐字,
            在同一菜单: !!m, 菜单数: Array.from(document.querySelectorAll('[role=menu]')).filter((s) => s.getBoundingClientRect().width > 1).length };
        }, [青.盒[0] + 14, 青.盒[1] + 14, '青绿色']);
        rec.点色块前 = 前置;
        if (前置.逐字命中 && 前置.在同一菜单) {
          await p.mouse.click(青.盒[0] + 14, 青.盒[1] + 14);
          await p.waitForTimeout(2000);
          await settle(p, R);
        }
        rec.after = { 着色: await 读着色(), 按钮: await 读背景色按钮(), 状态行: await R.status() };
        rec.after.着色数 = rec.after.着色.length;
        rec.diff = { 新增: rec.after.着色.filter((q) => !rec.before.着色.some((w) => JSON.stringify(w) === JSON.stringify(q))),
          消失: rec.before.着色.filter((q) => !rec.after.着色.some((w) => JSON.stringify(w) === JSON.stringify(q))) };
      }

      // ---- 复原：再开色板点「无颜色」
      const 板2 = await 开色板();
      rec.色板2 = 板2.板;
      if (板2.板 && !板2.板.__err && 板2.板.项数 > 0) {
        const 无 = 板2.板.项.find((q) => q.逐字 === '无颜色');
        const 前置 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y);
          const m = h ? h.closest('[role=menuitemradio]') : null;
          return { 逐字: m ? (m.getAttribute('aria-label') || m.innerText || '').replace(/\s+/g, ' ').trim() : null }; }, [无.盒[0] + 14, 无.盒[1] + 14]);
        rec.点复原前 = 前置;
        if (前置.逐字 === '无颜色') { await p.mouse.click(无.盒[0] + 14, 无.盒[1] + 14); await p.waitForTimeout(2000); await settle(p, R); }
        rec.restored = { 着色: await 读着色(), 按钮: await 读背景色按钮() };
        rec.复原diff = { 与before相同: JSON.stringify(rec.restored.着色) === JSON.stringify(rec.before.着色) };
      }
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

// ---- 清理
try {
  if ((await 组数(p)) > 0) rec.解组 = await 点解除编组(p);
  rec.删除 = [];
  for (const id of ((rec.建 && rec.建.ids) || [])) rec.删除.push(await 删一个(id));
} catch (e) { rec.删除异常 = String(e).slice(0, 300); }

await settle(p, R);
const 末 = await idsOf(p);
rec.收尾 = { 状态行: await R.status(), 节点数: 末.length, 组数: await 组数(p), 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits(),
  剩余自建: 末.filter((x) => ((rec.建 && rec.建.ids) || []).includes(x)) };
fs.writeFileSync(new URL('./_tmp-b143e.json', import.meta.url), JSON.stringify(rec, null, 1));
const 摘 = (t) => (rec[t] === undefined ? '(缺)' : rec[t]);
console.log(JSON.stringify({ 中止: rec.中止, 异常: rec.异常, 选中判定: rec.选中判定, 编组后: rec.编组后,
  空集风险: rec.空集风险,
  before着色数: rec.before && rec.before.着色数, after着色数: rec.after && rec.after.着色数,
  按钮前: rec.before && rec.before.按钮, 按钮后: rec.after && rec.after.按钮,
  diff: rec.diff, 复原diff: rec.复原diff, 收尾: rec.收尾, 摘: 摘('中止') }, null, 1));
await b.close();
