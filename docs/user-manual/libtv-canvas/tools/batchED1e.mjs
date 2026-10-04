// Batch ED-1e：⛔ 恢复 a-CUfJfmKzUJ —— ⌘Z 第一次失败的真因是**焦点不在画布上**。
//
// `organize-canvas.md:716` 早就记着：「⌘Z 撤不回来 —— 焦点交回画布
// （document.activeElement 变成 BODY）后再按，画布才响应」。
// ED-1d 直接按 ⌘Z（开屏后没点过画布）⇒ 无效。
//
// 本步：先读 activeElement 确认焦点在哪 → 点空白把焦点交回画布 → 按 ⌘Z → 核对 11 个基线 id。
// ⚠️ 点空白处不删任何东西（点在画布容器空白，不是节点上）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchED1e.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 基线 = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1',
  'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];

const 结果 = {};

const 读 = (page) => page.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  return {
    缩放: vp ? getComputedStyle(vp).transform : null,
    ids: [...document.querySelectorAll('.react-flow__node')].map(n => n.getAttribute('data-id')).sort(),
    焦点: document.activeElement ? (document.activeElement.tagName + '.' + (document.activeElement.className || '').toString().slice(0, 40)) : null,
  };
});

const 核对 = (ids) => ({
  数: ids.length,
  缺失: 基线.filter(x => !ids.includes(x)),
  多出: ids.filter(x => !基线.includes(x)),
});

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6000 });
  await closePromos(page);
  await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  const 前 = await 读(page);
  结果.开场 = { 焦点: 前.焦点, 核对: 核对(前.ids) };
  console.log('开场 焦点:', 前.焦点);
  console.log('开场 核对:', JSON.stringify(核对(前.ids)));
  落盘(结果);

  // ⭐ 点一块空白把焦点交回画布（点节点之间的空隙，避开所有节点矩形）
  await page.mouse.click(60, 700);   // 左下角空白
  await page.waitForTimeout(600);
  const 焦点后 = await page.evaluate(() => document.activeElement.tagName);
  console.log('点空白后焦点:', 焦点后);
  结果.点空白后焦点 = 焦点后;
  落盘(结果);

  // 按 ⌘Z
  await page.keyboard.press('Meta+z');
  await page.waitForTimeout(2500);
  const 一 = await 读(page);
  console.log('\n⌘Z 第1次后:', JSON.stringify(核对(一.ids)));
  结果.第1次 = 核对(一.ids);
  落盘(结果);

  if (核对(一.ids).缺失.length) {
    await page.keyboard.press('Meta+z');
    await page.waitForTimeout(2500);
    const 二 = await 读(page);
    console.log('⌘Z 第2次后:', JSON.stringify(核对(二.ids)));
    结果.第2次 = 核对(二.ids);
    落盘(结果);

    if (核对(二.ids).缺失.length) {
      await page.keyboard.press('Meta+z');
      await page.waitForTimeout(2500);
      const 三 = await 读(page);
      console.log('⌘Z 第3次后:', JSON.stringify(核对(三.ids)));
      结果.第3次 = 核对(三.ids);
      落盘(结果);
    }
  }

  const 末 = 核对((await 读(page)).ids);
  if (末.缺失.length === 0 && 末.多出.length === 0) {
    console.log('\n✅ 已恢复到 11 个基线节点');
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(5500);
    await closePromos(page);
    await page.keyboard.press('Meta+0');
    await page.waitForTimeout(1500);
    const 刷 = 核对((await 读(page)).ids);
    console.log('⭐ 刷新后复核:', JSON.stringify(刷));
    结果.刷新后 = 刷;
    落盘(结果);
  } else {
    console.log('\n❌ 仍未恢复:', JSON.stringify(末));
  }
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchED1e.json ===');
}
