/**
 * 批次 282：那一行在 `H ≤ 248` 时**看得见吗**？并拍两张对照图（点不动 / 生效）进手册。
 *
 * 📌 起意（批次 281 的第一条尾巴）：
 *   281 已钉死：**`H ≤ 248` 时鼠标点击送不到结果行**，
 *   命中测试落在 `DIV[data-testid="canvas-search-results-viewport"]`（结果列表的滚动视口）上；
 *   而**把点击直接派发到行元素上就能选中** ⇒ 行的处理器正常。
 *   🔴 **但还有一件没测**：那一行在屏上**是不是被这个视口裁掉了**。
 *   ⇒ **「看得见但点不到」与「根本看不见」对用户是两件完全不同的事**，
 *   **处置办法也不同**（前者可以说「行在那儿、点它没用，只能拉高」；后者连「行在哪」都要另说）。
 *
 * 📌 **本批两问**：
 *   Q1 **视口的盒子有多大、行在不在视口盒子里**（`getBoundingClientRect` + `scrollHeight/clientHeight/overflow-y`）
 *   Q2 **两张对照图**：`H = 248`（点不动）与 `H = 249`（生效），各拍一张**整视口**，
 *      并用 `3px solid #ff8c00` 把那一行框出来 ⇒ 手册里用户能一眼看到「行在那儿、但点不动」
 *
 * 📌 **预测先写死**（立规 129/130）：
 *   P1a **行被视口裁掉**：`H ≤ 248` 时视口的底边 `≤` 行的底边 ⇒ 图上应当**看不到完整的行**
 *   P1b **行没被裁、只是点不到**：视口底边 `>` 行底边 ⇒ 图上应当**完整看得见那一行**
 *   🔴 **P1a 与 P1b 给用户的话完全不同**，所以必须先量清楚再写手册。
 *
 * 📌 **三条前提**：
 *   ① **轴向自检**：`innerW/innerH` 逐字等于设定值；
 *   ② **截图前置检查（手册纪律）**：注入的画框层元素数必须 `=== 1`，
 *      两个框的宽高都必须 `> 0`，否则**不 shutter**（宁可不拍，也不要拍一张没有框的图）；
 *   ③ **命中测试自检**：`H = 249` 上命中必须落在行内部（批次 281 的正例），
 *      `H = 248` 上必须落在 `canvas-search-results-viewport` —— 两条都过才说明这轮读数与 281 一致。
 *
 * 📌 **纪律**：只读（不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**）；
 *   每臂开新页；末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b282.mjs      （落盘 /tmp/b282.json，图落 screenshots/199,200）
 */
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B282_OUT || '/tmp/b282.json';
const 手册目录 = path.resolve(process.cwd(), 'docs/user-manual/jimeng-canvas');
const 图目录 = path.join(手册目录, 'screenshots');
const 宽 = 460;
const 高度组 = [200, 220, 240, 248, 249];
const 拍图档 = new Map([[248, '199-search-row-covered-248.png'], [249, '200-search-row-clickable-249.png']]);
const 节点 = { id: 'node_236ctpehgg', 名: '视频 1', 备用名: ['视频 1', '视频'] };

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b282',
  问: 'H ≤ 248 时那一行是「被视口裁掉」还是「看得见但点不到」？',
  预测: {
    P1a_被裁掉: '视口底边 ≤ 行底边 ⇒ 图上看不到完整的行',
    P1b_没被裁: '视口底边 > 行底边 ⇒ 图上完整看得见那一行',
  },
  宽, 高度组, 节点, 臂: [], 图: [], 收尾: {},
};

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const 短名 = 节点.id.replace(/^node_/, '');

