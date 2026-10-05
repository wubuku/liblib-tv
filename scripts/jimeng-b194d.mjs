// 批次 194 d 轮：① 验批次 190 的另一条读数（「右键要落在标题行上」—— 本轮 c 轮在 **50%** 档
// 右键**正文区**读到的是 **7 项菜单**，而 190 在 **26%** 档读到 0 项 ⇒ 逐档对照，看它是缩放问题
// 还是坐标问题；② 拍四张图给 `edit-text-node.md`（11622 字 6 图，现为全册第二干）。
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const SHOTS = 'docs/user-manual/jimeng-canvas/screenshots';
const TID = 'node_5gftn3dnt1';   // 文本 3
const OUT = '/tmp/b194d.json';
const 记 = { 轮次: 'b194d', 正文区右键逐档: [], 图: {}, 收尾: null };
const save = () => fs.writeFileSync(OUT, JSON.stringify(记, null, 1));
const 认线型 = ['solid', 'dashed', 'dotted', 'double'];

const 清选中 = async (p) => {
  const 空 = await p.evaluate(() => { const ns = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
    for (let y = 100; y < innerHeight - 100; y += 15) for (let x = 330; x < innerWidth - 350; x += 15) {
      const h = document.elementFromPoint(x, y);
      if (h && h.classList && h.classList.contains('react-flow__pane') && !ns.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y]; }
    return null; });
  if (空) { await p.mouse.click(空[0], 空[1]); await p.waitForTimeout(900); }
};
const 几何 = (p) => p.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
  const r = n.getBoundingClientRect();
  const t = n.querySelector('[data-testid="flow-node-title"]');
  const tr = t ? t.getBoundingClientRect() : null;
  // ⚠️ 两条工具条是**两个不同 testid**：选中态是 `node-toolbar`（手册记 2 个实例），
  //   编辑态才是 `text-editor-toolbar`。第一版只找后者，**在选中态读到 null 直接崩**。
  //   两条都读出来、由调用方按状态挑，避免再犯（立规 67 的同族：别从一个 testid 顺推另一个）。
  const 盒 = (e) => { if (!e) return null; const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height]; };
  const 编辑态工具条 = 盒(document.querySelector('[data-testid="text-editor-toolbar"]'));
  const 所有nodeToolbar = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
    .sort((a, b) => { const x = a.getBoundingClientRect(), y = b.getBoundingClientRect();
      return (y.width * y.height) - (x.width * x.height); });
  return { 节点: [r.x, r.y, r.width, r.height], 标题行: tr ? [tr.x, tr.y, tr.width, tr.height] : null,
    编辑态工具条, 选中态工具条: 盒(所有nodeToolbar[0]), nodeToolbar实例数: 所有nodeToolbar.length,
    工具条: 编辑态工具条 || 盒(所有nodeToolbar[0]),
    正文中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
    标题中心: tr ? [Math.round(tr.x + tr.width / 2), Math.round(tr.y + tr.height / 2)] : null,
    完整在视口内: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight };
}, TID);
const 画框 = (p, 规格) => p.evaluate((spec) => {
  for (const e of Array.from(document.querySelectorAll('[data-b194]'))) e.remove();
  spec.forEach((s) => { const d = document.createElement('div'); d.id = s.id; d.setAttribute('data-b194', '1');
    d.style.cssText = `position:fixed;left:${Math.round(s.x)}px;top:${Math.round(s.y)}px;width:${Math.round(s.w)}px;height:${Math.round(s.h)}px;` +
      `border:3px ${s.线型 || 'solid'} #ff8c00;border-radius:6px;pointer-events:none;z-index:2147483000;`; document.body.appendChild(d); });
  const 一 = (id) => { const e = document.getElementById(id); if (!e) return null; const cs = getComputedStyle(e); const r = e.getBoundingClientRect();
    return { 宽: Math.round(r.width), 高: Math.round(r.height), borderStyle: cs.borderStyle, borderColor: cs.borderColor, pointerEvents: cs.pointerEvents }; };
  return Object.fromEntries(spec.map((s) => [s.id, 一(s.id)]));
}, 规格);
const 守卫 = (读, n) => { const 键 = Object.keys(读); const 每 = 键.map((k) => 读[k]);
  return { 框数对: 键.length === n, 全非空: 每.every((x) => x && x.宽 > 2 && x.高 > 2),
    线型都被认: 每.every((x) => x && 认线型.includes(x.borderStyle)),
    颜色都对: 每.every((x) => x && x.borderColor === 'rgb(255, 140, 0)'),
    pointerEvents都为none: 每.every((x) => x && x.pointerEvents === 'none') }; };
