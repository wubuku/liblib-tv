/**
 * 批次 212 c 轮：把「判据到底是什么」二选一地分开。
 *
 * 批次 212 b 轮 30 臂读出的分裂（w=1212）：
 *   受影响（终态 scale 掉到 `0.260267`、中心 Y 掉到 `≈254~260`）：
 *     音频 7 `[1662,1293]`、音频 68 `[1784,649]`、音频 1 `[595,570]`、音频 53 `[2024,1293]`、
 *     音频 54 `[1663,2440]`、音频 60 `[3283,2366]`、音频 61 `[1464,1406]`
 *   **不受影响**（scale 恒 `0.5`）：
 *     文本 3 `[560,319]`、时间线 1 `[40,370]`、导演台 `[640,441]`
 *
 * ⇒ 「连画布正中的音频 7 都降」⇒ **不是「离中心远」**。
 * ⇒ 「画布左上角的音频 1 也降」⇒ **不是「在某个角」**。
 *
 * 两个还活着的解释，本轮用**两个精心挑的节点**分开：
 *
 *   **甲：按画布 y 的阈值**（不受影响的最深 y = `440.651` 导演台；
 *      受影响的最浅 y = `464.75` 音频 5 ⇒ 阈值 T ∈ (440.651, 569.5]）
 *   **乙：按节点类型**（只有 `audio` 中招）
 *
 *   判别子：**时间线 2**（y = `998.612`，**非音频**、y 很大）
 *         + **图片**（y = `1981.81`，**非音频**、y 很大）
 *   · 甲成立 ⇒ 两者都该受影响
 *   · 乙成立 ⇒ 两者都不受影响
 *   另外 **音频 5**（y = `464.75`）用来在甲成立时把 T 夹得更紧。
 *
 * 附带把 **视频 1**（y = `400.111`，非音频、y 小）也测上，做反向对照。
 *
 * 只读：只点搜索结果，不新建/删除/拖动任何节点。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 宽集 = [1210, 1212];
const 节点们 = [
  { 名: '音频5_卡缝', id: 'node_gp499g9p3m', 词: '音频 5',   类型: 'audio',     画布: [794.805, 464.75] },
  { 名: '音频3_对照', id: 'node_dt0wpmba0d', 词: '音频 3',   类型: 'audio',     画布: [714.805, 689.5] },
  { 名: '时间线2_判别', id: 'node_d4tjtpnatq', 词: '时间线 2', 类型: 'timeline', 画布: [1282.76, 998.612] },
  { 名: '图片_判别',  id: 'node_gref4sw056',  词: 'b22-upload', 类型: 'image',  画布: [3562.42, 1981.81] },
  { 名: '视频1_反向', id: 'node_236ctpehgg',  词: '视频 1',   类型: 'video',     画布: [865, 400.111] },
  { 名: '导演台_对照', id: 'node_pxvkay973v', 词: '导演台',   类型: 'external',  画布: [640.055, 440.651] },
];

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b212c', 高度固定: H, 宽集, 节点们, 档: {} };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const w of 宽集) {
  out.档[w] = {};
  for (const n of 节点们) {
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
      if (!搜索钮) { out.档[w][n.名] = { 无效臂: '找不到搜索钮' }; await p.close(); continue; }
      await p.mouse.click(搜索钮[0], 搜索钮[1]);
      await p.waitForTimeout(1500);
      const 有输入框 = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
        if (!e) return false;
        e.focus(); e.select(); return true;
      });
      if (!有输入框) { out.档[w][n.名] = { 无效臂: '找不到搜索输入框' }; await p.close(); continue; }
      await p.keyboard.press('Backspace');
      await p.waitForTimeout(250);
      await p.keyboard.type(n.词, { delay: 90 });
      await p.waitForTimeout(2200);
      const 输入回读 = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
        return e ? e.value : null;
      });
      const tid = 'canvas-search-result-node_' + n.id.replace(/^node_/, '');
      const 前置 = await p.evaluate((t) => {
        const e = document.querySelector(`[data-testid="${t}"]`);
        if (!e) return { 存在: false, 现存: Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).slice(0, 8).map((x) => x.getAttribute('data-testid')) };
        const r = e.getBoundingClientRect();
        return { 存在: true, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 总条数: document.querySelectorAll('[data-testid^="canvas-search-result-node_"]').length };
      }, tid);
      if (!前置.存在 || 输入回读 !== n.词) {
        out.档[w][n.名] = { 无效臂: !前置.存在 ? '目标行不在' : '输入没进去', 前置, 输入回读 };
        log(`${w} ${n.名} ⛔ 无效臂`);
        await p.close(); continue;
      }
      await p.mouse.click(前置.点[0], 前置.点[1]);
      await p.waitForTimeout(4000);
      const 采样 = [];
      for (let k = 0; k < 3; k++) {
        采样.push(await p.evaluate((id) => {
          const n2 = document.querySelector(`.react-flow__node[data-id="${id}"]`);
          const vp = document.querySelector('.react-flow__viewport');
          const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
          const r = n2 ? n2.getBoundingClientRect() : null;
          return { 中心: r ? [Math.round((r.x + r.width / 2) * 1000) / 1000, Math.round((r.y + r.height / 2) * 1000) / 1000] : null,
            屏上: r ? [Math.round(r.width), Math.round(r.height)] : null,
            vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null };
        }, n.id));
        await p.waitForTimeout(500);
      }
      const ss = [...new Set(采样.map((x) => x.vp && x.vp[2]))];
      out.档[w][n.名] = { 类型: n.类型, 画布: n.画布, 总条数: 前置.总条数, 采样, 末: 采样[2],
        断言: { 判据: '3 次采样 scale 相同', 通过: ss.length === 1 } };
      log(`${w} ${n.名.padEnd(12)} (${n.类型.padEnd(9)}) canvasY=${String(n.画布[1]).padEnd(9)} → s=${JSON.stringify(ss)} 中心=${JSON.stringify(采样[2].中心)} 屏上=${JSON.stringify(采样[2].屏上)}`);
    } catch (e) { out.档[w][n.名] = { 出错: e.message }; log(`${w} ${n.名} 🔴 ${e.message}`); }
    finally { await p.close(); }
  }
}

// —— 判别表 ——
out.判别 = 节点们.map((n) => {
  const g = out.档[1212] && out.档[1212][n.名];
  const s = g && g.末 && g.末.vp ? g.末.vp[2] : null;
  return { 名: n.名, 类型: n.类型, canvasY: n.画布[1], canvasX: n.画布[0],
    终态scale: s, 受影响: s !== null && s < 0.499 };
});
log('\n判别表（w=1212，受影响 = 终态 scale < 0.499）：');
for (const r of out.判别) log(`  ${r.名.padEnd(12)} ${r.类型.padEnd(9)} y=${String(r.canvasY).padEnd(9)} s=${String(r.终态scale).padEnd(10)} ${r.受影响 ? '🔴 受影响' : '✅ 不受影响'}`);

fs.writeFileSync('/tmp/b212c.json', JSON.stringify(out, null, 1));
log('\n写入 /tmp/b212c.json');
process.exit(0);
