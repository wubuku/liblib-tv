/**
 * 批次 215：验批次 214 留下的**新假设** ——
 *   「媒体视频那个 `0.371397` **正好落在**批次 211 那条阶梯的取值范围内
 *     （`1212→0.260267` … `1230→0.487232`）⇒ 那个节点**可能也有自己的阶梯**，
 *     只是**整条阶梯在宽度轴上平移了**。」
 *
 * 📌 为什么非做不可（立规 95：能力必须这一版自带）：
 *   批次 213/214 都只测了 `w=1212` **一个宽度**。
 *   **一个点**既可以是「阶梯中段」，也可以是「巧合」—— 两者在单点上**逐字一样**。
 *   ⇒ 判据必须是**整条轨迹的形状**（有没有序、端点在哪），不是某一个读数。
 *
 * 📌 本轮的设计（这一版自带，不依赖任何旧脚本跑过）：
 *   **13 个宽度（`1210→1234` 步长 2）× 3 个节点，同一轮扫完**：
 *     · `音频 68` `node_tadm1nyykc` —— **正对照**：批次 211 f 轮记过它那条阶梯，
 *       本轮**必须先复现出它**（否则说明这一轮的取景路径坏了，后面两列都不可信）；
 *     · `文本 3`  `node_5gftn3dnt1`  —— **负对照**：批次 211 记它在 13 档**全部 `0.5`**；
 *     · 媒体视频（本轮新建的上传产物）—— **目标列**。
 *   📌 有了同轮的两列对照，「目标列自己的阶梯」才是**这一轮内**的对比出来的，
 *       而不是拿 211 的旧读数来比（批次 210 就栽在「跨轮拿旧读数比」上）。
 *
 * ⚠️ 诚实的限度（先写下来，免得事后当成结论）：
 *   批次 211 已证「过渡带是**目标节点画布位置 × 视口宽**」的函数，
 *   而本轮的新节点**画布位置与批次 213 那个不同**（新建是级联位置）⇒
 *   **本轮验的是「带媒体的视频节点有没有一条有序阶梯」，不是「213 那个节点那条阶梯」**。
 *   后者已被删除、本轮不可复现 —— 这条要如实记，不能圆。
 *
 * 📌 立规 92（判动画必须 rAF 逐帧）本轮**不适用**：这里要判的是**终态**不是过程，
 *   用的是「连采 3 次、3 次 `scale` 相同」这条 211 d 轮证过的终态判据。
 *
 * ⛔ 不触发任何生成：只走本地文件上传。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 上传文件 = '/tmp/jimeng-b196-probe.mp4';
const 宽集 = [];
for (let w = 1210; w <= 1234; w += 2) 宽集.push(w);
const OUT = '/tmp/b215.json';

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b215', 上传文件, 宽集 };

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
  const cands = ['video-node-compact', 'video-node-empty', 'video-node-result', 'video-node-full',
    'video-flow-node-surface', 'video-primary-preview-viewport', 'video-node-status-icon',
    'video-node-empty-placeholder', 'text-node-empty-placeholder'];
  const r = n.getBoundingClientRect();
  return { 变体: cands.filter((c) => n.querySelector(`[data-testid="${c}"]`)), 屏上: [Math.round(r.width), Math.round(r.height)] };
}, id);
const 选中集 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
const 焦点 = (p) => p.evaluate(() => {
  const a = document.activeElement;
  return { tag: a ? a.tagName : null,
    inCE: !!(a && (a.closest('[contenteditable]') || a.isContentEditable)),
    isInput: !!(a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA')) };
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
const 搜索框 = (p) => p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('input'))
    .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
  if (!e) return null;
  e.focus(); e.select();
  return true;
});
const 搜索回读 = (p) => p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('input'))
    .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
  return e ? e.value : null;
});
const 结果行点 = (p, id) => p.evaluate((nid) => {
  const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}, id.replace(/^node_/, ''));

/** 走「搜索面板 → 点那一行」把目标节点取景到画面中央。返回 {ok, 路径, 无效臂}。 */
async function 取景(p, 目标) {
  const 钮 = await 搜索钮(p);
  if (!钮) return { ok: false, 无效臂: '找不到搜索钮' };
  await p.mouse.click(钮[0], 钮[1]);
  await p.waitForTimeout(1500);
  if (!await 搜索框(p)) return { ok: false, 无效臂: '找不到搜索输入框' };
  await p.keyboard.press('Backspace');
  await p.waitForTimeout(200);
  await p.keyboard.type(目标.词, { delay: 90 });
  await p.waitForTimeout(2200);
  const 回读 = await 搜索回读(p);
  const 点 = await 结果行点(p, 目标.id);
  if (!点) return { ok: false, 无效臂: '目标行不在（现流行=' + JSON.stringify(await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).slice(0, 6).map((x) => x.getAttribute('data-testid')))) + '）' };
  if (回读 !== 目标.词) return { ok: false, 无效臂: '输入没进去，回读=' + JSON.stringify(回读) };
  await p.mouse.click(点[0], 点[1]);
  await p.waitForTimeout(4000);
  return { ok: true, 路径: '搜索面板', 点 };
}

