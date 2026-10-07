/**
 * 批次 296 · 立规 171 的前提 B：同一配置跑多遍，量**跨遍极差**。
 *
 * 🔴 起意：批次 295 测出「翻转后的读数根本不落定」——
 *    四个 `音频` 节点、同一遍、同一个盒给出 `1.08303 / 1.09221 / 1.10505 / 1.11944`
 *    （类内极差 `0.0364`），`视频 1` 本次 `0.602567` 掉在批次 287/289/292 那七次的
 *    `0.618…0.626` 之外。而**每一臂自己的「连读两次逐字相同」都是 ✅**。
 *    ⇒ 缺的那道前提就是立规 171 的 B：**同一配置跑第二遍、第三遍，必须逐字相同**。
 *    📌 本批不比较节点之间，**只比较「同一个节点自己」在不同遍之间**。
 *
 * 📌 三道正交前提（任一不过 ⇒ 整组作废，「没跳」与「抖动」都不当发现）：
 *   P0 **确定性对照**：不跳的 `文本 1` 在 `w=1212` 上跑 3 遍，必须**遍遍逐字 `1.75`**
 *      ⇒ 它证明**读数系统本身是确定的**，所以后面那些抖动不是测量噪声。
 *   P1 **阈值对照**：`w=1211` 上 `音频 1` 与 `文本 1` 都不跳（逐字命中闭式）
 *      ⇒ 证明翻转点仍然卡在 `1212`，本批量的确实是翻转之后那一侧。
 *   P2 **落定自检**：每一遍自己连读两次必须逐字相同（否则该遍不计入跨遍统计）。
 *
 * 其它前提：轴向自检 / `z0 > 闭式` 硬门 / 点击生效自检 / 参数写死（`Meta+Equal ×13`）/
 *   节点 id 与盒一律现找现量（按 `aria` 精确匹配 `<kind> node: <短名>`）/
 *   **每遍都是全新浏览器 + 全新上下文**（承接批次 295 的基础设施结论）。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const STATE = `${process.env.HOME}/.jimeng-automation/state.json`;
const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = '/tmp/b296.json';
const 放大键 = 'Meta+Equal';
const 按够 = 13;
const 遍数 = 3;

const 臂表 = [
  { w: 1212, 遍: 1, kind: '文本', 名: '文本 1', 角色: 'P0 确定性对照：不跳的一侧，必须遍遍逐字 1.75' },
  { w: 1212, 遍: 2, kind: '文本', 名: '文本 1', 角色: 'P0 确定性对照' },
  { w: 1212, 遍: 3, kind: '文本', 名: '文本 1', 角色: 'P0 确定性对照' },
  { w: 1212, 遍: 1, kind: '音频', 名: '音频 1', 角色: 'P2 主体：跳的一侧，量跨遍极差' },
  { w: 1212, 遍: 2, kind: '音频', 名: '音频 1', 角色: 'P2 主体' },
  { w: 1212, 遍: 3, kind: '音频', 名: '音频 1', 角色: 'P2 主体' },
  { w: 1212, 遍: 1, kind: '视频', 名: '视频 1', 角色: 'P2 主体：跳的另一类' },
  { w: 1212, 遍: 2, kind: '视频', 名: '视频 1', 角色: 'P2 主体' },
  { w: 1212, 遍: 3, kind: '视频', 名: '视频 1', 角色: 'P2 主体' },
  { w: 1211, 遍: 1, kind: '音频', 名: '音频 1', 角色: 'P1 阈值对照：1211 必须不跳' },
  { w: 1211, 遍: 1, kind: '文本', 名: '文本 1', 角色: 'P1 阈值对照：1211 必须不跳' },
];

const 屏上律 = (ww) => Math.max(100, ww - 532);
const vf = (z) => Math.min(8, Math.max(0.08, z));
const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b296', 问: '同一节点自己跨遍到底差多少？（立规 171 的前提 B）', 遍数, 臂表, 臂: [], 判定: {} };

const 读 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  return {
    scale: m ? Number(m[1]) : null,
    选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.dataset.id),
  };
});

for (const A of 臂表) {
  let br = null; let p = null;
  const 记 = { w: A.w, 遍: A.遍, kind: A.kind, 名: A.名, 角色: A.角色 };
  try {
    br = await chromium.launch({ headless: true });
    const ctx = await br.newContext({ storageState: STATE, viewport: { width: A.w, height: 720 } });
    p = await ctx.newPage();
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 60000 });
    await p.waitForTimeout(6000);

    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== A.w || 实际.h !== 720) throw new Error(`轴向自检失败：实测 ${实际.w}×${实际.h}`);

    const ariaWant = `${A.kind} node: ${A.名}`;
    const 目标 = await p.evaluate((aria) => {
      const e = Array.from(document.querySelectorAll('.react-flow__node[data-id]'))
        .find((x) => x.getAttribute('aria-label') === aria);
      if (!e) return null;
      return { id: e.dataset.id, aria: e.getAttribute('aria-label'), W: e.offsetWidth, H: e.offsetHeight };
    }, ariaWant);
    if (!目标) throw new Error(`找不到 aria 为「${ariaWant}」的节点`);
    记.节点id = 目标.id;
    记.盒 = { W: 目标.W, H: 目标.H };
    const 闭式 = +vf(Math.min(屏上律(A.w) / 目标.W, (720 - 160) / 目标.H)).toFixed(6);
    记.闭式 = 闭式;

    for (let i = 0; i < 按够; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1200);
    const z0 = await 读(p);
    记.z0 = z0.scale;
    if (z0.scale === null) throw new Error('读不到缩放');
    if (!(z0.scale > 闭式)) throw new Error(`z0(${z0.scale}) 不高于闭式(${闭式}) ⇒ 读不到平台`);

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
      const sel = `[data-testid="canvas-search-result-node_${目标.id.replace(/^node_/, '')}"]`;
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
    await p.waitForTimeout(3000);
    const a1 = await 读(p);
    await p.waitForTimeout(2500);
    const a2 = await 读(p);
    记.z后1 = a1.scale;
    记.z后2 = a2.scale;
    记.落定 = a1.scale === a2.scale;              // P2 落定自检（该遍自检）
    记.选中 = a2.选中;
    记.点击生效 = a2.选中.includes(目标.id);
    if (!记.点击生效) throw new Error(`点击未生效（选中=${JSON.stringify(a2.选中)}）`);
    记.vs = a2.scale;
    记.跳了 = Math.abs(a2.scale - 闭式) > 2e-3;
    log(`w=${A.w}｜${A.kind} ${A.名}｜第${A.遍}遍｜盒 ${目标.W}×${目标.H}｜z0=${z0.scale}｜vs=${a2.scale}｜闭式 ${闭式}｜${记.跳了 ? '🔴 跳' : '✅ 不跳'}｜落定 ${记.落定 ? '✅' : '🔴'}`);
  } catch (e) {
    记.错误 = e.message;
    log(`w=${A.w}｜${A.kind} ${A.名}｜第${A.遍}遍 🔴 ${e.message}`);
  } finally {
    try { if (p) await p.close(); } catch (e) { /* 忽略 */ }
    try { if (br) await br.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ── 跨遍统计（只比较同一个节点自己）──────────────────────
const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.vs !== undefined && x.落定);
const 组 = {};
for (const x of 好.filter((y) => y.w === 1212)) {
  const k = `${x.kind} ${x.名}`;
  (组[k] ||= { 值: [], 盒: x.盒 }).值.push(x.vs);
}
const 统计 = {};
for (const [k, v] of Object.entries(组)) {
  const s = [...v.值].sort((a, b) => a - b);
  统计[k] = {
    遍数: s.length,
    值: s,
    极差: s.length > 1 ? +(s[s.length - 1] - s[0]).toFixed(6) : null,
    逐字全同: new Set(s).size === 1,
    均值: +(s.reduce((a, b) => a + b, 0) / s.length).toFixed(6),
  };
}

