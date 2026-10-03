// Batch EB-1：缩放菜单的「百分比档位」到底是不是按缩放历史动态生成的。
//
// DQ 批从源码查清 `缩放至{percent}%` 是**带占位符的模板**，菜单里非写死的百分比
// 由它按「本画布的缩放历史」填出来。但那只是**源码**结论（📖）——
// 界面上从没验过：DQ 批那轮菜单里只有 50/100/800，没见过 200、也没见过「恢复 100%」。
//
// ⭐⭐ 本步是**纯只读**：只动缩放比（视图状态，不写账户数据、不建节点、不花积分），
//    目的是让「缩放历史」里出现 200，再重开菜单看：
//      ① `缩放至200%`（zoomTo200）会不会出现；
//      ② `恢复 100%`（zoomReset）会不会出现。
//    ⇒ 若出现，就直接证明「档位 = 缩放历史」这条源码结论在界面上为真。
//
// ⚠️ 不点任何百分比档位本身（点它只是改缩放，也安全，但本轮先只读菜单内容）。
import { launch, open, closePromos, shot, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEB1.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = { 阶段: [], 读数: {} };

/** 读左下角那个缩放百分比标签。 */
const 读缩放标签 = (page) => page.evaluate(() => {
  const m = document.body.innerText.match(/(\d+(?:\.\d+)?)%/g);
  return m ? m : [];
});

/** 打开缩放菜单，把里面每一行逐字读出来。 */
const 读缩放菜单 = async (page) => {
  // 缩放按钮：左下角那枚带百分比的
  const btn = page.locator('button:has-text("%")').first();
  if (!(await btn.count())) return null;
  await btn.click();
  await page.waitForTimeout(500);
  const rows = await page.evaluate(() => {
    const dd = document.querySelector('.mantine-Menu-dropdown');
    if (!dd) return null;
    return {
      容器: (() => { const r = dd.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}`; })(),
      行: [...dd.querySelectorAll('.mantine-Menu-item, .mantine-Menu-itemLabel, input')]
        .map(e => (e.tagName === 'INPUT' ? '[输入框]' : '') + (e.innerText || e.value || '').trim())
        .filter(Boolean),
      全文: dd.innerText,
      分割线数: dd.querySelectorAll('.mantine-Menu-divider').length,
    };
  });
  return rows;
};

const { browser, page } = await launch();

try {
  await open(page, CANVAS_URL, { settle: 4500 });
  await closePromos(page);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(600);

  // ── 阶段 1：打开菜单，记下**基线档位**（应复现 DQ 批的 50/100/800）──
  const 标签1 = await 读缩放标签(page);
  const 菜单1 = await 读缩放菜单(page);
  结果.读数.阶段1_基线 = { 左下角百分比: 标签1, 菜单: 菜单1 };
  结果.阶段.push('阶段1 基线菜单已读');
  console.log('─── 阶段1 基线 ───');
  console.log('左下角:', 标签1);
  console.log('菜单行:', JSON.stringify(菜单1?.行, null, 1));
  落盘(结果);

  // 菜单还开着，先按 Esc 关掉
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);

  // ── 阶段 2：⭐ 用输入框把缩放设成 200（纯视图操作）──
  const btn = page.locator('button:has-text("%")').first();
  await btn.click();
  await page.waitForTimeout(400);
  const input = page.locator('.mantine-Menu-dropdown input').first();
  const 有输入框 = await input.count();
  if (有输入框) {
    await input.fill('200');
    await input.press('Enter');
    await page.waitForTimeout(900);
  }
  const 标签2 = await 读缩放标签(page);
  结果.读数.阶段2_设成200 = { 有输入框, 左下角百分比: 标签2 };
  结果.阶段.push('阶段2 已设 200%');
  console.log('\n─── 阶段2 设成 200 ───');
  console.log('左下角:', 标签2);
  落盘(结果);

  // ── 阶段 3：⭐ 重开菜单，看 200% / 恢复100% 档位是否出现 ──
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
  const btn3 = page.locator('button:has-text("%")').first();
  await btn3.click();
  await page.waitForTimeout(500);
  const 菜单3 = await 读缩放菜单(page);
  结果.读数.阶段3_重开菜单 = { 菜单: 菜单3 };
  结果.阶段.push('阶段3 重开菜单已读');
  console.log('\n─── 阶段3 重开菜单 ⭐关键 ───');
  console.log('菜单行:', JSON.stringify(菜单3?.行, null, 1));
  console.log('有 zoomTo200(200%档)?', 菜单3?.行?.some(r => r.includes('200%')));
  console.log('有 恢复100%?', 菜单3?.行?.some(r => r.includes('恢复')));
  落盘(结果);

  await shot(page, '.evidence/batchEB1-缩放菜单-设200后重开.png');

  // ── 阶段 4：⭐ 再设成 50，看看档位是否跟着「历史」增加 ──
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);
  const btn4 = page.locator('button:has-text("%")').first();
  await btn4.click();
  await page.waitForTimeout(400);
  const input4 = page.locator('.mantine-Menu-dropdown input').first();
  if (await input4.count()) {
    await input4.fill('50');
    await input4.press('Enter');
    await page.waitForTimeout(900);
  }
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
  const btn5 = page.locator('button:has-text("%")').first();
  await btn5.click();
  await page.waitForTimeout(500);
  const 菜单5 = await 读缩放菜单(page);
  结果.读数.阶段4_再设50后重开 = { 菜单: 菜单5 };
  结果.阶段.push('阶段4 设50后菜单已读');
  console.log('\n─── 阶段4 设 50 后重开 ───');
  console.log('菜单行:', JSON.stringify(菜单5?.行, null, 1));
  落盘(结果);

} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEB1.json ===');
}
