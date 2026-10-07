/**
 * 批次 294：跳变与「窄 `W`」相关吗？ —— 加两个新宽度的节点当对照。
 *
 * 📌 起意（批次 293）：
 *   `w = 1211 → 1212` 的那个阈值上：
 *     `视频 1`（`320 × 569`）   ⇒ 跳（`0.984183 → 0.618949`）
 *     `音频 68`（`320 × 320`）   ⇒ 跳（`1.75 → 1.12308`）
 *     `图片 b22-upload`（`568.889 × 320`）⇒ **一个像素都没跳**（`1.19531`，闭式 `1.195313`）
 *   ⇒ 🔴 **跳的两个节点 `W` 都是 `320`，没跳的那个 `W` 是 `568.889`。**
 *   🔴 **但「相关」不等于「原因」** —— 必须再拉两个宽度不同的节点进来。
 *
 * 📌 **本批的四个节点与它们各自的作用（写死）**：
 *   `时间线 2`（`W ≈ 1200`，**最宽**）  🔴 **新对照：若「宽」的一律不跳，
 *                                            那么跳变就钉在「窄」这一侧**
 *   `文本 1`（`W ≈ 320`，与音频同宽）    📌 **同宽对照：若它也跳，则「`W = 320`」这条更硬**
 *   `音频 68`（`W = 320`）               📌 **已知参照（批次 293：跳）**
 *   `图片 b22-upload`（`W = 568.889`）   📌 **已知参照（批次 293：不跳）**
 *
 * 📌 **三条预测（测量前写死，前提⑤）**：
 *   P1 🔴 **在 `w = 1211` 上四个节点全部逐字命中闭式**
 *      （`1211` 已被批次 292/293 验过是闭式区，所以这是本批的自检）
 *   P2 📌 **跳变与 `W` 的相关性**：若「`W ≈ 320` 的跳、`W ≥ 568 的不跳」成立，
 *      则 `时间线`（`1200`）与 `文本`（`320`）应分别落在「不跳」与「跳」两列。
 *   P3 🔴 **若 `时间线`（`1200`）也跳** ⇒ **相关性被推翻** ⇒ **跳变与 `W` 无关**，
 *      线索要改到别的量（`kind`？节点在画布上的位置？）。
 *
 * 📌 **五条前提**：
 *   ① **轴向自检**：`innerW/innerH` 逐字等于设定值；
 *   ② 🔴 **`z0 > vs` 硬门**：`z0` 必须高于预测 `vs`，否则读到的不是平台；
 *   ③ 🔴 **落定自检**：点完连读两次（间隔 `2.5s`），必须逐字相同（立规 170）；
 *   ④ 📌 **跨遍一致性照样要报**（立规 171）—— 🔴 **臂内两次相同不等于定值**；
 *   ⑤ 🔴 **参数写死**：`532 / 160 / 0.08 / 8 / 0.5` 全部取自代码或已发布结论；
 *      📌 **`Wc` 用画布空间尺寸**（批次 288：分母必须是画布空间，DOM `offsetWidth` 会带来 `1.94e-4`）。
 *   📌 **节点不写死 id**：从 DOM 按 aria-label 现找，并**记下实际量到的 `offsetWidth/offsetHeight`**，
 *      🔴 **免得又一次把「记忆里的 `W`」当成实测值用**（立规 113）。
 *
 * 📌 **纪律**：只按放大键、只点搜索结果行；不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**；
 *   末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b294.mjs      （落盘 /tmp/b294.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B294_OUT || '/tmp/b294.json';
const 高 = 720;
const 放大键 = 'Meta+Equal';
const 按够 = 13;
const 宽度组 = [1211, 1212];

// 只给「标签前缀」，id 与尺寸一律现找现量（前提⑤）
const 想要的 = [
  { 键: '时间线', 前缀: '时间线', 作用: '最宽对照（若宽的不跳，相关性钉在窄侧）' },
  { 键: '文本',   前缀: '文本',   作用: '同宽对照（与音频同为 W≈320）' },
  { 键: '音频',   前缀: '音频',   作用: '已知参照：批次 293 跳' },
  { 键: '图片',   前缀: '图片',   作用: '已知参照：批次 293 不跳' },
];

// 🔴 前提⑤
const 屏上律 = (w) => Math.max(100, w - 532);
const 安全高 = 高 - 160;
const vf = (z) => Math.min(8, Math.max(0.08, z));

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b294',
  问: 'w=1212 的跳变与「窄 W」相关吗？',
  节点角色: 想要的, 宽度组, 臂: [], 判定: {},
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

/** 按 aria-label 前缀找出该类节点，取第一个，并把实测 offsetWidth/offsetHeight 一起带回来 */
const 找节点 = (p, 前缀) => p.evaluate((pre) => {
  const 全部 = Array.from(document.querySelectorAll('.react-flow__node[data-id]'));
  for (const e of 全部) {
    const 标签 = (e.getAttribute('aria-label') || e.textContent || '').trim();
    if (!标签.startsWith(pre)) continue;
    return { id: e.dataset.id, 标签, W: e.offsetWidth, Hc: e.offsetHeight };
  }
  return null;
}, 前缀);

