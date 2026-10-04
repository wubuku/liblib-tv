// Batch EI-13：⛔ 先修 EI-12 留下的状态偏差，再验「框选到底是相交还是必须包住」。
//
// 事故：EI-12 用**屏幕坐标**把图片节点挪回原位，但过程中视口平移了 ⇒ 屏幕上回去了、画布坐标没回去。
//       i-9nlG6HdjK2 画布 x 从 -1764 变成 -872.837（偏 891px）。
// 修法：改用**画布坐标**驱动（Δscreen = Δcanvas × zoom），并以 style.transform 为准做验收。
//
// 顺带验一条可能写错的老结论：手册 K-01/K-02 写「必须框完整包住节点才算选中，擦着边不算」。
//       EI-12 里只压住 63/164 px 的音频节点**也被选中了** ⇒ 旧结论可疑。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEI13.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 原始 = {
  'i-9nlG6HdjK2': [-1764, 900],
  'i-sODTbgLUm1': [-168, 900],
};

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
  await page.waitForTimeout(2000);

  const 读视口 = () => page.evaluate(() => {
    const el = document.querySelector('.react-flow__viewport');
    const m = el ? /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)[^)]*scale\((-?[\d.]+)\)/.exec(el.style.transform || '') : null;
    return m ? { tx: parseFloat(m[1]), ty: parseFloat(m[2]), zoom: parseFloat(m[3]), raw: el.style.transform } : { raw: el ? el.style.transform : '(无)' };
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

  const ids = Object.keys(原始);
  let 视口 = await 读视口();
  let 节点 = await 读节点(ids);
  记(`视口：${JSON.stringify(视口)}`);
  记(`修复前画布坐标：${JSON.stringify(Object.fromEntries(ids.map(i => [i, 节点[i].canvas])))}（应为 ${JSON.stringify(原始)}）`);

  // ---- 修：按画布坐标差 × zoom 拖回去
  for (const id of ids) {
    for (let 轮 = 0; 轮 < 4; 轮++) {
      视口 = await 读视口();
      节点 = await 读节点([id])[0] ? (await 读节点([id]))[id] : null;
      if (!节点 || !节点.canvas) { 记(`${id} 读不到`); break; }
      const dcx = 原始[id][0] - 节点.canvas[0];
      const dcy = 原始[id][1] - 节点.canvas[1];
      if (Math.abs(dcx) < 1.5 && Math.abs(dcy) < 1.5) { 记(`✅ ${id} 画布坐标已复原（残差 ${dcx.toFixed(1)},${dcy.toFixed(1)}）`); break; }
      const z = 视口.zoom || 0.468869;
      const dsx = dcx * z, dsy = dcy * z;
      const b = 节点.box;
      const sx = b[0] + b[2] / 2, sy = b[1] + b[3] / 2;
      await page.mouse.move(sx, sy);
      await page.mouse.down();
      await page.mouse.move(sx + dsx / 2, sy + dsy / 2, { steps: 10 });
      await page.mouse.move(sx + dsx, sy + dsy, { steps: 10 });
      await page.waitForTimeout(400);
      await page.mouse.up();
      await page.waitForTimeout(1800);
      记(`　${id} 第 ${轮 + 1} 轮：画布差 ${dcx.toFixed(1)},${dcy.toFixed(1)} → 屏幕拖 ${dsx.toFixed(1)},${dsy.toFixed(1)}（zoom ${z.toFixed(4)}）`);
    }
  }
  // ⭐ 静置后再验一次：确认视口平移已经停稳（EI-12 就是栽在这）
  await page.waitForTimeout(2500);
  节点 = await 读节点(ids);
  const 终 = {};
  for (const id of ids) 终[id] = { 目标: 原始[id], 现: 节点[id].canvas, 残差: 节点[id].canvas ? [Math.round(节点[id].canvas[0] - 原始[id][0] * 10) / 10, Math.round((节点[id].canvas[1] - 原始[id][1]) * 10) / 10] : null };
  结果.读数.复原结果 = 终;
  记(`\n⭐ 静置后终检：${JSON.stringify(终)}`);
  await page.screenshot({ path: EVID + 'ei13-复原终检.png' });

  // ---- 顺带记一张「复原后全景」供人工比对
  const 总数 = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  记(`节点总数：${总数}（基线 11）`);
  结果.读数.节点总数 = 总数;

  // ---- 验框选规则：相交 vs 必须包住（对 i-sODTbgLUm1 单节点做 4 组）
  const 框 = async (rect) => {
    await page.mouse.move(1380, 830); await page.mouse.click(1380, 830); await page.waitForTimeout(700);
    await page.mouse.move(rect[0], rect[1]); await page.mouse.down();
    await page.mouse.move((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2, { steps: 8 });
    await page.mouse.move(rect[2], rect[3], { steps: 8 });
    await page.waitForTimeout(300); await page.mouse.up();
    await page.mouse.move(1380, 830);
    await page.waitForTimeout(1500);
    return page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
  };

  const st = (await 读节点(['i-sODTbgLUm1']))['i-sODTbgLUm1'];
  const [bx, by, bw, bh] = st.box;
  记(`\n目标节点 i-sODTbgLUm1 屏幕 box=${JSON.stringify(st.box)}，画布坐标=${JSON.stringify(st.canvas)}`);
  const 用例 = [
    { 名: '① 完全包住（阳性对照）', rect: [bx - 20, by - 20, bx + bw + 20, by + bh + 20] },
    { 名: '② 只压住顶部 8px（擦边）', rect: [bx - 20, by + 8, bx + bw + 20, by + bh + 20] },
    { 名: '③ 只压住左半边', rect: [bx, by - 20, bx + bw / 2, by + bh + 20] },
    { 名: '④ 差 6px 完全不碰（阴性对照）', rect: [bx - 20, by - 20, bx + bw - 6, by + bh - 6] },
  ];
  结果.读数.框选规则 = [];
  for (const u of 用例) {
    const 选 = await 框(u.rect);
    const 含 = 选.includes('i-sODTbgLUm1');
    记(`${u.名}：选中 ${JSON.stringify(选)} ⇒ 目标${含 ? '**被选中**' : '未被选中'}`);
    结果.读数.框选规则.push({ 用例: u.名, rect: u.rect, 选中: 选, 目标被选中: 含 });
  }
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI13.json ===');
}
