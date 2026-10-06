/**
 * 批次 254：`412` / `532` 的来源 —— 先问「`w` 有没有二义性」。
 *
 * 📌 **问题**：批次 244–253 的取景律写的是 `screen = w − 412`（窄侧）/ `w − 532`（宽侧），
 *   而 `w` 一直取 `setViewportSize` 设进去的**视口宽**。
 *   🔴 但画布真正可用的是**容器宽**（`rf__wrapper` / `canvas-main-region`），
 *   两者**默认相等、于是不可区分**。侦察（b254-recon）在 `w=1100` 上实测：
 *   `innerW = docElW = bodyW = rf__wrapper.w = pane.w = 1100`
 *   —— 左侧 `160px` 工具栏与右侧 `200px` 的 `canvas-feature-sidecar` 都**浮在上面**，
 *   没有把容器挖窄。⇒ **要么 `412` 是「视口宽减去产品级余量」，
 *   要么是「容器宽减去某个跟浮层有关的余量」——取决于有没有控件能改窄容器。**
 *
 * 📌 **本批只做一件事**：把**每一个不改内容的画布 UI 开关**逐个点开，
 *   每次都量容器宽。两种可能，**分歧点明确**：
 *   · 有开关能改窄容器 ⇒ 下一批就在「改窄后」重跑取景律，
 *     `412` 是否随之平移就是判据；
 *   · 所有开关都改不动 ⇒ **`w` 没有二义性**，`412`/`532` 只能按「视口宽 − 余量」解释，
 *     这本身就是一条值得写进手册的排除性结论（省掉后面所有"容器宽"分支）。
 *
 * 🔴 纪律：**只点「展开/收起面板、开关显示」这类控件**；
 *   **绝不点**：分享、用户菜单、资产库、上传、生成历史里的条目、任何扣费页入口；
 *   不新建、不删除、不上传、不触发生成、不点「保存到主体库」。
 *   每点一个之前先量基线，点完**必须回到基线**再点下一个（避免状态互相污染）。
 *
 * 用法：node scripts/jimeng-b254.mjs      （读数落盘 /tmp/b254.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B254_OUT || '/tmp/b254.json';

const 宽 = 1100, 高 = 720;

const log = (...a) => console.log(a.join(' '));

// 🔴 只收「展开/收起类」控件 —— 一个都不许点到会产生副作用的入口
const 杠杆表 = [
  { 键: '搜索面板', 定位: () => document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="搜索"]'), 收: 'Escape×2' },
  { 键: '生成历史面板', 定位: () => document.querySelector('[data-testid="canvas-panel-launcher"][aria-label="生成历史"]'), 收: 'Escape×2' },
  { 键: '与 AI 对话侧车', 定位: () => document.querySelector('[data-testid="canvas-sidecar-launcher"]'), 收: 'Escape×1' },
  { 键: '小地图开关', 定位: () => document.querySelector('[data-testid="canvas-display-toggle-minimap"]'), 收: '再点一次' },
  { 键: '项目抽屉', 定位: () => document.querySelector('[data-testid="canvas-project-trigger"]'), 收: 'Escape×1' },
  { 键: '节点抽屉', 定位: () => document.querySelector('[data-testid="canvas-node-summary-trigger"]'), 收: 'Escape×1' },
  { 键: '缩放读数', 定位: () => document.querySelector('[data-testid="canvas-zoom-percent"]'), 收: 'Escape×1' },
];

const 量 = () => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const r = (sel) => {
    const e = document.querySelector(sel);
    if (!e) return null;
    const b = e.getBoundingClientRect();
    return { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height) };
  };
  const 浮层 = Array.from(document.querySelectorAll(
    '[data-testid="canvas-feature-sidecar"],[data-testid="canvas-fixed-toolbar-left-rail"],'
    + '[data-testid="canvas-navigation-dock"],[data-testid="canvas-sidecar-launchers"]'))
    .map((e) => {
      const b = e.getBoundingClientRect();
      return { t: e.getAttribute('data-testid'), x: Math.round(b.x), w: Math.round(b.width) };
    });
  return {
    innerW: window.innerWidth,
    scale: m ? Number(m[1]) : null,
    主区: r('[data-testid="canvas-main-region"]'),
    容器: r('[data-testid="rf__wrapper"]'),
    pane: r('.react-flow__pane'),
    浮层,
    节点数: document.querySelectorAll('.react-flow__node').length,
    状态行: (document.body.innerText.match(/\d+ nodes, \d+ edges, \d+ selected[^\n]*/) || [])[0] || null,
    // 打开中的对话框/抽屉层（用来判断「面板到底开没开」）
    浮窗: Array.from(document.querySelectorAll('[role="dialog"],[data-testid$="panel"],[data-testid$="drawer"],[data-testid*="search-panel"]'))
      .map((e) => {
        const b = e.getBoundingClientRect();
        return { t: e.getAttribute('data-testid') || e.getAttribute('role'), w: Math.round(b.width), h: Math.round(b.height) };
      }).filter((x) => x.w > 20).slice(0, 8),
  };
};

