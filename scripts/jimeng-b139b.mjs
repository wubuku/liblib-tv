// 批次 139 a 轮：建 3 个文本节点 → 框选 → 编组 → 首档读数。
//
// 本轮**不删组**（留给 b 轮做四档缩放）。归位走 `jimeng-b139-rescue.mjs`。
// ⚠️ 万一本轮崩在中途，组会留在共享画布上 —— 下一步先跑救援脚本再重跑本轮。
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 建N个, planBoxFor, doBox, 点选一组, 点编组, 读组态全, selIds, selCount, 组数, idsOf, canvasPos } from './jimeng-b139-lib.mjs';
import fs from 'node:fs';

const rec = { 轮: '139a' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { rec.断言 = rec.断言 || []; rec.断言.push({ 名, 通过: !!ok, 详情 }); if (!ok) 断言过 = false; };

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p), zoom: await R.zoom() };

  // ---- 建 3 个文本节点
  rec.建 = await 建N个(p, '文本', 3, 断言, 76);
  if (!(rec.建.ids && rec.建.ids.length === 3)) { rec.中止 = '建节点未成'; }
  else {
    // 建后几何：这决定了框选矩形能不能找到
    rec.建后几何 = await p.evaluate((W) => Array.from(document.querySelectorAll('.react-flow__node'))
      .filter((n) => W.includes(n.getAttribute('data-id')))
      .map((n) => { const r = n.getBoundingClientRect();
        return { id: n.getAttribute('data-id'), 屏上: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
          canvas: { w: n.offsetWidth, h: n.offsetHeight }, 逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16) }; }), rec.建.ids);
    rec.建后状态 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length };

    // ---- 选中这 3 个：先试框选，失败就换点选（两条路径都记进证据）
    const box = await planBoxFor(p, rec.建.ids);
    rec.框选计划 = box;
    let 选中方式 = null;
    if (box.ok) {
      const hit = await doBox(p, box.矩形);
      选中方式 = '框选';
      rec.框选 = { 命中: hit, 选中: await selIds(p), 选中数: await selCount(p) };
    } else {
      // 🔴 框选找不到就换点选，别一直加大搜索空间（批次 135 c 轮 / 本轮同一个教训的两半）
      const 点选 = await 点选一组(p, rec.建.ids);
      rec.点选 = 点选;
      选中方式 = '点选';
      if (!点选.ok) { rec.中止 = '点选也没成'; }
    }
    if (!rec.中止) {
      断言('③选中集合恰好等于这 3 个', JSON.stringify(await selIds(p)) === JSON.stringify([...rec.建.ids].sort()),
        { 选中方式, 选中: await selIds(p) });
    }
    if (!rec.中止 && 断言过) {
        // ---- 编组
        const g = await 点编组(p);
        rec.编组 = g;
        断言('④编组后组卡片恰好 1 个', g.ok, g);
        rec.编组后 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p) };
        // ---- 首档读数（当前缩放）
        rec.首档读数 = await 读组态全(p);
        rec.编组后canvas = await canvasPos(p);
      }
  }
} catch (e) {
  rec.异常 = String(e && e.stack || e).slice(0, 600);
}

await settle(p, readers(p));
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p),
  选中: await selCount(p), 浮层: await R.overlays(), zoom: await R.zoom() };
rec.断言全过 = 断言过;
fs.writeFileSync(new URL('./_tmp-b139a.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify(rec, null, 1));
await b.close();
