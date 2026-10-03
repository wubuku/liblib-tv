// 批次 143 g 轮 —— 收口：所选颜色那一层到底画在哪？
//
// 🔑 f 轮已经把机制挖到只剩最后一层：
//   · `group-background` 的类是 `… transition-colors bg-dreamina-bg-menu`
//     ⇒ 默认底色 = `--dreamina-color-bg-menu: #262626` = `rgb(38,38,38)` ✔
//   · 取色后它读作 `rgb(13,13,13)` = `#0d0d0d` = **`--dreamina-color-canvas-bg`**（画布背景色）
//   · 五个色相都有配套的 **`-block` 变量，尾数一律 `29`**：
//       brand-teal-block `#00cae029` / brand-indigo-block `#6d7cff29` /
//       brand-purple-block `#be68ff29` / brand-orange-block `#ff923029` /
//       brand-yellow-block `#ffd60029`
//     `29` = α 41/255 ≈ **16% 不透明度**
//   ⇒ 结论方向：所选颜色是**一层 16% 半透明**，而 `group-background` 只是**底**。
//
// 🔴 e/f 两轮的 dump **只遍历 `el.children`，从不读 `::before` / `::after`** ——
//   那一层极可能是伪元素。⇒ 本轮专门补读伪元素，并用**截图**作独立旁证
//   （截图是像素事实，不依赖任何 DOM 判据）。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, 点编组, 点解除编组, selIds, selCount, 组数, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 143, 轮: 'g', 目的: '伪元素 + 截图旁证' };
const 轮色 = ['无颜色', '青绿色', '靛蓝色', '紫色', '橙色', '黄色'];
const 目录 = new URL('./_tmp_b143g-shots/', import.meta.url);
fs.mkdirSync(目录, { recursive: true });

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

/** 🔑 读组卡片整棵子树 —— **这次连 `::before` / `::after` 伪元素一起读**。 */
const 读含伪元素 = () => p.evaluate(() => {
  const g = document.querySelector('.react-flow__node-group');
  if (!g) return { __err: 'no-group' };
  const r = g.getBoundingClientRect();
  const 条目 = [];
  const 看 = (el, 路径, d) => {
    const cs = getComputedStyle(el);
    const 自己 = { 路径, tag: el.tagName, testid: el.getAttribute('data-testid'),
      cls: String(el.className || '').slice(0, 130),
      背景: cs.backgroundColor, 背景图: cs.backgroundImage === 'none' ? 'none' : cs.backgroundImage.slice(0, 120),
      不透明度: cs.opacity };
    for (const 伪 of ['::before', '::after']) {
      const cp = getComputedStyle(el, 伪);
      if (cp.content === 'none' && cp.backgroundColor === 'rgba(0, 0, 0, 0)' && cp.backgroundImage === 'none') continue;
      条目.push({ 路径: 路径 + 伪, 伪, content: cp.content, cls: String(cp.pointerEvents || ''),
        背景: cp.backgroundColor, 背景图: cp.backgroundImage === 'none' ? 'none' : cp.backgroundImage.slice(0, 120),
        inset: [cp.top, cp.right, cp.bottom, cp.left].join(' '), 不透明度: cp.opacity, zIndex: cp.zIndex });
    }
    if (cs.backgroundColor !== 'rgba(0, 0, 0, 0)' || cs.backgroundImage !== 'none')
      条目.push(对象(自己));
    if (d < 8) Array.from(el.children).forEach((c, i) => 看(c, 路径 + '>' + c.tagName + '[' + i + ']', d + 1));
  };
  const 对象 = (o) => o;
  看(g, 'GROUP', 0);
  return { 组盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10], 条目数: 条目.length, 条目 };
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
      return { 逐字: (e.getAttribute('aria-label') || e.innerText || '').replace(/\s+/g, ' ').trim(), 盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; });
  });
  if (项.__err) return 项;
  const t = 项.find((q) => q.逐字 === 逐字);
  if (!t) return { __err: '色板里没有 ' + 逐字 };
  const 前置 = await p.evaluate(([x, y, w]) => { const h = document.elementFromPoint(x, y);
    const m = h ? h.closest('[role=menuitemradio]') : null;
    return { 逐字命中: !!m && (m.getAttribute('aria-label') || m.innerText || '').replace(/\s+/g, ' ').trim() === w }; }, [t.盒[0] + 14, t.盒[1] + 14, 逐字]);
  if (!前置.逐字命中) return { __err: '落点归属不符', 前置 };
  await p.mouse.click(t.盒[0] + 14, t.盒[1] + 14);
  await p.waitForTimeout(2200);
  await settle(p, R);
  return { ok: true };
};

/** 裁剪组卡片区域截图 —— 像素事实，不依赖 DOM 判据。 */
const 拍 = async (名) => {
  const g = await p.evaluate(() => { const e = document.querySelector('.react-flow__node-group');
    if (!e) return null; const r = e.getBoundingClientRect();
    return { x: Math.max(0, Math.round(r.x) - 8), y: Math.max(0, Math.round(r.y) - 8),
      width: Math.min(1280, Math.round(r.width) + 16), height: Math.min(720, Math.round(r.height) + 16) }; });
  if (!g) return { __err: 'no-group-box' };
  const f = new URL('./' + 名 + '.png', 目录);
  await p.screenshot({ path: f.pathname, clip: g });
  return { 文件: 名 + '.png', 裁剪: g };
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
    rec.选中判定 = { 恰好: JSON.stringify(await selIds(p)) === JSON.stringify([...建.ids].sort()) };
    if (!rec.选中判定.恰好) { rec.中止 = 'Shift 加选失败'; }
    else {
      rec.编组 = await 点编组(p);
      rec.轮次 = [];
      for (const c of 轮色) {
        const r = c === '无颜色' && rec.轮次.length === 0 ? { ok: true, 备注: '初始即无颜色，跳过取色' } : await 取色(c);
        if (r && r.__err) { rec.轮次.push({ 色: c, __err: r.__err }); break; }
        const 读 = await 读含伪元素();
        const 图 = await 拍('g-' + 轮色.indexOf(c) + '-' + c);
        rec.轮次.push({ 色: c, 组盒: 读.组盒, 条目数: 读.条目数,
          有伪元素的条目: 读.条目.filter((q) => q.伪),
          背景非透明的条目: 读.条目.filter((q) => !q.伪),
          截图: 图 });
      }
      rec.伪元素总数 = rec.轮次.reduce((a, q) => a + (q.有伪元素的条目 ? q.有伪元素的条目.length : 0), 0);
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
fs.writeFileSync(new URL('./_tmp-b143g.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 伪元素总数: rec.伪元素总数,
  轮次: (rec.轮次 || []).map((q) => ({ 色: q.色, 条目数: q.条目数, err: q.__err,
    伪: (q.有伪元素的条目 || []).map((e) => e.路径 + ' 背景=' + e.背景 + ' 背景图=' + e.背景图 + ' inset=' + e.inset),
    实体: (q.背景非透明的条目 || []).map((e) => e.路径 + (e.testid ? '[#' + e.testid + ']' : '') + ' cls=' + e.cls.slice(-40) + ' 背景=' + e.背景 + ' 背景图=' + e.背景图),
    截图: q.截图 })), 收尾: rec.收尾, 异常: rec.异常 }, null, 1));
await b.close();
