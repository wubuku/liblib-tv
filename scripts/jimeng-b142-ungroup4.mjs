// 批次 142 归位 f 轮：**平移视口**把两个组从视口外拖回屏幕内，然后解组删组。
//
// 🔑 **真根因终于清楚**（前六版都在错的假设上打转）：
//   组卡片屏上位置是 `y=724` 与 `y=748` —— **视口高只有 720**！
//   它们**整个在屏幕下方之外**，所以：
//     · `elementFromPoint` 返回 `null`（坐标越界）；
//     · `getBoundingClientRect()` 仍能给出盒子，于是「看起来有卡片」，实际点不到；
//     · 之前那轮「适配画布 ⇧1」把它推到 **20%** 缩放、两个组完全重叠 —— 适得其反。
//   ⇒ **这不是「点不到」，是「不在屏幕里」。** 归位第一步应当是**把对象弄进视口**。
//
// ✅ 本轮做法：**用空白处拖拽平移画布**（只改视图，节点 canvas 坐标不动），
//   把组的屏上 y 从 724/748 拖到 ~300，然后按已验成的路径操作：
//   点组卡片中心 → 选中 → 工具条「解除编组」。
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 组数, idsOf, canvasPos, 可点落点 } from './jimeng-b139-lib.mjs';
import fs from 'node:fs';

const 基线 = fs.readFileSync('/tmp/b120-baseline-ids.txt', 'utf8').split('\n').map((s) => s.trim()).filter(Boolean);
const rec = {};
const { b, p } = await openCanvas();
const R = readers(p);

const 找空地 = (p) => p.evaluate(() => {
  const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
  for (let y = 640; y >= 120; y -= 8)
    for (let x = 360; x <= innerWidth - 360; x += 12) {
      const h = document.elementFromPoint(x, y);
      if (h && h.classList && h.classList.contains('react-flow__pane')
        && !nodes.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return { x, y };
    }
  return null;
});

try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p) };
  rec.canvas前 = await canvasPos(p);
  rec.组起点 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group'))
    .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''))
    .map((g) => { const r = g.getBoundingClientRect();
      return { id: g.getAttribute('data-id'), 屏上: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) } }; }));
  rec.视口 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));

  // ---- 平移：把组往上带
  const 空 = await 找空地(p);
  rec.平移起点 = 空;
  if (空) {
    // 需要移动的像素 = 让第一个组的中心落到屏幕中部
    const g0 = rec.组起点[0];
    const 目标y = 320;
    const dy = 目标y - (g0.屏上.y + g0.屏上.h / 2);
    const dx = 0;
    rec.平移量 = { dx, dy };
    await p.mouse.move(空.x, 空.y);
    await p.mouse.down();
    for (let i = 1; i <= 12; i++) {
      await p.mouse.move(Math.round(空.x + (dx * i) / 12), Math.round(空.y + (dy * i) / 12));
      await p.waitForTimeout(30);
    }
    await p.mouse.up();
    await p.waitForTimeout(1600);
    await settle(p, R);
  }
  rec.平移后组 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group'))
    .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''))
    .map((g) => { const r = g.getBoundingClientRect();
      return { id: g.getAttribute('data-id'), 屏上: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
        在视口内: r.top >= 0 && r.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth,
        中心命中: (() => { const h = document.elementFromPoint(Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2));
          return h ? (h.tagName + '.' + String(h.className || '').split(' ')[0]).slice(0, 44) : null; })() }; }));
  // 🔑 平移只改视图：节点 canvas 坐标必须零变化
  const 后 = await canvasPos(p);
  rec.canvas位移数 = Object.keys(后).filter((k) => JSON.stringify(后[k]) !== JSON.stringify(rec.canvas前[k])).length;

  // ---- 现在点组中心 → 选中 → 解除编组
  rec.解组 = [];
  for (const g of rec.平移后组 || []) {
    if (!g.在视口内) { rec.解组.push({ id: g.id, 跳过: '仍不在视口内' }); continue; }
    const cx = Math.round(g.屏上.x + g.屏上.w / 2), cy = Math.round(g.屏上.y + g.屏上.h / 2);
    await p.mouse.click(cx, cy);
    await p.waitForTimeout(1400);
    const 选中组 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group'))
      .filter((q) => !/^__group-resize-chrome__/.test(q.getAttribute('data-id') || ''))
      .filter((q) => q.classList.contains('selected')).length);
    rec.解组.push({ id: g.id, 点: [cx, cy], 中心命中: g.中心命中, 点后选中组: 选中组 });
    if (选中组 > 0) {
      const 解 = await 可点落点(p, '[data-toolbar-value="ungroup"]', 3, 3);
      rec.解组[rec.解组.length - 1].解除编组落点 = 解;
      if (!解.__err) {
        await p.mouse.click(解.x, 解.y);
        await p.waitForTimeout(2500);
        await settle(p, R);
        rec.解组[rec.解组.length - 1].解后组数 = await 组数(p);
      }
    }
  }
  const 终 = await idsOf(p);
  rec.末尾 = { 状态行: await R.status(), 节点数: 终.length, 组数: await 组数(p) };
  rec.与基线差集 = { 多: 终.filter((x) => !基线.includes(x) && !/^__group-resize-chrome__/.test(x)), 少: 基线.filter((x) => !终.includes(x)) };
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 600); }
fs.writeFileSync(new URL('./_tmp-b142-ungroup4.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log('起点', JSON.stringify(rec.起点), '| 视口', JSON.stringify(rec.视口));
console.log('组起点', JSON.stringify(rec.组起点));
console.log('平移量', JSON.stringify(rec.平移量), '| canvas位移数', rec.canvas位移数);
console.log('平移后组', JSON.stringify(rec.平移后组, null, 1));
console.log('解组', JSON.stringify(rec.解组, null, 1));
console.log('末尾', JSON.stringify(rec.末尾), '| 差集', JSON.stringify(rec.与基线差集));
await b.close();
