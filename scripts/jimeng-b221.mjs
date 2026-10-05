/**
 * 批次 221：**先否掉一个具体假设**，而不是泛泛地「再测测」。
 *
 * 📌 批次 220 写下的入口（原文）：
 *   「`0.427534 × 569 = 243.3`、`1216 × 0.2 = 243.2`（很像）；
 *     但 `音频 68` 的落点 `0.299607 × 320 = 95.9`，而 `1216 × 0.079 = 96.1`（比例完全不同）
 *     ⇒ 若是同一类规则，它对不同节点该给出**同一个比例** ⇒ 这条假设很可能不成立，要先否掉。」
 *
 * 🔴 本批要做两件事：
 *   ① **否掉它**：用**已知的三个点**先算一遍「落点屏上宽度 ÷ 视口宽」这个比例 ——
 *     媒体视频在 `1214`/`1216`/`1219` 分别是 `0.1867` / `0.2001` / `0.2217`
 *     ⇒ **比例在变** ⇒ `1216` 处的 `0.2` 是**巧合**，不是规则。
 *   ② **换一条能立得住的入口**：拿 `-empty` 族（`音频 68`，**100% 确定、每档都露**）
 *     打一条**步长 1 的密集曲线**（`1209`–`1233`，共 25 档），
 *     看它的落点曲线到底服从什么形状 —— 这条曲线**没有随机性**，
 *     是本画布上**唯一**能干净反解函数关系的对象。
 *
 * 📌 第三件事：媒体视频在**同一批宽度**上也打一遍（每档 2 次），
 *   看它那些「稀疏露出的点」是不是落在 `音频 68` 同一条曲线的**另一个参数化**上。
 *
 * 📌 立规 99 的纪律：宽度组是**步长 1**，每档**独立开页**，每臂连采 3 次。
 * 📌 立规 100：落盘键带重复序号。
 *
 * ⛔ 不触发任何生成：只走本地文件上传。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 上传文件 = '/tmp/jimeng-b196-probe.mp4';
const 密集档 = [];
for (let w = 1209; w <= 1233; w += 1) 密集档.push(w);
const 媒体档 = [];
for (let w = 1212; w <= 1222; w += 1) 媒体档.push(w);
const 媒体次数 = 2;
const OUT = '/tmp/b221.json';

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b221', 上传文件, 密集档, 媒体档, 媒体次数 };

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
const 采样 = (p, id) => p.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const r = n ? n.getBoundingClientRect() : null;
  return { 中心: r ? [Math.round((r.x + r.width / 2) * 1000) / 1000, Math.round((r.y + r.height / 2) * 1000) / 1000] : null,
    屏上: r ? [Math.round(r.width), Math.round(r.height)] : null,
    off: n ? [n.offsetWidth, n.offsetHeight] : null,
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

/** 立规 103：搜索词走候选词表。 */
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
  const 去扩 = String(目标.词 || '').replace(/\.(mp4|mp3|mov|webm|png|jpg|jpeg)$/i, '');
  const 候选 = [...new Set([目标.词, 去扩, String(目标.词 || '').split('-').slice(0, 2).join('-')].filter(Boolean))];
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
    if (点 && 回读 === 词) { await p.mouse.click(点[0], 点[1]); await p.waitForTimeout(4500); return { ok: true, 用的词: 词, 试 }; }
  }
  return { ok: false, 无效臂: '候选词都没命中那一行', 试 };
}

let 臂序号 = 0;
async function 扫(tag, 宽集, 目标, 次数) {
  out[tag] = out[tag] || [];
  for (const w of 宽集) {
    for (let k = 1; k <= 次数; k++) {
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
        const 末 = 三采[2];
        const rec = { w, 次: k, 臂: 臂序号, scale: 末.vp ? 末.vp[2] : null,
          屏上: 末.屏上, off: 末.off, 中心: 末.中心, 页内一致: ss.length === 1,
          屏上宽占视口比: 末.屏上 ? Math.round((末.屏上[0] / w) * 10000) / 10000 : null };
        out[tag].push(rec);   // 📌 立规 100：按臂 push 进数组
        log(`${tag} w=${w} #${k} s=${JSON.stringify(ss)} 屏上=${JSON.stringify(末.屏上)} 比=${rec.屏上宽占视口比}`);
      } catch (e) { log(`${tag} w=${w} #${k} 🔴 ${e.message}`); }
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

// ============ 步骤 2：音频 68 密集曲线（步长 1，每档 1 次）+ 媒体视频同批宽度 ×2 ============
log('【a 组】音频 68 密集曲线 ' + 密集档.length + ' 档 × 1 次');
await 扫('音频68密集', 密集档, { id: 'node_tadm1nyykc', 词: '音频 68' }, 1);
if (out.媒体节点) {
  log('【b 组】媒体视频 ' + 媒体档.length + ' 档 × ' + 媒体次数 + ' 次');
  await 扫('媒体视频密集', 媒体档, { id: out.媒体节点.id, 词: out.媒体节点词 }, 媒体次数);
}

// ============ 步骤 3：收尾（立规 97 / 98 / 101 / 103）============
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
    for (let round = 1; round <= 3 && await 还在(p3, id); round++) {
      const 记 = { 轮: round };
      const 现 = (await 清单(p3)).find((n) => n.id === id);
      if (!现) { 步.备注 = '已不存在'; break; }
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
      const 去扩 = (现.aria || '').replace(/\.(mp4|mp3|mov|webm|png|jpg|jpeg)$/i, '');
      for (const 词 of [...new Set([去扩, 现.aria || ''].filter(Boolean))]) {
        await p3.keyboard.press('Backspace');
        await p3.waitForTimeout(200);
        await p3.keyboard.type(词, { delay: 90 });
        await p3.waitForTimeout(2200);
        const 行 = await 结果行点(p3, id);
        记.试词 = (记.试词 || []).concat([{ 词, 有行: !!行 }]);
        if (!行) continue;
        await p3.mouse.click(行[0], 行[1]);
        await p3.waitForTimeout(2000);
        break;
      }
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
