// 批次 143 a 轮 —— 纯侦察：**组工具条「背景色」取一个颜色后，组卡片底色到底变没变？**
//
// 🔑 为什么问这个：手册里组侧只记了**色板 DOM 契约**（`organize-group-layout.md:267-297`
//   记了面板 214×40、六枚色块逐字、0/1/2 成员三态相同），**从未验过「取一个颜色后
//   组卡片底色真的变了」这个执行结果**。而节点侧早就有这条（`SOURCE_OBSERVATIONS.md:765`
//   「应用效果实测」：点青绿色 → 卡片底色即时变、工具条按钮图标同步变）。
//   ⇒ **同一套色板，节点侧的执行结果有、组侧没有**，本轮补这条。
//
// 本轮是**侦察轮**，不打算直接出结论：先 dump 出组卡片整棵子树的背景相关样式，
// 搞清楚「底色」究竟画在**哪个元素**上（组卡片 `z-index:-2` 且整卡 `pointer-events:none`，
// 颜色多半不在 `.react-flow__node-group` 本身，而在某个子层）。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard, PORT } from './jimeng-b135-lib.mjs';
import { 建N个, planBoxFor, doBox, 点编组, 点解除编组, selIds, selCount, 组数, idsOf, canvasPos, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 143, 轮: 'a', 目的: '侦察组卡片背景色的承载元素' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };

/** dump 一棵子树的背景相关样式（限制深度，避免展开爆炸）。 */
const DUMP = (maxDepth) => p.evaluate((md) => {
  const box = (e) => { const r = e.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10 }; };
  const 树 = (el, d) => {
    const cs = getComputedStyle(el);
    return { 深度: d, tag: el.tagName, cls: String(el.className || '').slice(0, 100),
      bg: cs.backgroundColor,
      bgi: cs.backgroundImage === 'none' ? 'none' : cs.backgroundImage.slice(0, 70),
      opacity: cs.opacity, outline: cs.outline, borderColor: cs.borderColor,
      盒: [el.offsetWidth, el.offsetHeight], 屏上: box(el),
      子: d >= md ? '…' : Array.from(el.children).map((c) => 树(c, d + 1)) };
  };
  const 组 = Array.from(document.querySelectorAll('.react-flow__node-group'));
  return { 组DOM数: 组DOM数(), 全部: 组.map((g) => ({
    id: g.getAttribute('data-id'),
    是影子: /^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''),
    子树: 树(g, 0) })) };
  function 组DOM数() { return document.querySelectorAll('.react-flow__node-group').length; }
}, maxDepth);

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p), zoom: await R.zoom(),
    minimap: await R.minimap(), 积分: await R.credits() };

  // ---- 建 2 个文本节点
  rec.建 = await 建N个(p, '文本', 2, 断言, 76);
  if (!(rec.建.ids && rec.建.ids.length === 2)) { rec.中止 = '建节点未成'; }
  else {
    // 建后几何 —— 顺带回答批次 142 遗留的「建 N 个节点会不会叠放」
    rec.建后几何 = await p.evaluate((W) => Array.from(document.querySelectorAll('.react-flow__node'))
      .filter((n) => W.includes(n.getAttribute('data-id')))
      .map((n) => { const r = n.getBoundingClientRect();
        return { id: n.getAttribute('data-id'),
          屏上: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
          canvas: { w: n.offsetWidth, h: n.offsetHeight },
          逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16) }; }), rec.建.ids);
    rec.建后状态 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length };

    // ---- 框选这 2 个
    const box = await planBoxFor(p, rec.建.ids);
    rec.框选计划 = box;
    let 选中方式 = null;
    if (box.ok) { rec.框选 = { 命中: await doBox(p, box.矩形), 选中: await selIds(p) }; 选中方式 = '框选'; }
    if (选中方式) {
      断言('③选中集合恰好等于这 2 个', JSON.stringify(await selIds(p)) === JSON.stringify([...rec.建.ids].sort()),
        { 选中方式, 选中: await selIds(p) });
    } else { rec.中止 = '框选找不到安全矩形'; }

    if (!rec.中止) {
      const g = await 点编组(p);
      rec.编组 = g;
      断言('④编组后组卡片恰好 1 个', g.ok, g);

      // ---- 🔑 本轮真正的目标：把组卡片整棵子树的背景样式 dump 出来
      rec.背景前 = await DUMP(6);
    }
  }
} catch (e) {
  rec.异常 = String((e && e.stack) || e).slice(0, 800);
}

// ---- 清理：解组 → 逐个删（右键菜单，不走键盘）
try {
  if ((await 组数(p)) > 0) { rec.解组 = await 点解除编组(p); }
  rec.解组后 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p), 选中: await selIds(p) };
} catch (e) { rec.解组异常 = String(e).slice(0, 200); }

const 基线 = rec.建 && rec.建.ids ? rec.建.ids : [];
try {
  rec.删除 = [];
  for (const id of 基线) {
    // 🔴 批次 139 配方：右键删除前**先清成 0 选中、再单选目标**（多选态下菜单「删除」扫不到像素）
    const 现状 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      return { 在: !!n, 选中: !!(n && n.classList.contains('selected')), 选中数: document.querySelectorAll('.react-flow__node.selected').length }; }, id);
    if (现状.选中数 > 1) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
    if (!(await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      return !!(n && n.classList.contains('selected')); }, id))) {
      const 落 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
      if (落.__err) { rec.删除.push({ id, __err: 'no-point' }); continue; }
      await p.mouse.click(落.x, 落.y);
      await p.waitForTimeout(1200);
    }
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
          const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() };
        }
      return { __err: 'no-point' };
    });
    if (del.__err) { rec.删除.push({ id, __err: del.__err }); continue; }
    await p.mouse.click(del.x, del.y);
    await p.waitForTimeout(2500);
    await settle(p, R);
    const 后 = await idsOf(p);
    rec.删除.push({ id, 消失: 前.filter((x) => !后.includes(x)), 新增: 后.filter((x) => !前.includes(x)) });
  }
} catch (e) { rec.删除异常 = String(e).slice(0, 300); }

await settle(p, R);
const 末 = await idsOf(p);
rec.收尾 = { 状态行: await R.status(), 节点数: 末.length, 组数: await 组数(p), 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), minimap: await R.minimap(), 积分: await R.credits(),
  剩余自建: 末.filter((x) => 基线.includes(x)) };
rec.断言全过 = 断言过;
fs.writeFileSync(new URL('./_tmp-b143a.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log('\n===== 收尾 =====\n' + JSON.stringify(rec.收尾, null, 1));
await b.close();
