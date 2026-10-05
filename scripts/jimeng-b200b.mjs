// 批次 200 b 轮：重做 a 轮那 **18 条全是无效臂**的取景（立规 65 的一次集中发生）。
//
// a 轮做错的地方：每点完一条就按 **Esc** 想「回到起点」—— 但 Esc 是**关掉整个搜索面板**，
//   下一轮自然找不到那些行了。⇒ 18 次取景全部无效，只拿到两条与取景无关的读数。
//
// 📌 正确做法（立规 65 的正向用法）：**动作没生效就别把它当读数**，
//   而 a 轮脚本**没有判「这一臂到底有没有生效」**就直接继续了 —— 这才是真正要修的地方。
//   本轮每一臂都带**有效性断言**：点之前必须能读到该行的 testid，读不到 ⇒ 标无效臂、跳过。
//
// 本轮只做一件事：对**同一个 testid**（不是「第一条」）在 6 档视口下取景，
//   看落点与 ty 到底跟不跟视口走。
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 搜索词 = '音频';
const 视口集 = [
  { 名: '1000x720', w: 1000, h: 720 }, { 名: '1200x720', w: 1200, h: 720 },
  { 名: '1280x600', w: 1280, h: 600 }, { 名: '1280x720', w: 1280, h: 720 },
  { 名: '1280x840', w: 1280, h: 840 }, { 名: '1600x900', w: 1600, h: 900 },
];
// 目标：a 轮读到的六档**逐字相同**的第 1 条（用它把「对象变了」这个变量彻底钉死）
const 目标 = 'canvas-search-result-node_tadm1nyykc';
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b200b', 目标testid: 目标, 修的是什么: 'a 轮 18 臂全无效（Esc 把面板关了）且没判臂有效性' };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const 共享页 = ctx.pages().find((x) => x.url().includes('ai-canvas'));
out.共享页_前 = await 共享页.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);

out.档 = {};
for (const v of 视口集) {
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: v.w, height: v.h });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);

    // —— 完整的取景流程，**不按 Esc** ——
    const 搜索钮 = await p.evaluate(() => {
      const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
        || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (!搜索钮) { out.档[v.名] = { 无效: '找不到搜索钮' }; continue; }
    await p.mouse.click(搜索钮[0], 搜索钮[1]); await p.waitForTimeout(1500);
    await p.evaluate(() => { const e = document.querySelector('input[aria-label*="搜索"],input[type="text"]');
      if (e) { Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(e, '');
        e.dispatchEvent(new Event('input', { bubbles: true })); } });
    await p.keyboard.type(搜索词, { delay: 90 });
    await p.waitForTimeout(2200);

    // 🔴 臂有效性断言：点之前**必须**读得到那一行
    const 前置 = await p.evaluate((tid) => {
      const e = document.querySelector(`[data-testid="${tid}"]`);
      if (!e) return { 存在: false, 现存前5: Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).slice(0, 5).map((x) => x.getAttribute('data-testid')) };
      const r = e.getBoundingClientRect();
      return { 存在: true, 屏上: [r.x, r.y, r.width, r.height].map(Math.round),
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        aria: e.getAttribute('aria-label'),
        总条数: document.querySelectorAll('[data-testid^="canvas-search-result-node_"]').length };
    }, 目标);

    if (!前置.存在) {
      out.档[v.名] = { 无效: '目标行不在这一页', 前置 };
      log(`${v.名} ⛔ 无效臂：目标行不在（现存前5 = ${JSON.stringify(前置.现存前5)}）`);
      await p.close(); continue;
    }

    await p.mouse.click(前置.点[0], 前置.点[1]);
    // 连采 6 帧：等收敛 + 看是否多相（立规 76）
    const 帧 = [];
    for (let k = 0; k < 6; k++) {
      帧.push(await p.evaluate((tid) => {
        const id = tid.replace('canvas-search-result-node_', 'node_');
        const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return { 找不到: true };
        const r = n.getBoundingClientRect();
        const vp = document.querySelector('.react-flow__viewport');
        const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
        const cm = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
        return { 中心: [Math.round((r.x + r.width / 2) * 10000) / 10000, Math.round((r.y + r.height / 2) * 10000) / 10000],
          屏上: [r.x, r.y, r.width, r.height].map((q) => Math.round(q * 10000) / 10000),
          画布: cm ? [Number(cm[1]), Number(cm[2])] : null,
          vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null };
      }, 目标));
      await p.waitForTimeout(600);
    }
    const 末 = 帧[帧.length - 1];
    const xs = [...new Set(帧.map((f) => f.中心 && f.中心[0]))];
    const ys = [...new Set(帧.map((f) => f.中心 && f.中心[1]))];
    out.档[v.名] = { 前置, 末, 中心X取值: xs, 中心Y取值: ys,
      断言: { 判据: '6 帧去重后 X 与 Y 各只剩 1 个值（已收敛）', X收敛: xs.length === 1, Y收敛: ys.length === 1 } };
    log(`${v.名} | 总条数 ${前置.总条数} | 中心 ${JSON.stringify(末.中心)} | vp ${JSON.stringify(末.vp)} | 画布 ${JSON.stringify(末.画布)}`
      + ` | 收敛 X=${xs.length === 1} Y=${ys.length === 1}`);
  } catch (e) { out.档[v.名] = { 出错: e.message }; log(v.名, '🔴', e.message); }
  finally { await p.close(); }
}

fs.writeFileSync('/tmp/b200b.json', JSON.stringify(out, null, 1));
out.共享页_后 = await 共享页.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);
log('\n共享页 前/后：', JSON.stringify(out.共享页_前), '→', JSON.stringify(out.共享页_后));
await b.close();
