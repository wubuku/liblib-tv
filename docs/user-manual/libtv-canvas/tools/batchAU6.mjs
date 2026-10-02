// Batch AU6 —— 只做一件事：把节点**移进视口中央**再拍全参数面板。
//
// AU5 把读数拿到了（音频和视频都有「高级设置」，而且**默认就是展开的**），
// 但两张截图的面板都**溢出视口**：视频面板文字一直到 y=1028、音频面板 x 是负数。
// 截出来的图只能看到一半，没法当手册插图。
//
// 移位手段按可靠性排序，挨个试并**回读 rect 确认真的动了**：
//   ① 选中节点后按**方向键**（React Flow 的节点默认可键盘移动）
//   ② 不行就按住 `Shift` 拖节点本体
//   ③ 都不行就把画布缩到 50% 再 `⌘0`，让所有节点连面板一起进视口
// 判据是 `getBoundingClientRect()` 真的变小了/位置变了，不是「没报错」。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAU6';
const { browser, page } = await launch();

const rectOf = (titlePart) => page.evaluate((t) => {
  const n = [...document.querySelectorAll('.react-flow__node.selected')][0];
  if (!n) return { err: '没有选中节点' };
  // 参数面板的完整范围 = 节点元素里所有可见子元素的并集
  const nr = n.getBoundingClientRect();
  let x0 = nr.x, y0 = nr.y, x1 = nr.right, y1 = nr.bottom;
  for (const e of n.querySelectorAll('*')) {
    const q = e.getBoundingClientRect();
    if (q.width < 1 || q.height < 1) continue;
    if (q.bottom < 0 || q.top > 2000) continue;
    x0 = Math.min(x0, q.x); y0 = Math.min(y0, q.y); x1 = Math.max(x1, q.right); y1 = Math.max(y1, q.bottom);
  }
  return { nodeRect: [Math.round(nr.x), Math.round(nr.y), Math.round(nr.width), Math.round(nr.height)],
    panelUnion: [Math.round(x0), Math.round(y0), Math.round(x1 - x0), Math.round(y1 - y0)],
    fullyVisible: x0 >= 0 && y0 >= 0 && x1 <= 1440 && y1 <= 810,
    title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24) };
}, titlePart);

async function selectNode(titlePart) {
  const plan = await page.evaluate((t) => {
    const n = [...document.querySelectorAll('.react-flow__node')]
      .find((x) => (x.innerText || '').includes(t) && !(x.className || '').includes('selected'));
    if (!n) return { err: '视口里没有未选中的「' + t + '」' };
    const r = n.getBoundingClientRect();
    const cx = Math.min(Math.max(r.x + r.width / 2, 40), 1400);
    const cy = Math.min(Math.max(r.y + Math.min(r.height * 0.4, 60), 100), 700);
    const on = document.elementFromPoint(cx, cy);
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cx, cy, hitsNode: !!(on && n.contains(on)) };
  }, titlePart);
  if (plan.err) return plan;
  if (!plan.hitsNode) { plan.err = `点 (${plan.cx},${plan.cy}) 不在节点上`; return plan; }
  await page.mouse.click(plan.cx, plan.cy); await page.waitForTimeout(3200);
  return plan;
}
/** ① 方向键移位。 */
async function nudge(dir, times) {
  for (let i = 0; i < times; i += 1) {
    await page.keyboard.press(dir);
    await page.waitForTimeout(160);
  }
  await page.waitForTimeout(900);
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '把节点移进视口，让参数面板完整可见再截图' });

  const out = {};
  for (const [key, title] of [['video', '视频节点'], ['audio', '音频节点']]) {
    await page.mouse.click(120, 770).catch(() => {}); await page.waitForTimeout(1000);
    out[key] = { sel: await selectNode(title) };
    if (out[key].sel.err) { console.log(`AU6 ${title}:`, out[key].sel.err); continue; }
    out[key].before = await rectOf(title);
    console.log(`AU6 ${title} 移位前:`, JSON.stringify(out[key].before));

    // 算一下要往哪个方向挪多少
    const u = out[key].before.panelUnion;
    const needX = u[0] < 20 ? 20 - u[0] : (u[0] + u[2] > 1400 ? u[0] + u[2] - 1400 : 0);
    const needY = u[1] < 20 ? 20 - u[1] : (u[1] + u[3] > 800 ? u[1] + u[3] - 800 : 0);
    out[key].need = { needX: Math.round(needX), needY: Math.round(needY) };

    // ① 方向键：↑↓ 步长通常 1px 或 5px，Shift 加速；先试 5 次看有没有反应
    if (needX !== 0) await nudge(needX > 0 ? 'ArrowRight' : 'ArrowLeft', 6);
    if (needY !== 0) await nudge(needY > 0 ? 'ArrowDown' : 'ArrowUp', 6);
    out[key].afterKeys = await rectOf(title);
    out[key].movedByKeys = JSON.stringify(out[key].afterKeys.panelUnion) !== JSON.stringify(u);
    console.log(`AU6 ${title} 方向键后:`, JSON.stringify(out[key].afterKeys), '| 动了?', out[key].movedByKeys);

    // ② 不行就缩小画布（50%），面板跟着缩，多半能整块进来
    if (!out[key].afterKeys.fullyVisible) {
      const trig = await page.evaluate(() => {
        const e = [...document.querySelectorAll('*')].find((x) => /^\d+%$/.test((x.innerText || '').trim())
          && x.getBoundingClientRect().width < 60 && x.getBoundingClientRect().y > 700);
        if (!e) return null;
        const b = (e.closest('button,[role="button"]') || e).getBoundingClientRect();
        return { cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + b.height / 2) };
      });
      if (trig) {
        const menuOpen = () => page.evaluate(() => [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"]')]
          .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; }).length > 0);
        if (await menuOpen()) { await page.mouse.click(trig.cx, trig.cy); await page.waitForTimeout(1100); }
        if (!(await menuOpen())) { await page.mouse.click(trig.cx, trig.cy); await page.waitForTimeout(1600); }
        const it = await page.evaluate(() => {
          const m = [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"]')]
            .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; })[0];
          if (!m) return null;
          const el = [...m.querySelectorAll('button,div,li')].filter((e) => (e.innerText || '').trim() === '缩放至50%')
            .sort((a, b) => { const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
              return (ra.width * ra.height) - (rb.width * rb.height); })[0];
          if (!el) return null;
          const r = el.getBoundingClientRect();
          return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
        });
        if (it) { await page.mouse.click(it.cx, it.cy); await page.waitForTimeout(2200); }
      }
      await fitView(page, 1); await page.waitForTimeout(1800);
      out[key].afterZoom = await rectOf(title);
      console.log(`AU6 ${title} 缩放+适合屏幕后:`, JSON.stringify(out[key].afterZoom));
    }
    await shot(page, `M-14${key === 'video' ? 4 : 6}-${title}-面板完整.png`);
  }

  await logStep(B, {
    id: 'AU6-bring-panel-into-view', title: '把参数面板整块移进视口再截图',
    target: '方向键移位 → 缩到 50% + `⌘0`；每步**回读 panelUnion** 确认真的动了，不以「没报错」为准',
    evidence: out,
    visible_text: `视频：${JSON.stringify(out.video)}。音频：${JSON.stringify(out.audio)}`,
    shot: 'M-144-视频节点-面板完整.png',
  });
  console.log('AU6 完成');
} finally {
  await browser.close();
}
