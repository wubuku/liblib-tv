// 批次 144 d 轮 —— 顺手验一个**候选公式**：节点选中态工具条的宽度。
//
// 🔑 线索来自一处**跨层漂移**：`SOURCE_OBSERVATIONS.md:744`（§3.14）至今写着选中态工具条
//   `185×40`，而批次 93 已在 `use-node-toolbar.md:40` 用**三档实测**把它推翻并订正：
//   40%→`160×40`、60%→`192×40`、100%→`320×40`（并登记台账 `toolbar-selected-185x40`）。
//   批次 144 c 轮在 60% 档独立复测到 `192×40` ⇒ **与批次 93 逐字一致**。
//
// 💡 那三档读数指向一个**从未被写下来**的公式。逐个反推 canvas 口径：
//   40% → 160 ÷ 0.4 = 400　　60% → 192 ÷ 0.6 = 320　　100% → 320 ÷ 1 = 320
//   ⇒ 两个高缩放档都落在 **canvas 恒 320**，而 40% 档比 320×0.4=128 大 ⇒ 落在**下限区**。
//   候选：**`屏上宽 = max(320 × scale, 160)`**，交叉点 `160÷320 = 50%`。
//   这与批次 139 的组工具条 `max(卡片canvas宽×scale, 296)` 是**同一个模板**
//   （批次 142 推翻的是「所有族共用一个模板」，不是「max 模板本身不成立」）。
//
// 📌 三档不足以定案 —— 必须在**交叉点两侧密布**。本轮取 7 档：
//   30 / 40 / 45 / 50 / 55 / 60 / 100%，并按纪律锁 `data-id` + 等实测 `scale()` 追平。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 144, 轮: 'd', 目的: '验节点选中态工具条宽度公式 max(320×scale,160)' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 档位 = [30, 40, 45, 50, 55, 60, 100];

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

