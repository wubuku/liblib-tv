/**
 * 批次 216：把批次 215 那个「孤立凹陷点」扫开。
 *
 * 批次 215 留下的两个未测：
 *   ① 凹陷点到底 `1px` 还是 `3px` 宽（批次 215 用的**步长 2** 网格，`1216` 两侧
 *      `1214` / `1218` 都回到 `0.5` ⇒ 只能判「比 4px 窄」）；
 *   ② 这个节点的过渡带**在别的宽度区间是不是更宽**（215 只扫了 `1210~1234`）。
 *
 * 📌 本轮的设计要点 —— **与批次 215 同条件重建**：
 *   用**同一个文件** `/tmp/jimeng-b196-probe.mp4`、在**同一个 76 节点基线**上重建，
 *   目的是让**级联落点也逐字相同**（215 记的空节点 `[1921.29, 1340.24]`、
 *   上传产物 `[2481.29, 1380.24]`）。
 *   ⇒ 若 `1216` 的凹陷**第二次出现在同一个宽度**，那是**同条件复现**，
 *     而不是「另一个节点恰好也有个坑」。📌 这一步不是形式：批次 211 已证
 *     「过渡带是**节点画布位置 × 视口宽**的函数」⇒ 位置不同就不可比。
 *
 * 📌 三组臂：
 *   c 组（步长 1）：`1213`–`1219` 共 **7 档** —— 判凹陷的**宽度与形状**；
 *   d 组（粗扫）：`1150`–`1300` 步长 `2` 共 **26 档** —— 判**有没有更宽的带**；
 *   对照：`音频 68` 在 `1215` / `1216` / `1217` 三档（它在 215 的带是 `20px` 宽的
 *     斜坡，步长 1 上去应该仍然平滑有序 —— 若出现孤立点，说明「步长 1」本身有问题）。
 *
 * 📌 立规 97 / 98 收尾（本批一开始就按新规做，不栽第二次）：
 *   · 删节点走「缩放 50% → 画布直点」，**不调 `blur()`**，
 *     并用**肯定式**判据核对 `activeElement.closest('.react-flow')` 非 `null`；
 *   · 路径链**按结果推进**：每条路径后问「目标还在吗」，还在才换下一条。
 *
 * ⛔ 不触发任何生成：只走本地文件上传。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 上传文件 = '/tmp/jimeng-b196-probe.mp4';
const 细档 = [];
for (let w = 1213; w <= 1219; w += 1) 细档.push(w);
const 粗档 = [];
for (let w = 1150; w <= 1300; w += 2) 粗档.push(w);
const 对照档 = [1215, 1216, 1217];
const OUT = '/tmp/b216.json';

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b216', 上传文件, 细档, 粗档, 对照档 };

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
  const cands = ['video-node-compact', 'video-node-empty', 'video-node-result',
    'video-flow-node-surface', 'video-primary-preview-viewport', 'video-node-empty-placeholder'];
  const r = n.getBoundingClientRect();
  return { 变体: cands.filter((c) => n.querySelector(`[data-testid="${c}"]`)), 屏上: [Math.round(r.width), Math.round(r.height)] };
}, id);
const 还在 = async (p, id) => (await 清单(p)).some((n) => n.id === id);
const 焦点 = (p) => p.evaluate(() => {
  const a = document.activeElement;
  return { tag: a ? a.tagName : null, aria: a ? a.getAttribute('aria-label') : null,
    testid: a ? a.getAttribute('data-testid') : null,
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

/** 走「搜索面板 → 点那一行」取景。返回 {ok, 无效臂}。 */
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

/** 跑一批宽度档。`清单件` = [{名, id, 词}] */
async function 扫(p标签, 宽集, 目标们) {
  out[p标签] = {};
  for (const w of 宽集) {
    out[p标签][w] = {};
    for (const n of 目标们) {
      const p2 = await ctx.newPage();
      try {
        await p2.setViewportSize({ width: w, height: H });
        await p2.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
        await p2.waitForSelector('.react-flow__node', { timeout: 45000 });
        await p2.waitForTimeout(4500);
        const 前置 = await p2.evaluate((nid) => !!document.querySelector(`.react-flow__node[data-id="${nid}"]`), n.id);
        if (!前置) { out[p标签][w][n.名] = { 无效臂: '目标节点不在这一页' }; log(`${w} ${n.名} ⛔ 节点不在`); await p2.close(); continue; }
        const 取 = await 取景(p2, n);
        if (!取.ok) { out[p标签][w][n.名] = { 无效臂: 取.无效臂 }; log(`${w} ${n.名} ⛔ ${取.无效臂}`); await p2.close(); continue; }
        const 三采 = [];
        for (let k = 0; k < 3; k++) { 三采.push(await 采样(p2, n.id)); await p2.waitForTimeout(500); }
        const ss = [...new Set(三采.map((x) => x.vp && x.vp[2]))];
        out[p标签][w][n.名] = { 三采, 末: 三采[2], 变体: await 变体(p2, n.id),
          断言: { 判据: '3 次采样 scale 相同', 通过: ss.length === 1, ss } };
        log(`${w} ${n.名} s=${JSON.stringify(ss)} 中心=${JSON.stringify(三采[2].中心)} 屏上=${JSON.stringify(三采[2].屏上)}`);
      } catch (e) { out[p标签][w][n.名] = { 出错: e.message }; log(`${w} ${n.名} 🔴 ${e.message}`); }
      finally { try { await p2.close(); } catch (e) { /* 页签可能已被别的会话关掉 */ } }
    }
  }
}

