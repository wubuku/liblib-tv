/**
 * 批次 220：找 `-result` 族**落点双稳**的判别量（`w=1216` 时落点要么 `0.427534`、要么 `0.5`）。
 *
 * 📌 批次 219 已经确定的事实（不再重测）：
 *   · 「终态 `scale`」是**那段约 `340ms` 取景动画的落点**；
 *   · `-empty` 族（`音频 68`）4/4 落点 `0.299607`；`-result` 族 8 次里 `0.5`×5 / `0.427534`×3；
 *   · 不点搜索时 `scale` 恒 `0.260267`。
 *
 * 📌 批次 219 留下的两条口子，本批同时去堵：
 *   ① `<video>` 状态**全部读到 `null`** —— 因为它**不在目标节点的 DOM 子树里**
 *      ⇒ 本批改用 `document.querySelector('video')` **全局**查；
 *   ② 只知道落点有两个值，**不知道是什么决定选哪个**。
 *
 * 📌 候选判别量（逐帧全记，收尾再相关性分析；**事先不猜哪个对**）：
 *   E1 `.react-flow` 的屏上盒子（宽高）—— 若取景时可用区域变小，落点就该更小；
 *   E2 搜索面板此刻**在不在**、几何多大 —— 点结果行那一刻面板可能开/关；
 *   E3 全局 `video` 元素的 `readyState` / `videoWidth` / `videoHeight`；
 *   E4 目标节点的 `offsetWidth` / `offsetHeight`（**与缩放无关**的 CSS 尺寸）；
 *   E5 动画的**不同取值个数**与**动画跨度 ms**（批次 219 的原始读数）。
 *
 * 📌 判读纪律：
 *   ① 逐帧记录覆盖「开页 → 搜索 → 点结果行 → 落定」全程；
 *   ② 标记帧与帧记录**同一个时钟原点**（立规 102：批次 219 就是栽在两个时钟不可相减）；
 *   ③ 断言带非空守卫，取不到就记 `null` 而**不抛**。
 *
 * ⛔ 不触发任何生成：只走本地文件上传。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 上传文件 = '/tmp/jimeng-b196-probe.mp4';
const 目标宽 = 1216;
const 次数 = 10;
const 窗口ms = 11000;
const OUT = '/tmp/b220.json';

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b220', 上传文件, 目标宽, 次数, 窗口ms };

const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
    画布: t ? [Number(t[1]), Number(t[2])] : null };
}));
const 积分 = (p) => p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('*')).find((x) => (x.getAttribute('aria-label') || '').startsWith('Credits'));
  return e ? e.getAttribute('aria-label') : null;
});
const 状态行 = (p) => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes, (\d+) edges, (\d+) selected[^\n]*/) || [])[0] || null);
const 还在 = async (p, id) => (await 清单(p)).some((n) => n.id === id);
const 焦点 = (p) => p.evaluate(() => {
  const a = document.activeElement;
  return { tag: a ? a.tagName : null, inRF: !!(a && a.closest && a.closest('.react-flow')) };
});
const 搜索钮 = async (p) => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
    || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
});
const 结果行点 = (p, id) => p.evaluate((nid) => {
  const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}, id.replace(/^node_/, ''));

/**
 * 逐帧记录器。
 * 🔴 立规 102：帧与标记**必须同一个原点** —— 这里把 `t0` 存到 window，
 *    标记也用 `performance.now() - window.__t0`。
 */
