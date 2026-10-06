/**
 * 批次 254 · 侦察（不测规律，只找路）：
 *   ① 量「视口宽」与「画布容器宽」是不是同一个量；
 *   ② 把可能控制左右侧栏的按钮全部列出来（`aria-label` / `data-testid` / `title` / 文案）。
 *
 * 📌 **为什么要先做这一步**：
 *   批次 244–253 的整条取景律写的是 `screen = w − 412` / `w − 532`，
 *   而 `w` 一直取的是 **`setViewportSize` 设进去的视口宽**。
 *   🔴 但即梦页面上，视口宽 **≠** 画布容器宽：左侧资源栏、右侧属性栏都从视口里挖走一块。
 *   ⇒ **`412` 到底是「视口宽减去某个横向余量」，
 *   还是「画布容器宽减去某个横向余量」，从来没有被区分过** ——
 *   这正是 `412`/`532` 两个常数来源问题的核心分歧点。
 *   两种可能给出的**下一步测法完全不同**：
 *     · 若走容器宽 ⇒ 侧栏开合会**平移全部拐点**，是极强的机制线索；
 *     · 若走视口宽 ⇒ 侧栏开合只改容器宽、**不动物理常量**，说明 `412` 是产品级固定余量。
 *   ⇒ 先量几何、再决定怎么开闸。
 *
 * 🔴 纪律：**只读 DOM 与几何，一个控件都不点**（含侧栏开关）。
 *   不新建、不删除、不上传、不触发生成、不进扣费页、不点「保存到主体库」、不分享。
 *
 * 用法：node scripts/jimeng-b254-recon.mjs      （读数落盘 /tmp/b254-recon.json）
 */
import fs from 'node:fs';
import { chromium } from 'playwright';

const URL = 'https://jimeng.jianying.com/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f';
const OUT = process.env.B254R_OUT || '/tmp/b254-recon.json';

const log = (...a) => console.log(a.join(' '));

// 🔴 侦察只在**一个**中等宽度上做：太窄会把侧栏折叠掉，横向布局与常态不同
const 宽 = 1100, 高 = 720;

const 量几何 = () => {
  const r = (e) => {
    if (!e) return null;
    const b = e.getBoundingClientRect();
    return {
      tag: e.tagName.toLowerCase(),
      cls: (e.className && typeof e.className === 'string' ? e.className : '').slice(0, 90),
      testid: e.getAttribute('data-testid') || null,
      x: Math.round(b.x), y: Math.round(b.y),
      w: Math.round(b.width), h: Math.round(b.height),
    };
  };
  const vp = document.querySelector('.react-flow__viewport');
  const m = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  return {
    innerW: window.innerWidth,
    innerH: window.innerHeight,
    docElW: document.documentElement.clientWidth,
    bodyW: document.body.clientWidth,
    scale: m ? Number(m[1]) : null,
    reactFlow: r(document.querySelector('.react-flow')),
    pane: r(document.querySelector('.react-flow__pane')),
    viewport: r(document.querySelector('.react-flow__viewport')),
    节点数: document.querySelectorAll('.react-flow__node').length,
  };
};

const 列控件 = () => Array.from(document.querySelectorAll('button,[role="button"],[data-testid]'))
  .map((e) => {
    const b = e.getBoundingClientRect();
    if (b.width < 8 || b.height < 8) return null;           // 隐形的别列
    const txt = (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 30);
    return {
      tag: e.tagName.toLowerCase(),
      aria: e.getAttribute('aria-label') || null,
      title: e.getAttribute('title') || null,
      testid: e.getAttribute('data-testid') || null,
      text: txt || null,
      cls: (typeof e.className === 'string' ? e.className : '').slice(0, 70),
      x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height),
      pressed: e.getAttribute('aria-pressed'),
      expanded: e.getAttribute('aria-expanded'),
    };
  })
  .filter(Boolean);

const out = { 轮次: 'b254-recon', 视口: [宽, 高], 几何: null, 控件: [], 侧栏候选: [] };
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const p = await ctx.newPage();
try {
  await p.setViewportSize({ width: 宽, height: 高 });
  await p.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForSelector('.react-flow__node', { timeout: 45000 });
  await p.waitForTimeout(6000);

  out.几何 = await p.evaluate(量几何);
  out.控件 = await p.evaluate(列控件);
  log('=== 几何 ===');
  log(JSON.stringify(out.几何, null, 1));
  log(`=== 可见控件 ${out.控件.length} 个；侧栏候选（aria/title/testid 里带侧栏味道的）===`);
  // 关键词命中：面板/侧栏/收起/展开/导航/资源/属性/历史/图层/工具
  const 味 = /(panel|sidebar|side-?bar|collapse|expand|toggle|drawer|nav|resource|property|layer|history|tool)/i;
  out.侧栏候选 = out.控件.filter((c) =>
    味.test(c.aria || '') || 味.test(c.title || '') || 味.test(c.testid || '')
    || 味.test(c.cls || '') || 味.test(c.text || ''));
  for (const c of out.侧栏候选) {
    log(`  [${c.x},${c.y} ${c.w}x${c.h}] aria=${JSON.stringify(c.aria)} title=${JSON.stringify(c.title)}`
      + ` testid=${JSON.stringify(c.testid)} text=${JSON.stringify(c.text)} pressed=${c.pressed} expanded=${c.expanded}`);
  }
  log(`--- 全部 ${out.控件.length} 个控件的 testid/aria（备查）---`);
  for (const c of out.控件) {
    if (c.testid || c.aria) log(`  ${JSON.stringify(c.testid)} ${JSON.stringify(c.aria)} @${c.x},${c.y}`);
  }
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