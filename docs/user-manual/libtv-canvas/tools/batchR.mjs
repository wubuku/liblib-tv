// Batch R —— 把折叠的「高级设置」点开，收掉 #12 剩下的那半。
//
// 前九轮失败的原因，这轮定位到一个很具体的点上：
// batchP9 找到的标题元素是 **[399,755,642,28] —— 642px 宽，是整行**，
// 而「高级设置」四个字贴在这一行的**最左边**。
// 我点的是 `x = 399 + 642/2 = 720`（**行中心**），那个位置压根没有文字。
// batchP3 里同一枚按钮是 `w=626`，点中心当然点空。
//
// 这轮不点「容器中心」，而是**先量出文字本身的包围盒，再点文字**，
// 并在点之前用 elementFromPoint 自证「那个点上最顶层的确实是这行」。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchR';
const { browser, page } = await launch();

/** 折叠容器 + 「高级设置」文字的**真实包围盒** + 命中自检。 */
const probe = () => page.evaluate(() => {
  const s = document.querySelector('[class*="mantine-Slider-root"]');
  if (!s) return { ok: false, why: '页面上没有滑杆' };
  let clip = s.parentElement;
  for (let i = 0; i < 12 && clip; i += 1) { if (/overflow-hidden/.test(clip.className || '')) break; clip = clip.parentElement; }
  // 文字节点：文字最深的那个 div/span
  const leaves = [...document.querySelectorAll('div,span,button,label')]
    .filter((e) => (e.innerText || e.textContent || '').trim() === '高级设置' && e.children.length === 0);
  const txtEl = leaves[leaves.length - 1] || null;
  const tb = txtEl ? txtEl.getBoundingClientRect() : null;
  // 文字所在的那一整行（往上找）
  let row = txtEl;
  while (row && row.getBoundingClientRect().height < 20) row = row.parentElement;
  const rb = row ? row.getBoundingClientRect() : null;
  const cr = clip ? clip.getBoundingClientRect() : null;
  // 点文字正中，看最顶层是谁
  const hit = tb ? (() => { const t = document.elementFromPoint(tb.x + tb.width / 2, tb.y + tb.height / 2);
    return t ? { tag: t.tagName, cls: (t.className || '').toString().slice(0, 40), text: (t.innerText || '').trim().slice(0, 16) } : null; })() : null;
  const sliders = [...document.querySelectorAll('[class*="mantine-Slider-root"]')].map((e) => {
    const b = e.getBoundingClientRect();
    return { y: Math.round(b.y), bottom: Math.round(b.bottom), x: Math.round(b.x), w: Math.round(b.width),
      inViewport: b.y >= 0 && b.bottom <= window.innerHeight, insideClip: cr ? b.bottom <= cr.bottom + 2 : null };
  }).sort((a, b) => a.y - b.y);
  return {
    ok: true,
    clipClientH: clip ? clip.clientHeight : null, clipScrollH: clip ? clip.scrollHeight : null,
    clipRect: cr ? [Math.round(cr.x), Math.round(cr.y), Math.round(cr.width), Math.round(cr.height)] : null,
    textRect: tb ? [Math.round(tb.x), Math.round(tb.y), Math.round(tb.width), Math.round(tb.height)] : null,
    rowRect: rb ? [Math.round(rb.x), Math.round(rb.y), Math.round(rb.width), Math.round(rb.height)] : null,
    textInViewport: tb ? tb.y >= 0 && tb.bottom <= window.innerHeight : false,
    cursorAtText: txtEl ? getComputedStyle(txtEl).cursor : null,
    hitTest: hit, sliders,
    allVisible: sliders.length > 0 && sliders.every((x) => x.inViewport && x.insideClip),
    viewportH: window.innerHeight,
  };
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '点「高级设置」文字本身，不是整行中心' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  // 双击空白 → 在「添加节点」面板里点「音频」。
  // 一次点不中菜单是常事（双击落在画布外、或者正好压在别的东西上），
  // 所以**换位重试**，并以「节点数真的变了」为准 —— 参见 batchP3 的教训。
  let made = false;
  for (const [dx, dy] of [[0, 0], [0, 120], [0, 240], [-120, 120], [120, 120]]) {
    await page.mouse.dblclick(700 + dx, 200 + dy);
    await page.waitForTimeout(1100);
    const it = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
      .getByText('音频', { exact: false }).first();
    if (await it.count().catch(() => 0)) {
      await it.click({ timeout: 4000 }).catch(() => {});
      await page.waitForTimeout(2400);
      if (await page.evaluate(() => document.querySelectorAll('.react-flow__node').length > 0)) { made = true; break; }
    }
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(700);
  }
  if (!made) throw new Error('换五个位置都建不出音频节点');
  console.log('音频节点已建:', await nodeCount(page));
  await fitView(page, 1);
  for (let i = 0; i < 5; i += 1) { await page.keyboard.press('Meta+-'); await page.waitForTimeout(650); }
  await page.waitForTimeout(1200);

  // 把「高级设置」文字推进视口（连滚带平移，直到 textInViewport）
  for (let k = 0; k < 10; k += 1) {
    const p = await probe();
    if (p.ok && p.textInViewport) { console.log(`第 ${k} 次：文字已进视口 ${JSON.stringify(p.textRect)}`); break; }
    await page.keyboard.down('Space');
    await page.mouse.move(300, 600); await page.mouse.down(); await page.waitForTimeout(180);
    await page.mouse.move(300, 500, { steps: 8 }); await page.mouse.up(); await page.keyboard.up('Space');
    await page.waitForTimeout(1100);
  }

  const before = await probe();
  console.log('\n点之前:', JSON.stringify(before, null, 1));
  await shot(page, 'M-23-音频节点-高级设置折叠态.png');

  if (!before.ok || !before.textRect) throw new Error('没定位到「高级设置」文字：' + JSON.stringify(before));
  if (!before.textInViewport) throw new Error(`文字 ${JSON.stringify(before.textRect)} 不在视口内（视口高 ${before.viewportH}）`);
  if (!before.hitTest || !/高级设置/.test(before.hitTest.text || '')) {
    console.log('  ⚠️ 命中自检没过，最顶层是:', JSON.stringify(before.hitTest), '—— 仍然点一次试试');
  }

  // ★ 点文字本身，不点整行中心
  const px = Math.round(before.textRect[0] + before.textRect[2] / 2);
  const py = Math.round(before.textRect[1] + before.textRect[3] / 2);
  console.log(`\n点击「高级设置」文字 (${px}, ${py})  —— 文字宽 ${before.textRect[2]}px，整行宽 ${before.rowRect?.[2]}px`);
  await page.mouse.click(px, py);
  await page.waitForTimeout(900);
  const mid = await probe();
  await page.waitForTimeout(1800);
  const after = await probe();
  await shot(page, 'M-24-音频节点-高级设置展开.png');

  const verdict = after.clipClientH > before.clipClientH
    ? `**展开成功：折叠容器高度 ${before.clipClientH} → ${after.clipClientH}px**`
    : `**没展开：高度 ${before.clipClientH} → ${after.clipClientH}**`;

  await logStep(B, { id: 'R-expand-advanced', title: '音频节点「高级设置」：点开折叠分区',
    target: `点「高级设置」**文字本身** (${px},${py})（文字宽 ${before.textRect[2]}px，整行宽 ${before.rowRect?.[2]}px —— 前几轮点的是行中心）`,
    evidence: { before, mid, after },
    visible_text: `${verdict}。折叠容器 scrollHeight 恒为 ${after.clipScrollH}；` +
      `点前滑杆 y=${JSON.stringify(before.sliders.map((x) => x.y))}，点后 y=${JSON.stringify(after.sliders.map((x) => x.y))}；` +
      `**三个滑杆是否全部可见 ${before.allVisible} → ${after.allVisible}**（视口高 ${after.viewportH}）；` +
      `命中自检（该点最顶层元素）${JSON.stringify(before.hitTest)}`,
    shot: 'M-24-音频节点-高级设置展开.png' });
  console.log('\n判定:', verdict, '| 三滑杆全可见:', before.allVisible, '→', after.allVisible);
  console.log('节点:', await nodeCount(page));
} finally {
  await browser.close();
}
