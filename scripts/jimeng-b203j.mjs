/**
 * 批次 203 j 轮：补 i 轮留下的一格 —— 第二次「单击」会不会选中。
 *
 * i 轮实测：26% 档下第一次单击只把节点从 compact 展开成 full（六个时间点
 * `.selected` 恒 false）；第二次是**双击**，一下同时给了「选中 + 进编辑态」，
 * ⇒ 分不清「选中」到底是第二次单击给的，还是双击特有的。
 *
 * 本轮把第二次动作拆开：单击 → 单击 → 双击，各读一次。
 * 目标是把用户手册里那句话写准：「点一下会发生什么、再点一下会发生什么」。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';
import { openCanvas, readers, settle, setZoom, endState, PORT } from './jimeng-b135-lib.mjs';

const OUT = '/tmp/b203j.json';
const T1 = 'node_5gftn3dnt1';

const 采样 = (p) => p.evaluate((tid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${tid}"]`);
  const db = n ? n.getAttribute('aria-describedby') : null;
  const host = db ? document.getElementById(db) : null;
  const cnt = (t) => document.querySelectorAll(`[data-testid="${t}"]`).length;
  return {
    宿主testid: host ? host.getAttribute('data-testid') : null,
    selected类: n ? n.classList.contains('selected') : null,
    选中集: document.querySelectorAll('.react-flow__node.selected').length,
    选中态工具条: cnt('node-toolbar'),
    编辑态工具条: cnt('text-editor-toolbar'),
    编辑面: Array.from(document.querySelectorAll('[contenteditable="true"],textarea')).filter((e) => e.offsetWidth > 0).length,
    编辑面在节点内: (() => { const ed = Array.from(document.querySelectorAll('[contenteditable="true"]')).find((e) => e.offsetWidth > 0); return ed ? !!n.contains(ed) : null; })(),
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

const 保持点 = (p, id) => p.evaluate((tid) => {
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

const out = { 轮次: 'b203j', 步骤: [] };
await openCanvas();
await settle(p, R);
out.基线 = { ids: await R.ids(), testids: await R.testids() };

await setZoom(p, 26);
await p.mouse.click(1276, 716);
await p.waitForTimeout(1200);
out.前置断言 = { 判据: '点画布空白后选中集为 0', 实测: await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length) };

const 记 = async (名) => { const s = await 采样(p); out.步骤.push({ 步骤: 名, ...s }); console.error(`  ${名} → 宿主=${s.宿主testid} selected=${s.selected类} 选中集=${s.选中集} 选中条=${s.选中态工具条} 编辑条=${s.编辑态工具条} 编辑面=${s.编辑面}`); return s; };

await 记('① 前置（未点过）');
let pt = await 点(p, T1); out.第一击点位 = pt;
await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1200); await 记('② 第一次单击');
pt = await 保持点(p, T1); out.第二击点位 = pt;
await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1200); await 记('③ 第二次单击');
pt = await 保持点(p, T1); out.第三击点位 = pt;
await p.mouse.dblclick(pt.x, pt.y); await p.waitForTimeout(1500); await 记('④ 第三次双击');
await p.keyboard.press('Escape'); await p.waitForTimeout(900); await 记('⑤ Esc 之后');

// 50% 档对照：单击一次会怎样（26% 有「展开」这一步，50% 没有 compact）
await setZoom(p, 50); await p.mouse.click(1276, 716); await p.waitForTimeout(1200);
pt = await 点(p, T1);
out.五十档点位 = pt;
await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1200);
out.步骤.push({ 步骤: '⑥ 50% 档单击一次', ...(await 采样(p)), 点位: pt });
console.error(`  ⑥ 50% 单击 → ${JSON.stringify(out.步骤[out.步骤.length - 1])}`);

await p.mouse.click(1276, 716); await p.waitForTimeout(1000);
const fin = await setZoom(p, 26);
out.收尾 = await endState(p, R, out.基线);
out.收尾.归位scale = fin.实测scale;
out.收尾.末尾选中 = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
console.error(`写入 ${OUT}`);
console.log(JSON.stringify({ 前置断言: out.前置断言, 步骤: out.步骤, 末尾选中: out.收尾.末尾选中, 状态行: out.收尾.状态行 }, null, 1));
process.exit(0);
