// Batch P6 —— 只为补一张「滑杆真的在画面里」的截图。
//
// batchP5 已经用坐标把结构坐实了：节点本体 [506,191,427,427]（底边 y=619），
// 参数面板 [391,639,658,186]，高级设置分区 [391,854,658,116]，3 个 Mantine 滑杆在 y=870/906/942。
// 但视口只有 810 高 —— **滑杆全在画面外**，`innerText` 读得到、肉眼看不见。
//
// fitView 只框住**节点**，框不到挂在下面的面板，所以还得再手动缩。
// 目标：把滑杆整条拉进视口，拍下来。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchP6';
const { browser, page } = await launch();

/** 三个高级设置滑杆的实时位置 + 各自的标签。 */
const probe = () => page.evaluate(() => {
  const roots = [...document.querySelectorAll('[class*="mantine-Slider-root"]')].map((e) => {
    const b = e.getBoundingClientRect();
    return { y: Math.round(b.y), x: Math.round(b.x), w: Math.round(b.width), h: Math.round(b.height) };
  }).sort((a, b) => a.y - b.y);
  // 标签：在滑杆同一行左侧的文本
  const labels = roots.map((r) => {
    let best = null;
    for (const e of document.querySelectorAll('div,span,label')) {
      const b = e.getBoundingClientRect();
      if (e.children.length) continue;
      const t = (e.innerText || '').trim();
      if (!t || t.length > 6) continue;
      if (Math.abs(b.y + b.height / 2 - (r.y + r.h / 2)) < 14 && b.right <= r.x + 2) {
        if (!best || b.right > best.right) best = { t, right: Math.round(b.right) };
      }
    }
    return best ? best.t : null;
  });
  const all = roots.every((r) => r.y >= 0 && r.y + r.h <= window.innerHeight);
  return { count: roots.length, roots, labels, allInViewport: all, viewportH: window.innerHeight,
    zoomText: (document.body.innerText.match(/\d+%/) || [null])[0] };
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '把三个滑杆整条拉进视口再拍' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await page.mouse.dblclick(700, 200); await page.waitForTimeout(1200);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText('音频', { exact: false }).first().click({ timeout: 8000 });
  await page.waitForTimeout(2800);

  await fitView(page, 1);
  await page.waitForTimeout(1000);
  let p = await probe();
  console.log('fitView 后:', JSON.stringify(p));
  // 逐档缩小，直到三个滑杆全部进视口
  for (let i = 0; i < 8 && !p.allInViewport; i += 1) {
    await page.keyboard.press('Meta+-');
    await page.waitForTimeout(900);
    p = await probe();
    console.log(`  再缩一次 (${i + 1}): 滑杆 ${p.count} 个 y=${JSON.stringify(p.roots.map((r) => r.y))} 全进视口 ${p.allInViewport} 缩放 ${p.zoomText}`);
  }

  // 缩到底了第三个滑杆还是差 1px（y=803、底边 811、视口 810）——
  // 说明**光靠缩放救不回来**，得把画布内容整体往上平移。
  if (!p.allInViewport) {
    const need = Math.max(0, (p.roots[p.roots.length - 1].y + 8) - (p.viewportH - 12)) + 20;
    await page.keyboard.down('Space');
    await page.mouse.move(700, 600); await page.mouse.down(); await page.waitForTimeout(200);
    for (let i = 1; i <= 6; i += 1) { await page.mouse.move(700, 600 - i * (need / 6), { steps: 2 }); await page.waitForTimeout(50); }
    await page.mouse.up(); await page.keyboard.up('Space'); await page.waitForTimeout(1500);
    p = await probe();
    console.log('  Space+拖上移后:', JSON.stringify(p.roots.map((r) => r.y)), '全进视口', p.allInViewport);
  }

  await shot(page, 'M-24-音频节点-高级设置三滑杆.png');
  await logStep(B, { id: 'P6-audio-sliders', title: '音频节点高级设置：3 个滑杆的完整画面',
    target: `反复 ⌘- 缩到滑杆 y=${JSON.stringify(p.roots.map((r) => r.y))} 全部进入 ${p.viewportH}px 视口`,
    evidence: p,
    visible_text: `滑杆 ${p.count} 个，位置 ${JSON.stringify(p.roots)}，左侧标签 ${JSON.stringify(p.labels)}，` +
      `全部在视口内 ${p.allInViewport}（视口高 ${p.viewportH}，缩放 ${p.zoomText}）`,
    shot: 'M-24-音频节点-高级设置三滑杆.png' });
  console.log('节点:', await nodeCount(page));
} finally {
  await browser.close();
}
