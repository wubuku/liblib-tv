// Batch A（续）—— 缩放菜单 / 教程面板 + **画布四操作真跑一遍**（新建、重命名、复制、删除）。
//
// CRUD 只在专用测试项目 a4ef3de0... 里做，且新建出来的画布本身就是一次性的，
// 删的是自己刚建的，不碰用户任何项目（PROGRESS.md §0 安全边界第 4 条）。
import { launch, open } from './lib.mjs';
import { CANVAS_URL } from './test-project.mjs';
import { beginBatch, logStep, clearToasts, closePromos, shot, shotHighlighted, fingerprint, diffPanels } from './scenario.mjs';

const B = 'batchA2';
await beginBatch(B, { note: '缩放菜单 / 教程面板 / 画布新建·重命名·复制·删除（仅在专用测试项目内）' });

const { browser, page } = await launch();

async function openPanel(page, loc, settle = 1100) {
  const before = await fingerprint(page);
  await loc.click({ timeout: 6000 });
  await page.waitForTimeout(settle);
  const after = await fingerprint(page);
  const neu = diffPanels(before, after);
  return neu.length ? neu[neu.length - 1] : null;
}

/** 打开画布行「更多操作」菜单（hover 门控，必须用 el.click()）。 */
async function rowMenu(page) {
  const before = await fingerprint(page);
  await page.getByRole('button', { name: '更多操作', exact: true }).first().evaluate((el) => el.click());
  await page.waitForTimeout(800);
  const after = await fingerprint(page);
  const neu = diffPanels(before, after);
  return neu.length ? neu[neu.length - 1] : null;
}

const canvasTabs = () =>
  page.evaluate(() => [...document.querySelectorAll('button')].map((b) => (b.innerText || '').trim()).filter((t) => /^画布 \d+$/.test(t)));

