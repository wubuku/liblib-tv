// 批次 143 救援 —— 清掉 d 轮残留的 2 个孤儿文本节点。
//
// 🔑 为什么单独写：d 轮删除段用的是 `可点落点('.react-flow__node[data-id=…]')`，
//   叠放 + 2 选中 + `text-editor-node-overlay` 展开时，落点扫到的命中元素
//   **不在 `.react-flow__node` 里**（overlay 挂在 `.react-flow__renderer` 下）
//   ⇒ 恒 `no-point`，两个节点没删掉。
// 📌 立规：**归位通道必须独立于出错脚本**，不能靠重跑出错的那个脚本来清残留。
// 本脚本的删除配方：先 Escape 清到 0 选中 → 算「独占像素」（点它必定命中该节点）
//   → 单选 → 右键 → 上下文菜单「删除」。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { selIds, selCount, 组数, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const 目标 = ['node_35mtmtdg52', 'node_p4w8me1pv8'];
const rec = { 批次: 143, 轮: 'rescue', 目标 };

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
      if (!nn || nn.getAttribute('data-id') !== i) continue;   // 🔴 逐字等于目标
      if (h.tagName !== 'DIV') continue;
      if (h.closest('.octo-text-node-resize-controls')) continue;
      if (h.closest('[contenteditable]')) continue;
      if (/text-octo-ui-copy/.test(String(h.className || ''))) continue;
      好.push([x, y]);
    }
  if (!好.length) return { __err: 'no-exclusive-point', 盒: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) } };
  const cx = 好.reduce((a, q) => a + q[0], 0) / 好.length;
  const cy = 好.reduce((a, q) => a + q[1], 0) / 好.length;
  好.sort((u, v) => Math.hypot(u[0] - cx, u[1] - cy) - Math.hypot(v[0] - cx, v[1] - cy));
  return { 总数: 好.length, 落点: 好[0] };
}, id);

/** 一块真正「什么都没有」的画布空白：祖先链里既无 `.react-flow__node`，也无
 *  `text-editor-node-overlay`（多选态下 overlay 会铺在节点上，不排除它就永远点不中），
 *  且不是任何 button / role=button。 */
const 找真空白 = () => p.evaluate(() => {
  const 坏 = (x, y) => {
    const h = document.elementFromPoint(x, y);
    if (!h) return 'null';
    if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button]')) return 'button';
    if (h.closest('.react-flow__node')) return 'in-node';
    if (h.closest('[data-testid="text-editor-node-overlay"]')) return 'in-overlay';
    if (h.closest('.react-flow__node-toolbar')) return 'in-toolbar';
    if (!h.classList || !h.classList.contains('react-flow__pane')) return 'not-pane:' + h.tagName;
    return null;
  };
  for (let y = 90; y < innerHeight - 90; y += 8)
    for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
  return { __err: 'no-free-pane' };
});

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selIds(p), 组数: await 组数(p) };

  rec.动作 = [];
  for (const id of 目标) {
    if (!(await idsOf(p)).includes(id)) { rec.动作.push({ id, __已不在: true }); continue; }
    // ① 清到 0 选中。🔴 d 轮实测：**Escape 清不掉 2 个节点的选中**（实测 `清后: 2`），
    //    只能点画布空白。空白判据必须**额外排除 `text-editor-node-overlay`** ——
    //    多选态下 overlay 铺在节点上，不排除它就永远点不中任何节点。
    for (let k = 0; k < 3 && (await selCount(p)) > 0; k++) {
      const 空 = await 找真空白();
      rec['空白_' + k] = 空;
      if (空.__err) break;
      const 是控件 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y);
        return h ? (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button]') ? 1 : 0) : -1; }, [空.x, 空.y]);
      if (是控件 !== 0) break;
      await p.mouse.click(空.x, 空.y);
      await p.waitForTimeout(1100);
    }
    const 清后 = await selCount(p);
    if (清后 > 0) { rec.动作.push({ id, __err: '清不掉选中，剩 ' + 清后 }); continue; }

    // ② 单选：落在该节点的**独占**像素上
    const 落 = await 独占像素(id);
    rec['独占_' + id] = 落;
    if (落.__err) { rec.动作.push({ id, __err: '独占像素 ' + 落.__err, 清后 }); continue; }
    const 前置1 = await p.evaluate(([x, y, i]) => {
      const h = document.elementFromPoint(x, y); const nn = h ? h.closest('.react-flow__node') : null;
      return { 命中id: nn ? nn.getAttribute('data-id') : null, 等于目标: !!nn && nn.getAttribute('data-id') === i,
        浮层: Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length };
    }, [落.落点[0], 落.落点[1], id]);
    if (前置1.等于目标 && 前置1.浮层 === 0) { await p.mouse.click(落.落点[0], 落.落点[1]); await p.waitForTimeout(1300); }
    rec['前置1_' + id] = { ...前置1, 之后选中: await selIds(p) };

    // ③ 右键 → 上下文菜单「删除」
    const 前 = await idsOf(p);
    const 落2 = await 独占像素(id);
    if (落2.__err) { rec.动作.push({ id, __err: '右键前独占像素 ' + 落2.__err }); continue; }
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
    if (del.__err) { rec.动作.push({ id, __err: del.__err }); continue; }
    await p.mouse.click(del.x, del.y);
    await p.waitForTimeout(2500);
    await settle(p, R);
    const 后 = await idsOf(p);
    rec.动作.push({ id, 删除项: del, 消失: 前.filter((x) => !后.includes(x)), 新增: 后.filter((x) => !前.includes(x)) });
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

await settle(p, R);
const 末 = await idsOf(p);
rec.收尾 = { 状态行: await R.status(), 节点数: 末.length, 组数: await 组数(p), 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), minimap: await R.minimap(), 积分: await R.credits(),
  剩余目标: 末.filter((x) => 目标.includes(x)) };
rec.是否干净 = 末.length === 76 && rec.收尾.剩余目标.length === 0;
fs.writeFileSync(new URL('./_tmp-b143-rescue.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 起点: rec.起点, 动作: rec.动作, 收尾: rec.收尾, 是否干净: rec.是否干净, 异常: rec.异常 }, null, 1));
await b.close();
