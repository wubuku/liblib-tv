// Batch EI-15：⭐ 补上「合并分镜组」的**阳性对照**（阴性结论必须配阳性对照）。
//   难点：47% 下画布挤得满满的，找不到一个能同时装下两张 292×164 图片、又不碰到别的节点的框选矩形。
// 解法：缩到 25% → 程序化搜一块**确认空无一物**的区域 → 把两张图挪进去 → 框选 → 读下拉 → 挪回。
//   挪动用**画布坐标**驱动（EI-14 已验证可靠），结束必复原并终检。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEI15.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 原始 = { 'i-9nlG6HdjK2': [-1764, 900], 'i-sODTbgLUm1': [-168, 900] };
const 两图 = ['i-9nlG6HdjK2', 'i-sODTbgLUm1'];

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
  const 全部 = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map(n => {
    const r = n.getBoundingClientRect();
    const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    return { id: n.getAttribute('data-id'), 类型: (n.className.toString().match(/react-flow__node-([a-zA-Z]+)/) || [, '?'])[1], canvas: m ? [parseFloat(m[1]), parseFloat(m[2])] : null, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }));
  const 读 = async (id) => (await page.evaluate((i) => {
    const el = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(el.style.transform || '');
    return { canvas: m ? [parseFloat(m[1]), parseFloat(m[2])] : null, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }, id));

  const 原始记录 = {};
  for (const id of 两图) 原始记录[id] = await 读(id);
  记(`原始画布坐标：${JSON.stringify(Object.fromEntries(两图.map(i => [i, 原始记录[i].canvas])))}`);
  结果.读数.原始 = 原始记录;

  // ---- 缩到 25%：点左下角百分比按钮 → 菜单里选 25
  const 缩放 = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button,div,span')].find(x => /^\d+%$/.test((x.innerText || '').trim()) && x.getBoundingClientRect().width < 60 && x.getBoundingClientRect().top > 700);
    if (!b) return { 错: '找不到缩放百分比' };
    const r = b.getBoundingClientRect();
    b.click();
    return { 点击: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
  });
  记(`点缩放按钮：${JSON.stringify(缩放)}`);
  await page.waitForTimeout(1300);
  const 选25 = await page.evaluate(() => {
    const all = [...document.querySelectorAll('button,li,div')].filter(x => (x.innerText || '').trim() === '25%' || (x.innerText || '').trim() === '25');
    const vis = all.filter(x => { const r = x.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
    if (!vis.length) return null;
    vis.sort((a, b) => a.getBoundingClientRect().width - b.getBoundingClientRect().width);
    const r = vis[0].getBoundingClientRect();
    vis[0].click();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
  });
  记(`菜单里选 25%：${JSON.stringify(选25)}`);
  await page.waitForTimeout(2200);
  const 视口 = await 读视口();
  记(`缩放后视口：${视口.raw}（zoom ${视口.zoom}）`);
  结果.读数.视口25 = 视口;

  // ---- 找一块确认空无一物的区域（排除底部工具栏与右侧按钮带）
  const 布局 = await 全部();
  记(`25% 下节点：${JSON.stringify(布局.map(n => [n.类型, n.box]))}`);
  结果.读数.布局25 = 布局;

  const 找空地 = (布局, 需宽, 需高) => {
    const 障碍 = 布局.filter(n => !两图.includes(n.id)).map(n => n.box);
    // 候选区：避开底部工具栏(y>730)、右侧积分区(x>1330)、顶部栏(y<48)
    for (let y = 300; y < 640; y += 10) {
      for (let x = 120; x < 1300 - 需宽; x += 10) {
        const r = [x, y, x + 需宽, y + 需高];
        const 碰 = 障碍.some(b => !(r[2] < b[0] || r[0] > b[0] + b[2] || r[3] < b[1] || r[1] > b[1] + b[3]));
        if (!碰) return r;
      }
    }
    return null;
  };
  const 尺寸 = await page.evaluate(() => {
    const el = document.querySelector('.react-flow__node[data-id="i-9nlG6HdjK2"]');
    const r = el.getBoundingClientRect();
    return [Math.round(r.width), Math.round(r.height)];
  });
  const 空地 = 找空地(布局, 尺寸[0] * 2 + 40, 尺寸[1] + 40);
  记(`25% 下图片节点尺寸 ${JSON.stringify(尺寸)}，找到的空地：${JSON.stringify(空地)}`);
  结果.读数.空地 = 空地;
  if (!空地) throw new Error('25% 下也没找到空地');

  // ---- 把两张图挪进空地
  const 挪到屏幕 = async (id, 目标xy) => {
    for (let 轮 = 0; 轮 < 5; 轮++) {
      const st = await 读(id);
      if (!st) return `${id} 不见了`;
      const dx = 目标xy[0] - st.box[0], dy = 目标xy[1] - st.box[1];
      if (Math.abs(dx) <= 2 && Math.abs(dy) <= 2) return '已到位';
      const sx = st.box[0] + st.box[2] / 2, sy = st.box[1] + st.box[3] / 2;
      await page.mouse.move(sx, sy); await page.mouse.down();
      await page.mouse.move(sx + dx / 2, sy + dy / 2, { steps: 8 });
      await page.mouse.move(sx + dx, sy + dy, { steps: 8 });
      await page.waitForTimeout(400); await page.mouse.up();
      await page.waitForTimeout(1600);
    }
    return '多轮后仍有误差';
  };
  const 放1 = [空地[0], 空地[1]];
  const 放2 = [空地[0] + 尺寸[0] + 40, 空地[1]];
  记(`挪动：${JSON.stringify(两图[0])} → [${放1}]，${JSON.stringify(两图[1])} → [${放2}]`);
  记(`　${两图[0]}: ${await 挪到屏幕(两图[0], 放1)}`);
  记(`　${两图[1]}: ${await 挪到屏幕(两图[1], 放2)}`);
  const 放后 = await 全部();
  记(`放好后：${JSON.stringify(放后.map(n => [n.id, n.box]))}`);
  结果.读数.放后 = 放后;
  await page.screenshot({ path: EVID + 'ei15-挪进空地.png' });

  // ---- 框选（只框这两张）
  const m1 = 放后.find(n => n.id === 两图[0]).box, m2 = 放后.find(n => n.id === 两图[1]).box;
  const rx1 = Math.min(m1[0], m2[0]) - 16, ry1 = Math.min(m1[1], m2[1]) - 14;
  const rx2 = Math.max(m1[0] + m1[2], m2[0] + m2[2]) + 16, ry2 = Math.max(m1[1] + m1[3], m2[1] + m2[3]) + 14;
  await page.mouse.click(1390, 845); await page.waitForTimeout(700);
  await page.mouse.move(rx1, ry1); await page.mouse.down();
  await page.mouse.move((rx1 + rx2) / 2, (ry1 + ry2) / 2, { steps: 8 });
  await page.mouse.move(rx2, ry2, { steps: 8 });
  await page.waitForTimeout(350); await page.mouse.up();
  await page.mouse.move(1390, 845);
  await page.waitForTimeout(1800);
  const 选中 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => ({ id: n.getAttribute('data-id'), 类型: (n.className.toString().match(/react-flow__node-([a-zA-Z]+)/) || [, '?'])[1] })));
  记(`\n⭐ 框选结果：${JSON.stringify(选中)}`);
  结果.读数.框选 = 选中;
  await page.screenshot({ path: EVID + 'ei15-只框两图.png' });

  const 找工具条 = () => page.evaluate(() => {
    const all = [...document.querySelectorAll('div')].filter(e => /保存到资产/.test(e.innerText || '') && e.getBoundingClientRect().width > 120 && e.getBoundingClientRect().height > 0);
    if (!all.length) return { 找到: false };
    all.sort((p, q) => p.getBoundingClientRect().width - q.getBoundingClientRect().width);
    const c = all[0]; const r = c.getBoundingClientRect();
    return { 找到: true, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 按钮: [...c.querySelectorAll('button')].map(b => { const rb = b.getBoundingClientRect(); return { 文字: (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 12) || (b.getAttribute('aria-label') || '(无名)'), box: [Math.round(rb.left), Math.round(rb.top), Math.round(rb.width), Math.round(rb.height)] }; }) };
  });
  const 条 = await 找工具条();
  记(`工具条：${条.找到 ? JSON.stringify(条.box) : '没出现'}`);
  结果.读数.工具条 = 条;

  if (条.找到) {
    const 打 = 条.按钮.find(b => b.文字.startsWith('打组'));
    await page.mouse.click(Math.round(打.box[0] + 打.box[2] / 2), Math.round(打.box[1] + 打.box[3] / 2));
    await page.waitForTimeout(1600);
    const 项 = await page.evaluate(() => {
      const all = [...document.querySelectorAll('body *')].filter(e => /合并分镜组/.test(e.innerText || '') && e.getBoundingClientRect().width > 0);
      if (!all.length) return { 错: '菜单没开' };
      all.sort((p, q) => p.getBoundingClientRect().width * p.getBoundingClientRect().height - q.getBoundingClientRect().width * q.getBoundingClientRect().height);
      let h = all[0]; for (let i = 0; i < 3; i++) { if (h.querySelectorAll('button').length >= 2) break; h = h.parentElement; }
      return [...h.querySelectorAll('button')].map(e => { const cs = getComputedStyle(e); return { 文本: (e.innerText || '').trim().slice(0, 12), opacity: cs.opacity, cursor: cs.cursor, disabled: e.disabled === true }; });
    });
    记(`\n⭐⭐⭐【真值表·阳性对照】选区 = ${JSON.stringify(选中.map(s => s.类型))} ⇒「打组」下拉：${JSON.stringify(项)}`);
    结果.读数.真值表 = 项;
    await page.screenshot({ path: EVID + 'ei15-真值表-全图.png' });
    const 裁 = await page.evaluate(() => {
      const all = [...document.querySelectorAll('body *')].filter(e => /合并分镜组/.test(e.innerText || '') && e.getBoundingClientRect().width > 0);
      all.sort((p, q) => p.getBoundingClientRect().width * p.getBoundingClientRect().height - q.getBoundingClientRect().width * q.getBoundingClientRect().height);
      const r = all[0].getBoundingClientRect();
      return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
    });
    await page.screenshot({ path: EVID + 'ei15-真值表-裁图.png', clip: { x: Math.max(0, 裁[0] - 210), y: Math.max(0, 裁[1] - 110), width: 440, height: 200 } });
    记('✅ 已拍真值表裁图');
    await page.keyboard.press('Escape');
    await page.waitForTimeout(900);
  }

  // ---- 复原：先回 47% 视图再按画布坐标挪回（EI-14 验证过的做法）
  记('\n复原：');
  for (const id of 两图) {
    for (let 轮 = 0; 轮 < 5; 轮++) {
      const v = await 读视口();
      const st = await 读(id);
      if (!st || !st.canvas) break;
      const dcx = 原始[id][0] - st.canvas[0], dcy = 原始[id][1] - st.canvas[1];
      if (Math.abs(dcx) < 1.5 && Math.abs(dcy) < 1.5) { 记(`　✅ ${id} 画布坐标已复原，残差 ${dcx.toFixed(2)},${dcy.toFixed(2)}`); break; }
      const z = v.zoom || 0.25;
      const sx = st.box[0] + st.box[2] / 2, sy = st.box[1] + st.box[3] / 2;
      await page.mouse.move(sx, sy); await page.mouse.down();
      await page.mouse.move(sx + dcx * z / 2, sy + dcy * z / 2, { steps: 10 });
      await page.mouse.move(sx + dcx * z, sy + dcy * z, { steps: 10 });
      await page.waitForTimeout(450); await page.mouse.up();
      await page.waitForTimeout(1800);
      记(`　${id} 第 ${轮 + 1} 轮画布差 ${dcx.toFixed(1)},${dcy.toFixed(1)}（zoom ${z.toFixed(3)}）`);
    }
  }
  await page.waitForTimeout(3000);
  const 终 = {};
  for (const id of 两图) { const st = await 读(id); 终[id] = { 目标: 原始[id], 现: st.canvas, 残差: st.canvas ? [+(st.canvas[0] - 原始[id][0]).toFixed(2), +(st.canvas[1] - 原始[id][1]).toFixed(2)] : null }; }
  结果.读数.复原终检 = 终;
  记(`⭐ 静置 3s 后终检：${JSON.stringify(终)}`);
  await page.screenshot({ path: EVID + 'ei15-复原终检.png' });
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI15.json ===');
}
