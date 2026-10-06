/**
 * 批次 254 · 第二步：**把 `412` 的头号机制假设直接排掉**。
 *
 * 📌 背景（b254 第一步已测实）：7 个展开/收起类开关（搜索面板 320、生成历史 320、
 *   与 AI 对话面板 398、Agent 侧车 200→**400**、小地图、项目抽屉、节点抽屉）
 *   **逐个点开点关，画布容器 `rf__wrapper` / `canvas-main-region` / `pane` 始终 = 视口宽 `1100`，`Δ=0`**。
 *   ⇒ `412` / `532` **不是「画布容器挖掉 UI 之后的净宽」**。
 *
 * 📌 那它是不是**浮层占掉的宽度**？这是最顺手的机制假设（左侧 `160px` 工具栏、
 *   右侧 `200px` 侧车，形状也吻合「常数减去两块浮层」）。
 *   🔴 但这些浮层是**响应式**的：`w=1100` 时左栏 `160px`、侧车 `200px`；
 *   而取景律里用到的 `w` 小到 `300`。若浮层宽度**随 `w` 变**，而 `412` 在
 *   `w∈[300,1100]` 整段上**逐字恒定**，两者就**不可能是同一个量**。
 *
 * 📌 判据（**先写死**）：
 *   · 若浮层宽度（或左栏右沿、侧车左沿）在不同 `w` 上**逐字不同** ⇒ `412` **不是**浮层宽度；
 *   · 若全段逐字相同 ⇒ 假设存活，下一批就该去测「它到底等于哪块」。
 *
 * 📌 纪律：每臂**一个控件都不点**，纯读 DOM 几何；只开新页、不建不删不上传不生成。
 *
 * 用法：node scripts/jimeng-b254b.mjs      （读数落盘 /tmp/b254b.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B254B_OUT || '/tmp/b254b.json';
const 高 = 720;

// 🔴 这几档**每一个都是取景律上已有的读数点**（预测可与批次 244–253 逐字对照）
const 宽表 = [300, 400, 460, 500, 632, 692, 800, 1100];

const log = (...a) => console.log(a.join(' '));

const 量 = () => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const box = (sel) => {
    const e = document.querySelector(sel);
    if (!e) return null;
    const b = e.getBoundingClientRect();
    if (b.width < 1 || b.height < 1) return null;      // display:none 之类
    return { x: Math.round(b.x), w: Math.round(b.width), h: Math.round(b.height) };
  };
  return {
    innerW: window.innerWidth,
    scale: m ? Number(m[1]) : null,
    容器: box('[data-testid="rf__wrapper"]'),
    容器右沿: (() => { const b = box('[data-testid="rf__wrapper"]'); return b ? b.x + b.w : null; })(),
    左栏: box('[data-testid="canvas-fixed-toolbar-left-rail"]'),
    左工具条: box('[data-testid="canvas-fixed-toolbar"]'),
    导航坞: box('[data-testid="canvas-navigation-dock"]'),
    底部坞: box('[data-testid="canvas-bottom-dock"]'),
    侧车: box('[data-testid="canvas-feature-sidecar"]'),
    侧车启动: box('[data-testid="canvas-sidecar-launchers"]'),
    顶栏: box('[data-testid="canvas-top-bar"]'),
    顶栏右: box('[data-testid="canvas-top-bar-actions"]'),
    节点数: document.querySelectorAll('.react-flow__node').length,
  };
};

const out = { 轮次: 'b254b', 高, 宽表, 行: [] };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const 宽 of 宽表) {
  const p = await ctx.newPage();
  const 记 = { 宽, 预测_屏上净宽: 宽 - 412 };
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(5500);
    Object.assign(记, await p.evaluate(量));
    log(`【w=${宽}】容器=${JSON.stringify(记.容器)}`
      + ` 左栏=${JSON.stringify(记.左栏)} 工具条=${JSON.stringify(记.左工具条)}`
      + ` 导航坞=${JSON.stringify(记.导航坞)} 底部坞=${JSON.stringify(记.底部坞)}`
      + ` 侧车=${JSON.stringify(记.侧车)} 侧车启动=${JSON.stringify(记.侧车启动)}`
      + ` 顶栏=${JSON.stringify(记.顶栏)} 顶栏右=${JSON.stringify(记.顶栏右)}`);
  } catch (e) {
    记.错误 = e.message;
    log(`🔴 w=${宽} ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.行.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

// 📌 判据：逐字段比「是否全段逐字相同」
const 字段 = ['容器', '左栏', '左工具条', '导航坞', '底部坞', '侧车', '侧车启动', '顶栏', '顶栏右'];
out.变化表 = {};
for (const f of 字段) {
  const 序列 = out.行.map((r) => (r[f] ? JSON.stringify(r[f]) : '无'));
  const 唯一 = [...new Set(序列)];
  out.变化表[f] = { 序列, 唯一值数: 唯一.length, 逐字恒定: 唯一.length === 1 };
}
log('=== 字段是否随 w 变化 ===');
for (const f of 字段) {
  const v = out.变化表[f];
  log(`  ${f}: ${v.唯一值数} 种取值 ${v.逐字恒定 ? '（全段恒定）' : '（随 w 变）'} ⇒ ${v.序列.join(' | ')}`);
}
const 变的 = 字段.filter((f) => !out.变化表[f].逐字恒定);
out.结论 = 变的.length
  ? `浮层/容器宽度在 w∈[300,1100] 上逐字变化的有：${变的.join('、')}；而 412 在整段上逐字恒定 ⇒ 412 不是这些 UI 占掉的宽度`
  : '所有浮层宽度全段恒定 ⇒ 假设存活';
log('=== 结论 ===');
log(out.结论);
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
// 🔴 不要 `b.close()`：那会把无头浏览器一起关掉（批次 249 踩过）
process.exit(0);