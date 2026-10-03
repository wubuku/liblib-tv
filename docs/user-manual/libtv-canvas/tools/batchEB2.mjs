// Batch EB-2：先把「缩放菜单的触发按钮」找稳，再做动态档位实验。
//
// EB-1 阶段 3 失败的原因：200% 下 `button:has-text("%")` 没命中触发按钮，
// 菜单没打开，读数自然是 null。⇒ 先枚举左下角控件，拿到**稳定标识**再重做实验。
//
// ⭐ 本步仍然**纯只读**：只改缩放比（视图状态），不写账户数据。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEB2.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = { 读数: {} };

/** 枚举左下角（y > 视口高 0.7）的所有可交互元素，拿稳定标识。 */
const 枚举左下角 = (page) => page.evaluate(() => {
  const H = window.innerHeight;
  const out = [];
  for (const el of document.querySelectorAll('button,[role="button"],input,div')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (r.top < H * 0.7) continue;                 // 只看左下角区域
    if (el.querySelector('button,input')) continue; // 只要叶子节点
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.opacity === '0') continue;
    out.push({
      tag: el.tagName,
      text: (el.innerText || '').trim().slice(0, 30),
      aria: el.getAttribute('aria-label') || '',
      testid: el.getAttribute('data-testid') || '',
      cls: (el.className && el.className.toString().slice(0, 70)) || '',
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
    });
  }
  return out;
});

/** 读当前所有 .mantine-Menu-dropdown 的存在与内容。 */
const 读菜单 = (page) => page.evaluate(() => {
  const dds = [...document.querySelectorAll('.mantine-Menu-dropdown')];
  return {
    个数: dds.length,
    内容: dds.map(dd => [...dd.querySelectorAll('.mantine-Menu-itemLabel')]
      .map(e => e.innerText.trim()).filter(Boolean)),
    全文: dds.map(dd => dd.innerText),
  };
});

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 4500 });
  await closePromos(page);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(800);

  // ── 探测 1：左下角控件全枚举 ──
  const 角 = await 枚举左下角(page);
  结果.读数.左下角控件 = 角;
  console.log('═══ 左下角控件 ═══');
  for (const c of 角) console.log(`  [${c.tag}] text="${c.text}" aria="${c.aria}" box=${c.box} cls=${c.cls.slice(0,40)}`);
  落盘(结果);

  // ── 探测 2：找到那个百分比按钮，点开，读菜单 ──
  // 用最稳的办法：找 innerText 匹配 ^\d+(\.\d+)?%$ 的可点击元素
  const 点开缩放菜单 = async () => {
    const ok = await page.evaluate(() => {
      const els = [...document.querySelectorAll('button,div[role="button"],[class*="mantine-ActionIcon"]')];
      const hit = els.find(e => {
        const r = e.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) return false;
        return /^\s*\d+(\.\d+)?\s*%\s*$/.test(e.innerText || '') && e.querySelectorAll('button').length === 0;
      });
      if (!hit) return false;
      hit.click();
      return true;
    });
    await page.waitForTimeout(600);
    return ok;
  };

  const ok1 = await 点开缩放菜单();
  const 菜单1 = await 读菜单(page);
  结果.读数.基线菜单 = { 点开成功: ok1, ...菜单1 };
  console.log('\n═══ 基线菜单 ═══', ok1 ? '(点开成功)' : '(点开失败)');
  console.log('  个数:', 菜单1.个数, '| 档位:', JSON.stringify(菜单1.内容));
  落盘(结果);

  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);

  // ── 探测 3：⭐ 核心实验 —— 把缩放设成一个「从没出现过的值」，看它会不会变成新档位 ──
  // 用 137%：如果档位真按「缩放历史」生成，137% 应该冒出来。
  const 设缩放 = async (值) => {
    await 点开缩放菜单();
    const 有输入 = await page.evaluate(() => !!document.querySelector('.mantine-Menu-dropdown input'));
    if (有输入) {
      const input = page.locator('.mantine-Menu-dropdown input').first();
      await input.fill(String(值));
      await input.press('Enter');
      await page.waitForTimeout(1100);
    }
    return 有输入;
  };

  const a137 = await 设缩放(137);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(600);
  await 点开缩放菜单();
  const 菜单137 = await 读菜单(page);
  结果.读数.设137后 = { 输入框存在: a137, ...菜单137 };
  console.log('\n═══ ⭐ 设成 137% 后重开菜单 ═══');
  console.log('  个数:', 菜单137.个数, '| 档位:', JSON.stringify(菜单137.内容));
  console.log('  >>> 137% 出现了吗?', 菜单137.内容.some(r => r.includes('137')));
  console.log('  >>> 有「恢复 100%」吗?', 菜单137.内容.some(r => r.includes('恢复')));
  落盘(结果);

  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);

  // ── 探测 4：再设 200（DQ 批说 zoomTo200 没出现过）──
  const a200 = await 设缩放(200);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(600);
  await 点开缩放菜单();
  const 菜单200 = await 读菜单(page);
  结果.读数.设200后 = { 输入框存在: a200, ...菜单200 };
  console.log('\n═══ ⭐ 设成 200% 后重开菜单 ═══');
  console.log('  个数:', 菜单200.个数, '| 档位:', JSON.stringify(菜单200.内容));
  console.log('  >>> 200% 出现了吗?', 菜单200.内容.some(r => r.includes('200')));
  console.log('  >>> 有「恢复 100%」吗?', 菜单200.内容.some(r => r.includes('恢复')));
  落盘(结果);

} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEB2.json ===');
}
