/**
 * 批次 205：把「取景终态 `ty` 的断点落在 1200~1280 之间」这句话，
 * 变成「断点在**某一个确切的宽度**上」。
 *
 * 背景（批次 197 → 200 挂了 5 个批次的那条「未测」）：
 *   批次 197 发现 `落点X = 视口宽/2 − 166`；
 *   批次 200 把 `ty` 拟合为 `ty ≈ 0.504 × 视口高 + C`，拟合常数 **C 分两支**：
 *     1000 / 1200 宽  = `−407.435`（两档逐字相同）
 *     1280 三档 + 1600 = `−508` 那一支
 *   ⇒ 断点落在 1200 与 1280 **之间**，但**确切位置从未测过**。
 *
 * 🔴 为什么之前测不到（立规 79）：
 *   批次 199 只测了**初始平移**、从没测过**取景后**的 ty。
 *   本轮测的就是取景后。
 *
 * 本轮做法：
 *   ① 高度**固定 720**（这样 ty 里的 0.504×高 是常数，ty 本身就能直接比）；
 *   ② 宽度在 `1200~1280` 之间**密集取点**（步长 4，共 21 档）；
 *   ③ 每档都走**同一条取景流程**、点**同一个 testid**
 *      （`canvas-search-result-node_tadm1nyykc`，批次 200 已证明六档逐字同一节点）；
 *   ④ 每档**连采 6 帧**、按立规 76 报「6 帧去重后剩几个值」；
 *   ⑤ 每档带**有效性断言**（点之前必须读得到那一行、输入框的值必须等于搜索词，
 *      —— 批次 203 c 轮踩过 `nativeSet` 让 React 受控状态脱节的坑）。
 *
 * 🆕 顺带找一个「有没有侧栏在断点处出现/消失」的判别证据：`.react-flow` 的屏上盒子。
 *    如果断点真的是布局变化，那 `.react-flow` 的 x/宽 应该在断点处跳一下。
 *
 * 只读：不新建/删除节点，不生成，不下载。
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const 搜索词 = '音频';
const 目标 = 'canvas-search-result-node_tadm1nyykc';   // 批次 200：六档逐字同一节点
const H = 720;
const 宽集 = [];
for (let w = 1200; w <= 1280; w += 4) 宽集.push(w);

const log = (...a) => console.log(a.join(' '));
const out = {
  轮次: 'b205a',
  目标testid: 目标,
  高度固定: H,
  宽集,
  断点线索: '批次 200：ty ≈ 0.504×高 + C，C 分两支（1000/1200 宽 = −407.435；1280 三档 + 1600 = −508）',
  档: {},
};

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const 共享页 = ctx.pages().find((x) => x.url().includes('ai-canvas'));
out.共享页_前 = await 共享页.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);

for (const w of 宽集) {
  const p = await ctx.newPage();
  try {
    await p.setViewportSize({ width: w, height: H });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(4500);

    // —— 布局判别证据（不点任何东西，先读）——
    const 布局 = await p.evaluate(() => {
      const rf = document.querySelector('.react-flow');
      const r = rf ? rf.getBoundingClientRect() : null;
      return {
        reactFlow: r ? [r.x, r.y, r.width, r.height].map(Math.round) : null,
        侧栏数: document.querySelectorAll('aside, [data-testid*="sidebar"], [data-testid*="side-panel"]').length,
        启动钮数: document.querySelectorAll('[data-testid="canvas-panel-launcher"]').length,
      };
    });

    // —— 开搜索面板 ——
    const 搜索钮 = await p.evaluate(() => {
      const e = document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]')
        || Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '搜索');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    });
    if (!搜索钮) { out.档[w] = { 无效臂: '找不到搜索钮' }; await p.close(); continue; }
    await p.mouse.click(搜索钮[0], 搜索钮[1]);
    await p.waitForTimeout(1500);

    // 🔴 输入：必须 focus()+select()+Backspace（203 c 轮教训：nativeSet 会让 React 受控状态脱节）
    const 输入框 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      if (!e) return null;
      e.focus(); e.select();
      return { 已有值: e.value };
    });
    if (!输入框) { out.档[w] = { 无效臂: '找不到搜索输入框' }; await p.close(); continue; }
    await p.keyboard.press('Backspace');
    await p.waitForTimeout(250);
    await p.keyboard.type(搜索词, { delay: 90 });
    await p.waitForTimeout(2200);

    const 输入回读 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('input')).find((x) => (x.getAttribute('aria-label') || '').includes('搜索') || (x.placeholder || '').includes('搜索'));
      return e ? e.value : null;
    });

    // —— 臂有效性断言 ——
    const 前置 = await p.evaluate((tid) => {
      const e = document.querySelector(`[data-testid="${tid}"]`);
      if (!e) return { 存在: false, 现存: Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).slice(0, 5).map((x) => x.getAttribute('data-testid')) };
      const r = e.getBoundingClientRect();
      return { 存在: true, 屏上: [r.x, r.y, r.width, r.height].map(Math.round),
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        aria: e.getAttribute('aria-label'),
        总条数: document.querySelectorAll('[data-testid^="canvas-search-result-node_"]').length };
    }, 目标);

    const 输入断言 = { 判据: `输入框回读 === "${搜索词}"`, 回读: 输入回读, 通过: 输入回读 === 搜索词 };
    if (!前置.存在 || !输入断言.通过) {
      out.档[w] = { 无效臂: !前置.存在 ? '目标行不在这一页' : `输入没进去（回读 ${JSON.stringify(输入回读)}）`, 前置, 输入断言, 布局 };
      log(`${w} ⛔ 无效臂：${!前置.存在 ? '目标行不在' : '输入没进去'}`);
      await p.close(); continue;
    }

    await p.mouse.click(前置.点[0], 前置.点[1]);
    // —— 连采 6 帧（立规 76）——
    const 帧 = [];
    for (let k = 0; k < 6; k++) {
      帧.push(await p.evaluate((tid) => {
        const id = tid.replace('canvas-search-result-node_', 'node_');
        const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
        const vp = document.querySelector('.react-flow__viewport');
        const m = vp ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
        if (!n) return { 找不到: true };
        const r = n.getBoundingClientRect();
        return { 中心: [Math.round((r.x + r.width / 2) * 10000) / 10000, Math.round((r.y + r.height / 2) * 10000) / 10000],
          vp: m ? [Number(m[1]), Number(m[2]), Number(m[3])] : null };
      }, 目标));
      await p.waitForTimeout(600);
    }
    const 末 = 帧[帧.length - 1];
    const txs = [...new Set(帧.map((f) => f.vp && f.vp[0]))];
    const tys = [...new Set(帧.map((f) => f.vp && f.vp[1]))];
    out.档[w] = {
      布局, 前置: { 总条数: 前置.总条数, aria: 前置.aria }, 输入断言,
      末, tx取值: txs, ty取值: tys,
      断言: { 判据: '6 帧去重后 tx 与 ty 各只剩 1 个值', tx收敛: txs.length === 1, ty收敛: tys.length === 1 },
    };
    log(`${w} | tx=${JSON.stringify(txs)} | ty=${JSON.stringify(tys)} | 中心X=${末.中心 && 末.中心[0]} | rf=${JSON.stringify(布局.reactFlow)} | 收敛 tx=${txs.length === 1} ty=${tys.length === 1}`);
  } catch (e) {
    out.档[w] = { 出错: e.message };
    log(`${w} 🔴 ${e.message}`);
  } finally { await p.close(); }
}

// —— 汇总：把 ty 按两支分组，找跳变点 ——
const 有读数 = Object.entries(out.档).map(([w, g]) => ({ 宽: Number(w), ...g })).filter((g) => g.末 && g.末.vp && !g.无效臂 && !g.出错);
if (有读数.length) {
  const ys = 有读数.map((g) => g.ty取值[0]).filter((v) => v !== null && v !== undefined);
  const uniq = [...new Set(ys)].sort((a, c) => a - c);
  out.ty去重 = uniq;
  // 以相邻两档差 > 20 判为「跳变」
  const 跳 = [];
  for (let i = 1; i < 有读数.length; i++) {
    const a = 有读数[i - 1], c = 有读数[i];
    const d = (c.ty取值[0] ?? 0) - (a.ty取值[0] ?? 0);
    if (Math.abs(d) > 20) 跳.push({ 从: a.宽, 到: c.宽, ty从: a.ty取值[0], ty到: c.ty取值[0], 差: Math.round(d * 1000) / 1000 });
  }
  out.跳变 = 跳;
  out.有效档数 = 有读数.length;
  out.无效档数 = Object.keys(out.档).length - 有读数.length;
}
fs.writeFileSync('/tmp/b205a.json', JSON.stringify(out, null, 1));
log(`\n写入 /tmp/b205a.json ｜ 有效 ${out.有效档数} 档 ／ 无效 ${out.无效档数} 档`);
log(`ty 去重后剩 ${(out.ty去重 || []).length} 个值：${JSON.stringify(out.ty去重)}`);
log(`跳变：${JSON.stringify(out.跳变)}`);
process.exit(0);
