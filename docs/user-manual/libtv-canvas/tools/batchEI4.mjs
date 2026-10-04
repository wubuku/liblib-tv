// Batch EI-4：重拍一张**干净**的多选工具条截图（M-357 被 TV Director 抽屉挡了半屏）。
//
// ⭐ 本轮只读：框选 → 读工具条 → 读「打组」的下拉菜单项（**只读菜单，不点任何一项**）
//    → 点空白取消。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;          // tools/ 的绝对路径
const OUT = HERE + 'batchEI4.json';
// ⭐ §112.7：page.screenshot 的相对路径基于进程 cwd ⇒ 一律用绝对路径
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1200);
  // ⭐ 关掉 TV Director 抽屉（点开屏就有的那枚触发图标；Esc 不管用）
  const 关了抽屉 = await page.evaluate(() => {
    const 图标 = [...document.querySelectorAll('button')]
      .find(b => /TV Director|Agent/.test((b.innerText || '').trim()) && b.getBoundingClientRect().width < 60);
    if (!图标) return '没找到触发图标';
    图标.click();
    return '已点';
  });
  await page.waitForTimeout(1200);
  await page.evaluate(() => { for (const b of document.querySelectorAll('button')) if ((b.innerText || '').trim() === '知道了') { b.click(); return; } });
  await page.waitForTimeout(800);
  记(`关 TV Director：${关了抽屉}`);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  // 框选
  const 位置 = await page.evaluate(() => {
    const out = {};
    for (const id of ['i-9nlG6HdjK2', 'i-sODTbgLUm1']) {
      const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      const r = el.getBoundingClientRect();
      out[id] = [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
    }
    return out;
  });
  const a = 位置['i-9nlG6HdjK2'], b = 位置['i-sODTbgLUm1'];
  const x1 = Math.min(a[0], b[0]) - 20, y1 = Math.min(a[1], b[1]) - 10;
  const x2 = Math.max(a[0] + a[2], b[0] + b[2]) + 20, y2 = Math.max(a[1] + a[3], b[1] + b[3]) + 20;
  await page.mouse.move(x1, y1);
  await page.mouse.down();
  await page.mouse.move((x1 + x2) / 2, (y1 + y2) / 2, { steps: 12 });
  await page.mouse.move(x2, y2, { steps: 12 });
  await page.waitForTimeout(400);
  await page.mouse.up();
  await page.waitForTimeout(1600);

  const 选中 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
  结果.读数.选中 = 选中;
  记(`框选后：${JSON.stringify(选中)}`);

  await page.screenshot({ path: EVID + 'ei4-多选工具条-干净.png' });
  记('已拍干净版工具条');

  // ⭐ 读「打组」的下拉菜单（只读，不点任何一项）
  const 打组 = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim().startsWith('打组'));
    if (!b) return { 找到: false };
    const r = b.getBoundingClientRect();
    return { 找到: true, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], 文字: b.innerText.trim() };
  });
  结果.读数.打组按钮 = 打组;
  记(`「打组」按钮：${JSON.stringify(打组)}`);

  if (打组.找到) {
    await page.mouse.click(打组.中心[0], 打组.中心[1]);
    await page.waitForTimeout(1200);
    const 菜单 = await page.evaluate(() => {
      const ds = [...document.querySelectorAll('.mantine-Menu-dropdown, .mantine-Popover-dropdown')];
      return ds.map(d => ({ cls: d.className.toString().slice(0, 44), 文本: (d.innerText || '').replace(/\n/g, ' / ').slice(0, 160), 项: [...d.querySelectorAll('.mantine-Menu-item')].map(x => x.innerText.trim()) }));
    });
    结果.读数.打组菜单 = 菜单;
    记(`⭐「打组」的下拉菜单：${JSON.stringify(菜单.map(m => m.项))}`);
    await page.screenshot({ path: EVID + 'ei4-打组下拉.png' });
    落盘(结果);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(700);
  }

  // ⭐ 顺手读那枚无名按钮的 tooltip
  const 无名 = await page.evaluate(() => {
    const btns = [...document.querySelectorAll('button')].filter(b => {
      const r = b.getBoundingClientRect();
      return r.width === 32 && r.height === 32 && r.top < 200 && !b.innerText.trim() && !b.closest('.react-flow__node');
    });
    return btns.map(b => {
      const r = b.getBoundingClientRect();
      return { 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], svg: [...b.querySelectorAll('svg')].map(s => (s.getAttribute('class') || '').slice(0, 40)) };
    });
  });
  结果.读数.无名按钮 = 无名;
  记(`工具条上的无名 32×32 按钮：${JSON.stringify(无名)}`);

  for (const n of 无名) {
    await page.mouse.move(n.中心[0], n.中心[1]);
    await page.waitForTimeout(1100);
    const 气泡 = await page.evaluate(() => {
      const t = [...document.querySelectorAll('body *')].filter(e => e.children.length === 0 && /下载|导出|图片|素材/.test(e.innerText || '') && e.getBoundingClientRect().width > 0);
      return t.slice(0, 3).map(e => ({ 文本: e.innerText.trim().slice(0, 20), box: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; })() }));
    });
    记(`悬停无名按钮后的气泡：${JSON.stringify(气泡)}`);
    结果.读数['气泡_' + n.中心[0]] = 气泡;
  }
  落盘(结果);
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI4.json ===');
}
