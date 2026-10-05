/**
 * 批次 219：解那个**只有现象、没有机制**的空白 ——
 * 「`-result` 族为什么只有约 `20%` 的开页会露出斜坡值？」
 *
 * 📌 已知现象（批次 217 量化、批次 218 复核）：
 *   · `音频 68` / `视频 1`（`-empty` 族）在 `w=1216`：**10/10** 都给 `0.299607`；
 *   · 媒体视频（`-result` 族）在 `w=1214`/`1216`：**合计 2/10** 露出斜坡值，其余读封顶 `0.5`；
 *   · **页内**连采 3 次一致、**页间**会变 ⇒ 不是「慢收敛」。
 *
 * 🔴 两个互斥的机制假设，**本批用 rAF 逐帧把它们分开**（立规 92 的直接应用）：
 *   H1「**竞态**」：斜坡值其实**出现过**，只是随后被「取景到 0.5」的那一帧盖掉了
 *      ⇒ 读到 `0.5` 的那些开页里，transform **经过**了 `0.427534`；
 *   H2「**测量差异**」：斜坡值**从头到尾没出现过**，`0.5` 是直接算出来的
 *      ⇒ 读到 `0.5` 的那些开页里，transform **从未**经过 `0.427534`。
 *
 * 📌 附带取一条**机制侧线索**：目标节点里的 `<video>` 元素的
 *   `readyState` / `videoWidth` / `videoHeight` —— 如果斜坡值出现的时刻
 *   恰好对应「媒体尺寸刚变已知」的那一刻，那 H2 就有了具体机制。
 *
 * 📌 判读纪律：
 *   ① 逐帧记录**全程**覆盖「开页 → 搜索取景 → 终态」三个阶段（取景动作发生在帧序列中间）；
 *   ② 每一帧都带 `t`（相对开页起点的毫秒），取景动作单独打**标记帧**；
 *   ③ 断言都带非空守卫；`video` 查询用可选链，取不到就记 `null` 而**不抛**；
 *   ④ **不**用固定间隔轮询判过程（立规 92 踩过：700ms 间隔跳过了约 400ms 的整段动画）。
 *
 * 📌 对照：`音频 68` 同规格跑几遍，看「100% 露出」那类在帧序列里长什么样。
 *
 * ⛔ 不触发任何生成：只走本地文件上传。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 上传文件 = '/tmp/jimeng-b196-probe.mp4';
const 目标宽 = 1216;          // 批次 217 实测该节点在这一档约 20%–50% 露出
const 目标次数 = 8;           // 8 次开页，期望至少各 1 次「露出」与「封顶」
const 对照次数 = 4;           // `音频 68` 同规格
const 帧预算ms = 12000;       // 记录窗口
const OUT = '/tmp/b219.json';

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b219', 上传文件, 目标宽, 目标次数, 对照次数, 帧预算ms };

// ---------- 读数 ----------
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

/** 开一个 rAF 逐帧记录器：每帧记 [t, scale, 节点屏上尺寸, video 状态]。 */
const 开记录器 = (p, id) => p.evaluate(({ nid, 预算 }) => {
  window.__recId = nid;
  window.__rec = [];
  window.__recMarks = [];
  window.__recOn = true;
  const t0 = performance.now();
  const tick = () => {
    if (!window.__recOn) return;
    const now = performance.now() - t0;
    const vp = document.querySelector('.react-flow__viewport');
    const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
    const n = document.querySelector('.react-flow__node[data-id="' + nid + '"]');
    const r = n && n.getBoundingClientRect ? n.getBoundingClientRect() : null;
    let v = null;
    try { const el = n ? n.querySelector('video') : null;
      if (el) v = [el.readyState, el.videoWidth, el.videoHeight]; } catch (e) { v = null; }
    window.__rec.push([Math.round(now), m ? Number(m[3]) : null,
      r ? [Math.round(r.width), Math.round(r.height)] : null, v]);
    if (now < 预算) requestAnimationFrame(tick);
    else window.__recOn = false;
  };
  requestAnimationFrame(tick);
  return true;
}, { nid: id, 预算: 帧预算ms });

const 打标记 = (p, 名) => p.evaluate((m) => {
  window.__recMarks.push([Math.round(performance.now()), m]);
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
  await p.keyboard.press('Backspace');
  await p.waitForTimeout(200);
  await p.keyboard.type(目标.词, { delay: 90 });
  await p.waitForTimeout(2200);
  const 回读 = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('input'))
      .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
    return e ? e.value : null;
  });
  const 点 = await 结果行点(p, 目标.id);
  if (!点) return { ok: false, 无效臂: '目标行不在' };
  if (回读 !== 目标.词) return { ok: false, 无效臂: '输入没进去，回读=' + JSON.stringify(回读) };
  await p.mouse.click(点[0], 点[1]);
  await p.waitForTimeout(4000);
  return { ok: true };
}