const 清框 = (p) => p.evaluate(() => { for (const e of Array.from(document.querySelectorAll('[data-b194]'))) e.remove(); });

const { b, p } = await openCanvas();
const R = readers(p);
await pinViewport(p);
await settle(p, R);
const 基线 = { ids: await R.ids(), credits: await R.credits() };

// ① 正文区右键 —— 26% / 50% / 100% 三档
for (const z of [26, 50, 100]) {
  await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  await setZoom(p, z); await p.waitForTimeout(700);
  await 清选中(p);
  const G = await 几何(p);
  if (!G || !G.完整在视口内) { 记.正文区右键逐档.push({ 缩放: z, 无效: true, 原因: '节点不在视口内' }); save(); continue; }
  await p.mouse.click(G.正文中心[0], G.正文中心[1], { button: 'right' });
  await p.waitForTimeout(900);
  const n = await p.evaluate(() => document.querySelectorAll('[role=menuitem]').length);
  const 命中 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y);
    return h ? h.tagName + '[' + (h.getAttribute('data-testid') || String(h.className || '').split(' ')[0]) + ']' : null; }, G.正文中心);
  记.正文区右键逐档.push({ 缩放: z, 节点屏上: G.节点.map(Math.round), 正文中心: G.正文中心,
    落点命中: 命中, 菜单项数: n, 阳性守卫: { 通过: n > 0, 判据: `菜单项数 = ${n}` }, 有效: n > 0 });
  console.log(`缩放 ${z}%：正文中心 ${G.正文中心} 命中 ${命中} ⇒ 菜单 ${n} 项`);
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  save();
}

