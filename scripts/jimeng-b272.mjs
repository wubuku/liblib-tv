/**
 * 批次 272：把**宽度轴上那个 `2px` 台阶**的位置钉死，并测它的高度依赖。
 *
 * 📌 起意（批次 271 挖出来的）：那条「只由视口决定」的分支，其宽度项可写成
 *   `s = (w − 偏移) / 4091.4`，而实测
 *   `w=360 → 偏移 31.997`、`w=380/381 → 偏移 33.997`
 *   ⇒ 🔴 **中间有一个 `2px` 的台阶**（批次 270 在高度轴上也发现过一个形状相同的 `2.00` 台阶）。
 *
 * 📌 **本批用二分收敛**（立规：收敛型算法必须显式标注「哪些界已验证、哪些只是假设」）：
 *   已知 `偏移(360) = 32`（已验）、`偏移(380) = 34`（已验）⇒ 台阶在 `(360, 380]`。
 *   二分找**最小的 `w` 使偏移变成 `34`** ⇒ 每轮都把两个端点的偏移**实测出来**再夹逼，
 *   **不靠推理夹** ⇒ 输出里同时给出「已验证端点」与「本轮新测端点」。
 *
 * 📌 **顺带测一件能分辨「布局开关」还是「公式常数」的事**：
 *   🔴 那个台阶**落在哪个 `w`**？固定 `H=244` 二分完之后，
 *   **再换一个 `H` 重跑一次二分** ——
 *   · 若两个 `H` 给出**同一个 `w*`** ⇒ 它像是一个**响应式断点**（与 `H` 无关）
 *   · 若 `w*` 随 `H` 变 ⇒ 它是**随视口尺寸连续变化**的量，**不是断点**
 *   📌 这两条预测互斥，**一眼可辨**（与立规 149「问它对什么量敏感」同源）。
 *
 * 📌 **只读**：不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**。
 *   每臂开新页（批次 260）。**连采 6 帧去重**（立规 76）。末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b272.mjs      （落盘 /tmp/b272.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B272_OUT || '/tmp/b272.json';
const 节点 = { id: 'node_tadm1nyykc', 名: '音频 68', W: 320, Hc: 320 };
const 高度组 = process.argv.slice(2).map(Number).filter((n) => Number.isFinite(n) && n > 0);
const 高度组0 = 高度组.length ? 高度组 : [244, 300];   // 两个 H：若 w* 相同 ⇒ 断点；不同 ⇒ 连续量
const 帧数 = 6, 帧间隔 = 400;

const log = (...a) => console.log(a.join(' '));
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

async function 量偏移(高, 宽) {
  const p = await ctx.newPage();
  const 记 = { 高, 宽 };
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(5000);
    const 钮 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('button, [role="button"]'))
        .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    });
    if (!钮) throw new Error('找不到搜索钮');
    await p.mouse.click(钮[0], 钮[1]);
    await p.waitForTimeout(1500);
    const 短名 = 节点.id.replace(/^node_/, '');
    await p.evaluate(() => {
      const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
      if (inp) { inp.focus(); inp.select(); }
    });
    await p.keyboard.type(节点.名, { delay: 85 });
    await p.waitForTimeout(2200);
    const 行 = await p.evaluate((nid) => {
      const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
      if (!e) return { 有行: false };
      const r = e.getBoundingClientRect();
      return { 有行: true, 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 可点: r.width > 0 && r.height > 0 && r.y >= 0 && r.bottom <= innerHeight && r.x >= 0 && r.right <= innerWidth };
    }, 短名);
    if (!行.有行 || !行.可点) throw new Error(!行.有行 ? '搜不到那一行' : '结果行不可点');
    await p.mouse.click(行.中心[0], 行.中心[1]);
    await p.waitForTimeout(5000);
    await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    await p.keyboard.press('Escape'); await p.waitForTimeout(900);

    const 帧 = [];
    for (let i = 0; i < 帧数; i++) {
      帧.push(await p.evaluate((nid) => {
        const vp = document.querySelector('.react-flow__viewport');
        const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
        return m ? Number(m[1]) : null;
      }, 节点.id));
      await p.waitForTimeout(帧间隔);
    }
    const 去重 = [...new Set(帧)];
    记.去重后落点 = 去重;
    记.收敛 = 去重.length === 1;
    记.落点 = 记.收敛 ? 去重[0] : null;
    if (记.落点 !== null) {
      记.分子 = +(记.落点 * 4091.4).toFixed(4);
      记.偏移 = +(宽 - 记.分子).toFixed(4);
      记.偏移取整 = Math.round(记.偏移);
    }
  } catch (e) {
    记.错误 = e.message;
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
  }
  return 记;
}

const out = { 轮次: 'b272', 问: '宽度轴那个 2px 台阶落在哪个 w？它依赖 H 吗？', 节点, 高度组: 高度组0, 组: {}, 收尾: {} };

for (const 高 of 高度组0) {
  const 组 = { 高, 端点: {}, 二分轨迹: [] };
  out.组[高] = 组;
  // 📌 两个端点的偏移**都要实测**（不靠沿用上一批的数）
  const lo = await 量偏移(高, 360);
  const hi = await 量偏移(高, 380);
  组.端点.lo = lo; 组.端点.hi = hi;
  log(`H=${高} lo(w=360) 偏移=${lo.偏移} (取整 ${lo.偏移取整})｜hi(w=380) 偏移=${hi.偏移} (取整 ${hi.偏移取整})`);
  if (lo.偏移取整 === undefined || hi.偏移取整 === undefined || lo.偏移取整 === hi.偏移取整) {
    组.结论 = '两个端点偏移相同 ⇒ 这条二分的两个前提不成立，不夹逼';
    log(`H=${高} 🔴 ${组.结论}`);
    continue;
  }
  // 🔴 **前提检查（第一版缺了它，结论直接是错的）**：
  //   「偏移 ≈ 整数」这条律**只在异常分支内成立**。若某个高度落在**取景律 + 全局下限 `0.08`** 上，
  //   落点恒为 `0.08` ⇒ 分子恒 `0.08 × 4091.4 = 327.312` ⇒ 偏移 `= w − 327.312`，
  //   **每 `1px` 恰好加 `1`** ⇒ 二分照样能「收敛」，但它收敛到的是**下限的斜坡**，不是台阶。
  //   ⇒ 夹逼前必须验：端点的偏移**确实贴近整数**、且**落点不是 `0.08`**。
  const 前提 = (m) => m.落点 !== null && m.落点 > 0.08 + 1e-9 && Math.abs(m.偏移 - Math.round(m.偏移)) < 0.01;
  if (!前提(lo) || !前提(hi)) {
    组.结论 = {
      无效: true,
      原因: '端点不满足「偏移≈整数且落点>0.08」这一前提 ⇒ 该高度不在异常分支内（二分只会收敛到下限的斜坡）',
      lo落点: lo.落点, hi落点: hi.落点, lo偏移: lo.偏移, hi偏移: hi.偏移,
      全局下限提示: 0.08 * 4091.4,
    };
    log(`H=${高} 🔴 ${组.结论.原因}｜lo 落点=${lo.落点} 偏移=${lo.偏移}｜hi 落点=${hi.落点} 偏移=${hi.偏移}｜0.08×4091.4=${(0.08 * 4091.4).toFixed(3)}`);
    continue;
  }
  // 📌 二分：找最小的 w 使偏移 == hi 的偏移取整
  let a = 360, bb = 380, ta = lo.偏移取整, tb = hi.偏移取整;
  for (let 轮 = 1; 轮 <= 5 && bb - a > 1; 轮++) {
    const mid = Math.floor((a + bb) / 2);
    const m = await 量偏移(高, mid);
    组.二分轨迹.push(m);
    log(`  轮${轮} H=${高} w=${mid} 偏移=${m.偏移} (取整 ${m.偏移取整})`);
    if (m.偏移取整 === undefined) break;
    if (m.偏移取整 === tb) { bb = mid; tb = m.偏移取整; } else { a = mid; ta = m.偏移取整; }
    组.当前区间 = { lo端: a, hi端: bb };
  }
  组.结论 = {
    台阶位置_最小偏移切换的w: bb,
    已验证_hi端_偏移: tb,
    已验证_lo端_偏移: ta,
    区间剩余宽度: bb - a,
    说明: 'bb 是「偏移已变成新值」的最小 w；a 是「仍是旧值」的最大 w（两端都是实测，不是推理）',
  };
  log(`  ⇒ H=${高} 台阶在 w = ${bb}（区间剩余 ${bb - a}px，两端均实测）`);
}

{
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: 1280, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    out.收尾.节点数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    out.收尾.状态行 = await p.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
    out.收尾.通过 = out.收尾.节点数 === 76 && /0 selected/.test(out.收尾.状态行 || '');
    log(`\n末态独立复查：节点 ${out.收尾.节点数}｜${out.收尾.状态行} ⇒ ${out.收尾.通过 ? '✅' : '🔴'}`);
  } catch (e) { out.收尾.错误 = e.message; } finally { try { await p.close(); } catch (e) { /* 忽略 */ } }
}

const 位 = 高度组0.map((h) => ({ H: h, w星: out.组[h].结论?.台阶位置_最小偏移切换的w ?? null }));
out.汇总 = {
  各高度的台阶位置: 位,
  台阶位置是否与H无关: 位.every((x) => x.w星 !== null) && new Set(位.map((x) => x.w星)).size === 1,
  判定: 位.every((x) => x.w星 !== null)
    ? (new Set(位.map((x) => x.w星)).size === 1
      ? '两个 H 给出同一个 w* ⇒ 像响应式断点（与 H 无关）'
      : '两个 H 给出不同的 w* ⇒ 是随视口尺寸连续变化的量，不是断点')
    : '未完成',
};
log('\n=== 汇总 ===');
log(JSON.stringify(out.汇总, null, 1));
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`写入 ${OUT}`);
process.exit(0);
