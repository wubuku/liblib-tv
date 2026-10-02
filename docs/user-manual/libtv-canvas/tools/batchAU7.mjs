// Batch AU7 —— 用**拖拽**把节点移进视口，拿到能当插图的完整面板。
//
// AU6 的两条路都不通，而且第二件坏事反倒帮了忙：
//   · 方向键 `movedByKeys: false` —— 节点**不可键盘移动**（或需要先按 `Tab` 聚焦）
//   · `⌘0` 也没用：只把面板 x0 从 -209 挪到 -197
//
// 但它量出了一个决定性的几何关系：
//   节点 rect      = [48, 48, 145, 145]  → 中心 x = 120
//   面板 panelUnion = [-209, 26, 660, 506] → 中心 x = **121**
//   **面板以节点为中心居中，宽度 660 比节点本身（145）宽得多，两侧各溢出 257px。**
//
// 所以解法不是「把节点挪进视口」，而是「把节点挪到**视口中心**」——
// 节点在 x≈330 时，面板就是 [0, 660]，整块都在屏幕里。
//
// 拖拽要点：按下的那个点必须落在**节点本体**上，不能落在参数面板上
// （AU6 的视频节点就是 `hitsNode: false` —— 那个点上盖着别的东西）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';

const SPACE = '10354929';
const B = 'batchAU7';
const { browser, page } = await launch();