const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];
const 自建 = [];

// ============ 步骤 0：任何操作之前先记积分与 id 基线（立规 94 / 95）============
try {
  const p0 = await ctx.newPage();
  await p0.setViewportSize({ width: 1280, height: H });
  await p0.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p0.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p0.waitForTimeout(5000);
  const 基线 = await 清单(p0);
  out.步骤0_前置 = { 积分: await 积分(p0), 基线数: 基线.length,
    基线id: 基线.map((n) => n.id).sort(), 状态行: await 状态行(p0) };
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
  const 空节点id = 新增[0].id;
  自建.push(空节点id);
  out.步骤1_新建.上传前变体 = await 变体(p1, 空节点id);
  out.步骤1_新建.上传前积分 = await 积分(p1);
  log('【新建】' + JSON.stringify(新增[0]) + ' ｜ 上传前变体 ' + JSON.stringify(out.步骤1_新建.上传前变体));
  await p1.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤1: ' + e.message]); log('🔴 步骤1 ' + e.message); }

// ============ 步骤 2：上传 mp4（⛔ 只走本地文件，不触发生成）============
try {
  const p1 = await ctx.newPage();
  await p1.setViewportSize({ width: 1280, height: H });
  await p1.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p1.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p1.waitForTimeout(5000);
  out.步骤2_上传 = {};
  const files = p1.locator('input[type=file]');
  const nFile = await files.count();
  out.步骤2_上传.fileInput数 = nFile;
  let 目标 = -1;
  for (let i = 0; i < nFile; i++) {
    const acc = await files.nth(i).getAttribute('accept');
    if (acc && /video\/(mp4|quicktime)|\.mp4/.test(acc)) { 目标 = i; break; }
  }
  out.步骤2_上传.选中第几个 = 目标;
  if (目标 < 0) throw new Error('没有接受视频的 file input');
  const 上传前 = (await 清单(p1)).map((n) => n.id);
  await files.nth(目标).setInputFiles(上传文件);
  log('【上传】已投递 ' + 上传文件 + ' 到第 ' + 目标 + ' 个 file input');
  let 新出来 = null;
  for (let t = 0; t < 30; t++) {
    await p1.waitForTimeout(2000);
    const now = await 清单(p1);
    const 出来的 = now.filter((n) => !上传前.includes(n.id) && !自建.includes(n.id));
    if (出来的.length) { for (const nn of 出来的) 自建.push(nn.id); 新出来 = 出来的; break; }
  }
  if (!新出来 || !新出来.length) throw new Error('30 次轮询都没等到新产物');
  out.步骤2_上传.新产物 = 新出来;
  // 等视频变体稳定渲染
  let 稳定 = null;
  for (let t = 0; t < 20; t++) {
    await p1.waitForTimeout(2000);
    稳定 = await 变体(p1, 新出来[0].id);
    if (稳定 && 稳定.变体.includes('video-node-result')) break;
  }
  out.步骤2_上传.上传后变体 = 稳定;
  out.步骤2_上传.上传后积分 = await 积分(p1);
  out.步骤2_上传.节点数 = (await 清单(p1)).length;
  log('【上传】新产物 ' + JSON.stringify(新出来[0]) + ' ｜ 变体 ' + JSON.stringify(稳定));
  log('【积分】' + out.步骤1_新建.上传前积分 + ' → ' + out.步骤2_上传.上传后积分 + ' ｜ 节点数 ' + out.步骤2_上传.节点数);
  await p1.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤2: ' + e.message]); log('🔴 步骤2 ' + e.message); }

const 媒体节点 = (out.步骤2_上传 && out.步骤2_上传.新产物 && out.步骤2_上传.新产物[0]) || null;
out.媒体节点 = 媒体节点;
out.媒体节点词 = 媒体节点 ? ((媒体节点.aria || '').split('node: ')[1] || '').trim() : null;

// ============ 步骤 3：13 宽度 × 3 节点 同轮扫描 ============
if (媒体节点) {
  out.节点们 = [
    { 名: '正对照_音频68', id: 'node_tadm1nyykc', 词: '音频 68' },
    { 名: '负对照_文本3', id: 'node_5gftn3dnt1', 词: '文本 3' },
    { 名: '目标_媒体视频', id: 媒体节点.id, 词: out.媒体节点词 },
  ];
  out.档 = {};
  for (const w of 宽集) {
    out.档[w] = {};
    for (const n of out.节点们) {
      const p2 = await ctx.newPage();
      try {
        await p2.setViewportSize({ width: w, height: H });
        await p2.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
        await p2.waitForSelector('.react-flow__node', { timeout: 45000 });
        await p2.waitForTimeout(4500);
        const 前置 = await p2.evaluate((nid) => !!document.querySelector(`.react-flow__node[data-id="${nid}"]`), n.id);
        if (!前置) { out.档[w][n.名] = { 无效臂: '目标节点不在这一页' }; log(`${w} ${n.名} ⛔ 节点不在`); await p2.close(); continue; }
        const 取 = await 取景(p2, n);
        if (!取.ok) { out.档[w][n.名] = { 无效臂: 取.无效臂 }; log(`${w} ${n.名} ⛔ ${取.无效臂}`); await p2.close(); continue; }
        const 三采 = [];
        for (let k = 0; k < 3; k++) { 三采.push(await 采样(p2, n.id)); await p2.waitForTimeout(500); }
        const 档 = { 取景: 取.路径, 变体: await 变体(p2, n.id), 三采 };
        档.末 = 三采[2];
        const ss = [...new Set(三采.map((x) => x.vp && x.vp[2]))];
        档.断言 = { 判据: '3 次采样 scale 相同', 通过: ss.length === 1, ss };
        out.档[w][n.名] = 档;
        log(`${w} ${n.名} s=${JSON.stringify(ss)} 中心=${JSON.stringify(档.末.中心)} 屏上=${JSON.stringify(档.末.屏上)} 变体=${JSON.stringify((档.变体 || {}).变体)}`);
      } catch (e) { out.档[w][n.名] = { 出错: e.message }; log(`${w} ${n.名} 🔴 ${e.message}`); }
      finally { try { await p2.close(); } catch (e) { /* 页签可能已被别的会话关掉 */ } }
    }
  }
} else {
  log('⛔ 没有媒体节点，步骤 3 跳过');
}

// ============ 步骤 4：无条件清理，三条路径，逐 id 对照前置基线（立规 94 / 95）============
try {
  const p3 = await ctx.newPage();
  await p3.setViewportSize({ width: 1280, height: H });
  await p3.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p3.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p3.waitForTimeout(5000);
  out.清理 = { 要删: 自建.slice() };
  for (const id of 自建) {
    const 步 = { id };
    const now = await 清单(p3);
    const 目标 = now.find((n) => n.id === id);
    if (!目标) { 步.备注 = '已不存在'; out.清理[id] = 步; log('清理 ' + id + ' 已不存在'); continue; }
    // —— 路径 A：搜索面板按名/按 id 找行
    let 用哪 = null;
    for (const 词 of [(目标.aria || '').split('node: ')[1] || '', (目标.aria || ''), id.replace(/^node_/, '')]) {
      if (!词) continue;
      const 钮 = await 搜索钮(p3);
      if (钮) { await p3.mouse.click(钮[0], 钮[1]); await p3.waitForTimeout(1500); }
      if (!await 搜索框(p3)) continue;
      await p3.keyboard.press('Backspace');
      await p3.waitForTimeout(200);
      await p3.keyboard.type(词.trim(), { delay: 90 });
      await p3.waitForTimeout(2200);
      const 点 = await 结果行点(p3, id);
      if (点) { await p3.mouse.click(点[0], 点[1]); await p3.waitForTimeout(1800); 用哪 = 'A:搜索面板 词=' + JSON.stringify(词.trim()); break; }
      log('清理 ' + id + ' 路径A 词 ' + JSON.stringify(词.trim()) + ' 没命中');
    }
    // —— 路径 B：画布直点（把节点滚进视口 + 落点归属判据，立规 82）
    if (!用哪) {
      const 空地 = await p3.evaluate(() => {
        const 自由 = [];
        for (let y = 90; y <= 600; y += 30) for (let x = 20; x <= 900; x += 30) {
          const h = document.elementFromPoint(x, y);
          if (h && h.classList && h.classList.contains('react-flow__pane')) { 自由.push([x, y]); if (自由.length >= 6) return 自由; }
        }
        return 自由;
      });
      for (let t = 0; t < 12 && !用哪; t++) {
        const r = await p3.evaluate((nid) => { const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
          if (!n) return null; const b = n.getBoundingClientRect(); return [b.x, b.y, b.width, b.height]; }, id);
        if (!r) break;
        const cx = r[0] + r[2] / 2, cy = r[1] + r[3] / 2;
        const 归 = await p3.evaluate(([x, y, nid]) => {
          const el = document.elementFromPoint(x, y);
          const n = el ? el.closest('.react-flow__node') : null;
          return n ? n.getAttribute('data-id') : null;
        }, [cx, cy, id]);
        if (归 === id) { await p3.mouse.click(cx, cy); await p3.waitForTimeout(1500); 用哪 = 'B:画布直点'; break; }
        if (!空地.length) break;
        const 拖 = [Math.max(40, Math.min(cx - 400, 880)), Math.max(80, Math.min(cy - 340, 600))];
        await p3.mouse.move(空地[0][0], 空地[0][1]);
        await p3.mouse.down();
        for (let i = 1; i <= 8; i++) { await p3.mouse.move(空地[0][0] + (拖[0] - 空地[0][0]) * i / 8, 空地[0][1] + (拖[1] - 空地[0][1]) * i / 8); await p3.waitForTimeout(25); }
        await p3.mouse.up();
        await p3.waitForTimeout(900);
      }
    }
    步.路径 = 用哪 || '三条路径都失败';
    const 选中 = await 选中集(p3);
    const 焦 = await 焦点(p3);
    const 安全 = !焦.inCE && !焦.isInput && 选中.includes(id);
    步.选中集 = 选中; 步.焦点 = 焦; 步.焦点安全 = 安全;
    if (安全) { await p3.keyboard.press('Backspace'); await p3.waitForTimeout(2500); 步.按了Backspace = true; }
    步.删后仍在 = (await 清单(p3)).some((n) => n.id === id);
    out.清理[id] = 步;
    log('清理 ' + id + ' 路径=' + 步.路径 + ' 安全=' + 安全 + ' → 仍在 ' + 步.删后仍在);
  }
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
