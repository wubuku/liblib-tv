// Batch EB-3：⭐ 阳性对照 —— 证明「设成 137/200 之后缩放**真的变了**」。
//
// EB-2 的结论是「档位恒为 50/100/800，新值不冒出来」。
// ⭐⭐ 但这条结论有个致命前提：**缩放到底生效了没有**。
//    如果输入框填了没反应，那「档位没变」就可能只是「我压根没 zoom 过去」，
//    而**不是**「档位是写死的」——这两件事长得一模一样。
//
// ⇒ 本步每设一次缩放，都读**三重读数**：
//    ① 左下角按钮的 aria/文本（当前百分比）
//    ② React Flow 视口的 CSS transform matrix（真实缩放值）
//    ③ 缩放菜单的档位列表
//    三者一起，才能把「没生效」和「写死了」区分开。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEB3.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = { 读数: {} };

/** 一次读全：按钮百分比 + 视口 transform + 菜单档位。 */
const 读三重 = async (page) => {
  return page.evaluate(() => {
    const btn = document.querySelector('button[aria-label="缩放选项"]');
    // React Flow 的视口容器：class 里带 react-flow__viewport
    const vp = document.querySelector('.react-flow__viewport');
    let matrix = null, zoom = null;
    if (vp) {
      const t = getComputedStyle(vp).transform;
      matrix = t;
      const m = t && t.match(/matrix\(([-\d.e,]+)\)/);
      if (m) zoom = parseFloat(m[1].split(',')[0]);
    }
    const dds = [...document.querySelectorAll('.mantine-Menu-dropdown')];
    return {
      按钮文本: btn ? btn.innerText.trim() : null,
      视口matrix: matrix,
      视口zoom: zoom,
      菜单个数: dds.length,
      菜单档位: dds.map(dd => [...dd.querySelectorAll('.mantine-Menu-itemLabel')]
        .map(e => e.innerText.trim()).filter(Boolean)),
    };
  });
};

const 点开菜单 = async (page) => {
  await page.evaluate(() => {
    const b = document.querySelector('button[aria-label="缩放选项"]');
    if (b) b.click();
  });
  await page.waitForTimeout(600);
};

const 设缩放 = async (page, 值) => {
  await 点开菜单(page);
  const 有 = await page.evaluate(() => !!document.querySelector('.mantine-Menu-dropdown input'));
  if (!有) return false;
  const input = page.locator('.mantine-Menu-dropdown input').first();
  await input.fill(String(值));
  await input.press('Enter');
  await page.waitForTimeout(1200);
  return true;
};

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 4500 });
  await closePromos(page);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(800);

  const 流程 = [
    { 名: '初始', 设: null },
    { 名: '设137', 设: 137 },
    { 名: '设200', 设: 200 },
    { 名: '设25', 设: 25 },     // ⭐ 越界值：低于最小档，看会不会被夹住
    { 名: '设2000', 设: 2000 }, // ⭐ 超界值：高于 800，看会不会被夹住 —— 这一步能反证「800 是不是上限」
  ];

  for (const step of 流程) {
    if (step.设 !== null) await 设缩放(page, step.设);
    else await 点开菜单(page);

    const r = await 读三重(page);
    结果.读数[step.名] = r;
    落盘(结果);
    console.log(`\n─── ${step.名}${step.设 !== null ? `（输入 ${step.设}）` : ''} ───`);
    console.log('  按钮文本:', r.按钮文本, '| 视口zoom:', r.视口zoom);
    console.log('  matrix:', r.视口matrix);
    console.log('  菜单档位:', JSON.stringify(r.菜单档位));
    console.log('  >>> 档位里有该值吗?',
      r.菜单档位.flat().some(x => x.includes(String(step.设 ?? ''))));

    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);
  }

  结果.判读 = {
    '设137后按钮是否真的变了': 结果.读数.设137?.按钮文本,
    '设200后按钮是否真的变了': 结果.读数.设200?.按钮文本,
    '设2000后视口zoom（是否被夹到8）': 结果.读数.设2000?.视口zoom,
    '设25后视口zoom（是否被夹到.5）': 结果.读数.设25?.视口zoom,
    '所有阶段档位是否恒定': new Set(Object.values(结果.读数)
      .map(v => JSON.stringify(v.菜单档位))).size,
  };
  console.log('\n═══ 判读 ═══');
  for (const [k, v] of Object.entries(结果.判读)) console.log(`  ${k}: ${JSON.stringify(v)}`);

} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEB3.json ===');
}
