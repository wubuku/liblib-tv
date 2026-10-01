// 探针 07 —— 快捷键面板：按**表格单元格**逐列拆解，不靠 innerText 拼接顺序。
//
// 为什么必须这么较真：p06 抓到的扁平文本是
//   「移动画布 键盘 Space 触控板 鼠标 移动 V 抓手工具 H」
// 从这一串里无法判断 `V` 属于「移动」还是「抓手工具」——扁平化把行和列压平了。
// 面板里 `移动`/`抓手工具` 和 `键盘`/`触控板`/`鼠标` 是两组正交的列，
// 结论只能从单元格读出来。
import { launch, open, closePromos, shot, injectHighlight } from './lib.mjs';
import { CANVAS_URL } from './test-project.mjs';

const { browser, page } = await launch();

try {
  await open(page, CANVAS_URL, { settle: 3500 });
  await closePromos(page);
  const kb = page.getByRole('button', { name: '关闭浏览器通知提示', exact: true });
  if (await kb.count()) await kb.first().click().catch(() => {});
  const ok = page.getByRole('button', { name: '知道了', exact: true });
  if (await ok.count()) await ok.first().click().catch(() => {});
  await page.waitForTimeout(600);

  await page.getByRole('button', { name: '快捷键', exact: true }).click();
  await page.waitForTimeout(1500);
  await injectHighlight(page);

  const table = await page.evaluate(() => {
    const panels = [...document.querySelectorAll('div')].filter((el) => {
      const r = el.getBoundingClientRect();
      return r.width > 400 && r.height > 300 && /成组/.test(el.innerText || '');
    });
    const host = panels[panels.length - 1];
    if (!host) return { error: 'no host' };

    const rows = [];
    // 优先按 role=table/row/cell 结构读；没有就退回按视觉网格读。
    const trs = host.querySelectorAll('[role="row"]');
    if (trs.length) {
      trs.forEach((tr) => {
        rows.push([...tr.querySelectorAll('[role="cell"],[role="columnheader"],[role="gridcell"],td,th')]
          .map((td) => (td.innerText || '').replace(/\s+/g, ' ').trim()));
      });
    } else {
      // 视觉网格：收集每个文本叶子，按 y 聚成行、按 x 聚成列。
      const leaves = [];
      host.querySelectorAll('*').forEach((el) => {
        if (el.children.length) return;
        const t = (el.textContent || '').replace(/\s+/g, ' ').trim();
        if (!t) return;
        const r = el.getBoundingClientRect();
        if (r.width < 1 || r.height < 1) return;
        leaves.push({ t, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) });
      });
      const ys = [...new Set(leaves.map((l) => l.y))].sort((a, b) => a - b);
      for (const y of ys) {
        const inRow = leaves.filter((l) => Math.abs(l.y - y) < 6).sort((a, b) => a.x - b.x);
        if (inRow.length) rows.push(inRow.map((l) => l.t));
      }
    }
    return {
      sectionTitles: [...host.querySelectorAll('*')].filter((e) => !e.children.length && /^(创作|缩放|移动|其他|画布操作|节点操作)$/.test((e.textContent || '').trim())).map((e) => e.textContent.trim()),
      rows,
      hostRect: (() => { const r = host.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })(),
    };
  });

  console.log('=== 区块标题 ===', JSON.stringify(table.sectionTitles));
  console.log('=== 面板尺寸 ===', JSON.stringify(table.hostRect));
  console.log('=== 逐行 ===');
  for (const r of table.rows) console.log('  ' + JSON.stringify(r));

  // 逐单元格配图：把「动作」列和它的键位列各拍一张，供正文对照表配图。
  await shot(page, 'p07-shortcuts-full.png');
  const host = page.locator('div').filter({ hasText: /^创作/ }).last();
  if (await host.count()) {
    const box = await host.boundingBox().catch(() => null);
    if (box) {
      await shot(page, 'p07-shortcuts-创作段.png', { clip: { x: box.x, y: box.y, width: Math.min(box.width, 1440 - box.x), height: Math.min(200, 810 - box.y) } });
    }
  }
  console.log('shots saved');
} finally {
  await browser.close();
}
