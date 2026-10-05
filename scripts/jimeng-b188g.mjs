// 批次 188 g 轮：⊕ 的「多出来的 2 倍」到底在哪。
//
// 188 f 已经把**经验公式**钉死（10 档全中）：屏上 = min(72×缩放, 36)，拐点正好 50%。
// 但机制上有个说不通的地方：
//   22% 档：BUTTON 的 `offsetWidth = 36`，而 `getBoundingClientRect().width = 15.8`。
//   15.8 ÷ 0.22 = 71.8 ≈ 72，**正好是 offsetWidth 的两倍**；
//   同一个链上，父 DIV（569）与祖先 node（569）都严格等于 `offsetWidth × 缩放`。
//   而 f 逐层读过 computed `transform`：**全链只有 viewport 一处非 1**，
//   BUTTON 自身是 `matrix(1, 0, 0, 1, 18, -18)`（纯位移，缩放分量 = 1）。
// ⇒ 「有 2 倍」这件事**在 transform 里看不见**。三个候选：
//   ① 独立 CSS `scale` 属性（现代浏览器里它**不进 computed transform**，`transform` 读出来是 none/单位阵）
//   ② `zoom` 属性
//   ③ 我读的不是同一个盒子（例如读到的是某个伪元素或另一个实例）
// 本轮把 `transform` / `scale` / `zoom` / `width` / `padding` / `box-sizing` / `border` 全读出来逐个排除。
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '188g', 候选解释: ['独立 scale 属性', 'zoom 属性', '读的不是同一个盒子'] };
await settle(p, R);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
rec.起点 = { 节点数: 基线.ids.length, 积分: await R.credits(), 缩放: await R.zoom() };

// 选中带内容的图片节点（用搜索面板，188b/188f 验证过）
const 开 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
  if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
if (!开) throw new Error('没有搜索按钮');
await p.mouse.click(开[0], 开[1]); await p.waitForTimeout(1100);
const 输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
  if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
if (!输入) { await p.keyboard.press('Escape'); throw new Error('搜索面板没打开'); }
await p.mouse.click(输入[0], 输入[1]); await p.waitForTimeout(400);
await p.fill('[data-testid="canvas-search-panel"] input', 'b22-upload'); await p.waitForTimeout(1500);
const 命中 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
  .map((e) => { const r = e.getBoundingClientRect(); return { id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; })
  .filter((x) => x.文字.includes('b22-upload')));
if (!命中.length) { await p.keyboard.press('Escape'); throw new Error('搜索无命中'); }
await p.mouse.click(命中[0].点[0], 命中[0].点[1]); await p.waitForTimeout(1600);
rec.选中 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
await p.keyboard.press('Escape'); await p.waitForTimeout(500);
if (rec.选中.length !== 1) throw new Error('选中集不干净：' + JSON.stringify(rec.选中));

