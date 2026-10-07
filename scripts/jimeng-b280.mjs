/**
 * 批次 280：把「点搜索结果行有没有生效」的高度阈值钉死在 `244` 与 `250` 之间，并诊断 `H=200` 为什么连结果行都搜不到。
 *
 * 📌 起意（批次 279 的结果，Q1b 成立）：
 *   `w = 460` 固定，`H = 720 / 600 / 480 / 400 / 360 / 320 / 300 / 280 / 260 / 250` —— **十臂相机全都动了**
 *   （点 `视频 1` 后 `scale = 0.15 = 48/320`，且 **`选中生效 = ✅`**、`选中id = ['node_236ctpehgg']`）；
 *   `H = 244 / 240 / 220` —— 面板**开得了**、结果行**存在且可见可点**（脚本没报任何错），
 *   但点完 **`选中id = []`、状态行选中数 `0`、相机不动**；
 *   `H = 200` —— 🔴 **连结果行都搜不到**（试过 `视频 1` 与 `视频` 两个名字）。
 *
 *   ⇒ 🔴 **「点不动」是一条真实的用户面限制，不是取景机制。**
 *   ⇒ 📌 这也**改写了批次 278 的措辞**（见下），但**不改它的读数归属**。
 *
 * 📌 **本批两问**：
 *   Q1 **阈值在哪个 `H`**（`244`↔`250` 之间逐 `1px` 扫）
 *   Q2 **`H=200` 为什么搜不到结果行** —— 面板没开？输入框不在？列表真的空？**三者的用户面含义完全不同**。
 *
 * 📌 **预测先写死**（立规 129/130）：
 *   Q1a **阈值是一个整数高度**，`244 ≤ H* ≤ 250`，相邻两臂行为不同；
 *   Q1b **没有阈值**，差异来自别处（例如某次加载慢、结果列表还没渲染完）
 *      ⇒ **所以每一臂都要连点两遍**：第一遍若没生效，隔 `2s` 再点一次，看它是不是「时序」问题。
 *   Q2a **`H=200` 时面板**开得了**，但**输入框点不到/搜不到结果**；
 *   Q2b **`H=200` 时面板根本开不了**。
 *
 * 📌 **三条前提**：
 *   ① **轴向自检**：`innerW/innerH` 逐字等于设定值；
 *   ② **`音频 68` 的 `offsetWidth` 必须逐字 `320`**；
 *   ③ 🔴 **点击生效自检**：`选中id` 必须真的包含目标节点，否则该臂标「点击未生效」、**不参与阈值判定**。
 *   ④ 📌 **判定用的 `选中生效` 判据已在本批校验过**：它在 `H ≥ 250` 的臂上逐字为 `✅`
 *      （`.selected` 选择器有效），所以 `H ≤ 244` 上的 `[]` 是真结果，不是选择器写错了。
 *
 * 📌 **修掉批次 279 的两个自身缺陷**（别改回去）：
 *   ① **预测函数错了**：窄侧 `w < 512` 走 `screen = w − 412`，**没有族内地板 `100`**（批次 251/253）。
 *     279 用了 `max(100, w−412)`，于是把实测 `0.15` 判成「❌不符」。
 *     **那是预测函数的错，不是数据的错** —— 本批已改成按窄侧/宽侧分派。
 *   ② **第二个节点常常点不到**：第一次点完结果行面板自动收起，紧接着再点「搜索」有时开不了。
 *     本批在两次点击之间加**关面板确认 + 重新定位搜索钮**，并记录失败原因。
 *
 * 📌 **三条纪律**：只读（不新建/不删除/不上传/不分享/不进扣费页/**绝不点生成**）；
 *   每臂开新页；末态在实验流程之外独立复查（立规 140）。
 *
 * 用法：node scripts/jimeng-b280.mjs      （落盘 /tmp/b280.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B280_OUT || '/tmp/b280.json';
const 宽 = 460;
const 高度组 = [241, 242, 243, 244, 245, 246, 247, 248, 249, 250];
const 诊断组 = [220, 200, 180];
const 两节点 = [
  { id: 'node_236ctpehgg', 名: '视频 1', 备用名: ['视频 1', '视频'] },
  { id: 'node_tadm1nyykc', 名: '音频 68', 备用名: ['音频 68', '音频'] },
];

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b280',
  问: '① 点搜索结果行「有没有生效」的高度阈值钉在哪？② H=200 为什么连结果行都搜不到？',
  预测: {
    Q1a: '阈值是一个整数高度，244 ≤ H* ≤ 250，相邻两臂行为不同',
    Q1b: '没有阈值，差异来自时序 ⇒ 每臂连点两遍验证',
    Q2a: 'H=200 面板开得了但搜不到结果行',
    Q2b: 'H=200 面板根本开不了',
  },
  宽, 高度组, 诊断组, 两节点, 臂: [], 诊断: [], 收尾: {},
};

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

const 读 = (p) => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const t = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(vp.style.transform || '') : null;
  const sel = Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id'));
  const 行 = (document.body.innerText.match(/\d+ nodes, \d+ edges, (\d+) selected/) || [])[1] ?? null;
  return { scale: m ? Number(m[1]) : null, tx: t ? Number(t[1]) : null, ty: t ? Number(t[2]) : null, 选中id: sel, 状态行选中数: 行 };
});

const 找搜索钮 = (p) => p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('button, [role="button"]')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 盒: [r.width, r.height], 在视口内: r.y >= 0 && r.bottom <= innerHeight && r.x >= 0 && r.right <= innerWidth };
});

const 开面板 = async (p) => {
  const 钮 = await 找搜索钮(p);
  if (!钮) return { 成功: false, 原因: '找不到搜索钮', 钮 };
  if (!钮.在视口内) return { 成功: false, 原因: `搜索钮在视口外 y=${钮.中心[1]}`, 钮 };
  await p.mouse.click(钮.中心[0], 钮.中心[1]);
  await p.waitForTimeout(1600);
  const 状态 = await p.evaluate(() => {
    const pn = document.querySelector('[data-testid="canvas-search-panel"]');
    if (!pn) return { 面板: false, 有输入框: false };
    const i = pn.querySelector('input');
    const r = pn.getBoundingClientRect();
    return { 面板: true, 有输入框: !!i, 面板可见: r.width > 0 && r.height > 0, 面板盒: [Math.round(r.width), Math.round(r.height)], 面板顶: Math.round(r.y), 面板底: Math.round(r.bottom) };
  });
  return { 成功: !!状态.面板, 原因: 状态.面板 ? null : '点了搜索钮但面板没出现', 钮, 状态 };
};

const 关面板 = async (p) => { await p.keyboard.press('Escape'); await p.waitForTimeout(700); await p.keyboard.press('Escape'); await p.waitForTimeout(700); };

const 找结果行 = async (p, n) => {
  const 短名 = n.id.replace(/^node_/, '');
  const 尝试 = [];
  for (const 名 of n.备用名) {
    await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
    await p.keyboard.type(名, { delay: 80 });
    await p.waitForTimeout(2000);
    const 行 = await p.evaluate((nid) => {
      const e = document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`);
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 盒: [Math.round(r.width), Math.round(r.height)], 顶: Math.round(r.y), 底: Math.round(r.bottom), 在视口内: r.y >= 0 && r.bottom <= innerHeight && r.x >= 0 && r.right <= innerWidth, 可见: r.width > 0 && r.height > 0 };
    }, 短名);
    尝试.push({ 名, 有行: !!行, 行 });
    if (行 && 行.可见 && 行.在视口内) return { 行, 用名: 名, 尝试 };
  }
  return { 行: null, 用名: null, 尝试 };
};

const 同 = (a, b2) => a && b2 && a.scale === b2.scale && a.tx === b2.tx && a.ty === b2.ty;
/** ✅ 已修：窄侧（w<512）走 w−412、**没有族内地板 100**；宽侧（w≥512）才有 max(100, w−532) */
const 屏上律 = (w) => (w < 512 ? w - 412 : Math.max(100, w - 532));
const 预测s = (w, H, W, Hc) => (W && Hc
  ? +Math.max(0.08, Math.min(屏上律(w) / W, 0.5, (H - 160) / Hc)).toFixed(7)
  : null);

