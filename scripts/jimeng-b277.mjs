/**
 * 批次 277：接住批次 276 甩出来的两条线索，各追到底。
 *
 * 📌 线索一（**把 3px 对照档拆成单步**）：
 *   276 的 `1px(373→374)` 档：整数维度变化 `104` 处、直方图 `{"1":104}`（**全 +1、恰 2 的 0 处**）。
 *   276 的 `3px(372→375)` **对照**档：整数维度变化 `109` 处、直方图 `{"2":5,"3":104}`
 *   ⇒ 🔴 **对照差里测到了 `5` 处恰 `+2`**。
 *   📌 这一条同时干了两件事（立规 153）：
 *     ① **量纲够得着 `+2`**（它在对照差里被测到了）⇒ `1px` 档的 `0` 处是**真负结论**，不是「方法够不着」；
 *     ② **那 `5` 处 `+2` 里有东西**，只是 `3px` 这一档把它**混在 `3` 里面**了。
 *   🔴 **但我还没测：它落在哪一步** —— `372→373` / `373→374` / `374→375` 三步都能凑出 `+3`，
 *     只有真的拆开才知道。⇒ **本批 Part 1：扫 `371…377`，逐步 diff。**
 *
 * 📌 线索二（**点搜索结果行到底动不动相机**）：
 *   276 的四个相位里相机 `scale/tx/ty` **逐字相同**，包括「动作前」。
 *   🔴 两种读法分得开吗？分不开：
 *     H-a 「取景」是**空操作**（点谁都不动）⇒ 批次 253–275 那些「取景落点」
 *          读到的其实是**页面加载时的恢复位姿**，不是点搜索结果读到的；
 *     H-b 「取景」**有效**，只是 276 每次都点**同一个节点**（`音频 68`）⇒ 幂等，相机不动是当然的。
 *   ⇒ **只点同一个节点永远分不开**（立规 117 精神：要在能分辨的那一刀上测）。
 *   ⇒ **本批 Part 2：点三个**不同**节点**（`视频 1` / `图片 b22-upload` / `音频 68`，
 *     三者画布宽 `W` 与位置都不同）⇒ 相机动不动、动了的话新 `scale` 是不是**那个节点自己的**律。
 *
 * 📌 **预测先写死**（立规 129/130，不允许看到实测再改）：
 *   Q1a `+2` 落在 `373→374` ⇒ 它就是取景台阶本身；
 *   Q1b 落在 `372→373` 或 `374→375` ⇒ 与 `374` 无关，是**别的**机制（先排除掉再谈取景）。
 *   Q2a 三个节点点下来相机 `scale/tx/ty` 全同 ⇒ H-a，空操作；
 *   Q2b 相机随所点节点改变，且新 `scale` 逐字等于**该节点**的 `s = 屏上律(w)/W` ⇒ H-b，手册的律成立；
 *   Q2c 相机随所点节点改变，但 `scale` 仍是**上一个节点**的 ⇒ 律是全局的、与点谁无关。
 *
 * 📌 **Part 2 的两条前提**（不满足就整组作废，写明原因，不硬跑）：
 *   ① **轴向自检**：`innerW/innerH` 须逐字等于设定值；
 *   ② **DOM 读出的节点宽是不是那个 `W`**：`音频 68` 必须逐字读出 `320`，
 *      否则「用 `offsetWidth` 当 `W`」这个前提不成立，Part 2 的预测算不出来。
 *
 * 📌 **三条纪律**：只读（不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**）；
 *   每臂开新页；末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b277.mjs      （落盘 /tmp/b277.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B277_OUT || '/tmp/b277.json';
const 高 = 244;
const 扫描宽 = [371, 372, 373, 374, 375, 376, 377];      // Part 1：逐步 diff
const Part2臂 = [[460, 720], [560, 720]];                  // Part 2：点不同节点
const 三节点 = [
  { id: 'node_236ctpehgg', 名: '视频 1' },
  { id: 'node_gref4sw056', 名: '图片 b22-upload' },
  { id: 'node_tadm1nyykc', 名: '音频 68' },
];
const 帧数 = 3, 帧间隔 = 400;

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b277',
  问: '① 3px 对照档里那 5 处 +2 落在哪一步？② 点不同节点，相机动不动？',
  预测: {
    Q1a: '+2 落在 373→374 ⇒ 它就是取景台阶',
    Q1b: '落在别的步 ⇒ 与 374 无关，是别的机制',
    Q2a: '三个节点点下来相机全同 ⇒ 取景是空操作',
    Q2b: '相机随节点变且新 scale = 该节点自己的律 ⇒ 手册的律成立',
    Q2c: '相机随节点变但 scale 仍是上一个节点的 ⇒ 律是全局的',
  },
  扫描宽, 高, Part2臂, 三节点, Part1: {}, Part2: [], 收尾: {},
};

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

// ══════════ Part 1：整棵 DOM 的整数外框快照 ══════════
const 整数量 = ['offsetWidth', 'clientWidth', 'offsetHeight', 'clientHeight', 'scrollWidth', 'scrollHeight', 'offsetLeft', 'offsetTop'];

const 取一帧 = (p) => p.evaluate((attrs) => {
  const 路径 = (el) => {
    const parts = [];
    let e = el;
    while (e && e.nodeType === 1) {
      const par = e.parentElement;
      let i2 = 1;
      if (par) i2 = Array.from(par.children).filter((c) => c.nodeType === 1 && c.tagName === e.tagName).indexOf(e) + 1;
      parts.unshift(`${e.tagName}:${i2}`);
      e = par;
    }
    return parts.join('>');
  };
  const o = { _相机: null, _节点宽: {} };
  document.querySelectorAll('*').forEach((el) => {
    o[路径(el)] = attrs.map((a) => el[a]).join(',');
  });
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const t = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(vp.style.transform || '') : null;
  o._相机 = { scale: m ? Number(m[1]) : null, tx: t ? Number(t[1]) : null, ty: t ? Number(t[2]) : null };
  return o;
}, 整数量);

const 融帧 = (帧) => {
  const 稳定 = {};
  let 不稳定 = 0;
  const 键集 = Object.keys(帧[0]).filter((k) => !k.startsWith('_'));
  for (const k of 键集) {
    const v0 = 帧[0][k];
    if (帧.every((f) => f[k] === v0)) 稳定[k] = v0; else 不稳定++;
  }
  const 相机 = 帧[0]._相机;
  const 相机稳定 = 帧.every((f) => JSON.stringify(f._相机) === JSON.stringify(相机));
  // 前提检查：整数量纲必须真的被量到（批次 276 v1 死在这里）
  let 样本 = 0, 非空 = 0;
  for (const k of Object.keys(稳定)) {
    if (样本++ >= 200) break;
    const a = 稳定[k].split(',');
    if (a.length === 整数量.length && 整数量.some((_, i) => a[i] !== '')) 非空++;
  }
  return { 稳定, 元素总数: 键集.length, 稳定数: Object.keys(稳定).length, 不稳定元素数: 不稳定, 相机: 相机稳定 ? 相机 : null, 前提检查: { 取样元素数: 样本, 整数量非空元素数: 非空, 整数量可用: 样本 > 0 && 非空 / 样本 > 0.9 } };
};

log(`\n════════ Part 1：扫宽 ${扫描宽.join(' / ')}，高度 ${高} ════════`);
for (const 宽 of 扫描宽) {
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: window.innerWidth, h: window.innerHeight }));
    if (实际.w !== 宽 || 实际.h !== 高) throw new Error(`轴向自检失败：要 ${宽}×${高}，实测 ${实际.w}×${实际.h}`);
    const 帧 = [];
    for (let i = 0; i < 帧数; i++) { 帧.push(await 取一帧(p)); await p.waitForTimeout(帧间隔); }
    const 融 = 融帧(帧);
    if (!融.前提检查.整数量可用) throw new Error(`前提检查失败：整数量可用率 ${融.前提检查.整数量非空元素数}/${融.前提检查.取样元素数}`);
    out.Part1[宽] = 融;
    log(`  w=${宽}｜innerW=${实际.w}｜元素 ${融.元素总数}｜稳定 ${融.稳定数}｜不稳定 ${融.不稳定元素数}｜scale ${融.相机?.scale}｜整数量可用 ✅`);
  } catch (e) {
    out.Part1[宽] = { 错误: e.message };
    log(`  w=${宽} 🔴 ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

const 步diff = (a, c) => {
  const A = out.Part1[a]?.稳定, B = out.Part1[c]?.稳定;
  if (!A || !B) return { 错误: `缺快照 ${a}/${c}` };
  const 变 = [];
  for (const k of new Set([...Object.keys(A), ...Object.keys(B)])) {
    const x = (A[k] || '').split(','), y = (B[k] || '').split(',');
    if (x.length !== 整数量.length || y.length !== 整数量.length) continue;
    for (let i = 0; i < 整数量.length; i++) {
      if (x[i] === y[i] || x[i] === '' || y[i] === '') continue;
      变.push({ 路径: k, 量: 整数量[i], 从: +x[i], 到: +y[i], 差: +(y[i] - x[i]) });
    }
  }
  const 直方 = {};
  for (const e of 变) 直方[e.差] = (直方[e.差] || 0) + 1;
  return {
    变化数: 变.length,
    恰为2: 变.filter((e) => Math.abs(e.差) === 2).length,
    恰为3: 变.filter((e) => Math.abs(e.差) === 3).length,
    差直方图: Object.fromEntries(Object.entries(直方).sort((p, q) => Math.abs(+p[0]) - Math.abs(+q[0]))),
    恰2明细: 变.filter((e) => Math.abs(e.差) === 2).slice(0, 25),
    变明细: 变.slice(0, 30),
  };
};

out.逐步diff = {};
log('\n──── 逐步 diff（每一步都应当是 1px 视口差）────');
for (let i = 0; i < 扫描宽.length - 1; i++) {
  const a = 扫描宽[i], c = 扫描宽[i + 1];
  const d = 步diff(a, c);
  out.逐步diff[`${a}→${c}`] = d;
  log(`  ${a}→${c}：变化 ${d.变化数 ?? '—'} 处｜恰2 = ${d.恰为2 ?? '—'}｜恰3 = ${d.恰为3 ?? '—'}｜直方 ${JSON.stringify(d.差直方图)}`);
  for (const m of (d.恰2明细 || []).slice(0, 8)) log(`      ★恰2 ${m.路径.slice(-58)}｜${m.量} ${m.从}→${m.到}`);
}

const 有恰2的步 = Object.entries(out.逐步diff).filter(([, d]) => (d.恰为2 || 0) > 0).map(([k]) => k);
out.判定Q1 = { 有恰2的步, 结论: 有恰2的步.length === 0 ? '七档里一处 +2 都没有 ⇒ 276 那 5 处不是逐步产生的' : 有恰2的步.includes('373→374') ? '落在 373→374 ⇒ 它就是取景台阶' : `落在 ${有恰2的步.join('、')} ⇒ 与 374 无关` };
log(`\nQ1 判定：${out.判定Q1.结论}`);

// ══════════ Part 2：点不同节点，相机动不动 ══════════
const 读相机 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const t = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(vp.style.transform || '') : null;
  return { scale: m ? Number(m[1]) : null, tx: t ? Number(t[1]) : null, ty: t ? Number(t[2]) : null };
});

const 屏上律 = (w) => (w < 512 ? w - 412 : w - 532);

log(`\n════════ Part 2：点不同节点 ════════`);
for (const [宽, 高2] of Part2臂) {
  const p = await ctx.newPage();
  const 记 = { 宽, 高: 高2, 步: [] };
  try {
    await p.setViewportSize({ width: 宽, height: 高2 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: window.innerWidth, h: window.innerHeight }));
    if (实际.w !== 宽 || 实际.h !== 高2) throw new Error(`轴向自检失败：要 ${宽}×${高2}，实测 ${实际.w}×${实际.h}`);
    记.实际视口 = 实际;

    // 前提检查 ②：DOM 读出的节点宽是不是那个 W（音频 68 必须逐字 320）
    const 节点量 = await p.evaluate((ns) => {
      const o = {};
      for (const n of ns) {
        const e = document.querySelector(`.react-flow__node[data-id="${n.id}"]`);
        o[n.id] = e ? { offsetWidth: e.offsetWidth, offsetHeight: e.offsetHeight } : null;
      }
      return o;
    }, 三节点);
    记.节点量 = 节点量;
    const 音频W = 节点量['node_tadm1nyykc']?.offsetWidth;
    记.前提检查_W可从DOM读 = 音频W === 320;
    if (音频W !== 320) throw new Error(`前提检查失败：音频 68 的 offsetWidth 读出 ${音频W}，不是 320 ⇒ 「DOM 宽 = W」不成立，Part 2 预测算不出来`);

    记.C0_加载后 = await 读相机(p);
    log(`  [${宽}×${高2}] C0(加载后) scale=${记.C0_加载后.scale} tx=${记.C0_加载后.tx} ty=${记.C0_加载后.ty}`);

    for (const n of 三节点) {
      const 钮 = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('button, [role="button"]')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
      });
      if (!钮) throw new Error('找不到搜索钮');
      await p.mouse.click(钮.中心[0], 钮.中心[1]);
      await p.waitForTimeout(1600);
      await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
      await p.keyboard.type(n.名, { delay: 85 });
      await p.waitForTimeout(2200);
      const 短名 = n.id.replace(/^node_/, '');
      const 行 = await p.evaluate((nid) => {
        const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 在视口内: r.y >= 0 && r.bottom <= innerHeight && r.x >= 0 && r.right <= innerWidth };
      }, 短名);
      if (!行) { 记.步.push({ 节点: n.名, 错误: '搜不到那一行' }); log(`    点 ${n.名}：🔴 搜不到`); await p.keyboard.press('Escape'); await p.waitForTimeout(600); continue; }
      if (!行.在视口内) { 记.步.push({ 节点: n.名, 错误: '结果行在视口外', 行 }); log(`    点 ${n.名}：🔴 结果行在视口外`); await p.keyboard.press('Escape'); await p.waitForTimeout(600); continue; }

      await p.mouse.click(行.中心[0], 行.中心[1]);
      await p.waitForTimeout(5000);
      const 相机 = await 读相机(p);
      const 屏上 = await p.evaluate((nid) => {
        const e = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return { 宽: +r.width.toFixed(3), 高: +r.height.toFixed(3), 中心X: Math.round(r.x + r.width / 2), 中心Y: Math.round(r.y + r.height / 2) };
      }, n.id);
      const 目标W = 节点量[n.id]?.offsetWidth;
      const 预测s = 目标W ? Math.min(Math.max(屏上律(宽), 0) / 目标W, 0.5) : null;
      记.步.push({ 节点: n.名, id: n.id, W: 目标W, Hc: 节点量[n.id]?.offsetHeight, 屏上律: 屏上律(宽), 预测s, 相机, 屏上 });
      log(`    点 ${n.名}（W=${目标W}）｜相机 scale=${相机.scale} tx=${相机.tx} ty=${相机.ty}｜屏上 ${JSON.stringify(屏上)}｜预测 s=${预测s === null ? '—' : 预测s.toFixed(7)}`);
    }

    const 相机们 = [记.C0_加载后, ...记.步.filter((s) => s.相机).map((s) => s.相机)];
    记.相机逐字相同 = 相机们.every((c) => JSON.stringify(c) === JSON.stringify(相机们[0]));
    记.各步scale = 记.步.map((s) => ({ 节点: s.节点, scale: s.相机?.scale ?? null, 预测s: s.预测s ?? null }));
  } catch (e) {
    记.错误 = e.message;
    log(`  [${宽}×${高2}] 🔴 ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.Part2.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

const scale互异 = (记) => new Set(记.步.filter((s) => s.相机?.scale != null).map((s) => s.相机.scale)).size;
const 命中自己的律 = (记) => 记.步.filter((s) => s.预测s != null && s.相机?.scale != null)
  .map((s) => ({ 节点: s.节点, 实测: s.相机.scale, 预测: +s.预测s.toFixed(7), 逐字: Math.abs(s.相机.scale - s.预测s) < 5e-7 }));

out.判定Q2 = out.Part2.map((记) => ({
  臂: `${记.宽}x${记.高}`,
  相机逐字相同: 记.相机逐字相同 ?? null,
  不同scale个数: scale互异(记),
  逐字对表: 命中自己的律(记),
  结论: 记.错误 ? `🔴 ${记.错误}`
    : 记.相机逐字相同 ? 'Q2a：相机完全不动 ⇒ 取景是空操作'
      : scale互异(记) > 1
        ? (命中自己的律(记).length && 命中自己的律(记).every((x) => x.逐字) ? 'Q2b：相机随所点节点变，且新 scale 逐字等于该节点自己的律'
          : 'Q2c：相机随所点节点变，但 scale 不等于各节点自己的律 ⇒ 律是全局的')
        : 'scale 变了但只有一个取值：需看 tx/ty',
}));
log('\n──── Q2 判定 ────');
for (const j of out.判定Q2) { log(`  ${j.臂}：${j.结论}`); if (j.逐字对表?.length) log(`    ${JSON.stringify(j.逐字对表)}`); }

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