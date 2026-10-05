/**
 * 批次 228：**新建的节点多久之后能被画布搜索找到？**
 *
 * 入口来自批次 226 的失败：第一版新建空 `视频 2` 后 `21` 臂全部「候选词都没命中那一行」，
 * 当时只能记一句「推测新节点没进搜索索引，不下定论」。
 * 本批把那句推测**测成答案** —— 而且这个答案**对用户有直接价值**：
 * 用户建完节点立刻搜不到，到底是操作错了还是系统还没索引完。
 *
 * 🔴 三条方法纪律（前几批踩出来的，不遵守就会得出错的结论）：
 *
 * ① **只读判定命中，绝不点结果行。**
 *    批次 221 起就知道点搜索结果行会触发**取景动画**、改写 viewport transform。
 *    本实验问的是「索引里有没有这一行」，点下去反而把读数污染了。
 *    侦察（`jimeng-b228-recon.mjs`）已经把结构摸清，够只读了：
 *      - 命中 ⇒ `div[role="list"]` 里有行，且各 `button[role="tab"]` 带上计数（如「全部 1」）
 *      - 空 ⇒ `div[role="status"]` 逐字是 `未找到匹配节点`，各 tab **不带**计数
 *    这两条是**两个正交读量**（立规 108）：不能只看其中之一。
 *
 * ② **每一步都带阳性对照。**
 *    「搜不到」有两种可能：新节点没进索引，或者搜索这一会儿坏了。
 *    所以每个时间点都**同时**搜一个画布上早就存在的节点（`音频 68`）。
 *    对照也搜不到 ⇒ 那一步的读数**不能用来判断新节点**，必须重测。
 *
 * ③ **被 kill 掉会留下节点**（批次 226 的失效②：服务端留下了、本地进程没了）。
 *    所以开头先清点孤儿、结尾删净自己建的。
 *
 * ⛔ 本批不触发生成、不进入扣费页、不点「保存到主体库」、不分享、不下载。
 *    只新建 / 改名 / 删除**本会话自己创建的**节点。
 *
 * 用法：node scripts/jimeng-b228.mjs   （原始读数 /tmp/b228.json，日志 /tmp/b228.log）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b228.json';
// 📌 探针闸门会把 `.slice(0, 90)` 里的 `0, 90)` 误判成「数字开头的键」⇒ 一律走命名常量。
const 文本上限 = 70;

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b228', 开始: new Date().toISOString() };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const page = await ctx.newPage();
const 自建 = [];   // 本会话创建的节点，收尾必须删净

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => ({
  id: n.getAttribute('data-id'),
  aria: n.getAttribute('aria-label'),
  cls: typeof n.className === 'string' ? n.className : '',
})));
const 状态行 = (p) => p.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
const 积分 = (p) => p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('*')).find((x) => (x.getAttribute('aria-label') || '').startsWith('Credits'));
  return e ? e.getAttribute('aria-label') : null;
});

/** 只读地读一次搜索结果：输入 query，返回两个正交读量（列表文本 + 各 tab 计数）。 */
async function 搜一次(p, query) {
  // 打开搜索面板
  const 钮 = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('button, [role="button"]'))
      .find((x) => (x.getAttribute('aria-label') || '') === '搜索');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  });
  if (!钮) return { 错: '找不到 aria-label="搜索" 的按钮' };
  await p.mouse.click(钮[0] + 钮[2] / 2, 钮[1] + 钮[3] / 2);
  await p.waitForTimeout(1500);

  const 有框 = await p.evaluate(() => {
    const inp = Array.from(document.querySelectorAll('input'))
      .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
    if (!inp) return false;
    inp.focus(); inp.select();
    return true;
  });
  if (!有框) return { 错: '搜索面板里找不到输入框' };

  await p.keyboard.type(query, { delay: 80 });
  await p.waitForTimeout(2200);

  const 读 = await p.evaluate((上限) => {
    const inp = Array.from(document.querySelectorAll('input'))
      .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
    const 列表 = document.querySelector('[role="list"]');
    const 状态 = document.querySelector('[data-testid="canvas-search-panel"] [role="status"]');
    const tabs = Array.from(document.querySelectorAll('[data-testid="canvas-search-panel"] [role="tab"]'))
      .map((t) => (t.innerText || '').replace(/\s+/g, ' ').trim());
    return {
      回读: inp ? inp.value : null,
      列表文本: 列表 ? (列表.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 上限) : null,
      空态文本: 状态 ? (状态.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 上限) : null,
      tabs,
      列表行数: 列表 ? 列表.children.length : 0,
    };
  }, 文本上限);

  // 判命中：**必须两个正交读量同时成立**（列表有行 + tab 带计数）
  const 带计数的tab = 读.tabs.filter((t) => /\d/.test(t));
  读.判命中 = 读.列表行数 > 0 && 带计数的tab.length > 0;
  读.判空 = (读.空态文本 || '').includes('未找到匹配节点');
  读.用词 = query;
  return 读;
}

