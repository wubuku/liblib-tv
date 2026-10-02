// Batch AV4 —— 把「高级设置展开」的完整画面拍下来，视频和音频各一张。
//
// AV3 已经把机制坐实了（`grid-rows-[0fr]` 0px ↔ `[1fr]` 157px，是 toggle，三个开关默认全开），
// 但**图没拍好**：`dy = Math.min(-20, b.bottom - 790)` 这个式子写反了方向 ——
// 我想要 `790 - bottom`（负数），写成了 `Math.min(-20, …)`，结果只平移了 20px，
// 面板 bottom 仍在 890，**第三个开关「智能引用」落在视口外**。这种图不能进手册。
//
// 正确顺序（本轮改成这样）：
//   **点空白取消选中 → 拖节点到画面上部 → 再点它 → 再点 ⚙**
// 取消选中是关键：AU11 实测「拖不动」，是因为**参数面板盖住了节点上半部分**；
// 面板收起之后节点本体才整块暴露，`elementFromPoint` 才落在它身上。
//
// 顺带解决「音频节点一直选不中」：前几轮都是**先选了视频节点**，
// 视频面板（658 宽）正好压住两个音频节点。本轮改成**先选目标、再考虑别的**。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAV4';
const { browser, page } = await launch();

const panelRect = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return { err: '没有选中节点' };
  const c = [...n.querySelectorAll('div')]
    .map((e) => ({ e, r: e.getBoundingClientRect() }))
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
  const p = [...n.querySelectorAll('div')]
    .map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((o) => o.r.width > 400 && o.r.height > 100)
    .filter((o) => (o.e.innerText || '').includes('参考'))
    .sort((a, b) => (a.r.width * a.r.height) - (b.r.width * b.r.height))[0]?.e;
  if (!p) return null;
  const g = [...p.querySelectorAll('button')].find((e) => {
    const s = e.querySelector('svg'); if (!s) return false;
    return [...s.querySelectorAll('path')].map((x) => x.getAttribute('d') || '')
      .some((d) => d.startsWith('M14 17H5')); });
  if (!g) return null;
  const q = g.getBoundingClientRect();
  return { rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
    visible: q.width > 0 && q.height > 0 && q.y >= 0 && q.bottom <= 810 };
});

/** 点空白**取消选中**（面板随之收起，节点本体才暴露出来）。 */
async function deselect() {
  await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  await page.mouse.click(80, 120); await page.waitForTimeout(1800);
  return page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
}

/** 面板收起时拖节点到目标 y。 */
async function dragNodeToY(titlePart, targetY) {
  const g = await page.evaluate((t) => {
    for (const n of document.querySelectorAll('.react-flow__node')) {
      if (!(n.innerText || '').includes(t)) continue;
      const r = n.getBoundingClientRect();
      if (r.x < 5 || r.x + r.width > 1435 || r.y < 60 || r.y + r.height > 800) continue;
      for (const [fx, fy] of [[0.5, 0.5], [0.35, 0.5], [0.65, 0.5], [0.5, 0.3], [0.5, 0.7], [0.5, 0.2]]) {
        const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
        const on = document.elementFromPoint(cx, cy);
        if (on && n.contains(on) && !on.closest('[class*="Popover"],[class*="Menu"],[class*="Dropdown"]')) {
          return { cx: Math.round(cx), cy: Math.round(cy), nodeY: Math.round(r.y), nodeH: Math.round(r.height) };
        }
      }
    }
    return { err: '找不到可拖的「' + t + '」' };
  }, titlePart);
  if (g.err) return g;
  const dy = Math.round(targetY - g.nodeY);
  await page.mouse.move(g.cx, g.cy); await page.mouse.down();
  for (let i = 1; i <= 12; i += 1) { await page.mouse.move(g.cx, g.cy + (dy * i) / 12); await page.waitForTimeout(70); }
  await page.mouse.up(); await page.waitForTimeout(2000);
  const after = await page.evaluate((t) => {
    const n = [...document.querySelectorAll('.react-flow__node')].find((x) => (x.innerText || '').includes(t));
    return n ? Math.round(n.getBoundingClientRect().y) : null;
  }, titlePart);
  return { grabbed: g, dy, nodeYAfter: after };
}

async function selectByText(t) {
  const plan = await page.evaluate((t) => {
    for (const n of document.querySelectorAll('.react-flow__node')) {
      if (!(n.innerText || '').includes(t) || n.classList.contains('selected')) continue;
      const r = n.getBoundingClientRect();
      if (r.x < 5 || r.x + r.width > 1435 || r.y < 60 || r.y + r.height > 800) continue;
      for (const [fx, fy] of [[0.5, 0.4], [0.5, 0.5], [0.35, 0.5], [0.65, 0.5], [0.5, 0.25], [0.5, 0.3], [0.5, 0.7]]) {
        const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
        const on = document.elementFromPoint(cx, cy);
        if (on && n.contains(on) && !on.closest('[class*="Popover"],[class*="Menu"],[class*="Dropdown"]')) {
          return { cx: Math.round(cx), cy: Math.round(cy) };
        }
      }
    }
    return { err: '找不到可点的「' + t + '」' };
  }, t);
  if (plan.err) return plan;
  await page.mouse.click(plan.cx, plan.cy);
  await page.waitForTimeout(4000);
  return plan;
}

