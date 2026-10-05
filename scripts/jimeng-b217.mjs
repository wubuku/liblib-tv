/**
 * 批次 217：把批次 216 留下的两条结论**量化**，而不是再叙述一遍。
 *
 * 批次 216 立了**立规 99**（「不连续」不等于「无序」，判可复现必须同一宽度重复开页），
 * 但它自己**只做到 2 次观测**就下了判断：
 *   · 目标节点 `1214` 两次开页给出两个值（`0.398519` / `0.5`）⇒ 判「不稳定」；
 *   · 对照 `音频 68` `1216` 两次开屏给出**相同**值 ⇒ 判「稳定」。
 * 📌 **2 次观测不足以把「稳定」和「不稳定」区分开** ——
 *   一个 p=0.5 的量，两次相同与两次不同的概率是一样的。
 *   ⇒ 本批把观测次数提到 **5 次**，而且**三个节点**一起测。
 *
 * 📌 三个被测节点（覆盖批次 213 说的三个族）：
 *   · `音频 68` `node_tadm1nyykc`  `audio`  `-empty`   `320×320`（已知那条 `20px` 宽斜坡的主人）
 *   · `视频 1`  `node_236ctpehgg`  `video`  `-empty`   `320×320`（批次 213 说 `-empty` 必取 `0.260267`）
 *   · 媒体视频（本轮新建的上传产物）`video` `-result`  `568×320`（批次 216 说它页间不稳）
 *
 * 📌 第二件事：把批次 216 在右端看到的那段带（`1298: 0.26065` → `1300: 0.277483`）
 *   **追完** —— 它是刚起坡，坡顶在哪、还有没有第三段，都还不知道。
 *
 * 📌 第三件事：定位 `音频 68` 那条带**左端的断崖**到底在哪一 px
 *   （已知 `1210 → 0.5`、`1212 → 0.260267`，中间只有 `1211` 没测）。
 *
 * 📌 立规 97 / 98 收尾（批次 216 已验证一次成功，本批照做）。
 *
 * ⛔ 不触发任何生成：只走本地文件上传。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 上传文件 = '/tmp/jimeng-b196-probe.mp4';
const 重复次数 = 5;
const 重复宽 = 1216;
const 追带宽 = [];
for (let w = 1302; w <= 1330; w += 4) 追带宽.push(w);
const 断崖档 = [1209, 1211];
const OUT = '/tmp/b217.json';

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b217', 上传文件, 重复次数, 重复宽, 追带宽, 断崖档 };

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
  const cands = ['video-node-empty', 'video-node-result', 'video-flow-node-surface',
    'audio-node-empty', 'audio-node-result', 'text-flow-node-full'];
  const r = n.getBoundingClientRect();
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

/**
 * 跑一批臂。`目标们` = [{名, id, 词}]；每个宽度开**独立页签**。
 *
 * 🔴🔴 **立规 100（本批踩到并已修）**：落盘键**必须带重复序号**。
 *   第一版用 `记前缀 + 宽度 + '|' + 节点名` 当键，而「重复开页」那组 5 次的**宽度相同**
 *   ⇒ 5 次写进同一个键、**后写覆盖先写** ⇒ 落盘那份证据只剩第 5 次。
 *   ⇒ 现在键里带 `#臂序号`。
 */
