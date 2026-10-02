// Batch AU12 —— 收口前的最后一张图：**音频节点参数面板**。
//
// M-167 已经证明视频面板拍得到（Esc 关掉抽屉 + 选节点即可），这轮就照着办，只把
// `advanced` 判据从「节点子树 union」换成**面板容器本身**。
//
// 为什么要换（这轮最要紧的一处判据修正）：
//   我一直拿「`.react-flow__node` 子树里所有元素的 union」当「参数面板的位置」。
//   但子树里既有节点本体的预览区、又有溢出到各处的挂件，union 把**别的节点**也算进去了 ——
//   于是算出 `panelUnion y0=301`，而画面上工具条实际在 y≈504，**差了 203px**。
//   `elementFromPoint` 落在 732 命中 `.react-flow__pane`、拖拽也拖不动，都是这个错判据的连带后果。
//
//   正确做法就是正文第 272 行早就写下的那个 class：**面板容器 = `.node-floating-ui`**，
//   直接量它，别自己 union。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAU12';
const { browser, page } = await launch();

/** 面板 = `.node-floating-ui`，直接量它。 */
const panelGeom = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return { err: '没有选中节点' };
  const p = n.querySelector('.node-floating-ui');
  if (!p) return { err: '子树里没有 .node-floating-ui' };
  const r = p.getBoundingClientRect();
  const cs = getComputedStyle(p);
  // 面板底部一行的按钮清单（正文此前没记的那几枚）
  const bottomBtns = [...p.querySelectorAll('button,[role="button"]')]
    .map((e) => { const q = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
        text: (e.innerText || '').trim().slice(0, 8),
        rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; })
    .filter((b) => b.rect[3] > 0);
  // 「高级设置」标题 + 折叠容器，在面板坐标系里的位置
  let adv = null;
  for (const e of p.querySelectorAll('*')) {
    if ((e.textContent || '').trim() === '高级设置') {
      const q = e.getBoundingClientRect();
      const cx = q.x + q.width / 2, cy = q.y + q.height / 2;
      const on = (cx >= 0 && cy >= 0 && cx < 1440 && cy < 810) ? document.elementFromPoint(cx, cy) : null;
      adv = { rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
        inViewport: cx >= 0 && cy >= 0 && cx < 1440 && cy < 810,
        on: on ? on.tagName + '.' + (on.className || '').toString().slice(0, 40) : null,
        hits: !!(on && (on === e || e.contains(on))) };
      break;
    }
  }
  const sliders = [...p.querySelectorAll('.mantine-Slider-root')].map((e) => {
    const q = e.getBoundingClientRect();
    const row = e.closest('div');
    return { rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      value: e.querySelector('[aria-valuenow]')?.getAttribute('aria-valuenow') || null,
      label: (row ? row.textContent : '').replace(/\s+/g, ' ').trim().slice(0, 12) };
  });
  return { panelRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    panelCls: (p.className || '').toString().slice(0, 70),
    zIndex: cs.zIndex, position: cs.position,
    fullyVisible: r.x >= 0 && r.y >= 0 && r.right <= 1440 && r.bottom <= 810,
    bottomBtns, adv, sliders,
    any1fr: document.querySelectorAll('[class*="grid-rows-\\[1fr\\]"]').length,
    fullText: (p.innerText || '').replace(/\s+/g, ' ').trim() };
});

async function selectByText(t) {
  const plan = await page.evaluate((t) => {
    for (const n of document.querySelectorAll('.react-flow__node')) {
      if (!(n.innerText || '').includes(t) || n.classList.contains('selected')) continue;
      const r = n.getBoundingClientRect();
      if (r.x < 5 || r.x + r.width > 1435 || r.y < 60 || r.y + r.height > 800) continue;
      for (const [fx, fy] of [[0.5, 0.4], [0.5, 0.5], [0.35, 0.5], [0.65, 0.5], [0.5, 0.3]]) {
        const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
        const on = document.elementFromPoint(cx, cy);
        if (on && n.contains(on) && !on.closest('[class*="Popover"],[class*="Menu"],[class*="Dropdown"]')) {
          return { cx: Math.round(cx), cy: Math.round(cy),
            title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) };
        }
      }
    }
    return { err: '找不到可点的「' + t + '」' };
  }, t);
  if (plan.err) return plan;
  await page.mouse.click(plan.cx, plan.cy);
  await page.waitForTimeout(3800);
  return plan;
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1000);
  // **先 Esc 关掉 TV Director 抽屉**（AU11 新发现：Esc 有效，之前两轮是点错了按钮）
  await page.keyboard.press('Escape'); await page.waitForTimeout(1800);
  await beginBatch(B, { note: 'Esc 关抽屉 + 用 .node-floating-ui 当面板判据，拍音频面板' });

  const out = {};
  out.drawerGone = await page.evaluate(() =>
    !document.querySelector('.copilotKitMessagesContainer'));
  console.log('AU12 抽屉已关:', out.drawerGone);

  out.audio = { sel: await selectByText('音频节点') };
  console.log('AU12 选中音频:', JSON.stringify(out.audio.sel).slice(0, 300));
  if (!out.audio.sel.err) {
    out.audio.panel = await panelGeom();
    console.log('AU12 音频面板 rect:', JSON.stringify(out.audio.panel.panelRect),
      'class:', out.audio.panel.panelCls, '完全可见:', out.audio.panel.fullyVisible);
    console.log('AU12 高级设置:', JSON.stringify(out.audio.panel.adv));
    console.log('AU12 滑杆:', JSON.stringify(out.audio.panel.sliders));
    console.log('AU12 面板按钮:', JSON.stringify(out.audio.panel.bottomBtns).slice(0, 800));
    console.log('AU12 全页 grid-rows-[1fr]:', out.audio.panel.any1fr);
    console.log('AU12 面板全文:', out.audio.panel.fullText.slice(0, 300));
    await shot(page, 'M-168-音频节点-参数面板.png');
    out.audio.shot = 'M-168-音频节点-参数面板.png';
  }

  // 视频节点也用新判据量一遍，跟 M-167 的画面对齐
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  out.video = { sel: await selectByText('视频节点') };
  console.log('AU12 选中视频:', JSON.stringify(out.video.sel).slice(0, 300));
  if (!out.video.sel.err) {
    out.video.panel = await panelGeom();
    console.log('AU12 视频面板 rect:', JSON.stringify(out.video.panel.panelRect),
      '完全可见:', out.video.panel.fullyVisible);
    console.log('AU12 视频高级设置:', JSON.stringify(out.video.panel.adv));
    console.log('AU12 视频面板按钮:', JSON.stringify(out.video.panel.bottomBtns).slice(0, 900));
    console.log('AU12 视频面板全文:', out.video.panel.fullText.slice(0, 300));
    if (out.video.panel.fullyVisible) {
      await shot(page, 'M-169-视频节点-参数面板.png');
      out.video.shot = 'M-169-视频节点-参数面板.png';
    }
  }

  await logStep(B, {
    id: 'AU12-panel-geom-by-class', title: '用 .node-floating-ui 当面板判据（替掉子树 union）+ 音频面板实拍',
    target: '子树 union 会把别的节点算进来（算出的 y0 比画面上实际位置差 203px），'
      + '导致 elementFromPoint 命中 .react-flow__pane、拖拽也拖不动。正文 272 行早就写对了 class，'
      + '错的是我拿它当**线索**而没当**判据**',
    evidence: out,
    visible_text: JSON.stringify(out).slice(0, 3000),
    shot: 'M-168-音频节点-参数面板.png',
  });
  console.log('\nAU12 完成');
} finally {
  await browser.close();
}