/** 跑一次「开页 → 逐帧记录 → 取景 → 收记录」。 */
async function 跑一次(标签, 目标, 次) {
  const p = await ctx.newPage();
  const 记 = { 标签, 次, id: 目标.id };
  try {
    await p.setViewportSize({ width: 目标宽, height: H });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(1200);
    await 开记录器(p, 目标.id);
    await p.waitForTimeout(3000);
    await 打标记(p, '取景开始');
    const 取 = await 取景(p, 目标);
    await 打标记(p, '取景结束');
    if (!取.ok) { 记.无效臂 = 取.无效臂; log(`${标签} #${次} ⛔ ${取.无效臂}`); await p.close(); return 记; }
    await p.waitForTimeout(3000);
    const { 帧, 标记 } = await 收记录(p);
    记.帧数 = 帧.length;
    记.标记 = 标记;
    // 逐帧去重出 scale 序列（保留第一次出现的时间）
    const 序列 = [];
    for (const f of 帧) {
      const s = f[1];
      if (s === null) continue;
      const 末 = 序列[序列.length - 1];
      if (!末 || 末.s !== s) 序列.push({ t: f[0], s, 屏上: f[2], video: f[3] });
    }
    记.scale序列 = 序列;
    记.终态 = 序列.length ? 序列[序列.length - 1].s : null;
    const 去重 = [...new Set(序列.map((x) => x.s))];
    记.scale去重 = 去重;
    记.非封顶值 = 去重.filter((s) => s < 0.49);
    记.视频状态去重 = [...new Set(帧.map((f) => (f[3] ? f[3].join('/') : 'null')))];
    log(`${标签} #${次} 终态=${记.终态} 帧数=${记.帧数} scale序列=${JSON.stringify(序列.map((x) => x.s))} 非封顶=${JSON.stringify(记.非封顶值)} video=${JSON.stringify(记.视频状态去重)}`);
  } catch (e) { 记.出错 = e.message; log(`${标签} #${次} 🔴 ${e.message}`); }
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
  log('【前置】节点数 ' + 基线.length + ' ｜ ' + out.步骤0_前置.状态行 + ' ｜ 积分 ' + out.步骤0_前置.积分);
  await p0.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤0: ' + e.message]); log('🔴 步骤0 ' + e.message); }

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
  log('【上传】已投递 ' + 上传文件);
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

// ============ 步骤 2：逐帧记录（目标节点 8 次 + 对照 4 次）============
out.目标记录 = [];
out.对照记录 = [];
if (out.媒体节点) {
  for (let k = 1; k <= 目标次数; k++) {
    out.目标记录.push(await 跑一次('目标_媒体视频', { id: out.媒体节点.id, 词: out.媒体节点词 }, k));
  }
  for (let k = 1; k <= 对照次数; k++) {
    out.对照记录.push(await 跑一次('对照_音频68', { id: 'node_tadm1nyykc', 词: '音频 68' }, k));
  }
  // 判据汇总
  const 摘 = (rs) => ({
    次数: rs.length,
    终态去重: [...new Set(rs.map((r) => r.终态).filter((x) => x !== undefined && x !== null))],
    露出次数: rs.filter((r) => (r.非封顶值 || []).length > 0).length,
    从未露出的次数: rs.filter((r) => (r.非封顶值 || []).length === 0 && r.终态 !== undefined && r.终态 !== null).length,
  });
  out.判据 = { 目标: 摘(out.目标记录), 对照: 摘(out.对照记录) };
  log('【判据】' + JSON.stringify(out.判据));
} else {
  log('⛔ 没有媒体节点，逐帧记录跳过');
}

// ============ 步骤 3：收尾（立规 97 肯定式焦点 + 立规 98 按结果推进 + 立规 101 两步接力）============
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
      // ① 立规 101 第一步：**搜索**把节点框进视口
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
      记.词 = 词; 记.有行 = !!行;
      if (!行) { 记.失败 = '结果行不在'; 步.尝试.push(记); log(`  轮${round} 词「${词}」没有那一行`); continue; }
      await p3.mouse.click(行[0], 行[1]);
      await p3.waitForTimeout(2000);
      记.框进来后焦点 = await 焦点(p3);
      // ② 立规 101 第二步：**画布直点**把焦点交回 `.react-flow`
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
      记.格 = 格;
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
