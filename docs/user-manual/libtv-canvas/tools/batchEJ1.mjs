// Batch EJ-1：① 多选工具条最左那枚**无名**图标按钮的菜单（源码说它是 onLayoutChange / 排列）—— 只读，不点任何一项
//          ② ⭐ 全画布「无名图标按钮」普查：把所有**没有可访问名**（无文字、无 aria-label、无 title）的
//             图标按钮列出来，并用悬停差分给每个找气泡。
//             （零命中的话先怀疑判据，所以判据写成「无 innerText 且无 aria-label 且无 title 且有 svg」）
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEJ1.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 7000 });
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === '知道了'); if (b) b.click(); });
  await page.waitForTimeout(800);
  await page.evaluate(() => {
    const 条 = [...document.querySelectorAll('div')].filter(d => /开启浏览器通知/.test(d.innerText || ''));
    if (条.length) { 条.sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width); const btn = [...条[条.length - 1].querySelectorAll('button')].find(b => (b.innerText || '').trim() === ''); if (btn) btn.click(); }
  });
  await page.waitForTimeout(700);
  await page.evaluate(() => { for (const b of document.querySelectorAll('button')) if (b.getAttribute('aria-label') === '关闭' && b.getBoundingClientRect().width < 40) { b.click(); return; } });
  await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);

  记(`开局坐标偏差：${JSON.stringify(await 核对坐标(page))}`);

  // ---- 找一个「低」的框选区域，保证工具条不会跑到视口外（EI-11 就在 y=-50 上栽过）
  const 节点 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map(n => {
    const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), 类型: (n.className.toString().match(/react-flow__node-([a-zA-Z]+)/) || [, '?'])[1], box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }));
  记(`节点：${JSON.stringify(节点.map(n => [n.类型, n.box]))}`);

  // 选两个同一行的图片节点（它们之间的视频节点会被一起圈进来，无所谓，这一步只读菜单）
  const 图 = 节点.filter(n => n.类型 === 'image');
  const 目标 = [图[0], 图[1]].filter(Boolean);
  const x1 = Math.min(...目标.map(p => p.box[0])) - 20, y1 = Math.min(...目标.map(p => p.box[1])) - 12;
  const x2 = Math.max(...目标.map(p => p.box[0] + p.box[2])) + 20, y2 = Math.max(...目标.map(p => p.box[1] + p.box[3])) + 12;
  await page.mouse.click(1400, 848); await page.waitForTimeout(700);
  await page.mouse.move(x1, y1); await page.mouse.down();
  await page.mouse.move((x1 + x2) / 2, (y1 + y2) / 2, { steps: 10 });
  await page.mouse.move(x2, y2, { steps: 10 });
  await page.waitForTimeout(350); await page.mouse.up();
  await page.mouse.move(1400, 848);
  await page.waitForTimeout(1800);
  const 选中 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
  记(`框选后：${JSON.stringify(选中)}`);

  const 找工具条 = () => page.evaluate(() => {
    const all = [...document.querySelectorAll('div')].filter(e => /保存到资产/.test(e.innerText || '') && e.getBoundingClientRect().width > 300 && e.getBoundingClientRect().height > 0);
    if (!all.length) return { 找到: false };
    all.sort((p, q) => p.getBoundingClientRect().width - q.getBoundingClientRect().width);
    const c = all[0]; const r = c.getBoundingClientRect();
    return {
      找到: true, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      按钮: [...c.querySelectorAll('button')].map(b => {
        const rb = b.getBoundingClientRect();
        return { 文字: (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 12), aria: b.getAttribute('aria-label') || '', title: b.getAttribute('title') || '', box: [Math.round(rb.left), Math.round(rb.top), Math.round(rb.width), Math.round(rb.height)] };
      }),
    };
  });
  const 条 = await 找工具条();
  记(`工具条：${条.找到 ? JSON.stringify(条.box) : '没出现'}`);
  结果.读数.工具条 = 条;

  // ---- ① 点开最左那枚「无名」按钮，只读菜单
  if (条.找到) {
    const 最左 = 条.按钮[0];
    记(`最左按钮：${JSON.stringify(最左)}`);
    await page.mouse.click(Math.round(最左.box[0] + 最左.box[2] / 2), Math.round(最左.box[1] + 最左.box[3] / 2));
    await page.waitForTimeout(1600);
    // ⭐ §283 法：枚举工具条下方 320px 内所有可见浮层里的可点项
    const 菜单 = await page.evaluate((t) => {
      const 出 = [];
      for (const b of document.querySelectorAll('button')) {
        const r = b.getBoundingClientRect();
        if (r.width === 0) continue;
        if (r.top < t[1] + t[3] || r.top > t[1] + t[3] + 320) continue;
        if (r.left < t[0] - 60 || r.left > t[0] + t[2] + 60) continue;
        const cs = getComputedStyle(b);
        出.push({ 文本: (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 16), aria: b.getAttribute('aria-label') || '', box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], opacity: cs.opacity, cursor: cs.cursor });
      }
      return 出;
    }, 条.box);
    记(`⭐「排列」按钮下方的可点项：${JSON.stringify(菜单)}`);
    结果.读数.排列菜单 = 菜单;
    await page.screenshot({ path: EVID + 'ej1-排列菜单-全图.png' });
    if (菜单.length) {
      const m = 菜单[0].box;
      await page.screenshot({ path: EVID + 'ej1-排列菜单-裁图.png', clip: { x: Math.max(0, m[0] - 230), y: Math.max(0, m[1] - 90), width: 470, height: Math.min(330, 菜单.length * 40 + 130) } });
      记('✅ 已拍排列菜单裁图');
    }
    await page.keyboard.press('Escape');
    await page.waitForTimeout(900);
  }

  // ---- ② 全画布「无名图标按钮」普查
  const 无名 = await page.evaluate(() => {
    const 出 = [];
    for (const b of document.querySelectorAll('button')) {
      const r = b.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      const 文字 = (b.innerText || '').trim();
      const aria = b.getAttribute('aria-label') || '';
      const title = b.getAttribute('title') || '';
      if (文字 || aria || title) continue;          // 有可访问名的先排除
      const 在节点里 = !!b.closest('.react-flow__node');
      出.push({
        在节点里,
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        svg数: b.querySelectorAll('svg').length,
        中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
      });
    }
    return 出;
  });
  记(`\n⭐ 全画布无可访问名的图标按钮：${无名.length} 个`);
  for (const b of 无名) 记(`　${b.在节点里 ? '节点内' : '画布层'} box=${JSON.stringify(b.box)} svg=${b.svg数}`);
  结果.读数.无名按钮 = 无名;

  // 逐个悬停找气泡（差分法：先移开 → 记快照 → 悬停 → 再记）
  const 快照 = (X, Y) => page.evaluate(([x0, y0]) => [...document.querySelectorAll('body *')]
    .filter(e => e.children.length === 0)
    .map(e => { const r = e.getBoundingClientRect(); const t = (e.innerText || e.textContent || '').trim(); return { 文本: t.slice(0, 24), cls: (e.className || '').toString().slice(0, 46), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }; })
    .filter(x => x.文本 && x.文本.length < 16 && x.box[2] > 0 && x.box[2] < 320 && x.box[3] < 90
      && Math.abs(x.box[0] - x0) < 240 && Math.abs(x.box[1] - y0) < 140), [X, Y]);

  结果.读数.悬停结果 = [];
  for (const b of 无名) {
    await page.mouse.move(700, 800);
    await page.waitForTimeout(900);
    const 前 = await 快照(b.中心[0], b.中心[1]);
    await page.mouse.move(b.中心[0], b.中心[1]);
    await page.waitForTimeout(1500);
    const 后 = await 快照(b.中心[0], b.中心[1]);
    const 新 = 后.filter(y => !前.some(x => x.文本 === y.文本));
    记(`　悬停 [${b.box}]：新出现 ${JSON.stringify(新.map(n => [n.文本, n.box]))}`);
    结果.读数.悬停结果.push({ box: b.box, 在节点里: b.在节点里, 气泡: 新 });
    if (新.length) {
      const bb = 新[0].box;
      await page.screenshot({ path: EVID + `ej1-悬停${b.box[0]}-${b.box[1]}.png`, clip: { x: Math.max(0, bb[0] - 220), y: Math.max(0, bb[1] - 70), width: 480, height: 170 } });
    }
    await page.mouse.move(700, 800);
    await page.waitForTimeout(400);
  }
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  记(`⭐ 收尾坐标偏差：${JSON.stringify(await 核对坐标(page))}`);
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEJ1.json ===');
}