async function expandAndShoot(titlePart, shotName, logKey) {
  const o = {};
  o.deselected = await deselect();
  o.drag = await dragNodeToY(titlePart, 150);
  console.log(`AV4 ${titlePart} 拖动:`, JSON.stringify(o.drag));
  o.sel = await selectByText(titlePart);
  console.log(`AV4 ${titlePart} 选中:`, JSON.stringify(o.sel));
  if (o.sel.err) return o;
  o.panelCollapsed = await panelRect();
  o.gear = await gearRect();
  console.log(`AV4 ${titlePart} 折叠态面板:`, JSON.stringify(o.panelCollapsed.rect), 'gear:', JSON.stringify(o.gear));
  if (!o.gear) return o;
  const g = o.gear.rect;
  await page.mouse.click(g[0] + g[2] / 2, g[1] + g[3] / 2);
  await page.waitForTimeout(2800);
  o.panelExpanded = await panelRect();
  console.log(`AV4 ${titlePart} 展开后面板:`, JSON.stringify(o.panelExpanded.rect),
    '完全可见?', o.panelExpanded.fullyVisible);
  if (o.panelExpanded.fullyVisible) {
    await shot(page, shotName);
    o.shot = shotName;
  } else {
    // 这次 dy 算对：要把 bottom 拉到 800 以内
    const need = Math.round(800 - o.panelExpanded.bottom);
    o.panNeed = need;
    if (need < 0) {
      // 左键直接拖画布空白 = react-flow 默认平移
      const from = await page.evaluate(() => {
        const e = document.elementFromPoint(80, 120);
        return { tag: e ? e.tagName + '.' + (e.className || '').toString().slice(0, 40) : null };
      });
      await page.mouse.move(80, 120); await page.mouse.down();
      for (let i = 1; i <= 10; i += 1) { await page.mouse.move(80, 80 + (need * i) / 10); await page.waitForTimeout(60); }
      await page.mouse.up(); await page.waitForTimeout(1800);
      o.panFrom = from;
      o.panelAfterPan = await panelRect();
      console.log(`AV4 ${titlePart} 平移 ${need}px:`, JSON.stringify(o.panelAfterPan.rect),
        '完全可见?', o.panelAfterPan.fullyVisible);
      if (o.panelAfterPan.fullyVisible) { await shot(page, shotName); o.shot = shotName; }
    }
  }
  return o;
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2200);
  await beginBatch(B, { note: '先取消选中再拖节点，拍「高级设置展开」的完整画面（视频 + 音频）' });

  const out = {};
  out.video = await expandAndShoot('视频节点', 'M-142-视频节点-高级设置展开.png', 'video');
  out.audio = await expandAndShoot('音频节点', 'M-143-音频节点-高级设置展开.png', 'audio');

  // 音频展开后，那三个滑杆的真实状态
  if (out.audio && out.audio.shot) {
    out.audio.sliders = await page.evaluate(() => {
      const n = document.querySelector('.react-flow__node.selected');
      if (!n) return { err: '没选中' };
      return [...n.querySelectorAll('.mantine-Slider-root')].map((e) => {
        const q = e.getBoundingClientRect();
        const rowTxt = (e.closest('div[class*="flex"]')?.textContent || '').replace(/\s+/g, ' ').trim();
        return { rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
          now: e.querySelector('[aria-valuenow]')?.getAttribute('aria-valuenow') || null,
          max: e.querySelector('[aria-valuemax]')?.getAttribute('aria-valuemax') || null,
          rowText: rowTxt.slice(0, 16) };
      });
    });
    console.log('AV4 音频三个滑杆:', JSON.stringify(out.audio.sliders));
  }

  await logStep(B, {
    id: 'AV4-advanced-screenshots', title: '拍到「高级设置」展开后的完整画面（视频 / 音频各一张）',
    target: '**先点空白取消选中再拖节点** —— 面板盖着节点时是拖不动的（AU11 实测）；'
      + '平移量要按 `800 - bottom` 算（AV3 写反成 min(-20, …) 导致第三个开关落在视口外）',
    evidence: out,
    visible_text: JSON.stringify(out).slice(0, 2500),
    shot: 'M-142-视频节点-高级设置展开.png',
  });
  console.log('\nAV4 完成');
} finally {
  await browser.close();
}
