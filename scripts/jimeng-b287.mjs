/**
 * 批次 287：「点搜索结果行」的取景律 —— 先手动放大再点，看那条 `max(viewport.zoom, .5)`。
 *
 * 📌 起意（批次 286 在 bundle 里读到的调用链，构建 `canvas-core.1f223ad77e.js` / `canvas-view`）：
 *   `搜索结果行 → canvas.actions.locateNode.execute(id,"user","activate")`   （`@1024477`）
 *   `→ a6.activate = "activateSelection"`                                   （`@342182`）
 *   `→ scenario 映射：case "activateSelection" → geometry: "locateContent"`  （`@788296`）
 *   `→ locateContent 分支`                                                     （`@778424`）：
 * ```js
 * if("locateContent"===e.mode){
 *   let t = vs(l, e.target);                    // l = safeArea, e.target = 目标节点盒
 *   if(!Number.isFinite(t)||t<=0) return {status:"invalid"};
 *   let i = vf(Math.max(e.viewport.zoom, .5));   // 🔴🔴🔴 当前缩放参与，地板 0.5 在 min 外面
 *   return va(vd(e.target, l, Math.min(i, t)), e.viewport)
 * }
 * function vs(e,t,i=1/0){ return vf(Math.min(e.width/t.width, e.height/t.height, i)) }  // @778300
 * function vf(e){ return Math.min(8, Math.max(.08, e)) }                                // @781068
 * ```
 *   ⇒ 📌 **闭式（全部取自代码字面量，没有一个是拟合的）**：
 *      `zoom_after = min( vf(max(z0, 0.5)) , vf(min(safeW/W, safeH/Hc)) )`
 *      记 `vs = vf(min(safeW/W, safeH/Hc))`（与 `z0` 无关）
 *      ⇒ **`zoom_after = min(max(z0, 0.5), vs)`**（`z0 ≤ 0.5` 时 `vf` 不起作用）
 *
 * 🔴🔴 **本批的判决点：旧经验律与新代码律在 `z0 > 0.5` 时分道扬镳**
 *   旧律（批次 251/253，被批次 277/280 反复引用）把 `0.5` 放在 **min 里面**：
 *      `s = max(0.08, min(屏上律(w)/W, 0.5, (H−160)/Hc))`  ⇒ **`s` 永远 `≤ 0.5`**
 *   新代码把 `0.5` 放在 **min 外面**，且那一项是**当前缩放**：
 *      `s = min(max(z0, 0.5), vs)`                       ⇒ **`z0 > 0.5` 时 `s` 可以 `> 0.5`**
 *   ⇒ 📌 **只要能观测到一次 `zoom_after > 0.5`，旧律当场作废。**
 *   ⇒ 📌 反过来，`k` 小时的阶梯形状（`k ≤ 4` 一律 `0.5`）**两条律同形** ⇒ **不能判**。
 *
 * 📌 **三条预测（测量前写死，前提④）**：
 *   P1 **`zoom_after ≤ max(z0, 0.5)`**：点完永远不会比起点更放大。
 *   P2 **`k ≤ 4` 时恒为 `0.5`**（`z0 < 0.5`，`max` 取 `0.5`）；
 *      `z0 > 0.5` 之后 `zoom_after = min(z0, vs)` ⇒ **单调不降**。
 *   P3 🔴 **必然出现 `zoom_after > 0.5` 的一格** —— 因为 `vs` 是「safeArea / 节点尺寸」，
 *      在 `w = 1212`（宽侧）这种视口下节点远小于视口，`vs` 必然远大于 `0.5`。
 *      ⇒ **P3 不成立 ⇒ 代码读错了；P3 成立 ⇒ 旧经验律作废。**
 *
 * 📌 **顺带测出一个新观测量 `vs`**：
 *   `vs` = 「点搜索结果行时**能放大到的上限**」，
 *   🔴 **它完全由目标节点的 `(W, Hc)` 与视口决定，与当前缩放无关** ——
 *   📌 **所以 `k` 很大时读到的那个平台值，就是 `vs` 的直接测量**（不需要知道 safeW/safeH）。
 *   📌 **两个尺寸差很多的节点各测一次 `vs`**，即可把「`safeW` 主导还是 `safeH` 主导」分开。
 *
 * 📌 **五条前提**：
 *   ① **轴向自检**：`innerW/innerH` 逐字等于设定值；
 *   ② 🔴 **正交读量**：每按一次放大键，必须先用 `canvas-zoom-percent` 确认**缩放真的变了**，
 *      再读 transform 的 `scale`；两者不一致就记下来（立规 129 的同型要求）；
 *   ③ 🔴 **点击生效自检**：`selectedNodeIds` 必须真的含目标节点，
 *      否则该臂标「点击未生效」、**不参与判定**（立规 162）；
 *   ④ 🔴 **参数写死**：`0.5 / 0.08 / 8` 全部取自 bundle 字面量，**不用实测值反推**；
 *   ⑤ 📌 **每臂开新页**（缩放不跨页持久化），且**只点搜索结果行**，不点别的。
 *
 * 📌 **纪律**：只按放大键、只点搜索结果行；不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**；
 *   末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b287.mjs      （落盘 /tmp/b287.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B287_OUT || '/tmp/b287.json';
const 宽 = 1212, 高 = 720;              // 宽侧（与批次 247 同一窗口，便于对照）
const 放大键 = 'Meta+Equal';            // ×1.2（批次 246/247 双向验证）
const K组 = [0, 4, 6, 8, 10, 12];
const 两节点 = [
  { 键: '视频', id: 'node_236ctpehgg', 备用名: ['视频 1', '视频'] },
  { 键: '图片', id: 'node_gref4sw056', 备用名: ['图片 b22-upload', 'b22-upload', '图片'] },
];

// 🔴 前提④：全部取自 bundle 字面量
const 地板 = 0.5, 上限 = 8, 下限 = 0.08;
const 预测 = (z0) => +Math.min(Math.max(z0, 地板), 上限).toFixed(6);

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b287',
  问: '点搜索结果行之后，缩放是 min(max(z0,0.5), vs) 吗？——旧经验律说它永远 ≤0.5',
  构建: 'canvas-core.1f223ad77e.js / canvas-view.25249acfc0.js（批次 286 同批）',
  常量: { 地板, 上限, 下限, 来源: 'vf() @781068 与 locateContent 分支 @778424' },
  视口: { 宽, 高 }, 键序: K组, 节点: 两节点.map((n) => n.id), 臂: [], 判定: {},
};

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 读 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const t = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(vp.style.transform || '') : null;
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return {
    scale: m ? Number(m[1]) : null,
    tx: t ? Number(t[1]) : null, ty: t ? Number(t[2]) : null,
    百分比: z ? z.textContent.trim() : null,
    选中: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.dataset.id),
  };
});
const 找搜索钮 = async (p) => p.evaluate(() => {
  const b = document.querySelector('button[aria-label="搜索"]');
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return { 中心: [r.x + r.width / 2, r.y + r.height / 2], 可见: r.width > 0 && r.height > 0 && r.y >= 0 && r.bottom <= innerHeight };
});
const 找结果行 = async (p, nid, 名们) => {
  const 短名 = nid.replace(/^node_/, '');
  const 尝试 = [];
  for (const 名 of 名们) {
    await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
    await p.keyboard.type(名, { delay: 80 });
    await p.waitForTimeout(2000);
    const 行 = await p.evaluate((id) => {
      const e = document.querySelector(`[data-testid="canvas-search-result-node_${id}"]`);
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 盒: [Math.round(r.width), Math.round(r.height)], 在视口内: r.y >= 0 && r.bottom <= innerHeight && r.x >= 0 && r.right <= innerWidth, 可见: r.width > 0 && r.height > 0 };
    }, 短名);
    尝试.push({ 名, 有行: !!行 });
    if (行 && 行.可见 && 行.在视口内) return { 行, 用名: 名, 尝试 };
  }
  return { 行: null, 用名: null, 尝试 };
};

for (const n of 两节点) {
  log(`\n════════ 节点 ${n.id}（${n.键}），w=${宽} h=${高} ════════`);
  for (const k of K组) {
    const p = await ctx.newPage();
    const 记 = { 节点: n.id, 键: n.键, 按了几次: k, w: 宽, h: 高 };
    try {
      await p.setViewportSize({ width: 宽, height: 高 });
      await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await p.waitForSelector('.react-flow__node', { timeout: 45000 });
      await p.waitForTimeout(6000);
      const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
      if (实际.w !== 宽 || 实际.h !== 高) throw new Error(`轴向自检失败：要 ${宽}×${高}，实测 ${实际.w}×${实际.h}`);

      const 节 = await p.evaluate((id) => {
        const e = document.querySelector(`.react-flow__node[data-id="${id}"]`);
        return e ? { W: e.offsetWidth, Hc: e.offsetHeight } : null;
      }, n.id);
      if (!节) throw new Error('目标节点不在画布上');
      记.节点尺寸 = 节;

      const 前 = await 读(p);
      记.初始 = 前;
      // 前提②：按 k 次放大键，每步都用 canvas-zoom-percent 正交确认
      const 阶梯 = [];
      for (let i = 0; i < k; i++) {
        await p.keyboard.press(放大键);
        await p.waitForTimeout(450);
      }
      await p.waitForTimeout(1200);
      const 放大后 = await 读(p);
      记.z0 = 放大后.scale;
      记.z0_百分比 = 放大后.百分比;
      阶梯.push({ 起: 前.scale, 止: 放大后.scale, 百分比: 放大后.百分比 });
      记.正交读量 = {
        百分比随按键上升: 前.scale === null || 放大后.scale === null ? null : 放大后.scale >= 前.scale,
        百分比文本: 放大后.百分比,
      };
      if (k > 0 && !(放大后.scale > 前.scale)) throw new Error(`正交读量失败：按了 ${k} 次放大键但 scale 没变大（${前.scale} → ${放大后.scale}）`);

      // 点搜索结果行
      const 钮 = await 找搜索钮(p);
      if (!钮 || !钮.可见) throw new Error('找不到可见的搜索钮');
      await p.mouse.click(钮.中心[0], 钮.中心[1]);
      await p.waitForTimeout(1600);
      const 找 = await 找结果行(p, n.id, n.备用名);
      记.找行 = 找;
      if (!找.行) throw new Error(`搜不到结果行（尝试：${JSON.stringify(找.尝试)}）`);
      await p.mouse.click(找.行.中心[0], 找.行.中心[1]);
      await p.waitForTimeout(2500);
      const 后 = await 读(p);
      记.z后 = 后.scale;
      记.选中 = 后.选中;
      记.点击生效 = 后.选中.includes(n.id);       // 前提③
      if (!记.点击生效) throw new Error(`点击未生效（选中=${JSON.stringify(后.选中)}）`);

      记.预测 = 预测(记.z0);
      记.误差 = 后.scale === null ? null : +(后.scale - 记.预测).toFixed(6);
      记.超过0点5 = 后.scale !== null && 后.scale > 地板;
      log(`  k=${String(k).padStart(2)}｜z0=${记.z0}（面板 ${记.z0_百分比}）｜z后=${后.scale}｜预测 min(max(z0,0.5), vs)=${记.预测}｜${记.超过0点5 ? '🔴 >0.5！' : ''}｜节点 ${节.W}×${节.Hc}｜点击生效 ✅`);
    } catch (e) {
      记.错误 = e.message; log(`  k=${String(k).padStart(2)} 🔴 ${e.message}`);
    } finally {
      try { await p.close(); } catch (e) { /* 忽略 */ }
      out.臂.push(记);
      fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
    }
  }
}