/** 读可见工具条 + 实测 scale + 节点是否在视口内。 */
const 读一档 = (id) => p.evaluate((i) => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
  const scale = m ? Math.round(parseFloat(m[1]) * 1000) / 1000 : null;
  const tbs = Array.from(document.querySelectorAll('.react-flow__node-toolbar'))
    .map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((q) => q.r.width > 1 && q.r.height > 1)
    .sort((a, b) => b.r.width * b.r.height - a.r.width * a.r.height);
  const 节点 = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const nr = 节点 ? 节点.getBoundingClientRect() : null;
  const t = tbs[0];
  return {
    scale,
    工具条: t ? { 宽: Math.round(t.r.width * 100) / 100, 高: Math.round(t.r.height * 100) / 100,
      x: Math.round(t.r.x), y: Math.round(t.r.y),
      canvas宽: t.e.offsetWidth, canvas高: t.e.offsetHeight,
      按钮: Array.from(t.e.querySelectorAll('button,[role=button]')).map((e) => { const q = e.getBoundingClientRect();
        return { aria: e.getAttribute('aria-label'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(),
          盒: [Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10] }; }) } : null,
    可见工具条数: tbs.length,
    节点在视口: nr ? (nr.x >= 0 && nr.y >= 0 && nr.right <= innerWidth && nr.bottom <= innerHeight) : false,
    节点盒: nr ? [Math.round(nr.x), Math.round(nr.y), Math.round(nr.width), Math.round(nr.height)] : null,
    仍选中: !!(节点 && 节点.classList.contains('selected')),
  };
}, id);

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
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), minimap: await R.minimap() };

  const 建 = await 建N个(p, '文本', 1, 断言, 76);
  rec.建 = 建;
  const SELF = 建.ids && 建.ids[0];
  if (!SELF) { rec.中止 = '建节点未成'; }
  else {
    rec.各档 = [];
    for (const 目标 of 档位) {
      const z = await setZoom(p, 目标);
      await p.waitForTimeout(900);
      // 🔴 换缩放后**必须把鼠标移回节点**，否则工具条不出现（悬停触发）
      const 落 = await 独占像素(SELF);
      if (落.__err) { rec.各档.push({ 目标, __err: '独占像素 ' + 落.__err, zoom: z }); break; }
      await p.mouse.move(落.落点[0], 落.落点[1]);
      await p.waitForTimeout(1300);
      const 读 = await 读一档(SELF);
      const 期望max = Math.max(320 * 读.scale, 160);
      rec.各档.push({ 目标, setZoom: z, 实测scale: 读.scale, 仍选中: 读.仍选中,
        节点在视口: 读.节点在视口, 节点盒: 读.节点盒, 可见工具条数: 读.可见工具条数,
        工具条: 读.工具条, 预测max: Math.round(期望max * 100) / 100,
        canvas反推: 读.工具条 && 读.scale ? Math.round((读.工具条.宽 / 读.scale) * 100) / 100 : null });
    }
    // 复原缩放 + 重开小地图
    rec.复原 = await setZoom(p, 60);
    await p.waitForTimeout(1000);
    const 空 = await 找真空白();
    if (!空.__err) { await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1000); }
    rec.收尾zoom = await R.zoom();
    // 缩放会关小地图 —— 收尾必须重开
    const 小地图前 = await R.minimap();
    if (!小地图前 || 小地图前.ariaPressed !== 'true') {
      const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3);
      rec.小地图落点 = t;
      if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); }
    }
    rec.小地图后 = await R.minimap();

    // ---- 出表
    rec.表 = rec.各档.filter((q) => q.工具条).map((q) => ({
      目标: q.目标, 实测scale: q.实测scale, 工具条屏上宽: q.工具条.宽, 高: q.工具条.高,
      canvas口径: q.工具条.canvas宽, 屏上除以scale: q.canvas反推, 预测max: q.预测max,
      按钮数: (q.工具条.按钮 || []).length,
      按钮屏上: (q.工具条.按钮 || []).map((b) => b.盒[0]),
    }));
    // 🔴 `.every()` 之前必须有非空断言（批次 142 的空集通过教训）
    断言('① 七档至少读到 5 档工具条（防空集通过）', rec.表.length >= 5, { 实到: rec.表.length });
    if (rec.表.length >= 5) {
      断言('② 每档实测 scale 与目标逐档相符（±0.005）', rec.表.every((q) => Math.abs(q.实测scale - q.目标 / 100) <= 0.005), rec.表.map((q) => [q.目标, q.实测scale]));
      断言('③ 每档工具条高度恒 40', rec.表.every((q) => Math.abs(q.高 - 40) < 0.05), rec.表.map((q) => [q.目标, q.高]));
      断言('④ 每档工具条宽 == max(320×scale, 160)（±0.05）', rec.表.every((q) => Math.abs(q.工具条屏上宽 - q.预测max) <= 0.05), rec.表.map((q) => [q.目标, q.工具条屏上宽, q.预测max]));
      断言('⑤ 每档按钮数恒为 3', rec.表.every((q) => q.按钮数 === 3), rec.表.map((q) => [q.目标, q.按钮数]));
    }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

try { rec.删除 = []; for (const id of ((rec.建 && rec.建.ids) || [])) rec.删除.push(await 删一个(id));
} catch (e) { rec.删除异常 = String(e).slice(0, 300); }

await settle(p, R);
const 末 = await idsOf(p);
rec.收尾 = { 状态行: await R.status(), 节点数: 末.length, 选中: await selCount(p), 浮层: await R.overlays(),
  zoom: await R.zoom(), minimap: await R.minimap(), 积分: await R.credits(),
  剩余自建: 末.filter((x) => ((rec.建 && rec.建.ids) || []).includes(x)) };
rec.断言全过 = 断言过;
fs.writeFileSync(new URL('./_tmp-b144d.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 中止: rec.中止, 异常: rec.异常, 表: rec.表, 复原: rec.复原, 收尾zoom: rec.收尾zoom,
  小地图前: rec.小地图前, 小地图后: rec.小地图后, 删除: rec.删除, 收尾: rec.收尾 }, null, 1));
await b.close();
