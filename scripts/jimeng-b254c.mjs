/**
 * 批次 254 · 第三步：**把「被 UI 遮住的那部分」量出来，和 412 / 532 当面对账**。
 *
 * 📌 前两步已经排除掉两种读法：
 *   ① `412` 不是「画布容器净宽」—— 7 个面板开关逐个点开点关，`rf__wrapper` 恒 = 视口宽；
 *   ② `412` 不是「某块浮层的宽度/位置」—— 侧车、侧车启动、顶栏都随 `w` 变。
 *   🔴 但还剩**最宽容的一种读法**：`412` = 视口里**被 UI 遮住的总宽度**
 *   （左栏 + 导航坞 + 侧车 + 边距…随便怎么加）。
 *
 * 📌 所以本步**不去猜加法**，直接量一个不依赖任何猜测的量：
 *   `遮住宽 = 所有 chrome 元素与视口 [0, innerW] 的并集宽度`。
 *   然后对账 `遮住宽` 随 `w` 怎么变、`412`/`532` 怎么变。
 *
 * 📌 判据（先写死）：
 *   · 若 `遮住宽` 逐字恒定且 ≠ `412`/≠`532` ⇒ 遮住宽这条线也断了；
 *   · 若 `遮住宽` 随 `w` 变而 `412` 不变 ⇒ **直接排除**；
 *   · 若某档 `遮住宽` 恰等于 `412` 或 `532` ⇒ 记为**待复现的巧合**，不当机制。
 *
 * 🔴 纪律：一个控件都不点；只开新页、只读几何；不建不删不上传不生成不扣费。
 *
 * 用法：node scripts/jimeng-b254c.mjs      （读数落盘 /tmp/b254c.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B254C_OUT || '/tmp/b254c.json';
const 高 = 720;
const 宽表 = [400, 460, 500, 512, 632, 692, 800, 1100];

const log = (...a) => console.log(a.join(' '));

const 量 = () => {
  const 视口W = window.innerWidth;
  // 🔴 chrome 清单**写死并记进读数**：判定必须能被人复核，不能靠"挑出来的那些"
  const 名单 = [
    ['canvas-fixed-toolbar-left-rail', '左侧工具栏'],
    ['canvas-navigation-dock', '左下导航坞'],
    ['canvas-feature-sidecar', '右侧 Agent 侧车'],
    ['canvas-sidecar-launchers', '右下侧车启动钮'],
    ['canvas-top-bar', '顶栏'],
    ['canvas-top-bar-actions', '顶栏右侧动作区'],
    ['canvas-panel-launcher', '顶栏面板启动钮'],
    ['canvas-account-surface', '顶栏账号区'],
  ];
  const 清单 = 名单.map(([sel, 名]) => {
    const e = document.querySelector(`[data-testid="${sel}"]`);
    if (!e) return { 名, 缺: true };
    const b = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    return {
      名,
      x: Math.round(b.x), 右: Math.round(b.right), w: Math.round(b.width),
      在视口内: b.right > 0 && b.left < 视口W,
      遮挡可见: b.right > 0 && b.left < 视口W && cs.visibility !== 'hidden' && cs.display !== 'none',
      视口内部分: [Math.max(0, Math.round(b.left)), Math.min(视口W, Math.round(b.right))],
    };
  });
  // 📌 并集宽度：把每块的「视口内部分」合并去重再量总长
  const 段 = 清单.filter((c) => c.视口内部分 && c.视口内部分[1] > c.视口内部分[0]).map((c) => c.视口内部分);
  const 并 = [];
  for (const s of 段) {
    if (!并.length || s[0] > 并[并.length - 1][1]) 并.push([...s]);
    else 并[并.length - 1][1] = Math.max(并[并.length - 1][1], s[1]);
  }
  const 遮住宽 = 并.reduce((a, s) => a + (s[1] - s[0]), 0);
  const 视口容器 = document.querySelector('[data-testid="rf__wrapper"]');
  const cb = 视口容器 ? 视口容器.getBoundingClientRect() : null;
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  return {
    视口W,
    容器宽: cb ? Math.round(cb.width) : null,
    scale: m ? Number(m[1]) : null,
    清单,
    并集段: 并,
    遮住宽,
    遮住宽序列: 并.map((s) => `${s[0]}-${s[1]}`).join(','),
    节点数: document.querySelectorAll('.react-flow__node').length,
  };
};

const out = { 轮次: 'b254c', 高, 宽表, 行: [] };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];

for (const 宽 of 宽表) {
  const p = await ctx.newPage();
  const 记 = { 宽, 对账: { 减412: 宽 - 412, 减532: 宽 - 532 } };
  try {
    await p.setViewportSize({ width: 宽, height: 高 });
    await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await p.waitForSelector('.react-flow__node', { timeout: 45000 });
    await p.waitForTimeout(5500);
    Object.assign(记, await p.evaluate(量));
    记.对账.遮住宽等于412 = 记.遮住宽 === 412;
    记.对账.遮住宽等于532 = 记.遮住宽 === 532;
    log(`【w=${宽}】容器宽=${记.容器宽} 遮住宽=${记.遮住宽}（${记.遮住宽序列}）`
      + ` 412→${记.对账.减412} 532→${记.对账.减532}`
      + `${记.对账.遮住宽等于412 ? ' 🔴遮住宽==412' : ''}${记.对账.遮住宽等于532 ? ' 🔴遮住宽==532' : ''}`);
    for (const c of 记.清单) {
      if (c.缺) { log(`    （${c.名} 在本档不存在）`); continue; }
      log(`    ${c.名}: x=${c.x}..${c.右} w=${c.w} ${c.在视口内 ? '视口内' : '视口外'}`
        + `${c.视口内部分[1] > c.视口内部分[0] ? ` 视口内部分=${c.视口内部分[1] - c.视口内部分[0]}` : ' 视口内部分=0'}`);
    }
  } catch (e) {
    记.错误 = e.message;
    log(`🔴 w=${宽} ${e.message}`);
  } finally {
    try { await p.close(); } catch (e) { /* 忽略 */ }
    out.行.push(记);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
  }
}

const 序 = out.行.filter((r) => !r.错误);
const 遮 = 序.map((r) => r.遮住宽);
out.遮住宽唯一 = [...new Set(遮)];
out.遮住宽恒定 = out.遮住宽唯一.length === 1;
out.等于412的档 = 序.filter((r) => r.遮住宽 === 412).map((r) => r.宽);
out.等于532的档 = 序.filter((r) => r.遮住宽 === 532).map((r) => r.宽);
log('=== 对账 ===');
log(`遮住宽序列 = ${JSON.stringify(遮)}（唯一值 ${JSON.stringify(out.遮住宽唯一)}）`);
log(`遮住宽逐字恒定？ ${out.遮住宽恒定 ? '是' : '否'}`);
log(`遮住宽恰等于 412 的档：${JSON.stringify(out.等于412的档)}；恰等于 532 的档：${JSON.stringify(out.等于532的档)}`);
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
log('写入 ' + OUT);
// 🔴 不要 `b.close()`：那会把无头浏览器一起关掉（批次 249 踩过）
process.exit(0);