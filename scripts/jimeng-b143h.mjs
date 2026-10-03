// 批次 143 h 轮 —— 拍**正式入库截图**：组卡片已取色 + 工具条色板展开。
//
// 目的：一张图同时说清三件事
//   ① 组卡片底色**确实变了**（与「无颜色」态对照）；
//   ② 所选颜色**只染组卡片，不染成员节点**（截图里两个文本节点仍是原色）；
//   ③ 组工具条「背景色」按钮的 swatch 同步变成所选色、色板里当前项高亮。
//
// 取「紫色」：在 16% 叠加下深紫与深灰的色相差最容易被肉眼分辨。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, 点编组, 点解除编组, selIds, selCount, 组数, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 143, 轮: 'h', 目的: '正式入库截图' };
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);

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

const 删一个 = async (id) => {
  for (let k = 0; k < 3 && (await selCount(p)) > 0; k++) { const 空 = await 找真空白(); if (空.__err) break;
    await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1100); }
  const 落 = await 独占像素(id); if (落.__err) return { id, __err: '独占 ' + 落.__err };
  await p.mouse.click(落.落点[0], 落.落点[1]); await p.waitForTimeout(1200);
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
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom() };
  const 建 = await 建N个(p, '文本', 2, null, 76);
  rec.建 = 建;
  if (!(建.ids && 建.ids.length === 2)) { rec.中止 = '建节点未成'; }
  else {
    const [A, B] = 建.ids;
    const nA = (await 独占像素(A)).总数, nB = (await 独占像素(B)).总数;
    const 先点 = nB >= nA ? B : A, 后点 = 先点 === A ? B : A;
    const 落1 = await 独占像素(先点);
    await p.mouse.click(落1.落点[0], 落1.落点[1]); await p.waitForTimeout(1300);
    const 落2 = await 独占像素(后点);
    await p.keyboard.down('Shift'); await p.mouse.click(落2.落点[0], 落2.落点[1]); await p.keyboard.up('Shift');
    await p.waitForTimeout(1300);
    rec.选中判定 = { 恰好: JSON.stringify(await selIds(p)) === JSON.stringify([...建.ids].sort()) };
    if (!rec.选中判定.恰好) { rec.中止 = 'Shift 加选失败'; }
    else {
      rec.编组 = await 点编组(p);
      // 取「紫色」
      const 落 = await 可点落点(p, '[data-toolbar-value="group-color"]', 3, 3);
      await p.mouse.click(落.x, 落.y); await p.waitForTimeout(1500);
      const 紫 = await p.evaluate(() => {
        const 菜单 = Array.from(document.querySelectorAll('[role=menu]')).find((m) => m.getBoundingClientRect().width > 1);
        // ⚠️ 色块**没有 aria-label**，逐字只在 innerText 里（g 轮踩过一次）
        const e = Array.from(菜单.querySelectorAll('[role=menuitemradio]'))
          .find((s) => (s.getAttribute('aria-label') || s.innerText || '').replace(/\s+/g, ' ').trim() === '紫色');
        if (!e) return { __err: '色板里没有紫色' };
        const r = e.getBoundingClientRect(); return { x: Math.round(r.x + 14), y: Math.round(r.y + 14) };
      });
      if (紫.__err) { rec.中止 = 紫.__err; } else {
      await p.mouse.click(紫.x, 紫.y); await p.waitForTimeout(2200); await settle(p, R);
      rec.取色后 = { 状态行: await R.status(),
        底: await p.evaluate(() => { const e = document.querySelector('[data-testid="group-background"]'); const c = getComputedStyle(e);
          return { 背景: c.backgroundColor, before: getComputedStyle(e, '::before').backgroundColor, beforeOpacity: getComputedStyle(e, '::before').opacity }; }),
        swatch: await p.evaluate(() => { const s = document.querySelector('[data-toolbar-value="group-color"] .size-canvas-color-choice-trigger-swatch'); return s ? getComputedStyle(s).backgroundColor : null; }) };

      // 再把色板**重新打开**（停在紫色已选中态），让截图同时含底色与色板
      const 落2 = await 可点落点(p, '[data-toolbar-value="group-color"]', 3, 3);
      await p.mouse.click(落2.x, 落2.y); await p.waitForTimeout(1600);
      rec.色板开着 = await p.evaluate(() => Array.from(document.querySelectorAll('[role=menu]')).filter((m) => m.getBoundingClientRect().width > 1).length);
      rec.色板态 = await p.evaluate(() => { const 菜单 = Array.from(document.querySelectorAll('[role=menu]')).find((m) => m.getBoundingClientRect().width > 1);
        return 菜单 ? Array.from(菜单.querySelectorAll('[role=menuitemradio]')).map((e) => (e.getAttribute('aria-label') || '') + '=' + e.getAttribute('aria-checked')).join(' ') : '(无)'; });
      // 鼠标移开，避免 hover 态干扰；只移出组卡片，不移出视口（工具条会消失吗？工具条在选中态常驻）
      await p.mouse.move(1150, 700); await p.waitForTimeout(600);
      rec.图前浮层 = await R.overlays();
      rec.图前状态 = { 状态行: await R.status(), 浮层: await R.overlays() };
      const f = new URL('./52-group-background-applied.png', 出图);
      await p.screenshot({ path: f.pathname });
      rec.截图 = 'screenshots/52-group-background-applied.png';
      }
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

try { if ((await 组数(p)) > 0) rec.解组 = await 点解除编组(p);
  rec.删除 = []; for (const id of ((rec.建 && rec.建.ids) || [])) rec.删除.push(await 删一个(id));
} catch (e) { rec.删除异常 = String(e).slice(0, 300); }

await settle(p, R);
const 末 = await idsOf(p);
rec.收尾 = { 状态行: await R.status(), 节点数: 末.length, 组数: await 组数(p), 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits(),
  剩余自建: 末.filter((x) => ((rec.建 && rec.建.ids) || []).includes(x)) };
fs.writeFileSync(new URL('./_tmp-b143h.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 中止: rec.中止, 异常: rec.异常, 选中判定: rec.选中判定, 取色后: rec.取色后,
  色板开着: rec.色板开着, 色板态: rec.色板态, 图前状态: rec.图前状态, 截图: rec.截图, 解组: rec.解组 && rec.解组.ok,
  删除: rec.删除, 收尾: rec.收尾 }, null, 1));
await b.close();
