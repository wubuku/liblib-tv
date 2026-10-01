// Batch A —— 入口与画布 CRUD（旗舰流程之一）。
//
// 覆盖：首页入口 → 项目列表 → 画布下拉四操作 → 模式切换 → 发布与分享 → 教程 → 缩放菜单。
// 边界：**不发布、不分享给外部、不删除用户项目**。删除类只在专用测试项目里对新画布做，
//       且放在最后一步，万一失败也不影响前面已拍到的证据。
import { launch, open, ORIGIN } from './lib.mjs';
import { CANVAS_URL, TEST } from './test-project.mjs';
import { beginBatch, logStep, clearToasts, closePromos, shot, fingerprint, diffPanels } from './scenario.mjs';

const B = 'batchA';
await beginBatch(B, { canvas: CANVAS_URL, note: '入口 + 画布 CRUD；不触发付费生成、不发布、不删除用户项目' });

const { browser, page } = await launch();

async function openPanel(page, clickLocator, { settle = 1200 } = {}) {
  const before = await fingerprint(page);
  await clickLocator.click({ timeout: 6000 });
  await page.waitForTimeout(settle);
  const after = await fingerprint(page);
  const neu = diffPanels(before, after);
  // 取最大的新增面板作为「本次打开的面板」
  return neu.length ? neu[neu.length - 1] : null;
}

