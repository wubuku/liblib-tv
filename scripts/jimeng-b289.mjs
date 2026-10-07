/**
 * 批次 289：解一处未解冲突 —— 同一个节点、同一高度，两批读出的 `vs` 差 `37%`。
 *
 * 📌 **冲突（批次 287 vs 批次 288，如实记账，不选边）**：
 *   节点 `视频 1`（`320 × 569`）、`H = 720`：
 *     批次 287 在 `w = 1212` 读 `0.621424 / 0.625412 / 0.623708 / 0.622876`（四个不同 `z0`），
 *        ⚠️ **当时没有落定自检**；
 *     批次 288 在 `w = 900` 读 `0.984183`，✅ **有落定自检**（连读两次逐字相同）。
 *   批次 288 已把闭式对到 `7/7` 逐字：
 *     `vs = clamp(min(safeW/Wc, safeH/Hc), 0.08, 8)`，
 *     `safeW = max(100, w − 532)`、`safeH = H − 160`、`Wc/Hc` = 画布空间盒。
 *   代入 `w = 1212`：`min(680/320, 560/569) = min(2.125, 0.984183) = 0.984183`
 *   ⇒ 🔴 **闭式说 `0.984183`，批次 287 实测 `≈0.623`，差 `37%`**
 *   ⇒ **候选解释只有两个，必须分开**（立规 160）：
 *     (a) **`w = 1212` 上 `vs` 真的是 `≈0.623`** ⇒ 有个宽度相关的东西在 `900…1212` 之间改变了 `vs`；
 *     (b) **批次 287 那四臂读错了** ⇒ 成因在测量侧（落定、时序、别的）。
 *
 * 📌 **本批怎么分开**：
 *   🔴 **臂 A（判 (b)）**：在 `w = 1212` 上**带上落定自检**重测一遍。
 *      若读到 `0.984183` ⇒ **(b) 成立，批次 287 那四臂作废**；
 *      若读到 `≈0.623` **且两次逐字相同** ⇒ **(a) 成立**，且落定不是原因。
 *   🔴 **臂 B（给 (a) 定位）**：在 `900…1212` 之间扫宽度（`900/1000/1100/1212`）。
 *      按闭式这四档**都该是 `0.984183`**（宽项 `≥1.15` 恒大于高项）⇒
 *      📌 **哪一档先掉下去，翻转点就被夹在那两个宽度之间。**
 *   📌 **臂 C（重复性）**：`w = 1212` 跑**两遍**，读数必须逐字相同
 *      —— 若同臂内都不稳，那 (a)/(b) 的分法本身就要重写。
 *
 * 📌 **五条前提**：
 *   ① **轴向自检**：`innerW/innerH` 逐字等于设定值；
 *   ② 🔴 **落定自检**：点完连读两次（间隔 `2.5s`），**必须逐字相同**，否则标「未落定」并两次都记下来；
 *   ③ 🔴 **`z0 > vs` 硬门**：`z0` 必须高于预测 `vs`，否则读到的不是平台（沿用批次 288）；
 *   ④ 🔴 **点击生效自检**：`selectedNodeIds` 必须含目标节点；
 *   ⑤ 🔴 **参数写死**：闭式里的 `532 / 160 / 0.08 / 8 / 0.5` 全部取自代码或已发布结论。
 *
 * 📌 **纪律**：只按放大键、只点搜索结果行；不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**；
 *   末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b289.mjs      （落盘 /tmp/b289.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B289_OUT || '/tmp/b289.json';
const 高 = 720;
const 放大键 = 'Meta+Equal';
const 按够 = 13;
const 节点 = { 键: '视频', id: 'node_236ctpehgg', 备用名: ['视频 1', '视频'] };

// 🔴 前提⑤
const 屏上律 = (w) => Math.max(100, w - 532);
const 安全高 = 高 - 160;
const vf = (z) => Math.min(8, Math.max(0.08, z));
const 预测vs = (w, W, Hc) => +vf(Math.min(屏上律(w) / W, 安全高 / Hc)).toFixed(6);

// 臂 B 扫宽度；w=1212 跑两遍（臂 C 的重复性自检）
const 臂表 = [
  { w: 900, 遍: 1 }, { w: 1000, 遍: 1 }, { w: 1100, 遍: 1 },
  { w: 1212, 遍: 1 }, { w: 1212, 遍: 2 },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b289',
  问: '视频 1 在 w=1212 的 vs 到底是 0.623 还是 0.984183？翻转点在哪？',
  闭式: 'vs = clamp(min(max(100,w−532)/Wc, (H−160)/Hc), 0.08, 8)',
  臂: [], 判定: {},
};

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 读 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return {
    scale: m ? Number(m[1]) : null,
    百分比: z ? z.textContent.trim() : null,
    选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.dataset.id),
  };
});

for (const { w, 遍 } of 臂表) {
  const p = await ctx.newPage();
  const 记 = { w, 遍, h: 高, 节点: 节点.id, 按了几次: 按够 };
  try {
    await p.setViewportSize({ width: w, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
    if (实际.w !== w || 实际.h !== 高) throw new Error(`轴向自检失败：要 ${w}×${高}，实测 ${实际.w}×${实际.h}`);

    const 节 = await p.evaluate((nid) => {
      const e = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      return e ? { W: e.offsetWidth, Hc: e.offsetHeight } : null;
    }, 节点.id);
    if (!节) throw new Error('目标节点不在画布上');
    记.节点尺寸 = 节;
    记.预测vs = 预测vs(w, 节.W, 节.Hc);

    for (let i = 0; i < 按够; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
    await p.waitForTimeout(1200);
    const z0 = await 读(p);
    记.z0 = z0.scale; 记.z0_百分比 = z0.百分比;
    if (z0.scale === null) throw new Error('读不到缩放');
    if (!(z0.scale > 记.预测vs)) throw new Error(`z0(${z0.scale}) 不高于预测 vs(${记.预测vs}) ⇒ 读不到平台`);

    const 钮 = await p.evaluate(() => {
      const b = document.querySelector('button[aria-label="搜索"]');
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return { 中心: [r.x + r.width / 2, r.y + r.height / 2], 可见: r.width > 0 && r.height > 0 && r.y >= 0 && r.bottom <= innerHeight };
    });
    if (!钮 || !钮.可见) throw new Error('找不到可见的搜索钮');
    await p.mouse.click(钮.中心[0], 钮.中心[1]);
    await p.waitForTimeout(1600);

    let 行 = null, 用名 = null;
    for (const 名 of 节点.备用名) {
      await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
      await p.keyboard.type(名, { delay: 80 });
      await p.waitForTimeout(2000);
      const r = await p.evaluate((nid) => {
        const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid.replace(/^node_/, '')}"]`);
        if (!e) return null;
        const b = e.getBoundingClientRect();
        return { 中心: [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)], 可见: b.width > 0 && b.height > 0 && b.y >= 0 && b.bottom <= innerHeight && b.x >= 0 && b.right <= innerWidth };
      }, 节点.id);
      if (r && r.可见) { 行 = r; 用名 = 名; break; }
    }
    if (!行) throw new Error('搜不到可见的结果行');
    记.用名 = 用名;
    await p.mouse.click(行.中心[0], 行.中心[1]);
    await p.waitForTimeout(3000);
    const a1 = await 读(p);
    await p.waitForTimeout(2500);
    const a2 = await 读(p);
    记.z后1 = a1.scale; 记.z后2 = a2.scale;
    记.落定 = a1.scale === a2.scale;
    记.选中 = a2.选中;
    记.点击生效 = a2.选中.includes(节点.id);
    if (!记.点击生效) throw new Error(`点击未生效（选中=${JSON.stringify(a2.选中)}）`);
    记.vs实测 = a2.scale;
    记.误差 = +(a2.scale - 记.预测vs).toFixed(6);
    记.符合闭式 = Math.abs(记.误差) <= 1e-3;
    log(`w=${String(w).padEnd(5)} 第${遍}遍｜z0=${z0.scale}｜vs实测=${a2.scale}｜闭式=${记.预测vs}｜${记.符合闭式 ? '✅符合' : '🔴不符'}｜落定 ${记.落定 ? '✅' : `🔴 ${a1.scale} vs ${a2.scale}`}`);
  } catch (e) {
    记.错误 = e.message; log(`w=${String(w).padEnd(5)} 第${遍}遍 🔴 ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.vs实测 !== undefined);
const 未落定 = 好.filter((x) => !x.落定);
const 符合 = 好.filter((x) => x.符合闭式);
log('\n════ 汇总 ════');
log(`有效臂 ${好.length}｜其中未落定 ${未落定.length}｜符合闭式 ${符合.length}`);
for (const x of 好.sort((a, c) => a.w - c.w || a.遍 - c.遍)) {
  log(`  w=${String(x.w).padEnd(5)}#${x.遍}  vs=${String(x.vs实测).padEnd(10)} 闭式=${x.预测vs}`);
}
const 重复 = 好.filter((x) => x.w === 1212);
const 重复一致 = 重复.length === 2 && 重复[0].vs实测 === 重复[1].vs实测;

if (!好.length) {
  out.判定 = { 结论: '🔴 一条有效臂都没有 ⇒ 整组作废，不出判定' };
} else if (未落定.length) {
  out.判定 = { 结论: `🔴 有 ${未落定.length} 臂未落定（连读两次不同）⇒ 平台读数不可信，整组作废`, 明细: 未落定.map((x) => `w=${x.w}#${x.遍}: ${x.z后1} vs ${x.z后2}`) };
} else {
  const 不符 = 好.filter((x) => !x.符合闭式);
  out.判定 = {
    有效臂: `${好.length}/${out.臂.length}`,
    臂C_重复性: 重复一致 ? `✅ w=1212 两遍读数逐字相同（${重复[0].vs实测}）` : `🔴 w=1212 两遍不同：${重复.map((x) => x.vs实测).join(' / ')}`,
    符合闭式: `${符合.length}/${好.length}`,
    不符合的档: 不符.map((x) => `w=${x.w}#${x.遍} 实测 ${x.vs实测} vs 闭式 ${x.预测vs}`),
    结论: 符合.length === 好.length
      ? `✅ **全部 ${好.length} 臂符合闭式（0.984183）** ⇒ **候选 (b) 成立：批次 287 在 w=1212 的那四臂读错了**，其成因（无落定自检 / 时序）**仍未测**，但结论作废；w=900…1212 之间**没有翻转点**`
      : `⚠️ **有 ${不符.length} 臂不符合闭式** ⇒ **候选 (a) 成立：vs 确实随 w 在这一段变了**；翻转点被夹在上面的相邻两档之间；**其成因仍未测，不编**（立规 113）`,
  };
}
log('\n════ 判定 ════\n' + JSON.stringify(out.判定, null, 1));

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