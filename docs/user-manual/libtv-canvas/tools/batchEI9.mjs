// Batch EI-9：⭐ 查清「多选工具条」到底什么时候出现。
//   EI-8 的反常：用「点选 + Shift 加选」选中 2 个节点时，工具条上**找不到「打组」**；
//   而用**框选**选中 5 个时找得到。⇒ 要么工具条只在框选后出现，要么是我的判据/时序问题。
//   判据纪律：先看图。每一步都截图。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEI9.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

// 工具条带上的全部可见按钮（不看文字，只看几何）
const 扫工具条带 = () => page.evaluate(() => {
  const 带 = [];
  for (const b of document.querySelectorAll('button')) {
    const r = b.getBoundingClientRect();
    if (r.width === 0) continue;
    if (r.top > 70 && r.top < 140 && r.left > 250 && r.left < 1050 && !b.closest('.react-flow__node')) {
      带.push({ 文字: (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 12), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
    }
  }
  return 带;
});

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
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
  await page.waitForTimeout(1800);

  const 节点 = await page.evaluate(() => {
    const o = {};
    for (const n of document.querySelectorAll('.react-flow__node')) {
      const r = n.getBoundingClientRect();
      o[n.getAttribute('data-id')] = { 类型: (n.className.toString().match(/react-flow__node-([a-zA-Z]+)/) || [, '?'])[1], box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
    }
    return o;
  });
  结果.读数.节点 = 节点;
  记(`图片节点 box：${JSON.stringify(节点['i-9nlG6HdjK2'].box)} / ${JSON.stringify(节点['i-sODTbgLUm1'].box)}`);

  const 当前选中 = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));

  // ---- 步骤 1：单击第一个图片节点（只 1 个）
  let b1 = 节点['i-9nlG6HdjK2'].box;
  await page.mouse.click(Math.round(b1[0] + b1[2] / 2), Math.round(b1[1] + b1[3] / 2));
  await page.waitForTimeout(1600);
  记(`① 单击 1 个图片 → 选中 ${JSON.stringify(await 当前选中())}；工具条带：${JSON.stringify(await 扫工具条带())}`);
  await page.screenshot({ path: EVID + 'ei9-1-单击一个.png', clip: { x: 200, y: 40, width: 1000, height: 320 } });

  // ---- 步骤 2：Shift 加选第二个
  let b2 = 节点['i-sODTbgLUm1'].box;
  await page.keyboard.down('Shift');
  await page.mouse.click(Math.round(b2[0] + b2[2] / 2), Math.round(b2[1] + b2[3] / 2));
  await page.keyboard.up('Shift');
  await page.waitForTimeout(2000);
  const 选2 = await 当前选中();
  记(`② Shift 加选 → 选中 ${JSON.stringify(选2)}；工具条带：${JSON.stringify(await 扫工具条带())}`);
  await page.screenshot({ path: EVID + 'ei9-2-shift加选两个.png' });
  await page.screenshot({ path: EVID + 'ei9-2-裁.png', clip: { x: 200, y: 40, width: 1000, height: 320 } });

  // ---- 步骤 3：换一种加选方式 —— 在节点**边框**上 Shift 点（不点内容区）
  await page.keyboard.press('Escape');
  await page.mouse.click(1200, 700);
  await page.waitForTimeout(1000);
  b1 = 节点['i-9nlG6HdjK2'].box; b2 = 节点['i-sODTbgLUm1'].box;
  await page.mouse.click(b1[0] + 12, b1[1] + 12);           // 左上角（通常是选区把手/边框）
  await page.waitForTimeout(900);
  await page.keyboard.down('Shift');
  await page.mouse.click(b2[0] + 12, b2[1] + 12);
  await page.keyboard.up('Shift');
  await page.waitForTimeout(1800);
  记(`③ 角点 Shift 加选 → 选中 ${JSON.stringify(await 当前选中())}；工具条带：${JSON.stringify(await 扫工具条带())}`);
  await page.screenshot({ path: EVID + 'ei9-3-角点加选.png', clip: { x: 200, y: 40, width: 1000, height: 320 } });

  // ---- 步骤 4：框选（已知能出工具条，做阳性对照）
  await page.keyboard.press('Escape');
  await page.mouse.click(1200, 700);
  await page.waitForTimeout(900);
  const x1 = b1[0] - 20, y1 = b1[1] - 10, x2 = b2[0] + b2[2] + 20, y2 = b2[1] + b2[3] + 20;
  await page.mouse.move(x1, y1); await page.mouse.down();
  await page.mouse.move((x1 + x2) / 2, (y1 + y2) / 2, { steps: 10 });
  await page.mouse.move(x2, y2, { steps: 10 });
  await page.waitForTimeout(300); await page.mouse.up();
  await page.mouse.move(700, 760);
  await page.waitForTimeout(2000);
  const 选框 = await 当前选中();
  const 带 = await 扫工具条带();
  记(`④ 框选 → 选中 ${JSON.stringify(选框)}（${选框.length} 个）；工具条带：${JSON.stringify(带)}`);
  await page.screenshot({ path: EVID + 'ei9-4-框选.png', clip: { x: 200, y: 40, width: 1000, height: 320 } });
  结果.读数.工具条带 = 带;

  // ---- 步骤 5：若工具条在，开下拉读两项
  const 打组 = 带.find(t => t.文字.startsWith('打组'));
  if (打组) {
    await page.mouse.click(Math.round(打组.box[0] + 打组.box[2] / 2), Math.round(打组.box[1] + 打组.box[3] / 2));
    await page.waitForTimeout(1400);
    const 项 = await page.evaluate(() => {
      const all = [...document.querySelectorAll('body *')].filter(e => /合并分镜组/.test(e.innerText || '') && e.getBoundingClientRect().width > 0);
      if (!all.length) return { 错: '菜单没开' };
      all.sort((p, q) => p.getBoundingClientRect().width * p.getBoundingClientRect().height - q.getBoundingClientRect().width * q.getBoundingClientRect().height);
      let 宿主 = all[0]; for (let i = 0; i < 3; i++) { if (宿主.querySelectorAll('button').length >= 2) break; 宿主 = 宿主.parentElement; }
      return [...宿主.querySelectorAll('button')].map(e => { const cs = getComputedStyle(e); return { 文本: (e.innerText || '').trim().slice(0, 12), opacity: cs.opacity, cursor: cs.cursor, disabled: e.disabled === true, ariaDis: e.getAttribute('aria-disabled') }; });
    });
    记(`⑤ 框选态下的下拉：${JSON.stringify(项)}`);
    结果.读数.框选态下拉 = 项;
    await page.screenshot({ path: EVID + 'ei9-5-框选态下拉.png', clip: { x: 500, y: 50, width: 360, height: 240 } });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(800);
  } else 记('⑤ 框选后也没有「打组」⇒ 与 ④ 矛盾，必须看图');

  // ---- 步骤 6：先用 ⌘G 成组，再看组内能不能把「转分镜组」点成亮的
  //    （这是本手册早就列为 📖 的未验项；只读菜单，不点「转分镜组」）
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI9.json ===');
}
