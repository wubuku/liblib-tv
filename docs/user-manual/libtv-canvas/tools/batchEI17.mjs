// Batch EI-17：⭐ 最后一次尝试拿「合并分镜组」的阳性对照，**全程不移动任何节点**。
//   路线：框选 → 用修饰键点掉非图片节点 → 只剩 2 张图 → 读「打组」下拉。
//   上一轮 ⌘-点失败且工具条消失；这轮逐个试 Shift / ⌘ / Alt，点**节点边框内侧 3px**（避开标题、播放键）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEI17.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

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
  await page.waitForTimeout(3000);

  const 读全部 = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map(n => {
    const r = n.getBoundingClientRect();
    const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    return { id: n.getAttribute('data-id'), 类型: (n.className.toString().match(/react-flow__node-([a-zA-Z]+)/) || [, '?'])[1], canvas: m ? [parseFloat(m[1]), parseFloat(m[2])] : null, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }));
  const 选区 = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
  const 找工具条 = () => page.evaluate(() => {
    const all = [...document.querySelectorAll('div')].filter(e => /保存到资产/.test(e.innerText || '') && e.getBoundingClientRect().width > 300 && e.getBoundingClientRect().height > 0);
    if (!all.length) return { 找到: false };
    all.sort((p, q) => p.getBoundingClientRect().width - q.getBoundingClientRect().width);
    const c = all[0];
    return { 找到: true, 按钮: [...c.querySelectorAll('button')].map(b => { const rb = b.getBoundingClientRect(); return { 文字: (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 12) || (b.getAttribute('aria-label') || '(无名)'), box: [Math.round(rb.left), Math.round(rb.top), Math.round(rb.width), Math.round(rb.height)] }; }) };
  });

  const 节点 = await 读全部();
  const N = Object.fromEntries(节点.map(n => [n.id, n]));
  记(`节点布局：${JSON.stringify(节点.map(n => [n.类型, n.box]))}`);

  // 框选 3 个：i1、video、i2（会顺带压到音频/导演台，先看实际选到几个）
  const b1 = N['i-9nlG6HdjK2'].box, bv = N['v-eMpqKtiLlx'].box, b2 = N['i-sODTbgLUm1'].box;
  const rx1 = Math.min(b1[0], bv[0], b2[0]) - 18, ry1 = Math.min(b1[1], bv[1], b2[1]) - 14;
  const rx2 = Math.max(b1[0] + b1[2], bv[0] + bv[2], b2[0] + b2[2]) + 18, ry2 = Math.max(b1[1] + b1[3], bv[1] + bv[3], b2[1] + b2[3]) + 14;
  记(`框选矩形 ${JSON.stringify([rx1, ry1, rx2, ry2])}`);
  await page.mouse.click(1400, 848); await page.waitForTimeout(700);
  await page.mouse.move(rx1, ry1); await page.mouse.down();
  await page.mouse.move((rx1 + rx2) / 2, (ry1 + ry2) / 2, { steps: 10 });
  await page.mouse.move(rx2, ry2, { steps: 10 });
  await page.waitForTimeout(350); await page.mouse.up();
  await page.mouse.move(1400, 848);
  await page.waitForTimeout(1800);
  const 初选 = await 选区();
  记(`框选后：${JSON.stringify(初选)}（${初选.length} 个）`);
  结果.读数.初选 = 初选;

  // 逐个修饰键试着把非图片节点移出选区
  const 要清 = 初选.filter(id => !/^i-/.test(id));
  结果.读数.尝试 = [];
  for (const key of ['Shift', 'Meta', 'Alt']) {
    let 成功 = 0;
    for (const id of 要清) {
      const b = (await 读全部()).find(n => n.id === id);
      if (!b) continue;
      const px = b.box[0] + 3, py = b.box[1] + b.box[3] / 2;      // 左边框内侧 3px
      await page.keyboard.down(key);
      await page.mouse.click(px, py);
      await page.keyboard.up(key);
      await page.waitForTimeout(650);
      const s = await 选区();
      if (!s.includes(id)) { 成功++; 记(`　${key}+点 ${id} ⇒ 已移出选区，剩 ${JSON.stringify(s)}`); }
    }
    const s = await 选区();
    记(`${key} 键共移出 ${成功}/${要清.length} 个；现在选区 ${JSON.stringify(s)}，工具条 ${(await 找工具条()).找到 ? '在' : '无'}`);
    结果.读数.尝试.push({ 键: key, 移出: 成功, 选区: s, 工具条: (await 找工具条()).找到 });
    if (s.length === 2 && s.every(id => /^i-/.test(id))) break;
    // 复原选区再试下一种键
    await page.keyboard.press('Escape');
    await page.waitForTimeout(600);
    await page.mouse.move(rx1, ry1); await page.mouse.down();
    await page.mouse.move((rx1 + rx2) / 2, (ry1 + ry2) / 2, { steps: 10 });
    await page.mouse.move(rx2, ry2, { steps: 10 });
    await page.waitForTimeout(300); await page.mouse.up();
    await page.mouse.move(1400, 848);
    await page.waitForTimeout(1500);
  }

  const 终选 = await 选区();
  const 条 = await 找工具条();
  记(`\n终态：选区 ${JSON.stringify(终选)}，工具条 ${条.找到 ? '在' : '无'}`);
  await page.screenshot({ path: EVID + 'ei17-终态.png' });

  if (条.找到) {
    const 打 = 条.按钮.find(b => b.文字.startsWith('打组'));
    await page.mouse.click(Math.round(打.box[0] + 打.box[2] / 2), Math.round(打.box[1] + 打.box[3] / 2));
    await page.waitForTimeout(1500);
    const 项 = await page.evaluate(() => {
      const all = [...document.querySelectorAll('body *')].filter(e => /合并分镜组/.test(e.innerText || '') && e.getBoundingClientRect().width > 0);
      if (!all.length) return { 错: '菜单没开' };
      all.sort((p, q) => p.getBoundingClientRect().width * p.getBoundingClientRect().height - q.getBoundingClientRect().width * q.getBoundingClientRect().height);
      let h = all[0]; for (let i = 0; i < 3; i++) { if (h.querySelectorAll('button').length >= 2) break; h = h.parentElement; }
      return { 项: [...h.querySelectorAll('button')].map(e => { const cs = getComputedStyle(e); return { 文本: (e.innerText || '').trim().slice(0, 12), opacity: cs.opacity, cursor: cs.cursor }; }) };
    });
    记(`⭐【真值表】选区 ${JSON.stringify(终选)} ⇒ ${JSON.stringify(项)}`);
    结果.读数.真值表 = 项;
    await page.screenshot({ path: EVID + 'ei17-下拉-全图.png' });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(800);
  }

  const 收 = await 读全部();
  结果.读数.收尾 = 收.map(n => [n.id, n.canvas]);
  记(`收尾坐标：${JSON.stringify(收.map(n => [n.id, n.canvas]))}`);
  await page.waitForTimeout(6000);
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI17.json ===');
}
