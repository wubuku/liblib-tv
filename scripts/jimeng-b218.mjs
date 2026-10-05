/**
 * 批次 218：验**画布位置对 `-result` 族有没有影响** —— 这一条决定批次 211 那句要不要整体重写。
 *
 * 📌 三批下来的现状：
 *   · 批次 211：「过渡带是**目标节点画布位置 × 视口宽**共同决定的」
 *     （证据：`音频 68` 画布右下走阶梯、`文本 3` 画布左上恒 `0.5`）；
 *   · 批次 217 **收窄**：在**同一个变体族内部**，画布位置**只影响落点 Y、不影响终态 `scale`**
 *     （`音频 68` 与 `视频 1` 同为 `-empty`，位置差很远但 `w=1216` 十次逐字相同 `0.299607`）；
 *   ⇒ 于是位置真正起作用的场合只剩下**跨族**，而**跨族用「变体」就能判**。
 *   ⚠️ 但**位置对 `-result` 族到底有没有影响，217 明确标了「未测」** ——
 *     因为媒体视频的位置被「同条件重建」固定住了，测它就必须**主动改位置**。
 *
 * 📌 本轮的设计：**同一个节点、同一个宽度组，拖动前后各测一遍**。
 *   这是**唯一**能隔离「位置」这一个变量的做法（批次 212 不拖节点是因为怕动别人的坐标；
 *   而本轮拖的是**自己新建、且收尾会删掉**的节点 ⇒ 风险不对等的问题不存在）。
 *
 * 📌 为什么要选这几个宽度（都是媒体视频那条带上**已知的非封顶读数**）：
 *   `1214`(0.398519) `1216`(0.427534) `1219`(0.474882) `1298`(0.26065)
 *   `1310`(0.37851)  `1318`(0.483847)
 *   ⇒ 每一档都是**已经证明「会露出斜坡值」**的宽度，所以拖动后若读数变了，
 *     一定是位置起的作用，而不是「那一档本来就读 `0.5`」。
 *   📌 每档跑 **2 次独立开页** —— 批次 217 实测该节点的露出率只有 `20%`，
 *     1 次采样有 `80%` 的概率读到封顶值 ⇒ **2 次是下限，4 次才有统计意义**。
 *     本轮取 2 次（预算），并把「这个宽度本次是否露出」单独记下来。
 *
 * 📌 拖动纪律（这一版自带，不靠任何旧脚本）：
 *   ① 先读 `.react-flow__viewport` 的 `translate`/`scale`，用 **canvas→screen** 公式算落点；
 *   ② 按下点必须 `elementFromPoint` 落在**目标节点子树的非按钮处**（立规 82）；
 *   ③ 拖完**读节点的 inline transform 验证新画布坐标**，不靠肉眼；
 *   ④ 落点位置从**现成节点的包围盒里挑一个空格子**，避免压住别人的节点。
 *
 * ⛔ 不触发任何生成：只走本地文件上传。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 上传文件 = '/tmp/jimeng-b196-probe.mp4';
const 宽度组 = [1214, 1216, 1219, 1298, 1310, 1318];
const 每档次数 = 2;
const OUT = '/tmp/b218.json';

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b218', 上传文件, 宽度组, 每档次数 };

// ---------- 读数 ----------
const 清单 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
    画布: t ? [Number(t[1]), Number(t[2])] : null, 屏上: [Math.round(r.width), Math.round(r.height)] };
}));
const 积分 = (p) => p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('*')).find((x) => (x.getAttribute('aria-label') || '').startsWith('Credits'));
  return e ? e.getAttribute('aria-label') : null;
});
const 状态行 = (p) => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes, (\d+) edges, (\d+) selected[^\n]*/) || [])[0] || null);
const 变体 = (p, id) => p.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  const cands = ['video-node-empty', 'video-node-result', 'video-flow-node-surface'];
  return { 变体: cands.filter((c) => n.querySelector(`[data-testid="${c}"]`)), 屏上: [Math.round(r.width), Math.round(r.height)] };
}, id);
const 还在 = async (p, id) => (await 清单(p)).some((n) => n.id === id);
const 焦点 = (p) => p.evaluate(() => {
  const a = document.activeElement;
  return { tag: a ? a.tagName : null, aria: a ? a.getAttribute('aria-label') : null,
    inRF: !!(a && a.closest && a.closest('.react-flow')) };
});
const 采样 = (p, id) => p.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const r = n ? n.getBoundingClientRect() : null;
  return { 中心: r ? [Math.round((r.x + r.width / 2) * 1000) / 1000, Math.round((r.y + r.height / 2) * 1000) / 1000] : null,
    屏上: r ? [Math.round(r.width), Math.round(r.height)] : null,
    vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null };
}, id);
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