/** 一次「测一个词」：搜完就关面板，返回读数。 */
async function 测词(p, 词) {
  try {
    const r = await 搜一次(p, 词);
    await p.keyboard.press('Escape');
    await p.waitForTimeout(900);
    await p.keyboard.press('Escape');
    await p.waitForTimeout(600);
    return r;
  } catch (e) { return { 错: e.message, 用词: 词 }; }
}

/** 候选词阶梯（沿用批次 226 立规 103 的加强版，再加「只取数字部分」）。 */
function 候选(aria) {
  const s = String(aria || '');
  const 去node = s.replace(/^.*?node:\s*/, '');
  const 去kind = 去node.replace(/^[^\d]+\s*/, '');
  const 数字 = (s.match(/\d+/) || [])[0];
  return [...new Set([去node, 去kind, 数字 ? `视频 ${数字}` : '', 数字].filter(Boolean))];
}

// ============ 步骤 0：清点孤儿（批次 226 失效② 的教训） ============
try {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('.react-flow__node', { timeout: 45000 });
  await page.waitForTimeout(4500);
  out.基线 = { 状态行: await 状态行(page), 积分: await 积分(page), 节点数: (await 清单(page)).length };
  log('【基线】' + JSON.stringify(out.基线));
} catch (e) { out.出错 = ['步骤0: ' + e.message]; log('🔴 步骤0 ' + e.message); }

// ============ 步骤 1：建两个新节点（视频 + 文本，各一个 kind） ============
const 新节点 = [];
for (const kind of ['视频', '文本']) {
  try {
    const 建前 = (await 清单(page)).map((n) => n.id);
    const 入口 = await page.evaluate((k) => {
      const e = Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === k);
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
    }, kind);
    if (!入口) throw new Error(`面板上找不到「${kind}」入口`);
    const 归属 = await page.evaluate(([x, y, w, h]) => {
      const el = document.elementFromPoint(x + w / 2, y + h / 2);
      return el ? el.getAttribute('aria-label') : null;
    }, 入口);
    if (归属 !== kind) throw new Error(`「${kind}」入口落点归属不对：${归属}`);
    await page.mouse.click(入口[0] + 入口[2] / 2, 入口[1] + 入口[3] / 2);
    await page.waitForTimeout(3800);
    const 新增 = (await 清单(page)).filter((n) => !建前.includes(n.id));
    if (新增.length !== 1) throw new Error(`新建节点数不是 1：${JSON.stringify(新增.map((n) => n.aria))}`);
    自建.push(新增[0].id);
    新节点.push({ kind, ...新增[0], 建于: Date.now() });
    log(`【新建·${kind}】${JSON.stringify(新增[0])}`);
  } catch (e) { (out.出错 = out.出错 || []).concat(`新建${kind}: ${e.message}`); log(`🔴 新建${kind} ${e.message}`); }
}
out.新节点 = 新节点;
if (!新节点.length) { log('🔴 一个新节点都没建出来，后面的时间点测不了'); }

// ============ 步骤 2：按时间点测「搜不搜得到」 ============
const 时间点 = [
  { 名: 't=0s（刚建完立刻）', 等: 0 },
  { 名: 't=10s', 等: 10000 },
  { 名: 't=60s', 等: 50000 },
];
out.时间线 = [];
for (const tp of 时间点) {
  if (tp.等) await page.waitForTimeout(tp.等);
  const 记录 = { 名: tp.name || tp.名, 距建好秒: Math.round((Date.now() - (新节点[0]?.建于 || Date.now())) / 1000), 测: [] };

  // 阳性对照：画布上早就存在的节点
  const 对照 = await 测词(page, '音频 68');
  记录.阳性对照 = 对照;
  log(`【${记录.名}】阳性对照「音频 68」 → ${对照.错 ? '🔴 ' + 对照.错 : (对照.判命中 ? `✅ 命中（${对照.列表文本}）` : `⛔ 没命中（${对照.空态文本 || 对照.列表文本}）`)}`);

  // 目标：每一个新节点，候选词逐个试
  for (const n of 新节点) {
    const 试词 = [];
    for (const 词 of 候选(n.aria)) {
      if (试词.some((x) => x.用词 === 词)) continue;
      const r = await 测词(page, 词);
      试词.push(r);
      if (r.判命中) break;      // 命中就够了，不必再试更弱的候选
    }
    记录.测.push({ kind: n.kind, aria: n.aria, id: n.id, 试词, 命中: 试词.some((x) => x.判命中) });
    log(`【${记录.名}】${n.kind} ${JSON.stringify(n.aria)} → ${记录.测[记录.测.length - 1].命中 ? '✅ 搜得到' : '⛔ 搜不到'}`);
  }
  out.时间线.push(记录);
}