try {
  await open(page, CANVAS_URL, { settle: 3500 });
  await closePromos(page);
  await clearToasts(page);
  // 关掉 TV Director 抽屉，避免遮挡右下方工具条
  const cd = page.getByRole('button', { name: '关闭', exact: true }).first();
  if (await cd.count()) { await cd.click({ timeout: 3000 }).catch(() => {}); await page.waitForTimeout(500); }
  await page.waitForTimeout(500);

  // ── A6 缩放菜单
  const zoom = page.getByRole('button', { name: '缩放选项', exact: true }).first();
  if (await zoom.count()) {
    const panel = await openPanel(page, zoom, 900);
    await logStep(B, {
      id: 'A6-zoom', title: '缩放菜单：百分比 / 适合屏幕',
      target: 'role=button name="缩放选项"',
      visible_text: panel?.all,
      evidence: panel?.buttons,
      shot: panel ? await shot(page, 'A6-zoom-menu.png') : null,
    });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
  }

  // ── A7 教程面板
  const help = page.getByRole('button', { name: '教程', exact: true }).first();
  if (await help.count()) {
    const panel = await openPanel(page, help, 1800);
    await logStep(B, {
      id: 'A7-tutorial', title: '教程面板',
      target: 'role=button name="教程"',
      visible_text: panel?.all,
      evidence: panel?.buttons,
      shot: panel ? await shot(page, 'A7-tutorial.png') : null,
    });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(600);
    // 教程常是新窗口/外链，检查是否开了新页
    console.log('pages after tutorial:', page.context().pages().map((p) => p.url()));
  }

  // ── A8 画布 CRUD 真跑
  const tabBtn = () => page.locator('button').filter({ hasText: /^画布 \d+$/ }).first();
  console.log('canvases before:', JSON.stringify(await canvasTabs()));

  // A8-1 新建画布
  await tabBtn().click();
  await page.waitForTimeout(700);
  const newCanvas = page.getByRole('button', { name: '新建画布', exact: true }).first();
  if (await newCanvas.count()) {
    await shotHighlighted(page, newCanvas, 'A8a-canvas-dropdown-new.png', { step: 1 });
    await newCanvas.click();
    await page.waitForTimeout(2500);
    const after1 = await canvasTabs();
    await logStep(B, {
      id: 'A8a-create-canvas', title: '新建画布（面板 → 新建画布）',
      target: '画布下拉 → role=button name="新建画布"',
      evidence: { before: await canvasTabs(), url: page.url() },
      visible_text: `画布列表: ${JSON.stringify(after1)}`,
      shot: await shot(page, 'A8a-after-create.png'),
    });
  }

  // A8-2 重命名画布（行内 input）
  await tabBtn().click();
  await page.waitForTimeout(700);
  const m1 = await rowMenu(page);
  const rename = page.getByRole('menuitem', { name: '重命名画布' }).or(page.getByRole('button', { name: '重命名画布' }));
  if (await rename.count()) {
    await shotHighlighted(page, rename.first(), 'A8b-row-more-menu.png', { step: 2 });
    await rename.first().click();
    await page.waitForTimeout(900);
    const inp = page.locator('input[value], input[type="text"]').last();
    const ok = await inp.count();
    let renamed = null;
    if (ok) {
      await inp.fill('手册取证画布');
      await page.waitForTimeout(400);
      await shotHighlighted(page, inp, 'A8b-rename-input.png', { step: 3 });
      await inp.press('Enter');
      await page.waitForTimeout(1500);
    }
    renamed = await canvasTabs();
    await logStep(B, {
      id: 'A8b-rename-canvas', title: '重命名画布',
      target: '行级菜单「重命名画布」→ 行内输入框 → Enter',
      evidence: { menu_text: m1?.all, inputFound: !!ok },
      visible_text: `画布列表: ${JSON.stringify(renamed)}`,
      shot: await shot(page, 'A8b-after-rename.png'),
    });
  }

  // A8-3 复制画布
  await tabBtn().click();
  await page.waitForTimeout(700);
  await rowMenu(page);
  const dup = page.getByRole('menuitem', { name: '复制画布' }).or(page.getByRole('button', { name: '复制画布' }));
  if (await dup.count()) {
    await shotHighlighted(page, dup.first(), 'A8c-duplicate-menu.png', { step: 4 });
    await dup.first().click();
    await page.waitForTimeout(2500);
    await logStep(B, {
      id: 'A8c-duplicate-canvas', title: '复制画布',
      target: '行级菜单「复制画布」',
      evidence: { url_after: page.url() },
      visible_text: `画布列表: ${JSON.stringify(await canvasTabs())}`,
      shot: await shot(page, 'A8c-after-duplicate.png'),
    });
  }

  // A8-4 删除画布（只删刚复制出来的那张，保留至少一张）
  const beforeDel = await canvasTabs();
  await tabBtn().click();
  await page.waitForTimeout(700);
  await rowMenu(page);
  const del = page.getByRole('menuitem', { name: '删除画布' }).or(page.getByRole('button', { name: '删除画布' }));
  if (await del.count() && beforeDel.length > 2) {
    await shotHighlighted(page, del.first(), 'A8d-delete-menu.png', { step: 5 });
    await del.first().click();
    await page.waitForTimeout(1000);
    const conf = await fingerprint(page);
    const confirmPanel = conf.sort((a, b) => b.area - a.area)[0];
    await logStep(B, {
      id: 'A8d-delete-canvas-confirm', title: '删除画布的二次确认',
      target: '行级菜单「删除画布」',
      visible_text: confirmPanel?.all,
      evidence: confirmPanel?.buttons,
      shot: await shot(page, 'A8d-delete-confirm.png'),
    });
    const confirmBtn = page.getByRole('button', { name: '确认', exact: true }).or(page.getByRole('button', { name: '确定', exact: true }));
    if (await confirmBtn.count()) {
      await shotHighlighted(page, confirmBtn.last(), 'A8d-delete-confirm-btn.png', { step: 6 });
      await confirmBtn.last().click();
      await page.waitForTimeout(2500);
    }
    await logStep(B, {
      id: 'A8e-delete-canvas-done', title: '删除后的画布列表',
      evidence: { before: beforeDel },
      visible_text: `画布列表: ${JSON.stringify(await canvasTabs())}`,
      shot: await shot(page, 'A8e-after-delete.png'),
    });
  } else {
    console.log('删除步骤跳过：菜单未出现或画布数不足（避免删空）');
  }
} finally {
  await browser.close();
}
