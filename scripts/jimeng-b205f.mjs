/**
 * 批次 205 f 轮：判定「取景终态缩放那条阶梯」是**视口宽的函数**，
 * 还是**目标节点画布位置的函数**。
 *
 * 已定下来的（205 a~e 五轮）：
 *   · 落点中心 X 恒 = `w/2 − 166`（36 档逐字命中）
 *   · 取景终态 tx 在两段平台上都在 `w/2 − 1138.064` 这条直线上
 *   · 取景终态**缩放**在 `w ≤ 1210` 恒 `50%`、`1212..1230` 连续变化
 *     （`26.0% → 48.7%`）、`w ≥ 1232` 恒 `50%`；30 秒连采证明**不是慢收敛**
 *   · 落点中心 Y：`w ≤ 1211` 恒 `360`，`w ≥ 1212` 恒 `≈259.8`
 *   · `.react-flow` 盒子恒 `[0,0,w,720]`、侧栏计数恒 `2` ⇒ **不是侧栏出现/消失**
 *   · 初始平移 `tx = w/2 − 542.8491`、`ty` 恒 `−30.4641`，且**加载后不再随视口变**
 *
 * 剩下两种解释，本轮用**换一个位置的节点**来分：
 *   甲（宽度函数）：阶梯只跟 w 有关 ⇒ 换个节点，阶梯逐字相同
 *   乙（位置函数）：阶梯跟「节点要平移多远」有关 ⇒ 换个节点，阶梯会变
 *     · 音频 68 在画布**右下** `[1784.13, 649.111]`
 *     · 文本 3  在画布**左上** `[560, 319]`
 *     · 若甲成立，两者在同一 w 上的缩放逐字相同；若乙成立，不同。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 宽集 = [];
for (let w = 1210; w <= 1234; w += 2) 宽集.push(w);
// 两个目标：(testid, 画布位置, 搜索词)
const 目标们 = [
  { 名: '音频68_右下', testid: 'canvas-search-result-node_tadm1nyykc', 词: '音频', 画布: [1784.13, 649.111] },
  { 名: '文本3_左上', testid: 'canvas-search-result-node_5gftn3dnt1', 词: '文本', 画布: [560, 319] },
];

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b205f', 高度固定: H, 宽集, 目标们, 档: {} };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const t of 目标们) {
  out.档[t.名] = {};
  for (const w of 宽集) {
    const p = await ctx.newPage();
    try {
      await p.setViewportSize({ width: w, height: H });
      await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await p.waitForSelector('.react-flow__node', { timeout: 45000 });
      await p.waitForTimeout(4500);

      const 搜索钮 = await p.evaluate(() => {
        const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
          || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      });
      if (!搜索钮) { out.档[t.名][w] = { 无效臂: '找不到搜索钮' }; await p.close(); continue; }
      await p.mouse.click(搜索钮[0], 搜索钮[1]);
      await p.waitForTimeout(1500);
      const 有输入框 = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
        if (!e) return false;
        e.focus(); e.select(); return true;
      });
      if (!有输入框) { out.档[t.名][w] = { 无效臂: '找不到搜索输入框' }; await p.close(); continue; }
      await p.keyboard.press('Backspace');
      await p.waitForTimeout(250);
      await p.keyboard.type(t.词, { delay: 90 });
      await p.waitForTimeout(2200);

      const 输入回读 = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
        return e ? e.value : null;
      });
      const 前置 = await p.evaluate((tid) => {
        const e = document.querySelector(`[data-testid="${tid}"]`);
        if (!e) return { 存在: false };
        const r = e.getBoundingClientRect();
        return { 存在: true, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
          总条数: document.querySelectorAll('[data-testid^="canvas-search-result-node_"]').length };
      }, t.testid);
      if (!前置.存在 || 输入回读 !== t.词) {
        out.档[t.名][w] = { 无效臂: !前置.存在 ? '目标行不在' : '输入没进去', 前置, 输入回读 };
        log(`${t.名} ${w} ⛔ 无效臂`);
        await p.close(); continue;
      }

      await p.mouse.click(前置.点[0], 前置.点[1]);
      await p.waitForTimeout(4000);

      const 终 = await p.evaluate((tid) => {
        const id = tid.replace('canvas-search-result-node_', 'node_');
        const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
        const vp = document.querySelector('.react-flow__viewport');
        const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
        const r = n ? n.getBoundingClientRect() : null;
        const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
        return { 中心: r ? [Math.round((r.x + r.width / 2) * 1000) / 1000, Math.round((r.y + r.height / 2) * 1000) / 1000] : null,
          屏上: r ? [Math.round(r.width), Math.round(r.height)] : null,
          vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null,
          缩放aria: z ? z.getAttribute('aria-label') : null };
      }, t.testid);

      out.档[t.名][w] = { 前置: { 总条数: 前置.总条数 }, 终 };
      log(`${t.名} ${w} | 中心=${JSON.stringify(终.中心)} | s=${终.vp && 终.vp[2]} | 屏上=${JSON.stringify(终.屏上)} | ${终.缩放aria}`);
    } catch (e) {
      out.档[t.名][w] = { 出错: e.message };
      log(`${t.名} ${w} 🔴 ${e.message}`);
    } finally { await p.close(); }
  }
}

// —— 逐档并排比对两个目标的缩放 ——
out.比对 = [];
for (const w of 宽集) {
  const A = out.档['音频68_右下'][w], B = out.档['文本3_左上'][w];
  const sa = A && A.终 && A.终.vp ? A.终.vp[2] : null;
  const sb = B && B.终 && B.终.vp ? B.终.vp[2] : null;
  out.比对.push({ 宽: w, 音频68缩放: sa, 文本3缩放: sb, 逐字相同: sa !== null && sa === sb });
}
log('\n并排比对：');
for (const r of out.比对) log(`  ${r.宽} | 音频68 ${r.音频68缩放} | 文本3 ${r.文本3缩放} | ${r.逐字相同 ? '✅相同' : '❌不同'}`);

fs.writeFileSync('/tmp/b205f.json', JSON.stringify(out, null, 1));
log('\n写入 /tmp/b205f.json');
process.exit(0);
