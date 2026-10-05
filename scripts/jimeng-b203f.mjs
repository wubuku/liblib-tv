/**
 * 批次 203 f 轮：追「节点中心点 elementFromPoint 命中了一个不在该节点里的元素」。
 *
 * e 轮实测：26% 与 50% 两档，目标节点 node_5gftn3dnt1 的包围盒中心点
 * elementFromPoint 都命中同一个 class：
 *   `relative flex min-h-canvas-zero flex-1 flex-col items-center ... px-canvas-director-stage-node-inline`
 * 且 `h.closest('.react-flow__node[data-id=node_5gftn3dnt1]')` === null
 *   ⇒ 那个元素**不在目标节点子树里**，却盖在目标节点的几何中心上。
 *
 * 本轮只问：
 *  ① 挡住的那个元素属于哪个 .react-flow__node（或者不属于任何节点）？
 *  ② 它的屏上盒子多大、z-index 多大、pointer-events 是什么？
 *  ③ 这种「盖住节点中心」是普遍的吗（扫 76 个节点逐个问同一句）？
 *  ④ 绕开被盖的区域，点节点内别的位置，能不能进编辑态？
 *
 * 全部只读：不新建/删除节点，不生成，不下载。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';
import { openCanvas, readers, settle, setZoom, endState, PORT } from './jimeng-b135-lib.mjs';

const TARGET = 'node_5gftn3dnt1';
const OUT = '/tmp/b203f.json';

/** 逐个节点问：中心点命中谁？命中元素在本节点内吗？ */
const 扫描 = (p) => p.evaluate((tid) => {
  const nodes = Array.from(document.querySelectorAll('.react-flow__node'));
  const rows = nodes.map((n) => {
    const id = n.getAttribute('data-id');
    const r = n.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const h = document.elementFromPoint(cx, cy);
    const owner = h ? h.closest('.react-flow__node') : null;
    const ownerId = owner ? owner.getAttribute('data-id') : null;
    return {
      id,
      屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      在视口内: r.right > 0 && r.x < innerWidth && r.bottom > 0 && r.y < innerHeight,
      中心命中testid: h ? h.getAttribute('data-testid') : null,
      中心命中所属节点: ownerId,
      中心在本节点内: h ? !!h.closest(`.react-flow__node[data-id="${id}"]`) : null,
    };
  });
  return rows;
}, TARGET);

/** 细看挡在目标节点中心上的那个元素。 */
const 看遮挡者 = (p) => p.evaluate((tid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${tid}"]`);
  const r = n.getBoundingClientRect();
  const h = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
  if (!h) return null;
  const box = (e) => { const b = e.getBoundingClientRect(); return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; };
  const owner = h.closest('.react-flow__node');
  const cs = getComputedStyle(h);
  return {
    命中元素: {
      tag: h.tagName, class: String(h.className || '').slice(0, 120), testid: h.getAttribute('data-testid'),
      aria: h.getAttribute('aria-label'), 屏上: box(h), pointerEvents: cs.pointerEvents, zIndex: cs.zIndex,
      position: cs.position, opacity: cs.opacity,
      祖先链: (() => { const c = []; for (let e = h; e && e !== document.body; e = e.parentElement) { const t = e.getAttribute && e.getAttribute('data-testid'); c.push(e.tagName.toLowerCase() + (t ? '[' + t + ']' : '') + (e.className ? '.' + String(e.className).split(' ')[0] : '')); } return c.slice(0, 10); })(),
    },
    所属节点: owner ? { id: owner.getAttribute('data-id'), aria: owner.getAttribute('aria-label'), 屏上: box(owner), 子孙关系: h.closest(`.react-flow__node[data-id="${tid}"]`) ? '在目标内' : '不在目标内' } : null,
    目标节点: { 屏上: box(n) },
  };
}, TARGET);

