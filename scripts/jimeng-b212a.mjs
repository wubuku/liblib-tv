/**
 * 批次 212 a 轮：量画布**平移边界**（translateExtent）——
 * 这是解开「纵向落点为什么是 360 / ≈258 / ≈390」的唯一一把钥匙。
 *
 * 批次 211 留下的谜：
 *   · 同一宽度下，`音频 68`（画布右下）取景把缩放降到 26~49%，`文本 3`（画布左上）恒 50%
 *   · 纵向落点随节点走：`360`（音频68 @w≤1210）／`≈257~260`（音频68 @w≥1212）／`≈390`（文本3）
 *   · 已排除：慢收敛（30 秒连采）、侧栏出现/消失、响应式断点
 *   ⇒ 剩下的最强嫌疑是 **react-flow 的 translateExtent 夹取**
 *     （把视口限制在内容包围盒内，于是「把节点放到中心」这个目标在某些位置做不到）
 *
 * 📌 本轮不去猜，直接量边界：
 *   在 26% 与 50% 两档，用「拖 .react-flow__pane 空白处」把画布往四个方向推到底，
 *   记录每档能达到的 tx/ty 极值 ⇒ 换算成画布坐标区间 = translateExtent。
 *   判据：极值处若还留有「还能再推」的余量，就说明没到边界。
 *
 * 📌 立规 82：每次拖之前都要重新找一个「elementFromPoint 命中 .react-flow__pane 的点」，
 *   因为画布一动，原来的空白点可能已经落在某个节点上。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';
import { openCanvas, readers, settle, setZoom, endState, PORT } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b212a.json';

const 读vp = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  return { tx: m ? Number(m[1]) : null, ty: m ? Number(m[2]) : null, s: m ? Number(m[3]) : null };
});

/** 找一个真的落在 pane 空白上的点（立规 82 的归属判据反过来用：必须**不**属于任何节点）。 */
const 找空白 = (p) => p.evaluate(() => {
  for (let y = 80; y < innerHeight - 80; y += 12) {
    for (let x = 40; x < innerWidth - 40; x += 12) {
      const h = document.elementFromPoint(x, y);
      if (h && h.classList && h.classList.contains('react-flow__pane') && !h.closest('.react-flow__node')) return { x, y };
    }
  }
  return null;
});

/** 从 (x,y) 拖到 (x+dx, y+dy)，落点也要求在 pane 上（否则会被当成拖节点）。 */
const 拖 = async (p, dx, dy) => {
  const a = await 找空白(p);
  if (!a) return { 无效: '找不到 pane 空白点' };
  const b = await p.evaluate(([x0, y0, ddx, ddy]) => {
    const tx = x0 + ddx, ty = y0 + ddy;
    if (tx < 0 || ty < 0 || tx > innerWidth || ty > innerHeight) return null;
    const h = document.elementFromPoint(tx, ty);
    if (!h || !h.classList || !h.classList.contains('react-flow__pane')) return null;
    return { x: tx, y: ty };
  }, [a.x, a.y, dx, dy]);
  if (!b) return { 无效: `落点 (${a.x + dx},${a.y + dy}) 不在 pane 上`, 起: a };
  await p.mouse.move(a.x, a.y);
  await p.mouse.down();
  await p.mouse.move(b.x, b.y, { steps: 18 });
  await p.mouse.up();
  await p.waitForTimeout(700);
  return { 起: a, 落: b, vp: await 读vp(p) };
};

const browser = await chromium.connectOverCDP({ endpointURL: `http://127.0.0.1:${PORT}` });
const ctx = browser.contexts()[0];
let p = ctx.pages().find((x) => /jimeng\.jianying\.com/.test(x.url())) || ctx.pages()[0];
const R = readers(p);

const out = { 轮次: 'b212a', 档: {} };
await openCanvas();
await settle(p, R);
out.基线 = { ids: await R.ids(), testids: await R.testids() };
out.画布包围盒 = { xmin: 40.0555, xmax: 3562.42, ymin: 240, ymax: 2440.49, 中心: [1801.23775, 1340.245] };

for (const z of [26, 50]) {
  const s = await setZoom(p, z);
  const 档 = { 实测scale: s.实测scale, scale已追平: s.scale已追平, 初: await 读vp(p), 四向: {} };
  console.error(`\n【${z}%】初 ${JSON.stringify(档.初)}`);

  // 四个方向各推一次；每推完回到初态不可能，所以逐次累加取极值
  const 极值 = { txmin: Infinity, txmax: -Infinity, tymin: Infinity, tymax: -Infinity };
  const 记 = (v) => {
    if (!v || !v.vp) return;
    极值.txmin = Math.min(极值.txmin, v.vp.tx); 极值.txmax = Math.max(极值.txmax, v.vp.tx);
    极值.tymin = Math.min(极值.tymin, v.vp.ty); 极值.tymax = Math.max(极值.tymax, v.vp.ty);
  };
  记(档.初);

  for (const [名, dx, dy] of [['右', 900, 0], ['左', -900, 0], ['下', 0, 500], ['上', 0, -500]]) {
    const r = await 拖(p, dx, dy);
    档.四向[名] = r;
    if (r.vp) { 记(r); console.error(`   推${名} → tx=${r.vp.tx} ty=${r.vp.ty} s=${r.vp.s}`); }
    else console.error(`   推${名} ⛔ ${r.无效}`);
  }
  // 再来一轮，确认四个极值都真的到边（第二次推同一个方向应该几乎不动）
  档.二次确认 = {};
  for (const [名, dx, dy] of [['右', 900, 0], ['左', -900, 0], ['下', 0, 500], ['上', 0, -500]]) {
    const before = await 读vp(p);
    const r = await 拖(p, dx, dy);
    档.二次确认[名] = { 拖前: before, 拖后: r.vp || r.无效,
      位移: r.vp ? [Math.round((r.vp.tx - before.tx) * 1000) / 1000, Math.round((r.vp.ty - before.ty) * 1000) / 1000] : null };
    if (r.vp) 记(r);
    console.error(`   二次推${名} → 位移 ${JSON.stringify(档.二次确认[名].位移)}（≈0 表示已到边界）`);
  }
  档.极值 = 极值;
  // 换算成画布坐标区间
  const sc = 档.实测scale, W = 1280, H = 720;
  档.可见画布区间 = {
    x: [Math.round(-极值.txmax / sc * 100) / 100, Math.round((W - 极值.txmin) / sc * 100) / 100],
    y: [Math.round(-极值.tymax / sc * 100) / 100, Math.round((H - 极值.tymin) / sc * 100) / 100],
  };
  console.error(`   极值 ${JSON.stringify(极值)}`);
  console.error(`   可见画布区间 ${JSON.stringify(档.可见画布区间)}`);
  out.档[z] = 档;
}

const fin = await setZoom(p, 26);
out.收尾 = await endState(p, R, out.基线);
out.收尾.归位scale = fin.实测scale;
out.收尾.末尾选中 = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
console.error(`\n写入 ${OUT}`);
console.log(JSON.stringify(Object.fromEntries(Object.entries(out.档).map(([z, g]) => [z, {
  scale: g.实测scale, 极值: g.极值, 可见画布区间: g.可见画布区间,
  二次位移: Object.fromEntries(Object.entries(g.二次确认).map(([k, v]) => [k, v.位移])),
}])), null, 1));
process.exit(0);
