// Batch EI-21：⛔ 收尾修复。
//   i-sODTbgLUm1 在 (2152, 1312.1)，要回 (-168, 900) —— 位移大，单次拖得动。
//   i-9nlG6HdjK2 只差 12 画布 px，当前 27% 缩放下只有 3.3 屏幕 px，低于拖拽阈值 ⇒ 多试几种落点/步长。
// 每次拖拽都做身份核对，拖错立刻回滚。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEI21.json';
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
  const 表 = (a) => Object.fromEntries(a.map(n => [n.id, n.canvas]));

  const 拖 = async (id, 目标, 落点式) => {
    const 前 = 表(await 读全部());
    const all = await 读全部();
    const st = all.find(n => n.id === id);
    const v = await 读视口();
    if (!st || !st.canvas) return '读不到';
    const dcx = 目标[0] - st.canvas[0], dcy = 目标[1] - st.canvas[1];
    if (Math.abs(dcx) < 0.8 && Math.abs(dcy) < 0.8) return '已到位';
    const z = v.zoom || 0.273;
    const sx = 落点式 === '中' ? Math.round(st.box[0] + st.box[2] / 2) : Math.round(st.box[0] + 45);
    const sy = 落点式 === '中' ? Math.round(st.box[1] + st.box[3] / 2) : Math.round(st.box[1] + 6);
    await page.mouse.move(sx, sy);
    await page.mouse.down();
    await page.mouse.move(sx + dcx * z / 4, sy + dcy * z / 4, { steps: 14 });
    await page.mouse.move(sx + dcx * z / 2, sy + dcy * z / 2, { steps: 14 });
    await page.mouse.move(sx + dcx * z * 3 / 4, sy + dcy * z * 3 / 4, { steps: 14 });
    await page.mouse.move(sx + dcx * z, sy + dcy * z, { steps: 14 });
    await page.waitForTimeout(500);
    await page.mouse.up();
    await page.waitForTimeout(2300);
    const 后 = 表(await 读全部());
    const 动的 = Object.keys(后).filter(k => 前[k] && 后[k] && (Math.abs(后[k][0] - 前[k][0]) > 0.5 || Math.abs(后[k][1] - 前[k][1]) > 0.5));
    记(`　拖 ${id} 差 ${dcx.toFixed(0)},${dcy.toFixed(0)}（z=${z.toFixed(3)} 落点${落点式} ${sx},${sy}）⇒ 动的是 ${JSON.stringify(动的)}，现 ${JSON.stringify(后[id])}`);
    if (动的.length === 1 && 动的[0] === id) return '成功';
    if (!动的.length) return '没动';
    // 回滚误动的
    const 误 = 动的[0], 误原 = 前[误];
    const ms = (await 读全部()).find(n => n.id === 误);
    const mv = await 读视口();
    if (ms && ms.canvas) {
      const bx = 误原[0] - ms.canvas[0], by = 误原[1] - ms.canvas[1];
      const mz = mv.zoom || 0.273;
      const mx = Math.round(ms.box[0] + 45), my = Math.round(ms.box[1] + 6);
      await page.mouse.move(mx, my); await page.mouse.down();
      await page.mouse.move(mx + bx * mz / 2, my + by * mz / 2, { steps: 14 });
      await page.mouse.move(mx + bx * mz, my + by * mz, { steps: 14 });
      await page.waitForTimeout(500); await page.mouse.up();
      await page.waitForTimeout(2300);
      记(`　⤺ 回滚 ${误} → ${JSON.stringify((await 读全部()).find(n => n.id === 误).canvas)}`);
    }
    return '拖错已回滚';
  };

  // ---- ① 大位移：i-sODTbgLUm1
  for (let i = 0; i < 4; i++) {
    const st = (await 读全部()).find(n => n.id === 'i-sODTbgLUm1');
    if (!st) { 记('i-sODTbgLUm1 不在 DOM 里'); break; }
    const d = Math.abs(st.canvas[0] - 标准['i-sODTbgLUm1'][0]);
    if (d < 1) { 记('✅ i-sODTbgLUm1 已到位'); break; }
    记(`i-sODTbgLUm1 第 ${i + 1} 次（现 ${JSON.stringify(st.canvas)}，还差 ${d.toFixed(0)}）`);
    await 拖('i-sODTbgLUm1', 标准['i-sODTbgLUm1'], '标');
  }

  // ---- ② 小残差：i-9nlG6HdjK2 差 12px。依次试不同落点；都不行就换更大的中间步长绕一下。
  for (let i = 0; i < 6; i++) {
    const st = (await 读全部()).find(n => n.id === 'i-9nlG6HdjK2');
    if (!st) break;
    const dx = st.canvas[0] - 标准['i-9nlG6HdjK2'][0], dy = st.canvas[1] - 标准['i-9nlG6HdjK2'][1];
    if (Math.abs(dx) < 1 && Math.abs(dy) < 1) { 记('✅ i-9nlG6HdjK2 已到位'); break; }
    记(`i-9nlG6HdjK2 第 ${i + 1} 次（现 ${JSON.stringify(st.canvas)}，差 ${dx.toFixed(0)},${dy.toFixed(0)}）`);
    const r = await 拖('i-9nlG6HdjK2', 标准['i-9nlG6HdjK2'], i % 2 ? '中' : '标');
    if (r === '没动') {
      // 绕一步：先往反方向走 40 画布 px（够大能触发），再走回来
      记('　（没动）先做一次 40px 的大位移把阈值突破');
      await 拖('i-9nlG6HdjK2', [标准['i-9nlG6HdjK2'][0] - 40, 标准['i-9nlG6HdjK2'][1]], i % 2 ? '标' : '中');
      await 拖('i-9nlG6HdjK2', 标准['i-9nlG6HdjK2'], i % 2 ? '中' : '标');
    }
  }

  记('\n静置 15s…');
  await page.waitForTimeout(15000);
  const 终 = await 读全部();
  const 差 = 终.filter(n => 标准[n.id] && (!n.canvas || Math.abs(n.canvas[0] - 标准[n.id][0]) > 1.5 || Math.abs(n.canvas[1] - 标准[n.id][1]) > 1.5));
  记(`⭐ 终检：${终.length} 个节点，仍不符 ${JSON.stringify(差.map(n => [n.id, n.canvas, 标准[n.id]]))}`);
  记(`全表：${JSON.stringify(表(终))}`);
  结果.读数.终检 = 终;
  await page.screenshot({ path: EVID + 'ei21-终检.png' });
  await page.waitForTimeout(5000);
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI21.json ===');
}