/** 把一个元素的全部可疑样式量一次读全，外加它的 ::before/::after。 */
const 深读 = () => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const ms = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
  const scale = ms ? parseFloat(ms[1]) : null;
  const 节点 = document.querySelector('.react-flow__node.selected');
  if (!节点) return { scale, 缺: '没有选中节点' };
  const es = Array.from(节点.querySelectorAll('[aria-label^="Create connected node"]'));
  const 读一个 = (e, 名) => { const cs = getComputedStyle(e); const r = e.getBoundingClientRect();
    const 伪 = (which) => { const p2 = getComputedStyle(e, which); return { width: p2.width, height: p2.height, transform: p2.transform, scale: p2.scale, zoom: p2.zoom, content: p2.content }; };
    return { 名, tag: e.tagName, class: String(e.className || '').slice(0, 80), testid: e.getAttribute('data-testid'),
      屏上: { w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100 },
      offsetWidth: e.offsetWidth, offsetHeight: e.offsetHeight, clientWidth: e.clientWidth,
      rectWidth: r.width,
      /** 这些是「可能藏着 2 倍」的地方 */
      transform: cs.transform, scale: cs.scale, zoom: cs.zoom, rotate: cs.rotate,
      width: cs.width, height: cs.height, minWidth: cs.minWidth, minHeight: cs.minHeight,
      padding: cs.padding, border: cs.border, boxSizing: cs.boxSizing, fontSize: cs.fontSize,
      position: cs.position, top: cs.top, left: cs.left, right: cs.right, bottom: cs.bottom,
      before: 伪('::before'), after: 伪('::after') };
  };
  // 顺便把「按钮的直接父级」也深读一份：父级若带 scale，按钮的 rect 会被算进去
  const 父 = es[0] ? es[0].parentElement : null;
  return { scale, 缩放aria: (document.querySelector('[data-testid="canvas-zoom-percent"]') || {}).ariaLabel || null,
    节点屏上: (() => { const r = 节点.getBoundingClientRect(); return { w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100 }; })(),
    节点offset: { w: 节点.offsetWidth, h: 节点.offsetHeight },
    按钮数: es.length,
    按钮: es.map((e) => 读一个(e, '⊕')),
    父级: 父 ? 读一个(父, '按钮父级') : null,
    同位置同尺寸的元素: (() => { // 候选③：是不是有另一个盒子叠在同一位置
      const a = es[0]; if (!a) return null; const r = a.getBoundingClientRect();
      const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
      const h = document.elementFromPoint(cx, cy);
      const 链 = []; for (let n = h; n && n !== document.body; n = n.parentElement) 链.push(n.tagName + '.' + String(n.className || '').split(' ')[0] + (n.getAttribute('data-testid') ? '[' + n.getAttribute('data-testid') + ']' : ''));
      return { 落点: [cx, cy], 命中链: 链, 命中的是否就是按钮: h === a || a.contains(h) };
    })() };
});

rec.各档 = [];
for (const pct of [22, 26, 50, 100, 26]) {   // 只改缩放，不重新选中（立规 57）
  const z = await setZoom(p, pct);
  await p.mouse.move(1250, 706); await p.waitForTimeout(900);
  const d = await 深读();
  rec.各档.push({ 档: pct, 回读: z.回读, setZoom已追平: z.scale已追平, ...d });
}

// —— 判定
rec.判定 = rec.各档.map((r) => {
  const a = r.按钮 && r.按钮[0];
  if (!a) return { 档: r.档, 缺: true, 按钮数: r.按钮数 };
  const 比 = { 屏上w: a.屏上.w, offsetWidth: a.offsetWidth, width样式: a.width, minWidth: a.minWidth, padding: a.padding,
    boxSizing: a.boxSizing, border: a.border, transform: a.transform, scale属性: a.scale, zoom: a.zoom,
    before: { width: a.before.width, transform: a.before.transform, scale: a.before.scale, content: a.before.content },
    after: { width: a.after.width, transform: a.after.transform, scale: a.after.scale, content: a.after.content } };
  return { 档: r.档, scale: r.scale, 屏上除以缩放: Math.round((a.屏上.w / r.scale) * 100) / 100, ...比,
    父级: r.父级 ? { 屏上w: r.父级.屏上.w, offsetWidth: r.父级.offsetWidth, transform: r.父级.transform, scale属性: r.父级.scale, zoom: r.父级.zoom, minWidth: r.父级.minWidth, width: r.父级.width } : null,
    落点命中的是否就是按钮: r.同位置同尺寸的元素 ? r.同位置同尺寸的元素.命中的是否就是按钮 : null,
    落点链: r.同位置同尺寸的元素 ? r.同位置同尺寸的元素.命中链.slice(0, 3) : null };
});
rec.判定.非空守卫 = { 档数: rec.各档.length, 每档都读到按钮: rec.各档.every((r) => (r.按钮 || []).length >= 1),
  每档都选中: rec.各档.every((r) => !r.缺), 落点都命中按钮: rec.各档.every((r) => r.同位置同尺寸的元素 && r.同位置同尺寸的元素.命中的是否就是按钮 === true) };

await p.keyboard.press('Escape'); await p.waitForTimeout(700);
rec.收尾 = await endState(p, R, 基线);
console.log(JSON.stringify(rec, null, 1));
await b.close();