for (const w of 宽度组) {
  for (const 角色 of 想要的) {
    const p = await ctx.newPage();
    const 记 = { w, h: 高, 键: 角色.键, 作用: 角色.作用, 按了几次: 按够 };
    try {
      await p.setViewportSize({ width: w, height: 高 });
      await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await p.waitForSelector('.react-flow__node', { timeout: 45000 });
      await p.waitForTimeout(6000);
      const 实际 = await p.evaluate(() => ({ w: innerWidth, h: innerHeight }));
      if (实际.w !== w || 实际.h !== 高) throw new Error(`轴向自检失败：要 ${w}×${高}，实测 ${实际.w}×${实际.h}`);

      const 目标 = await 找节点(p, 角色.前缀);
      if (!目标) throw new Error(`按标签前缀「${角色.前缀}」找不到节点`);
      记.节点id = 目标.id; 记.节点标签 = 目标.标签;
      记.实测盒 = { W: 目标.W, Hc: 目标.Hc };          // 🔴 实测，不靠记忆（立规 113）
      // 画布空间尺寸：DOM 宽是取整后的，画布宽可能不是整数（批次 288）
      const vp = await p.evaluate(() => {
        const e = document.querySelector('.react-flow__viewport');
        const m = e ? /scale\(([\d.]+)\)/.exec(e.style.transform || '') : null;
        return m ? Number(m[1]) : null;
      });
      记.初始zoom = vp;
      // 🔴 v2 修：offsetWidth/offsetHeight **本身就是画布空间（布局）尺寸**，
      //   v1 这里又除了一次 zoom，把 320 放大成 1229.5 ⇒ 闭式与相关性判定全错。
      //   （屏幕尺寸才是 画布尺寸 × zoom；布局尺寸不需要。）
      记.画布W = 目标.W;
      记.画布H = 目标.Hc;
      记.预测vs = 记.画布W && 记.画布H
        ? +vf(Math.min(屏上律(w) / 记.画布W, 安全高 / 记.画布H)).toFixed(6) : null;

      for (let i = 0; i < 按够; i++) { await p.keyboard.press(放大键); await p.waitForTimeout(380); }
      await p.waitForTimeout(1200);
      const z0 = await 读(p);
      记.z0 = z0.scale;
      if (z0.scale === null) throw new Error('读不到缩放');
      if (记.预测vs !== null && !(z0.scale > 记.预测vs)) throw new Error(`z0(${z0.scale}) 不高于预测 vs(${记.预测vs}) ⇒ 读不到平台`);

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
      const 候选名 = [目标.标签, 角色.前缀, `${角色.前缀} 1`, `${角色.前缀} 2`];
      for (const 名 of [...new Set(候选名)]) {
        await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
        await p.keyboard.type(名, { delay: 80 });
        await p.waitForTimeout(2000);
        const r = await p.evaluate((nid) => {
          const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid.replace(/^node_/, '')}"]`);
          if (!e) return null;
          const b = e.getBoundingClientRect();
          return { 中心: [Math.round(b.x + b.width / 2), Math.round(b.y + b.height / 2)], 可见: b.width > 0 && b.height > 0 && b.y >= 0 && b.bottom <= innerHeight && b.x >= 0 && b.right <= innerWidth };
        }, 目标.id);
        if (r && r.可见) { 行 = r; 用名 = 名; break; }
      }
      if (!行) throw new Error(`搜不到「${目标.标签}」的可见结果行`);
      记.用名 = 用名;
      await p.mouse.click(行.中心[0], 行.中心[1]);
      await p.waitForTimeout(3000);
      const a1 = await 读(p);
      await p.waitForTimeout(2500);
      const a2 = await 读(p);
      记.z后1 = a1.scale; 记.z后2 = a2.scale;
      记.落定 = a1.scale === a2.scale;
      记.选中 = a2.选中;
      记.点击生效 = a2.选中.includes(目标.id);
      if (!记.点击生效) throw new Error(`点击未生效（选中=${JSON.stringify(a2.选中)}）`);
      记.vs实测 = a2.scale;
      记.符合闭式 = 记.预测vs === null ? null : Math.abs(a2.scale - 记.预测vs) <= 2e-3;
      log(`${w}｜${角色.键.padEnd(4)}｜盒 ${目标.W}×${目标.Hc}｜画布 ${记.画布W}×${记.画布H}｜z0=${z0.scale}｜vs=${a2.scale}｜闭式 ${记.预测vs}｜${记.符合闭式 === null ? '（无预测）' : 记.符合闭式 ? '✅' : '🔴'}｜落定 ${记.落定 ? '✅' : '🔴'}`);
    } catch (e) {
      记.错误 = e.message; log(`${w}｜${角色.键} 🔴 ${e.message}`);
    } finally {
      try { await p.close(); } catch (e) { /* 忽略 */ }
      out.臂.push(记);
      fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
    }
  }
}

