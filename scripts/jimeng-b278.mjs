/**
 * 批次 278：在「异常分支」那个区间里，**点搜索结果行到底动不动相机？**
 *
 * 📌 起意（批次 276 + 277 合起来甩出的两条，合起来只指向一个问题）：
 *   276：相机在四个相位里 `scale/tx/ty` **逐字相同**（含「动作前」）
 *        ⇒ 点 `音频 68` 的结果行，看起来不动。
 *   277 Part 2（`w=460/560`、**点两个不同节点**）：
 *        `w=460`：加载后 `0.102655` → 点 `视频 1` 后 **`0.15`** ⇒ **相机动了**；
 *        `w=560`：加载后 `0.124653` → 点后 **`0.3125`** ⇒ **相机动了**。
 *        而且 `0.15 = 48/320`、`0.3125 = 100/320`（**族内地板 `100/W` 兜住了 `w−532=28`**）
 *        ⇒ ✅ **取景律连同族内地板，两档各 `2/2` 逐字命中**（批次 253 那张表独立复现）。
 *   🔴 **于是 `w=372–377` 不动、`w=460/560` 会动，中间一定有一条分界线。**
 *      它可能意味着：🔴 **那个「异常分支」（偏移 `32/34`、分母 `4091.4`）
 *      根本不是取景，而是「加载时的初始自适应」** —— 手册里整条律的**事件标注就错了**。
 *
 * 📌 **本批只回答一件事**：**相机从哪个 `w` 起才开始跟着点谁而变。**
 *
 * 📌 **预测先写死**（立规 129/130）：
 *   P1 **存在一条分界线**：`w` 小于某值时相机完全不动（只有初始自适应），
 *      越过某值后相机随所点节点变。
 *   P2 **没有分界线**：相机一直会动，只是异常分支区间的取景落点**恰好等于**初始自适应。
 *      （若 P2 成立，则批次 271/272 那条偏移律测的确实是取景，只是我还没找到让相机先跑开的办法。）
 *   🔴 **P1 与 P2 的后果差得很远**（P1 ⇒ 要改手册的事件标注），所以**必须用两个不同节点**去测，
 *      只点同一个节点分不开（幂等，见批次 276）。
 *
 * 📌 **三条前提**（不满足就整组作废、写明原因，不硬跑）：
 *   ① **轴向自检**：`innerW/innerH` 逐字等于设定值；
 *   ② **整数量纲可用率** `< 0.9` 直接 `throw`（立规 156，批次 276 的教训）；
 *   ③ **`音频 68` 的 `offsetWidth` 必须逐字 `320`**，否则「`DOM` 宽 = `W`」不成立。
 *
 * 📌 **三条纪律**：只读（不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**）；
 *   每臂开新页；末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b278.mjs      （落盘 /tmp/b278.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B278_OUT || '/tmp/b278.json';
const 高 = 244;                                    // 与批次 271/272/276 同一切片
const 宽度组 = [340, 360, 372, 374, 380, 390, 400, 410, 412, 414, 420, 440, 460];
const 分母 = 4091.4;                               // 批次 271 定的异常分支宽度项分母
const 三节点 = [
  { id: 'node_236ctpehgg', 名: '视频 1', 备用名: ['视频 1', '视频'] },
  { id: 'node_gref4sw056', 名: '图片 b22-upload', 备用名: ['图片 b22-upload', 'b22-upload', '图片 b22', 'b22'] },
  { id: 'node_tadm1nyykc', 名: '音频 68', 备用名: ['音频 68', '音频'] },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b278',
  问: '相机从哪个 w 起才开始跟着「点了哪个节点」变？',
  预测: {
    P1: '存在分界线：小的 w 相机完全不动（只有初始自适应），越过某值后才随节点变',
    P2: '没有分界线：一直会动，只是异常分支区间取景落点恰好等于初始自适应',
  },
  宽度组, 高, 分母, 三节点, 臂: [], 收尾: {},
};

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 读相机 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const t = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(vp.style.transform || '') : null;
  return { scale: m ? Number(m[1]) : null, tx: t ? Number(t[1]) : null, ty: t ? Number(t[2]) : null };
});

const 同 = (a, b2) => a && b2 && a.scale === b2.scale && a.tx === b2.tx && a.ty === b2.ty;
const 屏上律 = (w) => (w < 512 ? w - 412 : w - 532);
/** 手册那条取景律：s = min( max(100, 屏上律(w)) / W , 0.5 )，再被应用下限 0.08 兜住 */
const 预测s = (w, W) => (W ? +Math.max(0.08, Math.min(Math.max(100, 屏上律(w)) / W, 0.5)).toFixed(7) : null);