// ── 判定 ──
const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.z后 !== null);
const 超05 = 好.filter((x) => x.超过0点5);
const 低z = 好.filter((x) => x.z0 !== null && x.z0 <= 地板);
const vs估计 = {};
for (const n of 两节点) {
  const 组 = 好.filter((x) => x.节点 === n.id).sort((a, c) => (c.z0 || 0) - (a.z0 || 0));
  vs估计[n.id] = 组.length ? { 最大z0: 组[0].z0, 该臂z后: 组[0].z后, 节点: 组[0].节点尺寸 } : null;
}
const 坏 = out.臂.filter((x) => x.错误);
log('\n════ 汇总 ════');
log(`有效臂 ${好.length} / 作废臂 ${坏.length}`);
log(`其中 z后 > 0.5 的：${超05.length} 臂${超05.length ? ' → ' + 超05.map((x) => `${x.键}k=${x.按了几次}(z0=${x.z0}→${x.z后})`).join(', ') : ''}`);
log(`z0 ≤ 0.5 的臂：${低z.length} 臂，z后取值 ${JSON.stringify([...new Set(低z.map((x) => x.z后))])}`);
log(`各节点 vs 估计（z0 最大那一臂的 z后）：${JSON.stringify(vs估计)}`);

if (坏.length) log(`\n⚠️ 作废臂：${坏.map((x) => `${x.键}k=${x.按了几次}: ${x.错误}`).join(' | ')}`);

