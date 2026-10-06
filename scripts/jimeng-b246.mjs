/**
 * 批次 246：音频凹口的地板**跟不跟画布当前缩放走**？
 *
 * 📌 线索：音频凹口的地板**恰好等于画布默认缩放 `0.260267`**，
 *   而其余三族的地板都是「屏上 `100px`」换算出来的
 *   （文本 `0.3125`、时间线 `0.0833333`、图像 `0.175781`）
 *   ⇒ **性质不同**。两种可能，本批把它们分开：
 *     ① 音频地板**真的是「当前画布缩放」** ⇒ 先把缩放改小再定位，地板应跟着变小；
 *     ② 它只是**碰巧**等于项目默认缩放 ⇒ 改小缩放后地板仍是 `0.260267`。
 *
 * 🔴 纪律：
 *   · **正交读量**：改完缩放必须先读 `canvas-zoom-percent` 确认改动生效，**再**点搜索结果行；
 *   · **不点结果行之外的任何东西**，不新建、不删除、不上传、不触发生成；
 *   · 缩放**不跨页面持久化**（批次 246 试点实测：新开页仍是 `0.260267`）⇒ 每臂开新页即可，无需手动还原；
 *   · **两组对照**（同一臂里各定位一次太贵，分成两臂）：
 *       A. 音频 68 ⇒ 若地板跟缩放走，落点应是 `0.217`；否则 `0.260267`
 *       B. 文本 3  ⇒ 若地板是「屏上 100px」这个**绝对量**，改缩放后应**仍是 `0.3125`**
 *
 * 用法：node scripts/jimeng-b246.mjs   （读数落盘 /tmp/b246.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b246.json';
const 视口宽 = 1212;                 // 音频凹口的起点；文本在这个宽度恒为 0.5（作对照）
const 缩小一次后 = 0.217;             // 试点实测：⌘− 一次 0.260267 → 0.217
// 🔴🔴 **第一版把 B 臂的视口宽也设成了 1212，那是错的** —— 文本在 `1212` 恒为 `0.5`（封顶），
//   **根本没碰到它的地板**（地板只出现在 `w ≤ 632`）。它实际只回答了「封顶支依不依赖当前缩放」
//   （答案：不依赖），**没有回答地板的问题**。
//   ⇒ 第三臂把文本放到 `w = 600`，那里才有地板（实测 `0.3125`）。
const 两臂 = [
  { 名: '音频 68 @1212', id: 'node_tadm1nyykc', 宽: 1212, 词: ['音频 68', '音频'],
    改缩放后预期: [缩小一次后, 0.260267], 说明: '凹口地板若跟当前画布缩放走 ⇒ 0.217；若只是碰巧等于默认值 ⇒ 仍是 0.260267' },
  { 名: '文本 3 @1212（封顶支，作废重测）', id: 'node_5gftn3dnt1', 宽: 1212, 词: ['测试文字样例', '文字样例', '测试'],
    改缩放后预期: [0.5], 说明: '第一版这臂想测地板，但 1212 是封顶区 ⇒ 只能测「封顶支依不依赖当前缩放」' },
  { 名: '文本 3 @600（真地板）', id: 'node_5gftn3dnt1', 宽: 600, 词: ['测试文字样例', '文字样例', '测试'],
    改缩放后预期: [0.3125, 缩小一次后],
    说明: '地板若是「屏上 100px」这个**绝对量** ⇒ 仍是 0.3125；若是「当前缩放」⇒ 0.217。**这才是原本要问的那一问**' },
];

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b246', 视口宽, 臂: [] };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const 臂 of 两臂) {
  const p = await ctx.newPage();
  const 记 = { 臂: 臂.名, 宽: 臂.宽, 说明: 臂.说明 };
  try {
    await p.setViewportSize({ width: 臂.宽, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(5000);

    const 读缩放 = () => p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
      return { scale: m ? Number(m[1]) : null, aria: z ? z.getAttribute('aria-label') : null };
    });

    记.定位前缩放 = await 读缩放();

    // ---- 先缩小一次，**确认生效**再点结果行（正交读量） ----
    await p.keyboard.press('Meta+-');
    await p.waitForTimeout(1500);
    记.缩小后缩放 = await 读缩放();
    log(`【${臂.名}】定位前缩放 ${记.定位前缩放.scale} → ⌘− 后 ${记.缩小后缩放.scale}（${记.缩小后缩放.aria}）`);
    if (记.缩小后缩放.scale === 记.定位前缩放.scale) throw new Error('⌘− 没改到缩放，本臂作废（不改机制、不猜）');

    // ---- 搜索 → 点结果行定位 ----
    const 钮 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('button, [role="button"]'))
        .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
    });
    if (!钮) throw new Error('找不到搜索钮');
    await p.mouse.click(钮[0] + Math.round(钮[2] / 2), 钮[1] + Math.round(钮[3] / 2));
    await p.waitForTimeout(1500);
    await p.evaluate(() => {
      const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
      if (inp) { inp.focus(); inp.select(); }
    });

    const 短名 = 臂.id.replace(/^node_/, '');
    let 点 = null;
    for (const 词 of 臂.词) {
      await p.evaluate(() => {
        const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
        if (inp) { inp.focus(); inp.select(); }
      });
      await p.keyboard.type(词, { delay: 85 });
      await p.waitForTimeout(2200);
      const 读行 = await p.evaluate((nid) => {
        const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
        const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
        return { 回读: inp ? inp.value : null, 有行: !!e };
      }, 短名);
      if (读行.有行 && 读行.回读 === 词) {
        点 = await p.evaluate((nid) => {
          const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
          if (!e) return null;
          const r = e.getBoundingClientRect();
          return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
        }, 短名);
        if (点) { await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(5000); 记.用的词 = 词; break; }
      }
    }
    if (!点) throw new Error('候选词都没命中那一行');
    await p.keyboard.press('Escape');
    await p.waitForTimeout(600);
    await p.keyboard.press('Escape');
    await p.waitForTimeout(900);

    记.定位后 = await p.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
      const nr = n ? n.getBoundingClientRect() : null;
      return {
        落点: m ? Number(m[1]) : null,
        aria: z ? z.getAttribute('aria-label') : null,
        屏上: nr ? [Math.round(nr.width), Math.round(nr.height)] : null,
        中心Y: nr ? Math.round(nr.y + nr.height / 2) : null,
        状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
      };
    }, 臂.id);

    记.落在预期内 = 臂.改缩放后预期.some((v) => Math.abs(记.定位后.落点 - v) < 1e-4);
    log(`【${臂.名}】定位后落点 ${记.定位后.落点}（${记.定位后.aria}）｜ 屏上 ${JSON.stringify(记.定位后.屏上)} ｜ 中心Y ${记.定位后.中心Y}`);
    log(`        预期 ${JSON.stringify(臂.改缩放后预期)} ⇒ ${记.落在预期内 ? '✅ 命中其中一个' : '🔴 都不符'}`);
  } catch (e) {
    记.错误 = e.message;
    log(`🔴 ${臂.名} ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
  }
  out.臂.push(记);
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
}

log('写入 ' + OUT);
await b.close();