const 开记录器 = (p, id) => p.evaluate(({ nid, 窗口 }) => {
  window.__recId = nid;
  window.__rec = [];
  window.__recMarks = [];
  window.__recOn = true;
  window.__t0 = performance.now();
  const t0 = window.__t0;
  const tick = () => {
    if (!window.__recOn) return;
    const now = performance.now() - t0;
    const vp = document.querySelector('.react-flow__viewport');
    const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
    const n = document.querySelector('.react-flow__node[data-id="' + nid + '"]');
    let 屏上 = null, off = null;
    if (n) { const r = n.getBoundingClientRect(); 屏上 = [Math.round(r.width), Math.round(r.height)];
      off = [n.offsetWidth, n.offsetHeight]; }
    const rf = document.querySelector('.react-flow');
    let 盒 = null;
    if (rf) { const r = rf.getBoundingClientRect(); 盒 = [Math.round(r.width), Math.round(r.height)]; }
    let 面板 = 0;
    try { 面板 = document.querySelectorAll('[role=dialog],[role=searchbox],[data-testid*="search"]').length; } catch (e) { 面板 = -1; }
    let 视频 = null;
    try { const v = document.querySelector('video');
      if (v) 视频 = [v.readyState, v.videoWidth, v.videoHeight, Math.round(v.getBoundingClientRect().width)]; } catch (e) { 视频 = null; }
    window.__rec.push([Math.round(now), m ? Number(m[3]) : null, 屏上, off, 盒, 面板, 视频]);
    if (now < 窗口) requestAnimationFrame(tick);
    else window.__recOn = false;
  };
  requestAnimationFrame(tick);
  return true;
}, { nid: id, 窗口: 窗口ms });

const 打标记 = (p, 名) => p.evaluate((m) => {
  // 🔴 立规 102：与帧同一个原点
  window.__recMarks.push([Math.round(performance.now() - window.__t0), m]);
}, 名);

const 收记录 = (p) => p.evaluate(() => {
  window.__recOn = false;
  return { 帧: window.__rec, 标记: window.__recMarks };
});

async function 取景(p, 目标) {
  const 钮 = await 搜索钮(p);
  if (!钮) return { ok: false, 无效臂: '找不到搜索钮' };
  await p.mouse.click(钮[0], 钮[1]);
  await p.waitForTimeout(1500);
  const 有框 = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('input'))
      .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
    if (!e) return false;
    e.focus(); e.select(); return true;
  });
  if (!有框) return { ok: false, 无效臂: '找不到搜索输入框' };
  // 🔴 候选词表：**先全名，再去扩展名**。
  //   本批实测：上传产物的节点名**有时带 `.mp4`、有时不带**
  //   （批次 215–219 是 `视频 node: jimeng-b196-probe`，本批是
  //   `视频 node: jimeng-b196-probe.mp4`），
  //   而**搜索只命中不带扩展名的那种** ⇒ 只用全名会得到「目标行不在」的无效臂。
  const 去扩 = String(目标.词 || '').replace(/\.(mp4|mp3|mov|webm|png|jpg|jpeg)$/i, '');
  const 候选 = [...new Set([目标.词, 去扩, 目标.词.split('-').slice(0, 2).join('-')].filter(Boolean))];
  const 试 = [];
  for (const 词 of 候选) {
    await p.keyboard.press('Backspace');
    await p.waitForTimeout(200);
    await p.keyboard.type(词, { delay: 90 });
    await p.waitForTimeout(2200);
    const 回读 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('input'))
        .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      return e ? e.value : null;
    });
    const 点 = await 结果行点(p, 目标.id);
    试.push({ 词, 回读, 有行: !!点 });
    if (点 && 回读 === 词) {
      await p.mouse.click(点[0], 点[1]);
      await p.waitForTimeout(4000);
      return { ok: true, 用的词: 词, 试 };
    }
  }
  return { ok: false, 无效臂: '候选词都没命中那一行', 试 };
}

