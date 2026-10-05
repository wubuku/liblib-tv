/**
 * 批次 205 b 轮：a 轮 21 档里出现了一个**没法用「断点」解释**的现象，必须先排除掉它。
 *
 * a 轮（宽 1200~1280 步长 4、高 720、点同一个 testid、6 帧 × 600ms）读到的末帧 scale：
 *   w ≤ 1208        → 0.5
 *   w = 1212..1228  → 0.260267 / 0.299607 / 0.34461 / 0.396052 / 0.454807   🔴 不是 0.5
 *   w ≥ 1232        → 0.5
 * 而 0.260267 **正是画布的初始缩放**（批次 199 记的十二档逐字相同的那一档），
 * 中间四档又是单调趋近 0.5 的中间值 ⇒ **高度怀疑是「取景动画在 6 帧内没跑完」**，
 * 而不是「这一段宽度有什么特殊机制」。
 *
 * 📌 立规 79：否证的对象必须是现象本身。「ty 在 1212~1228 是斜坡」这个现象，
 *   在确认 scale 收敛之前，**不能**当成「断点在这一段」来解释。
 *
 * 本轮两件事：
 *   ① **长采样**：点完一直采到连续 4 帧完全相同（或 24 帧 / ~17s 封顶），
 *      把「中间档是不是没收敛」这件事变成可判定的读数；
 *   ② 若确认收敛了，再读那一段的**几何**：`.react-flow` 盒子、搜索面板盒子、
 *      节点屏上盒子，并扫一遍「有没有元素的边界/中心能解释 中心Y 从 360 变成 ~260」。
 *
 * 宽度改为 1206~1234 步长 2（把 1208/1212 之间的缝收窄到 2px）。
 * 只读：不新建/删除节点，不生成，不下载。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 搜索词 = '音频';
const 目标 = 'canvas-search-result-node_tadm1nyykc';
const H = 720;
const 宽集 = [];
for (let w = 1206; w <= 1234; w += 2) 宽集.push(w);
const 帧间隔 = 700;
const 最大帧数 = 24;

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b205b', 目标testid: 目标, 高度固定: H, 宽集, 帧间隔ms: 帧间隔, 最大帧数, 档: {} };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

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
    if (!搜索钮) { out.档[w] = { 无效臂: '找不到搜索钮' }; await p.close(); continue; }
    await p.mouse.click(搜索钮[0], 搜索钮[1]);
    await p.waitForTimeout(1500);

    const 有输入框 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      if (!e) return false;
      e.focus(); e.select();
      return true;
    });
    if (!有输入框) { out.档[w] = { 无效臂: '找不到搜索输入框' }; await p.close(); continue; }
    await p.keyboard.press('Backspace');
    await p.waitForTimeout(250);
    await p.keyboard.type(搜索词, { delay: 90 });
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
    }, 目标);
    const 输入断言 = { 判据: `输入框回读 === "${搜索词}"`, 回读: 输入回读, 通过: 输入回读 === 搜索词 };
    if (!前置.存在 || !输入断言.通过) {
      out.档[w] = { 无效臂: !前置.存在 ? '目标行不在' : '输入没进去', 前置, 输入断言 };
      log(`${w} ⛔ 无效臂`);
      await p.close(); continue;
    }

    await p.mouse.click(前置.点[0], 前置.点[1]);

    // —— 长采样：采到连续 4 帧完全相同 ——
    const 轨迹 = [];
    let 稳定起 = -1;
    for (let k = 0; k < 最大帧数; k++) {
      const f = await p.evaluate((tid) => {
        const id = tid.replace('canvas-search-result-node_', 'node_');
        const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
        const vp = document.querySelector('.react-flow__viewport');
        const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
        if (!n) return { 找不到: true };
        const r = n.getBoundingClientRect();
        return { cx: Math.round((r.x + r.width / 2) * 10000) / 10000, cy: Math.round((r.y + r.height / 2) * 10000) / 10000,
          vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null };
      }, 目标);
      轨迹.push(f);
      const s = f.vp ? JSON.stringify(f.vp) : null;
      if (轨迹.length >= 5) {
        const 后4 = 轨迹.slice(-4).map((q) => JSON.stringify(q.vp));
        if (后4.every((x) => x === 后4[0])) { 稳定起 = 轨迹.length - 3; break; }
      }
      await p.waitForTimeout(帧间隔);
    }
    const 末 = 轨迹[轨迹.length - 1];

    // —— 收敛后的几何 ——
    const 几何 = await p.evaluate((tid) => {
      const id = tid.replace('canvas-search-result-node_', 'node_');
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; };
      // 扫一遍：有没有元素的下边界 ≈ 519、或中心 ≈ 260（用来解释 中心Y 从 360 变成 ~260）
      const 候选 = [];
      for (const e of document.querySelectorAll('.react-flow > *, .react-flow__renderer > *, [data-testid]')) {
        const r = e.getBoundingClientRect();
        if (r.width < 40 || r.height < 40) continue;
        if (Math.abs(r.bottom - 519) < 12 || Math.abs((r.y + r.height / 2) - 260) < 12) {
          候选.push({ testid: e.getAttribute('data-testid'), tag: e.tagName, 盒: box(e) });
        }
        if (候选.length > 8) break;
      }
      return {
        reactFlow: box(document.querySelector('.react-flow')),
        节点: box(n),
        搜索面板: box(document.querySelector('[data-testid="canvas-feature-panel"]')),
        面板开: !!document.querySelector('[data-testid="canvas-feature-panel"]'),
        缩放aria: (() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; })(),
        候选,
      };
    }, 目标);

    const 收敛 = 稳定起 > 0;
    out.档[w] = {
      前置: { 总条数: 前置.总条数 }, 输入断言, 轨迹, 稳定起, 收敛,
      末, 几何,
      断言: { 判据: '连续 4 帧 vp 三元组完全相同', 通过: 收敛, 采样帧数: 轨迹.length },
    };
    log(`${w} | 收敛=${收敛}(第${稳定起}帧起) | 末 tx=${末.vp && 末.vp[0]} ty=${末.vp && 末.vp[1]} s=${末.vp && 末.vp[2]} | 中心=${末.cx},${末.cy} | 缩放aria=${几何.缩放aria} | 面板${几何.面板开 ? '开' : '关'}${几何.搜索面板 ? JSON.stringify(几何.搜索面板) : ''}`);
  } catch (e) {
    out.档[w] = { 出错: e.message };
    log(`${w} 🔴 ${e.message}`);
  } finally { await p.close(); }
}

fs.writeFileSync('/tmp/b205b.json', JSON.stringify(out, null, 1));
log(`\n写入 /tmp/b205b.json`);
process.exit(0);
