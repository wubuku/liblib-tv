// Batch BF3 —— 补 BF2 留下的两个小口。
//
// 1. 画布下拉的**准确条目数**。BF2 按容器 x 范围筛，读到 65 条 ——
//    里面必然有父子重复（BF1 读 161 条时同一行就出现 2~3 次）。
//    ✅ 正确做法：先按「**最内层**」去重（同一行只保留不含同文案子元素的那些），
//    再按 y 排序数一遍；并且**把下拉容器滚到底**确认到底有多少条。
//    还要看当前画布（「画布 2」）是怎么标的 —— 有没有勾、有没有高亮。
//
// 2. `适合屏幕 ⌘ 0` 这一行。BF2 点它时 scale **没变** —— 但那次画布
//    刚被 `⌘0` 框过一次，本来就接近适配状态，**「没变化」分不清是幂等还是无效**。
//    ✅ 这轮先故意放大到 200%，再点它，scale 必须明显回落 —— 才算坐实。
//    （同样的分诊思路：给每个动作配一个「**它一定会产生变化的初始状态**」。
//      上一轮把「幂等」和「无效」混在一起，正是 §31 说的那类错误。）
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBF3';
const { browser, page } = await launch();

const snapScale = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const m = v ? /scale\(([\d.]+)\)/.exec(v.style.transform || '') : null;
  return m ? +m[1] : null; });

const openZoom = async () => {
  const p = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => x.getAttribute('aria-label') === '缩放选项');
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
  });
  if (!p) return null;
  await page.mouse.move(p.x, p.y); await page.waitForTimeout(250);
  await page.mouse.click(p.x, p.y); await page.waitForTimeout(2000);
  return p;
};

