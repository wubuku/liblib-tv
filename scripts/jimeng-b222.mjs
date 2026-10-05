/**
 * 批次 222：**单变量实验** —— 只改「画布当前缩放」这一个量，看取景带的**地板值**动不动。
 *
 * 📌 批次 221 留下的两个入口里，挑了**更便宜、可能直接揭机制**的那条：
 *   两条取景带的**地板值都恰好 `0.260267`**（音频 `1212` 本批实测、媒体 `1202` 批次 216 实测），
 *   而批次 219 已经证明：`0.260267` 就是这个画布**完全不点搜索**时的默认缩放（`Zoom options, 26%`）。
 *   ⇒ 「地板 = 当前画布缩放」这个机制解释，和「地板是硬常数 `0.260267`」，
 *     **只差把画布缩放改掉这一个变量**。
 *
 * 🔴 两个互斥假设：
 *   **H1（地板 = 当前画布缩放）**：把画布缩放改成 `40%` 之后，带子的地板应变成 `0.4`，
 *     带子**变窄并上移**（按批次 221 拟合的 `ln` 斜率 `0.0348/px`，
 *     从 `0.5` 降到 `0.4` 只需 `ln(1.25)/0.0348 ≈ 6.4px` ⇒ 带子应缩到约 `[1224, 1230]`）。
 *   **H2（地板是硬常数）**：带子**原封不动**停在 `[1212, 1230]`，地板仍是 `0.260267`。
 *
 * 📌 立规 98：兜底链按**结果**推进。
 * 📌 立规 100：落盘按臂 `push`（键含重复序号）。
 * 📌 立规 103：搜索词走候选词表。
 * 📌 立规 101：清理时「搜索框进视口 → 画布直点交回焦点 → 才按 ⌫」。
 *
 * 📌 本批**每臂多记一个读数**：开页后、**点搜索之前**先读一次 `.react-flow__viewport` 的 `scale`
 *   （即「这一次开页时画布的当前缩放」）⇒ 31 档各有一对「当前缩放 / 落点」。
 *   这一对读数**同源同页**，不需要跨批次比较（批次 102 的同原点纪律）。
 *
 * ⛔ 不触发任何生成：只走本地文件上传。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 上传文件 = '/tmp/jimeng-b196-probe.mp4';
const 目标宽 = 40;          // 🔴 唯一被改的变量
const 扫描档 = [];
for (let w = 1210; w <= 1240; w += 1) 扫描档.push(w);
const 目标 = { id: 'node_tadm1nyykc', 词: '音频 68' };   // -empty 族，100% 复现
const OUT = '/tmp/b222.json';

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b222', 目标宽, 扫描档, 目标 };

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
/** 只读 `.react-flow__viewport` 的 scale —— 不碰任何节点。 */
const 当前缩放 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  if (!vp) return null;
  const m = /scale\(([\d.]+)\)/.exec(vp.style.transform || '');
  return m ? Number(m[1]) : null;
});
const 缩放标签 = (p) => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
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

