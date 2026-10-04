// Batch EI-16：⛔① 修 v-eMpqKtiLlx：EI-15 误把它从 (-1787,900) 拖到 (-1068,864)，没复原。
//          ② 静置 15s 再读，确认这次真的落盘（EI-13/EI-14 的「复原成功」都没落盘过）。
//          ③ ⭐ 改用**无破坏**手段做真值表：框选后用 ⌘-点 / Shift-点把多余的节点**移出选区**，
//             绝不移动任何节点。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEI16.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

// ⭐ 权威坐标（来自 EI-14/15 读数里未被本轮改动过的整数值）
const 标准 = {
  'a-GgqvrVz0pw': [719.388, 1509.13], 'a-THmbuJXQj4': [-1356, 600], 'b-mfkcQNULC3': [636, 300],
  'i-9nlG6HdjK2': [-1764, 900], 'i-sODTbgLUm1': [-168, 900], 'n-56F19pXVB4': [-1225.03, 370.975],
  't-2AK3Ukyxj3': [-1476, 1524], 't-UtVx3lZmrV': [600, 900], 'v-eMpqKtiLlx': [-1787, 900],
  'v-oZNpH99MtM': [132, 300], 'v-v2hlWY4Br3': [-696, 300],
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
  await page.waitForTimeout(3000);

  const 读视口 = () => page.evaluate(() => {
    const el = document.querySelector('.react-flow__viewport');
    const m = el ? /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)[^)]*scale\((-?[\d.]+)\)/.exec(el.style.transform || '') : null;
    return m ? { zoom: parseFloat(m[3]), raw: el.style.transform } : { raw: '(无)' };
  });
  const 读全部 = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map(n => {
    const r = n.getBoundingClientRect();
    const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    return { id: n.getAttribute('data-id'), 类型: (n.className.toString().match(/react-flow__node-([a-zA-Z]+)/) || [, '?'])[1], canvas: m ? [parseFloat(m[1]), parseFloat(m[2])] : null, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }));
  const 读一 = (id) => page.evaluate((i) => {
    const el = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(el.style.transform || '');
    return { canvas: m ? [parseFloat(m[1]), parseFloat(m[2])] : null, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }, id);

  const 开局 = await 读全部();
  const 差异 = 开局.filter(n => 标准[n.id] && (!n.canvas || Math.abs(n.canvas[0] - 标准[n.id][0]) > 1.5 || Math.abs(n.canvas[1] - 标准[n.id][1]) > 1.5))
    .map(n => ({ id: n.id, 标准: 标准[n.id], 现: n.canvas }));
  记(`开局：${开局.length} 个节点；与标准不符的：${JSON.stringify(差异)}`);
  结果.读数.开局 = 开局;
  结果.读数.差异 = 差异;

  // ---- ① 修 v-eMpqKtiLlx
  for (const d of 差异) {
    for (let 轮 = 0; 轮 < 5; 轮++) {
      const v = await 读视口();
      const st = await 读一(d.id);
      if (!st || !st.canvas) break;
      const dcx = d.标准[0] - st.canvas[0], dcy = d.标准[1] - st.canvas[1];
      if (Math.abs(dcx) < 1.2 && Math.abs(dcy) < 1.2) { 记(`✅ ${d.id} 已复原，残差 ${dcx.toFixed(2)},${dcy.toFixed(2)}`); break; }
      const z = v.zoom || 0.468869;
      const sx = st.box[0] + st.box[2] / 2, sy = st.box[1] + st.box[3] / 2;
      await page.mouse.move(sx, sy); await page.mouse.down();
      await page.mouse.move(sx + dcx * z / 2, sy + dcy * z / 2, { steps: 10 });
      await page.mouse.move(sx + dcx * z, sy + dcy * z, { steps: 10 });
      await page.waitForTimeout(450); await page.mouse.up();
      await page.waitForTimeout(2000);
      记(`　${d.id} 第 ${轮 + 1} 轮画布差 ${dcx.toFixed(1)},${dcy.toFixed(1)}（zoom ${z.toFixed(4)}）`);
    }
  }
  // ⭐ 静置 15 秒再读：验证是否真的落盘（这正是 EI-13/14 栽的地方）
  记('静置 15s 等落盘…');
  await page.waitForTimeout(15000);
  const 静置后 = await 读全部();
  const 残 = 静置后.filter(n => 标准[n.id] && (!n.canvas || Math.abs(n.canvas[0] - 标准[n.id][0]) > 1.5 || Math.abs(n.canvas[1] - 标准[n.id][1]) > 1.5)).map(n => ({ id: n.id, 标准: 标准[n.id], 现: n.canvas }));
  记(`⭐ 静置后仍不符的：${JSON.stringify(残)}`);
  结果.读数.静置后差异 = 残;
  await page.screenshot({ path: EVID + 'ei16-复原后.png' });

  // ---- ② ⭐ 无破坏真值表：框选 → 用 ⌘-点 把非图片节点移出选区
  const 找工具条 = () => page.evaluate(() => {
    const all = [...document.querySelectorAll('div')].filter(e => /保存到资产/.test(e.innerText || '') && e.getBoundingClientRect().width > 300 && e.getBoundingClientRect().height > 0);
    if (!all.length) return { 找到: false };
    all.sort((p, q) => p.getBoundingClientRect().width - q.getBoundingClientRect().width);
    const c = all[0]; const r = c.getBoundingClientRect();
    return { 找到: true, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 按钮: [...c.querySelectorAll('button')].map(b => { const rb = b.getBoundingClientRect(); return { 文字: (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 12) || (b.getAttribute('aria-label') || '(无名)'), box: [Math.round(rb.left), Math.round(rb.top), Math.round(rb.width), Math.round(rb.height)] }; }) };
  });
  const 读下拉 = async () => {
    const 条 = await 找工具条();
    const 打 = 条.按钮 && 条.按钮.find(b => b.文字.startsWith('打组'));
    if (!打) return { 错: '工具条上没有「打组」' };
    await page.mouse.click(Math.round(打.box[0] + 打.box[2] / 2), Math.round(打.box[1] + 打.box[3] / 2));
    await page.waitForTimeout(1500);
    const 项 = await page.evaluate(() => {
      const all = [...document.querySelectorAll('body *')].filter(e => /合并分镜组/.test(e.innerText || '') && e.getBoundingClientRect().width > 0);
      if (!all.length) return { 错: '菜单没开' };
      all.sort((p, q) => p.getBoundingClientRect().width * p.getBoundingClientRect().height - q.getBoundingClientRect().width * q.getBoundingClientRect().height);
      let h = all[0]; for (let i = 0; i < 3; i++) { if (h.querySelectorAll('button').length >= 2) break; h = h.parentElement; }
      return [...h.querySelectorAll('button')].map(e => { const cs = getComputedStyle(e); return { 文本: (e.innerText || '').trim().slice(0, 12), opacity: cs.opacity, cursor: cs.cursor }; });
    });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(800);
    return 项;
  };

  const 节点 = await 读全部();
  const N = Object.fromEntries(节点.map(n => [n.id, n]));
  const 要移出 = ['a-GgqvrVz0pw', 'a-THmbuJXQj4', 'n-56F19pXVB4', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3', 't-UtVx3lZmrV', 't-2AK3Ukyxj3', 'b-mfkcQNULC3'];
  const ps = 节点.map(n => n.box);
  const x1 = Math.min(...ps.map(p => p[0])) - 20, y1 = Math.min(...ps.map(p => p[1])) - 12;
  const x2 = Math.max(...ps.map(p => p[0] + p[2])) + 20, y2 = Math.max(...ps.map(p => p[1] + p[3])) + 12;
  await page.mouse.click(1395, 845); await page.waitForTimeout(700);
  await page.mouse.move(x1, y1); await page.mouse.down();
  await page.mouse.move((x1 + x2) / 2, (y1 + y2) / 2, { steps: 10 });
  await page.mouse.move(x2, y2, { steps: 10 });
  await page.waitForTimeout(350); await page.mouse.up();
  await page.mouse.move(1395, 845);
  await page.waitForTimeout(1800);
  记(`\n全框选后：${JSON.stringify(await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id'))))}`);

  // 用 ⌘-点把非图片节点逐个移出选区（**点节点卡片空白边角，避开标题与播放键**）
  for (const id of 要移出) {
    if (!N[id]) continue;
    const b = N[id].box;
    const px = b[0] + b[2] - 10, py = b[1] + b[3] - 10;      // 右下角内 10px
    await page.keyboard.down('Meta');
    await page.mouse.click(px, py);
    await page.keyboard.up('Meta');
    await page.waitForTimeout(700);
  }
  await page.mouse.move(1395, 845);
  await page.waitForTimeout(1800);
  const 剩 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => ({ id: n.getAttribute('data-id'), 类: (n.className.toString().match(/react-flow__node-([a-zA-Z]+)/) || [, '?'])[1] })));
  记(`⭐ ⌘-点移出后，选区：${JSON.stringify(剩)}`);
  const 条 = await 找工具条();
  记(`工具条：${条.找到 ? '仍在' : '消失'}`);
  结果.读数.无破坏选区 = { 选区: 剩, 工具条还在: 条.找到 };
  await page.screenshot({ path: EVID + 'ei16-cmd点移出后.png' });

  if (条.找到 && 剩.length === 2 && 剩.every(s => s.类 === 'image')) {
    const 项 = await 读下拉();
    记(`\n⭐⭐⭐【真值表·阳性对照】选区 = 2 个图片节点 ⇒「打组」下拉：${JSON.stringify(项)}`);
    结果.读数.真值表 = 项;
    await page.screenshot({ path: EVID + 'ei16-真值表-全图.png' });
    const 裁 = await page.evaluate(() => {
      const all = [...document.querySelectorAll('body *')].filter(e => /合并分镜组/.test(e.innerText || '') && e.getBoundingClientRect().width > 0);
      if (!all.length) return [0, 0, 0, 0];
      all.sort((p, q) => p.getBoundingClientRect().width * p.getBoundingClientRect().height - q.getBoundingClientRect().width * q.getBoundingClientRect().height);
      const r = all[0].getBoundingClientRect();
      return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
    });
    await page.keyboard.down('Meta');
    await page.mouse.click(裁[0] + 裁[2] / 2, 裁[1] + 40);
    await page.mouse.up('Meta');
    await page.waitForTimeout(1400);
    await page.screenshot({ path: EVID + 'ei16-真值表-裁图.png', clip: { x: Math.max(0, 裁[0] - 200), y: Math.max(0, 裁[1] - 110), width: 430, height: 200 } });
    记('✅ 已拍真值表裁图');
    await page.keyboard.press('Escape');
    await page.waitForTimeout(700);
  } else {
    记(`⚠️ 没拿到「纯 2 图」选区（下拉仍可读，作为对照）：${JSON.stringify(await 读下拉())}`);
  }

  // ---- 收尾再核一次位置（全程没动过节点，应该还是标准值）
  const 收尾 = await 读全部();
  const 收尾差 = 收尾.filter(n => 标准[n.id] && (!n.canvas || Math.abs(n.canvas[0] - 标准[n.id][0]) > 1.5 || Math.abs(n.canvas[1] - 标准[n.id][1]) > 1.5)).map(n => ({ id: n.id, 标准: 标准[n.id], 现: n.canvas }));
  记(`\n收尾位置核查：${JSON.stringify(收尾差)}`);
  结果.读数.收尾差异 = 收尾差;
  await page.waitForTimeout(8000);
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI16.json ===');
}