// ② 四张图：先回到 50%（节点够大、图里有信息量）
await p.keyboard.press('Escape'); await p.waitForTimeout(500);
await setZoom(p, 50); await p.waitForTimeout(800);
await 清选中(p);
{
  // 185 选中态
  const G = await 几何(p);
  await p.mouse.click(G.标题中心[0], G.标题中心[1]); await p.waitForTimeout(1100);
  const 断言 = { 选中数: await R.selCount() };
  const G2 = await 几何(p);
  const 工具条 = G2.工具条;
  const 规格 = [
    { id: '__b194-node', x: G2.节点[0] - 10, y: G2.节点[1] - 10, w: G2.节点[2] + 20, h: G2.节点[3] + 20, 线型: 'solid' },
    { id: '__b194-tb', x: 工具条[0] - 6, y: 工具条[1] - 6, w: 工具条[2] + 12, h: 工具条[3] + 12, 线型: 'dashed' },
  ];
  const 读 = await 画框(p, 规格);
  const g = 守卫(读, 2);
  记.图['185'] = { 断言, 几何: G2, 守卫: g, 读数: 读 };
  console.log('185 守卫 =', JSON.stringify(g), '选中数 =', 断言.选中数);
  if (断言.选中数 === 1 && Object.values(g).every(Boolean)) {
    const y0 = Math.min(G2.节点[1] - 10, 工具条[1] - 6) - 10;
    const h = (G2.节点[1] + G2.节点[3] + 10) - y0;
    await p.screenshot({ path: `${SHOTS}/185-text-node-selected.png`, clip: { x: Math.round(G2.节点[0] - 24), y: Math.round(y0), width: Math.round(G2.节点[2] + 48), height: Math.round(h) } });
    记.图['185'].裁切 = { x: Math.round(G2.节点[0] - 24), y: Math.round(y0), width: Math.round(G2.节点[2] + 48), height: Math.round(h) };
    console.log('185 已拍');
  }
  save();
  await 清框(p);

  // 186 编辑态（同一裁切）：双击正文
  await p.mouse.dblclick(G2.正文中心[0], G2.正文中心[1]); await p.waitForTimeout(2600);
  const 编辑态 = await p.evaluate(() => ({
    编辑面: document.querySelectorAll('.tiptap.ProseMirror').length,
    节点内contenteditable: document.querySelectorAll('.react-flow__node [contenteditable]').length,
    工具条: !!document.querySelector('[data-testid="text-editor-toolbar"]'),
    节点选中: document.querySelectorAll('.react-flow__node.selected').length,
    编辑面几何: (() => { const e = document.querySelector('.tiptap.ProseMirror'); if (!e) return null;
      const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })(),
    编辑面在节点内: (() => { const e = document.querySelector('.tiptap.ProseMirror');
      return e ? !!e.closest('.react-flow__node') : null; })(),
    焦点: (() => { const a = document.activeElement; return a ? a.tagName + '[' + (a.getAttribute('aria-label') || a.getAttribute('data-testid') || '') + ']' : null; })() }));
  console.log('编辑态 =', JSON.stringify(编辑态));
  const G3 = await 几何(p);
  const 规格2 = [{ id: '__b194-node', x: G3.节点[0] - 10, y: G3.节点[1] - 10, w: G3.节点[2] + 20, h: G3.节点[3] + 20, 线型: 'solid' }];
  const 读2 = await 画框(p, 规格2);
  const g2 = 守卫(读2, 1);
  记.图['186'] = { 编辑态, 几何: G3, 守卫: g2, 读数: 读2 };
  console.log('186 守卫 =', JSON.stringify(g2));
  if (编辑态.编辑面 >= 1 && Object.values(g2).every(Boolean)) {
    const y0 = G3.节点[1] - 10 - 10 - 46;   // 与 185 同一裁切上沿：把工具条该在的位置也留出来
    await p.screenshot({ path: `${SHOTS}/186-text-node-editing.png`, clip: { x: Math.round(G3.节点[0] - 24), y: Math.round(y0), width: Math.round(G3.节点[2] + 48), height: Math.round((G3.节点[1] + G3.节点[3] + 10) - y0) } });
    记.图['186'].裁切 = { x: Math.round(G3.节点[0] - 24), y: Math.round(y0), width: Math.round(G3.节点[2] + 48), height: Math.round((G3.节点[1] + G3.节点[3] + 10) - y0) };
    console.log('186 已拍');
  }
  save();
  await 清框(p);

  // 187 编辑器是 portal 浮层：节点框 + 编辑面框 + 工具条框，同一画面
  const 规格3 = [
    { id: '__b194-node', x: G3.节点[0] - 6, y: G3.节点[1] - 6, w: G3.节点[2] + 12, h: G3.节点[3] + 12, 线型: 'solid' },
    { id: '__b194-ed', x: 编辑态.编辑面几何[0] - 5, y: 编辑态.编辑面几何[1] - 5, w: 编辑态.编辑面几何[2] + 10, h: 编辑态.编辑面几何[3] + 10, 线型: 'dashed' },
  ];
  if (编辑态.工具条) { const Gt = await 几何(p);
    const TB = Gt.编辑态工具条 || Gt.选中态工具条; if (TB) 规格3.push({ id: '__b194-tb', x: TB[0] - 5, y: TB[1] - 5, w: TB[2] + 10, h: TB[3] + 10, 线型: 'dashed' }); }
  const 读3 = await 画框(p, 规格3);
  const g3 = 守卫(读3, 规格3.length);
  记.图['187'] = { 编辑态, 规格3, 守卫: g3, 读数: 读3 };
  console.log('187 守卫 =', JSON.stringify(g3), '框数 =', 规格3.length);
  if (Object.values(g3).every(Boolean)) {
    const xs = 规格3.map((s) => s.x), ys = 规格3.map((s) => s.y);
    const xe = 规格3.map((s) => s.x + s.w), ye = 规格3.map((s) => s.y + s.h);
    const x = Math.min(...xs) - 14, y = Math.min(...ys) - 14;
    await p.screenshot({ path: `${SHOTS}/187-text-editor-portal.png`, clip: { x: Math.round(x), y: Math.round(y), width: Math.round(Math.max(...xe) - x + 14), height: Math.round(Math.max(...ye) - y + 14) } });
    记.图['187'].裁切 = { x: Math.round(x), y: Math.round(y), width: Math.round(Math.max(...xe) - x + 14), height: Math.round(Math.max(...ye) - y + 14) };
    console.log('187 已拍');
  }
  save();
  await 清框(p);
  await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
}