/** 立规 101：搜索框进视口 → 画布直点交回焦点 → 才按 ⌫。 */
async function 删一个(p, id) {
  const 记 = { id, 尝试: [] };
  for (let round = 1; round <= 3 && await 还在(p, id); round++) {
    const 一轮 = { 轮: round };
    const 现 = (await 清单(p)).find((n) => n.id === id);
    if (!现) { 一轮.备注 = '已不存在'; 记.尝试.push(一轮); break; }
    const 钮 = await 搜索钮(p);
    if (!钮) { 一轮.失败 = '找不到搜索钮'; 记.尝试.push(一轮); break; }
    await p.mouse.click(钮[0], 钮[1]);
    await p.waitForTimeout(1500);
    const 有框 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('input'))
        .find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      if (!e) return false;
      e.focus(); e.select(); return true;
    });
    if (!有框) { 一轮.失败 = '找不到搜索输入框'; 记.尝试.push(一轮); break; }
    const 去扩 = (现.aria || '').replace(/\.(mp4|mp3|mov|webm|png|jpg|jpeg)$/i, '');
    for (const 词 of [...new Set([去扩, 现.aria || ''].filter(Boolean))]) {
      await p.keyboard.press('Backspace');
      await p.waitForTimeout(200);
      await p.keyboard.type(词, { delay: 90 });
      await p.waitForTimeout(2200);
      const 行 = await 结果行点(p, id);
      一轮.试词 = (一轮.试词 || []).concat([{ 词, 有行: !!行 }]);
      if (!行) continue;
      await p.mouse.click(行[0], 行[1]);
      await p.waitForTimeout(2000);
      break;
    }
    一轮.框进来后焦点 = await 焦点(p);
    const 格 = await p.evaluate((nid) => {
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
    if (格.x === undefined) { 一轮.失败 = '直点失败：' + 格.失败; 记.尝试.push(一轮); log(`  轮${round} 直点失败 ${格.失败}`); continue; }
    await p.mouse.click(格.x, 格.y);
    await p.waitForTimeout(1500);
    一轮.直点后焦点 = await 焦点(p);
    一轮.选中集 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
    const 守卫过 = !!(一轮.选中集 && 一轮.选中集.includes(id) && 一轮.直点后焦点.inRF);
    一轮.守卫过 = 守卫过;
    if (!守卫过) { 一轮.失败 = '守卫没过'; 记.尝试.push(一轮); log(`  轮${round} 守卫没过`); continue; }
    await p.keyboard.press('Backspace');
    await p.waitForTimeout(2600);
    一轮.删后仍在 = await 还在(p, id);
    记.尝试.push(一轮);
    log(`  轮${round} 框进来后inRF=${一轮.框进来后焦点.inRF} → 直点后inRF=${一轮.直点后焦点.inRF} → 删后仍在 ${一轮.删后仍在} ｜ 当前 ${(await 清单(p)).length} 个节点`);
  }
  记.最终还在 = await 还在(p, id);
  return 记;
}

async function 设缩放(p, 值) {
  const b = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
    if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (!b) return { ok: false, 失败: '找不到缩放按钮' };
  await p.mouse.click(b[0], b[1]);
  await p.waitForTimeout(1200);
  await p.fill('[data-testid="canvas-zoom-percent-input"]', String(值));
  await p.keyboard.press('Enter');
  await p.waitForTimeout(3000);
  return { ok: true, 标签: await 缩放标签(p), 实际: await 当前缩放(p) };
}

const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];
const 自建 = [];

async function 开页(w) {
  const p = await ctx.newPage();
  await p.setViewportSize({ width: w, height: H });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(4500);
  return p;
}