/** 量视口 / 行 / 命中，并按需注入画框层后拍照 */
const 量一档 = async (p, 高, 要拍图) => {
  const 实际 = await p.evaluate(() => ({ w: window.innerWidth, h: window.innerHeight }));
  if (实际.w !== 宽 || 实际.h !== 高) throw new Error(`轴向自检失败：要 ${宽}×${高}，实测 ${实际.w}×${实际.h}`);

  const 钮 = await p.evaluate(() => {
    const e = Array.from(document.querySelectorAll('button, [role="button"]')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 在视口内: r.y >= 0 && r.bottom <= innerHeight };
  });
  if (!钮 || !钮.在视口内) throw new Error('搜索钮不在视口内');
  await p.mouse.click(钮.中心[0], 钮.中心[1]);
  await p.waitForTimeout(1600);
  if (!await p.evaluate(() => !!document.querySelector('[data-testid="canvas-search-panel"]'))) throw new Error('搜索面板没打开');

  let 行 = null;
  for (const 名 of 节点.备用名) {
    await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
    await p.keyboard.type(名, { delay: 80 });
    await p.waitForTimeout(2200);
    行 = await p.evaluate((nid) => {
      const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height), 底: Math.round(r.bottom), 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    }, 短名);
    if (行) break;
  }
  if (!行) throw new Error('搜不到结果行');

  // 视口盒 + 行盒 + 交集
  const 几何 = await p.evaluate((nid) => {
    const vp = document.querySelector('[data-testid="canvas-search-results-viewport"]');
    const row = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
    const r1 = vp ? vp.getBoundingClientRect() : null;
    const r2 = row.getBoundingClientRect();
    const cs = vp ? getComputedStyle(vp) : null;
    const 交顶 = Math.max(r1.top, r2.top), 交底 = Math.min(r1.bottom, r2.bottom);
    return {
      视口: r1 ? { x: Math.round(r1.x), y: Math.round(r1.y), w: Math.round(r1.width), h: Math.round(r1.height), 底: Math.round(r1.bottom), clientHeight: vp.clientHeight, scrollHeight: vp.scrollHeight, scrollTop: vp.scrollTop, overflowY: cs.overflowY } : null,
      行: { x: Math.round(r2.x), y: Math.round(r2.y), w: Math.round(r2.width), h: Math.round(r2.height), 底: Math.round(r2.bottom) },
      行在视口内: r1 ? (r2.top >= r1.top - 0.5 && r2.bottom <= r1.bottom + 0.5) : null,
      交集高: Math.max(0, Math.round(交底 - 交顶)),
    };
  }, 短名);

  // 前提③：命中测试与批次 281 一致性
  const 命中 = await p.evaluate(({ x, y, nid }) => {
    const el = document.elementFromPoint(x, y);
    const 在行内 = !!(el && el.closest && el.closest(`[data-testid="canvas-search-result-node_${nid}"]`));
    return { tag: el?.tagName ?? null, testid: el?.getAttribute('data-testid') ?? null, 在行内 };
  }, { x: 行.中心[0], y: 行.中心[1], nid: 短名 });

  const 屏文 = await p.evaluate(() => {
    const pn = document.querySelector('[data-testid="canvas-search-panel"]');
    return pn ? (pn.innerText || '').replace(/\n+/g, ' ').trim() : null;
  });

  // 前提②：截图前置检查 —— 注入画框层并读回
  let 截图 = null;
  if (要拍图) {
    const 检查 = await p.evaluate(({ x, y, w, h }) => {
      document.querySelectorAll('.__b282_box').forEach((e) => e.remove());
      const 层 = document.createElement('div');
      层.className = '__b282_box';
      层.style.cssText = `position:fixed;left:${x - 3}px;top:${y - 3}px;width:${w + 6}px;height:${h + 6}px;border:3px solid #ff8c00;border-radius:4px;pointer-events:none;z-index:2147483647;`;
      document.body.appendChild(层);
      const cs = getComputedStyle(层);
      const r = 层.getBoundingClientRect();
      return {
        层数: document.querySelectorAll('.__b282_box').length,
        宽: Math.round(r.width), 高: Math.round(r.height),
        borderStyle: cs.borderTopStyle, borderColor: cs.borderTopColor, pointerEvents: cs.pointerEvents,
      };
    }, { x: 行.x, y: 行.y, w: 行.w, h: 行.h });
    if (!(检查.层数 === 1 && 检查.宽 > 0 && 检查.高 > 0)) throw new Error(`截图前置检查失败：${JSON.stringify(检查)}`);
    const 文件 = path.join(图目录, 拍图档.get(高));
    await p.screenshot({ path: 文件 });
    await p.evaluate(() => document.querySelectorAll('.__b282_box').forEach((e) => e.remove()));
    截图 = { 文件: path.relative(手册目录, 文件), 画框检查: 检查, 屏文 };
  }

  return { 几何, 命中, 屏文, 截图 };
};

for (const 高 of 高度组) {
  const p = await ctx.newPage();
  const 记 = { 高, 宽 };
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    Object.assign(记, await 量一档(p, 高, 拍图档.has(高)));
    记.判定 = 记.几何.行在视口内 ? 'P1b：行完整落在视口盒子里 ⇒ 看得见但点不到' : 'P1a：行被视口裁掉 ⇒ 看不见也点不到';
    log(`H=${高}｜视口 ${JSON.stringify(记.几何.视口)}`);
    log(`    行 ${JSON.stringify(记.几何.行)}｜交集高 ${记.几何.交集高}｜行在视口内 ${记.几何.行在视口内}｜命中 ${记.命中.tag}/${记.命中.testid} 在行内=${记.命中.在行内}`);
    log(`    ⇒ ${记.判定}`);
  } catch (e) { 记.错误 = e.message; log(`H=${高} 🔴 ${e.message}`); }
  finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    if (记.截图) out.图.push({ 高, ...记.截图 });
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

out.判定 = {
  视口盒: out.臂.map((a) => ({ 高: a.高, 视口: a.几何?.视口 ?? null, 行: a.几何?.行 ?? null, 行在视口内: a.几何?.行在视口内 ?? null, 命中在行内: a.命中?.在行内 ?? null })),
  结论: out.臂.every((a) => a.几何?.行在视口内)
    ? 'P1b ✅ 所有档位下行都完整落在视口盒子里 ⇒ 是「看得见但点不到」'
    : out.臂.some((a) => a.几何?.行在视口内 === false)
      ? 'P1a ✅ 部分档位下行被视口裁掉'
      : '🔴 无法判定',
};
log(`\n════ 判定 ════\n${out.判定.结论}`);
for (const a of out.臂) if (a.几何) log(`  H=${a.高}：视口 h=${a.几何.视口?.h} clientH=${a.几何.视口?.clientHeight} scrollH=${a.几何.视口?.scrollHeight} overflowY=${a.几何.视口?.overflowY}｜行 y=${a.几何.行.y}..${a.几何.行.底}｜交集高 ${a.几何.交集高}`);

// 末态独立复查（立规 140）
{
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: 1280, height: 720 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    out.收尾.节点数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    out.收尾.状态行 = await p.evaluate(() => (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null);
    out.收尾.通过 = out.收尾.节点数 === 76 && /0 selected/.test(out.收尾.状态行 || '');
    log(`\n末态独立复查：节点 ${out.收尾.节点数}｜${out.收尾.状态行} ⇒ ${out.收尾.通过 ? '✅' : '🔴'}`);
  } catch (e) { out.收尾.错误 = e.message; } finally { try { await p.close(); } catch (e) { /* 忽略 */ } }
}

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`\n写入 ${OUT}`);
process.exit(0);