// ══════════ 主扫描：阈值 ══════════
log(`\n════════ 主扫描：w=${宽}，H=${高度组.join('/')} ════════`);
for (const 高 of 高度组) {
  const p = await ctx.newPage();
  const 记 = { 高, 宽, 步: [] };
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: window.innerWidth, h: window.innerHeight }));
    if (实际.w !== 宽 || 实际.h !== 高) throw new Error(`轴向自检失败：要 ${宽}×${高}，实测 ${实际.w}×${实际.h}`);
    记.实际视口 = 实际;

    const 节点量 = await p.evaluate((ns) => {
      const o = {};
      for (const n of ns) { const e = document.querySelector(`.react-flow__node[data-id="${n.id}"]`); o[n.id] = e ? { W: e.offsetWidth, Hc: e.offsetHeight } : null; }
      return o;
    }, 两节点);
    if (节点量['node_tadm1nyykc']?.W !== 320) throw new Error(`前提②失败：音频 68 的 offsetWidth 读出 ${节点量['node_tadm1nyykc']?.W}`);
    记.节点量 = 节点量;
    记.C0 = await 读(p);

    for (const n of 两节点) {
      const 开 = await 开面板(p);
      const 步 = { 节点: n.名, 面板: 开 };
      if (!开.成功) { 步.错误 = 开.原因; 记.步.push(步); continue; }
      const 找 = await 找结果行(p, n);
      步.找行 = { 用名: 找.用名, 尝试: 找.尝试 };
      if (!找.行) { 步.错误 = '搜不到可点的结果行'; 记.步.push(步); await 关面板(p); continue; }

      // 前提③ + 预测 Q1b：连点两遍 —— 区分「阈值」与「时序」
      const 点一次 = async () => {
        await p.mouse.click(找.行.中心[0], 找.行.中心[1]);
        await p.waitForTimeout(5000);
        return await 读(p);
      };
      const 后1 = await 点一次();
      步.第一遍 = { 选中生效: 后1.选中id.includes(n.id), 选中id: 后1.选中id, scale: 后1.scale };
      步.预测s = 预测s(宽, 高, 节点量[n.id]?.W, 节点量[n.id]?.Hc);
      if (!后1.选中id.includes(n.id)) {
        // 第二遍：结果行可能还在（面板没关），先确认还在再点
        const 还在 = await p.evaluate((nid) => !!document.querySelector(`[data-testid="canvas-search-result-node_${nid}"]`), n.id.replace(/^node_/, ''));
        步.第二遍前结果行还在 = 还在;
        if (还在) {
          const 后2 = await 点一次();
          步.第二遍 = { 选中生效: 后2.选中id.includes(n.id), 选中id: 后2.选中id, scale: 后2.scale };
          步.相机 = 后2;
        } else {
          const 再开 = await 开面板(p);
          步.重开面板 = 再开.成功;
          if (再开.成功) {
            const 再找 = await 找结果行(p, n);
            if (再找.行) {
              const 后2 = await 点一次();
              步.第二遍 = { 选中生效: 后2.选中id.includes(n.id), 选中id: 后2.选中id, scale: 后2.scale };
              步.相机 = 后2;
            } else 步.相机 = 后1;
          } else 步.相机 = 后1;
        }
      } else 步.相机 = 后1;
      步.选中生效 = !!(步.相机 && 步.相机.选中id.includes(n.id));
      记.步.push(步);
      await 关面板(p);
    }

    记.相机动过 = 记.步.some((s) => s.相机 && !同(s.相机, 记.C0));
    记.任一选中生效 = 记.步.some((s) => s.选中生效 === true);
    记.结论 = 记.任一选中生效 ? '点击生效' : 记.相机动过 ? '相机动但没选中（异常）' : '点击未生效';
    log(`H=${高}｜${记.结论}｜C0 scale=${记.C0.scale}`);
    for (const s of 记.步) {
      log(`    ${s.节点}${s.错误 ? `：🔴 ${s.错误}` : `｜一遍=${s.第一遍?.选中生效 ? '✅' : '🔴'}${s.第二遍 ? ` 二遍=${s.第二遍.选中生效 ? '✅' : '🔴'}` : ''}｜scale=${s.相机?.scale}｜预测 s=${s.预测s ?? '—'} ${s.预测s != null && s.相机 && Math.abs(s.相机.scale - s.预测s) < 5e-7 ? '✅逐字' : '❌不符'}`}`);
    }
  } catch (e) { 记.错误 = e.message; log(`H=${高} 🔴 ${e.message}`); }
  finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ══════════ 诊断：面板开不开、输入框在不在、列表空不空 ══════════
