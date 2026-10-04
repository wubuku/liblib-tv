// Batch EI-10：⭐⭐ 推翻「点选不出工具条」这个 EI-8/EI-9 的读数。
//   真相：工具条是 absolute 定位、贴在**选区包围盒**顶边上方 14px（源码 GROUP_TOOLBAR_ROW_STYLE + translateY(-14px)），
//   EI-9 扫的 y∈[70,140] 这条带根本没覆盖到点选那一组（y≈271）⇒ 判据缺陷，不是功能缺失。
//   本脚本：① 全视口定位工具条，量它与选区包围盒的偏移（两种选法各量一次）
//           ② 两个图片节点时「合并分镜组」是否变亮（真值表）
//           ③ 开一次「打组」菜单后，蓝点是否消失（源码 !H 控制的提示点）
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEI10.json';
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
  await page.waitForTimeout(1800);

  // ⭐ 全视口找工具条：按「含『保存到资产』的最外层容器」定位，不预设 y
  const 找工具条 = () => page.evaluate(() => {
    const all = [...document.querySelectorAll('div')].filter(e => /保存到资产/.test(e.innerText || '') && e.getBoundingClientRect().width > 300 && e.getBoundingClientRect().height > 0);
    if (!all.length) return { 找到: false };
    all.sort((p, q) => p.getBoundingClientRect().width - q.getBoundingClientRect().width);
    const 容器 = all[0];
    const r = 容器.getBoundingClientRect();
    const btns = [...容器.querySelectorAll('button')].map(b => { const rb = b.getBoundingClientRect(); return { 文字: (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 12) || (b.getAttribute('aria-label') || '(无名)'), aria: b.getAttribute('aria-label') || '', box: [Math.round(rb.left), Math.round(rb.top), Math.round(rb.width), Math.round(rb.height)] }; });
    return {
      找到: true, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      class: 容器.className.toString().slice(0, 120),
      style: 容器.getAttribute('style'),
      按钮: btns,
    };
  });

  const 选区信息 = () => page.evaluate(() => {
    const sel = [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id'));
    const rects = [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getBoundingClientRect());
    if (!rects.length) return { 选中: sel, 包围盒: null };
    const l = Math.min(...rects.map(r => r.left)), t = Math.min(...rects.map(r => r.top));
    const rr = Math.max(...rects.map(r => r.right)), bb = Math.max(...rects.map(r => r.bottom));
    return { 选中: sel, 包围盒: [Math.round(l), Math.round(t), Math.round(rr - l), Math.round(bb - t)], 中心x: Math.round((l + rr) / 2), 顶边y: Math.round(t) };
  });

  const 量一次 = async (名) => {
    await page.waitForTimeout(1600);
    const 条 = await 找工具条();
    const 区 = await 选区信息();
    if (条.找到 && 区.包围盒) {
      记(`${名}：选区包围盒 ${JSON.stringify(区.包围盒)}（顶边 y=${区.顶边y}，中心 x=${区.中心x}，${区.选中.length} 个）`);
      记(`　　工具条 box=${JSON.stringify(条.box)}；横向差=${条.box[0] + 条.box[2] / 2 - 区.中心x}px，纵向差（选区顶边 − 工具条底边）=${区.顶边y - (条.box[1] + 条.box[3])}px`);
      记(`　　style=${条.style}`);
      记(`　　按钮：${JSON.stringify(条.按钮.map(b => b.文字))}`);
      记(`　　aria：${JSON.stringify(条.按钮.map(b => b.aria || '无'))}`);
    } else {
      记(`${名}：工具条 ${条.找到 ? '有' : '没有'}，选区 ${区.选中.length} 个`);
    }
    return { 名, 工具条: 条, 选区: 区 };
  };

  const 节点 = await page.evaluate(() => { const o = {}; for (const n of document.querySelectorAll('.react-flow__node')) { const r = n.getBoundingClientRect(); o[n.getAttribute('data-id')] = { 类型: (n.className.toString().match(/react-flow__node-([a-zA-Z]+)/) || [, '?'])[1], box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }; } return o; });
  结果.读数.节点 = 节点;

  // ---- 用法 A：点选 + Shift 加选（EI-9 判「没有工具条」的那一组）
  let b1 = 节点['i-9nlG6HdjK2'].box, b2 = 节点['i-sODTbgLUm1'].box;
  await page.mouse.click(Math.round(b1[0] + b1[2] / 2), Math.round(b1[1] + b1[3] / 2));
  await page.waitForTimeout(800);
  await page.keyboard.down('Shift');
  await page.mouse.click(Math.round(b2[0] + b2[2] / 2), Math.round(b2[1] + b2[3] / 2));
  await page.keyboard.up('Shift');
  await page.mouse.move(700, 780);
  const A = await 量一次('【A 点选 + Shift 加选两个图片】');
  await page.screenshot({ path: EVID + 'ei10-A-点选两图.png' });
  await page.screenshot({ path: EVID + 'ei10-A-裁.png', clip: { x: 60, y: 200, width: 1120, height: 340 } });
  结果.读数.A = A;

  // ---- 用法 B：框选这两个（严格只框住它们 ⇒ 用来跑真值表）
  await page.keyboard.press('Escape');
  await page.mouse.click(1200, 780);
  await page.waitForTimeout(1000);
  b1 = 节点['i-9nlG6HdjK2'].box; b2 = 节点['i-sODTbgLUm1'].box;
  const y1 = Math.min(b1[1], b2[1]) - 6, y2 = Math.max(b1[1] + b1[3], b2[1] + b2[3]) + 6;
  await page.mouse.move(b1[0] - 14, y1); await page.mouse.down();
  await page.mouse.move((b1[0] + b2[0] + b2[2]) / 2, (y1 + y2) / 2, { steps: 10 });
  await page.mouse.move(b2[0] + b2[2] + 14, y2, { steps: 10 });
  await page.waitForTimeout(300); await page.mouse.up();
  await page.mouse.move(700, 780);
  const B = await 量一次('【B 框选（尽量只框两个图片）】');
  结果.读数.B = B;
  await page.screenshot({ path: EVID + 'ei10-B-框选两图.png' });

  // ---- 真值表：两个都是图片 ⇒ 「合并分镜组」应该变亮
  const 读下拉 = async () => {
    const 条 = await 找工具条();
    const 打 = 条.按钮 && 条.按钮.find(b => b.文字.startsWith('打组'));
    if (!打) return { 错: '工具条上没有「打组」' };
    await page.mouse.click(Math.round(打.box[0] + 打.box[2] / 2), Math.round(打.box[1] + 打.box[3] / 2));
    await page.waitForTimeout(1400);
    const 项 = await page.evaluate(() => {
      const all = [...document.querySelectorAll('body *')].filter(e => /合并分镜组/.test(e.innerText || '') && e.getBoundingClientRect().width > 0);
      if (!all.length) return { 错: '菜单没开' };
      all.sort((p, q) => p.getBoundingClientRect().width * p.getBoundingClientRect().height - q.getBoundingClientRect().width * q.getBoundingClientRect().height);
      let 宿主 = all[0]; for (let i = 0; i < 3; i++) { if (宿主.querySelectorAll('button').length >= 2) break; 宿主 = 宿主.parentElement; }
      return [...宿主.querySelectorAll('button')].map(e => { const cs = getComputedStyle(e); return { 文本: (e.innerText || '').trim().slice(0, 12), opacity: cs.opacity, cursor: cs.cursor, disabled: e.disabled === true }; });
    });
    return 项;
  };
  const 区B = await 选区信息();
  const 下拉B = await 读下拉();
  记(`\n【真值表·全是图片】选区 ${JSON.stringify(区B.选中)} → 下拉：${JSON.stringify(下拉B)}`);
  结果.读数.真值表_全图片 = { 选区: 区B, 下拉: 下拉B };
  await page.screenshot({ path: EVID + 'ei10-真值表-两图下拉.png', clip: { x: 480, y: 180, width: 340, height: 200 } });

  // ---- 蓝点：开过一次菜单后，dot 是否消失（源码 !H；Q 会 safeSetItem(n5,"1")）
  const 点前 = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find(x => (x.getAttribute('aria-label') || '') === '打组菜单');
    if (!b) return { 错: '找不到「打组菜单」按钮' };
    const dot = [...b.querySelectorAll('span')].map(s => { const r = s.getBoundingClientRect(); return { 尺寸: [Math.round(r.width), Math.round(r.height)], 背景: getComputedStyle(s).backgroundColor }; }).filter(x => x.尺寸[0] > 0 && x.尺寸[0] <= 6);
    return { aria: b.getAttribute('aria-label'), 蓝点: dot, localStorage键: Object.keys(localStorage).filter(k => /group|menu|hint|tip|guide/i.test(k)) };
  });
  记(`\n⭐ 开菜单前：「打组菜单」按钮蓝点=${JSON.stringify(点前.蓝点)}；相关 localStorage 键=${JSON.stringify(点前.localStorage键)}`);
  结果.读数.蓝点_开前 = 点前;

  await page.keyboard.press('Escape');
  await page.waitForTimeout(1000);
  const 点后 = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find(x => (x.getAttribute('aria-label') || '') === '打组菜单');
    if (!b) return { 错: '菜单关掉后按钮不见了' };
    const dot = [...b.querySelectorAll('span')].map(s => { const r = s.getBoundingClientRect(); return { 尺寸: [Math.round(r.width), Math.round(r.height)], 背景: getComputedStyle(s).backgroundColor }; }).filter(x => x.尺寸[0] > 0 && x.尺寸[0] <= 6);
    return { 蓝点: dot, localStorage键: Object.keys(localStorage).filter(k => /group|menu|hint|tip|guide/i.test(k)), 值: Object.fromEntries(Object.keys(localStorage).filter(k => /group|menu|hint|tip|guide/i.test(k)).map(k => [k, localStorage.getItem(k)])) };
  });
  记(`⭐ 开过一次菜单并关掉后：蓝点=${JSON.stringify(点后.蓝点)}；localStorage=${JSON.stringify(点后.值)}`);
  结果.读数.蓝点_开后 = 点后;
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI10.json ===');
}
