// 探针 11 —— 专门把「重命名画布」这一个交互钉死。
//
// 前两版都没拿到结论：一次读到 1 行（动画期瞬态），一次填完 Enter 后名字没变。
// 这一版把每一步都落成证据：截图 + input 读数 + 网络请求 + **耐心等动画结束后**
// 再读行列表（并把等待条件写成「行数稳定两次」）。
import { launch, open } from './lib.mjs';
import { CANVAS_URL } from './test-project.mjs';
import { clearToasts, closePromos, shot } from './scenario.mjs';
import { openDropdown, openRowMenu, closeDropdown } from './canvas-dropdown.mjs';

const { browser, page } = await launch();
const reqs = [];

/** 等到行列表连续两次读数相同才算稳。 */
async function stableRows(page, tries = 8) {
  let prev = null;
  for (let i = 0; i < tries; i += 1) {
    const now = await page.evaluate(() =>
      [...document.querySelectorAll('.mantine-Popover-dropdown button[aria-label^="切换到画布 "]')]
        .map((b) => (b.getAttribute('aria-label') || '').replace('切换到画布 ', ''))
        .sort(),
    );
    if (prev && JSON.stringify(now) === JSON.stringify(prev)) return { rows: now, stableAt: i };
    prev = now;
    await page.waitForTimeout(600);
  }
  return { rows: prev, stableAt: -1 };
}

try {
  page.on('request', (r) => {
    const p = new URL(r.url()).pathname;
    if (/\/api\/canvas\//.test(p)) reqs.push(`${r.method()} ${p}`);
  });

  await open(page, CANVAS_URL, { settle: 4000 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(1200);

  await openDropdown(page, 1000);
  console.log('BEFORE:', JSON.stringify(await stableRows(page)));

  const menu = await openRowMenu(page, '画布 1');
  console.log('行菜单:', menu?.all);
  await shot(page, 'p11-1-row-menu.png');

  const rename = page.getByRole('menuitem', { name: '重命名画布' }).or(page.getByRole('button', { name: '重命名画布' }));
  await rename.first().click();
  await page.waitForTimeout(1000);

  const inputs = await page.evaluate(() =>
    [...document.querySelectorAll('.mantine-Popover-dropdown input')].map((i) => ({
      type: i.type, value: i.value, aria: i.getAttribute('aria-label'),
      sel: (i.getAttribute('selectionStart'), i.selectionStart), selEnd: i.selectionEnd,
      focused: i === document.activeElement,
    })),
  );
  console.log('下拉内的 input:', JSON.stringify(inputs));
  await shot(page, 'p11-2-rename-input.png');

  // 注意：React 只设了 input.type **属性**，DOM 上没有 type="text" 属性，
  // 所以 `input[type="text"]` 选不中它。只能用 aria-label。
  const inp = page.getByLabel('画布名称').first();
  if (await inp.count()) {
    await inp.click();
    await page.keyboard.press('Meta+A');
    await inp.type('手册取证画布', { delay: 25 });
    await page.waitForTimeout(600);
    console.log('填完 input.value =', await inp.inputValue());
    await shot(page, 'p11-3-typed.png');

    reqs.length = 0;
    await inp.press('Enter');
    await page.waitForTimeout(3000);

    console.log('提交后网络:', JSON.stringify(reqs.slice(0, 10)));
    await openDropdown(page, 1200);
    const after = await stableRows(page);
    console.log('AFTER:', JSON.stringify(after));
    console.log('顶栏按钮:', await page.evaluate(() => [...document.querySelectorAll('button')].map((b) => (b.innerText || '').trim()).filter((t) => /^画布/.test(t))));
    await shot(page, 'p11-4-after-enter.png');

    // 若 Enter 没生效，试 blur 提交
    if (after.rows.join() === '画布 1,画布 2') {
      console.log('Enter 未生效 → 改试 blur 提交');
      await openRowMenu(page, '画布 1');
      await page.getByRole('menuitem', { name: '重命名画布' }).or(page.getByRole('button', { name: '重命名画布' })).first().click();
      await page.waitForTimeout(900);
      const inp2 = page.getByLabel('画布名称').first();
      await inp2.click();
      await page.keyboard.press('Meta+A');
      await inp2.type('手册取证画布', { delay: 25 });
      reqs.length = 0;
      await page.getByRole('button', { name: '确认', exact: true }).or(page.getByRole('button', { name: '保存', exact: true })).first().click({ timeout: 3000 }).catch(() => console.log('无确认按钮'));
      await page.waitForTimeout(2500);
      console.log('blur/确认后网络:', JSON.stringify(reqs.slice(0, 10)));
      await openDropdown(page, 1200);
      console.log('AFTER2:', JSON.stringify(await stableRows(page)));
      await shot(page, 'p11-5-after-blur.png');
    }
  }
  await closeDropdown(page);
} finally {
  await browser.close();
}