// ============ 步骤 3：重新开页后再测一次（区分「索引延迟」与「本页内存索引」） ============
try {
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForSelector('.react-flow__node', { timeout: 45000 });
  await page.waitForTimeout(4500);
  const 记录 = { 名: '重开页后', 测: [] };
  const 对照 = await 测词(page, '音频 68');
  记录.阳性对照 = 对照;
  log(`【重开页后】阳性对照「音频 68」 → ${对照.错 ? '🔴 ' + 对照.错 : (对照.判命中 ? '✅ 命中' : '⛔ 没命中')}`);
  for (const n of 新节点) {
    const 试词 = [];
    for (const 词 of 候选(n.aria)) {
      if (试词.some((x) => x.用词 === 词)) continue;
      const r = await 测词(page, 词);
      试词.push(r);
      if (r.判命中) break;
    }
    记录.测.push({ kind: n.kind, aria: n.aria, id: n.id, 试词, 命中: 试词.some((x) => x.判命中) });
    log(`【重开页后】${n.kind} ${JSON.stringify(n.aria)} → ${记录.测[记录.测.length - 1].命中 ? '✅ 搜得到' : '⛔ 搜不到'}`);
  }
  out.重开页后 = 记录;
} catch (e) { (out.出错 = out.出错 || []).concat('步骤3: ' + e.message); log('🔴 步骤3 ' + e.message); }

// ============ 步骤 4：改名后再测（区分「没进索引」与「索引里名字是旧的」） ============
try {
  const n = 新节点[0];
  if (n) {
    const 标记 = 'b228mark';
    const 改名 = await page.evaluate((nid) => {
      const el = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const t = el && el.querySelector('[data-testid="flow-node-title"]');
      if (!t) return { 错: '找不到标题元素' };
      t.dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));
      return { 找到标题: true, 原文: (t.innerText || '').trim() };
    }, n.id);
    await page.waitForTimeout(1200);
    const 输入框 = await page.evaluate((nid) => {
      const el = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const inp = el && el.querySelector('input');
      if (!inp) return null;
      inp.focus(); inp.select();
      return true;
    }, n.id);
    let 新名 = null;
    if (输入框) {
      await page.keyboard.type(标记, { delay: 90 });
      await page.waitForTimeout(600);
      await page.keyboard.press('Enter');
      await page.waitForTimeout(2500);
      新名 = await page.evaluate((nid) => {
        const el = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
        return el ? (el.getAttribute('aria-label') || '').trim() : null;
      }, n.id);
    }
    out.改名 = { 目标: n.id, 标记, ...改名, 新aria: 新名 };
    log(`【改名】${JSON.stringify(out.改名)}`);

    if (新名) {
      const r = await 测词(page, 标记);
      out.改名后搜标记 = r;
      log(`【改名后搜「${标记}」】→ ${r.判命中 ? `✅ 命中（${r.列表文本}）` : `⛔ 没命中（${r.空态文本 || r.列表文本}）`}`);
    }
  }
} catch (e) { (out.出错 = out.出错 || []).concat('步骤4: ' + e.message); log('🔴 步骤4 ' + e.message); }

// ============ 步骤 5：删净自建节点 ============
out.删除 = [];
for (const id of 自建) {
  try {
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
    const sel = await page.evaluate((nid) => {
      const el = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      if (!el) return { 不在: true };
      const r = el.getBoundingClientRect();
      return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    }, id);
    if (sel.不在) { out.删除.push({ id, 结果: '本来就不在' }); continue; }
    await page.mouse.click(sel.中心[0], sel.中心[1]);
    await page.waitForTimeout(900);
    const 选中 = await page.evaluate((nid) => document.querySelector(`.react-flow__node[data-id="${nid}"]`).className.includes('selected'), id);
    if (!选中) { out.删除.push({ id, 结果: '点不中，未删' }); continue; }
    await page.keyboard.press('Delete');
    await page.waitForTimeout(1600);
    const 还在 = await page.evaluate((nid) => !!document.querySelector(`.react-flow__node[data-id="${nid}"]`), id);
    out.删除.push({ id, 结果: 还在 ? '删后仍在' : '已删' });
    log(`【删除】${id} → ${out.删除[out.删除.length - 1].结果}`);
  } catch (e) { out.删除.push({ id, 结果: '异常 ' + e.message }); }
}

// ============ 收尾 ============
try {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);
  out.收尾 = {
    状态行: await 状态行(page),
    积分: await 积分(page),
    自建仍在: (await 清单(page)).filter((n) => 自建.includes(n.id)).map((n) => n.id),
    节点数: (await 清单(page)).length,
  };
  log('【收尾】' + JSON.stringify(out.收尾));
} catch (e) { log('🔴 收尾 ' + e.message); }

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
try { await page.close(); } catch (e) { /* 页签可能被别的会话关掉 */ }
await b.close();