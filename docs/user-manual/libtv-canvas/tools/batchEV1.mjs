// Batch EV-1：⭐⭐ 攻「网格吸附到底什么时候真对齐」的第一步 —— **先把网格本身读出来**。
//
// 背景：Batch EH 已经证明「网格吸附」这枚按钮**确实会翻状态**（svg 数 1 → 2），
//   但同一批也实测到「点开之后拖节点并没有对齐」，
//   用的是「4 / 8 / 10 / 20 各种步长都试一遍」这种**猜步长**的笨办法。
//   本轮改成：**先从 DOM 里把网格的绘制方式和真实步长读出来**，再谈拖拽。
//
// 为什么必须先读网格：网格画在 CSS background 里，
//   **background-size 的像素值 ÷ 缩放 = 画布坐标系里的步长**。
//   有了这个数，才能判断「落点是不是落在网格线上」——
//   之前是拿一串猜的步长去对，永远对不上就误判成「没吸附」。
//
// 本轮三件事：
//   ① 枚举全页所有「画着重复图案」的元素（渐变 / data-uri svg），把网格揪出来。
//   ② ⭐ 阳性对照：拿**节点的权威画布坐标**反推视口变换，
//      自己算出来的 zoom/pan 必须和 `.react-flow__viewport` 的 transform 吻合，
//      否则说明我读 transform 的方法有问题，后面全不可信。
//   ③ 读出网格步长（CSS px 与画布单位两套）。
//
// ⛔ 本轮**不动任何节点**，只读。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEV1.json';
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

  // ⌘0 重置视图：否则视口外的网格/节点不渲染，后面全是「读不到」
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);

  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  // ════════ ① 视口变换（.react-flow__viewport 的 transform）═══════
  const 视口 = await page.evaluate(() => {
    const vp = document.querySelector('.react-flow__viewport');
    if (!vp) return { 找到: false };
    const cs = getComputedStyle(vp);
    const pane = document.querySelector('.react-flow__pane');
    const p = pane ? getComputedStyle(pane) : null;
    return {
      找到: true,
      class: vp.className,
      transform: cs.transform,
      宽: vp.getBoundingClientRect().width,
      高: vp.getBoundingClientRect().height,
      paneTransform: p ? p.transform : null,
    };
  });
  记('视口：' + JSON.stringify(视口));
  结果.读数.视口 = 视口;

  // ════════ ② 阳性对照：用节点权威坐标反推变换 ════════
  // 节点 a 的画布坐标已知（canvas-baseline），量它的屏幕位置，
  // 两相减就能得到 pan；两节点相减就能得到 zoom。
  // ⭐ 这一步是自证：如果反推出来的 zoom 和 transform 里的对不上，说明我读错了，后面全废。
  const 节点屏 = await page.evaluate((ids) => {
    const 出 = {};
    for (const id of ids) {
      const el = document.querySelector(`[data-id="${id}"]`);
      if (!el) { 出[id] = null; continue; }
      const r = el.getBoundingClientRect();
      出[id] = { left: r.left, top: r.top, 宽: r.width, 高: r.height };
    }
    return 出;
  }, ['v-oZNpH99MtM', 'v-v2hlWY4Br3', 'b-mfkcQNULC3', 'a-THmbuJXQj4', 't-UtVx3lZmrV']);

  const 反推 = [];
  const 已知 = { 'v-oZNpH99MtM': [132, 300], 'v-v2hlWY4Br3': [-696, 300], 'b-mfkcQNULC3': [636, 300], 'a-THmbuJXQj4': [-1356, 600], 't-UtVx3lZmrV': [600, 900] };
  for (const id of Object.keys(已知)) {
    const s = 节点屏[id];
    if (!s) { 反推.push({ id, 读到了: false }); continue; }
    反推.push({ id, 读到了: true, 画布: 已知[id], 屏幕: [Math.round(s.left), Math.round(s.top)], 宽: Math.round(s.宽) });
  }
  记('节点屏幕位置（与权威画布坐标对照）：' + JSON.stringify(反推));
  结果.读数.节点屏 = 反推;

  // ════════ ③ 枚举全页「画着重复图案」的元素 ════════
  // ⭐ 不预设它叫什么名字、不预设它在哪个 class —— 全量枚举后离线找判据。
  const 图案 = await page.evaluate(() => {
    const 出 = [];
    const 全部 = document.querySelectorAll('*');
    for (const e of 全部) {
      const cs = getComputedStyle(e);
      const bi = cs.backgroundImage;
      if (!bi || bi === 'none') continue;
      const r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) continue;
      // 只留「看起来是重复图案」的：渐变、data-uri、或尺寸很大的背景
      const 像图案 = bi.includes('gradient') || bi.includes('data:image') || bi.includes('svg');
      出.push({
        tag: e.tagName,
        cls: (e.className && e.className.baseVal !== undefined ? e.className.baseVal : String(e.className || '')).slice(0, 120),
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        backgroundImage: bi.slice(0, 300),
        backgroundSize: cs.backgroundSize,
        backgroundRepeat: cs.backgroundRepeat,
        backgroundPosition: cs.backgroundPosition,
        opacity: cs.opacity,
        像图案,
        子数: e.children.length,
      });
    }
    return { 命中总数: 出.length, 像图案的: 出.filter((x) => x.像图案), 全部: 出 };
  });
  记('图案候选：命中 ' + 图案.命中总数 + ' 个，其中像重复图案的 ' + 图案.像图案的.length + ' 个');
  记('像图案的逐个：' + JSON.stringify(图案.像图案的, null, 1));
  结果.读数.图案 = 图案;

  // ════════ ④ 专门找 react-flow 自己的网格节点 ════════
  // @xyflow/react 的 <Background> 有两种画法：SVG 图案 或 CSS 渐变。
  // 这里按「祖先链里带 grid/background」来找，不靠猜 class 名。
  const RF网格 = await page.evaluate(() => {
    const 出 = [];
    for (const e of document.querySelectorAll('[class*="grid"],[class*="background"],[class*="pattern"],[class*="dot"]')) {
      const r = e.getBoundingClientRect();
      const cs = getComputedStyle(e);
      出.push({
        tag: e.tagName,
        cls: String(e.className.baseVal !== undefined ? e.className.baseVal : e.className).slice(0, 140),
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        backgroundImage: cs.backgroundImage.slice(0, 240),
        backgroundSize: cs.backgroundSize,
        子数: e.children.length,
        祖先: (() => { const a = []; let p = e.parentElement; let i = 0; while (p && i < 5) { a.push(String(p.className).split(' ')[0]); p = p.parentElement; i++; } return a; })(),
      });
    }
    return 出;
  });
  记('react-flow 网格类候选：' + JSON.stringify(RF网格, null, 1));
  结果.读数.RF网格 = RF网格;

  // ════════ ⑤ 画布几何（画一整张，方便肉眼核对网格长什么样）═══════
  await page.screenshot({ path: EVID + 'ev1-画布全景.png' });
  记('已拍 ev1-画布全景.png');

  // ════════ ⑥ 底部状态栏 / 任何写着像素或缩放的地方 ════════
  const 文本 = await page.evaluate(() => {
    const 出 = [];
    for (const e of document.querySelectorAll('div,span,p,button')) {
      if (e.children.length) continue;
      const t = (e.textContent || '').trim();
      if (!t) continue;
      if (!/^\d+(\.\d+)?\s*%?$/.test(t) && !/网格|吸附|grid/i.test(t)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) continue;
      出.push({ 文字: t, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
    }
    return 出;
  });
  记('百分比/网格相关文本：' + JSON.stringify(文本));
  结果.读数.文本 = 文本;

  记('⭐⭐ 收尾坐标复核：' + JSON.stringify(await 核对坐标(page)));
  结果.收尾 = { 真的被移动: (await 读全部坐标(page)).filter(Boolean).length, 偏差: await 核对坐标(page) };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String(e && e.stack || e);
} finally {
  落盘(结果);
  await browser.close();
}
