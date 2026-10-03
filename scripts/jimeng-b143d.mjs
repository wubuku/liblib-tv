// 批次 143 d 轮 —— 绕开框选，验「点选 + Shift 加选」能不能拿到 2 选中并编组。
//
// 🔑 为什么换路（a 轮 `planBoxFor` 失败，b/c 轮拖动被 overlay 打断）：
//   · a 轮：叠放两节点的包围盒外扩后找不到「四角不在任何节点内」的矩形（76 节点太密）。
//   · c/diag：**单击文本节点会展开 `text-editor-node-overlay`（内含 tiptap contenteditable），
//     而该 overlay 挂在 `.react-flow__renderer` 下、**不在 `.react-flow__node` 里**
//     ⇒ overlay 一旦展开，`closest('.react-flow__node')` 恒为 `null`。
//     叠放下再拖动，鼠标落在 overlay 上 ⇒ 拖不动（diag 实测位移 0）。
//   ⇒ 只剩两条不经框选的路：**Shift 加选**，或先用产品自己的「宫格布局」排开。
// 本轮验第一条。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, 点编组, 点解除编组, selIds, selCount, 组数, idsOf, canvasPos, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 143, 轮: 'd', 目的: '验 Shift 加选 → 编组' };

/** 节点内「独占可点像素」：点它会选中该节点（点空白/点别的节点都不算）。 */
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
      if (!nn || nn.getAttribute('data-id') !== i) continue;   // 🔴 必须逐字等于目标
      if (h.tagName !== 'DIV') continue;
      if (h.closest('.octo-text-node-resize-controls')) continue;
      if (h.closest('[contenteditable]')) continue;
      if (/text-octo-ui-copy/.test(String(h.className || ''))) continue;
      好.push([x, y]);
    }
  if (!好.length) return { __err: 'no-exclusive-point' };
  // 🔴 c/diag 轮踩过：取「质心」有缺陷 —— 像素集不连续时质心会落到**别的节点**上。
  //   这里改成取**中位序**像素（落在集合里且靠近几何中心，天然合格）。
  const cx = 好.reduce((a, q) => a + q[0], 0) / 好.length;
  const cy = 好.reduce((a, q) => a + q[1], 0) / 好.length;
  好.sort((u, v) => (Math.hypot(u[0] - cx, u[1] - cy)) - (Math.hypot(v[0] - cx, v[1] - cy)));
  return { 总数: 好.length, 落点: 好[0], 前3: 好.slice(0, 3) };
}, id);

const 删一个 = async (id) => {
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  const 落 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
  if (落.__err) return { id, __err: 'no-point' };
  await p.mouse.click(落.x, 落.y);
  await p.waitForTimeout(900);
  const 前 = await idsOf(p);
  const 落2 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
  if (落2.__err) return { id, __err: 'no-point-2' };
  await p.mouse.click(落2.x, 落2.y, { button: 'right' });
  await p.waitForTimeout(1800);
  const del = await p.evaluate(() => {
    const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
      .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
    if (!els.length) return { __err: 'no-delete-item' };
    const e = els[0]; const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
      for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
        const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y };
      }
    return { __err: 'no-point' };
  });
  if (del.__err) return { id, __err: del.__err };
  await p.mouse.click(del.x, del.y);
  await p.waitForTimeout(2500);
  await settle(p, R);
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
    rec.建前canvas = await canvasPos(p);
    rec.独占 = {};
    for (const id of 建.ids) rec.独占[id] = await 独占像素(id);

    // ---- ① 先点 A（独占像素最多的那个）
    const 先点 = rec.独占[B].总数 > rec.独占[A].总数 ? B : A;   // 点上层那个，命中更稳
    const 后点 = 先点 === A ? B : A;
    const 落1 = rec.独占[先点].落点;
    rec.先点 = { id: 先点, 落点: 落1 };
    // 每次点击前重新断言：落点归属 + 无浮层
    const 前置1 = await p.evaluate(([x, y, i]) => {
      const h = document.elementFromPoint(x, y); const nn = h ? h.closest('.react-flow__node') : null;
      return { 命中id: nn ? nn.getAttribute('data-id') : null, 等于目标: !!nn && nn.getAttribute('data-id') === i,
        浮层: Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length,
        overlay: !!document.querySelector('[data-testid="text-editor-node-overlay"]') };
    }, [落1[0], 落1[1], 先点]);
    rec.前置1 = 前置1;
    if (前置1.等于目标 && 前置1.浮层 === 0) {
      await p.mouse.click(落1[0], 落1[1]);
      await p.waitForTimeout(1300);
    }
    rec.第一次点后 = { 选中: await selIds(p), 选中数: await selCount(p), 状态行: await R.status() };

    // ---- ② Shift 加选第二个
    const 落2 = rec.独占[后点].落点;
    const 前置2 = await p.evaluate(([x, y, i]) => {
      const h = document.elementFromPoint(x, y); const nn = h ? h.closest('.react-flow__node') : null;
      return { 命中id: nn ? nn.getAttribute('data-id') : null, 等于目标: !!nn && nn.getAttribute('data-id') === i,
        浮层: Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length };
    }, [落2[0], 落2[1], 后点]);
    rec.前置2 = 前置2;
    rec.加选落点 = { id: 后点, 落点: 落2 };
    if (前置2.等于目标 && 前置2.浮层 === 0) {
      await p.keyboard.down('Shift');
      await p.mouse.click(落2[0], 落2[1]);
      await p.keyboard.up('Shift');
      await p.waitForTimeout(1300);
    }
    rec.Shift点后 = { 选中: await selIds(p), 选中数: await selCount(p), 状态行: await R.status() };
    rec.选中判定 = { 期望: [...建.ids].sort(), 实际: await selIds(p),
      恰好: JSON.stringify(await selIds(p)) === JSON.stringify([...建.ids].sort()) };

    // ---- ③ 编组
    if (rec.选中判定.恰好) {
      rec.编组 = await 点编组(p);
      rec.编组后 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p) };
    } else { rec.中止 = 'Shift 加选没拿到 2 选中'; }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

// ---- 清理
try {
  if ((await 组数(p)) > 0) { rec.解组 = await 点解除编组(p); }
  rec.解组后 = { 状态行: await R.status(), 组数: await 组数(p), 选中: await selIds(p) };
  rec.删除 = [];
  for (const id of ((rec.建 && rec.建.ids) || [])) rec.删除.push(await 删一个(id));
} catch (e) { rec.删除异常 = String(e).slice(0, 300); }

await settle(p, R);
const 末 = await idsOf(p);
rec.收尾 = { 状态行: await R.status(), 节点数: 末.length, 组数: await 组数(p), 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), 剩余自建: 末.filter((x) => ((rec.建 && rec.建.ids) || []).includes(x)) };
fs.writeFileSync(new URL('./_tmp-b143d.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 独占: rec.独占 && Object.fromEntries(Object.entries(rec.独占).map(([k, v]) => [k, { 总数: v.总数, 落点: v.落点 }])),
  第一次点后: rec.第一次点后, Shift点后: rec.Shift点后, 选中判定: rec.选中判定, 编组: rec.编组, 编组后: rec.编组后,
  解组: rec.解组, 删除: rec.删除, 收尾: rec.收尾, 异常: rec.异常 }, null, 1));
await b.close();
