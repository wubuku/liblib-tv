/**
 * 批次 203 i 轮：分清「`.selected` class 滞后」与「这个 class 压根不出现」。
 *
 * h 轮 26% 档读到的分裂状态：
 *   点一下 compact 文本节点 → 描述宿主从 `text-flow-node-compact`（第一层）
 *   换成 `text-flow-node-full`（第二层），但 `.react-flow__node.selected`
 *   这个 class **一个都没有**（`选中集 = []`）。
 *
 * 两种可能，不能混：
 *   A. class 会加上，只是**晚于**变体切换（滞后）
 *   B. 这个 class 在这条路径上**根本不会出现**
 *
 * 判据：点击后按时间点采样，看 `selected` 出现的时间戳相对变体切换是早是晚还是永不出现。
 * 顺带把画布归位到 0 选中（h 轮收尾还剩 1 个选中）。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';
import { openCanvas, readers, settle, setZoom, endState, PORT } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b203i.json';
const T1 = 'node_5gftn3dnt1';

const 采样 = (p) => p.evaluate((tid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${tid}"]`);
  const db = n ? n.getAttribute('aria-describedby') : null;
  const host = db ? document.getElementById(db) : null;
  return {
    宿主testid: host ? host.getAttribute('data-testid') : null,
    宿主父就是节点根: host ? host.parentElement === n : null,
    selected类: n ? n.classList.contains('selected') : null,
    节点class: n ? Array.from(n.classList).filter((c) => c !== '').slice(0, 8) : null,
    选中集: document.querySelectorAll('.react-flow__node.selected').length,
    selected族: Array.from(document.querySelectorAll('[class*="selected"]')).slice(0, 6).map((e) => (e.getAttribute('data-testid') || e.tagName) + '|' + Array.from(e.classList).filter((c) => /selected/.test(c)).join('.')),
    编辑态工具条: document.querySelectorAll('[data-testid="text-editor-toolbar"]').length,
    编辑面: Array.from(document.querySelectorAll('[contenteditable="true"],textarea')).filter((e) => e.offsetWidth > 0).length,
  };
}, T1);

/** 在节点内找一个真能命中的点。 */
const 点 = (p, id) => p.evaluate((tid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${tid}"]`);
  const r = n.getBoundingClientRect();
  for (let fy = 0.15; fy <= 0.9; fy += 0.15) for (let fx = 0.15; fx <= 0.9; fx += 0.15) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    const h = document.elementFromPoint(x, y);
    if (h && h.closest(`.react-flow__node[data-id="${tid}"]`)) return { x, y };
  }
  return null;
}, id);

const browser = await chromium.connectOverCDP({ endpointURL: `http://127.0.0.1:${PORT}` });
const ctx = browser.contexts()[0];
let p = ctx.pages().find((x) => /jimeng\.jianying\.com/.test(x.url())) || ctx.pages()[0];
const R = readers(p);

const out = { 轮次: 'b203i', 时间序列: [], 证据: [] };
await openCanvas();
await settle(p, R);
out.基线 = { ids: await R.ids(), testids: await R.testids() };

await setZoom(p, 26);
await p.mouse.click(1276, 716);
await p.waitForTimeout(1200);
out.前置 = { 断言: { 判据: '点画布空白后选中集为 0', 实测: await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length) } };
out.前置.前置采样 = await 采样(p);

const pt = await 点(p, T1);
out.点位 = pt;
if (pt) {
  await p.mouse.click(pt.x, pt.y);
  for (const ms of [50, 200, 500, 1000, 2000, 4000]) {
    await p.waitForTimeout(ms === 50 ? 50 : ms - (out.时间序列.length ? [50, 200, 500, 1000, 2000, 4000][out.时间序列.length - 1] : 0));
    const s = await 采样(p);
    out.时间序列.push({ 累计ms: ms, ...s });
    console.error(`  ${ms}ms → 宿主=${s.宿主testid} selected类=${s.selected类} 选中集=${s.选中集} 编辑面=${s.编辑面}`);
  }
}

// 二次单击：点已经变 full 的同一位置，看会不会进编辑态 / selected 会不会出现
if (pt) {
  await p.mouse.dblclick(pt.x, pt.y);
  await p.waitForTimeout(1500);
  out.二次双击 = await 采样(p);
  console.error(`  二次双击 → ${JSON.stringify(out.二次双击)}`);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(900);
}

// 归位：清选中 + 26%
await p.mouse.click(1276, 716);
await p.waitForTimeout(1000);
const fin = await setZoom(p, 26);
out.收尾 = await endState(p, R, out.基线);
out.收尾.归位scale = fin.实测scale;
out.收尾.末尾选中 = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
console.error(`写入 ${OUT}`);
console.log(JSON.stringify({ 前置: out.前置, 时间序列: out.时间序列, 二次双击: out.二次双击, 末尾选中: out.收尾.末尾选中 }, null, 1));
process.exit(0);
