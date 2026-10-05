/**
 * 批次 212 b 轮：用**画布上现成的 10 个位置各异的节点**，在 3 个宽度上各做一次取景，
 * 看「节点画布位置 → 终态缩放 / 纵向落点」到底服从什么规则。
 *
 * 批次 211 的谜：同一宽度下，`音频 68`（画布右下）取景把缩放降到 26~49%，
 *   `文本 3`（画布左上）恒 50% ⇒ 过渡带是「节点位置 × 宽度」的函数。
 *   但**规则本身**还没隔离。
 *
 * 📌 为什么用现成节点、**不拖动节点**：
 *   拖节点能隔离「位置」这一个变量，但会把画布坐标改掉，
 *   而第 9 道门（画布焦点守卫 + 位置比对）要对着基线核对 ⇒ 风险不对等。
 *   画布上已有 76 个节点、位置从 `[40,370]` 到 `[3562,2440]` 铺满，
 *   拿 10 个代表点去测，**只读、不动任何东西**。
 *
 * 📌 每档的纪律（沿用批次 210/211 立规 86/87）：
 *   ① 清空搜索框用 `focus()+select()+Backspace`，并**断言输入框回读 === 搜索词**；
 *   ② 点之前**按 testid 找那一行**（不点「第一条」）—— 同名节点（音频 7 / 音频 70）会混；
 *   ③ 取景后等 4 秒再读，并**连采 3 次**确认终态稳定（批次 211 d 轮证过 30 秒内不变）。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 宽集 = [1210, 1212, 1232];
const 节点们 = [
  { 名: '中心',   id: 'node_20sb5adarj', 词: '音频 7',   画布: [1662.76, 1292.96] },
  { 名: '左上',   id: 'node_5gftn3dnt1',  词: '文本 3',   画布: [560.055, 319.375] },
  { 名: '右中',   id: 'node_tadm1nyykc',  词: '音频 68',  画布: [1784.13, 649.111] },
  { 名: '左中',   id: 'node_ay7f1jn45r',  词: '音频 1',   画布: [594.805, 569.5] },
  { 名: '中右',   id: 'node_fd0p2amd3p',  词: '音频 53',  画布: [2024.43, 1292.96] },
  { 名: '最下中', id: 'node_pz48stvt07',  词: '音频 54',  画布: [1662.76, 2440.49] },
  { 名: '右下角', id: 'node_fyy39951ae',  词: '音频 60',  画布: [3282.76, 2365.96] },
  { 名: '左上角', id: 'node_cdwf8x6fbj',  词: '时间线 1', 画布: [40.0555, 370.5] },
  { 名: '左下偏中', id: 'node_jc6t41x8d2', 词: '音频 61', 画布: [1464.13, 1405.96] },
  { 名: '外部节点', id: 'node_pxvkay973v', 词: '导演台',   画布: [640.055, 440.651] },
];

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b212b', 高度固定: H, 宽集, 节点数: 节点们.length, 档: {} };

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
        return { 存在: true, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
          总条数: document.querySelectorAll('[data-testid^="canvas-search-result-node_"]').length, aria: e.getAttribute('aria-label') };
      }, tid);
      const 输入断言 = { 回读: 输入回读, 通过: 输入回读 === n.词 };
      if (!前置.存在 || !输入断言.通过) {
        out.档[w][n.名] = { 无效臂: !前置.存在 ? '目标行不在' : '输入没进去', 前置, 输入断言, 画布: n.画布 };
        log(`${w} ${n.名} ⛔ 无效臂：${!前置.存在 ? '目标行不在 ' + JSON.stringify(前置.现存) : '输入回读=' + 输入回读}`);
        await p.close(); continue;
      }

      await p.mouse.click(前置.点[0], 前置.点[1]);
      await p.waitForTimeout(4000);

      // 连采 3 次确认终态稳定
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
      out.档[w][n.名] = { 画布: n.画布, 前置: { 总条数: 前置.总条数, aria: 前置.aria }, 输入断言, 采样, 末: 采样[2],
        断言: { 判据: '3 次采样的 scale 相同（终态稳定）', 通过: ss.length === 1, 去重: ss } };
      log(`${w} ${n.名.padEnd(6)} 画布[${n.画布}] → s=${末(ss)} 中心=${JSON.stringify(采样[2].中心)} 屏上=${JSON.stringify(采样[2].屏上)} 稳定=${ss.length === 1}`);
    } catch (e) {
      out.档[w][n.名] = { 出错: e.message, 画布: n.画布 };
      log(`${w} ${n.名} 🔴 ${e.message}`);
    } finally { await p.close(); }
  }
}
function 末(a) { return a && a[0] !== undefined ? JSON.stringify(a) : JSON.stringify(a); }

fs.writeFileSync('/tmp/b212b.json', JSON.stringify(out, null, 1));
log('\n写入 /tmp/b212b.json');
process.exit(0);
