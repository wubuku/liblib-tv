/**
 * 批次 228b（决定性探针）：**批次 226 为什么会判成「新节点搜不到」？**
 *
 * 批次 228 的结论是「新节点**立刻**就能搜到」（t=0/10s/60s/重开页 共 8/8 命中，
 * 阳性对照 4/4 命中），而批次 226 写下的却是「新建节点根本不进搜索索引，21 臂全部候选词都没命中」。
 * 两批结论**直接冲突**，必须有一批错。
 *
 * 📌 嫌疑点（读代码读出来的，不是猜的）：
 *   批次 226 的结果行定位函数是
 *     `document.querySelector('[data-testid="canvas-search-result-node_<id 不带 node_ 前缀>"]')`
 *   它**要求那一行带一个 data-testid**，找不到就返回 null ⇒ 报「候选词都没命中」。
 *   而批次 228 的侦察（`jimeng-b228-recon.mjs`）实测：结果行**既没有 `data-id`、
 *   也没有 `role="option"`** ⇒ 用「按 id 找行」这条路，可能从一开始就找不到。
 *
 * 🔴 本脚本要钉死的正是这一点：**新建节点的搜索结果行，到底有没有那个 data-testid。**
 *   做法是同一时刻把两条都 dump 出来对照 —— 「早就存在的节点」vs「刚建的节点」，
 *   **只差一个变量**（是不是新建的）。若前者有、后者没有 ⇒ 批次 226 判负的是**读法**，不是产品。
 *
 * ⛔ 只新建 / 删除本会话自己创建的**一个**节点；不触发生成、不进入扣费页。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b228b.json';
const log = (...a) => console.log(a.join(' '));
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const page = await ctx.newPage();
const out = {};
let 自建 = null;

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => ({
  id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
})));

/** 搜一个词，然后把结果行的**全部属性**原样 dump 出来。 */
async function dump行(p, 词) {
  const 钮 = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('button, [role="button"]'))
      .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  });
  if (!钮) return { 错: '找不到搜索钮' };
  await p.mouse.click(钮[0] + 钮[2] / 2, 钮[1] + 钮[3] / 2);
  await page.waitForTimeout(1500);
  await p.evaluate(() => {
    const inp = Array.from(document.querySelectorAll('input'))
      .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
    inp.focus(); inp.select();
  });
  await p.keyboard.type(词, { delay: 80 });
  await p.waitForTimeout(2400);

  const r = await p.evaluate(() => {
    const 列表 = document.querySelector('[role="list"]');
    const 行 = 列表 ? Array.from(列表.querySelectorAll('*')).filter((e) => (e.innerText || '').trim().length > 0 && e.getBoundingClientRect().height > 8) : [];
    return {
      回读: (() => { const i = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索')); return i ? i.value : null; })(),
      空态: (() => { const s = document.querySelector('[data-testid="canvas-search-panel"] [role="status"]'); return s ? (s.innerText || '').trim() : null; })(),
      行: 行.slice(0, 8).map((e) => {
        const attrs = {};
        for (const a of Array.from(e.attributes)) attrs[a.name] = String(a.value).slice(0, 80);
        return { 标签: e.tagName, 属性: attrs, 文本: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 50) };
      }),
    };
  });

  await p.keyboard.press('Escape');
  await p.waitForTimeout(900);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(700);
  return r;
}

try {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('.react-flow__node', { timeout: 45000 });
  await page.waitForTimeout(4500);

  // ---- 对照 A：早就存在的节点 ----
  out.对照_既存 = await dump行(page, '音频 68');
  log('【对照·既存「音频 68」】回读=' + out.对照_既存.回读 + ' 空态=' + out.对照_既存.空态);
  (out.对照_既存.行 || []).forEach((r) => log('   行 ' + JSON.stringify(r)));

  // ---- 建一个新节点 ----
  const 建前 = (await 清单(page)).map((n) => n.id);
  const 入口 = await page.evaluate(() => {
    const e = Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '视频');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  });
  if (!入口) throw new Error('找不到「视频」入口');
  await page.mouse.click(入口[0] + 入口[2] / 2, 入口[1] + 入口[3] / 2);
  await page.waitForTimeout(3800);
  const 新增 = (await 清单(page)).filter((n) => !建前.includes(n.id));
  if (新增.length !== 1) throw new Error('新建节点数不是 1');
  自建 = 新增[0];
  out.新建 = 自建;
  log('【新建】' + JSON.stringify(自建));

  // ---- 对照 B：刚建的新节点 ----
  const 短名 = String(自建.aria).replace(/^.*?node:\s*/, '');
  out.对照_新建 = await dump行(page, 短名);
  out.对照_新建.用词 = 短名;
  log(`【对照·新建「${短名}」】回读=${out.对照_新建.回读} 空态=${out.对照_新建.空态}`);
  (out.对照_新建.行 || []).forEach((r) => log('   行 ' + JSON.stringify(r)));

  // ---- 决定性判据：批次 226 用的那条选择器，两边分别能不能命中 ----
  const 查选择器 = async (p, id) => p.evaluate((nid) => {
    const s = '[data-testid="canvas-search-result-node_' + nid.replace(/^node_/, '') + '"]';
    const e = document.querySelector(s);
    return { 选择器: s, 命中: !!e, 行数: document.querySelectorAll('[role="list"] *').length };
  }, id);
  out.选择器_既存 = await 查选择器(page, 'node_tadm1nyykc');   // 音频 68
  out.选择器_新建 = await 查选择器(page, 自建.id);
  log('【批次 226 的选择器·既存】' + JSON.stringify(out.选择器_既存));
  log('【批次 226 的选择器·新建】' + JSON.stringify(out.选择器_新建));
} catch (e) { out.出错 = e.message; log('🔴 ' + e.message); }

// ---- 收尾：删掉自建节点（Backspace，批次 228 实测 Delete 无效） ----
if (自建) {
  try {
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
    const 点 = await page.evaluate((nid) => {
      const el = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      for (let dy = -r.height / 4; dy <= r.height / 4; dy += 6) {
        for (let dx = -r.width / 4; dx <= r.width / 4; dx += 6) {
          const x = Math.round(r.x + r.width / 2 + dx);
          const y = Math.round(r.y + r.height / 2 + dy);
          const h = document.elementFromPoint(x, y);
          if (h && h.closest(`.react-flow__node[data-id="${nid}"]`) && !h.closest('[role="dialog"], button, a, input, textarea')) return [x, y];
        }
      }
      return null;
    }, 自建.id);
    if (点) {
      await page.mouse.click(点[0], 点[1]);
      await page.waitForTimeout(1200);
      await page.keyboard.press('Backspace');
      await page.waitForTimeout(2400);
    }
    out.删除 = { id: 自建.id, 还在: (await 清单(page)).some((n) => n.id === 自建.id) };
    log('【删除】' + JSON.stringify(out.删除));
  } catch (e) { log('🔴 删除 ' + e.message); }
}

try {
  out.收尾 = await page.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
  log('【收尾】' + out.收尾);
} catch (e) { /* 忽略 */ }

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
try { await page.close(); } catch (e) { /* 忽略 */ }
await b.close();