const out = { 轮次: 'b254', 视口: [宽, 高], 基线: null, 臂: [] };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = await ctx.newPage();
try {
  await p.setViewportSize({ width: 宽, height: 高 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(6000);

  out.基线 = await p.evaluate(量);
  log('=== 基线 ===');
  log(`innerW=${out.基线.innerW} 容器=${JSON.stringify(out.基线.容器)} 主区=${JSON.stringify(out.基线.主区)}`
    + ` pane=${JSON.stringify(out.基线.pane)} 浮层=${JSON.stringify(out.基线.浮层)}`);

  const 基线容器宽 = out.基线.容器 ? out.基线.容器.w : null;

  for (const 杠 of 杠杆表) {
    const 记 = { 键: 杠.键 };
    try {
      const 点位 = await p.evaluate((k) => {
        const 表 = {
          搜索面板: '[data-testid="canvas-panel-launcher"][aria-label="搜索"]',
          生成历史面板: '[data-testid="canvas-panel-launcher"][aria-label="生成历史"]',
          '与 AI 对话侧车': '[data-testid="canvas-sidecar-launcher"]',
          小地图开关: '[data-testid="canvas-display-toggle-minimap"]',
          项目抽屉: '[data-testid="canvas-project-trigger"]',
          节点抽屉: '[data-testid="canvas-node-summary-trigger"]',
          缩放读数: '[data-testid="canvas-zoom-percent"]',
        };
        const e = document.querySelector(表[k]);
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      }, 杠.键);
      if (!点位) throw new Error('控件不存在');
      记.点位 = 点位;
      await p.mouse.click(点位[0], 点位[1]);
      await p.waitForTimeout(2600);
      记.点开 = await p.evaluate(量);

      // 📌 收干净：能用 Escape 就 Escape，开关类再点一次
      if (杠.收.includes('Escape')) {
        const n = 杠.收.includes('×2') ? 2 : 1;
        for (let i = 0; i < n; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
      }
      if (杠.收.includes('再点一次')) { await p.mouse.click(点位[0], 点位[1]); await p.waitForTimeout(1800); }
      await p.waitForTimeout(1200);
      记.收回 = await p.evaluate(量);

      const 开后宽 = 记.点开.容器 ? 记.点开.容器.w : null;
      记.点开后容器宽 = 开后宽;
      记.点开后比基线窄 = 开后宽 != null && 基线容器宽 != null ? 基线容器宽 - 开后宽 : null;
      记.收回了 = 记.收回.容器 && 记.点开.容器 ? 记.收回.容器.w === 记.点开.容器.w : null;
      记.有改窄 = typeof 记.点开后比基线窄 === 'number' && 记.点开后比基线窄 > 0;

      log(`【${杠.键}】容器 ${基线容器宽} → ${开后宽}（Δ=${记.点开后比基线窄}）`
        + ` 主区w=${记.点开.主区 ? 记.点开.主区.w : '?'}`
        + ` 浮窗=${JSON.stringify(记.点开.浮窗)} 浮层=${JSON.stringify(记.点开.浮层)}`
        + ` ｜ 收回后容器w=${记.收回.容器 ? 记.收回.容器.w : '?'} · ${记.有改窄 ? '🔴 改窄了！' : '未改窄'}`);
    } catch (e) {
      记.错误 = e.message;
      log(`🔴 ${杠.键} ${e.message}`);
    }
    out.臂.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }

  const 改窄的 = out.臂.filter((a) => a.有改窄).map((a) => a.键);
  out.结论 = 改窄的.length ? `有 ${改窄的.length} 个开关能把画布容器改窄：${改窄的.join('、')}`
    : '所有展开/收起类开关都改不动画布容器宽 ⇒ w（视口宽）没有二义性';
  log('=== 结论 ===');
  log(out.结论);
  log(`末态：${out.臂.length ? JSON.stringify(out.臂[out.臂.length - 1].收回.状态行) : '?'}`);
} catch (e) {
  out.错误 = e.message;
  log('🔴 ' + e.message);
} finally {
  try { await p.close(); } catch (e) { /* 忽略 */ }
  fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  log('写入 ' + OUT);
}
// 🔴 不要 `b.close()`：那会把无头浏览器一起关掉（批次 249 踩过）
process.exit(0);