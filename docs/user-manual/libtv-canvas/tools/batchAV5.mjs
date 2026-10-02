// Batch AV5 —— 修 AV4 的两个错，并把音频节点「第三轮点不中」一次问穿。
//
// AV4 失败的两个原因，都不是产品的：
//   ① `selectByText('视频节点')` 用 `innerText.includes()` 匹配，**视口里有两个视频节点**，
//      它取到的不是我刚拖动的那个（cx=1302，靠右那个，面板右边缘 1631 已出视口）→ gear 读不到。
//      修法：**拖完用坐标点它**，别用文本再找一遍（§「页面上有同类元素时，取第一个是随机数」）。
//   ② 音频节点连续三轮点不中（AV1/AV2/AV13/AV4）。按 §「连续 N 次失败时先 dump 全部，别继续调条件」，
//      这一轮**先 dump 再决定**：把每个 `.react-flow__node` 的 rect、class、
//      以及中心点 `elementFromPoint` 命中的是谁，全列出来。
//
// 好消息：AV4 证实**拖动是有效的**（dy -173，nodeY 323 → 166），
// 所以「先取消选中再拖」这条路可以放心用 —— 面板收起后节点本体才暴露。
// 节点拖到 y=166 时，面板 y0=266，**展开后 411 高 → bottom 677 < 810，整块在屏内**。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAV5';
const { browser, page } = await launch();

/** 为什么点不中：把每个节点的 rect + 中心点命中者全列出来。 */
const whyNotClickable = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
  const on = (cx >= 0 && cy >= 0 && cx < innerWidth && cy < innerHeight) ? document.elementFromPoint(cx, cy) : null;
  const inView = r.x >= 5 && r.x + r.width <= 1435 && r.y >= 60 && r.y + r.height <= 800;
  return { id: (n.getAttribute('data-id') || n.className || '').toString().slice(0, 26),
    text: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 22),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    selected: n.classList.contains('selected'), inView,
    centerHits: on ? on.tagName + '.' + (on.className || '').toString().slice(0, 34) : null,
    centerInsideSelf: !!(on && n.contains(on)),
    whoElse: on && !n.contains(on)
      ? (on.closest('.react-flow__node') ? '另一个节点: ' + (on.closest('.react-flow__node').innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18)
        : on.tagName + '.' + (on.className || '').toString().slice(0, 30)) : null };
}));

const panelRect = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return { err: '没有选中节点' };
  const c = [...n.querySelectorAll('div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((o) => o.r.width > 400 && o.r.height > 100)
    .filter((o) => (o.e.innerText || '').includes('参考'))
    .sort((a, b) => (a.r.width * a.r.height) - (b.r.width * b.r.height))[0];
  if (!c) return { err: '没找到面板' };
  return { rect: [Math.round(c.r.x), Math.round(c.r.y), Math.round(c.r.width), Math.round(c.r.height)],
    bottom: Math.round(c.r.bottom), fullyVisible: c.r.x >= 0 && c.r.y >= 0 && c.r.right <= 1440 && c.r.bottom <= 810 };
});

const gearRect = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return null;
  const p = [...n.querySelectorAll('div')].map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((o) => o.r.width > 400 && o.r.height > 100)
    .filter((o) => (o.e.innerText || '').includes('参考'))
    .sort((a, b) => (a.r.width * a.r.height) - (b.r.width * b.r.height))[0]?.e;
  if (!p) return null;
  const g = [...p.querySelectorAll('button')].find((e) => {
    const s = e.querySelector('svg'); if (!s) return false;
    return [...s.querySelectorAll('path')].map((x) => x.getAttribute('d') || '').some((d) => d.startsWith('M14 17H5')); });
  if (!g) return null;
  const q = g.getBoundingClientRect();
  return { rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
    inView: q.x >= 0 && q.y >= 0 && q.right <= 1440 && q.bottom <= 810 };
});

async function deselect() {
  await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  await page.mouse.click(80, 120); await page.waitForTimeout(1800);
  return page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
}

