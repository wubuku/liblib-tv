/**
 * 批次 259：`适配画布` 到底**给节点留了多少边** —— 以及它和「初次自适应」为什么差 `0.038`。
 *
 * 📌 背景（批次 257）：同一视口 `1280 × 720` 下
 *   · **进页时的缩放** = `0.260267`；
 *   · 点缩放菜单里的 **`适配画布`** 之后 = **`0.222179`**。
 *   🔴 两个都是「把画布塞进视口」，却差 `0.038`（约 `14.6%`）—— **差在哪，从没被问过。**
 *   而这是**用户真的会点的按钮**，值得写进手册。
 *
 * 📌 本批测**一个能直接回答用户问题的量**：点完 `适配画布` 之后，
 *   **全部节点的包围盒距视口四边各剩多少 px**（`左 / 右 / 上 / 下`）。
 *   · 若四边留白**逐字相同且与 `w` 无关** ⇒ 是一个固定 padding；
 *   · 若留白随 `w` 变 ⇒ 是按比例或按某一轴算的；
 *   · 再把「初次自适应」那一档的留白**同样算一遍**当对照 ⇒
 *     **两者是不是同一套 padding、只是触发时机不同**，一眼可见。
 *
 * 📌 判据（先写死）：**逐档列四边留白原值**，不预设它等于任何数；
 *   差异是否存在**等号**上，交由读数自己说。
 *
 * 🔴 纪律：只点**缩放菜单里的 `适配画布`**（纯视图操作）；
 *   不新建、不删除、不上传、不触发生成、不进扣费页、不点「保存到主体库」、不分享。
 *
 * 用法：node scripts/jimeng-b259.mjs      （读数落盘 /tmp/b259.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B259_OUT || '/tmp/b259.json';
const 高 = 720;
const 宽表 = [700, 900, 1100, 1400];

const log = (...a) => console.log(a.join(' '));

/** 📌 一次读齐：缩放 + 全部节点的包围盒 + 四边留白 */
const 量 = () => {
  const W = window.innerWidth, H = window.innerHeight;
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const ns = Array.from(document.querySelectorAll('.react-flow__node'));
  const rs = ns.map((n) => n.getBoundingClientRect());
  if (!rs.length) return { scale: null, 节点数: 0 };
  const 左 = Math.min(...rs.map((r) => r.left));
  const 右 = Math.max(...rs.map((r) => r.right));
  const 上 = Math.min(...rs.map((r) => r.top));
  const 下 = Math.max(...rs.map((r) => r.bottom));
  const 四舍 = (v) => Math.round(v * 100) / 100;
  return {
    视口: [W, H],
    scale: m ? Number(m[1]) : null,
    节点数: ns.length,
    包围盒: { 左: 四舍(左), 右: 四舍(右), 上: 四舍(上), 下: 四舍(下) },
    留白: { 左: 四舍(左), 右: 四舍(W - 右), 上: 四舍(上), 下: 四舍(H - 下) },
    越界: { 左: 四舍(左) < 0, 右: 四舍(W - 右) < 0, 上: 四舍(上) < 0, 下: 四舍(H - 下) < 0 },
  };
};

const 点适配 = async (p) => {
  const 钮 = await p.evaluate(() => {
    const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
    if (!z) return null;
    const b = z.getBoundingClientRect();
    return [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)];
  });
  if (!钮) throw new Error('找不到缩放读数钮');
  await p.mouse.click(钮[0], 钮[1]);
  await p.waitForTimeout(1100);
  const 位 = await p.evaluate(() => {
    const 面 = document.querySelector('[data-testid="canvas-zoom-menu"]');
    if (!面) return null;
    const e = Array.from(面.querySelectorAll('div,button')).find((x) => (x.innerText || '').trim().startsWith('适配画布'));
    if (!e) return null;
    const b = e.getBoundingClientRect();
    return [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)];
  });
  if (!位) throw new Error('菜单里找不到「适配画布」');
  await p.mouse.click(位[0], 位[1]);
  await p.waitForTimeout(1800);
};

const out = { 轮次: 'b259', 高, 宽表, 臂: [] };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const 宽 of 宽表) {
  const p = await ctx.newPage();
  const 记 = { 宽, 高 };
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);

    记.初次自适应 = await p.evaluate(量);
    await 点适配(p);
    记.点适配后 = await p.evaluate(量);
    记.适配是否改变 = 记.初次自适应.scale !== 记.点适配后.scale;

    log(`【w=${宽}】初次 scale=${记.初次自适应.scale} 留白=${JSON.stringify(记.初次自适应.留白)}`);
    log(`        适配 scale=${记.点适配后.scale} 留白=${JSON.stringify(记.点适配后.留白)}`
      + ` 越界=${JSON.stringify(记.点适配后.越界)} ${记.适配是否改变 ? '' : '（没变）'}`);
  } catch (e) {
    记.错误 = e.message;
    log(`🔴 w=${宽} ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
  }
  out.臂.push(记);
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
}

// 📌 判据：把两栏的留白并排列出来，**不预设它等于任何数**
const 好 = out.臂.filter((a) => !a.错误);
out.对照 = 好.map((a) => ({
  w: a.宽,
  初次: { scale: a.初次自适应?.scale, 留白: a.初次自适应?.留白 },
  适配: { scale: a.点适配后?.scale, 留白: a.点适配后?.留白 },
}));
log('=== 对照表 ===');
for (const r of out.对照) {
  log(`  w=${String(r.w).padStart(4)} ｜ 初次 ${r.初次.scale} 留白 ${JSON.stringify(r.初次.留白)}`
    + ` ｜ 适配 ${r.适配.scale} 留白 ${JSON.stringify(r.适配.留白)}`);
}
const 适配留白集 = [...new Set(好.map((a) => JSON.stringify(a.点适配后?.留白)))];
const 初次留白集 = [...new Set(好.map((a) => JSON.stringify(a.初次自适应?.留白)))];
log(`适配后的留白有 ${适配留白集.length} 种；初次的留白有 ${初次留白集.length} 种`);
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
// 🔴 不要 `b.close()`：那会把无头浏览器一起关掉（批次 249 踩过）
process.exit(0);