// Batch AR2 —— 补 AR 的两处缺口：
//
//   AR2a  AR 抓到 popup 的 URL 和标题，但没有**画面**。
//         手册写「在新窗口打开」，用户想看到打开的到底是什么。
//         这次把 popup 那个 page 单独截一张 —— 拍完立刻关，一个字都不点。
//
//   AR2b  AR 两枚按钮的 hover 提示都是「**按 ESC 退出**」。
//         这是 Mantine Popover 的关法提示，也就是说**这个面板是可以用 Esc 收的**。
//         §15 有一条规矩是「不按 Esc 关浮层」（怕它连带改别的东西），
//         但这里提示自己把 Esc 写出来了，值得实测一次 Esc 到底收不收得了。
//         判据要问「画布有没有被动过」：关面板前后对比 URL、`.react-flow__node` 数、
//         以及面板容器还在不在 —— 别只问「面板没了没」。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { openDropdown } from './canvas-dropdown.mjs';
import { nodeCount } from './canvas-ops.mjs';
import { SHOTS } from './lib.mjs';

const SPACE = '10354929';
const B = 'batchAR2';
const { browser, ctx, page } = await launch();

const shareOpen = () => page.evaluate(() => [...document.querySelectorAll('div,section,aside')]
  .some((e) => {
    const r = e.getBoundingClientRect();
    return r.width > 200 && r.height > 120 && /发布你的作品|分享链接/.test((e.innerText || '').replace(/\s+/g, ' '));
  }));
const findItem = (text) => page.evaluate((t) => {
  const el = [...document.querySelectorAll('div,li,button,span,a')]
    .filter((e) => (e.innerText || '').trim() === t)
    .sort((a, b) => { const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
      return (ra.width * ra.height) - (rb.width * rb.height); })[0];
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
}, text);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '补拍「新窗口打开」的画面 + 实测 Esc 能不能关发布面板' });

  // ── AR2a 新窗口打开：拍画面 ────────────────────────────
  const popups = [];
  ctx.on('page', (p) => popups.push(p));

  await openDropdown(page, 1400);
  const more = await page.evaluate(() => {
    const pop = [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"],[class*="Dropdown-dropdown"]')]
      .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 120 && r.height > 60; })[0];
    if (!pop) return null;
    const b = [...pop.querySelectorAll('button,[role="button"]')]
      .filter((x) => x.getAttribute('aria-label') === '更多操作')[0];
    if (!b) return null;
    const r = b.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      row: (b.previousElementSibling?.innerText || '').trim() };
  });
  if (!more) throw new Error('画布下拉里没有「更多操作」');
  await page.mouse.click(more.cx, more.cy); await page.waitForTimeout(1700);
  const item = await findItem('在新窗口打开');
  if (!item) throw new Error('行菜单里找不到「在新窗口打开」');
  await page.mouse.click(item.cx, item.cy);
  await page.waitForTimeout(6000);

  let win = { err: `一个 popup 都没抓到（抓到 ${popups.length} 个）` };
  if (popups.length) {
    const p = popups[0];
    const url = p.url();
    // **只读**：等它自己把画布 shell 挂上，不点任何东西
    await p.waitForLoadState('domcontentloaded', { timeout: 30000 }).catch(() => {});
    await p.waitForTimeout(5000);
    const inner = await p.evaluate(() => ({
      hasFlow: !!document.querySelector('.react-flow'),
      nodeCount: document.querySelectorAll('.react-flow__node').length,
      topbar: (document.querySelector('header')?.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
      zoomLabel: ([...document.querySelectorAll('*')].find((e) => /^\d+%$/.test((e.innerText || '').trim())
        && e.getBoundingClientRect().width < 60 && e.getBoundingClientRect().y > 700)?.innerText || '').trim(),
    })).catch((e) => ({ err: String(e).slice(0, 120) }));
    await p.screenshot({ path: `${SHOTS}/M-121-在新窗口打开-新标签页.png` });
    win = { url, title: await p.title().catch(() => '?'), inner };
    console.log('AR2a 新窗口:', JSON.stringify(win));
  }
  for (const p of popups) { await p.close().catch(() => {}); }
  ctx.removeAllListeners('page');
  await page.waitForTimeout(800);

  // ── AR2b Esc 能不能关发布面板 ─────────────────────────
  const trig = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button,[role="button"]')]
      .find((e) => (e.getAttribute('aria-label') || '').trim() === '发布与分享');
    if (!b) return null;
    const r = b.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
  });
  let esc = { err: '没找到触发点' };
  if (trig) {
    await page.mouse.click(trig.cx, trig.cy); await page.waitForTimeout(2200);
    const wasOpen = await shareOpen();
    const before = { url: page.url(), nodes: await nodeCount(page) };
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1500);
    const nowOpen = await shareOpen();
    const after = { url: page.url(), nodes: await nodeCount(page) };
    esc = { openedByClick: wasOpen, stillOpenAfterEsc: nowOpen, before, after,
      urlChanged: before.url !== after.url, nodeCountChanged: before.nodes !== after.nodes };
    console.log('AR2b Esc:', JSON.stringify(esc));
    await shot(page, 'M-123-发布与分享-按ESC之后.png');
  }

  await logStep(B, {
    id: 'AR2-shot-and-esc', title: '补拍「新窗口打开」画面 + 实测 Esc 能否关发布面板',
    target: 'popup 单独截图只读；Esc 前后同时比对「面板还在不在」「URL 变没变」「节点数变没变」',
    evidence: { row: more.row, win, esc },
    visible_text: `「在新窗口打开」点完弹出新标签页：${JSON.stringify(win)}。`
      + `\n\nEsc 实测：${JSON.stringify(esc)}`,
    shot: 'M-121-在新窗口打开-新标签页.png',
  });
  console.log('AR2 完成');
} finally {
  await browser.close();
}
