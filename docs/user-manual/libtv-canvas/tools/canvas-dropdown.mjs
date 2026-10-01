// 画布下拉的可靠操作封装。
//
// 三次踩坑换来的：
// 1. 读画布列表不能靠「找 innerText 匹配 /^画布 \d+$/ 的按钮」——新建画布后顶栏按钮
//    和下拉行同时存在，会读出 ["画布 1","画布 1"] 这种假重名。正确做法只读
//    .mantine-Popover-dropdown 里 aria-label^="切换到画布 " 的行。
// 2. 行级「更多操作」是 hover 门控：opacity:0 + pointer-events:none，
//    Playwright 的 click() 会等 actionability 直接超时；必须先 hover 行再 el.click()。
// 3. 顶部「画布 N」按钮本身 aria-label 为空、正文是「画布 N」，用 filter({hasText}) 定位。
import { fingerprint, diffPanels } from './scenario.mjs';

const dropdownVisible = (page) =>
  page.evaluate(() => {
    const d = document.querySelector('.mantine-Popover-dropdown');
    if (!d) return false;
    const r = d.getBoundingClientRect();
    return r.width > 20 && r.height > 20;
  });

/** 顶栏「画布 N」按钮的稳定定位：Popover 下拉自身用 aria-labelledby 指向它。
 *  不能用 /^画布 \d+$/ 这种文本匹配——画布一旦被改名（「手册取证画布」）就再也匹配不上，
 *  实测就是这个正则让整条画布链路在改过名之后全部失联。 */
export async function tabButton(page) {
  const id = await page.evaluate(() => document.querySelector('.mantine-Popover-dropdown')?.getAttribute('aria-labelledby') || null);
  if (id) {
    const byId = page.locator(`[id="${id}"]`);
    if (await byId.count()) return byId.first();
  }
  return page.locator('button[aria-haspopup="dialog"], button[aria-expanded]').filter({ hasText: /画布|副本|手册/ }).first();
}

/** 幂等地打开画布下拉。顶栏按钮是 toggle —— 无脑点第二次反而会把它关掉，
 *  上一版就因此读回空行列表（误判成「重命名把画布删了」）。 */
export async function openDropdown(page, settle = 800) {
  if (!(await dropdownVisible(page))) {
    const tab = await tabButton(page);
    await tab.click({ timeout: 8000 });
    await page.waitForTimeout(settle);
  }
  await page.waitForFunction(() => {
    const d = document.querySelector('.mantine-Popover-dropdown');
    if (!d) return false;
    const r = d.getBoundingClientRect();
    return r.width > 20 && r.height > 20;
  }, { timeout: 8000 }).catch(() => {});
  return page.locator('.mantine-Popover-dropdown').first();
}

/** 从下拉里读出真实的画布行（新画布在最前）。 */
export async function readCanvasRows(page) {
  return page.evaluate(() =>
    [...document.querySelectorAll('.mantine-Popover-dropdown button[aria-label^="切换到画布 "]')].map((b) => ({
      label: b.getAttribute('aria-label'),
      name: (b.innerText || '').trim(),
      y: Math.round(b.getBoundingClientRect().y),
    })),
  );
}

/** hover 某一行 → el.click() 打开该行「更多操作」菜单，返回菜单文本。 */
export async function openRowMenu(page, rowName) {
  const before = await fingerprint(page);
  const row = page.locator('.mantine-Popover-dropdown button[aria-label^="切换到画布 "]', { hasText: rowName }).first();
  await row.hover();
  await page.waitForTimeout(350);
  const menuBtn = page
    .locator('.mantine-Popover-dropdown button[aria-label="更多操作"]')
    .nth((await page.locator('.mantine-Popover-dropdown button[aria-label^="切换到画布 "]', { hasText: rowName }).count()) - 1);
  // 直接在目标行内找「更多操作」，避免 nth 猜错
  await row.evaluate((el) => {
    const rowBox = el.closest('.group\\/canvas-row') || el.parentElement?.parentElement?.parentElement;
    const btn = (rowBox || document).querySelector('button[aria-label="更多操作"]');
    (btn || el).click();
  });
  await page.waitForTimeout(800);
  const after = await fingerprint(page);
  const neu = diffPanels(before, after);
  return neu.length ? neu[neu.length - 1] : null;
}

export async function closeDropdown(page) {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);
}
