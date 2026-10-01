// Batch A（四）—— 复制画布 / 删除画布 / 切换画布，全部收口并留证。
import { launch, open } from './lib.mjs';
import { CANVAS_URL } from './test-project.mjs';
import { beginBatch, logStep, clearToasts, closePromos, shot, shotHighlighted, fingerprint } from './scenario.mjs';
import { openDropdown, readCanvasRows, openRowMenu, closeDropdown } from './canvas-dropdown.mjs';

/** 等到行列表连续两次读数相同。 */
async function stableRows(page, tries = 10) {
  let prev = null;
  for (let i = 0; i < tries; i += 1) {
    const now = await readCanvasRows(page);
    const names = now.map((r) => r.name).sort();
    if (prev && JSON.stringify(names) === JSON.stringify(prev)) return names;
    prev = names;
    await page.waitForTimeout(600);
  }
  return prev;
}

const tabLabel = (page) =>
  page.evaluate(() => {
    const id = document.querySelector('.mantine-Popover-dropdown')?.getAttribute('aria-labelledby');
    const el = id ? document.getElementById(id) : null;
    return el ? (el.innerText || '').trim() : null;
  });

const B = 'batchA4';
await beginBatch(B, { note: '复制 / 删除 / 切换画布（仅专用测试项目内）' });

const { browser, page } = await launch();

try {
  await open(page, CANVAS_URL, { settle: 4000 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(1200);

  await openDropdown(page, 1000);
  const before = await stableRows(page);
  const tab0 = await tabLabel(page);
  await shot(page, 'A9a-dropdown-before.png');
  await logStep(B, {
    id: 'A9a-baseline', title: '操作前基线',
    target: '画布下拉',
    evidence: { rows: before, activeTab: tab0 },
    visible_text: `行: ${JSON.stringify(before)}；顶栏标签: ${JSON.stringify(tab0)}`,
  });

  // ── 复制当前画布
  await openRowMenu(page, tab0);
  const dup = page.getByRole('menuitem', { name: '复制画布' }).or(page.getByRole('button', { name: '复制画布' }));
  if (await dup.count()) {
    await shotHighlighted(page, dup.first(), 'A9b-duplicate-menu-item.png', { step: 1 });
    await dup.first().click();
    await page.waitForTimeout(3200);
    await openDropdown(page, 1200);
    const after = await stableRows(page);
    const tab1 = await tabLabel(page);
    await logStep(B, {
      id: 'A9b-duplicate', title: '复制画布：命名规则与是否自动切换',
      target: '行级菜单「复制画布」',
      evidence: { before, after, activeTabBefore: tab0, activeTabAfter: tab1 },
      visible_text: `行: ${JSON.stringify(after)}；顶栏标签: ${JSON.stringify(tab1)}`,
      shot: await shot(page, 'A9b-after-duplicate.png'),
    });
    await closeDropdown(page);
  }

  // ── 删除刚复制出来的那张（列表最前），保证至少还剩 2 张
  await openDropdown(page, 1000);
  const rows = await readCanvasRows(page);
  if (rows.length >= 3) {
    const victim = rows[0].name;
    const menu = await openRowMenu(page, victim);
    const del = page.getByRole('menuitem', { name: '删除画布' }).or(page.getByRole('button', { name: '删除画布' }));
    if (await del.count()) {
      await shotHighlighted(page, del.first(), 'A9c-delete-menu-item.png', { step: 2 });
      await del.first().click();
      await page.waitForTimeout(1400);
      const conf = (await fingerprint(page)).sort((a, b) => b.area - a.area)[0];
      await logStep(B, {
        id: 'A9c-delete-confirm', title: '删除画布的二次确认框文案',
        target: '行级菜单「删除画布」',
        evidence: { victim, buttons: conf?.buttons },
        visible_text: conf?.all,
        shot: await shot(page, 'A9c-delete-confirm.png'),
      });
      const ok = page.getByRole('button', { name: '确认', exact: true }).or(page.getByRole('button', { name: '确定', exact: true }));
      if (await ok.count()) {
        await shotHighlighted(page, ok.last(), 'A9c-delete-confirm-btn.png', { step: 3 });
        await ok.last().click();
        await page.waitForTimeout(3200);
      } else {
        console.log('未找到确认按钮');
      }
      await openDropdown(page, 1200);
      const after2 = await stableRows(page);
      await logStep(B, {
        id: 'A9d-delete-done', title: '删除后的回落',
        target: '确认按钮',
        evidence: { before: rows.map((r) => r.name), activeTabAfter: await tabLabel(page) },
        visible_text: `行: ${JSON.stringify(after2)}`,
        shot: await shot(page, 'A9d-after-delete.png'),
      });
      await closeDropdown(page);
    }
  } else {
    console.log('删除跳过，画布数 =', rows.length);
  }

  // ── 切换画布
  await openDropdown(page, 1000);
  const rows2 = await readCanvasRows(page);
  const target = rows2[rows2.length - 1];
  if (target) {
    await page.locator('.mantine-Popover-dropdown button[aria-label^="切换到画布 "]').first().hover();
    await shotHighlighted(page, page.locator('.mantine-Popover-dropdown button[aria-label^="切换到画布 "]').first(), 'A9e-switch-row.png', { step: 4 });
    await page.locator('.mantine-Popover-dropdown button[aria-label^="切换到画布 "]').first().click();
    await page.waitForTimeout(3000);
    await logStep(B, {
      id: 'A9e-switch', title: '切换到另一张画布（是否换 projectId）',
      target: '行「切换到画布 …」',
      evidence: { clicked: target.label, urlAfter: page.url() },
      visible_text: `顶栏标签: ${JSON.stringify(await tabLabel(page))}`,
      shot: await shot(page, 'A9e-after-switch.png'),
    });
  }
} finally {
  await browser.close();
}