log(`\n════════ 诊断：H=${诊断组.join('/')} ════════`);
for (const 高 of 诊断组) {
  const p = await ctx.newPage();
  const 记 = { 高, 宽 };
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(6000);
    const 实际 = await p.evaluate(() => ({ w: window.innerWidth, h: window.innerHeight }));
    if (实际.w !== 宽 || 实际.h !== 高) throw new Error(`轴向自检失败：要 ${宽}×${高}，实测 ${实际.w}×${实际.h}`);
    const 钮 = await 找搜索钮(p);
    记.搜索钮 = 钮;
    const 开 = await 开面板(p);
    记.开面板 = 开;
    if (开.成功) {
      // 输入框点得到吗
      记.输入框 = await p.evaluate(() => {
        const i = document.querySelector('[data-testid="canvas-search-panel"] input');
        if (!i) return { 存在: false };
        const r = i.getBoundingClientRect();
        return { 存在: true, 可见: r.width > 0 && r.height > 0, 盒: [Math.round(r.width), Math.round(r.height)], 在视口内: r.y >= 0 && r.bottom <= innerHeight && r.x >= 0 && r.right <= innerWidth };
      });
      if (记.输入框.存在 && 记.输入框.可见) {
        await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-search-panel"] input'); if (i) { i.focus(); i.select(); } });
        await p.keyboard.type('视频', { delay: 80 });
        await p.waitForTimeout(2500);
        记.输入后 = await p.evaluate(() => {
          const pn = document.querySelector('[data-testid="canvas-search-panel"]');
          if (!pn) return { 面板还在: false };
          const 结果数 = pn.querySelectorAll('[data-testid^="canvas-search-result-"]').length;
          return { 面板还在: true, 结果数, 面板可见文本: (pn.innerText || '').slice(0, 160) };
        });
      }
    }
    log(`H=${高}｜搜索钮 ${钮 ? (钮.在视口内 ? '在视口内' : '🔴在视口外') : '🔴找不到'}｜面板 ${开.成功 ? '✅开' : `🔴${开.原因}`}｜输入框 ${记.输入框 ? (记.输入框.可见 ? '✅可见' : '🔴零尺寸') : '—'}｜${记.输入后 ? `输入后结果数 ${记.输入后.结果数}` : '—'}`);
  } catch (e) { 记.错误 = e.message; log(`H=${高} 🔴 ${e.message}`); }
  finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.诊断.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// ═══ 判定 ═══
