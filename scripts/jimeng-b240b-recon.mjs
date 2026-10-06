/**
 * 批次 240b 只读侦察：**空文本节点到底在不在搜索索引里？**
 *
 * 📌 起因：批次 240 用「点搜索结果行」定位节点时，`文本 3`（标题逐字「测试文字样例」）
 *   一切正常，而 `文本 1` / `文本 2`（标题逐字都是「双击编辑文本」，**空内容占位**）
 *   **5 臂全部「候选词都没命中那一行」**。
 *   ⇒ 必须先分清是「**它不在索引里**」还是「**我搜的词不对**」，否则会写下一个错的结论。
 *
 * 🔴 纪律：**只读** —— 只看搜索面板的结果行，**绝不点结果行**。
 *   判据用**两个正交读量**（立规：搜索命中必须只读判定）：
 *     ① `div[role="list"]` 里到底有没有行；
 *     ② 每个 `button[role="tab"]` 上的**计数**（逐字读）。
 *   两个读量必须同时为「有」，才算命中。
 *
 * 用法：node scripts/jimeng-b240b-recon.mjs   （读数落盘 /tmp/b240b-recon.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b240b-recon.json';
const 词表 = ['测试文字样例', '双击编辑文本', '双击', '编辑文本', '文本'];
/** 画布上三个文本节点的 id（来自批次 236 普查 `/tmp/b236.json`）。 */
const 三节点 = {
  node_3bfb9r79qe: '文本 1（z=0，空）',
  node_aw29cp094x: '文本 2（z=2，空）',
  node_5gftn3dnt1: '文本 3（z=3，有内容）',
};

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b240b-recon', 词表: [] };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = await ctx.newPage();

try {
  await p.setViewportSize({ width: 1280, height: 720 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(4500);

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

  for (const 词 of 词表) {
    await p.evaluate(() => {
      const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
      if (inp) { inp.focus(); inp.select(); }
    });
    await p.keyboard.type(词, { delay: 85 });
    await p.waitForTimeout(2200);

    const 读 = await p.evaluate((ids) => {
      const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
      // 读量 ①：结果列表容器里到底有没有行（逐个列出 testid，不靠前缀猜）
      const 行 = Array.from(document.querySelectorAll('[role="list"] [role="listitem"], [role="list"] button, [role="list"] li'))
        .map((e) => ({
          testid: e.getAttribute('data-testid'),
          文本: (e.innerText || '').replace(/\n/g, ' | ').slice(0, 80),
        }));
      // 读量 ②：各分类 tab 上的计数
      const tab = Array.from(document.querySelectorAll('button[role="tab"]'))
        .map((e) => (e.innerText || '').replace(/\n/g, ' ').trim());
      const 命中 = {};
      for (const id of Object.keys(ids)) {
        命中[id] = !!document.querySelector(`[data-testid="canvas-search-result-node_${id.replace(/^node_/, '')}"]`);
      }
      return { 回读: inp ? inp.value : null, 列表容器数: document.querySelectorAll('[role="list"]').length, 行, tab, 命中 };
    }, 三节点);

    out.词表.push({ 词, ...读 });
    log(`词「${词}」→ 列表容器 ${读.列表容器数} 个｜行 ${读.行.length} 条｜tab ${JSON.stringify(读.tab)}`);
    for (const r of 读.行) log(`    行 testid=${r.testid}  「${r.文本}」`);
    log(`    三节点命中：${JSON.stringify(读.命中)}`);
  }

  await p.keyboard.press('Escape');
  await p.waitForTimeout(500);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(800);
} catch (e) {
  out.错误 = e.message;
  log('🔴 ' + e.message);
} finally {
  try { await p.close(); } catch (e) { /* 忽略 */ }
}

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
await b.close();
