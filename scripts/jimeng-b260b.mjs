/**
 * 批次 260 · 正式扫描：**把「初次自适应」的留白曲线量出来**（探路已证明只能一宽度一页面）。
 *
 * 📌 探路结论（`b260.mjs`）：同一页里连续改 `14` 个宽度，
 *   `scale` **逐字不动**（恒 `0.155938`）⇒ **初次自适应只在加载时算一次**，
 *   `resize` 不重算 ⇒ **必须一宽度开一次页**。
 *   📌 顺带记到：**内容靠左钉住**（左缘恒 `32`，右缘随宽度线性增长）——
 *   那是 `w=700` 那一次适配的结果，`w` 变大时**并不会重新居中**。
 *
 * 📌 为什么要扫：批次 259 只拿到 `4` 个点（单边留白 `31.01 / 40.0 / 50.0 / 32.0`），
 *   **既不是常数，也没有一条简单比例套得住**。
 *   🔴 用 `4` 个点去拟合一个未知的函数，**必然能拟合出好几条**——
 *   ⇒ 按立规 129，**先把现象宽度量出来**：本批一次测 `14` 个宽度，
 *   让「留白随 `w` 怎么走」这条曲线自己说话，**不预设它是常数还是比例**。
 *
 * 📌 判据（先写死）：
 *   · 单边留白**逐字恒定** ⇒ 固定 padding；
 *   · 单边留白随 `w` **线性** ⇒ 比例 padding（并把斜率与截距一起报出来）；
 *   · **分段**（出现拐点）⇒ 有 `min()` 或分段规则；
 *   · **看不出结构** ⇒ **如实写「未闭合」并报出覆盖了多少个宽度**（立规 132）。
 *
 * 🔴 纪律：每档开新页、只读 DOM；不新建、不删除、不上传、不触发生成、
 *   不进扣费页、不点「保存到主体库」、不分享。
 *
 * 用法：node scripts/jimeng-b260b.mjs      （读数落盘 /tmp/b260b.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B260B_OUT || '/tmp/b260b.json';
const 高 = 720;
const 宽表 = [640, 680, 720, 760, 800, 860, 920, 980, 1040, 1100, 1160, 1220, 1280, 1400];

const log = (...a) => console.log(a.join(' '));

const 量 = () => {
  const W = window.innerWidth, H = window.innerHeight;
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const rs = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
  if (!rs.length) return { scale: null, 节点数: 0 };
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

const out = { 轮次: 'b260b', 高, 宽表, 行: [] };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const 宽 of 宽表) {
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    const r = await p.evaluate(量);
    // 📌 单边留白取左右平均（见下方「左右差 2px」的处理）与上下平均
    const 横均 = (r.留白.左 + r.留白.右) / 2;
    const 竖均 = (r.留白.上 + r.留白.下) / 2;
    out.行.push({
      宽, ...r,
      横均: Math.round(横均 * 100) / 100,
      竖均: Math.round(竖均 * 100) / 100,
      左右差: Math.round((r.留白.左 - r.留白.右) * 100) / 100,
      上下差: Math.round((r.留白.上 - r.留白.下) * 100) / 100,
    });
    log(`  w=${String(宽).padStart(4)} scale=${String(r.scale).padEnd(10)}`
      + ` 横均=${String(out.行[out.行.length - 1].横均).padStart(7)}`
      + ` 竖均=${String(out.行[out.行.length - 1].竖均).padStart(7)}`
      + ` 左右差=${out.行[out.行.length - 1].左右差}`);
  } catch (e) {
    out.行.push({ 宽, 错: e.message });
    log(`🔴 w=${宽} ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// 📌 判据：绑定轴 = 留白较小的那一轴；只看**绑定轴**的留白曲线
const 好 = out.行.filter((r) => !r.错);
const 曲线 = 好.map((r) => {
  const 横绑 = r.横均 <= r.竖均;
  return { w: r.宽, scale: r.scale, 绑定: 横绑 ? '宽' : '高', 留白: 横绑 ? r.横均 : r.竖均, 横均: r.横均, 竖均: r.竖均 };
});
out.曲线 = 曲线;
log('=== 绑定轴的留白曲线 ===');
for (const c of 曲线) log(`  w=${String(c.w).padStart(4)} 绑定=${c.绑定} 留白=${String(c.留白).padStart(8)} (横${c.横均}/竖${c.竖均})`);

const 唯一留白 = [...new Set(曲线.map((c) => c.留白))];
out.留白唯一值 = 唯一留白;
out.留白恒定 = 唯一留白.length === 1;
log(`绑定轴留白有 ${唯一留白.length} 个不同取值；逐字恒定？ ${out.留白恒定 ? '是' : '否'}`);

// 📌 若不是常数，试着拟合 留白 = k·w + c（对宽绑定那几档）
const 宽绑 = 曲线.filter((c) => c.绑定 === '宽');
if (宽绑.length >= 2) {
  const n = 宽绑.length;
  const sx = 宽绑.reduce((a, c) => a + c.w, 0), sy = 宽绑.reduce((a, c) => a + c.留白, 0);
  const sxx = 宽绑.reduce((a, c) => a + c.w * c.w, 0), sxy = 宽绑.reduce((a, c) => a + c.w * c.留白, 0);
  const k = (n * sxy - sx * sy) / (n * sxx - sx * sx);
  const c0 = (sy - k * sx) / n;
  out.线性拟合 = { k, 截距: c0, 点数: n, 最大残差: Math.max(...宽绑.map((c) => Math.abs(c.留白 - (k * c.w + c0)))) };
  log(`线性拟合（${n} 个宽绑定点）：留白 ≈ ${k.toFixed(6)}·w + ${c0.toFixed(4)}，最大残差 ${out.线性拟合.最大残差.toFixed(4)}`);
}
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`覆盖：${好.length} / ${宽表.length} 个宽度（立规 132：负结果也要报覆盖面）`);
log('写入 ' + OUT);
// 🔴 不要 `b.close()`：那会把无头浏览器一起关掉（批次 249 踩过）
process.exit(0);