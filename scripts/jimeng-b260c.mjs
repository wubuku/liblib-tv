/**
 * 批次 260 · 第三步：**「纵向留白 = 32」是固定值，还是比例？换高度一测就知道。**
 *
 * 📌 扫描（b260b，`14` 档宽度）已经确定：
 *   · 隐含包围盒**逐档恒为 `4091.2 × 2520.5`** —— 与批次 259 的 `适配画布` **同一个盒子**；
 *   · **纵向**留白在 `w ≥ 1220` **逐字饱和在 `32.00`**；
 *   · **横向**留白随视口宽增长（`29.01 → 30.01 → 32.01 → … → 52.02`），
 *     比例在 `0.0444`–`0.0462` 之间抖动（受整数取整影响），**不是常数**。
 *
 * 🔴 但「纵向 `32`」有两种读法，**必须分开**：
 *   ① **固定 `32px`**；
 *   ② **比例**：`32 / 720 = 2/45` ⇒ 高度变了它跟着变。
 *   ⇒ **判据：把 `H` 换掉**（此前所有批次的高度恒为 `720`，这是一条全新轴）。
 *     留白**逐字仍是 `32`** ⇒ 固定；**随 `H` 变** ⇒ 比例。
 *
 * 📌 顺带把 `H` 这一列的**隐含包围盒**也重算一遍 ——
 *   若包围盒**不随 `H` 变**（应当如此），说明「初次自适应 = 固定盒子 × padding」这个结构本身是稳的。
 *
 * 🔴 纪律：每档开新页、只读 DOM；只改视口大小（纯视图）；
 *   不新建、不删除、不上传、不触发生成、不进扣费页、不点「保存到主体库」、不分享。
 *
 * 用法：node scripts/jimeng-b260c.mjs      （读数落盘 /tmp/b260c.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B260C_OUT || '/tmp/b260c.json';
// 🔴 宽固定在 `1400`（扫描里已证：`w ≥ 1220` 时**纵向**才是绑定轴）
const 宽 = 1400;
const 高表 = [360, 540, 720, 900, 1080, 1440];

const log = (...a) => console.log(a.join(' '));

const 量 = () => {
  const W = window.innerWidth, H = window.innerHeight;
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const rs = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
  if (!rs.length) return { scale: null, 节点数: 0 };
  const 四舍 = (v) => Math.round(v * 100) / 100;
  const 左 = 四舍(Math.min(...rs.map((r) => r.left)));
  const 右 = 四舍(W - Math.max(...rs.map((r) => r.right)));
  const 上 = 四舍(Math.min(...rs.map((r) => r.top)));
  const 下 = 四舍(H - Math.max(...rs.map((r) => r.bottom)));
  return {
    视口: [W, H], 节点数: rs.length,
    scale: m ? Number(m[1]) : null,
    留白: { 左, 右, 上, 下 },
    竖均: Math.round(((上 + 下) / 2) * 100) / 100,
    横均: Math.round(((左 + 右) / 2) * 100) / 100,
  };
};

const out = { 轮次: 'b260c', 宽, 高表, 行: [] };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const 高 of 高表) {
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    const r = await p.evaluate(量);
    const 隐含bboxH = (高 - r.留白.上 - r.留白.下) / r.scale;
    const 隐含bboxW = (宽 - r.留白.左 - r.留白.右) / r.scale;
    out.行.push({ 高, ...r, 隐含bboxW: Math.round(隐含bboxW * 10) / 10, 隐含bboxH: Math.round(隐含bboxH * 10) / 10 });
    log(`  H=${String(高).padStart(4)} scale=${String(r.scale).padEnd(10)}`
      + ` 竖均=${String(r.竖均).padStart(7)}（占高 ${(r.竖均 / 高 * 100).toFixed(3)}%）`
      + ` 横均=${String(r.横均).padStart(7)}`
      + ` 隐含bbox=${out.行[out.行.length - 1].隐含bboxW}×${out.行[out.行.length - 1].隐含bboxH}`);
  } catch (e) {
    out.行.push({ 高, 错: e.message });
    log(`🔴 H=${高} ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

const 好 = out.行.filter((r) => !r.错);
const 竖集 = [...new Set(好.map((r) => r.竖均))];
out.竖余唯一值 = 竖集;
out.竖余恒定 = 竖集.length === 1;
const bbox集 = [...new Set(好.map((r) => `${r.隐含bboxW}×${r.隐含bboxH}`))];
out.隐含bbox唯一值 = bbox集;
log('=== 判据 ===');
log(`纵向留白有 ${竖集.length} 个不同取值：${JSON.stringify(竖集)} ⇒ **${out.竖余恒定 ? '固定像素值（不是比例）' : '随高度变 ⇒ 是比例'}**`);
log(`隐含包围盒有 ${bbox集.length} 个不同取值：${JSON.stringify(bbox集)}`);
if (out.竖余恒定) out.结论 = `纵向留白是固定 **${竖集[0]}px**（与视口高无关），不是比例`;
else out.结论 = `纵向留白随高度变：${好.map((r) => `H=${r.高}→${r.竖均}`).join('，')} ⇒ 是比例`;
log(out.结论);
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`覆盖：${好.length} / ${高表.length} 档高度（立规 132）`);
log('写入 ' + OUT);
// 🔴 不要 `b.close()`：那会把无头浏览器一起关掉（批次 249 踩过）
process.exit(0);