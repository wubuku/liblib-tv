// Batch P9 —— 点开折叠的「高级设置」，把三个滑杆拍下来。
//
// batchP8 的祖先链把真相钉死了：
//   #5 <DIV class="min-h-0 overflow-hidden"  rect=[391,658,658,0]  scrollH/clientH = 145 / 0
//   #6 <DIV class="grid transition-[grid-template-rows] ...">
// 高度 0、内容 145、overflow hidden，外层是 grid-template-rows 过渡 ——
// 这是 `0fr → 1fr` 的经典折叠手法。**「高级设置」确实是可折叠分区，当前是折叠态。**
//
// 所以手册原来那句「音频节点点了会展开 3 滑杆」**本来就是对的**，
// 是我前面四轮把点击坐标打到了 y=809 / y=830（视口只有 810 高）才误判成「点了没反应」。
//
// 这轮：先把节点摆到视口上半部让「高级设置」标题**一定在视口内**，
// 按文案精确定位那个标题 div，点它，验 clientHeight 0 → 145，滑杆三兄弟全部可见。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchP9';
const { browser, page } = await launch();

/** 折叠容器（grid-template-rows 那层）+ 它的实时高度 + 三个滑杆的可见性。 */
const probe = () => page.evaluate(() => {
  const s = document.querySelector('[class*="mantine-Slider-root"]');
  if (!s) return { ok: false, why: '页面上没有滑杆' };
  // 往上找那层 min-h-0 overflow-hidden
  let box = s.parentElement, clip = null;
  for (let i = 0; i < 12 && box; i += 1) {
    if (/overflow-hidden/.test(box.className || '')) { clip = box; break; }
    box = box.parentElement;
  }
  // 「高级设置」标题：先试 clip 的前一个兄弟（同一折叠块的惯例写法），
  // 失败就**全页按文案精确定位** —— 兄弟关系并不保证成立，第一版就是这么漏掉的。
  let header = null;
  if (clip) {
    let h = clip.previousElementSibling;
    while (h && !/高级设置/.test(h.innerText || '')) h = h.previousElementSibling;
    if (h) header = h;
  }
  if (!header) {
    const exact = [...document.querySelectorAll('div,span,button,label')]
      .filter((e) => (e.innerText || e.textContent || '').trim() === '高级设置');
    // 取最深的那个（叶子），它的框最贴近实际可点区域
    if (exact.length) {
      exact.sort((a, b) => a.querySelectorAll('*').length - b.querySelectorAll('*').length);
      header = exact[0];
    }
  }
  const cr = clip ? clip.getBoundingClientRect() : null;
  const hr = header ? header.getBoundingClientRect() : null;
  const sliders = [...document.querySelectorAll('[class*="mantine-Slider-root"]')].map((e) => {
    const b = e.getBoundingClientRect();
    return { y: Math.round(b.y), bottom: Math.round(b.bottom), x: Math.round(b.x), w: Math.round(b.width),
      inViewport: b.y >= 0 && b.bottom <= window.innerHeight, fullyInsideClip: cr ? b.bottom <= cr.bottom + 2 : null };
  }).sort((a, b) => a.y - b.y);
  return {
    ok: true,
    clipClass: clip ? (clip.className || '').toString().slice(0, 40) : null,
    clipClientH: clip ? clip.clientHeight : null, clipScrollH: clip ? clip.scrollHeight : null,
    clipRect: cr ? [Math.round(cr.x), Math.round(cr.y), Math.round(cr.width), Math.round(cr.height)] : null,
    headerText: header ? (header.innerText || '').replace(/\s+/g, ' ').trim() : null,
    headerRect: hr ? [Math.round(hr.x), Math.round(hr.y), Math.round(hr.width), Math.round(hr.height)] : null,
    headerInViewport: hr ? hr.y >= 0 && hr.bottom <= window.innerHeight : false,
    headerCursor: header ? getComputedStyle(header).cursor : null,
    sliders,
    allSlidersVisible: sliders.length > 0 && sliders.every((x) => x.inViewport && x.fullyInsideClip),
    viewportH: window.innerHeight,
  };
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '把「高级设置」标题弄进视口再点，验 clientHeight 0 → 145' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  // 放在靠上的位置：参数面板挂在下面，节点越高，整块越容易全部进视口
  await page.mouse.dblclick(700, 130); await page.waitForTimeout(1200);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText('音频', { exact: false }).first().click({ timeout: 8000 });
  await page.waitForTimeout(2800);
  await fitView(page, 1);
  for (let i = 0; i < 5; i += 1) { await page.keyboard.press('Meta+-'); await page.waitForTimeout(650); }
  await page.waitForTimeout(1200);
  // 再往上平移，确保「高级设置」标题落在视口内
  for (let k = 0; k < 4; k += 1) {
    const p = await probe();
    if (p.ok && p.headerInViewport) { console.log(`平移 ${k} 次后标题已进视口: ${JSON.stringify(p.headerRect)}`); break; }
    await page.keyboard.down('Space');
    await page.mouse.move(300, 600); await page.mouse.down(); await page.waitForTimeout(180);
    await page.mouse.move(300, 480, { steps: 8 }); await page.mouse.up(); await page.keyboard.up('Space');
    await page.waitForTimeout(1300);
  }

  const before = await probe();
  console.log('\n点之前:', JSON.stringify(before, null, 1));
  await shot(page, 'M-28-音频节点-高级设置折叠态.png');

  if (!before.ok || !before.headerRect) throw new Error('没定位到「高级设置」标题：' + JSON.stringify(before));
  if (!before.headerInViewport) throw new Error(`「高级设置」标题 ${JSON.stringify(before.headerRect)} 不在视口内，点不到`);

  const [hx, hy] = [before.headerRect[0] + before.headerRect[2] / 2, before.headerRect[1] + before.headerRect[3] / 2];
  await page.mouse.click(Math.round(hx), Math.round(hy));
  await page.waitForTimeout(1400);
  const mid = await probe();
  await page.waitForTimeout(1600);
  const after = await probe();
  await shot(page, 'M-24-音频节点-高级设置三滑杆.png');
  console.log('\n点之后:', JSON.stringify({ clipClientH: after.clipClientH, clipScrollH: after.clipScrollH, sliders: after.sliders, all: after.allSlidersVisible }, null, 1));

  const verdict = after.clipClientH > before.clipClientH
    ? `**折叠容器高度 ${before.clipClientH} → ${after.clipClientH}px，分区确实展开了**`
    : `**点完高度没变（${before.clipClientH} → ${after.clipClientH}）**`;
  await logStep(B, { id: 'P9-expand-advanced', title: '音频节点「高级设置」：点开折叠分区，三个滑杆现身',
    target: `点「高级设置」标题 (${Math.round(hx)},${Math.round(hy)})，cursor=${before.headerCursor}`,
    evidence: { before, mid, after },
    visible_text: `${verdict}。折叠容器 class=${before.clipClass}，scrollH 恒为 ${after.clipScrollH}；` +
      `「高级设置」标题 ${JSON.stringify(before.headerRect)}；三个滑杆点后位置 ${JSON.stringify(after.sliders.map((s) => [s.y, s.inViewport, s.fullyInsideClip]))}；` +
      `**三个滑杆是否全部可见 ${after.allSlidersVisible}**（视口高 ${after.viewportH}）`,
    shot: 'M-24-音频节点-高级设置三滑杆.png' });
  console.log('\n判定:', verdict, ' 三滑杆全可见:', after.allSlidersVisible);
  console.log('节点:', await nodeCount(page));
} finally {
  await browser.close();
}
