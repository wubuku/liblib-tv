/**
 * 批次 295 · 前置转储：把画布上「每一个」节点的精确 aria-label、data-id、盒尺寸全量读出来。
 *
 * 🔴 起意：批次 294 记下的参照节点名「音频 68」经批次 295 复跑暴露是**记错了**——
 *    DOM 里 aria-label 的真实形态是「<kind> node: <短名>」（例：`音频 node: 音频 1`），
 *    而「音频 68」在手册里大量出现的地方**指的是「节点 N」面板里的计数**
 *    （这一类有 68 个），两者字面相同、含义不同 ⇒ b294 用前缀 `音频` 找到的是
 *    `音频 node: 音频 1`（node_ay7f1jn45r），不是「音频 68」。
 *    ⇒ 本脚本不预设任何节点名，只负责把真值原样搬出来。
 *
 * 前提检查：
 *   ① 轴向自检：innerWidth/innerHeight 必须等于设定值，否则整组作废；
 *   ② 标签取自 DOM（aria-label），一字不改、不trim 之外不做任何加工；
 *   ③ 盒用 offsetWidth/offsetHeight（= 画布空间布局尺寸，立规 174，不再除 zoom）；
 *   ④ 顺手算一遍闭式 vs，仅作对照打印，不作判决。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const w = 1212;
const 高 = 720;
const OUT = '/tmp/b295-dump.json';

const 屏上律 = (ww) => Math.max(100, ww - 532);
const 安全高 = 高 - 160;
const vf = (z) => Math.min(8, Math.max(0.08, z));
const 闭式 = (W, H) => +vf(Math.min(屏上律(w) / W, 安全高 / H)).toFixed(6);

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = await ctx.newPage();
const out = { 轮次: 'b295-dump', w, h: 高 };

await p.setViewportSize({ width: w, height: 高 });
await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForSelector('.react-flow__node', { timeout: 45000 });
await p.waitForTimeout(6000);

// 前提①：轴向自检
const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
out.轴向自检 = 实际.w === w && 实际.h === 高 ? 'PASS' : 'FAIL';
if (out.轴向自检 === 'FAIL') throw new Error(`轴向自检失败：${实际.w}x${实际.h}`);

out.节点 = await p.evaluate(() => {
  const 全 = Array.from(document.querySelectorAll('.react-flow__node[data-id]'));
  return 全.map((e) => ({
    id: e.dataset.id,
    aria: e.getAttribute('aria-label'),
    // 前提③：offsetWidth/offsetHeight 就是画布空间布局尺寸
    W: e.offsetWidth,
    H: e.offsetHeight,
    text: (e.textContent || '').trim().slice(0, 40),
  }));
});

// 前提②的对照：把 aria 拆成 kind / 短名（只拆不改，原文另存）
const 类统计 = {};
for (const n of out.节点) {
  const m = /^(.*?) node: (.*)$/.exec(n.aria || '');
  const kind = m ? m[1] : '（不匹配 <kind> node: <名> 形态）';
  const 名 = m ? m[2] : (n.aria || '');
  const k = (类统计[kind] ||= { 个数: 0, 盒: {}, 名样: [], 闭式: {} });
  k.个数++;
  const bk = n.W + 'x' + n.H;
  k.盒[bk] = (k.盒[bk] || 0) + 1;
  if (k.名样.length < 4) k.名样.push(名);
  k.闭式[bk] = 闭式(n.W, n.H);
}
out.类统计 = 类统计;
out.节点数 = out.节点.length;

for (const [k, v] of Object.entries(类统计)) {
  console.log(`${k.padEnd(8)} ×${String(v.个数).padStart(2)}  盒 ${JSON.stringify(v.盒)}  闭式 ${JSON.stringify(v.闭式)}  名样 ${JSON.stringify(v.名样)}`);
}
console.log('总节点', out.节点数, '｜轴向自检', out.轴向自检);

const pz = await ctx.newPage();
try {
  await pz.setViewportSize({ width: 1280, height: 720 });
  await pz.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await pz.waitForSelector('.react-flow__node', { timeout: 45000 });
  await pz.waitForTimeout(6000);
  out.末态 = await pz.evaluate(() => ({
    节点数: document.querySelectorAll('.react-flow__node').length,
    状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
    积分: (document.querySelector('[data-testid="canvas-commerce-entry"]') || {}).textContent || null,
  }));
  console.log('末态独立复查：', JSON.stringify(out.末态));
} finally { try { await pz.close(); } catch (e) { /* 忽略 */ } }

await p.close();
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log('写入', OUT);
process.exit(0);