/** 只保留「最内层」：自身文本与父相同的不算。 */
const leafRows = (pg) => pg.evaluate(() => {
  const ok = (e) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(e.tagName);
  return [...document.querySelectorAll('div,li,button,span,a')].filter(ok)
    .map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter(({ r }) => r.width > 30 && r.height > 8 && r.height < 60 && r.x > 150 && r.x < 400 && r.y > 40 && r.y < 810)
    .filter(({ e, r }) => {
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      if (!t || t.length > 30) return false;
      // 最内层：父元素里没有一个「更小且同文」的子元素
      for (const c of e.querySelectorAll('*')) {
        const q = c.getBoundingClientRect();
        if ((c.innerText || '').replace(/\s+/g, ' ').trim() === t && q.width * q.height < r.width * r.height) return false;
      }
      return true; })
    .map(({ e, r }) => ({ text: (e.innerText || '').replace(/\s+/g, ' ').trim(),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cur: /bg-canvas-controls-active|font-semibold|text-white/.test(
        (e.className || '').toString() + (e.parentElement?.className || '').toString()),
      cls: (e.className || '').toString().slice(0, 44) }))
    .sort((a, b) => a.rect[1] - b.rect[1]);
});

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1600);
  await fitView(page); await page.waitForTimeout(1600);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '画布下拉准确条目数 + 适合屏幕在非适配态的行为' });

  const out = {};
  await page.mouse.move(720, 260); await page.waitForTimeout(800);

  // ═══ 1. 画布下拉的准确条目数
  console.log('--- BF3-1 画布下拉 ---');
  const cb = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => /^画布\s*\d+$/.test((x.innerText || '').replace(/\s+/g, ' ').trim()));
    if (!e) return { err: '没找到「画布 N」' };
    const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), text: (e.innerText || '').trim() }; });
  if (cb.err) { console.log(' ', cb.err); out.canvasMenu = cb; }
  else {
    await page.mouse.move(cb.x, cb.y); await page.waitForTimeout(300);
    await page.mouse.click(cb.x, cb.y); await page.waitForTimeout(2400);
    // 找到下拉容器并读它的滚动高度 vs 可见高度
    const host = await page.evaluate(() => {
      const cands = [...document.querySelectorAll('div,ul,section')]
        .filter((e) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(e.tagName))
        .map((e) => ({ e, r: e.getBoundingClientRect() }))
        .filter(({ e, r }) => r.x > 150 && r.x < 400 && r.y > 40 && r.y < 300 && r.height > 100
          && (e.innerText || '').match(/画布\s*\d+/g)?.length >= 2)
        .sort((a, b) => a.r.width * a.r.height - b.r.width * b.r.height);
      if (!cands.length) return { err: 'no host' };
      const { e, r } = cands[0];
      // 找内部真正的滚动容器
      let sc = e;
      for (const c of e.querySelectorAll('*')) {
        if (c.scrollHeight > c.clientHeight + 10 && c.clientHeight > 60) sc = c;
      }
      const q = sc.getBoundingClientRect();
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        scrollRect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
        scrollH: sc.scrollHeight, clientH: sc.clientHeight, scrollable: sc.scrollHeight > sc.clientHeight + 10,
        scrollTop: sc.scrollTop }; });
    console.log('  容器：', JSON.stringify(host));
    const rows1 = await leafRows(page);
    console.log(`  视口内最内层行 ${rows1.length} 条：`);
    rows1.forEach((r) => console.log(`    [${r.rect}]${r.cur ? ' ★当前' : '   '} "${r.text}"`));
    out.canvasMenu = { btn: cb, host, rowsTop: rows1, nTop: rows1.length };
    await shot(page, 'M-192-画布下拉-列表.png');
    out.shot = 'M-192-画布下拉-列表.png';

    // 滚到底
    if (host && !host.err && host.scrollable) {
      await page.mouse.move(host.rect[0] + host.rect[2] / 2, host.rect[1] + 40);
      await page.mouse.wheel(0, 2000); await page.waitForTimeout(1400);
      const rows2 = await leafRows(page);
      const all = [...new Set([...rows1.map((r) => r.text), ...rows2.map((r) => r.text)])];
      console.log(`  滚到底后 ${rows2.length} 条；去重合计 **${all.length}** 张画布`);
      console.log(`  全部：${all.join(' / ')}`);
      out.canvasMenu.rowsBottom = rows2;
      out.canvasMenu.all = all;
      out.canvasMenu.nAll = all.length;
    }
    await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
  }

  // ═══ 2. 适合屏幕 —— 先放大到 200%，再点，必须看到回落
  console.log('\n--- BF3-2 适合屏幕（非适配态）---');
  await fitView(page); await page.waitForTimeout(1800);
  const zp = await openZoom();
  if (!zp) { console.log('  没找到缩放按钮'); out.fit = { err: 'no zoom btn' }; }
  else {
    const inp = await page.evaluate(() => {
      const e = document.querySelector('input[aria-label="缩放比例"]');
      if (!e) return { err: 'no input' };
      e.focus(); return { ok: true }; });
    if (inp.err) { console.log('  ', inp.err); out.fit = inp; }
    else {
      await page.keyboard.press('Meta+a'); await page.keyboard.type('200');
      await page.keyboard.press('Enter'); await page.waitForTimeout(2400);
      const big = await snapScale();
      console.log(`  故意放大到 scale = ${big}`);
      // 菜单此刻应该还开着（BF2 坐实动作项不关菜单）
      const stillOpen = await page.evaluate(() => !!document.querySelector('input[aria-label="缩放比例"]'));
      console.log(`  输入框仍在（菜单还开着）：${stillOpen}`);
      // 逐个点
      const seq = [];
      if (!stillOpen) await openZoom();
      const hit = await page.evaluate(() => {
        const e = [...document.querySelectorAll('div,button,span')]
          .filter((x) => !['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE'].includes(x.tagName))
          .filter((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '适合屏幕 ⌘ 0')
          .map((x) => { const r = x.getBoundingClientRect();
            return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
              w: Math.round(r.width), h: Math.round(r.height) }; })
          .sort((a, b) => a.w * a.h - b.w * b.h)[0];
        return e || { err: '没找到「适合屏幕 ⌘ 0」' }; });
      if (hit.err) { console.log('  ', hit.err); out.fit = hit; }
      else {
        await page.mouse.click(hit.x, hit.y); await page.waitForTimeout(2600);
        const after = await snapScale();
        console.log(`  点「适合屏幕 ⌘ 0」：${big} → ${after} ${after !== big ? '✅ 回落了' : '❌ 没变'}`);
        out.fit = { startScale: big, afterScale: after, changed: after !== big, hit,
          menuStillOpen: await page.evaluate(() => !!document.querySelector('input[aria-label="缩放比例"]')) };
        console.log(`  点完菜单仍开着：${out.fit.menuStillOpen}`);
      }
    }
    // 复原 100%
    const z2 = await openZoom();
    if (z2) {
      const ok2 = await page.evaluate(() => {
        const e = document.querySelector('input[aria-label="缩放比例"]');
        if (!e) return false; e.focus(); return true; });
      if (ok2) { await page.keyboard.press('Meta+a'); await page.keyboard.type('100');
        await page.keyboard.press('Enter'); await page.waitForTimeout(2200); }
      await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
    }
    out.restored = await snapScale();
    console.log('  复原 scale =', out.restored);
  }

  await logStep(B, {
    id: 'BF3-canvas-menu-count-fit-screen',
    title: '画布下拉准确条目数 / 「适合屏幕」在非适配态确实会回落',
    target: 'BF2 里「适合屏幕」点了没变，但那次画布刚被 ⌘0 框过、本就接近适配 —— '
      + '"没变化"分不清是幂等还是无效。这轮先故意放大到 200% 再点。'
      + '画布下拉则改用「最内层去重」重数，并滚到底确认。',
    evidence: out,
    visible_text: JSON.stringify({ canvasMenu: { nTop: out.canvasMenu?.nTop, nAll: out.canvasMenu?.nAll, all: out.canvasMenu?.all },
      fit: out.fit, restored: out.restored }).slice(0, 3000),
    shot: out.shot,
  });
  console.log('\nBF3 完成');
} finally {
  await browser.close();
}
