/**
 * 批次 222b：**修正批次 222 的前提错误** —— 「改了设置」不等于「读数是在那个设置下测的」。
 *
 * 🔴 批次 222 第一版（`jimeng-b222.mjs`）的实测结果：
 *   把画布缩放改成 `40%` 之后，**紧接着读到的确实变了**（`实际 scale 0.4`、标签
 *   `Zoom options, 40%`），但**随后每一个新开的页面，开页时的 `scale` 又回到 `0.260267`**，
 *   落点也逐字复现批次 221 ⇒ 🔴 **画布缩放根本不持久化到新开的页面**。
 *   ⇒ 第一版那个「单变量实验」**根本没做成**：被改的量在读数那一刻并不生效。
 *
 * 📌 本版的做法：**同一个页面里改缩放，并且只 `setViewportSize`、绝不重载。**
 *   每档的次序是：`设缩放(40%) → resize 到 w → 读当前缩放（验证它扛过了 resize）
 *   → 取景 → 三采落点`。⇒ 「当前缩放」与「落点」是**同一页面、同一时刻**的一对读数。
 *
 * 🔴 同样要能死的假设（这才是本版真正的靶子）：
 *   **H1（地板 = 当前画布缩放）**：当前缩放 `0.4` 时，带子地板应变成 `0.4`、
 *     带子变窄上移（按批次 221 的 `ln` 斜率 `0.0348/px`，`0.5→0.4` 只需 `≈6.4px`
 *     ⇒ 带子应缩到约 `[1224, 1230]`）。
 *   **H2（地板是硬常数 `0.260267`）**：当前缩放 `0.4` 时，带子仍停在 `[1212, 1230]`、
 *     地板仍是 `0.260267`。
 *   **H3（resize 会把缩放重置）**：resize 之后当前缩放不再是 `0.4`
 *     ⇒ 那就只能改成「每档 resize 之后再设一次缩放」，本版会**逐档记录**这一点。
 *
 * 📌 立规 106：**改设置之前先证明这个设置在读数那一刻生效**，
 *   并且**证明它扛过了中途发生的一切**（本批的中途事件是 viewport resize）。
 *
 * ⛔ 不触发任何生成；不新建节点（本版不需要清理，只把缩放归位）。
 */

import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 上传文件 = '/tmp/jimeng-b196-probe.mp4';
const 目标宽 = 40;          // 🔴 唯一被改的变量（同一个页面内生效，不靠持久化）
const 扫描档 = [];
for (let w = 1210; w <= 1240; w += 1) 扫描档.push(w);
const 目标 = { id: 'node_tadm1nyykc', 词: '音频 68' };   // -empty 族，100% 复现
const OUT = '/tmp/b222b.json';

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


// ============ 主流程：单页面、只 resize、每档先验证当前缩放 ============
const browser = await chromium.connectOverCDP({ endpointURL: 'http://127.0.0.1:9444' });
const ctx = browser.contexts()[0];

async function 开页(w) {
  const p = await ctx.newPage();
  await p.setViewportSize({ width: w, height: H });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(4500);
  return p;
}