/** 拖到 targetY，**返回拖后该节点自身的 rect**（后续一律用坐标点它，不再按文本找）。 */
async function dragTo(titlePart, targetY) {
  const g = await page.evaluate((t) => {
    for (const n of document.querySelectorAll('.react-flow__node')) {
      if (!(n.innerText || '').includes(t)) continue;
      const r = n.getBoundingClientRect();
      if (r.x < 5 || r.x + r.width > 1435 || r.y < 60 || r.y + r.height > 800) continue;
      for (const [fx, fy] of [[0.5, 0.5], [0.35, 0.5], [0.65, 0.5], [0.5, 0.3], [0.5, 0.7], [0.5, 0.2]]) {
        const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
        const on = document.elementFromPoint(cx, cy);
        if (on && n.contains(on) && !on.closest('[class*="Popover"],[class*="Menu"],[class*="Dropdown"]')) {
          return { cx: Math.round(cx), cy: Math.round(cy), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
        }
      }
    }
    return { err: '找不到可拖的「' + t + '」' };
  }, titlePart);
  if (g.err) return g;
  const dy = Math.round(targetY - g.rect[1]);
  await page.mouse.move(g.cx, g.cy); await page.mouse.down();
  for (let i = 1; i <= 12; i += 1) { await page.mouse.move(g.cx, g.cy + (dy * i) / 12); await page.waitForTimeout(70); }
  await page.mouse.up(); await page.waitForTimeout(2200);
  // 拖完用「离目标最近的同类节点」认回来，而不是取第一个
  const after = await page.evaluate(([t, wantY]) => {
    const cands = [...document.querySelectorAll('.react-flow__node')]
      .filter((n) => (n.innerText || '').includes(t))
      .map((n) => { const r = n.getBoundingClientRect();
        return { n, r, d: Math.abs(r.y - wantY) }; })
      .sort((a, b) => a.d - b.d);
    if (!cands.length) return { err: '拖完找不到了' };
    const { r } = cands[0];
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: (cands[0].n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 26),
      cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
  }, [titlePart, targetY]);
  return { grabbed: g, dy, after };
}

async function expandAndShoot(titlePart, shotName) {
  const o = {};
  o.deselected = await deselect();
  o.drag = await dragTo(titlePart, 150);
  console.log(`AV5 ${titlePart} 拖:`, JSON.stringify(o.drag).slice(0, 300));
  if (o.drag.err || !o.drag.after || o.drag.after.err) return o;
  // **用坐标点它**（不再 innerText 匹配）
  await page.mouse.click(o.drag.after.cx, o.drag.after.cy);
  await page.waitForTimeout(4200);
  o.panelCollapsed = await panelRect();
  o.gear = await gearRect();
  console.log(`AV5 ${titlePart} 折叠面板:`, JSON.stringify(o.panelCollapsed.rect), 'gear:', JSON.stringify(o.gear));
  if (!o.gear || !o.gear.inView) return o;
  const g = o.gear.rect;
  await page.mouse.click(g[0] + g[2] / 2, g[1] + g[3] / 2);
  await page.waitForTimeout(3000);
  o.panelExpanded = await panelRect();
  console.log(`AV5 ${titlePart} 展开面板:`, JSON.stringify(o.panelExpanded.rect), '完整?', o.panelExpanded.fullyVisible);
  if (o.panelExpanded.fullyVisible) { await shot(page, shotName); o.shot = shotName; }
  return o;
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2200);
  await beginBatch(B, { note: '拖完用坐标选（不再文本匹配）+ 先 dump 音频节点为什么点不中' });

  const out = {};
  out.dumpAtStart = await whyNotClickable();
  console.log('AV5 起始时所有节点（取消选中后）:');
  for (const n of out.dumpAtStart) {
    console.log(`  ${String(n.rect).padEnd(22)} sel=${n.selected ? 'Y' : 'N'} inView=${n.inView ? 'Y' : 'N'} selfHit=${n.centerHits ? (n.centerInsideSelf ? 'Y' : 'N') : '-'} ${n.text}  | 点心命中: ${n.centerHits} ${n.whoElse ? ' ← ' + n.whoElse : ''}`);
  }

  out.video = await expandAndShoot('视频节点', 'M-142-视频节点-高级设置展开.png');
  await deselect();
  out.dumpBeforeAudio = await whyNotClickable();
  out.audio = await expandAndShoot('音频节点', 'M-143-音频节点-高级设置展开.png');
  if (out.audio && out.audio.shot) {
    out.audio.sliders = await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node.selected');
      if (!n) return { err: '没选中' };
      return [...n.querySelectorAll('.mantine-Slider-root')].map((e) => {
        const q = e.getBoundingClientRect();
        return { rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
          now: e.querySelector('[aria-valuenow]')?.getAttribute('aria-valuenow') || null,
          max: e.querySelector('[aria-valuemax]')?.getAttribute('aria-valuemax') || null,
          label: (e.parentElement?.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 10) };
      });
    });
    console.log('AV5 音频滑杆:', JSON.stringify(out.audio.sliders));
  }

  await logStep(B, {
    id: 'AV5-coordinate-select-and-dump', title: '拖完用坐标选节点（不再按文本匹配）+ 音频节点点不中的原因',
    target: '视口里有两个视频节点时，`innerText.includes()` 取第一个就是随机数 —— '
      + 'AV4 因此拖了 A 却打开了 B。音频节点连续三轮点不中，这一轮先把 rect/命中者全 dump 出来',
    evidence: out,
    visible_text: JSON.stringify({ dump: out.dumpAtStart, video: out.video, audio: out.audio }).slice(0, 3000),
    shot: 'M-142-视频节点-高级设置展开.png',
  });
  console.log('\nAV5 完成');
} finally {
  await browser.close();
}