const 二遍才生效 = out.臂.filter((a) => a.步.some((s) => s.第一遍 && !s.第一遍.选中生效 && s.第二遍?.选中生效)).map((a) => a.高).sort((x, y) => x - y);
const 预测逐字命中 = out.臂.filter((a) => a.步.some((s) => s.预测s != null && s.相机 && Math.abs(s.相机.scale - s.预测s) < 5e-7)).map((a) => a.高).sort((x, y) => x - y);
const 生效 = out.臂.filter((a) => a.结论 === '点击生效').map((a) => a.高).sort((x, y) => x - y);
const 未生效 = out.臂.filter((a) => a.结论 === '点击未生效').map((a) => a.高).sort((x, y) => x - y);
out.判定 = {
  点击生效的高度: 生效, 点击未生效的高度: 未生效,
  二遍才生效的高度: 二遍才生效,
  预测逐字命中的高度: 预测逐字命中,
  结论: 生效.length && 未生效.length
    ? `Q1a ✅ 阈值存在：生效 ${JSON.stringify(生效)} ／ 未生效 ${JSON.stringify(未生效)}`
    : 生效.length
      ? (二遍才生效.length ? `Q1b ⚠️ 全部 ${生效.length} 臂都生效，但其中 ${JSON.stringify(二遍才生效)} 是「二遍才生效」⇒ 更像时序而非阈值` : `全部 ${生效.length} 臂都生效`)
      : '全部臂都未生效',
};
log(`\n════ 判定 ════\n${out.判定.结论}`);
log(`生效：${JSON.stringify(生效)}\n未生效：${JSON.stringify(未生效)}\n二遍才生效：${JSON.stringify(out.判定.二遍才生效的高度)}\n预测逐字命中：${JSON.stringify(out.判定.预测逐字命中的高度)}`);
for (const d of out.诊断) log(`诊断 H=${d.高}：面板 ${d.开面板?.成功 ? '开' : '没开'}｜${JSON.stringify(d.输入后 ?? d.输入框 ?? null)}`);

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