// Batch A（三）—— 画布 CRUD 真跑 + 教程按钮定性。
import { launch, open } from './lib.mjs';
import { CANVAS_URL } from './test-project.mjs';
import { beginBatch, logStep, clearToasts, closePromos, shot, shotHighlighted, fingerprint, diffPanels } from './scenario.mjs';
import { openDropdown, readCanvasRows, openRowMenu, closeDropdown } from './canvas-dropdown.mjs';

const B = 'batchA3';
await beginBatch(B, { note: '画布新建/重命名/复制/删除（仅专用测试项目）+ 教程按钮定性' });

const { browser, page } = await launch();

try {
  await open(page, CANVAS_URL, { settle: 3500 });
  await closePromos(page);
  await clearToasts(page);
  const cd = page.getByRole('button', { name: '关闭', exact: true }).first();
  if (await cd.count()) { await cd.click({ timeout: 3000 }).catch(() => {}); await page.waitForTimeout(400); }

  // ── 教程按钮定性：它到底是「教程」还是「联系客服」？
  const help = page.getByRole('button', { name: '教程', exact: true }).first();
  const helpAttrs = await help.evaluate((el) => ({
    aria: el.getAttribute('aria-label'),
    dataSidebarBtn: el.getAttribute('data-sidebar-btn'),
    html: el.outerHTML.slice(0, 200),
  }));
  const reqs = [];
  page.on('request', (r) => reqs.push(`${r.method()} ${new URL(r.url()).pathname}`));
  const navBefore = page.url();
  await help.click({ timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(2500);
  const popups = page.context().pages().filter((p) => p !== page);
  const newPanels = diffPanels(await fingerprint(page), await fingerprint(page));
  await logStep(B, {
    id: 'A7b-tutorial-identity', title: '底部「教程」按钮的真实身份',
    target: 'role=button name="教程"',
    evidence: {
      ...helpAttrs,
      navBefore,
      navAfter: page.url(),
      popupUrls: popups.map((p) => p.url()),
      newRequests: reqs.filter((r) => !/\.(js|css|png|svg|woff2?|ico|mp4|webp)/.test(r)).slice(-15),
      panelAppeared: newPanels.length > 0,
    },
    visible_text: '点击后页面上没有出现任何新面板，也没有跳转 / 弹窗',
    shot: await shot(page, 'A7b-tutorial-click.png'),
  });
  for (const p of popups) await p.close().catch(() => {});

  // ── 画布 CRUD
  await openDropdown(page);
  const rows0 = await readCanvasRows(page);
  await logStep(B, {
    id: 'A8a-dropdown-rows', title: '画布下拉的真实行（新画布在最前）',
    target: '顶栏「画布 N」→ .mantine-Popover-dropdown',
    evidence: rows0,
    visible_text: `行: ${JSON.stringify(rows0.map((r) => r.label))}`,
    shot: await shot(page, 'A8a-canvas-dropdown-rows.png'),
  });

  // 重命名当前画布（画布 1）
  const menu1 = await openRowMenu(page, '画布 1');
  await logStep(B, {
    id: 'A8b-row-menu', title: '画布行「更多操作」四项',
    target: 'hover 行 → el.click() 绕过 pointer-events',
    visible_text: menu1?.all,
    evidence: menu1?.buttons,
    shot: menu1 ? await shot(page, 'A8b-row-more-menu.png') : null,
  });

  const rename = page.getByRole('menuitem', { name: '重命名画布' }).or(page.getByRole('button', { name: '重命名画布' }));
  if (await rename.count()) {
    await rename.first().click();
    await page.waitForTimeout(900);
    // 输入框必须锁定在下拉里：用页面级 input[type=text] 会误命中顶栏「项目名称」。
    const inp = page.locator('.mantine-Popover-dropdown input[type="text"]').first();
    if (await inp.count()) {
      console.log('rename input value before:', await inp.inputValue());
      await shotHighlighted(page, inp, 'A8c-rename-inline-input.png', { step: 2 });
      await inp.fill('手册取证画布');
      await page.waitForTimeout(400);
      await inp.press('Enter');
      await page.waitForTimeout(1800);
    }
    await openDropdown(page);
    const rows1 = await readCanvasRows(page);
    await logStep(B, {
      id: 'A8c-rename-done', title: '重命名生效（Enter 提交）',
      target: '行内 input → Enter',
      evidence: rows1,
      visible_text: `行: ${JSON.stringify(rows1.map((r) => r.label))}`,
      shot: await shot(page, 'A8c-after-rename.png'),
    });
    await closeDropdown(page);
  }

  // 复制
  await openDropdown(page);
  const menu2 = await openRowMenu(page, '手册取证画布');
  const dup = page.getByRole('menuitem', { name: '复制画布' }).or(page.getByRole('button', { name: '复制画布' }));
  if (await dup.count()) {
    await dup.first().click();
    await page.waitForTimeout(2800);
    await openDropdown(page);
    const rows2 = await readCanvasRows(page);
    await logStep(B, {
      id: 'A8d-duplicate', title: '复制画布（是否自动切到副本）',
      target: '行级菜单「复制画布」',
      evidence: { urlAfter: page.url(), menuText: menu2?.all },
      visible_text: `行: ${JSON.stringify(rows2.map((r) => r.label))}`,
      shot: await shot(page, 'A8d-after-duplicate.png'),
    });
    await closeDropdown(page);
  }

  // 新建一张（凑够删除条件）
  await openDropdown(page);
  const nc = page.getByRole('button', { name: '新建画布', exact: true }).first();
  if (await nc.count()) { await nc.click(); await page.waitForTimeout(2500); }
  await openDropdown(page);
  const rows3 = await readCanvasRows(page);
  console.log('rows after create:', JSON.stringify(rows3));

  // 删除副本（保留至少 2 张，避免删空）
  if (rows3.length >= 3) {
    const victim = rows3[0].name; // 新建/复制的在最前
    await openRowMenu(page, victim);
    const del = page.getByRole('menuitem', { name: '删除画布' }).or(page.getByRole('button', { name: '删除画布' }));
    if (await del.count()) {
      await shotHighlighted(page, del.first(), 'A8e-delete-menu.png', { step: 3 });
      await del.first().click();
      await page.waitForTimeout(1200);
      const conf = (await fingerprint(page)).sort((a, b) => b.area - a.area)[0];
      await logStep(B, {
        id: 'A8e-delete-confirm', title: '删除画布的二次确认框',
        target: '行级菜单「删除画布」',
        evidence: { victim, before: rows3 },
        visible_text: conf?.all,
        shot: await shot(page, 'A8e-delete-confirm.png'),
      });
      const ok = page.getByRole('button', { name: '确认', exact: true }).or(page.getByRole('button', { name: '确定', exact: true }));
      if (await ok.count()) {
        await shotHighlighted(page, ok.last(), 'A8e-delete-confirm-btn.png', { step: 4 });
        await ok.last().click();
        await page.waitForTimeout(2800);
      }
      await openDropdown(page);
      const rows4 = await readCanvasRows(page);
      await logStep(B, {
        id: 'A8f-delete-done', title: '删除后剩余画布（活动画布被删时的回落）',
        evidence: { url: page.url() },
        visible_text: `行: ${JSON.stringify(rows4.map((r) => r.label))}`,
        shot: await shot(page, 'A8f-after-delete.png'),
      });
      await closeDropdown(page);
    }
  } else {
    console.log('删除跳过，画布数 =', rows3.length);
  }
} finally {
  await browser.close();
}