/** 跑一组臂。落盘键**必须带臂序号**（立规 100）。 */
let 臂序号 = 0;
async function 扫(tag, 目标) {
  out[tag] = out[tag] || [];
  for (const w of 宽度组) {
    for (let k = 1; k <= 每档次数; k++) {
      臂序号 += 1;
      const p2 = await ctx.newPage();
      try {
        await p2.setViewportSize({ width: w, height: H });
        await p2.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
        await p2.waitForSelector('.react-flow__node', { timeout: 45000 });
        await p2.waitForTimeout(4500);
        const 前置 = await p2.evaluate((nid) => !!document.querySelector(`.react-flow__node[data-id="${nid}"]`), 目标.id);
        if (!前置) { log(`${tag} w=${w} #${k} ⛔ 节点不在`); await p2.close(); continue; }
        const 取 = await 取景(p2, 目标);
        if (!取.ok) { log(`${tag} w=${w} #${k} ⛔ ${取.无效臂}`); await p2.close(); continue; }
        const 三采 = [];
        for (let i = 0; i < 3; i++) { 三采.push(await 采样(p2, 目标.id)); await p2.waitForTimeout(500); }
        const ss = [...new Set(三采.map((x) => x.vp && x.vp[2]))];
        out[tag].push({ w, 次: k, 臂: 臂序号, scale: 三采[2].vp ? 三采[2].vp[2] : null,
          Y: 三采[2].中心 ? 三采[2].中心[1] : null, X: 三采[2].中心 ? 三采[2].中心[0] : null,
          屏上: 三采[2].屏上, 页内一致: ss.length === 1 });
        log(`${tag} w=${w} #${k} s=${JSON.stringify(ss)} Y=${三采[2].中心 ? 三采[2].中心[1] : null} 屏上=${JSON.stringify(三采[2].屏上)}`);
      } catch (e) { log(`${tag} w=${w} #${k} 🔴 ${e.message}`); }
      finally { try { await p2.close(); } catch (e) { /* 页签可能被别的会话关掉 */ } }
    }
  }
}

const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];
const 自建 = [];

// ============ 步骤 0：前置读数 + **挑一个空旷的目标位置**============
let 目标位置 = null;
try {
  const p0 = await ctx.newPage();
  await p0.setViewportSize({ width: 1280, height: H });
  await p0.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p0.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p0.waitForTimeout(5000);
  const 基线 = await 清单(p0);
  out.步骤0_前置 = { 积分: await 积分(p0), 基线数: 基线.length, 基线id: 基线.map((n) => n.id).sort(), 状态行: await 状态行(p0) };
  // 媒体视频的画布尺寸是 568×320 ⇒ 用这个盒子去挑空格子
  目标位置 = await p0.evaluate((sz) => {
    const 全部 = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
      const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
      const r = n.getBoundingClientRect();
      const s = r.width ? 1 : 1;
      return t ? { x: Number(t[1]), y: Number(t[2]), w: r.width, h: r.height } : null;
    }).filter(Boolean);
    // 用 scale 把屏上尺寸换回 canvas 尺寸不必要：直接用**屏上尺寸的量级**判断重叠会失真，
    // 所以这里改用「canvas 坐标 + 一个保守的边长」来挑。
    const 边 = Math.max(sz[0], sz[1]) * 0.9;
    const 候选 = [];
    for (let y = 240; y <= 2200; y += 40) for (let x = 60; x <= 3400; x += 40) 候选.push([x, y]);
    for (const [cx, cy] of 候选) {
      const 压 = 全部.some((n) => {
        const nw = Math.max(n.w, 160), nh = Math.max(n.h, 160);
        return cx < n.x + nw + 边 && cx + sz[0] + 边 > n.x && cy < n.y + nh + 边 && cy + sz[1] + 边 > n.y;
      });
      if (!压) return { 选中: [cx, cy], 候选数: 候选.length };
    }
    return { 失败: true };
  }, [568, 320]);
  out.目标位置 = 目标位置;
  log('【前置】节点数 ' + 基线.length + ' ｜ ' + out.步骤0_前置.状态行 + ' ｜ 积分 ' + out.步骤0_前置.积分);
  log('【目标位置】' + JSON.stringify(目标位置));
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
  let 稳定 = null;
  for (let t = 0; t < 20; t++) {
    await p1.waitForTimeout(2000);
    稳定 = await 变体(p1, 新出来[0].id);
    if (稳定 && 稳定.变体.includes('video-node-result')) break;
  }
  out.上传后变体 = 稳定;
  log('【上传】新产物 ' + JSON.stringify(新出来[0]) + ' ｜ 变体 ' + JSON.stringify(稳定));
  await p1.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤2: ' + e.message]); log('🔴 步骤2 ' + e.message); }

