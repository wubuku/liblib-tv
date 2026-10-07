/**
 * 批次 279：取景失效的**分界线在高度上** —— 找出那个 `H`，并查清「点击到底生效没有」。
 *
 * 📌 起意（批次 278 的结果，它比预期干净得多）：
 *   278 在 **`H = 244`** 上扫 `w = 340 / 360 / 372 / 374 / 380 / 390 / 400 / 410 / 412 / 414 / 420 / 440 / 460`
 *   共 `13` 臂、每臂点**三个不同节点**（`视频 1` / `图片 b22-upload` / `音频 68`）：
 *   🔴 **相机一次都没动过**（`13/13` 臂「一步都没动过」）。
 *   而批次 277 Part 2 在**同一批节点**、**`H = 720`**、`w = 460 / 560` 上，相机**动了**。
 *   ⇒ 🔴 **分界线在高度上，不在宽度上。** 这不是「没有分界线」，是分界线在另一根轴上。
 *
 * 📌 **为什么这一条很重要**：
 *   批次 265–275 那整串「异常分支」读数（偏移 `32/34`、分母 `4091.4`、台阶在 `w=374`）
 *   **全部取自 `H = 244`** ⇒ 🔴 **它们测的是页面加载时的「初始自适应」，不是「点搜索结果行」的取景。**
 *   数字本身没错，但**事件标注错了** —— 手册里必须写清「这是在哪个事件上读到的」。
 *
 * 📌 **本批回答两件事**：
 *   Q1 **分界线在哪个 `H`**（`w` 固定在已知会动的 `460`）
 *   Q2 🔴 **点击到底生效没有** —— 278 只记了相机，**没记选中状态**。
 *      若连「选中」都没发生，那「相机不动」就有一个更平凡的解释（点击没落到结果行上），
 *      **必须先排除它，否则「取景不生效」这句话是在一个未证的前提上说的**（立规 142）。
 *
 * 📌 **预测先写死**（立规 129/130）：
 *   Q1a **存在 `H` 阈值**：`H` 小于某值时相机不动、且**节点确实被选中**（点生效了、只是不取景）；
 *   Q1b **点击根本没生效**（连选中都没有）⇒ 「相机不动」另有平凡解释，本批的结论要整个改写；
 *   Q1c **相机一直会动**，`H` 不是闸门 ⇒ 278 的读数另有原因。
 *
 * 📌 **三条前提**（不满足就整组作废、写明原因）：
 *   ① **轴向自检**：`innerW/innerH` 逐字等于设定值；
 *   ② **`音频 68` 的 `offsetWidth` 必须逐字 `320`**；
 *   ③ 🔴 **点击生效自检（新增，Q2 的前提）**：每次点完**必须读到选中状态变化**，
 *      否则该臂标为「点击未生效」，**不参与「取景是否生效」的判定**。
 *
 * 📌 **三条纪律**：只读（不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**）；
 *   每臂开新页；末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b279.mjs      （落盘 /tmp/b279.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B279_OUT || '/tmp/b279.json';
const 宽 = 460;                        // 批次 277 已证 `H=720` 时在此宽度取景会动
const 高度组 = [720, 600, 480, 400, 360, 320, 300, 280, 260, 250, 244, 240, 220, 200];
const 两节点 = [
  { id: 'node_236ctpehgg', 名: '视频 1', 备用名: ['视频 1', '视频'] },
  { id: 'node_tadm1nyykc', 名: '音频 68', 备用名: ['音频 68', '音频'] },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b279',
  问: '① 取景失效的分界线在哪个 H？② 点击到底生效没有（选中状态变没变）？',
  预测: {
    Q1a: '存在 H 阈值：低于它相机不动、但节点确实被选中',
    Q1b: '点击根本没生效（连选中都没有）⇒ 「相机不动」另有平凡解释',
    Q1c: '相机一直会动，H 不是闸门',
  },
  宽, 高度组, 两节点, 臂: [], 收尾: {},
};

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 读 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const t = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(vp.style.transform || '') : null;
  const sel = Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id'));
  const 状态行 = (document.body.innerText.match(/\d+ nodes, \d+ edges, (\d+) selected/) || [])[1] ?? null;
  return { scale: m ? Number(m[1]) : null, tx: t ? Number(t[1]) : null, ty: t ? Number(t[2]) : null, 选中id: sel, 状态行选中数: 状态行 };
});

const 同 = (a, b2) => a && b2 && a.scale === b2.scale && a.tx === b2.tx && a.ty === b2.ty;
const 屏上律 = (w) => (w < 512 ? w - 412 : w - 532);
const 预测s = (w, H, W, Hc) => (W && Hc
  ? +Math.max(0.08, Math.min(Math.max(100, 屏上律(w)) / W, 0.5, (H - 160) / Hc)).toFixed(7)
  : null);

for (const 高 of 高度组) {
  const p = await ctx.newPage();
  const 记 = { 高, 宽, 步: [] };
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);

    // 前提①：轴向自检
    const 实际 = await p.evaluate(() => ({ w: window.innerWidth, h: window.innerHeight }));
    if (实际.w !== 宽 || 实际.h !== 高) throw new Error(`轴向自检失败：要 ${宽}×${高}，实测 ${实际.w}×${实际.h}`);
    记.实际视口 = 实际;

    // 前提②：DOM 宽 = W
    const 节点量 = await p.evaluate((ns) => {
      const o = {};
      for (const n of ns) {
        const e = document.querySelector(`.react-flow__node[data-id="${n.id}"]`);
        o[n.id] = e ? { W: e.offsetWidth, Hc: e.offsetHeight } : null;
      }
      return o;
    }, 两节点);
    记.节点量 = 节点量;
    const 音频W = 节点量['node_tadm1nyykc']?.W;
    if (音频W !== 320) throw new Error(`前提②失败：音频 68 的 offsetWidth 读出 ${音频W}，不是 320`);

    记.C0_加载后 = await 读(p);

    for (const n of 两节点) {
      const 钮 = await p.evaluate(() => {
        const e = Array.from(document.querySelectorAll('button, [role="button"]')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 在视口内: r.y >= 0 && r.bottom <= innerHeight };
      });
      if (!钮) throw new Error('找不到搜索钮');
      if (!钮.在视口内) { 记.步.push({ 节点: n.名, 错误: '搜索钮在视口外' }); continue; }
      await p.mouse.click(钮.中心[0], 钮.中心[1]);
      await p.waitForTimeout(1600);
      if (!await p.evaluate(() => !!document.querySelector('[data-testid="canvas-search-panel"]'))) {
        记.步.push({ 节点: n.名, 错误: '搜索面板没打开' }); continue;
      }

      const 短名 = n.id.replace(/^node_/, '');
      let 行 = null, 用名 = null;
      for (const 名 of n.备用名) {
        await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
        await p.keyboard.type(名, { delay: 80 });
        await p.waitForTimeout(2000);
        行 = await p.evaluate((nid) => {
          const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
          if (!e) return null;
          const r = e.getBoundingClientRect();
          return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 在视口内: r.y >= 0 && r.bottom <= innerHeight && r.x >= 0 && r.right <= innerWidth, 可见: r.width > 0 && r.height > 0 };
        }, 短名);
        if (行 && 行.可见 && 行.在视口内) { 用名 = 名; break; }
        行 = null;
      }
      if (!行) { 记.步.push({ 节点: n.名, 错误: `搜不到结果行（试过 ${n.备用名.join(' / ')}）` }); await p.keyboard.press('Escape'); await p.waitForTimeout(700); continue; }

      await p.mouse.click(行.中心[0], 行.中心[1]);
      await p.waitForTimeout(5000);
      const 后 = await 读(p);
      const W = 节点量[n.id]?.W, Hc = 节点量[n.id]?.Hc;
      // 前提③：点击生效自检 —— 选中状态必须真的变了
      const 选中生效 = 后.选中id.includes(n.id);
      记.步.push({
        节点: n.名, 用名, W, Hc, 屏上律: 屏上律(宽), 预测s: 预测s(宽, 高, W, Hc),
        相机: 后, 选中生效,
        选中id: 后.选中id, 状态行选中数: 后.状态行选中数,
      });
    }

    const C0 = { scale: 记.C0_加载后.scale, tx: 记.C0_加载后.tx, ty: 记.C0_加载后.ty };
    记.C0相机 = C0;
    记.有效步 = 记.步.filter((s) => s.选中生效 === true);
    记.点击全未生效 = 记.步.length > 0 && 记.有效步.length === 0;
    记.相机动过 = 记.步.filter((s) => s.相机 && !同(s.相机, C0)).length > 0;
    记.结论 = 记.点击全未生效 ? '点击未生效（不参与判定）' : 记.相机动过 ? '相机动过' : '点击生效但相机不动';
    log(`H=${高}｜C0 scale=${记.C0_加载后.scale}｜${记.结论}`);
    for (const s of 记.步) {
      log(`    点 ${s.节点}${s.错误 ? `：🔴 ${s.错误}` : `｜选中生效=${s.选中生效 ? '✅' : '🔴'}｜scale=${s.相机.scale}｜预测 s=${s.预测s ?? '—'} ${s.预测s != null && Math.abs(s.相机.scale - s.预测s) < 5e-7 ? '✅逐字' : '❌不符'}`}`);
    }
  } catch (e) {
    记.错误 = e.message;
    log(`H=${高} 🔴 ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ═══ 判定 ═══
const 动 = out.臂.filter((a) => a.结论 === '相机动过').map((a) => a.高);
const 不动 = out.臂.filter((a) => a.结论 === '点击生效但相机不动').map((a) => a.高);
const 点不动 = out.臂.filter((a) => a.结论 === '点击未生效（不参与判定）').map((a) => a.高);
const 报错 = out.臂.filter((a) => a.错误).map((a) => a.高);
out.判定 = {
  相机动过的高度: 动, 点击生效但相机不动的高度: 不动,
  点击未生效的高度: 点不动, 报错的高度: 报错,
  预测逐字命中的高度: out.臂.filter((a) => a.步.some((s) => s.预测s != null && Math.abs(s.相机.scale - s.预测s) < 5e-7)).map((a) => a.高),
  结论: 点不动.length
    ? `🔴 Q1b：${JSON.stringify(点不动)} 这些高度上点击**根本没生效**（连选中都没有）⇒ 「相机不动」另有平凡解释`
    : 动.length && 不动.length
      ? `Q1a ✅ 阈值存在：动 ${JSON.stringify(动.sort((a, b2) => b2 - a))} ／ 不动 ${JSON.stringify(不动.sort((a, b2) => b2 - a))}`
      : 不动.length
        ? `Q1a ✅ 全部 ${不动.length} 个高度都是「点生效、相机不动」`
        : 动.length ? 'Q1c：相机在所有臂都动过 ⇒ H 不是闸门' : '🔴 无法判定',
};
log(`\n════ 判定 ════\n${out.判定.结论}`);
log(`动过：${JSON.stringify(动)}\n不动：${JSON.stringify(不动)}\n点不动：${JSON.stringify(点不动)}\n报错：${JSON.stringify(报错)}`);
log(`预测逐字命中：${JSON.stringify(out.判定.预测逐字命中的高度)}`);

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