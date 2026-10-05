/**
 * 批次 228c：把「**同一页**」与「**换页后**」分开测 —— 批次 226 与 228 的冲突可能就出在这里。
 *
 * 已知事实（都有读数）：
 *   批次 228：在**建完节点的同一个页面**里搜，`视频 2` **立刻**就有结果行
 *     （`data-testid="canvas-search-result-node_<id>"`，与既存节点逐字同构）⇒ 8/8 命中。
 *   批次 226：建完节点后**另开新页**去搜，21 臂全部「候选词都没命中那一行」。
 * ⇒ 两者唯一的差别就是「**在不在建节点的那一页**」。
 * ⚠️ 所以现在**不能**简单说批次 226 错了：也可能产品真是「本页立即可搜、换页要等索引」。
 *    这两件事对用户意义完全不同，必须分开测。
 *
 * 本脚本做**受控对照**，只差一个变量（在哪一页搜）：
 *   ① 页 A（建节点的那一页）：t≈5s / 30s / 90s 各搜一次
 *   ② 页 B（建完后另开的新页）：t≈5s / 30s / 90s 各搜一次
 *   每一步都记：结果行是否存在、行数、批次 226 那条 testid 选择器能不能命中、
 *   以及阳性对照（既存的 `音频 68`）在**同一页同一时刻**能不能搜到。
 *
 * 判读纪律：
 *   - 阳性对照在页 B 搜不到 ⇒ 那一步读数**作废**（是页 B 的索引整体没建，不是新节点的问题）
 *   - 阳性对照能搜到、只有新节点搜不到 ⇒ 「换页后新节点还没进索引」成立
 *
 * ⛔ 只新建 / 删除本会话自己创建的一个节点。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b228c.json';
const log = (...a) => console.log(a.join(' '));
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const out = { 页A: [], 页B: [] };
let 建好时刻 = 0;
let 自建 = null;

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')));

/** 在指定页面搜一个词，返回**两个正交读量** + 批次 226 的那条选择器能不能命中。 */
async function 读(p, 词, 目标id) {
  const 钮 = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('button, [role="button"]'))
      .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  });
  if (!钮) return { 错: '找不到搜索钮' };
  // 面板可能已开着：开着就直接用，关闭才点按钮
  const 已开 = await p.evaluate(() => !!document.querySelector('[data-testid="canvas-search-panel"] input'));
  if (!已开) { await p.mouse.click(钮[0] + 钮[2] / 2, 钮[1] + 钮[3] / 2); await p.waitForTimeout(1500); }
  const 有框 = await p.evaluate(() => {
    const inp = document.querySelector('[data-testid="canvas-search-panel"] input');
    if (!inp) return false;
    inp.focus(); inp.select();
    return true;
  });
  if (!有框) return { 错: '面板里没有输入框' };
  await p.keyboard.type(词, { delay: 80 });
  await p.waitForTimeout(2400);
  const r = await p.evaluate((id) => {
    const 列表 = document.querySelector('[role="list"]');
    const 状态 = document.querySelector('[data-testid="canvas-search-panel"] [role="status"]');
    const tabs = Array.from(document.querySelectorAll('[data-testid="canvas-search-panel"] [role="tab"]'))
      .map((t) => (t.innerText || '').replace(/\s+/g, ' ').trim());
    const sel = '[data-testid="canvas-search-result-node_' + String(id).replace(/^node_/, '') + '"]';
    return {
      回读: (document.querySelector('[data-testid="canvas-search-panel"] input') || {}).value || null,
      空态: 状态 ? (状态.innerText || '').trim() : null,
      可见行数: 列表 ? Array.from(列表.querySelectorAll('[data-node-id]')).length : 0,
      列表文本: 列表 ? (列表.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) : null,
      带计数tab数: tabs.filter((t) => /\d/.test(t)).length,
      目标选择器命中: id ? !!document.querySelector(sel) : null,
      目标选择器: id ? sel : null,
    };
  }, 目标id || null);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(800);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(600);
  return r;
}