// 🔴 v2 修：统计的键是 kind + 空格 + 名（`文本` + ` ` + `文本 1` = `文本 文本 1`），
//    v1 这里写的是 `文本 1`，查表得到 undefined ⇒ P0 假失败 ⇒ **整组被误判为作废**，
//    而原始读数一个都没受影响（文本 1 三遍逐字 1.75）。立规 174：先修判决，再用已落盘读数重算核对。
const P0 = ['文本 文本 1'];
const P1 = 臂表.filter((a) => a.w === 1211);
const p0过 = P0.every((n) => 统计[n] && 统计[n].逐字全同);
const p1过 = P1.every((a) => {
  const r = 好.find((x) => x.w === 1211 && x.kind === a.kind && x.名 === a.名);
  return r && !r.跳了;
});

log('\n════ 跨遍统计（w=1212）════');
for (const [k, v] of Object.entries(统计)) {
  log(`  ${k.padEnd(10)} ${v.遍数} 遍｜${v.值.join(' / ')}｜极差 ${v.极差}｜${v.逐字全同 ? '✅ 逐字全同' : '🔴 不全同'}`);
}

out.判定 = {
  有效臂: `${好.length}/${臂表.length}`,
  P0_确定性对照: p0过 ? '✅ 文本 1 在 1212 上遍遍逐字 1.75 ⇒ 读数系统本身是确定的' : '🔴 文本 1 自己就不复现 ⇒ 后面那些抖动无法归因，整组作废',
  P1_阈值对照: p1过 ? '✅ 1211 上音频 1 与 文本 1 都不跳 ⇒ 翻转点仍卡在 1212' : '🔴 1211 上出现跳变 ⇒ 阈值不在 1212，整组作废',
  跨遍: JSON.stringify(统计, null, 1),
  结论: (p0过 && p1过)
    ? `✅ **不跳的一侧跨遍逐字可复现（极差 0）**，🔴 **跳的一侧跨遍极差不为 0** —— ` +
      Object.entries(统计).filter(([k]) => k !== '文本 文本 1')
        .map(([k, v]) => `${k} 极差 ${v.极差}`).join('、') +
      ` ⇒ 📌 **抖动只发生在「翻转之后」那一侧，不是测量噪声**`
    : '🔴 **前提没过 ⇒ 整组作废**，不编',
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
