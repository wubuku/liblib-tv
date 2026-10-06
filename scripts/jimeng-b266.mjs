/**
 * 批次 266：**取景封顶 `0.5` 是字面常数，还是随视口高度变的几何量？**
 *
 * 📌 起意（批次 253 留下的洞）：
 *   批次 244–263 把取景律测到「窄侧 `screen = w−412` / 宽侧 `screen = w−532`
 *   ＋ 两个缩放地板 ＋ **封顶 `0.5`**」，而 253 明确记下：
 *   🔴 **这整条律里每一个常数都是在「高度 = `720`」这一个切片上定出来的**。
 *   253 验的是「**律是纯横向的**」＋「中心 `Y = H/2`」，
 *   **验的是横向律随 `H` 不变，不是「封顶值本身随 `H` 不变」。**
 *   ⇒ 「`0.5` 是不是一个几何量」至今**一次都没测过**。
 *
 * 📌 **为什么封顶最可能不是几何量**（先写下预期，再验）：
 *   节点屏上高 `≈` 屏上宽（同族正方），封顶后屏上宽 `= 0.5·W = 160`。
 *   而**垂直方向**能不能装下 `160`，只在 **`H < 160`** 时才成为约束
 *   ⇒ 📌 **三种假设只在 `H < 0.5·W = 160` 这一段才分得开**：
 *     H1 **字面常数**：封顶恒 `0.5`，`H` 再小也不动，节点**溢出视口**。
 *     H2 **垂直装得下才放行**（`screen ≤ H`）：`H < 160` 后封顶**下移**，
 *        `H=120 ⇒ ≤0.375`、`100 ⇒ ≤0.3125`、`80 ⇒ 0.25`。
 *     H3 **装进视口的一半**（`min(0.5, H/2W)`）：`H=160` 就该读 `0.25`。
 *   ⇒ 宽侧取 `w = 1000`（`1000−532 = 468 > 160` ⇒ **封顶必然生效**），
 *     高度扫 `720 → 60`，**有信息量的臂全在 `160` 以下**。
 *
 * 📌 **顺带一个用户面事实**（本批的另一半价值）：
 *   取景靠**搜索面板点结果行**触发，而面板要在**多小的视口高**下还能打开/点得着？
 *   ⇒ ⚠️ 若它在某个高度**打不开**，那是**真实的使用限制**，
 *     **要量出来写进手册**，而不是换个触发方式假装测到了（立规 142）。
 *
 * 📌 **三条纪律**：
 *   · **只读**：不新建、不删除、不上传、不分享、不进扣费页、**绝不点生成**；
 *   · 每臂**开新页**（批次 260 已证 `resize` 不重算，只有「定位」会重算）；
 *   · 末态**在实验流程之外**独立复查（立规 140）：`76` 节点 / `0` 选中 / 积分 `725`。
 *
 * 用法：node scripts/jimeng-b266.mjs      （读数落盘 /tmp/b266.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B266_OUT || '/tmp/b266.json';
const 宽 = 1000;                       // 封顶必然生效（1000−532 = 468 ≫ 160）
const 高表 = [720, 400, 300, 240, 200, 180, 160, 140, 120, 100, 80, 60];
const 节点id = 'node_tadm1nyykc';       // 音频 68，算法宽 W = 320（无副作用，批次 263 末态确认仍在）
const 节点名 = '音频 68';
const W = 320;
const 封顶 = 0.5;

const log = (...a) => console.log(a.join(' '));

// 📌 预测先算好并落盘，不允许看到实测再改（立规 129/130）
const 预测 = (h) => {
  const 屏上 = Math.min(宽 - 532, 封顶 * W);          // = min(468, 160) = 160 ⇒ 封顶生效
  const 装得下 = h / W;                                // 垂直方向允许的最大缩放
  return {
    屏上宽预测: 屏上,
    落点_H1_字面常数: 封顶,
    落点_H2_垂直装得下: +Math.min(封顶, 装得下).toFixed(6),
    落点_H3_视口一半: +Math.min(封顶, 装得下 / 2).toFixed(6),
    三者是否分得开: Math.min(封顶, 装得下) !== 封顶 || 装得下 / 2 !== 封顶,
  };
};

const 数节点 = (p) => p.evaluate(() => document.querySelectorAll('.react-flow__node').length);

const out = {
  轮次: 'b266', 问: '取景封顶 0.5 是字面常数，还是随视口高度变的几何量？',
  宽, 节点id, 节点名, W, 高表, 臂: [], 面板可达性: [], 收尾: {},
};
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const 高 of 高表) {
  const p = await ctx.newPage();
  const 记 = { 高, 宽 };
  Object.assign(记, 预测(高));
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(5000);

    // ── 先量「搜索面板在这个高度下能不能用」（用户面事实，与取景结论独立）──
    const 可达 = { 高 };
    const 钮 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('button, [role="button"]'))
        .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 盒: [r.width, r.height], 在视口内: r.y >= 0 && r.bottom <= innerHeight };
    });
    可达.搜索钮 = 钮;
    if (!钮 || 钮.高 === 0) { 可达.结论 = '找不到搜索钮'; 记.可达 = 可达; out.臂.push(记); log(`H=${高} 🔴 ${可达.结论}`); await p.close(); continue; }
    if (!钮.中心 || 钮.中心[1] < 0 || 钮.中心[1] > 高) { 可达.结论 = '搜索钮在视口外'; 记.可达 = 可达; out.臂.push(记); log(`H=${高} 🔴 ${可达.结论}`); await p.close(); continue; }
    await p.mouse.click(钮.中心[0], 钮.中心[1]);
    await p.waitForTimeout(1500);

    const 短名 = 节点id.replace(/^node_/, '');
    await p.evaluate(() => {
      const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
      if (inp) { inp.focus(); inp.select(); }
    });
    await p.keyboard.type(节点名, { delay: 85 });
    await p.waitForTimeout(2200);

    const 行 = await p.evaluate((nid) => {
      const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
      if (!e) return { 有行: false };
      const r = e.getBoundingClientRect();
      return {
        有行: true, 盒: [Math.round(r.width), Math.round(r.height)],
        中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        在视口内: r.y >= 0 && r.bottom <= innerHeight && r.x >= 0 && r.right <= innerWidth,
        可见: r.width > 0 && r.height > 0,
      };
    }, 短名);
    可达.结果行 = 行;
    可达.结论 = !行.有行 ? '搜不到那一行'
      : !行.可见 ? '结果行零尺寸'
        : !行.在视口内 ? `结果行在视口外（y=${行.中心[1]} > H=${高}）`
          : '✅ 可点';
    记.可达 = 可达;
    out.面板可达性.push(可达);
    if (可达.结论 !== '✅ 可点') { out.臂.push(记); log(`H=${高} ⚠️ ${可达.结论}`); await p.close(); continue; }

    await p.mouse.click(行.中心[0], 行.中心[1]);
    await p.waitForTimeout(5000);
    await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    await p.keyboard.press('Escape'); await p.waitForTimeout(900);

    记.读数 = await p.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
      const nr = n ? n.getBoundingClientRect() : null;
      return {
        落点: m ? Number(m[1]) : null,
        缩放标签: z ? z.getAttribute('aria-label') : null,
        布局宽: n ? n.offsetWidth : null,
        屏上: nr ? [+nr.width.toFixed(4), +nr.height.toFixed(4)] : null,
        中心X: nr ? Math.round(nr.x + nr.width / 2) : null,
        中心Y: nr ? Math.round(nr.y + nr.height / 2) : null,
        节点顶: nr ? Math.round(nr.y) : null,
        节点底: nr ? Math.round(nr.bottom) : null,
        视口高: null,
        竖直溢出: nr ? +(Math.max(0, -nr.y) + Math.max(0, nr.bottom - innerHeight)).toFixed(2) : null,
        状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
      };
    }, 节点id);
    记.读数.视口高 = 高;

    // ── 判别：三个假设各判一次 ──
    const L = 记.读数.落点;
    const 命中 = [];
    if (L !== null) {
      if (Math.abs(L - 0.5) <= 1e-9) 命中.push('H1 字面常数 0.5');
      if (Math.abs(L - 记.落点_H2_垂直装得下) <= 1e-6) 命中.push('H2 垂直装得下');
      if (Math.abs(L - 记.落点_H3_视口一半) <= 1e-6) 命中.push('H3 视口一半');
    }
    记.命中假设 = 命中;
    记.溢出证实H1 = 记.读数.竖直溢出 !== null && 记.读数.竖直溢出 > 0.5;
    out.臂.push(记);
    log(`H=${String(高).padStart(3)} 落点=${L} 屏上=${JSON.stringify(记.读数.屏上)} 中心Y=${记.读数.中心Y}(应=${高 / 2}) 竖直溢出=${记.读数.竖直溢出} ⇒ ${命中.join(' / ') || '无假设命中'}`);
  } catch (e) {
    记.错误 = e.message;
    out.臂.push(记);
    log(`H=${高} 🔴 ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ============ 末态独立复查（立规 140，在实验流程之外） ============
{
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: 1280, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    out.收尾.节点数 = await 数节点(p);
    out.收尾.状态行 = await p.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
    out.收尾.积分 = await p.evaluate(() => {
      const t = document.body.innerText || '';
      const m = t.match(/(\d{2,6})\s*(?:积分|credits?|点)/i);
      return m ? m[1] : null;
    });
    out.收尾.期望 = { 节点数: 76, 选中: 0, 积分: '725' };
    out.收尾.通过 = out.收尾.节点数 === 76 && /0 selected/.test(out.收尾.状态行 || '');
    log(`\n末态独立复查：节点 ${out.收尾.节点数}｜${out.收尾.状态行}｜积分 ${out.收尾.积分} ⇒ ${out.收尾.通过 ? '✅' : '🔴'}`);
  } catch (e) {
    out.收尾.错误 = e.message;
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
  }
}

// ============ 汇总 ============
const 成功 = out.臂.filter((a) => a.读数);
out.汇总 = {
  臂总数: out.臂.length,
  成功取景臂: 成功.length,
  面板不可达臂: out.臂.length - 成功.length,
  落点恒为0_5的臂: 成功.filter((a) => Math.abs(a.读数.落点 - 0.5) <= 1e-9).length,
  落点非0_5的臂: 成功.filter((a) => Math.abs(a.读数.落点 - 0.5) > 1e-9).length,
  中心Y等于H除2的臂: 成功.filter((a) => a.读数.中心Y === a.高 / 2).length,
  竖直溢出大于0_5的臂: 成功.filter((a) => a.溢出证实H1).length,
  最小可用高度: Math.min(...成功.map((a) => a.高)),
  面板最小可用高度: out.面板可达性.filter((a) => a.结论 === '✅ 可点').length
    ? Math.min(...out.面板可达性.filter((a) => a.结论 === '✅ 可点').map((a) => a.高)) : null,
};
log('\n=== 汇总 ===');
log(JSON.stringify(out.汇总, null, 1));
log('\n=== 逐臂 ===');
for (const a of out.臂) log(`  H=${String(a.高).padStart(3)}｜${a.可达 ? a.可达.结论 : ''}｜落点 ${a.读数 ? a.读数.落点 : '—'}｜H1 ${a.落点_H1_字面常数} H2 ${a.落点_H2_垂直装得下} H3 ${a.落点_H3_视口一半}`);

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`\n写入 ${OUT}`);
process.exit(0);
