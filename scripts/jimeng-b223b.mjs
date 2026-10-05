/**
 * 批次 223b：**接着往右扫时间线族**（`CSS 1200×207`）。
 *
 * 📌 批次 223 已经拿到的两条硬读数：
 *   ① **`视频 1`（`320×569`）与 `音频 68`（`320×320`）的 `N` 曲线逐档相同**
 *      （`0.269333/0.26 = 1.035897` vs `1.035898`；`0.486732/0.26 = 1.872046` vs `1.872047`）
 *      ⇒ 🔴 **`w*` 与 CSS 高度无关**（立规 104 的中心 Y 判别：带子右端 `1231` 起 Y 从 `243` 跳到 `360` 家族）。
 *   ② 🔴 **M-线性（预测 `w* ≈ 1175.9`）与 M-倒数（预测 `w* ≈ 1194.9`）都被否掉**：
 *      时间线族在 `1165`–`1205` 四十一档**全读 `0.5`、且中心 Y 恰好 `360`** ——
 *      而「`0.5` + `Y = 360`」正是立规 104 里「居中 50%」那一支 ⇒ 按结果推进（立规 98），
 *      **整段都在 `w*` 的左边** ⇒ **`w* > 1205`**，
 *      也就是**方向与「CSS 越宽 `w*` 越小」的外推相反**（`320→1212`、`569→1202`）。
 *
 * 📌 本版：时间线族 `1206`–`1290` **步长 3**（带子约 `19px` 宽，步长 `3` 仍能拿到 ≥`4` 个带内点，
 *   够把起点夹到 `±3px`，再决定要不要步长 `1` 精修）。
 *
 * ⛔ 全程只读：不新建、不上传、不删除；每档把缩放设回 `26%`。
 */

import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const H = 720;
const 上传文件 = '/tmp/jimeng-b196-probe.mp4';
const 目标宽 = 26;          // 🔴 唯一被改的变量（同一个页面内生效，不靠持久化）
const 扫描档 = [];
for (let w = 1210; w <= 1240; w += 1) 扫描档.push(w);
const 目标 = { id: 'node_tadm1nyykc', 词: '音频 68' };   // -empty 族，100% 复现
const 时间线档 = []; for (let w = 1206; w <= 1290; w += 3) 时间线档.push(w);   // 往右夹 w*
const 视频档 = [];                                                                    // 本版不再测

const OUT = '/tmp/b223b.json';

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



const 目标集 = [
  { 标签: '时间线1200x207', id: 'node_d4tjtpnatq', 词: '时间线 2', 档: 时间线档 },
  { 标签: '视频1_320x569', id: 'node_236ctpehgg', 词: '视频 1', 档: 视频档 },
];

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

const p0 = await 开页(1280);
out.步骤0_前置 = {
  积分: await 积分(p0), 基线id: (await 清单(p0)).map((n) => n.id).sort(),
  基线数: (await 清单(p0)).length, 状态行: await 状态行(p0),
  缩放标签: await 缩放标签(p0), 当前缩放: await 当前缩放(p0),
  CSS尺寸: await p0.evaluate(() => {
    const g = (id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); return n ? [n.offsetWidth, n.offsetHeight] : null; };
    return { 音频68: g('node_tadm1nyykc'), 时间线2: g('node_d4tjtpnatq'), 视频1: g('node_236ctpehgg'), 文本3: g('node_5gftn3dnt1') };
  }),
};
log('【前置】节点 ' + out.步骤0_前置.基线数 + ' ｜ 新页缩放 ' + out.步骤0_前置.缩放标签 + '（实际 ' + out.步骤0_前置.当前缩放 + '）');
log('【前置】CSS 尺寸 ' + JSON.stringify(out.步骤0_前置.CSS尺寸));
await p0.close();

const 主 = await 开页(1280);
let 臂序号 = 0;
out.扫描 = {};
for (const 组 of 目标集) {
  out.扫描[组.标签] = [];
  log('【扫描】' + 组.标签 + ' ' + 组.档.length + ' 档（目标 ' + 组.词 + '）');
  for (const w of 组.档) {
    臂序号 += 1;
    try {
      await 主.setViewportSize({ width: w, height: H });
      await 主.waitForTimeout(900);
      const 设 = await 设缩放(主, 目标宽);
      await 主.waitForTimeout(700);
      const 当前 = await 当前缩放(主);
      const 前置 = await 主.evaluate((nid) => !!document.querySelector(`.react-flow__node[data-id="${nid}"]`), 组.id);
      if (!前置) { log(`  w=${w} ⛔ 节点不在`); continue; }
      const 取 = await 取景(主, 组);
      if (!取.ok) { log(`  w=${w} ⛔ ${取.无效臂}`); out.扫描[组.标签].push({ w, 臂: 臂序号, 无效臂: 取.无效臂 }); continue; }
      const 三采 = [];
      for (let i = 0; i < 3; i++) { 三采.push(await 采样(主, 组.id)); await 主.waitForTimeout(450); }
      const ss = [...new Set(三采.map((x) => x.vp && x.vp[2]))];
      const 末 = 三采[2];
      const rec = { w, 臂: 臂序号, 当前缩放: 当前, scale: 末.vp ? 末.vp[2] : null,
        屏上: 末.屏上, off: 末.off, 中心: 末.中心, 页内一致: ss.length === 1, 用的词: 取.用的词 };
      out.扫描[组.标签].push(rec);
      log(`  w=${w} z0=${当前} → s=${JSON.stringify(ss)} 屏上=${JSON.stringify(末.屏上)} 中心Y=${末.中心 ? 末.中心[1] : null}`);
    } catch (e) { log(`  w=${w} 🔴 ${e.message}`); }
  }
}

// 收尾：缩放归位 + 清点（本批不建节点）
try {
  await 主.setViewportSize({ width: 1280, height: H });
  await 主.waitForTimeout(900);
  const 归位 = await 设缩放(主, 26);
  const 末清单 = await 清单(主);
  const 基线集 = new Set(out.步骤0_前置.基线id || []);
  out.清理 = { 缩放归位: 归位, 最终缩放: await 缩放标签(主), 最终当前缩放: await 当前缩放(主),
    最终数: 末清单.length, 状态行: await 状态行(主), 积分: await 积分(主),
    多出来: 末清单.filter((n) => !基线集.has(n.id)).map((n) => n.id + ' ' + n.aria),
    少了: (out.步骤0_前置.基线id || []).filter((x) => !末清单.some((n) => n.id === x)) };
  log('【收尾】缩放 ' + out.清理.最终缩放 + '（实际 ' + out.清理.最终当前缩放 + '）｜ 节点 ' + out.清理.最终数 +
      ' ｜ 多 ' + JSON.stringify(out.清理.多出来) + ' ｜ 少 ' + JSON.stringify(out.清理.少了));
  log('【收尾】' + out.清理.状态行 + ' ｜ 积分 ' + out.清理.积分);
  await 主.close();
} catch (e) { out.清理 = { 出错: e.message }; log('🔴 清理 ' + e.message); }

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
process.exit(0);