const geom = () => page.evaluate(() => {
  const n = [...document.querySelectorAll('.react-flow__node.selected')][0];
  if (!n) return { err: '没有选中节点' };
  const nr = n.getBoundingClientRect();
  let x0 = nr.x, y0 = nr.y, x1 = nr.right, y1 = nr.bottom;
  for (const e of n.querySelectorAll('*')) {
    const q = e.getBoundingClientRect();
    if (q.width < 1 || q.height < 1 || q.bottom < -200 || q.top > 2400) continue;
    x0 = Math.min(x0, q.x); y0 = Math.min(y0, q.y); x1 = Math.max(x1, q.right); y1 = Math.max(y1, q.bottom);
  }
  return { nodeRect: [Math.round(nr.x), Math.round(nr.y), Math.round(nr.width), Math.round(nr.height)],
    panelUnion: [Math.round(x0), Math.round(y0), Math.round(x1 - x0), Math.round(y1 - y0)],
    fullyVisible: x0 >= 0 && y0 >= 0 && x1 <= 1440 && y1 <= 810,
    title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24) };
});
/** 找一个**确实落在节点本体上**的按下点。 */
const grabPoint = () => page.evaluate(() => {
  const n = [...document.querySelectorAll('.react-flow__node.selected')][0];
  if (!n) return { err: '没有选中节点' };
  const r = n.getBoundingClientRect();
  // 在节点内部**网格采样**，挑第一个「点上确实是节点自己」的位置
  for (const fx of [0.5, 0.35, 0.65, 0.2, 0.8]) {
    for (const fy of [0.5, 0.3, 0.7]) {
      const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
      if (cx < 5 || cx > 1435 || cy < 60 || cy > 780) continue;
      const on = document.elementFromPoint(cx, cy);
      if (on && n.contains(on) && !on.closest('[class*="Popover"],[class*="Menu"]')) {
        return { cx: Math.round(cx), cy: Math.round(cy), fx, fy,
          on: on.tagName + '.' + (on.className || '').toString().slice(0, 40) };
      }
    }
  }
  return { err: '节点内部找不到可按下的点（都被挡住了）',
    nodeRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
});
async function dragBy(dx, dy) {
  const g = await grabPoint();
  if (g.err) return g;
  await page.mouse.move(g.cx, g.cy);
  await page.mouse.down();
  for (let i = 1; i <= 12; i += 1) {
    await page.mouse.move(g.cx + (dx * i) / 12, g.cy + (dy * i) / 12);
    await page.waitForTimeout(70);
  }
  await page.mouse.up();
  await page.waitForTimeout(1800);
  return { grabbed: g, moved: [dx, dy] };
}
async function selectNode(titlePart) {
  const plan = await page.evaluate((t) => {
    const n = [...document.querySelectorAll('.react-flow__node')]
      .find((x) => (x.innerText || '').includes(t) && !(x.className || '').includes('selected'));
    if (!n) return { err: '视口里没有未选中的「' + t + '」' };
    const r = n.getBoundingClientRect();
    // 先点一下**先取消上一个选中**，再点它
    for (const [fx, fy] of [[0.5, 0.4], [0.35, 0.5], [0.65, 0.5], [0.5, 0.7]]) {
      const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
      if (cx < 5 || cx > 1435 || cy < 60 || cy > 780) continue;
      const on = document.elementFromPoint(cx, cy);
      if (on && n.contains(on)) return { cx: Math.round(cx), cy: Math.round(cy) };
    }
    return { err: '节点内部没有可点的点' };
  }, titlePart);
  if (plan.err) return plan;
  await page.mouse.click(plan.cx, plan.cy); await page.waitForTimeout(3200);
  return plan;
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '拖拽把节点挪到视口中心，让 660 宽的参数面板整块进屏' });

  const out = {};
  for (const [key, title] of [['audio', '音频节点'], ['video', '视频节点']]) {
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(900);
    out[key] = { sel: await selectNode(title) };
    if (out[key].sel.err) { console.log(`AU7 ${title}:`, out[key].sel.err); continue; }
    out[key].before = await geom();
    console.log(`AU7 ${title} 拖前:`, JSON.stringify(out[key].before));

    // 目标：节点中心落到视口中心 (720, 400)
    const nr = out[key].before.nodeRect;
    const nodeCx = nr[0] + nr[2] / 2, nodeCy = nr[1] + nr[3] / 2;
    let dx = 720 - nodeCx, dy = 400 - nodeCy;
    out[key].target = { dx: Math.round(dx), dy: Math.round(dy) };
    out[key].drag1 = await dragBy(dx, dy);
    out[key].after = await geom();
    console.log(`AU7 ${title} 拖后:`, JSON.stringify(out[key].after), '| 完整可见?', out[key].after.fullyVisible);

    // 还差一点就再拖一次
    if (!out[key].after.fullyVisible) {
      const nr2 = out[key].after.nodeRect;
      const cx2 = nr2[0] + nr2[2] / 2, cy2 = nr2[1] + nr2[3] / 2;
      const u = out[key].after.panelUnion;
      // 面板左溢出就右移、右溢出就左移；下溢出就上移
      const ddx = (u[0] < 0 ? -u[0] : 0) - (u[0] + u[2] > 1440 ? u[0] + u[2] - 1440 : 0);
      const ddy = (u[1] < 0 ? -u[1] : 0) - (u[1] + u[3] > 810 ? u[1] + u[3] - 810 : 0);
      out[key].drag2 = await dragBy(Math.round(ddx || 720 - cx2), Math.round(ddy || 400 - cy2));
      out[key].after2 = await geom();
      console.log(`AU7 ${title} 再拖后:`, JSON.stringify(out[key].after2), '| 完整可见?', out[key].after2.fullyVisible);
    }
    await shot(page, `M-14${key === 'video' ? 4 : 6}-${title}-面板完整.png`);
    out[key].final = out[key].after2 || out[key].after;
  }

  await logStep(B, {
    id: 'AU7-drag-node-to-center', title: '拖拽把节点挪到视口中心，拍完整参数面板',
    target: '**先量出「面板以节点为中心居中、宽 660 比节点宽得多」**再决定往哪挪；拖拽前先找一个「点上确实是节点本体」的按下点',
    evidence: out,
    visible_text: JSON.stringify(out).slice(0, 3000),
    shot: 'M-144-视频节点-面板完整.png',
  });
  console.log('AU7 完成');
} finally {
  await browser.close();
}
