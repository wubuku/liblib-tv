// Batch EG-4：⭐ EG-3 查明了「资产管理」弹窗的真身 —— **它不是 Mantine Modal**。
//
//   [5] <DIV> box=[72,80,1296,650]  cls="rounded-xl pointer-events-auto flex flex-col w-[calc(100vw-32px)] h-[calc(100vh-80px)]"
//   [6] <DIV> box=[0,0,1440,810]    cls="z-201 pointer-events-none fixed inset-0 flex items-center justify-center outline-none"
//   [7] <DIV> box=[0,810,1440,0]    ← 高度 0 的一层，却含 38 个按钮（含唯一的「更多操作」）
//
// ⭐ 那枚「更多操作」在 [7] 里，**不在弹窗容器 [5] 里** —— 与 AUDIT.md:66 记的
//   「『更多操作』是行的兄弟节点、被自己的行判据挡在门外」是**同一个坑**。
//
// 本步：在弹窗里找到「可灵主体库」下的分类卡片 → 点它那枚「更多操作」→
//   悬停「移动到 ›」读子菜单（⭐ 只读）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEG4.json', import.meta.url).pathname;
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

  await page.evaluate(() => { for (const b of document.querySelectorAll('button')) if ((b.innerText || '').trim() === '资产管理') { b.click(); return; } });
  await page.waitForTimeout(1600);
  await page.evaluate(() => { const d = document.querySelector('.mantine-Drawer-content'); const t = d && [...d.querySelectorAll('button')].find(b => (b.innerText || '').trim() === '资产'); if (t) t.click(); });
  await page.waitForTimeout(1500);
  await page.evaluate(() => { const d = document.querySelector('.mantine-Drawer-content'); const m = d && [...d.querySelectorAll('button')].find(b => (b.innerText || '').trim() === '管理'); if (m) m.click(); });
  await page.waitForTimeout(2200);
  记('已开「资产管理」弹窗');

  // ⭐ 按**精确几何**定位弹窗（EG-3 的读数：box=[72,80,1296,650]），不靠启发式
  const 卡片 = await page.evaluate(() => {
    const shell = [...document.querySelectorAll('div')].find(e => {
      const r = e.getBoundingClientRect();
      return Math.abs(r.left - 72) < 4 && Math.abs(r.top - 80) < 4
        && Math.abs(r.width - 1296) < 6 && Math.abs(r.height - 650) < 6
        && getComputedStyle(e).pointerEvents === 'auto';
    });
    if (!shell) return { 错: '没找到弹窗容器（按几何 [72,80,1296,650]）' };
    // ⭐ 「更多操作」是**悬停才挂载**的（EG-4 实测：静态扫同行右侧 0 个）
    const 卡片文本 = [...shell.querySelectorAll('*')]
      .filter(e => e.children.length === 0 && /待分类资产/.test(e.innerText || ''))
      .map(e => { const r = e.getBoundingClientRect(); return { text: e.innerText.trim(), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] }; });
    const sr = shell.getBoundingClientRect();
    return {
      弹窗box: [Math.round(sr.left), Math.round(sr.top), Math.round(sr.width), Math.round(sr.height)],
      全文: shell.innerText.slice(0, 220).replace(/\n/g, ' / '),
      卡片文本,
      同行按钮: [],   // ⭐ 必须在 evaluate 外面悬停后再扫，这里留空
    };
  });

  // ⭐ 悬停那一行（同 3 个位置），再扫同行右侧的按钮
  for (const t of (卡片.卡片文本 || [])) {
    for (const dx of [40, 70, 100, 60]) {
      await page.mouse.move(t.中心[0] + dx, t.中心[1]);
      await page.waitForTimeout(400);
    }
    const 同行 = await page.evaluate((t) => {
      const out = [];
      for (const b of document.querySelectorAll('button')) {
        const r = b.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) continue;
        if (Math.abs((r.top + r.height / 2) - t.中心[1]) > 16) continue;
        if (r.left < t.box[0]) continue;
        out.push({ aria: b.getAttribute('aria-label') || '', box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] });
      }
      return out;
    }, t);
    卡片.同行按钮.push(...同行.map(o => ({ 名: t.text, ...o })));
    记(`悬停「${t.text}」后同行按钮：${JSON.stringify(同行)}`);
  }
  卡片.卡片 = (卡片.同行按钮 || []).filter(o => o.aria === '更多操作');
  结果.读数.卡片 = 卡片;
  记(`卡片文本：${JSON.stringify(卡片.卡片文本)}`);
  记(`同行按钮：${JSON.stringify(卡片.同行按钮)}`);
  记(`  弹窗全文：${卡片.全文}`);

  if (卡片.错) { console.log('  ', 卡片.错); }
  for (const c of (卡片.卡片 || [])) {
    await page.mouse.click(c.中心[0], c.中心[1]);
    await page.waitForTimeout(1100);
    const 菜单 = await page.evaluate(() => {
      const d = document.querySelector('.mantine-Menu-dropdown');
      return d ? [...d.querySelectorAll('.mantine-Menu-item')].map(x => x.innerText.trim()) : null;
    });
    记(`「${c.名}」菜单：${JSON.stringify(菜单)}`);
    结果.读数['菜单_' + c.名] = 菜单;

    if (菜单 && 菜单.includes('移动到')) {
      // ⭐ 真实鼠标悬停（合成事件开不了子菜单，:880 记过）
      const 移到 = await page.evaluate(() => {
        const it = [...document.querySelectorAll('.mantine-Menu-item')].find(x => x.innerText.trim() === '移动到');
        if (!it) return null;
        const r = it.getBoundingClientRect();
        return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
      });
      for (const [dx, dy] of [[0, 0], [3, 1], [0, 0]]) {
        await page.mouse.move(移到[0] + dx, 移到[1] + dy);
        await page.waitForTimeout(600);
      }
      await page.waitForTimeout(900);
      const 子 = await page.evaluate(() => {
        const dds = [...document.querySelectorAll('.mantine-Menu-dropdown, .mantine-Popover-dropdown, [class*="Popover-dropdown"]')];
        return dds.map(d => ({ 文本: (d.innerText || '').replace(/\n/g, ' / ').slice(0, 100), 项: [...d.querySelectorAll('.mantine-Menu-item')].map(x => x.innerText.trim()) }));
      });
      结果.读数['子菜单_' + c.名] = 子;
      记(`⭐⭐ 「${c.名}」→「移动到 ›」子菜单：${JSON.stringify(子.map(s => s.项))}`);
      await page.screenshot({ path: `.evidence/batchEG4-${c.名}-移动到子菜单.png` });
      落盘(结果);
    }
    await page.keyboard.press('Escape');
    await page.waitForTimeout(700);
  }
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEG4.json ===');
}
