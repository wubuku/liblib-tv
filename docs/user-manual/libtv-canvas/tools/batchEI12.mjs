// Batch EI-12：⭐ 把 📖「合并分镜组 在纯图片选区下能不能用」升级成实测。
//
// 难点：全画布只有 2 个图片节点，而它们之间**正好**卡着视频节点 v-eMpqKtiLlx（y 范围完全相同 [317,481]），
//       所以**任何一条框选矩形都不可能只圈住这两张图**。
// 解法：把两个图片节点**临时挪**到画布空区（挪动不是删除，不动任何数据），框选验证，再**精确挪回**。
// 安全：全程记录每一步的 style.transform，结束时逐个核对复原；基线节点一个都不删。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEI12.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 移 = { i1: 'i-9nlG6HdjK2', i2: 'i-sODTbgLUm1' };
const 目标 = { i1: [430, 520], i2: [760, 520] };     // 画布空区的左上角（CSS px，47% 缩放下）

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

  const 视口 = await page.evaluate(() => {
    const el = document.querySelector('.react-flow__viewport');
    return { transform: el ? el.style.transform : '(无)', 文字: el ? el.textContent.slice(0, 0) : '' };
  });
  记(`视口 transform：${视口.transform}`);
  结果.读数.视口 = 视口;

  const 读节点 = () => page.evaluate((ids) => {
    const o = {};
    for (const id of ids) {
      const el = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!el) { o[id] = null; continue; }
      const r = el.getBoundingClientRect();
      o[id] = { transform: el.style.transform, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
    }
    return o;
  }, [移.i1, 移.i2]);

  const 原始 = await 读节点();
  记(`原始位置：${JSON.stringify(原始)}`);
  结果.读数.原始 = 原始;

  // ---- 挪动：屏幕拖拽。节点移动距离 = 画布距离 / zoom
  const 挪 = async (id, 目标xy) => {
    for (let 轮 = 0; 轮 < 3; 轮++) {
      const 状态 = (await 读节点())[id];
      if (!状态) return `${id} 不见了`;
      // transform 形如 translate(Xpx, Ypx)，X/Y 是**画布坐标**
      const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(状态.transform);
      if (!m) return `${id} transform 解析不了：${状态.transform}`;
      const cx = parseFloat(m[1]), cy = parseFloat(m[2]);
      const b = 状态.box;
      const sx = b[0] + b[2] / 2, sy = b[1] + b[3] / 2;
      // 目标左上角（CSS px）→ 画布坐标 = (目标 + 视口偏移) / zoom；直接用「当前左上角 → 目标左上角」的屏幕差即可
      const dxScreen = 目标xy[0] - b[0];
      const dyScreen = 目标xy[1] - b[1];
      await page.mouse.move(sx, sy);
      await page.mouse.down();
      await page.mouse.move(sx + dxScreen / 2, sy + dyScreen / 2, { steps: 8 });
      await page.mouse.move(sx + dxScreen, sy + dyScreen, { steps: 8 });
      await page.waitForTimeout(350);
      await page.mouse.up();
      await page.waitForTimeout(1300);
      const 后 = (await 读节点())[id];
      const 误差 = 后 ? [Math.round(后.box[0] - 目标xy[0]), Math.round(后.box[1] - 目标xy[1])] : null;
      记(`  挪 ${id} 第 ${轮 + 1} 轮：目标 [${目标xy}]，实际误差 ${JSON.stringify(误差)}`);
      if (误差 && Math.abs(误差[0]) <= 2 && Math.abs(误差[1]) <= 2) return '已到位';
    }
    return '三轮后仍有误差';
  };

  记('① 挪两个图片节点到空区：');
  const 挪1 = await 挪(移.i1, 目标.i1);
  记(`　${移.i1}: ${挪1}`);
  const 挪2 = await 挪(移.i2, 目标.i2);
  记(`　${移.i2}: ${挪2}`);
  const 挪后 = await 读节点();
  记(`挪完：${JSON.stringify(挪后)}`);
  结果.读数.挪后 = 挪后;
  await page.screenshot({ path: EVID + 'ei12-挪开后.png' });

  // ---- 框选：只框这两张图
  const b1 = 挪后[移.i1].box, b2 = 挪后[移.i2].box;
  const x1 = Math.min(b1[0], b2[0]) - 14, y1 = Math.min(b1[1], b2[1]) - 12;
  const x2 = Math.max(b1[0] + b1[2], b2[0] + b2[2]) + 14, y2 = Math.max(b1[1] + b1[3], b2[1] + b2[3]) + 12;
  await page.mouse.move(1300, 820); await page.mouse.click(1300, 820); await page.waitForTimeout(700);
  await page.mouse.move(x1, y1); await page.mouse.down();
  await page.mouse.move((x1 + x2) / 2, (y1 + y2) / 2, { steps: 10 });
  await page.mouse.move(x2, y2, { steps: 10 });
  await page.waitForTimeout(350); await page.mouse.up();
  await page.mouse.move(1300, 820);
  await page.waitForTimeout(1800);

  const 选中 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => ({
    id: n.getAttribute('data-id'), 类型: (n.className.toString().match(/react-flow__node-([a-zA-Z]+)/) || [, '?'])[1],
  })));
  记(`\n⭐ 框选结果：${JSON.stringify(选中)}`);
  结果.读数.框选 = 选中;
  await page.screenshot({ path: EVID + 'ei12-只框两图.png' });

  const 找工具条 = () => page.evaluate(() => {
    const all = [...document.querySelectorAll('div')].filter(e => /保存到资产/.test(e.innerText || '') && e.getBoundingClientRect().width > 300 && e.getBoundingClientRect().height > 0);
    if (!all.length) return { 找到: false };
    all.sort((p, q) => p.getBoundingClientRect().width - q.getBoundingClientRect().width);
    const c = all[0]; const r = c.getBoundingClientRect();
    return { 找到: true, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 按钮: [...c.querySelectorAll('button')].map(b => { const rb = b.getBoundingClientRect(); return { 文字: (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 12) || (b.getAttribute('aria-label') || '(无名)'), box: [Math.round(rb.left), Math.round(rb.top), Math.round(rb.width), Math.round(rb.height)] }; }) };
  });
  const 条 = await 找工具条();
  记(`工具条：${条.找到 ? JSON.stringify(条.box) + ' 按钮 ' + JSON.stringify(条.按钮.map(b => b.文字)) : '没出现'}`);
  结果.读数.工具条 = 条;

  if (条.找到) {
    const 打 = 条.按钮.find(b => b.文字.startsWith('打组'));
    await page.mouse.click(Math.round(打.box[0] + 打.box[2] / 2), Math.round(打.box[1] + 打.box[3] / 2));
    await page.waitForTimeout(1500);
    const 项 = await page.evaluate(() => {
      const all = [...document.querySelectorAll('body *')].filter(e => /合并分镜组/.test(e.innerText || '') && e.getBoundingClientRect().width > 0);
      if (!all.length) return { 错: '菜单没开' };
      all.sort((p, q) => p.getBoundingClientRect().width * p.getBoundingClientRect().height - q.getBoundingClientRect().width * q.getBoundingClientRect().height);
      let h = all[0]; for (let i = 0; i < 3; i++) { if (h.querySelectorAll('button').length >= 2) break; h = h.parentElement; }
      return [...h.querySelectorAll('button')].map(e => { const cs = getComputedStyle(e); return { 文本: (e.innerText || '').trim().slice(0, 12), opacity: cs.opacity, cursor: cs.cursor, disabled: e.disabled === true }; });
    });
    记(`\n⭐⭐【真值表】选区只有 2 个图片节点时，「打组」下拉：${JSON.stringify(项)}`);
    结果.读数.真值表 = 项;
    await page.screenshot({ path: EVID + 'ei12-两图下拉-全图.png' });
    const r2 = await page.evaluate(() => {
      const all = [...document.querySelectorAll('body *')].filter(e => /合并分镜组/.test(e.innerText || '') && e.getBoundingClientRect().width > 0);
      all.sort((p, q) => p.getBoundingClientRect().width * p.getBoundingClientRect().height - q.getBoundingClientRect().width * q.getBoundingClientRect().height);
      const r = all[0].getBoundingClientRect();
      return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
    });
    await page.screenshot({ path: EVID + 'ei12-两图下拉-裁图.png', clip: { x: Math.max(0, r2[0] - 230), y: Math.max(0, r2[1] - 110), width: 470, height: 210 } });
    记('✅ 已拍两图下拉（干净 + 裁图）');
    await page.keyboard.press('Escape');
    await page.waitForTimeout(900);
  }

  // ---- 复原：把两个图片节点挪回原始屏幕位置
  记('\n③ 复原位置：');
  const 当前 = await 读节点();
  for (const key of ['i1', 'i2']) {
    const id = 移[key];
    const 原 = 原始[id];
    const 目 = { x: 原.box[0], y: 原.box[1] };
    for (let 轮 = 0; 轮 < 3; 轮++) {
      const st = (await 读节点())[id];
      const dx = 目.x - st.box[0], dy = 目.y - st.box[1];
      if (Math.abs(dx) <= 2 && Math.abs(dy) <= 2) { 记(`　${id} 已回到原位（误差 ${dx},${dy}）`); break; }
      const sx = st.box[0] + st.box[2] / 2, sy = st.box[1] + st.box[3] / 2;
      await page.mouse.move(sx, sy); await page.mouse.down();
      await page.mouse.move(sx + dx / 2, sy + dy / 2, { steps: 8 });
      await page.mouse.move(sx + dx, sy + dy, { steps: 8 });
      await page.waitForTimeout(350); await page.mouse.up();
      await page.waitForTimeout(1300);
      记(`　${id} 第 ${轮 + 1} 轮回移，位移 ${dx},${dy}`);
    }
  }
  const 复原 = await 读节点();
  const 核对 = {};
  for (const key of ['i1', 'i2']) {
    const id = 移[key];
    核对[id] = {
      原transform: 原始[id].transform, 现transform: 复原[id].transform,
      差: (() => {
        const a = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(原始[id].transform) || [];
        const b = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(复原[id].transform) || [];
        return a.length && b.length ? [Math.round(parseFloat(b[1]) - parseFloat(a[1])), Math.round(parseFloat(b[2]) - parseFloat(a[2]))] : '解析不了';
      })(),
    };
  }
  结果.读数.复原核对 = 核对;
  记(`复原核对：${JSON.stringify(核对)}`);
  await page.screenshot({ path: EVID + 'ei12-复原后.png' });
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI12.json ===');
}
