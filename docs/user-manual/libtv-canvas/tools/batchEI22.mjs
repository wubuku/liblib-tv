// Batch EI-22：⛔ 最后的收尾修复。
//   现状：i-sODTbgLUm1 ✓ (-168,900)；i-9nlG6HdjK2 差 12px；v-eMpqKtiLlx 被回滚累积搞到 (-1860,900) 差 73px。
//
// ⭐ 本轮的新办法：**按下去之前先用 document.elementFromPoint 确认那个像素属于哪个节点**。
//   之前老是拖错节点，就是因为低缩放下两个节点在屏幕上叠着，落点看着在 A 身上其实命中 B。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEI22.json';
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
  // ⭐ 这个像素属于哪个节点？往上找最近的 .react-flow__node
  const 归属 = (x, y) => page.evaluate(([px, py]) => {
    const el = document.elementFromPoint(px, py);
    if (!el) return { 命中: null, 标签: '(空)' };
    const n = el.closest('.react-flow__node');
    return { 命中: n ? n.getAttribute('data-id') : null, 标签: el.tagName + '.' + (el.className || '').toString().slice(0, 46) };
  }, [x, y]);
  const 表 = (a) => Object.fromEntries(a.map(n => [n.id, n.canvas]));

  // 在目标节点的框内网格采样，找一个「确实属于它」的落点
  const 找落点 = async (id) => {
    const all = await 读全部();
    const st = all.find(n => n.id === id);
    if (!st) return null;
    const [bx, by, bw, bh] = st.box;
    const 候选 = [];
    for (const fx of [0.5, 0.2, 0.8, 0.05, 0.95, 0.35, 0.65]) {
      for (const fy of [0.06, 0.5, 0.94, 0.25, 0.75]) {
        候选.push([Math.round(bx + bw * fx), Math.round(by + bh * fy)]);
      }
    }
    for (const [x, y] of 候选) {
      const g = await 归属(x, y);
      if (g.命中 === id) return { x, y, 标签: g.标签 };
    }
    return null;
  };

  const 修 = async (id, 目标, 最大轮) => {
    for (let i = 0; i < 最大轮; i++) {
      const all = await 读全部();
      const st = all.find(n => n.id === id);
      if (!st || !st.canvas) return '节点不在';
      const dx = st.canvas[0] - 目标[0], dy = st.canvas[1] - 目标[1];
      if (Math.abs(dx) < 0.8 && Math.abs(dy) < 0.8) return `✅ 已到位（残差 ${dx.toFixed(2)},${dy.toFixed(2)}）`;
      const 落 = await 找落点(id);
      if (!落) { 记(`　${id} 找不到属于自己的落点`); return '无落点'; }
      const v = await 读视口();
      const z = v.zoom || 0.29;
      const 前 = 表(await 读全部());
      const dsx = -dx * z, dsy = -dy * z;
      记(`　${id} 第 ${i + 1} 次：画布差 ${dx.toFixed(0)},${dy.toFixed(0)} → 屏幕 ${dsx.toFixed(1)},${dsy.toFixed(1)}（z=${z.toFixed(3)}）落点 ${落.x},${落.y} 命中=${落.标签}`);
      await page.mouse.move(落.x, 落.y);
      await page.mouse.down();
      await page.mouse.move(落.x + dsx / 3, 落.y + dsy / 3, { steps: 14 });
      await page.mouse.move(落.x + dsx * 2 / 3, 落.y + dsy * 2 / 3, { steps: 14 });
      await page.mouse.move(落.x + dsx, 落.y + dsy, { steps: 14 });
      await page.waitForTimeout(500);
      await page.mouse.up();
      await page.waitForTimeout(2300);
      const 后 = 表(await 读全部());
      const 动的 = Object.keys(后).filter(k => 前[k] && 后[k] && (Math.abs(后[k][0] - 前[k][0]) > 0.5 || Math.abs(后[k][1] - 前[k][1]) > 0.5));
      记(`　　⇒ 动的是 ${JSON.stringify(动的)}；${id} 现 ${JSON.stringify(后[id])}`);
      if (动的.length && 动的[0] !== id) return `⚠️ 仍然拖错了（动了 ${JSON.stringify(动的)}），停止`;
    }
    return '多轮未收敛';
  };

  const 开 = await 读全部();
  记(`开局：${JSON.stringify(表(开))}`);
  const 坏 = 开.filter(n => 标准[n.id] && n.canvas && (Math.abs(n.canvas[0] - 标准[n.id][0]) > 1.5 || Math.abs(n.canvas[1] - 标准[n.id][1]) > 1.5));
  记(`待修：${JSON.stringify(坏.map(n => [n.id, n.canvas, 标准[n.id]]))}`);

  for (const n of 坏) 记(`修 ${n.id}：${await 修(n.id, 标准[n.id], 5)}`);

  记('\n静置 15s…');
  await page.waitForTimeout(15000);
  const 终 = await 读全部();
  const 差 = 终.filter(n => 标准[n.id] && (!n.canvas || Math.abs(n.canvas[0] - 标准[n.id][0]) > 1.5 || Math.abs(n.canvas[1] - 标准[n.id][1]) > 1.5));
  记(`⭐ 终检：${终.length} 个节点，仍不符 ${JSON.stringify(差.map(n => [n.id, n.canvas, 标准[n.id]]))}`);
  记(`全表：${JSON.stringify(表(终))}`);
  结果.读数.终检 = 终;
  await page.screenshot({ path: EVID + 'ei22-终检.png' });
  await page.waitForTimeout(5000);
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI22.json ===');
}