// ============ 步骤 2：拖动前测（P1 = 级联落点）============
const 媒体 = out.媒体节点 ? { 名: '媒体视频', id: out.媒体节点.id, 词: out.媒体节点词 } : null;
if (媒体) {
  out.拖动前位置 = out.媒体节点.画布;
  log('【拖动前】画布 ' + JSON.stringify(out.拖动前位置));
  await 扫('拖动前', 媒体);
}

// ============ 步骤 3：把它拖到目标位置（P2）============
if (媒体 && 目标位置 && 目标位置.选中) {
  try {
    const pd = await ctx.newPage();
    await pd.setViewportSize({ width: 1280, height: H });
    await pd.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await pd.waitForSelector('.react-flow__node', { timeout: 45000 });
    await pd.waitForTimeout(5000);
    out.拖动 = {};
    // ① 缩到 50%，让节点有实体面积
    const zb = await pd.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
      if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
    if (zb) { await pd.mouse.click(zb[0], zb[1]); await pd.waitForTimeout(1200);
      await pd.fill('[data-testid="canvas-zoom-percent-input"]', '50');
      await pd.keyboard.press('Enter'); await pd.waitForTimeout(2500); }
    out.拖动.缩放 = await pd.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
    // ② 找一个**在节点子树的非按钮处**的按下点（立规 82）
    const 按下 = await pd.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      if (!n) return { 失败: '不在 DOM' };
      const r = n.getBoundingClientRect();
      if (r.right < 0 || r.x > innerWidth || r.bottom < 0 || r.y > innerHeight) return { 失败: '不在视口内', 盒: [r.x, r.y, r.width, r.height] };
      for (let fy = 0.3; fy <= 0.85; fy += 0.1) for (let fx = 0.3; fx <= 0.85; fx += 0.1) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        const h = document.elementFromPoint(x, y);
        if (!h || !h.closest(`.react-flow__node[data-id="${nid}"]`)) continue;
        if (h.closest('button,[role=button]')) continue;
        return { x, y, 相对: [Math.round(fx * 100), Math.round(fy * 100)] };
      }
      return { 失败: '找不到非按钮的按下点' };
    }, 媒体.id);
    out.拖动.按下点 = 按下;
    if (按下.x === undefined) throw new Error('按下点失败：' + 按下.失败);
    // ③ canvas→screen，算出目标中心该落在屏幕哪里
    const vp = await pd.evaluate(() => {
      const v = document.querySelector('.react-flow__viewport');
      const m = v ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(v.style.transform || '') : null;
      return m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null;
    });
    out.拖动.vp = vp;
    if (!vp) throw new Error('读不到 viewport transform');
    const 尺寸 = await 变体(pd, 媒体.id);
    out.拖动.尺寸 = 尺寸;
    const 目标中心 = [目标位置.选中[0] + 284, 目标位置.选中[1] + 160];
    const 现中心画布 = [out.媒体节点.画布[0] + 284, out.媒体节点.画布[1] + 160];
    const toScreen = (cv) => [cv[0] * vp[2] + vp[0], cv[1] * vp[2] + vp[1]];
    const 落屏 = toScreen(目标中心);
    const 起屏 = toScreen(现中心画布);
    const 实际按 = [按下.x, 按下.y];
    const 终点 = [Math.round(实际按[0] + (落屏[0] - 起屏[0])), Math.round(实际按[1] + (落屏[1] - 起屏[1]))];
    out.拖动.起屏 = 起屏.map(Math.round);
    out.拖动.落屏 = 落屏.map(Math.round);
    out.拖动.终点 = 终点;
    // ④ 拖
    await pd.mouse.move(实际按[0], 实际按[1]);
    await pd.mouse.down();
    for (let i = 1; i <= 14; i++) {
      await pd.mouse.move(Math.round(实际按[0] + (终点[0] - 实际按[0]) * i / 14), Math.round(实际按[1] + (终点[1] - 实际按[1]) * i / 14));
      await pd.waitForTimeout(45);
    }
    await pd.mouse.up();
    await pd.waitForTimeout(2500);
    // ⑤ **读 inline transform 验证**，不靠肉眼
    const 拖后 = (await 清单(pd)).find((n) => n.id === 媒体.id);
    out.拖动.拖后 = 拖后;
    out.拖动.期望 = 目标位置.选中;
    out.拖动.误差 = 拖后 && 拖后.画布 ? [Math.round((拖后.画布[0] - 目标位置.选中[0]) * 100) / 100, Math.round((拖后.画布[1] - 目标位置.选中[1]) * 100) / 100] : null;
    out.拖动.边数 = await pd.evaluate(() => (document.body.innerText.match(/(\d+) edges/) || [])[1]);
    log('【拖后】画布 ' + JSON.stringify(拖后 && 拖后.画布) + ' ｜ 期望 ' + JSON.stringify(目标位置.选中) + ' ｜ 误差 ' + JSON.stringify(out.拖动.误差) + ' ｜ 边数 ' + out.拖动.边数);
    await pd.close();
  } catch (e) { out.出错 = (out.出错 || []).concat(['步骤3: ' + e.message]); log('🔴 步骤3 ' + e.message); }
}

