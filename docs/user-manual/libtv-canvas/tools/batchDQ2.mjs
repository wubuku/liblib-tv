// Batch DQ-2：实测缩放菜单，核对源码里的发现。
//
// ⭐⭐ DQ-1 反向核对抓到手册一处**实打实的错误**：
//   手册 `20-reference.md` 的「缩放」面板写着七行，最后一行是 `缩放至800%`，
//   而源码里**根本没有 `缩放至800%` 这个字面量**，只有：
//     `zoomTo50`  = 缩放至50%
//     `zoomTo100` = 缩放至100%
//     `zoomTo200` = 缩放至200%      ← 手册没有
//     `zoomToPercent` = 缩放至{percent}%   ← **动态拼接** ⇒ 百分比档位是用户缩放历史生成的
//     `zoomReset` = 恢复 100%        ← **手册完全没有**
//
// ⭐ 假设：菜单里的百分比档位**不止固定的三个**，而是「固定 50/100/200」+「用户缩放过的值」。
//   手册那次看到的 `800%` 很可能是**用户历史里的一个值**，不是固定项。
//
// ⭐ 本步只读：点开菜单、逐行读文字、记容器尺寸，**不点任何一项**（点了会改变画布缩放）。
//   读完按 ESC 关掉。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 菜单: null, 打开前: null };
const SAVE = () => writeFile(new URL('./batchDQ2.json', import.meta.url), JSON.stringify(out, null, 2));

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
await page.waitForTimeout(1500);
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2800);
for (let i = 0; i < 3; i += 1) {
  const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
  if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(600);
}
const pk = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
  if (!b) return null; const r = b.getBoundingClientRect();
  return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
});
if (pk) { await page.mouse.click(pk[0], pk[1]); await page.waitForTimeout(1200); }

// 打开前的画布缩放
out.打开前 = await page.evaluate(() => {
  const el = document.querySelector('[class*="zoom"], [data-zoom]');
  const t = [...document.querySelectorAll('div,span')].map((e) => (e.innerText || '').trim()).filter((x) => /^\d{1,3}%$/.test(x));
  return { 视口里出现的百分比文本: [...new Set(t)].slice(0, 6) };
});
LOG(`打开前画布上的百分比文本: ${JSON.stringify(out.打开前.视口里出现的百分比文本)}`);

// ⭐ 用 aria-label 认按钮（不按坐标）
const btn = page.locator('button[aria-label="缩放选项"]').first();
const n = await btn.count();
LOG(`「缩放选项」按钮: ${n} 个`);
if (!n) {
  LOG('⛔ 没找到「缩放选项」按钮 —— 改用 DOM 枚举');
  const 全部 = await page.evaluate(() => [...document.querySelectorAll('button[aria-label]')].map((b) => b.getAttribute('aria-label')));
  LOG(JSON.stringify(全部));
} else {
  await btn.click();
  await page.waitForTimeout(1200);
  const m = await page.evaluate(() => {
    const dd = document.querySelector('.mantine-Menu-dropdown');
    if (!dd) return { 找到: false };
    const b = dd.getBoundingClientRect();
    // 逐行读：直接子元素里含文字的
    const 行 = [...dd.querySelectorAll('*')].filter((e) => {
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      if (!t || t.length > 40) return false;
      // 只取叶子 + 菜单项
      return e.children.length === 0 || e.getAttribute('role') === 'menuitem';
    }).map((e) => {
      const r = e.getBoundingClientRect();
      const c = getComputedStyle(e);
      return {
        文字: (e.innerText || '').replace(/\s+/g, ' ').trim(),
        role: e.getAttribute('role') || e.tagName.toLowerCase(),
        尺寸: [Math.round(r.width), Math.round(r.height)],
        位置: [Math.round(r.x), Math.round(r.y)],
        可见: r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0,
      };
    });
    return { 找到: true, 容器: [Math.round(b.width), Math.round(b.height)], 行 };
  });
  out.菜单 = m;
  if (m.找到) {
    LOG(`菜单容器: ${m.容器.join('×')}`);
    LOG(`读到 ${m.行.length} 条：`);
    for (const r of m.行) LOG(`   ${r.可见 ? '👁' : '·'} [${r.role}] ${r.尺寸.join('×')} @${r.位置.join(',')} 「${r.文字}」`);
  } else {
    LOG('⛔ 菜单容器没找到');
  }
  await shot(page, 'DQ-a-缩放菜单全貌.png');
  LOG('📸 DQ-a');
}

// ⭐ 读完后按 ESC 关掉，不点任何一项（点了会改变画布缩放）
await page.keyboard.press('Escape');
await page.waitForTimeout(1000);
const 关掉 = await page.evaluate(() => !document.querySelector('.mantine-Menu-dropdown'));
LOG(`\nESC 后菜单已关闭: ${关掉}`);
out.ESC已关闭 = 关掉;
out.关闭后缩放未变 = await page.evaluate(() => {
  const t = [...document.querySelectorAll('div,span')].map((e) => (e.innerText || '').trim()).filter((x) => /^\d{1,3}%$/.test(x));
  return [...new Set(t)].slice(0, 6);
});
LOG(`关闭后百分比文本: ${JSON.stringify(out.关闭后缩放未变)}`);

SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDQ2.json ===');