try {
  // ───────────────────────── A1 首页：进入创作的第一跳
  await open(page, `${ORIGIN}/`, { settle: 3000 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(800);
  await logStep(B, {
    id: 'A1-home', title: '首页：进入创作的第一跳',
    target: '左侧栏「新建项目」/ 主区「新建画布创作」/ 8 个快捷生成按钮',
    visible_text: await page.evaluate(() => (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 700)),
    evidence: await page.evaluate(() => [...document.querySelectorAll('button')].filter((b) => b.getBoundingClientRect().width > 60).map((b) => (b.innerText || b.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ')).filter(Boolean).slice(0, 20)),
    shot: await shot(page, 'A1-home-overview.png'),
  });

  // ───────────────────────── A2 项目列表页
  await open(page, `${ORIGIN}/project`, { settle: 2500 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(800);
  await logStep(B, {
    id: 'A2-projects', title: '项目列表：回收站 / 新建文件夹 / 开始创作',
    target: '/project 顶栏「回收站」「新建文件夹」',
    visible_text: await page.evaluate(() => (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 600)),
    evidence: await page.evaluate(() => [...document.querySelectorAll('button,a')].filter((b) => b.getBoundingClientRect().width > 1).map((b) => b.getAttribute('aria-label') || (b.innerText || '').trim().replace(/\s+/g, ' ')).filter(Boolean).slice(0, 30)),
    shot: await shot(page, 'A2-projects-list.png'),
  });

  // 项目卡片的「更多」菜单 —— hover 门控，自动化点击无效，用 DOM click 绕过 pointer-events
  const moreBtn = page.getByRole('button', { name: '更多', exact: true }).first();
  if (await moreBtn.count()) {
    const menu = await openPanel(page, moreBtn, { settle: 1000 });
    await logStep(B, {
      id: 'A2b-project-more', title: '项目卡片「更多」菜单',
      target: 'role=button name="更多"',
      visible_text: menu?.all,
      evidence: menu?.buttons,
      shot: menu ? await shot(page, 'A2b-project-more-menu.png') : null,
    });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
  }

  // ───────────────────────── A3 画布：下拉与四个行级操作
  await open(page, CANVAS_URL, { settle: 3500 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(800);
  await logStep(B, {
    id: 'A3-canvas-open', title: '进入画布（工作流模式 · 空画布）',
    target: '顶部「画布 1」下拉',
    visible_text: await page.evaluate(() => (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 500)),
    evidence: { url: page.url(), title: await page.title(), projectId: TEST.projectId },
    shot: await shot(page, 'A3-canvas-empty.png'),
  });

  const canvasTabBtn = page.locator('button').filter({ hasText: /^画布 \d+$/ }).first();
  const dd = await openPanel(page, canvasTabBtn, { settle: 900 });
  await logStep(B, {
    id: 'A3b-canvas-dropdown', title: '画布下拉：新建 / 切换 / 更多操作',
    target: '顶栏「画布 1」',
    visible_text: dd?.all,
    evidence: dd?.buttons,
    shot: dd ? await shot(page, 'A3b-canvas-dropdown.png') : null,
  });

  // 行级「更多操作」（hover 门控）
  const rowMore = page.getByRole('button', { name: '更多操作', exact: true }).first();
  if (await rowMore.count()) {
    const before = await fingerprint(page);
    await rowMore.evaluate((el) => el.click());
    await page.waitForTimeout(900);
    const after = await fingerprint(page);
    const neu = diffPanels(before, after);
    const menu = neu.length ? neu[neu.length - 1] : null;
    await logStep(B, {
      id: 'A3c-canvas-row-more', title: '画布行「更多操作」菜单',
      target: 'role=button name="更多操作"（hover 门控，用 el.click() 绕过 pointer-events）',
      visible_text: menu?.all,
      evidence: menu?.buttons,
      shot: menu ? await shot(page, 'A3c-canvas-row-more.png') : null,
    });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
  }

  // ───────────────────────── A4 模式切换：工作流 ↔ 故事板
  for (const [name, file] of [['工作流', 'A4a-mode-workflow.png'], ['故事板', 'A4b-mode-storyboard.png']]) {
    const b = page.getByRole('button', { name, exact: true }).first();
    if (!(await b.count())) continue;
    await b.click({ timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(1600);
    const info = await page.evaluate(() => ({
      text: (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 600),
      pressed: [...document.querySelectorAll('[aria-pressed],[data-active],[aria-selected]')].map((e) => `${e.getAttribute('aria-label') || (e.innerText || '').trim()}=${e.getAttribute('aria-pressed') ?? e.getAttribute('data-active') ?? e.getAttribute('aria-selected')}`).slice(0, 10),
    }));
    await logStep(B, {
      id: `A4-mode-${name}`, title: `模式切换：${name}`,
      target: `role=button name="${name}"`,
      visible_text: info.text,
      evidence: info.pressed,
      shot: await shot(page, file),
    });
  }

  // ───────────────────────── A5 发布与分享（只读面板，绝不点发布）
  const share = page.getByRole('button', { name: '发布与分享', exact: true }).first();
  if (await share.count()) {
    const panel = await openPanel(page, share, { settle: 1400 });
    await logStep(B, {
      id: 'A5-share', title: '发布与分享面板（只读，未点发布）',
      target: 'role=button name="发布与分享"',
      visible_text: panel?.all,
      evidence: panel?.buttons,
      shot: panel ? await shot(page, 'A5-share-panel.png') : null,
    });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);
  }

  // ───────────────────────── A6 缩放菜单
  const zoom = page.getByRole('button', { name: '缩放选项', exact: true }).first();
  if (await zoom.count()) {
    const panel = await openPanel(page, zoom, { settle: 900 });
    await logStep(B, {
      id: 'A6-zoom', title: '缩放菜单（百分比 / 适合屏幕）',
      target: 'role=button name="缩放选项"',
      visible_text: panel?.all,
      evidence: panel?.buttons,
      shot: panel ? await shot(page, 'A6-zoom-menu.png') : null,
    });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
  }

  // ───────────────────────── A7 教程面板
  const help = page.getByRole('button', { name: '教程', exact: true }).first();
  if (await help.count()) {
    const panel = await openPanel(page, help, { settle: 1600 });
    await logStep(B, {
      id: 'A7-tutorial', title: '教程面板',
      target: 'role=button name="教程"',
      visible_text: panel?.all,
      evidence: panel?.buttons,
      shot: panel ? await shot(page, 'A7-tutorial.png') : null,
    });
  }
} finally {
  await browser.close();
}