// 步骤 0：前置基线 + 「换新页会怎样」的正面取证（批次 222 的核心发现，重复一遍确认）
try {
  const p0 = await 开页(1280);
  const 基线 = await 清单(p0);
  out.步骤0_前置 = { 积分: await 积分(p0), 基线数: 基线.length,
    基线id: 基线.map((n) => n.id).sort(), 状态行: await 状态行(p0),
    新页缩放标签: await 缩放标签(p0), 新页当前缩放: await 当前缩放(p0) };
  log('【前置】节点数 ' + 基线.length + ' ｜ 新开页缩放 ' + out.步骤0_前置.新页缩放标签 +
      '（实际 ' + out.步骤0_前置.新页当前缩放 + '）');
  await p0.close();
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤0: ' + e.message]); log('🔴 步骤0 ' + e.message); }

// 步骤 1：在**这一个页面**上把缩放设成 40%，随后只 resize、不重载
const 主 = await 开页(1280);
try {
  out.步骤1_设缩放 = { 设定: 目标宽, 结果: await 设缩放(主, 目标宽) };
  log('【设缩放】' + 目标宽 + '% ⇒ ' + out.步骤1_设缩放.结果.标签 + '（实际 ' + out.步骤1_设缩放.结果.实际 + '）');
} catch (e) { out.出错 = (out.出错 || []).concat(['步骤1: ' + e.message]); log('🔴 步骤1 ' + e.message); }

// 步骤 2：扫描
log('【扫描】' + 扫描档.length + ' 档 × 1 次，同一页面内只 resize');
out.扫描 = [];
let 臂序号 = 0;
for (const w of 扫描档) {
  臂序号 += 1;
  try {
    await 主.setViewportSize({ width: w, height: H });
    await 主.waitForTimeout(900);
    // 📌 立规 106：每档都**重新设一次**缩放，并**当场验证**
    const 设 = await 设缩放(主, 目标宽);
    await 主.waitForTimeout(700);
    const 当前 = await 当前缩放(主);
    const 前置 = await 主.evaluate((nid) => !!document.querySelector(`.react-flow__node[data-id="${nid}"]`), 目标.id);
    if (!前置) { log(`w=${w} ⛔ 节点不在`); continue; }
    const 取 = await 取景(主, 目标);
    if (!取.ok) { log(`w=${w} ⛔ ${取.无效臂}`); continue; }
    const 三采 = [];
    for (let i = 0; i < 3; i++) { 三采.push(await 采样(主, 目标.id)); await 主.waitForTimeout(450); }
    const ss = [...new Set(三采.map((x) => x.vp && x.vp[2]))];
    const 末 = 三采[2];
    const rec = { w, 臂: 臂序号, 设后标签: 设.标签, 设后当前缩放: 当前,
      设后生效: 当前 === 0.4, scale: 末.vp ? 末.vp[2] : null,
      屏上: 末.屏上, off: 末.off, 中心: 末.中心, 页内一致: ss.length === 1 };
    out.扫描.push(rec);
    log(`w=${w} 设后当前=${当前}${当前 === 0.4 ? '' : ' ⚠️没生效'} → 落点 s=${JSON.stringify(ss)} 屏上=${JSON.stringify(末.屏上)} 中心Y=${末.中心 ? 末.中心[1] : null}`);
  } catch (e) { log(`w=${w} 🔴 ${e.message}`); }
}

// 步骤 3：缩放归位 + 收尾读数（本版不建节点，只需把缩放放回去并清点）
try {
  await 主.setViewportSize({ width: 1280, height: H });
  await 主.waitForTimeout(900);
  const 归位 = await 设缩放(主, 26);
  out.清理 = { 缩放归位: 归位, 最终当前缩放: await 当前缩放(主), 最终缩放标签: await 缩放标签(主),
    最终数: (await 清单(主)).length, 最终状态行: await 状态行(主), 最终积分: await 积分(主) };
  const 基线集 = new Set((out.步骤0_前置 || {}).基线id || []);
  const 末清单 = await 清单(主);
  out.清理.多出来 = 末清单.filter((n) => !基线集.has(n.id)).map((n) => n.id + ' ' + n.aria);
  out.清理.少了 = ((out.步骤0_前置 || {}).基线id || []).filter((x) => !末清单.some((n) => n.id === x));
  log('【收尾】缩放 ' + out.清理.最终缩放标签 + '（实际 ' + out.清理.最终当前缩放 + '）｜ 节点 ' +
      out.清理.最终数 + ' ｜ 多 ' + JSON.stringify(out.清理.多出来) + ' ｜ 少 ' + JSON.stringify(out.清理.少了));
  log('【收尾】' + out.清理.最终状态行 + ' ｜ 积分 ' + out.清理.最终积分);
  await 主.close();
} catch (e) { out.清理 = { 出错: e.message }; log('🔴 清理 ' + e.message); }

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);
