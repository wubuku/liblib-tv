// 批次 143 i 轮 —— 定案一件事：**叠放 + 2 选中时，Esc 到底能不能清空选中？**
//
// 🔴 为什么必须定案：我在 §4.65.4 已经写了「`Escape` 清不掉 2 个节点的选中
//   （实测 `清后: 2`，连按三次都是 2）」，而 `90-troubleshooting.md:312` 的
//   Esc 语义全表里明写「画布选中态（单选 / **多选** / 选中编组）| ✅ 清空选中」。
//   ⇒ **两处直接打架**，而手册是对的概率更高（那是 2026-10-01 逐项实测过的全表）。
//
//   本项目纪律：**按任何字母/数字键前必须过 keyGuard；keyGuard 报 safe 还要先把焦点
//   交回画布**（否则快捷键被别的东西吞）。我在 rescue 脚本里 `press('Escape')`
//   **既没过 keyGuard、也没确认焦点在哪** ⇒ 那个「清不掉」很可能是**我的方法问题**。
//
// 💡 真正的嫌疑：**叠放 2 选中时 `text-editor-node-overlay` 展开，
//   里面的 tiptap `ProseMirror`（contenteditable）拿走了焦点** ⇒ Esc 被编辑器吃掉。
//
// 本轮读三样：按 Esc 前的 `document.activeElement`、按 Esc 后的选中数、以及焦点移到 body 后的对照。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, selIds, selCount, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 143, 轮: 'i', 目的: '定案 Esc 能否清多选' };

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

/** 读焦点落在哪（连同「在不在画布里」）。 */
const 读焦点 = () => p.evaluate(() => {
  const a = document.activeElement;
  const 链 = []; for (let n = a; n && n !== document.body; n = n.parentElement) {
    链.push({ tag: n.tagName, cls: String(n.className || '').split(' ').slice(0, 2).join(' ').slice(0, 46),
      testid: n.getAttribute('data-testid') }); }
  return { tag: a ? a.tagName : null, cls: a ? String(a.className || '').slice(0, 60) : null,
    testid: a ? a.getAttribute('data-testid') : null,
    isCE: !!(a && (a.closest('[contenteditable]') || a.isContentEditable)),
    在编辑器overlay里: !!(a && a.closest('[data-testid="text-editor-node-overlay"]')),
    在画布wrapper里: !!(a && a.closest('.react-flow__pane, .react-flow__renderer, .react-flow')),
    链: 链.slice(0, 6) };
});

const 造2选中 = async (ids) => {
  const [A, B] = ids;
  const nA = (await 独占像素(A)).总数, nB = (await 独占像素(B)).总数;
  const 先 = nB >= nA ? B : A, 后 = 先 === A ? B : A;
  const l1 = await 独占像素(先);
  await p.mouse.click(l1.落点[0], l1.落点[1]); await p.waitForTimeout(1300);
  const l2 = await 独占像素(后);
  await p.keyboard.down('Shift'); await p.mouse.click(l2.落点[0], l2.落点[1]); await p.keyboard.up('Shift');
  await p.waitForTimeout(1400);
  return { 恰好: JSON.stringify(await selIds(p)) === JSON.stringify([...ids].sort()), 实际: await selIds(p) };
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
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 焦点: await 读焦点(), keyGuard: await keyGuard(p) };

  const 建 = await 建N个(p, '文本', 2, null, 76);
  rec.建 = 建;
  if (!(建.ids && 建.ids.length === 2)) { rec.中止 = '建节点未成'; }
  else {
    rec.轮次 = [];

    // ---- 轮 1：2 选中刚做完，焦点在未知处，直接按 Esc（= rescue 脚本的做法）
    let s = await 造2选中(建.ids);
    rec['轮1_造选中'] = s;
    rec['轮1_按Esc前'] = { 焦点: await 读焦点(), 选中数: await selCount(p), keyGuard: await keyGuard(p) };
    await p.keyboard.press('Escape'); await p.waitForTimeout(1300);
    rec['轮1_按Esc后'] = { 焦点: await 读焦点(), 选中数: await selCount(p), 浮层: await R.overlays() };
    await p.keyboard.press('Escape'); await p.waitForTimeout(1300);
    rec['轮1_再按一次'] = { 焦点: await 读焦点(), 选中数: await selCount(p) };

    // ---- 轮 2：**先交出焦点**（点真空白之外，改用把焦点显式点到画布 pane 上），
    //   再造 2 选中，再按 Esc。看是不是焦点问题。
    const 空 = await 找真空白();
    if (!空.__err) { await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1200); }
    rec['轮2_清后'] = { 选中数: await selCount(p), 焦点: await 读焦点() };
    s = await 造2选中(建.ids);
    rec['轮2_造选中'] = s;
    rec['轮2_按Esc前'] = { 焦点: await 读焦点(), 选中数: await selCount(p) };
    // 显式把焦点放到画布 pane 上（focus()，不触发选中变化）
    await p.evaluate(() => { const e = document.querySelector('.react-flow__pane');
      if (e) { e.setAttribute('tabindex', '-1'); e.focus(); } });
    await p.waitForTimeout(400);
    rec['轮2_强制聚焦后'] = { 焦点: await 读焦点(), 选中数: await selCount(p) };
    await p.keyboard.press('Escape'); await p.waitForTimeout(1300);
    rec['轮2_按Esc后'] = { 焦点: await 读焦点(), 选中数: await selCount(p) };

    // ---- 轮 3：单选态对照（手册全表说单选 ✅ 清空）
    if (await selCount(p) > 0) { const 空2 = await 找真空白(); if (!空2.__err) { await p.mouse.click(空2.x, 空2.y); await p.waitForTimeout(1200); } }
    const l = await 独占像素(建.ids[1]);
    await p.mouse.click(l.落点[0], l.落点[1]); await p.waitForTimeout(1300);
    rec['轮3_单选后'] = { 选中数: await selCount(p), 焦点: await 读焦点() };
    await p.evaluate(() => { const e = document.querySelector('.react-flow__pane'); if (e) { e.setAttribute('tabindex', '-1'); e.focus(); } });
    await p.waitForTimeout(300);
    await p.keyboard.press('Escape'); await p.waitForTimeout(1300);
    rec['轮3_按Esc后'] = { 选中数: await selCount(p), 焦点: await 读焦点() };
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

try { rec.删除 = []; for (const id of ((rec.建 && rec.建.ids) || [])) rec.删除.push(await 删一个(id));
} catch (e) { rec.删除异常 = String(e).slice(0, 300); }

await settle(p, R);
const 末 = await idsOf(p);
rec.收尾 = { 状态行: await R.status(), 节点数: 末.length, 选中: await selCount(p), 浮层: await R.overlays(),
  zoom: await R.zoom(), 剩余自建: 末.filter((x) => ((rec.建 && rec.建.ids) || []).includes(x)) };
fs.writeFileSync(new URL('./_tmp-b143i.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 起点焦点: rec.起点 && rec.起点.焦点, 轮次: rec.轮次, 删除: rec.删除, 收尾: rec.收尾, 异常: rec.异常 }, null, 1));
for (const k of Object.keys(rec)) if (k.startsWith('轮') && k !== '轮次') console.log(k, JSON.stringify(rec[k]));
await b.close();