// ============ 步骤 4：拖动后测（P2）============
if (媒体) {
  out.拖动后位置 = out.拖动 && out.拖动.拖后 ? out.拖动.拖后.画布 : null;
  log('【拖动后】画布 ' + JSON.stringify(out.拖动后位置));
  await 扫('拖动后', 媒体);
}

// ============ 步骤 5：收尾（立规 97 / 98）============
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
    for (const 路径 of ['直点(50%)', '直点(再试)', '点两次']) {
      if (!await 还在(p3, id)) break;
      const 记 = { 路径 };
      const 格 = await p3.evaluate((nid) => {
        const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
        if (!n) return { 失败: '不在 DOM' };
        const r = n.getBoundingClientRect();
        if (r.right < 0 || r.x > innerWidth || r.bottom < 0 || r.y > innerHeight) return { 失败: '不在视口内' };
        for (let fy = 0.1; fy <= 0.95; fy += 0.142857) for (let fx = 0.1; fx <= 0.95; fx += 0.142857) {
          const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
          const h = document.elementFromPoint(x, y);
          if (h && h.closest(`.react-flow__node[data-id="${nid}"]`)) return { x, y };
        }
        return { 失败: '49 个候选点没有一个在节点内（被盖）' };
      }, id);
      记.格 = 格;
      if (格.x === undefined) { 记.失败 = 格.失败; 步.尝试.push(记); log('  ' + 路径 + ' 失败：' + 格.失败); continue; }
      await p3.mouse.click(格.x, 格.y);
      await p3.waitForTimeout(1400);
      if (路径 === '点两次') { await p3.mouse.click(格.x, 格.y); await p3.waitForTimeout(1000); }
      记.焦点 = await 焦点(p3);
      记.选中集 = await p3.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
      const 守卫过 = !!(记.选中集 && 记.选中集.includes(id) && 记.焦点.inRF);
      记.守卫过 = 守卫过;
      if (!守卫过) { 记.失败 = '守卫没过'; 步.尝试.push(记); log('  ' + 路径 + ' 守卫没过 ' + JSON.stringify(记.焦点)); continue; }
      await p3.keyboard.press('Backspace');
      await p3.waitForTimeout(2600);
      记.删后仍在 = await 还在(p3, id);
      步.尝试.push(记);
      log(`  ${路径} inRF=${记.焦点.inRF} → 删后仍在 ${记.删后仍在} ｜ 当前 ${(await 清单(p3)).length} 个节点`);
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