/** 在目标节点内找一个「没被盖住」的点，试双击进编辑态。 */
const 试编辑 = (p) => p.evaluate((tid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${tid}"]`);
  const r = n.getBoundingClientRect();
  const 候选 = [];
  for (let fy = 0.15; fy <= 0.9; fy += 0.15) for (let fx = 0.15; fx <= 0.9; fx += 0.15) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    const h = document.elementFromPoint(x, y);
    const ok = !!(h && h.closest(`.react-flow__node[data-id="${tid}"]`));
    候选.push({ 相对: [Math.round(fx * 100), Math.round(fy * 100)], 点: [x, y], 在节点内: ok, 命中: h ? (h.getAttribute('data-testid') || String(h.className || '').slice(0, 40)) : null });
  }
  return 候选;
}, TARGET);

const b = (p, k) => { console.error('⚠️ ' + k); };

const browser = await chromium.connectOverCDP({ endpointURL: `http://127.0.0.1:${PORT}` });
const ctx = browser.contexts()[0];
let p = ctx.pages().find((x) => /jimeng\.jianying\.com/.test(x.url())) || ctx.pages()[0];
const R = readers(p);

const out = { 轮次: 'b203f', 目标: TARGET };
await openCanvas();
await settle(p, R);
out.基线 = { ids: await R.ids(), testids: await R.testids() };

for (const z of [26, 50]) {
  const s = await setZoom(p, z);
  if (!s.scale已追平) b(p, `${z}% 没追平`);
  await p.waitForTimeout(500);
  out[`${z}%`] = {};
  out[`${z}%`].遮挡者 = await 看遮挡者(p);
  out[`${z}%`].候选点 = await 试编辑(p);
  out[`${z}%`].扫描统计 = await p.evaluate((rows) => {
    const 视口内 = rows.filter((r) => r.在视口内);
    const 被盖 = 视口内.filter((r) => r.中心在本节点内 === false);
    const 详情 = 被盖.slice(0, 8).map((r) => ({ id: r.id, 屏上: r.屏上, 命中所属节点: r.中心命中所属节点, 命中testid: r.中心命中testid }));
    return { 节点总数: rows.length, 视口内数: 视口内.length, 中心被盖数: 被盖.length, 详情 };
  }, await 扫描(p));
  console.error(`  ${z}%：视口内 ${out[`${z}%`].扫描统计.视口内数} 个，中心被盖 ${out[`${z}%`].扫描统计.中心被盖数} 个`);
}

// 挑一个在节点内的候选点双击，判能不能进编辑态
const z = 26;
const ok = out[`${z}%`].候选点.find((c) => c.在节点内);
if (ok) {
  await p.mouse.dblclick(ok.点[0], ok.点[1]);
  await p.waitForTimeout(1500);
  out[`${z}%`].双击 = {
    点的: ok,
    进入编辑态: await p.evaluate(() => Array.from(document.querySelectorAll('[contenteditable="true"],textarea')).filter((e) => e.offsetWidth > 0).length),
    textEditorToolbar: await p.evaluate(() => document.querySelectorAll('[data-testid="text-editor-toolbar"]').length),
    nodeToolbar: await p.evaluate(() => document.querySelectorAll('[data-testid="node-toolbar"]').length),
  };
  console.error(`  ${z}% 改点双击 → ${JSON.stringify(out[`${z}%`].双击)}`);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(800);
} else {
  out[`${z}%`].双击 = { 无效: '候选点里没有一个在节点内' };
}

const fin = await setZoom(p, 26);
out.收尾 = await endState(p, R, out.基线);
out.收尾.归位scale = fin.实测scale;

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
console.error(`写入 ${OUT}`);
console.log(JSON.stringify({ 遮挡者26: out['26%'].遮挡者, 扫描统计26: out['26%'].扫描统计, 扫描统计50: out['50%'].扫描统计, 候选点数26: out['26%'].候选点.length, 节点内候选26: out['26%'].候选点.filter((c) => c.在节点内).length, 双击: out['26%'].双击 }, null, 1));
// 🔴 不调 `browser.close()`：对 `connectOverCDP` 连上来的实例，`close()` 会挂住
//    （批次 203 e 轮实测：文件已落盘、命令却卡到 240s 超时）。
//    断开连接即可让脚本自己退出，浏览器实例留在 9444 继续常驻。
process.exit(0);
