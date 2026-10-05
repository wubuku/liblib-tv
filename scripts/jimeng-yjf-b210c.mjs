// 会话 mvs_fb62b78 · 批次 210 c 轮：**每档新开页**重做密集扫描（a 轮那个常数是假的）。
//
// 🔴 为什么必须重做：
//   b 轮只变一个变量，得到 ——
//     1200：复用页 ty = −44.5555、新开页 ty = −44.5555   ⇒ **逐字相同**（分支 A 不受影响）
//     1280：复用页 ty = −156.555 、新开页 ty = −144.773   ⇒ **差 11.782**
//   而新开页@1280 的 −144.773 与批次 200 的 −145.169 / 批次 198 的 −144.596 同族（差 ≤0.6）
//   ⇒ **批次 200 的 C ≈ −508 是对的；a 轮那个 C = −519.435 是被「复用页 carryover」污染出来的。**
//   carryover 的机制：复用页 resize 之后，**取景落点不会立刻按新宽度重算**，
//   会带着上一档的落点（b 轮复用页@1280 的 6 帧里同时出现 −44.5556 与 −156.555 两个值）。
//
// ⇒ 立规 88：**「每一档都换一个干净状态」不是洁癖，是读绝对值的必要条件。**
//   复用同一页签只适合读**差值/相对关系**（比如断点在哪两档之间变），
//   **不适合读某个量的绝对常数** —— 因为上一个自变量的残值会留在里面。
//
// 本轮：每档 **newPage + goto + 用完 close**（与批次 200 同条件；批次 201 已把有头弹窗这个放大器去掉）。
// 每档同时记两个量：**加载后的初始 vp** 与 **取景后的 vp**。
//   初始 vp 顺带验批次 199 那条「12 档初始平移逐字相同」—— 它只在一页复用时成立，
//   新开页时初始 tx 逐字不同（b 轮已见 1200 → 57.1509、1280 → 97.1509）。
import fs from 'node:fs';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 搜索词 = '音频';
const 目标 = 'canvas-search-result-node_tadm1nyykc';
const H = 720;
const 高度系数 = 0.504;
const 宽度集 = [1200, 1210, 1215, 1220, 1225, 1230, 1240, 1260, 1280];
const log = (...a) => console.log(a.join(' '));
const OUT = '/tmp/b210c.json';
const out = { 轮次: 'b210c', 条件: '每档 newPage + goto + 用完 close',
  为什么: 'a 轮用一页复用 ⇒ 取景落点带上一档残值 ⇒ 绝对常数是假的（立规 88）',
  测的两个量: ['加载后的初始 vp', '取景后的 vp'], 高度系数, 高度固定: H, 无效臂: 0, 档: {} };

const { chromium } = await import('playwright');
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const 共享页 = ctx.pages().find((x) => x.url().includes('ai-canvas'));
out.共享页_前 = await 共享页.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);

const 读vp = () => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null;
};

for (const w of 宽度集) {
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: w, height: H });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);

    const 初始 = await p.evaluate(读vp);        // ← 量 ①：加载后的初始 vp

    // 🔴 清场必须在开面板**之前**（立规 87：纪律要贴在取点那一行，不能只写在文件头）
    await p.keyboard.press('Escape');
    await p.waitForTimeout(400);
    const 搜索钮 = await p.evaluate(() => {
      const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
        || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    });
    if (!搜索钮) { out.档[w] = { 无效: '找不到搜索钮', 初始 }; out.无效臂++; log(w, '⛔ 找不到搜索钮'); continue; }
    await p.mouse.click(搜索钮[0], 搜索钮[1]);
    await p.waitForTimeout(1200);
    await p.evaluate(() => {
      const e = document.querySelector('input[aria-label*="搜索"],input[type="text"]');
      if (e) {
        Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(e, '');
        e.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
    await p.keyboard.type(搜索词, { delay: 90 });   // 点完结果行之后一个键都不按
    await p.waitForTimeout(2000);

    const 前置 = await p.evaluate((tid) => {
      const e = document.querySelector(`[data-testid="${tid}"]`);
      const id = tid.replace('canvas-search-result-node_', 'node_');
      if (!e) return { 存在: false, 节点在: !!document.querySelector(`.react-flow__node[data-id="${id}"]`),
        现存前5: Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).slice(0, 5).map((x) => x.getAttribute('data-testid')) };
      const r = e.getBoundingClientRect();
      return { 存在: true, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        总条数: document.querySelectorAll('[data-testid^="canvas-search-result-node_"]').length,
        节点在: !!document.querySelector(`.react-flow__node[data-id="${id}"]`) };
    }, 目标);
    if (!前置.存在 || !前置.节点在) {
      out.档[w] = { 无效: !前置.存在 ? '目标行不在' : '画布上找不到目标节点', 前置, 初始 };
      out.无效臂++; log(w, '⛔ 无效臂', JSON.stringify(前置).slice(0, 90)); continue;
    }

    await p.mouse.click(前置.点[0], 前置.点[1]);
    const 帧 = [];
    for (let k = 0; k < 6; k++) { 帧.push(await p.evaluate(读vp)); await p.waitForTimeout(600); }

    const 有效帧 = 帧.filter((f) => f && f.length === 3 && Number.isFinite(f[1]));  // 立规 86
    if (有效帧.length === 0) { out.档[w] = { 无效: '6 帧全空', 帧, 初始 }; out.无效臂++; log(w, '⛔ 6 帧全空'); continue; }

    const ty集合 = [...new Set(帧.map((f) => f && f[1]))];
    const tx集合 = [...new Set(帧.map((f) => f && f[0]))];
    const sc集合 = [...new Set(帧.map((f) => f && f[2]))];
    const ty终 = ty集合[ty集合.length - 1];
    out.档[w] = {
      初始, 前置, 帧, 有效帧数: 有效帧.length,
      ty取值: ty集合, tx取值: tx集合, scale取值: sc集合,
      ty终值: ty终,
      C终值: Math.round((ty终 - 高度系数 * H) * 1000) / 1000,
      初始tx: 初始 ? 初始[0] : null,
      初始tx减半宽: 初始 ? Math.round((初始[0] - w / 2) * 10000) / 10000 : null,
      断言: { 读到数了: 有效帧.length > 0, ty收敛: ty集合.length === 1 },
    };
    log(w, '| 初始tx', 初始 && 初始[0], '| ty终', ty终, '| C', out.档[w].C终值,
      '| ty取值', JSON.stringify(ty集合), '| 收敛', ty集合.length === 1);
  } catch (e) { out.档[w] = { 出错: e.message }; out.无效臂++; log(w, '🔴', e.message); }
  finally { try { await p.close(); } catch {} fs.writeFileSync(OUT, JSON.stringify(out, null, 1)); }
}

out.共享页_后 = await 共享页.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);
log('\n共享页 前/后：', JSON.stringify(out.共享页_前), '→', JSON.stringify(out.共享页_后));
log('无效臂：', out.无效臂, '/', 宽度集.length);
const 行 = 宽度集.filter((w) => out.档[w] && out.档[w].ty终值 != null)
  .map((w) => `${w}: ty=${out.档[w].ty终值} C=${out.档[w].C终值} 初始tx=${out.档[w].初始tx}`);
log('\n=== 汇总 ===\n' + 行.join('\n'));
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
await b.close();
