/**
 * 批次 303 · 用一条**不需要预先知道 vs** 的预测去撞 `locateContent` 的算式。
 *
 * 🔴 起意：批次 302 测到「路径依赖只值 0.0025、只解释跨遍波动的 12%」，
 *    而它那 `8` 条臂里**有 `2` 条被我自己那条过严的硬门作废**，且作废的恰恰是
 *    `z0` 最小（最靠近平台）的那一档 ⇒ 🔴 **最可能有信号的地方没测到**。
 *
 * 📌 换一个更锐利的杠杆：**让 `z0` 掉到 `vs` 以下。**
 *    批次 298 读出的算式是 `zoom = min( vf(max(viewport.zoom, .5)), vs )`，
 *    ⇒ 🔴 **若 `z0 < vs`，则 `min` 取的是 `max(z0,.5)`，也就是「什么都不动」**
 *    ⇒ 📌 **预测 P3（不需要预先知道 `vs`）**：
 *          **起点 `z0` 低于平台时，定位后的缩放应逐字等于 `z0`。**
 *    📌 这条预测要么逐字命中、要么被推翻，**没有中间态**。
 *
 * 📌 预期形状（`音频 1`、`w=1212`，实测平台 `≈1.102`）：
 *      `z0 = 2.779 / 2.316 / 1.93 / 1.608 / 1.34 / 1.1167 / 0.9306 / 0.7755`
 *      `≥ 1.34` ⇒ 落在平台 `≈1.10` ｜ 🔴 **`1.1167` 是刀口**（离平台只差 `1%`）
 *      🔴 **`0.9306` 及以下 ⇒ 应逐字等于 `z0`**
 *    `文本 1`（平台 `1.75`）的刀口在 `z0 = 1.608` 那档。
 *
 * 📌 判据（**测量前写死**）：
 *      **P3** `z0 < vs` 的那些臂，`vs实测` **必须逐字等于 `z0`** ⇒ 命中即坐实算式；
 *          任一条不等 ⇒ 🔴 **算式被推翻**，不许含糊。
 *      **P4** `z0 ≥ vs` 的那些臂，终点应挤在平台附近（极差小）。
 *
 * 前提检查：轴向自检 / **落定自检** / 点击生效自检 / `aria` 精确匹配现找现量 /
 *   参数写死（放大键次数是唯一变量）/ 每臂独立浏览器。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b303.json';
const 放大键 = 'Meta+Equal';
const w = 1212;

// 放大键次数是唯一变量；z0 ≈ 2.779 ÷ 1.2^(13−n)
const 臂表 = [
  { 键: '音频1/13', kind: '音频', 名: '音频 1', 按: 13 },
  { 键: '音频1/10', kind: '音频', 名: '音频 1', 按: 10 },
  { 键: '音频1/9',  kind: '音频', 名: '音频 1', 按: 9 },
  { 键: '音频1/8',  kind: '音频', 名: '音频 1', 按: 8 },
  { 键: '音频1/7',  kind: '音频', 名: '音频 1', 按: 7 },
  { 键: '音频1/6',  kind: '音频', 名: '音频 1', 按: 6 },
  { 键: '文本1/13', kind: '文本', 名: '文本 1', 按: 13 },
  { 键: '文本1/11', kind: '文本', 名: '文本 1', 按: 11 },
  { 键: '文本1/10', kind: '文本', 名: '文本 1', 按: 10 },
  { 键: '文本1/9',  kind: '文本', 名: '文本 1', 按: 9 },
];

const vf = (z) => Math.min(8, Math.max(0.08, z));
const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b303',
  问: '让起点掉到平台以下：终点该逐字等于起点 —— 这条不需要预先知道 vs',
  判据: { P3: 'z0 低于平台 ⇒ 终点逐字等于 z0（算式坐实）', P4: 'z0 高于平台 ⇒ 终点挤在平台附近' },
  w, 臂表, 臂: [], 判定: {},
};

for (const A of 臂表) {
  let br = null; let p = null; let nid = null;
  const 记 = { 键: A.键, w, 按: A.按, kind: A.kind, 名: A.名 };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: w, height: 720 } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== w || 实际.h !== 720) throw new Error(`轴向自检失败：实测 ${实际.w}×${实际.h}`);

    const ariaWant = `${A.kind} node: ${A.名}`;
    const 目标 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      return e ? { id: e.dataset.id, W: e.offsetWidth, H: e.offsetHeight } : null;
    }, ariaWant);
    if (!目标) throw new Error(`找不到 aria 为「${ariaWant}」的节点`);
    nid = 目标.id;
    记.画布盒 = { W: 目标.W, H: 目标.H };

    for (let i = 0; i < A.按; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1400);
    const 读缩放 = () => p.evaluate(() => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Number(m[1]) : null;
    });
    const z0 = await 读缩放();
    记.z0 = z0;
    if (z0 === null) throw new Error('读不到缩放');
    if (!(z0 > 0.5)) throw new Error(`z0(${z0}) 低于 .5 下限，无法观察 min 那一侧`);

    const 钮 = await p.evaluate(() => {
      const b = document.querySelector('button[aria-label="搜索"]');
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return { 中心: [r.x + r.width / 2, r.y + r.height / 2], 可见: r.width > 0 && r.height > 0 && r.y >= 0 && r.bottom <= innerHeight };
    });
    if (!钮 || !钮.可见) throw new Error('找不到可见的搜索钮');
    await p.mouse.click(钮.中心[0], 钮.中心[1]);
    await p.waitForTimeout(1600);

    let 行 = null; let 用名 = null;
    for (const 名 of [A.名, ariaWant, A.kind]) {
      await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
      await p.keyboard.type(名, { delay: 80 });
      await p.waitForTimeout(2000);
      const sel = `[data-testid="canvas-search-result-node_${nid.replace(/^node_/, '')}"]`;
      let r = await p.evaluate((s) => {
        const e = document.querySelector(s);
        if (!e) return null;
        e.scrollIntoView({ block: 'center' });
        const b = e.getBoundingClientRect();
        return { 中心: [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)], 可见: b.width > 0 && b.height > 0 && b.y >= 0 && b.bottom <= innerHeight && b.x >= 0 && b.right <= innerWidth };
      }, sel);
      if (r && !r.可见) {
        await p.waitForTimeout(600);
        r = await p.evaluate((s) => { const e = document.querySelector(s); const b = e.getBoundingClientRect(); return { 中心: [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)], 可见: b.width > 0 && b.height > 0 && b.y >= 0 && b.bottom <= innerHeight && b.x >= 0 && b.right <= innerWidth }; }, sel);
      }
      if (r && r.可见) { 行 = r; 用名 = 名; break; }
    }
    if (!行) throw new Error(`搜不到「${A.名}」的可见结果行`);
    记.用名 = 用名;
    await p.mouse.click(行.中心[0], 行.中心[1]);
    await p.waitForTimeout(3200);
    const a1 = await 读缩放();
    await p.waitForTimeout(2600);
    const 后 = await p.evaluate((nid2) => {
      const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
      return {
        scale: m ? Number(m[1]) : null,
        选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((x) => x.dataset.id),
      };
    }, nid);
    记.z后1 = a1;
    记.落定 = a1 === 后.scale;
    记.点击生效 = 后.选中.includes(nid);
    if (!记.点击生效) throw new Error(`点击未生效（选中=${JSON.stringify(后.选中)}）`);
    记.终点 = 后.scale;
    记.与起点逐字相同 = 后.scale === z0;
    记.比起点 = +(后.scale - z0).toFixed(6);
    log(`${A.键.padEnd(10)}｜z0=${String(z0).padEnd(9)}｜终点=${String(后.scale).padEnd(10)}｜落定 ${记.落定 ? '✅' : '🔴'}｜${记.与起点逐字相同 ? '✅ 与起点逐字相同' : '🔴 与起点不同（差 ' + 记.比起点 + '）'}`);
  } catch (e) {
    记.错误 = e.message;
    log(`${A.键.padEnd(10)}🔴 ${e.message}`);
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.终点 !== undefined && x.落定);
log('\n════ 全表 ════');
for (const x of 好) log(`  ${x.键.padEnd(10)} z0=${String(x.z0).padEnd(9)} 终点=${String(x.终点).padEnd(10)} ${x.与起点逐字相同 ? '✅=z0' : '🔴≠z0'}`);

// 平台：取「起点明显高于平台」的那些臂的终点
const 高起 = 好.filter((x) => !x.与起点逐字相同);
const 平台 = 高起.length ? {
  音频: (() => { const a = 好.filter((x) => x.kind === '音频' && !x.与起点逐字相同); return a.length ? +(a.reduce((s, x) => s + x.终点, 0) / a.length).toFixed(6) : null; })(),
  文本: (() => { const a = 好.filter((x) => x.kind === '文本' && !x.与起点逐字相同); return a.length ? +(a.reduce((s, x) => s + x.终点, 0) / a.length).toFixed(6) : null; })(),
} : null;

// P3：终点逐字等于起点的那些臂
const 同起 = 好.filter((x) => x.与起点逐字相同);
const P3过 = 同起.length >= 2 && 同起.every((x) => Math.abs(x.比起点) === 0);

out.判定 = {
  有效臂: `${好.length}/${臂表.length}`,
  平台估计: 平台,
  与起点逐字相同: 同起.map((x) => ({ 键: x.键, z0: x.z0, 终点: x.终点 })),
  与起点不同: 高起.map((x) => ({ 键: x.键, z0: x.z0, 终点: x.终点 })),
  P3: P3过
    ? `✅ **命中**：${同起.length} 条臂的终点与起点逐字相同 ⇒ \`zoom = min(vf(max(viewport.zoom,.5)), vs)\` 算式在 \`z0 < vs\` 那一侧被坐实`
    : '🔴 **P3 未命中**：终点没有逐字等于起点 ⇒ 算式被推翻或还有别的动作',
  P4: 平台 ? `平台估计：音频 ≈${平台.音频}、文本 ≈${平台.文本}；「起点高于平台」的那些臂终点极差：音频 ${(() => { const a = 好.filter((x) => x.kind === '音频' && !x.与起点逐字相同); return a.length > 1 ? +(Math.max(...a.map((x) => x.终点)) - Math.min(...a.map((x) => x.终点))).toFixed(6) : null; })()}、文本 ${(() => { const a = 好.filter((x) => x.kind === '文本' && !x.与起点逐字相同); return a.length > 1 ? +(Math.max(...a.map((x) => x.终点)) - Math.min(...a.map((x) => x.终点))).toFixed(6) : null; })()}` : '（无）',
};
log('\n════ 判定 ════\n' + JSON.stringify(out.判定, null, 1));

const brz = await chromium.launch({ headless: true });
const ctxz = await brz.newContext({ storageState: STATE, viewport: { width: 1280, height: 720 } });
const pz = await ctxz.newPage();
try {
  await pz.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await pz.waitForSelector('.react-flow__node', { timeout: 60000 });
  await pz.waitForTimeout(6000);
  out.末态 = await pz.evaluate(() => ({
    节点数: document.querySelectorAll('.react-flow__node').length,
    状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
    积分: (document.querySelector('[data-testid="canvas-commerce-entry"]') || {}).textContent || null,
  }));
  log('末态独立复查：', JSON.stringify(out.末态));
} finally { try { await pz.close(); await brz.close(); } catch (e) { /* 忽略 */ } }

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入', OUT);
process.exit(0);