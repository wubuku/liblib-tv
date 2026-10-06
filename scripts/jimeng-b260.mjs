/**
 * 批次 260 · 探路：**改视口宽但不重新加载**，应用会不会自己重算「初次自适应」？
 *
 * 📌 背景（批次 259）：`适配画布` 的公式已闭合
 *   （`min((视口宽−200)/4091.4, (视口高−160)/2520.5)`），
 *   而**初次自适应**的绑定轴单边留白是 `31.0 / 40.0 / 50.0 / 32.0`
 *   —— **不是常数**，也没有一条简单比例套得住 ⇒ **规则未闭合**。
 *
 * 📌 本步只做**一件很便宜的事**，它决定后面能不能做得快：
 *   在**同一个页面**里连续改 `setViewportSize`，看缩放会不会跟着变。
 *   · 会变 ⇒ 应用**在 resize 时重算适配** ⇒ 后面可以在**一页**里扫几十个宽度，
 *     把「现象宽度」先量出来再定步长（立规 129），**不必每个宽度都开一次页**；
 *   · 不会变 ⇒ 初次适配只在**加载时**算一次 ⇒ 只能一宽度一页面地扫（慢，但可行）。
 *
 * 📌 顺带把**每个宽度的四边留白**记下来 —— 若重算发生，留白曲线本身就是答案的一半。
 *
 * 🔴 纪律：只改视口大小（纯视图）；不新建、不删除、不上传、不触发生成、不进扣费页、
 *   不点「保存到主体库」、不分享。
 *
 * 用法：node scripts/jimeng-b260.mjs      （读数落盘 /tmp/b260.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B260_OUT || '/tmp/b260.json';
const 高 = 720;
// 🔴 探路用的宽：刻意跨过批次 259 测到的绑定轴切换点（`1100 → 1400`）
const 宽表 = [700, 800, 900, 1000, 1100, 1150, 1200, 1250, 1300, 1350, 1400, 1450, 1500, 1600];

const log = (...a) => console.log(a.join(' '));

const 量 = () => {
  const W = window.innerWidth, H = window.innerHeight;
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const rs = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
  if (!rs.length) return { 视口: [W, H], scale: null, 节点数: 0 };
  const 左 = Math.min(...rs.map((r) => r.left));
  const 右 = Math.max(...rs.map((r) => r.right));
  const 上 = Math.min(...rs.map((r) => r.top));
  const 下 = Math.max(...rs.map((r) => r.bottom));
  const 四舍 = (v) => Math.round(v * 100) / 100;
  return {
    视口: [W, H],
    scale: m ? Number(m[1]) : null,
    节点数: rs.length,
    留白: { 左: 四舍(左), 右: 四舍(W - 右), 上: 四舍(上), 下: 四舍(H - 下) },
  };
};

const out = { 轮次: 'b260-探路', 高, 宽表, 行: [], 会重算: null };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = await ctx.newPage();
try {
  await p.setViewportSize({ width: 宽表[0], height: 高 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(6500);

  for (const 宽 of 宽表) {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.waitForTimeout(1500);
    const r = await p.evaluate(量);
    out.行.push({ 宽, ...r });
    log(`  w=${String(宽).padStart(4)} scale=${String(r.scale).padEnd(10)} 留白=${JSON.stringify(r.留白)} 节点=${r.节点数}`);
  }

  const 缩放集 = [...new Set(out.行.map((r) => r.scale))];
  out.会重算 = 缩放集.length > 1;
  log('=== 探路结论 ===');
  log(`同一页里 ${宽表.length} 个宽度读出 ${缩放集.length} 个不同的 scale ⇒ **${out.会重算 ? '会重算（可以在一页里扫）' : '不会重算（只能一宽度一页地扫）'}**`);
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
} catch (e) {
  out.错误 = e.message;
  log('🔴 ' + e.message);
} finally {
  try { await p.close(); } catch (e) { /* 忽略 */ }
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  log('写入 ' + OUT);
}
// 🔴 不要 `b.close()`：那会把无头浏览器一起关掉（批次 249 踩过）
process.exit(0);