const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];
const 自建 = [];

// ============ 步骤 0：前置读数与 id 基线（立规 94 / 95）============
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

// ============ 步骤 1：新建空视频节点（立规 82：先证归属）============
try {
  const p1 = await ctx.newPage();
  await p1.setViewportSize({ width: 1280, height: H });
  await p1.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p1.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p1.waitForTimeout(5000);
  out.步骤1_新建 = {};
  const 入口 = await p1.evaluate(() => {
    const e = Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '视频');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  });
  out.步骤1_新建.视频入口盒 = 入口;
  if (!入口) throw new Error('面板上找不到「视频」入口');
  const 归属 = await p1.evaluate(([x, y, w, h]) => {
    const el = document.elementFromPoint(x + w / 2, y + h / 2);
    return el ? { tag: el.tagName, aria: el.getAttribute('aria-label') } : null;
  }, 入口);
  out.步骤1_新建.落点归属 = 归属;
  if (!归属 || 归属.aria !== '视频') throw new Error('「视频」入口落点归属不对：' + JSON.stringify(归属));
  const 建前 = (await 清单(p1)).map((n) => n.id);
  await p1.mouse.click(入口[0] + 入口[2] / 2, 入口[1] + 入口[3] / 2);
  await p1.waitForTimeout(3500);
  const 新增 = (await 清单(p1)).filter((n) => !建前.includes(n.id));
  out.步骤1_新建.新增 = 新增;
  if (新增.length !== 1) throw new Error('新建节点数不是 1：' + JSON.stringify(新增));
  自建.push(新增[0].id);
  out.步骤1_新建.上传前变体 = await 变体(p1, 新增[0].id);
  out.步骤1_新建.上传前积分 = await 积分(p1);
  log('【新建】' + JSON.stringify(新增[0]) + ' ｜ 变体 ' + JSON.stringify(out.步骤1_新建.上传前变体));
  await p1.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤1: ' + e.message]); log('🔴 步骤1 ' + e.message); }

