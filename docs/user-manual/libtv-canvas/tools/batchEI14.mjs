// Batch EI-14：① 修 EI-13 的 bug（`(await 读节点([id]))[0]` 取错导致「读不到」，两个图片节点其实一直没修）
//          ② 重测框选规则：EI-13 四组读数**自相矛盾**（完全包住未选中 / 擦边却选中），
//             拿不出结论。本轮每组框选前后都打几何快照 + 截图，确认画布没漂。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEI14.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 原始 = { 'i-9nlG6HdjK2': [-1764, 900], 'i-sODTbgLUm1': [-168, 900] };

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
  await page.waitForTimeout(2500);

  const 读视口 = () => page.evaluate(() => {
    const el = document.querySelector('.react-flow__viewport');
    const m = el ? /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)[^)]*scale\((-?[\d.]+)\)/.exec(el.style.transform || '') : null;
    return m ? { zoom: parseFloat(m[3]), raw: el.style.transform } : { raw: el ? el.style.transform : '(无)' };
  });
  const 读节点 = (ids) => page.evaluate((list) => {
    const o = {};
    for (const id of list) {
      const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!el) { o[id] = null; continue; }
      const r = el.getBoundingClientRect();
      const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(el.style.transform || '');
      o[id] = { canvas: m ? [parseFloat(m[1]), parseFloat(m[2])] : null, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
    }
    return o;
  }, ids);
  const 全部节点 = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map(n => {
    const r = n.getBoundingClientRect();
    const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    return { id: n.getAttribute('data-id'), 类型: (n.className.toString().match(/react-flow__node-([a-zA-Z]+)/) || [, '?'])[1], canvas: m ? [parseFloat(m[1]), parseFloat(m[2])] : null, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }));

  const ids = Object.keys(原始);
  const 视口0 = await 读视口();
  const 节前 = await 读节点(ids);
  记(`视口 ${视口0.raw}（zoom ${视口0.zoom}）`);
  const 前坐标 = Object.fromEntries(ids.map(i => [i, 节前[i].canvas]));
  记(`修复前：${JSON.stringify(前坐标)}  目标 ${JSON.stringify(原始)}`);

  // ---- 修复（这次取快照的写法是对的）
  for (const id of ids) {
    for (let 轮 = 0; 轮 < 5; 轮++) {
      const 视口 = await 读视口();
      const 快照 = await 读节点([id]);
      const st = 快照[id];
      if (!st || !st.canvas) { 记(`❌ ${id} 读不到`); break; }
      const dcx = 原始[id][0] - st.canvas[0], dcy = 原始[id][1] - st.canvas[1];
      if (Math.abs(dcx) < 1.5 && Math.abs(dcy) < 1.5) { 记(`✅ ${id} 画布坐标已复原，残差 ${dcx.toFixed(2)},${dcy.toFixed(2)}`); break; }
      const z = 视口.zoom || 0.468869;
      const dsx = dcx * z, dsy = dcy * z;
      const b = st.box;
      const sx = b[0] + b[2] / 2, sy = b[1] + b[3] / 2;
      await page.mouse.move(sx, sy);
      await page.mouse.down();
      await page.mouse.move(sx + dsx / 2, sy + dsy / 2, { steps: 10 });
      await page.mouse.move(sx + dsx, sy + dsy, { steps: 10 });
      await page.waitForTimeout(450);
      await page.mouse.up();
      await page.waitForTimeout(2000);
      记(`　${id} 第 ${轮 + 1} 轮：画布差 ${dcx.toFixed(1)},${dcy.toFixed(1)} → 屏幕拖 ${dsx.toFixed(1)},${dsy.toFixed(1)}`);
    }
  }
  await page.waitForTimeout(3000);
  const 节后 = await 读节点(ids);
  const 视口1 = await 读视口();
  const 核对 = {};
  for (const id of ids) 核对[id] = { 目标: 原始[id], 现: 节后[id].canvas, 残差: 节后[id].canvas ? [+(节后[id].canvas[0] - 原始[id][0]).toFixed(2), +(节后[id].canvas[1] - 原始[id][1]).toFixed(2)] : null };
  结果.读数.复原 = { 视口前: 视口0.raw, 视口后: 视口1.raw, 核对 };
  记(`\n⭐ 复原终检（静置 3s 后）：${JSON.stringify(核对)}`);
  记(`视口变化：${视口0.raw}  →  ${视口1.raw}`);
  await page.screenshot({ path: EVID + 'ei14-复原终检.png' });
  结果.读数.全部节点 = await 全部节点();

  // ---- 框选规则重测（带前后几何快照）
  const 框 = async (rect, 标签) => {
    await page.mouse.click(1390, 840);
    await page.waitForTimeout(800);
    const 前 = await 全部节点();
    const 视口前 = await 读视口();
    await page.mouse.move(rect[0], rect[1]);
    await page.mouse.down();
    await page.mouse.move((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2, { steps: 8 });
    await page.mouse.move(rect[2], rect[3], { steps: 8 });
    await page.waitForTimeout(350);
    await page.mouse.up();
    await page.waitForTimeout(1600);
    const 选 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
    const 后 = await 全部节点();
    const 视口后 = await 读视口();
    const 漂 = 前.filter(p => { const q = 后.find(x => x.id === p.id); return !q || Math.abs(q.box[0] - p.box[0]) > 2 || Math.abs(q.box[1] - p.box[1]) > 2; }).map(p => p.id);
    记(`${标签}：选中 ${JSON.stringify(选)}；视口 ${视口前.raw === 视口后.raw ? '未变' : '⚠️变了 ' + 视口后.raw}；节点漂移 ${JSON.stringify(漂)}`);
    return { 标签, rect, 选中: 选, 视口后: 视口后.raw, 漂移: 漂, 前几何: 前.filter(p => ['i-9nlG6HdjK2', 'i-sODTbgLUm1', 'a-GgqvrVz0pw', 'v-eMpqKtiLlx'].includes(p.id)) };
  };

  const st = (await 读节点(['i-sODTbgLUm1']))['i-sODTbgLUm1'];
  const [bx, by, bw, bh] = st.box;
  记(`\n目标 i-sODTbgLUm1 屏幕 box=${JSON.stringify(st.box)}，画布=${JSON.stringify(st.canvas)}`);
  结果.读数.框选规则 = [];
  const 用例 = [
    { 名: '① 完全包住（阳性对照）', rect: [bx - 24, by - 24, bx + bw + 24, by + bh + 24] },
    { 名: '② 只压住顶部 8px', rect: [bx - 24, by + 8, bx + bw + 24, by + bh + 24] },
    { 名: '③ 只压住左半边', rect: [bx, by - 24, bx + bw / 2, by + bh + 24] },
    { 名: '④ 差 6px 完全不碰（阴性对照）', rect: [bx - 24, by - 24, bx + bw - 6, by + bh - 6] },
    { 名: '⑤ 只压住右下角 6px×6px', rect: [bx + bw - 6, by + bh - 6, bx + bw + 24, by + bh + 24] },
  ];
  for (const u of 用例) {
    const r = await 框(u.rect, u.名);
    r.目标被选中 = r.选中.includes('i-sODTbgLUm1');
    r.目标几何 = r.前几何.find(p => p.id === 'i-sODTbgLUm1');
    delete r.前几何;
    记(`　⇒ 目标${r.目标被选中 ? '**被选中**' : '未被选中'}`);
    结果.读数.框选规则.push(r);
    await page.screenshot({ path: EVID + `ei14-${u.名.slice(0, 2)}.png` });
  }
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI14.json ===');
}
