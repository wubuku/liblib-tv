// Batch EG-1：把 organize-canvas.md 里两条**纯观察**的 📖 一次结掉。
//
// ① :894 「`可灵主体库` 会不会也出现在「移动到 ›」子菜单里」—— 本轮只读子菜单，**不改任何数据**。
// ② :287 「网格吸附是否在别的画布 / 别的项目设置里才生效」—— 切到另一个画布，**只点开关按钮**，
//    不拖节点（拖动会改位置），只看按钮态和 class 是否变化。
//
// ⛔ 本脚本**不点任何删除、不提交任何输入、不拖动任何节点**。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEG1.json', import.meta.url).pathname;
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

  // ═════ ① 「移动到 ›」子菜单里有没有「可灵主体库」 ═════
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) {
      if ((b.innerText || '').trim() === '资产管理' || /资产管理/.test(b.getAttribute('aria-label') || '')) { b.click(); return; }
    }
  });
  await page.waitForTimeout(1600);
  记('开了「资产管理」抽屉');

  // 切到「资产」页签
  const 切页签 = await page.evaluate(() => {
    const drawer = document.querySelector('.mantine-Drawer-content');
    if (!drawer) return false;
    const tab = [...drawer.querySelectorAll('button')].find(b => (b.innerText || '').trim() === '资产');
    if (!tab) return false;
    tab.click(); return true;
  });
  await page.waitForTimeout(1600);
  记(`切到「资产」页签：${切页签}`);

  // 读出这一页里的所有行
  const 行清单 = await page.evaluate(() => {
    const drawer = document.querySelector('.mantine-Drawer-content');
    if (!drawer) return [];
    const out = [];
    for (const b of drawer.querySelectorAll('button[aria-label="更多操作"]')) {
      let row = b;
      for (let i = 0; i < 4 && row; i++, row = row.parentElement) {
        const t = (row.innerText || '').trim();
        if (t && t.length < 40) { const r = row.getBoundingClientRect(); out.push({ 行名: t.split('\n')[0], box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 更多操作: [Math.round(b.getBoundingClientRect().left), Math.round(b.getBoundingClientRect().top)] }); break; }
      }
    }
    return out;
  });
  结果.读数.资产页行 = 行清单;
  记(`「资产」页有 ${行清单.length} 行：${JSON.stringify(行清单.map(r => r.行名))}`);

  // 逐行打开 ⋯ → 悬停「移动到」→ 读子菜单
  for (const r of 行清单) {
    const 点开 = await page.evaluate((xy) => {
      const b = [...document.querySelectorAll('button[aria-label="更多操作"]')].find(x => {
        const br = x.getBoundingClientRect();
        return Math.abs(br.left - xy[0]) < 3 && Math.abs(br.top - xy[1]) < 3;
      });
      if (!b) return false; b.click(); return true;
    }, r.更多操作);
    await page.waitForTimeout(1000);
    if (!点开) continue;

    const 菜单项 = await page.evaluate(() => {
      const d = document.querySelector('.mantine-Menu-dropdown');
      return d ? { 项: [...d.querySelectorAll('.mantine-Menu-item')].map(x => x.innerText.trim()), box: (() => { const b = d.getBoundingClientRect(); return [Math.round(b.left), Math.round(b.top), Math.round(b.width), Math.round(b.height)]; })() } : null;
    });
    结果.读数['菜单_' + r.行名] = 菜单项;
    记(`「${r.行名}」菜单：${JSON.stringify(菜单项?.项)}`);

    if (菜单项 && 菜单项.项.includes('移动到')) {
      // ⭐ 子菜单是**悬停**触发（organize-canvas.md:880 明确记过）
      const 悬停 = await page.evaluate(() => {
        const it = [...document.querySelectorAll('.mantine-Menu-item')].find(x => x.innerText.trim() === '移动到');
        if (!it) return false;
        const r = it.getBoundingClientRect();
        // 用真实鼠标悬停
        it.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
        it.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
        return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
      });
      if (悬停) {
        await page.mouse.move(悬停[0], 悬停[1]);
        await page.waitForTimeout(400);
        await page.mouse.move(悬停[0] + 1, 悬停[1]);
        await page.waitForTimeout(1200);
      }
      const 子菜单 = await page.evaluate(() => {
        const dds = [...document.querySelectorAll('.mantine-Menu-dropdown, .mantine-Popover-dropdown')];
        return dds.map(d => ({ cls: d.className.toString().slice(0, 50), 文本: d.innerText.replace(/\n/g, ' / '), 项: [...d.querySelectorAll('.mantine-Menu-item')].map(x => x.innerText.trim()) }));
      });
      结果.读数['子菜单_' + r.行名] = 子菜单;
      记(`⭐⭐ 「${r.行名}」→「移动到 ›」子菜单：${JSON.stringify(子菜单.map(s => s.项))}`);
    }
    await page.keyboard.press('Escape');
    await page.waitForTimeout(700);
  }

  // ═════ ② 网格吸附：切到另一个画布，只看开关态 ═════
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1000);

  const 本画布吸附 = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find(x => (x.getAttribute('aria-label') || '') === '网格吸附');
    if (!b) return null;
    const cs = getComputedStyle(b);
    return { ariaPressed: b.getAttribute('aria-pressed'), data状态: b.getAttribute('data-state'), 背景: cs.backgroundColor, opacity: cs.opacity, cls: b.className.toString().slice(0, 90) };
  });
  结果.读数.本画布吸附 = 本画布吸附;
  记(`本画布「网格吸附」按钮态：${JSON.stringify(本画布吸附)}`);

  落盘(结果);
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEG1.json ===');
}
