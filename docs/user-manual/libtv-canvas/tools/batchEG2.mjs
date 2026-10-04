// Batch EG-2：EG-1 走错了入口 —— `可灵主体库` 不在抽屉的「资产」页签里，
//   而在**「管理」弹窗的左侧栏**（organize-canvas.md:1042 有截图）。
//
// 本步：点「管理」→ 弹窗里切到「可灵主体库」→ 看它那一行有没有 ⋯ 菜单 →
//   若有，悬停「移动到 ›」读子菜单（**只读，不点任何会改数据的**）。
//
// ⛔ 不点删除、不提交输入、不上传文件。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEG2.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  // ① 先进抽屉，再切「资产」页签，然后点工具行里的「管理」（文字是「管理」）
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) {
      if ((b.innerText || '').trim() === '资产管理') { b.click(); return; }
    }
  });
  await page.waitForTimeout(1600);
  await page.evaluate(() => {
    const drawer = document.querySelector('.mantine-Drawer-content');
    if (!drawer) return;
    const tab = [...drawer.querySelectorAll('button')].find(b => (b.innerText || '').trim() === '资产');
    if (tab) tab.click();
  });
  await page.waitForTimeout(1600);
  记('开了抽屉并切到「资产」页签');

  const 开了 = await page.evaluate(() => {
    // 抽屉工具行里那枚文字是「管理」的按钮
    const drawer = document.querySelector('.mantine-Drawer-content');
    const 范围 = drawer || document;
    for (const b of 范围.querySelectorAll('button')) {
      if ((b.innerText || '').trim() === '管理') { b.click(); return true; }
    }
    return false;
  });
  await page.waitForTimeout(2000);
  记(`点「管理」：${开了}`);

  const 弹窗 = await page.evaluate(() => {
    const c = [...document.querySelectorAll('.mantine-Modal-content')].find(e => /个人资产库|可灵主体库/.test(e.innerText || ''));
    if (!c) return { 错: '没有弹窗' };
    const r = c.getBoundingClientRect();
    return {
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      全文: c.innerText.slice(0, 400),
      侧栏: [...c.querySelectorAll('button,[role="button"]')].map(b => (b.innerText || '').trim()).filter(Boolean).slice(0, 12),
    };
  });
  结果.读数.管理弹窗 = 弹窗;
  记(`管理弹窗：${JSON.stringify(弹窗?.box)} 侧栏=${JSON.stringify(弹窗?.侧栏)}`);

  // ② 切到「可灵主体库」
  const 切了 = await page.evaluate(() => {
    for (const b of document.querySelectorAll('button,[role="button"]')) {
      if ((b.innerText || '').trim() === '可灵主体库') { b.click(); return true; }
    }
    return false;
  });
  await page.waitForTimeout(1800);
  记(`切到「可灵主体库」：${切了}`);

  const 库内容 = await page.evaluate(() => {
    const c = [...document.querySelectorAll('.mantine-Modal-content')].find(e => /可灵主体库/.test(e.innerText || ''));
    if (!c) return null;
    return {
      全文: c.innerText.slice(0, 300),
      卡片数: [...c.querySelectorAll('[class*="rounded"]')].filter(e => {
        const t = (e.innerText || '').trim();
        return t && t.length < 30 && /\d{4}-\d{2}-\d{2}/.test(e.innerText || '');
      }).length,
      更多操作: [...c.querySelectorAll('button[aria-label="更多操作"]')].map(b => {
        const r = b.getBoundingClientRect();
        return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
      }),
      全部按钮: [...c.querySelectorAll('button')].map(b => {
        const r = b.getBoundingClientRect();
        if (r.width === 0) return null;
        return { 文字: (b.innerText || '').trim().slice(0, 14), aria: b.getAttribute('aria-label') || '', box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
      }).filter(Boolean).slice(0, 16),
    };
  });
  结果.读数.可灵主体库 = 库内容;
  记(`可灵主体库内容：${JSON.stringify(库内容?.全文?.slice(0, 120))}`);
  记(`  更多操作按钮：${JSON.stringify(库内容?.更多操作)}`);
  记(`  全部按钮：${JSON.stringify(库内容?.全部按钮)}`);

  // ③ 回到「个人资产库」，这次**用真实鼠标悬停**开子菜单（合成事件开不了，:880 记过）
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button,[role="button"]')) {
      if ((b.innerText || '').trim() === '个人资产库') { b.click(); return; }
    }
  });
  await page.waitForTimeout(1800);

  const more = 库内容?.更多操作?.[0];
  const 找more = await page.evaluate(() => {
    const b = document.querySelector('.mantine-Modal-content button[aria-label="更多操作"]');
    if (!b) return null;
    const r = b.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
  });
  if (找more) {
    await page.mouse.click(找more[0], 找more[1]);
    await page.waitForTimeout(1000);
    const 菜单 = await page.evaluate(() => {
      const d = document.querySelector('.mantine-Menu-dropdown');
      return d ? [...d.querySelectorAll('.mantine-Menu-item')].map(x => x.innerText.trim()) : null;
    });
    记(`弹窗里「待分类资产」菜单：${JSON.stringify(菜单)}`);

    // ⭐ 真实鼠标移到「移动到」上
    const 移到 = await page.evaluate(() => {
      const it = [...document.querySelectorAll('.mantine-Menu-item')].find(x => x.innerText.trim() === '移动到');
      if (!it) return null;
      const r = it.getBoundingClientRect();
      return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
    });
    if (移到) {
      await page.mouse.move(移到[0], 移到[1]);
      await page.waitForTimeout(500);
      await page.mouse.move(移到[0] + 2, 移到[1] + 1);
      await page.waitForTimeout(400);
      await page.mouse.move(移到[0], 移到[1]);
      await page.waitForTimeout(1400);
      const 子 = await page.evaluate(() => {
        const dds = [...document.querySelectorAll('.mantine-Menu-dropdown, .mantine-Popover-dropdown, [class*="Popover"]')];
        return dds.map(d => ({ cls: d.className.toString().slice(0, 46), 文本: (d.innerText || '').replace(/\n/g, ' / ').slice(0, 120) }));
      });
      结果.读数.弹窗内子菜单 = 子;
      记(`⭐⭐ 悬停「移动到」后的浮层：${JSON.stringify(子.map(s => s.文本))}`);
      await page.screenshot({ path: '.evidence/batchEG2-弹窗内移动到子菜单.png' });
      落盘(结果);
    }
  }
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEG2.json ===');
}
