/**
 * 批次 291：把比较集**放开到全部元素**，找「宽度不是 `w` 的线性函数」的那个元素。
 *
 * 📌 起意（批次 290 亲手指出的盲区）：
 *   批次 290 只 diff 了带 `data-testid` 的元素，得到 `1100…1300` 之间
 *   **表面线性、节点盒不变、零元素增删** 的干净负面结果。
 *   🔴 **但一个「没有 testid 的面板」若在断点处出现或变宽，那批差分根本看不见它。**
 *   📌 **立规 166 的同型陷阱的另一面：固定比较集让差分可靠，但也把集外的东西一并屏蔽了
 *   ⇒「在集内没找到」永远不等于「不存在」（立规 160）。**
 *
 * 📌 **本批的判据换了 —— 这是关键**：
 *   批次 290 问的是「它**变没变**」；本批问的是「它的宽度**是不是 `w` 的线性函数**」。
 *   🔴 **后者不需要事先规定比较集长什么样**，它对**每一个**元素都成立
 *   ⇒ 📌 **这正好绕开「集内/集外」那个盲区。**
 *
 * 📌 **判定口径（写死）**：
 *   对相邻两档 `a → c`（`Δ = c − a`），每个元素按 `Δrect.w` 归类：
 *     · **跟随** `Δrect.w == Δ`（差 `≤0.5px`，含亚像素抖动）
 *     · **固定** `|Δrect.w| ≤ 0.5`
 *     · 🔴 **其余一律「不规则」** —— 📌 **不规则就是线索**
 *   另报：在**该对两档都在场**的元素里，**只在这一对里出现或消失**的那些。
 *
 * 📌 **三条前提**：
 *   ① **轴向自检**：`innerW/innerH` 逐字等于设定值；
 *   ② 🔴 **元素键必须稳定**：用 `标签|data-testid|类名前 40|同键兄弟中的序号` 作键，
 *      否则「增删」会被索引漂移伪装成「大量元素变了」（立规 166 的同型坑）；
 *   ③ 📌 **只看相邻两档**，不跨档比较（避免差异累加）。
 *
 * 📌 **纪律**：**纯只读，一个东西都不点**；不新建/不删除/不上传/不分享/不进扣费页/绝不点生成；
 *   末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b291.mjs      （落盘 /tmp/b291.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B291_OUT || '/tmp/b291.json';
const 高 = 720;
const 宽度组 = [1100, 1150, 1200, 1210, 1212, 1300];
const 容差 = 0.5;                       // 亚像素抖动容差（写死）

const log = (...a) => console.log(a.join(' '));
const out = { 轮次: 'b291', 问: '哪一个元素的宽度不是 w 的线性函数？', 宽度组, 容差, 臂: [], 差分: [], 判定: {} };

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

// 前提②：稳定键
const 读 = (p) => p.evaluate(() => {
  const 表 = {};
  const 同键计数 = new Map();
  const walk = (el, 父键) => {
    const kids = Array.from(el.children);
    const 局部 = new Map();
    for (const k of kids) {
      const t = (k.tagName || '').toLowerCase();
      const tid = k.getAttribute && k.getAttribute('data-testid');
      const cls = ((k.getAttribute && k.getAttribute('class')) || '').slice(0, 40);
      const 基 = `${t}|${tid || ''}|${cls}`;
      const i = (局部.get(基) || 0); 局部.set(基, i + 1);
      const 键 = 父键 + '>' + 基 + '#' + i;
      同键计数.set(键, (同键计数.get(键) || 0) + 1);
      const r = k.getBoundingClientRect();
      表[键] = [+(r.width).toFixed(2), +(r.height).toFixed(2), +(r.x).toFixed(2), +(r.right).toFixed(2)];
      walk(k, 键);
    }
  };
  walk(document.body, 'body');
  const dup = Array.from(同键计数.values()).filter((n) => n > 1).length;
  return { 表, 元素数: Object.keys(表).length, 键冲突: dup };
});

for (const w of 宽度组) {
  const p = await ctx.newPage();
  const 记 = { w, h: 高 };
  try {
    await p.setViewportSize({ width: w, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(7000);
    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== w || 实际.h !== 高) throw new Error(`轴向自检失败：要 ${w}×${高}，实测 ${实际.w}×${实际.h}`);
    const r = await 读(p);
    记.元素数 = r.元素数;
    记.键冲突 = r.键冲突;
    记.表 = r.表;
    log(`${String(w).padStart(4)}×${高}｜元素 ${r.元素数} 个｜键冲突 ${r.键冲突}`);
  } catch (e) {
    记.错误 = e.message; log(`${String(w).padStart(4)} 🔴 ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

const 好 = out.臂.filter((x) => !x.错误 && x.表);
log(`\n════ 元素总数 ════\n${好.map((x) => `${x.w}:${x.元素数}`).join('  ')}`);

for (let i = 1; i < 好.length; i++) {
  const a = 好[i - 1], c = 好[i];
  const Δ = c.w - a.w;
  const 键集 = Object.keys(a.表);
  const 共同 = 键集.filter((k) => k in c.表);
  const 新增 = Object.keys(c.表).filter((k) => !(k in a.表));
  const 消失 = 键集.filter((k) => !(k in c.表));
  const 跟随 = [], 固定 = [], 不规则 = [];
  for (const k of 共同) {
    const d = c.表[k][0] - a.表[k][0];
    if (Math.abs(d - Δ) <= 容差) 跟随.push(k);
    else if (Math.abs(d) <= 容差) 固定.push(k);
    else 不规则.push({ 键: k, 从: a.表[k][0], 到: c.表[k][0], Δ宽: +d.toFixed(2), 期望: Δ });
  }
  out.差分.push({ 从: a.w, 到: c.w, Δ, 共同数: 共同.length, 跟随: 跟随.length, 固定: 固定.length, 不规则数: 不规则.length, 不规则: 不规则.slice(0, 40), 新增数: 新增.length, 新增: 新增.slice(0, 20), 消失数: 消失.length, 消失: 消失.slice(0, 20) });
  log(`\n  ${a.w} → ${c.w}（Δ=${Δ}）｜共同 ${共同.length}｜跟随 ${跟随.length}｜固定 ${固定.length}｜🔴 不规则 ${不规则.length}｜新增 ${新增.length}｜消失 ${消失.length}`);
  for (const r of 不规则.slice(0, 12)) log(`      不规则: ${r.键}\n          宽 ${r.从} → ${r.到}（Δ${r.Δ宽}，期望 ${r.期望}）`);
  for (const k of 新增.slice(0, 8)) log(`      新增: ${k}  宽 ${c.表[k][0]}`);
  for (const k of 消失.slice(0, 8)) log(`      消失: ${k}  宽 ${a.表[k][0]}`);
}

const 全不规则 = out.差分.filter((d) => d.不规则数 > 0);
const 全增删 = out.差分.filter((d) => d.新增数 > 0 || d.消失数 > 0);
log('\n════ 判定 ════');
if (!好.length) {
  out.判定 = { 结论: '🔴 一条有效臂都没有 ⇒ 整组作废' };
} else if (全不规则.length) {
  out.判定 = {
    有效臂: `${好.length}/${out.臂.length}`,
    有不规则元素的相邻档: 全不规则.map((d) => `${d.从}→${d.到}（${d.不规则数} 个）`).join('; '),
    有增删的相邻档: 全增删.length ? 全增删.map((d) => `${d.从}→${d.到} +${d.新增数}/-${d.消失数}`).join('; ') : '✅ 零',
    结论: `✅ 找到了：宽度**不是 w 的线性函数**的元素出现在 ${全不规则.map((d) => `${d.从}→${d.到}`).join('、')} —— 📌 **这就是 safeW 那条不连续性藏身的地方**`,
  };
} else {
  out.判定 = {
    有效臂: `${好.length}/${out.臂.length}`,
    增删: 全增删.length ? `⚠️ ${全增删.map((d) => `${d.从}→${d.到} +${d.新增数}/-${d.消失数}`).join('; ')}` : '✅ 零',
    结论: `🔴 **全屏每个元素的宽度都是 w 的线性函数**（跟随 ${out.差分[0]?.跟随} 个/档，固定 ${out.差分[0]?.固定} 个/档，不规则 **0**）⇒ 📌 **DOM 布局层到此为止，safeW 那条不连续性不在渲染出来的盒上**；成因仍未测，不编（立规 113）`,
  };
}
log(JSON.stringify(out.判定, null, 1));

const pz = await ctx.newPage();
try {
  await pz.setViewportSize({ width: 1280, height: 720 });
  await pz.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await pz.waitForSelector('.react-flow__node', { timeout: 45000 });
  await pz.waitForTimeout(6000);
  out.末态 = await pz.evaluate(() => ({
    节点数: document.querySelectorAll('.react-flow__node').length,
    状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
  }));
} finally { try { await pz.close(); } catch (e) { /* 忽略 */ } }
log(`\n末态独立复查：${JSON.stringify(out.末态)}`);

fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log(`写入 ${OUT}`);
process.exit(0);