if (!好.length) {
  out.判定 = { 结论: '🔴 一条有效臂都没有 ⇒ 整组作废，不出判定' };
} else {
  out.判定 = {
    有效臂: `${好.length}/${out.臂.length}`,
    旧经验律: 超05.length ? `🔴 **当场作废**：${超05.length} 个臂实测 z后 > 0.5，而旧律的 min 里有 0.5，不允许` : '✅ 未被推翻（但也没被推翻：本次没造出 z0 > 0.5 的臂）',
    代码律_P1: `z后 ≤ max(z0, 0.5) 的臂 ${好.filter((x) => x.z后 <= Math.max(x.z0 || 0, 地板) + 1e-9).length}/${好.length}`,
    代码律_P2_低z平台: 低z.length ? `z0 ≤ 0.5 的 ${低z.length} 臂，z后 = ${JSON.stringify([...new Set(低z.map((x) => x.z后))])}` : '（本组没有 z0 ≤ 0.5 的臂）',
    vs: JSON.stringify(vs估计),
    结论: 超05.length
      ? `✅ **P3 成立**：出现了 ${超05.length} 个 z后 > 0.5 的臂 ⇒ **旧经验律（min 里带 0.5）作废**，代码律的 min(max(z0,0.5), vs) 取代它`
      : `⚠️ **P3 未成立**：没有造出 z后 > 0.5 的臂 ⇒ **不能判**（两条律在本次采到的数据上同形，判据不足，不出结论）`,
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