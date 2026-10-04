// Batch EJ-3：排列菜单的项**不是 <button>**（EJ-2 一路爬到 BODY 才暴露出来），
//   和「组操作条」一样是 div/span。改用「精确文本匹配 + 取共同祖先」。
//
// ⭐ 顺带确认一件事：「批量下载」本身就是灰的（opacity 0.45 + cursor not-allowed），
//   和「合并分镜组」同一套禁用表达 —— 它的悬停气泡「当前选区无可下载的资源」正好解释了原因。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEJ3.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

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
  await page.waitForTimeout(3000);
  记(`开局坐标偏差：${JSON.stringify(await 核对坐标(page))}`);

  const 节点 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map(n => {
    const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), 类型: (n.className.toString().match(/react-flow__node-([a-zA-Z]+)/) || [, '?'])[1], box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }));
  const 找工具条 = () => page.evaluate(() => {
    const all = [...document.querySelectorAll('div')].filter(e => /保存到资产/.test(e.innerText || '') && e.getBoundingClientRect().width > 300 && e.getBoundingClientRect().height > 0);
    if (!all.length) return { 找到: false };
    all.sort((p, q) => p.getBoundingClientRect().width - q.getBoundingClientRect().width);
    const c = all[0]; const r = c.getBoundingClientRect();
    return { 找到: true, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 按钮: [...c.querySelectorAll('button')].map(b => { const rb = b.getBoundingClientRect(); const cs = getComputedStyle(b); return { 文字: (b.innerText || '').trim().slice(0, 12) || (b.getAttribute('aria-label') || '(无名)'), box: [Math.round(rb.left), Math.round(rb.top), Math.round(rb.width), Math.round(rb.height)], opacity: cs.opacity, cursor: cs.cursor }; }) };
  });

  // ⭐ 用「精确文本」找菜单项，取同时包含三项的最内层祖先当容器
  const 读菜单 = () => page.evaluate(() => {
    const 三项 = ['宫格排列', '水平排列', '垂直排列'];
    const 叶 = 三项.map(t => [...document.querySelectorAll('div,span,li,button')]
      .filter(e => (e.innerText || '').trim() === t && e.getBoundingClientRect().width > 0)
      .sort((a, b) => a.getBoundingClientRect().width - b.getBoundingClientRect().width)[0]);
    if (叶.some(x => !x)) return { 开: false, 缺: 三项.filter((t, i) => !叶[i]) };
    // 共同祖先
    let 容器 = 叶[0];
    while (容器 && !三項都在(容器)) 容器 = 容器.parentElement;
    function 三項都在(el) { return 三项.every(t => [...el.querySelectorAll('div,span,li,button')].some(e => (e.innerText || '').trim() === t)); }
    const r = 容器 ? 容器.getBoundingClientRect() : null;
    return {
      开: !!容器,
      容器: r ? [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] : null,
      容器class: 容器 ? (容器.className || '').toString().slice(0, 140) : '',
      容器style: 容器 ? (容器.getAttribute('style') || '').slice(0, 160) : '',
      上沿被切: r ? r.top < 0 : null,
      项: 容器 ? [...容器.querySelectorAll('div,span,li,button')]
        .filter(e => 三项.includes((e.innerText || '').trim()) && e.children.length <= 2)
        .map(e => { const rr = e.getBoundingClientRect(); const cs = getComputedStyle(e); return { 文本: e.innerText.trim(), tag: e.tagName, cls: (e.className || '').toString().slice(0, 80), box: [Math.round(rr.left), Math.round(rr.top), Math.round(rr.width), Math.round(rr.height)], opacity: cs.opacity, cursor: cs.cursor, svg数: e.querySelectorAll('svg').length }; }) : [],
    };
  });

  const 跑 = async (标签, ids) => {
    const ps = ids.map(id => 节点.find(n => n.id === id)).filter(Boolean);
    const x1 = Math.min(...ps.map(p => p.box[0])) - 20, y1 = Math.min(...ps.map(p => p.box[1])) - 12;
    const x2 = Math.max(...ps.map(p => p.box[0] + p.box[2])) + 20, y2 = Math.max(...ps.map(p => p.box[1] + p.box[3])) + 12;
    await page.mouse.click(1400, 848); await page.waitForTimeout(700);
    await page.mouse.move(x1, y1); await page.mouse.down();
    await page.mouse.move((x1 + x2) / 2, (y1 + y2) / 2, { steps: 10 });
    await page.mouse.move(x2, y2, { steps: 10 });
    await page.waitForTimeout(350); await page.mouse.up();
    await page.mouse.move(1400, 848); await page.waitForTimeout(1800);
    const 条 = await 找工具条();
    const 选 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
    记(`\n【${标签}】选区 ${JSON.stringify(选)}；工具条 ${JSON.stringify(条.box || null)}`);
    记(`　工具条七键的视觉态：${JSON.stringify((条.按钮 || []).map(b => [b.文字, b.opacity, b.cursor]))}`);
    if (!条.找到) return null;
    await page.mouse.click(Math.round(条.按钮[0].box[0] + 15), Math.round(条.按钮[0].box[1] + 16));
    await page.waitForTimeout(1600);
    const m = await 读菜单();
    记(`　菜单开=${m.开} 容器=${JSON.stringify(m.容器)} 上沿被切=${m.上沿被切}`);
    记(`　容器 class=${m.容器class}`);
    记(`　容器 style=${m.容器style}`);
    for (const it of (m.项 || [])) 记(`　　项「${it.文本}」 <${it.tag}> box=${JSON.stringify(it.box)} opacity=${it.opacity} cursor=${it.cursor} svg=${it.svg数}`);
    await page.screenshot({ path: EVID + `ej3-${标签}.png` });
    if (m.容器 && !m.上沿被切) {
      const c = m.容器;
      await page.screenshot({ path: EVID + `ej3-${标签}-裁图.png`, clip: { x: Math.max(0, c[0] - 290), y: Math.max(0, c[1] - 26), width: 640, height: c[3] + 70 } });
      记('　✅ 已拍裁图');
    }
    await page.keyboard.press('Escape');
    await page.waitForTimeout(900);
    return m;
  };

  const 低 = 节点.filter(n => n.box[1] > 450);
  const A = 低.length >= 2 ? await 跑('低处-菜单完整', 低.slice(0, 2).map(n => n.id)) : null;
  const 图 = 节点.filter(n => n.类型 === 'image');
  const B = 图.length >= 2 ? await 跑('高处-菜单被顶出视口', 图.slice(0, 2).map(n => n.id)) : null;
  结果.读数.低处 = A;
  结果.读数.高处 = B;
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  try { 记(`⭐ 收尾坐标偏差：${JSON.stringify(await 核对坐标(page))}`); } catch {}
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEJ3.json ===');
}
