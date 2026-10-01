// 探针 09 —— 画布下拉的真实行结构 + 教程按钮到底去哪了。
//
// A8 卡住的教训：更多操作 是 hover 门控，且行是异步出现的；上一版用
// getByRole('button',{name:'更多操作'}) 硬等 20 秒直接超时。这里改成：
// 打开下拉 → 打印每一行的完整 DOM 摘要（含 hover 才出现的节点）→ 再决定怎么点。
import { launch, open } from './lib.mjs';
import { CANVAS_URL } from './test-project.mjs';
import { clearToasts, closePromos, shot, fingerprint } from './scenario.mjs';

const { browser, page } = await launch();

try {
  await open(page, CANVAS_URL, { settle: 3500 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(600);

  const tabBtn = page.locator('button').filter({ hasText: /^画布 \d+$/ }).first();
  await tabBtn.click();
  await page.waitForTimeout(1000);

  const rows = await page.evaluate(() => {
    const dd = document.querySelector('.mantine-Popover-dropdown');
    if (!dd) return { error: 'no dropdown' };
    const out = [];
    dd.querySelectorAll('*').forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.width < 8 || r.height < 8) return;
      const s = getComputedStyle(el);
      out.push({
        tag: el.tagName,
        role: el.getAttribute('role'),
        aria: el.getAttribute('aria-label'),
        title: el.getAttribute('title'),
        text: (el.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 30),
        op: s.opacity,
        pe: s.pointerEvents,
        vis: s.visibility,
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        cls: (el.className || '').toString().slice(0, 60),
      });
    });
    return { html: dd.outerHTML.slice(0, 2500), nodes: out.slice(0, 45) };
  });

  console.log('=== 下拉 HTML（前 2500 字符） ===');
  console.log(rows.html);
  console.log('\n=== 下拉节点 ===');
  for (const n of rows.nodes || []) {
    console.log(`  ${n.tag} role=${n.role || '-'} aria=${JSON.stringify(n.aria)} text=${JSON.stringify(n.text)} op=${n.op} pe=${n.pe} ${n.rect.join(',')}`);
  }
  await shot(page, 'p09-canvas-dropdown-dom.png');

  await page.keyboard.press('Escape');
  await page.waitForTimeout(600);

  // ── 教程按钮到底做什么
  console.log('\n=== 教程按钮 ===');
  const help = page.getByRole('button', { name: '教程', exact: true }).first();
  console.log('exists:', await help.count());
  if (await help.count()) {
    console.log('outerHTML:', await help.evaluate((el) => el.outerHTML.slice(0, 400)));
    const popup = [];
    page.on('popup', (p) => popup.push('popup:' + p.url()));
    await help.click({ timeout: 5000 }).catch((e) => console.log('click warn', e.message.slice(0, 60)));
    await page.waitForTimeout(2000);
    const after = await fingerprint(page);
    const big = after.sort((a, b) => b.area - a.area).slice(0, 2);
    for (const b of big) console.log(`  new panel area=${b.area}: ${b.all.slice(0, 500)}`);
    console.log('pages:', page.context().pages().map((p) => p.url()));
    console.log('popup events:', popup);
    await shot(page, 'p09-after-tutorial.png');
  }
} finally {
  await browser.close();
}