let 臂序号 = 0;
async function 扫(tag, 宽集, 目标们, 记前缀) {
  out[tag] = out[tag] || {};
  for (const w of 宽集) {
    for (const n of 目标们) {
      臂序号 += 1;
      const 键 = 记前缀 + w + '|' + n.名 + '#' + 臂序号;
      const p2 = await ctx.newPage();
      try {
        await p2.setViewportSize({ width: w, height: H });
        await p2.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
        await p2.waitForSelector('.react-flow__node', { timeout: 45000 });
        await p2.waitForTimeout(4500);
        const 前置 = await p2.evaluate((nid) => !!document.querySelector(`.react-flow__node[data-id="${nid}"]`), n.id);
        if (!前置) { log(`${w} ${n.名} ⛔ 节点不在`); await p2.close(); continue; }
        const 取 = await 取景(p2, n);
        if (!取.ok) { log(`${w} ${n.名} ⛔ ${取.无效臂}`); await p2.close(); continue; }
        const 三采 = [];
        for (let k = 0; k < 3; k++) { 三采.push(await 采样(p2, n.id)); await p2.waitForTimeout(500); }
        const ss = [...new Set(三采.map((x) => x.vp && x.vp[2]))];
        out[tag][键] = { 三采, 末: 三采[2], 页内一致: ss.length === 1, ss };
        log(`${w} ${n.名} s=${JSON.stringify(ss)} Y=${JSON.stringify(三采[2].中心)} 屏上=${JSON.stringify(三采[2].屏上)}`);
      } catch (e) { log(`${w} ${n.名} 🔴 ${e.message}`); }
      finally { try { await p2.close(); } catch (e) { /* 页签可能被别的会话关掉 */ } }
    }
  }
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

// ============ 步骤 1：建空视频节点 + 上传（⛔ 只走本地文件）============
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
  if (!入口) throw new Error('面板上找不到「视频」入口');
  const 归属 = await p1.evaluate(([x, y, w, h]) => {
    const el = document.elementFromPoint(x + w / 2, y + h / 2);
    return el ? el.getAttribute('aria-label') : null;
  }, 入口);
  out.步骤1_新建.落点归属 = 归属;
  if (归属 !== '视频') throw new Error('「视频」入口落点归属不对：' + 归属);
  const 建前 = (await 清单(p1)).map((n) => n.id);
  await p1.mouse.click(入口[0] + 入口[2] / 2, 入口[1] + 入口[3] / 2);
  await p1.waitForTimeout(3500);
  const 新增 = (await 清单(p1)).filter((n) => !建前.includes(n.id));
  if (新增.length !== 1) throw new Error('新建节点数不是 1：' + JSON.stringify(新增));
  自建.push(新增[0].id);
  out.步骤1_新建.新增 = 新增;
  out.步骤1_新建.上传前积分 = await 积分(p1);
  log('【新建】' + JSON.stringify(新增[0]));
  await p1.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤1: ' + e.message]); log('🔴 步骤1 ' + e.message); }

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
  out.媒体节点 = 新出来[0];
  out.媒体节点词 = ((新出来[0].aria || '').split('node: ')[1] || '').trim();
  let 稳定 = null;
  for (let t = 0; t < 20; t++) {
    await p1.waitForTimeout(2000);
    稳定 = await 变体(p1, 新出来[0].id);
    if (稳定 && 稳定.变体.includes('video-node-result')) break;
  }
  out.步骤2_上传.上传后变体 = 稳定;
  out.步骤2_上传.上传后积分 = await 积分(p1);
  log('【上传】新产物 ' + JSON.stringify(新出来[0]) + ' ｜ 变体 ' + JSON.stringify(稳定));
  log('【积分】' + out.步骤1_新建.上传前积分 + ' → ' + out.步骤2_上传.上传后积分);
  await p1.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤2: ' + e.message]); log('🔴 步骤2 ' + e.message); }

// ============ 步骤 3：重复开页测「稳不稳」===========
const 三节点 = [
  { 名: '音频68_empty', id: 'node_tadm1nyykc', 词: '音频 68' },
  { 名: '视频1_empty', id: 'node_236ctpehgg', 词: '视频 1' },
];
if (out.媒体节点) 三节点.push({ 名: '媒体视频_result', id: out.媒体节点.id, 词: out.媒体节点词 });
out.三节点 = 三节点;
const 重复集 = [];
for (let i = 1; i <= 重复次数; i++) 重复集.push(重复宽);
log('【重复开页】宽度 ' + 重复宽 + ' × ' + 重复次数 + ' 次 × ' + 三节点.length + ' 个节点');
await 扫('重复开页', 重复集, 三节点, '第');
// 目标节点在 1214 上（批次 216 读到两个不同值的那个宽度）也重复 5 次
if (out.媒体节点) {
  const 重复集2 = [];
  for (let i = 1; i <= 重复次数; i++) 重复集2.push(1214);
  log('【重复开页】宽度 1214 × ' + 重复次数 + ' 次 × 目标节点');
  await 扫('重复开页1214', 重复集2, [{ 名: '媒体视频_result', id: out.媒体节点.id, 词: out.媒体节点词 }], '第');
}

// ============ 步骤 4：追完右端第二段带 + 定位音频 68 的断崖 ============
if (out.媒体节点) {
  log('【追带】' + 追带宽.join(','));
  await 扫('追右端带', 追带宽, [{ 名: '媒体视频_result', id: out.媒体节点.id, 词: out.媒体节点词 }], 'w');
}
log('【断崖】' + 断崖档.join(','));
await 扫('音频68断崖', 断崖档, [{ 名: '音频68_empty', id: 'node_tadm1nyykc', 词: '音频 68' }], 'w');

// ============ 步骤 5：收尾（立规 97 肯定式焦点 + 立规 98 按结果推进）============
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
      await p3.keyboard.press('Backspace');   // 📌 立规 97：不调 blur()
      await p3.waitForTimeout(2600);
      记.删后仍在 = await 还在(p3, id);
      步.尝试.push(记);
      log(`  ${路径} 焦点inRF=${记.焦点.inRF} → 删后仍在 ${记.删后仍在} ｜ 当前 ${(await 清单(p3)).length} 个节点`);
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