const 页A = await ctx.newPage();
let 页B = null;
try {
  await 页A.setViewportSize({ width: 1280, height: 720 });
  await 页A.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await 页A.waitForSelector('.react-flow__node', { timeout: 45000 });
  await 页A.waitForTimeout(4500);

  // ---- 建节点 ----
  const 建前 = await 清单(页A);
  const 入口 = await 页A.evaluate(() => {
    const e = Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '视频');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  });
  await 页A.mouse.click(入口[0] + 入口[2] / 2, 入口[1] + 入口[3] / 2);
  await 页A.waitForTimeout(3800);
  const 新增 = (await 清单(页A)).filter((n) => !建前.includes(n));
  if (新增.length !== 1) throw new Error('新建节点数不是 1：' + 新增.length);
  自建 = 新增[0];
  建好时刻 = Date.now();
  const 短名 = await 页A.evaluate((nid) => {
    const el = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    return el ? String(el.getAttribute('aria-label') || '').replace(/^.*?node:\s*/, '') : null;
  }, 自建);
  out.新建 = { id: 自建, 短名, 建于: new Date(建好时刻).toISOString() };
  log('【新建】' + JSON.stringify(out.新建));

  // ---- 另开页 B（批次 226 的条件） ----
  页B = await ctx.newPage();
  await 页B.setViewportSize({ width: 1280, height: 720 });
  await 页B.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await 页B.waitForSelector('.react-flow__node', { timeout: 45000 });
  await 页B.waitForTimeout(4500);
  const 在页B = await 清单(页B);
  log(`【页 B 已开】节点在页 B 上：${在页B.includes(自建)}（共 ${在页B.length} 个）`);

  // ---- 受控对照：三个时间点 × 两页 ----
  for (const 目标秒 of [5, 30, 90]) {
    const 已过 = Math.round((Date.now() - 建好时刻) / 1000);
    if (目标秒 > 已过) await 页A.waitForTimeout((目标秒 - 已过) * 1000);
    const 距 = Math.round((Date.now() - 建好时刻) / 1000);

    const a对照 = await 读(页A, '音频 68', null);
    const a目标 = await 读(页A, out.新建.短名, 自建);
    out.页A.push({ 距建好秒: 距, 对照: a对照, 目标: a目标 });
    log(`【页 A · ${距}s】对照 ${a对照.可见行数 !== undefined ? (a对照.可见行数 > 0 ? '✅' : '⛔') + a对照.列表文本 : JSON.stringify(a对照)} ｜ 目标 ${a目标.可见行数 !== undefined ? (a目标.可见行数 > 0 ? '✅' : '⛔') + (a目标.列表文本 || a目标.空态) : JSON.stringify(a目标)} ｜ 226选择器=${a目标.目标选择器命中}`);

    const b对照 = await 读(页B, '音频 68', null);
    const b目标 = await 读(页B, out.新建.短名, 自建);
    out.页B.push({ 距建好秒: 距, 对照: b对照, 目标: b目标 });
    log(`【页 B · ${距}s】对照 ${b对照.可见行数 !== undefined ? (b对照.可见行数 > 0 ? '✅' : '⛔') + b对照.列表文本 : JSON.stringify(b对照)} ｜ 目标 ${b目标.可见行数 !== undefined ? (b目标.可见行数 > 0 ? '✅' : '⛔') + (b目标.列表文本 || b目标.空态) : JSON.stringify(b目标)} ｜ 226选择器=${b目标.目标选择器命中}`);
  }
} catch (e) { out.出错 = e.message; log('🔴 ' + e.message); }

// ---- 收尾：删掉自建节点 ----
if (自建) {
  for (const p of [页A, 页B].filter(Boolean)) {
    try {
      await p.keyboard.press('Escape');
      await p.waitForTimeout(400);
      const 点 = await p.evaluate((nid) => {
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
      }, 自建);
      if (!点) continue;
      await p.mouse.click(点[0], 点[1]);
      await p.waitForTimeout(1200);
      await p.keyboard.press('Backspace');
      await p.waitForTimeout(2400);
      const 还在 = (await 清单(p)).includes(自建);
      log(`【删除·${p === 页A ? '页A' : '页B'}】还在=${还在}`);
      if (!还在) break;
    } catch (e) { log('🔴 删除 ' + e.message); }
  }
  out.删除 = { id: 自建, 页A还在: (await 清单(页A)).includes(自建), 页B还在: 页B ? (await 清单(页B)).includes(自建) : null };
}

out.收尾 = await 页A.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
log('【收尾】' + out.收尾);
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
for (const p of [页A, 页B].filter(Boolean)) { try { await p.close(); } catch (e) { /* 忽略 */ } }
await b.close();