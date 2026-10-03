// 批次 142 归位 g 轮：**用滚轮**把组从视口下方带进屏幕，再解组。
//
// 🔴 前七版全部失败，卡点始终同一个：组卡片屏上 `y=556..892`（视口高 720）
//   ⇒ **大半在屏幕外**，`elementFromPoint` 返 `null`，点不到。
//   上一版想用空白拖拽平移，实测**位置一字未变**（`canvas位移数 0`）——
//   因为空白处 mousedown 被 React Flow 解释成**框选**，不是平移。
//
// ✅ 本轮改用**滚轮**：手册记载滚轮可以平移画布。
//   滚轮**只改视图**（节点 canvas 坐标不动），比拖拽安全得多，也不会误建边。
//   每滚一格就**回读组的屏上 y**，直到它完全进入视口。
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 组数, idsOf, canvasPos, 可点落点 } from './jimeng-b139-lib.mjs';
import fs from 'node:fs';

const 基线 = fs.readFileSync('/tmp/b120-baseline-ids.txt', 'utf8').split('\n').map((s) => s.trim()).filter(Boolean);
const rec = { 滚动: [] };
const { b, p } = await openCanvas();
const R = readers(p);

const 组屏上 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group'))
  .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''))
  .map((g) => { const r = g.getBoundingClientRect();
    return { id: g.getAttribute('data-id'), y: Math.round(r.y), bottom: Math.round(r.bottom),
      x: Math.round(r.x), w: Math.round(r.width), h: Math.round(r.height),
      在视口内: r.top >= 70 && r.bottom <= innerHeight - 60 }; }));

try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p) };
  rec.canvas前 = await canvasPos(p);
  rec.视口 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
  rec.组起点 = await 组屏上(p);

  // 把鼠标放到画布中部（避开 dock 与顶栏），逐格滚动，把第一个组带进视口
  await p.mouse.move(640, 400);
  await p.waitForTimeout(400);
  for (let i = 0; i < 60; i++) {
    const gs = await 组屏上(p);
    const g0 = gs[0];
    rec.滚动.push({ i, 组y: g0 && g0.y, 在视口内: g0 && g0.在视口内 });
    if (g0 && g0.y >= 80 && g0.bottom <= 700) break;
    await p.mouse.wheel(0, 240);
    await p.waitForTimeout(320);
  }
  rec.滚动后 = await 组屏上(p);
  const 后 = await canvasPos(p);
  rec.canvas位移数 = Object.keys(后).filter((k) => JSON.stringify(后[k]) !== JSON.stringify(rec.canvas前[k])).length;
  rec.状态行 = await R.status();

  // ---- 组进视口后：点中心 → 选中 → 解除编组
  rec.解组 = [];
  for (const g of rec.滚动后 || []) {
    const cx = Math.round(g.x + g.w / 2);
    const cy = Math.max(90, Math.min(690, Math.round(g.y + g.h / 2)));
    const 命中 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y);
      return h ? (h.tagName + '.' + String(h.className || '').split(' ')[0]).slice(0, 44) : null; }, [cx, cy]);
    await p.mouse.click(cx, cy);
    await p.waitForTimeout(1400);
    const 选中组 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group'))
      .filter((q) => !/^__group-resize-chrome__/.test(q.getAttribute('data-id') || ''))
      .filter((q) => q.classList.contains('selected')).length);
    rec.解组.push({ id: g.id, 点: [cx, cy], 命中, 点后选中组: 选中组 });
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
fs.writeFileSync(new URL('./_tmp-b142-ungroup5.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log('起点', JSON.stringify(rec.起点), '| 组起点', JSON.stringify(rec.组起点));
console.log('滚动轨迹', JSON.stringify(rec.滚动));
console.log('滚动后', JSON.stringify(rec.滚动后), '| canvas位移数', rec.canvas位移数);
console.log('解组', JSON.stringify(rec.解组, null, 1));
console.log('末尾', JSON.stringify(rec.末尾), '| 差集', JSON.stringify(rec.与基线差集));
await b.close();