for (const 宽 of 宽度组) {
  const p = await ctx.newPage();
  const 记 = { 宽, 高, 步: [] };
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);

    // 前提①：轴向自检
    const 实际 = await p.evaluate(() => ({ w: window.innerWidth, h: window.innerHeight }));
    if (实际.w !== 宽 || 实际.h !== 高) throw new Error(`轴向自检失败：要 ${宽}×${高}，实测 ${实际.w}×${实际.h}`);
    记.实际视口 = 实际;

    // 前提③：DOM 读出的节点宽是不是那个 W
    const 节点量 = await p.evaluate((ns) => {
      const o = {};
      for (const n of ns) {
        const e = document.querySelector(`.react-flow__node[data-id="${n.id}"]`);
        o[n.id] = e ? { W: e.offsetWidth, Hc: e.offsetHeight } : null;
      }
      return o;
    }, 三节点);
    记.节点量 = 节点量;
    const 音频W = 节点量['node_tadm1nyykc']?.W;
    if (音频W !== 320) throw new Error(`前提③失败：音频 68 的 offsetWidth 读出 ${音频W}，不是 320`);

    记.C0_加载后 = await 读相机(p);

    for (const n of 三节点) {
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
        记.步.push({ 节点: n.名, 错误: '搜索面板没打开' });
        continue;
      }

      // 结果行定位：按备用名逐个试（批次 277 的「搜不到」就死在这一步）
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
      const 相机 = await 读相机(p);
      const W = 节点量[n.id]?.W;
      记.步.push({ 节点: n.名, 用名, W, Hc: 节点量[n.id]?.Hc, 屏上律: 屏上律(宽), 预测s: 预测s(宽, W), 相机 });
    }

    const 相机们 = [记.C0_加载后, ...记.步.filter((s) => s.相机).map((s) => s.相机)];
    记.相机取值数 = new Set(相机们.map((c) => `${c.scale}/${c.tx}/${c.ty}`)).size;
    记.任一点动过 = 相机们.slice(1).some((c) => !同(c, 相机们[0]));
    for (const s of 记.步) if (s.相机) {
      s.分子 = +(s.相机.scale * 分母).toFixed(4);
      s.偏移 = +(宽 - s.相机.scale * 分母).toFixed(4);
      s.预测偏移 = +(宽 - (s.预测s != null ? s.预测s * s.W : NaN)).toFixed(4);
    }
    const 首 = 记.步.find((s) => s.相机);
    记.C0分子 = +(记.C0_加载后.scale * 分母).toFixed(4);
    记.C0偏移 = +(宽 - 记.C0_加载后.scale * 分母).toFixed(4);
    记.首节点预测命中 = 首 && 首.预测s != null ? Math.abs(首.相机.scale - 首.预测s) < 5e-7 : null;
    记.结论 = 记.相机取值数 > 1 ? '相机动过' : '相机一步都没动过';

    log(`w=${宽}｜C0 scale=${记.C0_加载后.scale}（分子 ${记.C0分子}，偏移 ${记.C0偏移}）｜${记.结论}`);
    for (const s of 记.步) {
      log(`    点 ${s.节点}${s.错误 ? `：🔴 ${s.错误}` : `（W=${s.W}）｜scale=${s.相机.scale} 分子=${s.分子} 偏移=${s.偏移}｜预测 s=${s.预测s ?? '—'} 预测偏移=${s.预测偏移 ?? '—'} ${s.预测s != null && Math.abs(s.相机.scale - s.预测s) < 5e-7 ? '✅逐字' : '❌不符'}`}`);
    }
  } catch (e) {
    记.错误 = e.message;
    log(`w=${宽} 🔴 ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ═══ 判定 ═══
const 会动 = out.臂.filter((a) => a.结论 === '相机动过').map((a) => a.宽);
const 不动 = out.臂.filter((a) => a.结论 === '相机一步都没动过').map((a) => a.宽);
const 报错 = out.臂.filter((a) => a.错误).map((a) => a.宽);
out.判定 = {
  会动的宽度: 会动, 不动的宽度: 不动, 报错的宽度: 报错,
  全部命中律的臂: out.臂.filter((a) => a.首节点预测命中 === true).map((a) => a.宽),
  结论: 不动.length && 会动.length
    ? `P1 ✅ 存在分界线：不动 ${JSON.stringify(不动)} ／ 会动 ${JSON.stringify(会动)}`
    : 不动.length
      ? `P1 ✅ 全部 ${不动.length} 臂相机都没动过 ⇒ 在这条扫描范围里「点搜索结果行」不生效`
      : 会动.length
        ? 'P2 相机在所有臂都动过 ⇒ 没有分界线'
        : '🔴 全部臂报错，无法判定',
};
log(`\n════ 判定 ════\n${out.判定.结论}`);
log(`不动：${JSON.stringify(不动)}\n会动：${JSON.stringify(会动)}\n报错：${JSON.stringify(报错)}`);
log(`预测逐字命中的臂：${JSON.stringify(out.判定.全部命中律的臂)}`);

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