// 批次 143 f 轮 —— 定案：「青绿色」点下去，组卡片底色为什么是 `rgb(13,13,13)` 而不是 `rgb(0,202,224)`？
//
// 🔴 e 轮实测出一个**自相矛盾**（两条都成立，不是读数错）：
//   · 工具条「背景色」按钮的 swatch：`rgb(51,51,51)` → **`rgb(0, 202, 224)`**（青绿，确实生效了）
//   · 组卡片 `[data-testid="group-background"]`：`rgb(38,38,38)` → **`rgb(13,13,13)`**
//     —— 三通道相等的深灰，**一点青绿成分都没有**，而且比原色**更深**。
//   色板 6 项逐字与 `aria-checked` 全对、点击前置（逐字命中/同一菜单/菜单数 1）全过。
//
// 本轮两件事：
//   ① **五种颜色逐个点**，看 `group-background` 各自得到什么值 —— 判断「合成」还是「无关的第三值」；
//   ② 读 `group-background` 的 **inline style / CSS 自定义属性 / opacity / filter / mix-blend-mode**，
//      定位这个字面值是从哪来的。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, 点编组, 点解除编组, selIds, selCount, 组数, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 143, 轮: 'f', 目的: '定案 group-background 的真实着色机制' };
const 五色 = ['无颜色', '青绿色', '靛蓝色', '紫色', '橙色', '黄色'];

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

/** 🔑 读 `group-background` 的**完整**着色上下文。 */
const 读组背景 = () => p.evaluate(() => {
  const el = document.querySelector('.react-flow__node-group [data-testid="group-background"]');
  if (!el) return { __err: 'not-found' };
  const cs = getComputedStyle(el);
  const 变量 = {};
  for (let i = 0; i < cs.length; i++) { const k = cs[i];
    if (k.startsWith('--') && /color|background|group|fill|brand/i.test(k)) { const v = cs.getPropertyValue(k).trim(); if (v) 变量[k] = v; } }
  return {
    tag: el.tagName, testid: el.getAttribute('data-testid'),
    class完整: String(el.className || ''),
    inlineStyle: el.getAttribute('style'),
    outerHTML: el.outerHTML.slice(0, 600),
    背景: cs.backgroundColor, 背景图: cs.backgroundImage === 'none' ? 'none' : cs.backgroundImage,
    不透明度: cs.opacity, 滤镜: cs.filter, 混合模式: cs.mixBlendMode, 背景混合: cs.backgroundBlendMode,
    背景滤镜: cs.backdropFilter === 'none' ? 'none' : cs.backdropFilter,
    z: cs.zIndex, 混合: cs.isolation,
    父: { tag: el.parentElement.tagName, class完整: String(el.parentElement.className || ''), style: el.parentElement.getAttribute('style'), testid: el.parentElement.getAttribute('data-testid') },
    组根style: (() => { const g = document.querySelector('.react-flow__node-group'); return g ? g.getAttribute('style') : null; })(),
    变量,
  };
});

const 读按钮swatch = () => p.evaluate(() => {
  const s = document.querySelector('[data-toolbar-value="group-color"] .size-canvas-color-choice-trigger-swatch');
  return s ? getComputedStyle(s).backgroundColor : '(无 swatch)';
});

const 取色 = async (逐字) => {
  const 落 = await 可点落点(p, '[data-toolbar-value="group-color"]', 3, 3);
  if (落.__err) return { __err: '按钮 ' + 落.__err };
  await p.mouse.click(落.x, 落.y);
  await p.waitForTimeout(1500);
  const 项 = await p.evaluate(() => {
    const 菜单 = Array.from(document.querySelectorAll('[role=menu]')).find((m) => m.getBoundingClientRect().width > 1);
    if (!菜单) return { __err: 'no-menu' };
    return Array.from(菜单.querySelectorAll('[role=menuitemradio]')).map((e) => { const q = e.getBoundingClientRect();
      return { 逐字: (e.getAttribute('aria-label') || e.innerText || '').replace(/\s+/g, ' ').trim(),
        盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
        checked: e.getAttribute('aria-checked'),
        内芯: (() => { const c = e.querySelector('.size-canvas-color-choice-swatch'); return c ? getComputedStyle(c).backgroundColor : null; })() }; });
  });
  if (项.__err) return 项;
  const 目标 = 项.find((q) => q.逐字 === 逐字);
  if (!目标) return { __err: '色板里没有 ' + 逐字, 项逐字: 项.map((q) => q.逐字) };
  const 前置 = await p.evaluate(([x, y, t]) => { const h = document.elementFromPoint(x, y);
    const m = h ? h.closest('[role=menuitemradio]') : null;
    return { 逐字命中: !!m && (m.getAttribute('aria-label') || m.innerText || '').replace(/\s+/g, ' ').trim() === t, 菜单数: Array.from(document.querySelectorAll('[role=menu]')).filter((s) => s.getBoundingClientRect().width > 1).length }; },
    [目标.盒[0] + 14, 目标.盒[1] + 14, 逐字]);
  if (!前置.逐字命中) return { __err: '落点归属不符', 前置 };
  await p.mouse.click(目标.盒[0] + 14, 目标.盒[1] + 14);
  await p.waitForTimeout(2000);
  await settle(p, R);
  return { 目标: { 逐字: 目标.逐字, checked: 目标.checked, 内芯: 目标.内芯 }, 前置, 之后: await 读组背景(), 之后swatch: await 读按钮swatch(),
    之后板选中: await p.evaluate(() => { const 菜单 = Array.from(document.querySelectorAll('[role=menu]')).find((m) => m.getBoundingClientRect().width > 1);
      if (!菜单) return '(色板已关)';
      return Array.from(菜单.querySelectorAll('[role=menuitemradio]')).map((e) => (e.getAttribute('aria-label') || e.innerText || '').replace(/\s+/g, ' ').trim() + '=' + e.getAttribute('aria-checked')).join(' '); }) };
};

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
    rec.选中判定 = { 恰好: JSON.stringify(await selIds(p)) === JSON.stringify([...建.ids].sort()), 实际: await selIds(p) };
    if (!rec.选中判定.恰好) { rec.中止 = 'Shift 加选失败'; }
    else {
      rec.编组 = await 点编组(p);
      rec.组背景基准 = await 读组背景();
      rec.基准swatch = await 读按钮swatch();
      rec.逐色 = [];
      for (const c of 五色) {
        const r = await 取色(c);
        rec.逐色.push({ 色: c, 结果: r && r.__err ? r : {
          板内态: r.目标, 前置: r.前置, 组背景: r.之后.背景, 组背景完整: r.之后,
          swatch: r.之后swatch, 之后板选中: r.之后板选中 } });
        if (r && r.__err) break;
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
  浮层: await R.overlays(), zoom: await R.zoom(), 剩余自建: 末.filter((x) => ((rec.建 && rec.建.ids) || []).includes(x)) };
fs.writeFileSync(new URL('./_tmp-b143f.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 基准: rec.组背景基准 && { 背景: rec.组背景基准.背景, inline: rec.组背景基准.inlineStyle, 变量: rec.组背景基准.变量, 组根style: rec.组背景基准.组根style },
  基准swatch: rec.基准swatch,
  逐色: (rec.逐色 || []).map((q) => ({ 色: q.色, 背景: q.结果 && q.结果.组背景, swatch: q.结果 && q.结果.swatch, 板内态: q.结果 && q.结果.板内态, 之后板选中: q.结果 && q.结果.之后板选中, err: q.结果 && q.结果.__err })),
  收尾: rec.收尾, 异常: rec.异常 }, null, 1));
await b.close();