const 好 = out.臂.filter((x) => !x.错误 && x.点击生效 && x.vs实测 !== undefined);
log('\n════ 逐节点配对（按实测画布宽排序）════');
const 按键 = {};
for (const x of 好) (按键[x.键] = 按键[x.键] || []).push(x);
const 表 = Object.keys(按键).map((k) => {
  const 组 = 按键[k].sort((a, c) => a.w - c.w);
  return {
    键: k, 作用: 组[0].作用,
    画布W: 组[0].画布W, 画布H: 组[0].画布H,
    在1211: 组.find((x) => x.w === 1211) || null,
    在1212: 组.find((x) => x.w === 1212) || null,
    跳了: 组.some((x) => x.符合闭式 === false),
  };
}).sort((a, c) => (a.画布W ?? 0) - (c.画布W ?? 0));
for (const r of 表) {
  log(`  ${r.键.padEnd(4)} 画布W=${String(r.画布W).padEnd(9)} H=${String(r.画布H).padEnd(7)} ` +
      `1211→${r.在1211 ? r.在1211.vs实测 : '—'}｜1212→${r.在1212 ? r.在1212.vs实测 : '—'}｜${r.跳了 ? '🔴 跳' : '✅ 不跳'}｜${r.作用}`);
}

const 配对齐 = 表.every((r) => r.在1211 && r.在1212);
const 窄跳 = 表.filter((r) => r.跳了).map((r) => r.画布W);
const 宽不跳 = 表.filter((r) => !r.跳了).map((r) => r.画布W);
if (!配对齐) {
  out.判定 = { 结论: '🔴 有节点缺 1211/1212 其中一档 ⇒ 配对不完整，整组作废（立规 164）', 表: 表.map((r) => r.键) };
} else {
  const 相关 = 窄跳.length > 0 && 宽不跳.length > 0 && Math.max(...窄跳) < Math.min(...宽不跳);
  out.判定 = {
    有效臂: `${好.length}/${out.臂.length}`,
    落定: 好.every((x) => x.落定) ? '✅ 全部臂内落定' : `🔴 ${好.filter((x) => !x.落定).map((x) => x.键 + '@' + x.w).join('、')} 未落定`,
    P1_1211全中闭式: `${表.filter((r) => r.在1211 && r.在1211.符合闭式).length}/${表.length} 个节点在 w=1211 上逐字命中闭式`,
    跳了的: 表.filter((r) => r.跳了).map((r) => `${r.键}(W=${r.画布W})`).join('、') || '（无）',
    没跳的: 表.filter((r) => !r.跳了).map((r) => `${r.键}(W=${r.画布W})`).join('、') || '（无）',
    判决: 相关
      ? `✅ **「窄 W 跳、宽 W 不跳」这条相关性成立** —— 跳的画布宽最大 ${Math.max(...窄跳)}，不跳的最小 ${Math.min(...宽不跳)}，**两者不交叠** ⇒ 📌 阈值夹在 (${Math.max(...窄跳)}, ${Math.min(...宽不跳)}] 之间；⚠️ **相关不等于成因**，下一步要在那个区间里加密取点`
      : 窄跳.length === 0
        ? `🔴 **一个都没跳** ⇒ 与批次 292/293 冲突，**成因未测，不选边**（立规 113）`
        : `🔴 **相关性不成立** —— 跳与不跳的画布宽区间**交叠** ⇒ 📌 **跳变与「窄 W」无关**，线索要改到别的量（kind？节点在画布上的位置？），**不编**（立规 113）`,
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