// 188 标题改名态：单击 Rename 钮 → 双击它 → INPUT[Node title]
{
  const G = await 几何(p);
  await p.mouse.click(G.标题中心[0], G.标题中心[1]); await p.waitForTimeout(1100);
  const rename点 = await p.evaluate((nid) => { const b = document.querySelector(`.react-flow__node[data-id="${nid}"] [aria-label^="Rename "]`);
    if (!b) return null; const r = b.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, TID);
  记.图['188'] = { rename点 };
  if (!rename点) { console.log('没有 Rename 钮'); } else {
    await p.mouse.click(rename点[0], rename点[1]); await p.waitForTimeout(700);
    await p.mouse.dblclick(rename点[0], rename点[1]); await p.waitForTimeout(1300);
    const 输入 = await p.evaluate(() => { const i = document.querySelector('input[aria-label="Node title"]'); if (!i) return null;
      const r = i.getBoundingClientRect();
      return { 值: i.value, 屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        焦点在它上面: document.activeElement === i,
        落在标题行矩形内: (() => { const t = document.querySelector('.react-flow__node.selected [data-testid="flow-node-title"]');
          if (!t) return null; const tr = t.getBoundingClientRect();
          return r.x >= tr.x - 1 && r.x + r.width <= tr.x + tr.width + 1; })(),
        编辑面数: document.querySelectorAll('.tiptap.ProseMirror').length }; });
    console.log('标题改名态 =', JSON.stringify(输入));
    const G4 = await 几何(p);
    const 规格4 = [{ id: '__b194-in', x: 输入.屏上[0] - 6, y: 输入.屏上[1] - 6, w: 输入.屏上[2] + 12, h: 输入.屏上[3] + 12, 线型: 'solid' },
                   { id: '__b194-ti', x: G4.标题行[0] - 6, y: G4.标题行[1] - 6, w: G4.标题行[2] + 12, h: G4.标题行[3] + 12, 线型: 'dashed' }];
    const 读4 = await 画框(p, 规格4);
    const g4 = 守卫(读4, 2);
    记.图['188'] = { ...记.图['188'], 输入, 守卫: g4, 读数: 读4 };
    console.log('188 守卫 =', JSON.stringify(g4));
    if (输入 && Object.values(g4).every(Boolean)) {
      const x = Math.min(规格4[0].x, 规格4[1].x) - 14, y = Math.min(规格4[0].y, 规格4[1].y) - 14;
      const w = Math.max(规格4[0].x + 规格4[0].w, 规格4[1].x + 规格4[1].w) - x + 14;
      const h = Math.max(规格4[0].y + 规格4[0].h, 规格4[1].y + 规格4[1].h) - y + 14;
      await p.screenshot({ path: `${SHOTS}/188-text-rename-input.png`, clip: { x: Math.round(x), y: Math.round(y), width: Math.round(w), height: Math.round(h) } });
      记.图['188'].裁切 = { x: Math.round(x), y: Math.round(y), width: Math.round(w), height: Math.round(h) };
      console.log('188 已拍');
    }
  }
  save();
  await 清框(p);
  // 取消改名（Esc），别真的改了节点名
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
}
const 改名后标题 = await p.evaluate((nid) => { const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  return { aria: n ? n.getAttribute('aria-label') : null, 标题文字: n ? (n.querySelector('[data-testid="flow-node-title"]') || {}).innerText : null }; }, TID);
记.改名后 = { ...改名后标题, 说明: 'Esc 取消后应与原名「文本 3」一致' };
console.log('改名后 =', JSON.stringify(记.改名后));
save();
await 清选中(p);
await setZoom(p, 26); await p.waitForTimeout(600);
const ids = await R.ids();
记.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), zoom: await R.zoom(), credits: await R.credits(), 节点数: ids.length,
  残留: ids.filter((x) => !基线.ids.includes(x)), 丢失: 基线.ids.filter((x) => !ids.includes(x)) };
save();
console.log('收尾 =', JSON.stringify(记.收尾));
await b.close();
console.log('写出', OUT);
