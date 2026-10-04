// Batch EV-2：⭐⭐⭐ 把网格的**真实步长**算出来 —— 这是 Batch EH「猜步长」失败的根因。
//
// EV-1 的判据（枚举 CSS background-image）读出 17 个，**全是 TV Director 那个 orb**，
//   一个网格都没有。⛔ 读到 0 先怀疑判据：网格不是 CSS 背景，
//   而是 `<svg class="react-flow__background">` 里的 `<pattern>`。EV-1 的兜底枚举抓到了它：
//   `svg.react-flow__background` [0,0,1440,810]，子元素 2 个；
//   里面是 `<pattern class="react-flow__background-pattern dots">`。
//
// 本轮做的事：
//   ① 把这个 pattern / circle 的**全部几何属性**倒出来（不预设属性名）。
//   ② ⭐ 算出**画布坐标系下的网格步长**（pattern 的 width/height 会被 zoom 缩放，
//      所以要拿屏幕像素 ÷ zoom 反推），并和视口变换交叉验算。
//   ③ ⭐⭐ 关键一步：**直接从渲染出来的圆点位置反推间距** ——
//      枚举页面上所有 `<circle>` 的实际屏幕坐标，算相邻两点的屏幕距离。
//      这是**不依赖任何属性名**的判据，两条路对上了才算数。
//
// ⛔ 本轮仍然**不动任何节点**。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEV2.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const browser = await launch();
const page = browser.page;
try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  // ════════ ① pattern / circle 的全量属性 ════════
  const 网格属性 = await page.evaluate(() => {
    const svg = document.querySelector('svg.react-flow__background');
    if (!svg) return { 找到: false };
    const 全 = (e) => {
      const o = {};
      for (const a of e.attributes) o[a.name] = a.value;
      return o;
    };
    return {
      找到: true,
      svg: 全(svg),
      子: [...svg.children].map((c) => ({
        标签: c.tagName,
        属性: 全(c),
        子: [...c.children].map((g) => ({ 标签: g.tagName, 属性: 全(g), 子数: g.children.length })),
      })),
    };
  });
  记('网格属性：' + JSON.stringify(网格属性, null, 1));
  结果.读数.网格属性 = 网格属性;

  // ════════ ② 视口变换（用来把屏幕像素换算回画布单位）═══════
  const 视口 = await page.evaluate(() => {
    const vp = document.querySelector('.react-flow__viewport');
    const t = getComputedStyle(vp).transform;
    const m = /matrix\(([^)]+)\)/.exec(t);
    const n = m ? m[1].split(',').map(Number) : null;
    return { transform: t, zoom: n ? n[0] : null, pan: n ? [n[4], n[5]] : null };
  });
  记('视口：' + JSON.stringify(视口));
  结果.读数.视口 = 视口;

  // ════════ ③ ⭐ 从「实际渲染出来的圆点」反推屏幕间距 ════════
  // 这条路完全不依赖属性名：只要有 circle，就量它们的 cx/cy，算差。
  const 圆点 = await page.evaluate(() => {
    const out = [];
    for (const c of document.querySelectorAll('svg.react-flow__background circle')) {
      out.push({
        cx: parseFloat(c.getAttribute('cx')),
        cy: parseFloat(c.getAttribute('cy')),
        r: parseFloat(c.getAttribute('r')),
        fill: c.getAttribute('fill'),
        stroke: c.getAttribute('stroke'),
        祖先pattern: (() => { let p = c.parentElement; return p ? String(p.getAttribute('class') || p.tagName) : null; })(),
        祖先svg: (() => { let p = c; while (p && p.tagName !== 'svg') p = p.parentElement; return p ? String(p.getAttribute('class')) : null; })(),
      });
    }
    return { 数量: out.length, 样本: out.slice(0, 6) };
  });
  记('圆点：' + JSON.stringify(圆点, null, 1));
  结果.读数.圆点 = 圆点;

  // ════════ ④ 用 <pattern> 的 width/height 算屏幕步长，再除 zoom ════════
  const 算步长 = await page.evaluate(() => {
    const pat = document.querySelector('pattern.react-flow__background-pattern, .react-flow__background pattern');
    if (!pat) return { 找到: false };
    const w = parseFloat(pat.getAttribute('width'));
    const h = parseFloat(pat.getAttribute('height'));
    const pt = pat.getAttribute('patternTransform');
    const u = pat.getAttribute('patternUnits');
    // patternTransform 里通常带 scale(zoom) 和 translate(offset)
    let scale = null, tx = null, ty = null;
    if (pt) {
      const sm = /scale\(([-\d.]+)\)/.exec(pt);
      if (sm) scale = parseFloat(sm[1]);
      const tm = /translate\(([-\d.]+)[ ,]+([-\d.]+)\)/.exec(pt);
      if (tm) { tx = parseFloat(tm[1]); ty = parseFloat(tm[2]); }
    }
    return { 找到: true, width: w, height: h, patternTransform: pt, patternUnits: u, scale, tx, ty };
  });
  记('算步长：' + JSON.stringify(算步长));
  结果.读数.算步长 = 算步长;

  // ════════ ⑤ 像素级取证：放大截一块画布空白处，肉眼数点距 ════════
  // 裁一小块纯空白（没有节点的地方），点距一眼能看出来。
  const vp = await page.$('.react-flow__viewport');
  if (vp) {
    const bb = await vp.boundingBox();
    if (bb) {
      await page.screenshot({
        path: EVID + 'ev2-网格左上角.png',
        clip: { x: Math.max(0, bb.x + 6), y: Math.max(0, bb.y + 6), width: 320, height: 200 },
      });
      记('已拍 ev2-网格左上角.png（320×200 CSS px，看点距最直观）');
    }
  }

  // ════════ ⑥ 当前网格吸附是开还是关（枚举，不按名查）═══════
  const 底栏 = await page.evaluate(() => {
    const out = [];
    for (const e of document.querySelectorAll('button')) {
      const r = e.getBoundingClientRect();
      if (r.top < 740 || r.bottom > 810 || r.left > 340) continue;
      if (e.querySelector('button')) continue;
      out.push({
        aria: e.getAttribute('aria-label'),
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        svg数: e.querySelectorAll('svg').length,
        背景: getComputedStyle(e).backgroundColor,
      });
    }
    return out;
  });
  记('底栏：' + JSON.stringify(底栏));
  结果.读数.底栏 = 底栏;

  记('⭐⭐ 收尾坐标复核：' + JSON.stringify(await 核对坐标(page)));
  结果.收尾 = { 偏差: await 核对坐标(page), 已渲染节点数: Object.keys(await 读全部坐标(page)).length };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  落盘(结果);
  await browser.browser.close();
  console.log('\n=== 已写 tools/batchEV2.json ===');
}