// ============ 步骤 0：前置基线 + 确认原缩放是 26% ============
try {
  const p0 = await 开页(1280);
  const 基线 = await 清单(p0);
  out.步骤0_前置 = { 积分: await 积分(p0), 基线数: 基线.length,
    基线id: 基线.map((n) => n.id).sort(), 状态行: await 状态行(p0),
    改前缩放标签: await 缩放标签(p0), 改前当前缩放: await 当前缩放(p0) };
  log('【前置】节点数 ' + 基线.length + ' ｜ 积分 ' + out.步骤0_前置.积分 +
      ' ｜ 改前缩放 ' + out.步骤0_前置.改前缩放标签 + '（实际 scale ' + out.步骤0_前置.改前当前缩放 + '）');
  await p0.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤0: ' + e.message]); log('🔴 步骤0 ' + e.message); }

// ============ 步骤 1：🔴 改画布缩放（唯一被改的变量）============
try {
  const p1 = await 开页(1280);
  const 前 = { 标签: await 缩放标签(p1), 实际: await 当前缩放(p1) };
  const r = await 设缩放(p1, 目标宽);
  out.步骤1_改缩放 = { 改前: 前, 设定: 目标宽, 结果: r };
  log('【改缩放】' + 目标宽 + '% ⇒ 标签 ' + r.标签 + '（实际 scale ' + r.实际 + '）');
  await p1.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤1: ' + e.message]); log('🔴 步骤1 ' + e.message); }

// ============ 步骤 2：建空视频节点 + 上传（为了清理路径与批次 221 对齐）============
try {
  const p1 = await 开页(1280);
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
  out.空节点当前缩放 = await 当前缩放(p1);
  log('【新建】' + JSON.stringify(新增[0]));
  await p1.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤2: ' + e.message]); log('🔴 步骤2 ' + e.message); }

try {
  const p1 = await 开页(1280);
  const files = p1.locator('input[type=file]');
  let 目标i = -1;
  for (let i = 0, n = await files.count(); i < n; i++) {
    const acc = await files.nth(i).getAttribute('accept');
    if (acc && /video\/(mp4|quicktime)|\.mp4/.test(acc)) { 目标i = i; break; }
  }
  if (目标i < 0) throw new Error('没有接受视频的 file input');
  const 上传前 = (await 清单(p1)).map((n) => n.id);
  await files.nth(目标i).setInputFiles(上传文件);
  let 新出来 = null;
  for (let t = 0; t < 30; t++) {
    await p1.waitForTimeout(2000);
    const 出来的 = (await 清单(p1)).filter((n) => !上传前.includes(n.id) && !自建.includes(n.id));
    if (出来的.length) { for (const nn of 出来的) 自建.push(nn.id); 新出来 = 出来的; break; }
  }
  if (!新出来 || !新出来.length) throw new Error('30 次轮询都没等到新产物');
  out.媒体节点 = 新出来[0];
  log('【上传】新产物 ' + JSON.stringify(新出来[0]));
  await p1.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤3: ' + e.message]); log('🔴 步骤3 ' + e.message); }

// ============ 步骤 4：扫描（每臂先读「当前缩放」，再取景）============
log('【扫描】' + 扫描档.length + ' 档 × 1 次，目标 ' + JSON.stringify(目标));
out.扫描 = [];
let 臂序号 = 0;
for (const w of 扫描档) {
  臂序号 += 1;
  const p2 = await ctx.newPage();
  try {
    await p2.setViewportSize({ width: w, height: H });
    await p2.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p2.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p2.waitForTimeout(4500);
    const 前置 = await p2.evaluate((nid) => !!document.querySelector(`.react-flow__node[data-id="${nid}"]`), 目标.id);
    if (!前置) { log(`w=${w} ⛔ 节点不在`); await p2.close(); continue; }
    // 📌 同源读数对：开页时的当前缩放（未取景）
    const 当前 = await 当前缩放(p2);
    const 取 = await 取景(p2, 目标);
    if (!取.ok) { log(`w=${w} ⛔ ${取.无效臂}`); await p2.close(); continue; }
    const 三采 = [];
    for (let i = 0; i < 3; i++) { 三采.push(await 采样(p2, 目标.id)); await p2.waitForTimeout(500); }
    const ss = [...new Set(三采.map((x) => x.vp && x.vp[2]))];
    const 末 = 三采[2];
    const rec = { w, 臂: 臂序号, 当前缩放开页时: 当前, scale: 末.vp ? 末.vp[2] : null,
      屏上: 末.屏上, off: 末.off, 中心: 末.中心, 页内一致: ss.length === 1 };
    out.扫描.push(rec);
    log(`w=${w} 当前=${当前} → 落点 s=${JSON.stringify(ss)} 屏上=${JSON.stringify(末.屏上)} 中心Y=${末.中心 ? 末.中心[1] : null}`);
  } catch (e) { log(`w=${w} 🔴 ${e.message}`); }
  finally { try { await p2.close(); } catch (e) { /* 页签可能被别的会话关掉 */ } }
}

// ============ 步骤 5：收尾（删自建节点 + 缩放归位 26%）============
try {
  const p3 = await 开页(1280);
  out.清理 = { 要删: 自建.slice() };
  await 设缩放(p3, 50);           // 先放大，保证自建节点在视口里
  for (const id of 自建) out.清理[id] = await 删一个(p3, id);
  const 归位 = await 设缩放(p3, 26);
  out.清理.缩放归位 = 归位;
  const 末清单 = await 清单(p3);
  const 基线集 = new Set((out.步骤0_前置 || {}).基线id || []);
  out.清理.最终数 = 末清单.length;
  out.清理.多出来 = 末清单.filter((n) => !基线集.has(n.id)).map((n) => n.id + ' ' + n.aria);
  out.清理.少了 = ((out.步骤0_前置 || {}).基线id || []).filter((x) => !末清单.some((n) => n.id === x));
  out.清理.最终状态行 = await 状态行(p3);
  out.清理.最终积分 = await 积分(p3);
  out.清理.最终缩放 = await 缩放标签(p3);
  out.清理.最终当前缩放 = await 当前缩放(p3);
  log('【收尾】节点数 ' + out.清理.最终数 + ' ｜ 多 ' + JSON.stringify(out.清理.多出来) + ' ｜ 少 ' + JSON.stringify(out.清理.少了));
  log('【收尾】' + out.清理.最终状态行 + ' ｜ 缩放 ' + out.清理.最终缩放 + '（实际 ' + out.清理.最终当前缩放 + '）｜ 积分 ' + out.清理.最终积分);
  await p3.close();
} catch (e) { out.清理 = { 出错: e.message }; log('🔴 清理 ' + e.message); }

out.自建清单 = 自建;
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);