async function 跑一次(次) {
  const p = await ctx.newPage();
  const 记 = { 次 };
  try {
    await p.setViewportSize({ width: 目标宽, height: H });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(1200);
    await 开记录器(p, out.媒体节点.id);
    await p.waitForTimeout(2500);
    await 打标记(p, '取景开始');
    const 取 = await 取景(p, { id: out.媒体节点.id, 词: out.媒体节点词 });
    await 打标记(p, '取景结束');
    if (!取.ok) { 记.无效臂 = 取.无效臂; log(`#${次} ⛔ ${取.无效臂}`); await p.close(); return 记; }
    await p.waitForTimeout(2500);
    const { 帧, 标记 } = await 收记录(p);
    记.帧数 = 帧.length;
    记.标记 = 标记;
    const 序列 = [];
    for (const f of 帧) {
      if (f[1] === null) continue;
      const 末 = 序列[序列.length - 1];
      if (!末 || 末.s !== f[1]) 序列.push({ t: f[0], s: f[1], 屏上: f[2], off: f[3], 盒: f[4], 面板: f[5], 视频: f[6] });
    }
    记.序列 = 序列;
    记.落点 = 序列.length ? 序列[序列.length - 1].s : null;
    记.动画步数 = 序列.length;
    记.动画跨度ms = 序列.length > 1 ? 序列[序列.length - 1].t - 序列[1].t : null;
    // 判别量取「动画开始那一帧」（即第一个不等于起始值的帧）与「落定帧」
    const 动帧 = 序列.filter((x) => x.s !== 序列[0].s);
    记.动起 = 动帧.length ? 动帧[0] : null;
    记.落帧 = 序列.length ? 序列[序列.length - 1] : null;
    // 落点前后各 300ms 内环境量的取值集合
    const 落t = 记.落帧 ? 记.落帧.t : 0;
    const 窗 = 帧.filter((f) => Math.abs(f[0] - 落t) <= 300);
    记.落点邻域 = {
      reactFlow盒: [...new Set(窗.map((f) => JSON.stringify(f[4])))],
      面板数: [...new Set(窗.map((f) => f[5]))],
      视频: [...new Set(窗.map((f) => (f[6] ? f[6].join('/') : 'null')))],
      节点offset: [...new Set(窗.map((f) => JSON.stringify(f[3])))],
    };
    记.全程 = {
      reactFlow盒: [...new Set(帧.map((f) => JSON.stringify(f[4])))],
      面板数: [...new Set(帧.map((f) => f[5]))],
      视频: [...new Set(帧.map((f) => (f[6] ? f[6].join('/') : 'null')))],
      节点offset: [...new Set(帧.map((f) => JSON.stringify(f[3])))],
    };
    log(`#${次} 落点=${记.落点} 步数=${记.动画步数} 跨度=${记.动画跨度ms}ms ｜ 动起盒=${记.动起 ? JSON.stringify(记.动起.盒) : null} 面板=${记.动起 ? 记.动起.面板 : null} 视频=${记.动起 ? (记.动起.视频 ? 记.动起.视频.join('/') : 'null') : null}`);
  } catch (e) { 记.出错 = e.message; log(`#${次} 🔴 ${e.message}`); }
  finally { try { await p.close(); } catch (e) { /* 页签可能被别的会话关掉 */ } }
  return 记;
}

const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];
const 自建 = [];

