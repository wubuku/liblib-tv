// Batch EI-20：⛔ 修复两张图片节点的位置（EI-19 结束时它们不在标准坐标上）。
//   i-9nlG6HdjK2  目标 (-1764, 900)
//   i-sODTbgLUm1  目标 (-168, 900)
//
// ⭐ 上一轮栽在「拖拽抓错节点」：低缩放下节点挨得近，鼠标落点会命中隔壁节点。
//   本轮每次拖拽前后都对比**全部节点的坐标**，一旦发现动的不是目标，立刻把误动的那个拖回去。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEI20.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 标准 = {
  'a-GgqvrVz0pw': [719.388, 1509.13], 'a-THmbuJXQj4': [-1356, 600], 'b-mfkcQNULC3': [636, 300],
  'i-9nlG6HdjK2': [-1764, 900], 'i-sODTbgLUm1': [-168, 900], 'n-56F19pXVB4': [-1225.03, 370.975],
  't-2AK3Ukyxj3': [-1476, 1524], 't-UtVx3lZmrV': [600, 900], 'v-eMpqKtiLlx': [-1787, 900],
  'v-oZNpH99MtM': [132, 300], 'v-v2hlWY4Br3': [-696, 300],
};

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
  await page.waitForTimeout(3500);

  const 读视口 = () => page.evaluate(() => {
    const el = document.querySelector('.react-flow__viewport');
    const m = el ? /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)[^)]*scale\((-?[\d.]+)\)/.exec(el.style.transform || '') : null;
    return m ? { zoom: parseFloat(m[3]), raw: el.style.transform } : { raw: '(无)' };
  });
  const 读全部 = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map(n => {
    const r = n.getBoundingClientRect();
    const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    return { id: n.getAttribute('data-id'), canvas: m ? [parseFloat(m[1]), parseFloat(m[2])] : null, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }));
  const 表 = (all) => Object.fromEntries(all.map(n => [n.id, n.canvas]));

  const 开 = await 读全部();
  const 视口 = await 读视口();
  记(`开局 ${开.length} 个节点，视口 ${视口.raw}`);
  记(`坐标：${JSON.stringify(表(开))}`);
  const 不符 = 开.filter(n => 标准[n.id] && (!n.canvas || Math.abs(n.canvas[0] - 标准[n.id][0]) > 1.5 || Math.abs(n.canvas[1] - 标准[n.id][1]) > 1.5));
  记(`不符标准的：${JSON.stringify(不符.map(n => [n.id, n.canvas, 标准[n.id]]))}`);
  结果.读数.开局 = 开;

  // ---- 带身份核对的单次拖拽
  const 拖一次 = async (id, 目标) => {
    const 前 = 表(await 读全部());
    const st = (await 读全部()).find(n => n.id === id);
    const v = await 读视口();
    if (!st || !st.canvas) return { 结果: '读不到' };
    const dcx = 目标[0] - st.canvas[0], dcy = 目标[1] - st.canvas[1];
    if (Math.abs(dcx) < 1.2 && Math.abs(dcy) < 1.2) return { 结果: '已到位' };
    const z = v.zoom || 0.46;
    // 落点：节点**标题条**那一行（左上角往右 40px、往下 6px），那里没有播放/预览控件
    const sx = Math.round(st.box[0] + 45), sy = Math.round(st.box[1] + 6);
    await page.mouse.move(sx, sy);
    await page.mouse.down();
    await page.mouse.move(sx + dcx * z / 3, sy + dcy * z / 3, { steps: 12 });
    await page.mouse.move(sx + dcx * z * 2 / 3, sy + dcy * z * 2 / 3, { steps: 12 });
    await page.mouse.move(sx + dcx * z, sy + dcy * z, { steps: 12 });
    await page.waitForTimeout(450);
    await page.mouse.up();
    await page.waitForTimeout(2200);
    const 后 = 表(await 读全部());
    const 动的 = Object.keys(后).filter(k => 前[k] && 后[k] && (Math.abs(后[k][0] - 前[k][0]) > 0.5 || Math.abs(后[k][1] - 前[k][1]) > 0.5));
    记(`　拖 ${id} 画布差 ${dcx.toFixed(0)},${dcy.toFixed(0)}（zoom ${z.toFixed(3)}，落点 ${sx},${sy}）⇒ 实际动的是 ${JSON.stringify(动的)}`);
    if (动的.length === 1 && 动的[0] === id) return { 结果: '成功' };
    if (动的.length === 0) return { 结果: '没动' };
    // ⭐ 动错了：把误动的节点按同样的画布增量拖回去
    const 误 = 动的[0];
    const 误目标 = [前[误][0], 前[误][1]];
    const ms = (await 读全部()).find(n => n.id === 误);
    const mv = await 读视口();
    if (ms && ms.canvas) {
      const bx = 误目标[0] - ms.canvas[0], by = 误目标[1] - ms.canvas[1];
      const mz = mv.zoom || 0.46;
      const mx = Math.round(ms.box[0] + 45), my = Math.round(ms.box[1] + 6);
      await page.mouse.move(mx, my);
      await page.mouse.down();
      await page.mouse.move(mx + bx * mz / 2, my + by * mz / 2, { steps: 12 });
      await page.mouse.move(mx + bx * mz, my + by * mz, { steps: 12 });
      await page.waitForTimeout(450);
      await page.mouse.up();
      await page.waitForTimeout(2200);
      const 撤 = 表(await 读全部());
      记(`　⤺ 已把误动的 ${误} 拖回 ${JSON.stringify(误目标)}，现 ${JSON.stringify(撤[误])}`);
    }
    return { 结果: '拖错已回滚' };
  };

  for (let 外 = 0; 外 < 6; 外++) {
    const all = await 读全部();
    const 坏 = all.filter(n => 标准[n.id] && (!n.canvas || Math.abs(n.canvas[0] - 标准[n.id][0]) > 1.5 || Math.abs(n.canvas[1] - 标准[n.id][1]) > 1.5));
    if (!坏.length) { 记('✅ 全部到位'); break; }
    记(`\n第 ${外 + 1} 轮，待修：${JSON.stringify(坏.map(n => [n.id, n.canvas]))}`);
    const r = await 拖一次(坏[0].id, 标准[坏[0].id]);
    记(`　结果：${r.结果}`);
    if (r.结果 === '拖错已回滚' || r.结果 === '没动') {
      // 换个落点重试：改用节点正中心
      const st = (await 读全部()).find(n => n.id === 坏[0].id);
      const v = await 读视口();
      if (st && st.canvas) {
        const dcx = 标准[坏[0].id][0] - st.canvas[0], dcy = 标准[坏[0].id][1] - st.canvas[1];
        const z = v.zoom || 0.46;
        const sx = Math.round(st.box[0] + st.box[2] / 2), sy = Math.round(st.box[1] + st.box[3] / 2);
        await page.mouse.move(sx, sy); await page.mouse.down();
        await page.mouse.move(sx + dcx * z / 2, sy + dcy * z / 2, { steps: 12 });
        await page.mouse.move(sx + dcx * z, sy + dcy * z, { steps: 12 });
        await page.waitForTimeout(450); await page.mouse.up();
        await page.waitForTimeout(2200);
        const 后 = 表(await 读全部());
        记(`　（中心落点重试）${JSON.stringify(后[坏[0].id])}`);
      }
    }
  }

  记('\n静置 15s 等落盘…');
  await page.waitForTimeout(15000);
  const 终 = await 读全部();
  const 终差 = 终.filter(n => 标准[n.id] && (!n.canvas || Math.abs(n.canvas[0] - 标准[n.id][0]) > 1.5 || Math.abs(n.canvas[1] - 标准[n.id][1]) > 1.5));
  记(`⭐ 终检：${终.length} 个节点，仍不符的 ${JSON.stringify(终差.map(n => [n.id, n.canvas, 标准[n.id]]))}`);
  记(`坐标全表：${JSON.stringify(表(终))}`);
  结果.读数.终检 = 终;
  结果.读数.终检差异 = 终差;
  await page.screenshot({ path: EVID + 'ei20-终检.png' });
  await page.waitForTimeout(5000);
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI20.json ===');
}