// ============ 步骤 2：上传同一个 mp4（⛔ 只走本地文件）============
try {
  const p1 = await ctx.newPage();
  await p1.setViewportSize({ width: 1280, height: H });
  await p1.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p1.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p1.waitForTimeout(5000);
  out.步骤2_上传 = {};
  const files = p1.locator('input[type=file]');
  let 目标 = -1;
  for (let i = 0, n = await files.count(); i < n; i++) {
    const acc = await files.nth(i).getAttribute('accept');
    if (acc && /video\/(mp4|quicktime)|\.mp4/.test(acc)) { 目标 = i; break; }
  }
  out.步骤2_上传.选中第几个 = 目标;
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
  out.步骤2_上传.新产物 = 新出来;
  let 稳定 = null;
  for (let t = 0; t < 20; t++) {
    await p1.waitForTimeout(2000);
    稳定 = await 变体(p1, 新出来[0].id);
    if (稳定 && 稳定.变体.includes('video-node-result')) break;
  }
  out.步骤2_上传.上传后变体 = 稳定;
  out.步骤2_上传.上传后积分 = await 积分(p1);
  out.步骤2_上传.节点数 = (await 清单(p1)).length;
  // 📌 与批次 215 的同条件核对：级联落点是否逐字相同
  // ⚠️ 空节点 id **不能**去引用步骤 1 的块作用域变量（`const 新增` 出了块就是未定义 ——
  //    第一版就是在这里炸的，`node --check` 同样拦不住，见立规 96 的同源教训）：
  //    一律走 `out` 传递。
  out.空节点 = (out.步骤1_新建 || {}).新增 ? out.步骤1_新建.新增[0] : null;
  out.同条件核对 = { 批次215空节点画布: [1921.29, 1340.24], 本批空节点画布: (out.空节点 || {}).画布,
    批次215产物画布: [2481.29, 1380.24], 本批产物画布: (新出来[0] || {}).画布 };
  log('【上传】新产物 ' + JSON.stringify(新出来[0]) + ' ｜ 变体 ' + JSON.stringify(稳定));
  log('【同条件】' + JSON.stringify(out.同条件核对));
  log('【积分】' + out.步骤1_新建.上传前积分 + ' → ' + out.步骤2_上传.上传后积分 + ' ｜ 节点数 ' + out.步骤2_上传.节点数);
  await p1.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤2: ' + e.message]); log('🔴 步骤2 ' + e.message); }

const 媒体节点 = (out.步骤2_上传 && out.步骤2_上传.新产物 && out.步骤2_上传.新产物[0]) || null;
out.媒体节点 = 媒体节点;
out.媒体节点词 = 媒体节点 ? ((媒体节点.aria || '').split('node: ')[1] || '').trim() : null;

// ============ 步骤 3：c 组步长 1 + 对照 ============
if (媒体节点) {
  const 目标列 = { 名: '目标_媒体视频', id: 媒体节点.id, 词: out.媒体节点词 };
  await 扫('c组_步长1', 细档, [目标列]);
  await 扫('c组_对照音频68', 对照档, [{ 名: '对照_音频68', id: 'node_tadm1nyykc', 词: '音频 68' }]);
  // ============ 步骤 4：d 组粗扫 1150~1300 ============
  await 扫('d组_粗扫', 粗档, [目标列]);
} else {
  log('⛔ 没有媒体节点，扫描全部跳过');
}

// ============ 步骤 5：收尾（立规 97 肯定式焦点 + 立规 98 按结果推进）============
try {
  const p3 = await ctx.newPage();
  await p3.setViewportSize({ width: 1280, height: H });
  await p3.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p3.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p3.waitForTimeout(5000);
  out.清理 = { 要删: 自建.slice() };
  // 缩到 50%，让节点有实体面积（立规 95：这一版自己带齐）
  const zb = await p3.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
    if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (zb) { await p3.mouse.click(zb[0], zb[1]); await p3.waitForTimeout(1200);
    await p3.fill('[data-testid="canvas-zoom-percent-input"]', '50');
    await p3.keyboard.press('Enter'); await p3.waitForTimeout(2500); }
  out.清理.缩放到 = await p3.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });

  for (const id of 自建) {
    const 步 = { id, 尝试: [] };
    if (!await 还在(p3, id)) { 步.备注 = '已不存在'; out.清理[id] = 步; continue; }
    // 📌 立规 98：**推进看结果** —— 每条路径后都问「目标还在吗」
    for (const 路径 of ['直点(50%)', '直点(再试)', '点两次']) {
      if (!await 还在(p3, id)) break;
      const 记 = { 路径 };
      const 格 = await p3.evaluate((nid) => {
        const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
        if (!n) return { 失败: '不在 DOM' };
        const r = n.getBoundingClientRect();
        if (r.right < 0 || r.x > innerWidth || r.bottom < 0 || r.y > innerHeight) return { 失败: '不在视口内', 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
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
      // 📌 立规 97：**肯定式**判据 —— 焦点必须在 .react-flow 内
      const 守卫过 = !!(记.选中集 && 记.选中集.includes(id) && 记.焦点.inRF);
      记.守卫过 = 守卫过;
      记.守卫判据 = '选中集含目标 且 activeElement.closest(".react-flow") 非 null';
      if (!守卫过) { 记.失败 = '守卫没过：选中=' + JSON.stringify(记.选中集) + ' 焦点=' + JSON.stringify(记.焦点); 步.尝试.push(记); log('  ' + 路径 + ' 守卫没过 ' + JSON.stringify(记.焦点)); continue; }
      // 📌 立规 97：**不调 blur()**
      await p3.keyboard.press('Backspace');
      await p3.waitForTimeout(2600);
      记.删后仍在 = await 还在(p3, id);
      步.尝试.push(记);
      log(`  ${路径} 焦点=${JSON.stringify(记.焦点)} inRF=${记.焦点.inRF} → 删后仍在 ${记.删后仍在} ｜ 当前 ${(await 清单(p3)).length} 个节点`);
    }
    步.最终还在 = await 还在(p3, id);
    out.清理[id] = 步;
    log('⇒ ' + id + ' 最终还在 ' + 步.最终还在);
  }
  // 缩放归位
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