// ============ 步骤 0：前置读数与 id 基线 ============
try {
  const p0 = await ctx.newPage();
  await p0.setViewportSize({ width: 1280, height: H });
  await p0.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p0.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p0.waitForTimeout(5000);
  const 基线 = await 清单(p0);
  out.步骤0_前置 = { 积分: await 积分(p0), 基线数: 基线.length, 基线id: 基线.map((n) => n.id).sort(), 状态行: await 状态行(p0) };
  log('【前置】节点数 ' + 基线.length + ' ｜ 积分 ' + out.步骤0_前置.积分);
  await p0.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤0: ' + e.message]); }

// ============ 步骤 1：建空视频节点 + 上传 ============
try {
  const p1 = await ctx.newPage();
  await p1.setViewportSize({ width: 1280, height: H });
  await p1.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p1.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p1.waitForTimeout(5000);
  const 入口 = await p1.evaluate(() => {
    const e = Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '视频');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  });
  if (!入口) throw new Error('面板上找不到「视频」入口');
  const 归属 = await p1.evaluate(([x, y, w, h]) => {
    const el = document.elementFromPoint(x + w / 2, y + h / 2);
    return el ? el.getAttribute('aria-label') : null;
  }, 入口);
  if (归属 !== '视频') throw new Error('「视频」入口落点归属不对：' + 归属);
  const 建前 = (await 清单(p1)).map((n) => n.id);
  await p1.mouse.click(入口[0] + 入口[2] / 2, 入口[1] + 入口[3] / 2);
  await p1.waitForTimeout(3500);
  const 新增 = (await 清单(p1)).filter((n) => !建前.includes(n.id));
  if (新增.length !== 1) throw new Error('新建节点数不是 1：' + JSON.stringify(新增));
  自建.push(新增[0].id);
  out.空节点 = 新增[0];
  log('【新建】' + JSON.stringify(新增[0]));
  await p1.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤1: ' + e.message]); log('🔴 步骤1 ' + e.message); }

try {
  const p1 = await ctx.newPage();
  await p1.setViewportSize({ width: 1280, height: H });
  await p1.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p1.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p1.waitForTimeout(5000);
  const files = p1.locator('input[type=file]');
  let 目标 = -1;
  for (let i = 0, n = await files.count(); i < n; i++) {
    const acc = await files.nth(i).getAttribute('accept');
    if (acc && /video\/(mp4|quicktime)|\.mp4/.test(acc)) { 目标 = i; break; }
  }
  if (目标 < 0) throw new Error('没有接受视频的 file input');
  const 上传前 = (await 清单(p1)).map((n) => n.id);
  await files.nth(目标).setInputFiles(上传文件);
  let 新出来 = null;
  for (let t = 0; t < 30; t++) {
    await p1.waitForTimeout(2000);
    const 出来的 = (await 清单(p1)).filter((n) => !上传前.includes(n.id) && !自建.includes(n.id));
    if (出来的.length) { for (const nn of 出来的) 自建.push(nn.id); 新出来 = 出来的; break; }
  }
  if (!新出来 || !新出来.length) throw new Error('30 次轮询都没等到新产物');
  out.媒体节点 = 新出来[0];
  out.媒体节点词 = ((新出来[0].aria || '').split('node: ')[1] || '').trim();
  log('【上传】新产物 ' + JSON.stringify(新出来[0]));
  await p1.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤2: ' + e.message]); log('🔴 步骤2 ' + e.message); }

// ============ 步骤 2：逐帧记环境量 × 10 次 ============
out.记录 = [];
if (out.媒体节点) {
  for (let k = 1; k <= 次数; k++) out.记录.push(await 跑一次(k));
  // 相关性汇总：**按落点分组**，看每个环境量在两组里是否不同
  const 组 = {};
  for (const r of out.记录) {
    if (r.落点 === undefined || r.落点 === null) continue;
    (组[r.落点] = 组[r.落点] || []).push(r);
  }
  out.分组 = {};
  for (const k of Object.keys(组)) {
    out.分组[k] = {
      次数: 组[k].length,
      步数: [...new Set(组[k].map((r) => r.动画步数))].sort((a, b) => a - b),
      跨度ms: [...new Set(组[k].map((r) => r.动画跨度ms))].sort((a, b) => a - b),
      动起盒: [...new Set(组[k].map((r) => (r.动起 ? JSON.stringify(r.动起.盒) : 'null')))],
      落点邻域盒: [...new Set(组[k].flatMap((r) => r.落点邻域.reactFlow盒))],
      面板数: [...new Set(组[k].flatMap((r) => r.落点邻域.面板数))],
      视频: [...new Set(组[k].flatMap((r) => r.落点邻域.视频))],
      节点offset: [...new Set(组[k].flatMap((r) => r.落点邻域.节点offset))],
    };
  }
  log('【分组】' + JSON.stringify(out.分组, null, 1));
} else {
  log('⛔ 没有媒体节点，跳过');
}

// ============ 步骤 3：收尾（立规 97 / 98 / 101）============
try {
  const p3 = await ctx.newPage();
  await p3.setViewportSize({ width: 1280, height: H });
  await p3.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p3.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p3.waitForTimeout(5000);
  out.清理 = { 要删: 自建.slice() };
  const zb = await p3.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
    if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (zb) { await p3.mouse.click(zb[0], zb[1]); await p3.waitForTimeout(1200);
    await p3.fill('[data-testid="canvas-zoom-percent-input"]', '50');
    await p3.keyboard.press('Enter'); await p3.waitForTimeout(2500); }
  for (const id of 自建) {
    const 步 = { id, 尝试: [] };
    if (!await 还在(p3, id)) { 步.备注 = '已不存在'; out.清理[id] = 步; continue; }
    for (let round = 1; round <= 3 && await 还在(p3, id); round++) {
      const 记 = { 轮: round };
      const 钮 = await 搜索钮(p3);
      if (!钮) { 记.失败 = '找不到搜索钮'; 步.尝试.push(记); break; }
      await p3.mouse.click(钮[0], 钮[1]);
      await p3.waitForTimeout(1500);
      const 有框 = await p3.evaluate(() => {
        const e = Array.from(document.querySelectorAll('input'))
          .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
        if (!e) return false;
        e.focus(); e.select(); return true;
      });
      if (!有框) { 记.失败 = '找不到搜索输入框'; 步.尝试.push(记); break; }
      await p3.keyboard.press('Backspace');
      await p3.waitForTimeout(200);
      const 名 = ((await 清单(p3)).find((n) => n.id === id) || {}).aria || '';
      const 词 = (名.split('node: ')[1] || 名).trim();
      await p3.keyboard.type(词, { delay: 90 });
      await p3.waitForTimeout(2200);
      const 行 = await 结果行点(p3, id);
      if (!行) { 记.失败 = '结果行不在'; 步.尝试.push(记); log(`  轮${round} 没有那一行`); continue; }
      await p3.mouse.click(行[0], 行[1]);
      await p3.waitForTimeout(2000);
      记.框进来后焦点 = await 焦点(p3);
      const 格 = await p3.evaluate((nid) => {
        const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
        if (!n) return { 失败: '不在 DOM' };
        const r = n.getBoundingClientRect();
        if (r.right < 0 || r.x > innerWidth || r.bottom < 0 || r.y > innerHeight) return { 失败: '不在视口内' };
        for (let fy = 0.15; fy <= 0.9; fy += 0.125) for (let fx = 0.15; fx <= 0.9; fx += 0.125) {
          const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
          const h = document.elementFromPoint(x, y);
          if (h && h.closest(`.react-flow__node[data-id="${nid}"]`)) return { x, y };
        }
        return { 失败: '候选点全被盖' };
      }, id);
      if (格.x === undefined) { 记.失败 = '直点失败：' + 格.失败; 步.尝试.push(记); log(`  轮${round} 直点失败 ${格.失败}`); continue; }
      await p3.mouse.click(格.x, 格.y);
      await p3.waitForTimeout(1500);
      记.直点后焦点 = await 焦点(p3);
      记.选中集 = await p3.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
      const 守卫过 = !!(记.选中集 && 记.选中集.includes(id) && 记.直点后焦点.inRF);
      记.守卫过 = 守卫过;
      if (!守卫过) { 记.失败 = '守卫没过'; 步.尝试.push(记); log(`  轮${round} 守卫没过`); continue; }
      await p3.keyboard.press('Backspace');
      await p3.waitForTimeout(2600);
      记.删后仍在 = await 还在(p3, id);
      步.尝试.push(记);
      log(`  轮${round} 框进来后inRF=${记.框进来后焦点.inRF} → 直点后inRF=${记.直点后焦点.inRF} → 删后仍在 ${记.删后仍在} ｜ 当前 ${(await 清单(p3)).length} 个节点`);
    }
    步.最终还在 = await 还在(p3, id);
    out.清理[id] = 步;
  }
  try {
    const zb2 = await p3.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
      if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (zb2) { await p3.mouse.click(zb2[0], zb2[1]); await p3.waitForTimeout(1200);
      await p3.fill('[data-testid="canvas-zoom-percent-input"]', '26');
      await p3.keyboard.press('Enter'); await p3.waitForTimeout(2500); }
  } catch (e) { log('🔴 缩放归位 ' + e.message); }
  const 末清单 = await 清单(p3);
  const 基线集 = new Set((out.步骤0_前置 || {}).基线id || []);
  out.清理.最终数 = 末清单.length;
  out.清理.多出来 = 末清单.filter((n) => !基线集.has(n.id)).map((n) => n.id + ' ' + n.aria);
  out.清理.少了 = ((out.步骤0_前置 || {}).基线id || []).filter((x) => !末清单.some((n) => n.id === x));
  out.清理.最终状态行 = await 状态行(p3);
  out.清理.最终积分 = await 积分(p3);
  out.清理.最终缩放 = await p3.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
  log('【收尾】节点数 ' + out.清理.最终数 + ' ｜ 多 ' + JSON.stringify(out.清理.多出来) + ' ｜ 少 ' + JSON.stringify(out.清理.少了));
  log('【收尾】' + out.清理.最终状态行 + ' ｜ 缩放 ' + out.清理.最终缩放 + ' ｜ 积分 ' + out.清理.最终积分);
  await p3.close();
} catch (e) { out.清理 = { 出错: e.message }; log('🔴 清理 ' + e.message); }

out.自建清单 = 自建;
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);
