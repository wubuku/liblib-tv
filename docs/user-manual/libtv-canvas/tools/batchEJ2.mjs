// Batch EJ-2：EJ-1 的判据缺陷修正 —— 排列菜单**向上弹**，而我只扫了工具条下方 320px。
// 本轮：① 全视口扫，读菜单容器与三项的精确读数
//       ② 换一组**位置更低**的节点做框选，让工具条落到视口中部，拍一张菜单完整可见的干净图
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEJ2.json';
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
    return { 找到: true, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 按钮: [...c.querySelectorAll('button')].map(b => { const rb = b.getBoundingClientRect(); return { 文字: (b.innerText || '').trim().slice(0, 12) || (b.getAttribute('aria-label') || '(无名)'), box: [Math.round(rb.left), Math.round(rb.top), Math.round(rb.width), Math.round(rb.height)] }; }) };
  });

  // ⭐ 全视口扫：只要元素里有「排列」二字且在视口内，就把它连祖先链一起端出来
  const 读排列菜单 = async () => page.evaluate(() => {
    const all = [...document.querySelectorAll('body *')].filter(e => /垂直排列/.test(e.innerText || ''));
    const 可见 = all.filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
    if (!可见.length) return { 开: false };
    可见.sort((a, b) => a.getBoundingClientRect().width * a.getBoundingClientRect().height - b.getBoundingClientRect().width * b.getBoundingClientRect().height);
    const 叶 = 可见[0];
    let 宿主 = 叶;
    for (let i = 0; i < 4; i++) {
      const n = 宿主.querySelectorAll('button,li,[role="menuitem"]').length;
      if (n >= 3) break;
      宿主 = 宿主.parentElement;
      if (!宿主) break;
    }
    const 链 = [];
    let cur = 宿主;
    for (let i = 0; i < 4 && cur; i++) {
      const r = cur.getBoundingClientRect();
      链.push({ tag: cur.tagName, cls: (cur.className || '').toString().slice(0, 110), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
      cur = cur.parentElement;
    }
    return {
      开: true,
      容器: 宿主 ? (() => { const r = 宿主.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; })() : null,
      容器class: 宿主 ? (宿主.className || '').toString().slice(0, 130) : '',
      项: 宿主 ? [...宿主.querySelectorAll('button,li,[role="menuitem"]')].map(e => {
        const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
        return { 文本: (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 14), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], opacity: cs.opacity, cursor: cs.cursor, svg数: e.querySelectorAll('svg').length };
      }) : [],
      祖先链: 链,
      超出视口上沿: 宿主 ? 宿主.getBoundingClientRect().top < 0 : null,
    };
  });

  const 跑一遍 = async (标签, 选哪些) => {
    const ps = 选哪些.map(id => 节点.find(n => n.id === id)).filter(Boolean);
    const x1 = Math.min(...ps.map(p => p.box[0])) - 20, y1 = Math.min(...ps.map(p => p.box[1])) - 12;
    const x2 = Math.max(...ps.map(p => p.box[0] + p.box[2])) + 20, y2 = Math.max(...ps.map(p => p.box[1] + p.box[3])) + 12;
    await page.mouse.click(1400, 848); await page.waitForTimeout(700);
    await page.mouse.move(x1, y1); await page.mouse.down();
    await page.mouse.move((x1 + x2) / 2, (y1 + y2) / 2, { steps: 10 });
    await page.mouse.move(x2, y2, { steps: 10 });
    await page.waitForTimeout(350); await page.mouse.up();
    await page.mouse.move(1400, 848); await page.waitForTimeout(1800);
    const 选 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
    const 条 = await 找工具条();
    记(`\n【${标签}】选区 ${JSON.stringify(选)}；工具条 ${条.找到 ? JSON.stringify(条.box) : '无'}`);
    if (!条.找到) return;
    const 最左 = 条.按钮[0];
    await page.mouse.click(Math.round(最左.box[0] + 最左.box[2] / 2), Math.round(最左.box[1] + 最左.box[3] / 2));
    await page.waitForTimeout(1600);
    const 菜单 = await 读排列菜单();
    记(`  菜单：开=${菜单.开} 容器=${JSON.stringify(菜单.容器)} class=${(菜单.容器class || '').slice(0, 70)}`);
    记(`  超出视口上沿=${菜单.超出视口上沿}`);
    for (const it of (菜单.项 || [])) 记(`  　项「${it.文本}」 box=${JSON.stringify(it.box)} opacity=${it.opacity} cursor=${it.cursor} svg=${it.svg数}`);
    记(`  祖先链：${JSON.stringify((菜单.祖先链 || []).map(c => c.tag + '.' + c.cls.slice(0, 44)))}`);
    await page.screenshot({ path: EVID + `ej2-${标签}.png` });
    if (菜单.容器 && !菜单.超出视口上沿) {
      const c = 菜单.容器;
      await page.screenshot({ path: EVID + `ej2-${标签}-裁图.png`, clip: { x: Math.max(0, c[0] - 300), y: Math.max(0, c[1] - 40), width: 660, height: (c[1] + c[3]) - Math.max(0, c[1] - 40) + 60 } });
      记('  ✅ 已拍裁图');
    }
    await page.keyboard.press('Escape');
    await page.waitForTimeout(900);
    return 菜单;
  };

  // ① 高处那组（菜单会被顶出视口）
  const 菜单A = await 跑一遍('高处-菜单被顶出视口', ['i-9nlG6HdjK2', 'i-sODTbgLUm1']);
  // ② 低处那组：底部两个节点（文本节点 + 音频节点），让工具条落到视口中部
  const 低 = 节点.filter(n => n.box[1] > 450);
  记(`\n位置靠下的节点：${JSON.stringify(低.map(n => [n.类型, n.id, n.box]))}`);
  const 菜单B = 低.length >= 2 ? await 跑一遍('低处-菜单完整', 低.slice(0, 2).map(n => n.id)) : null;

  结果.读数.菜单A = 菜单A;
  结果.读数.菜单B = 菜单B;
  落盘(结果);
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  try { 记(`⭐ 收尾坐标偏差：${JSON.stringify(await 核对坐标(page))}`); } catch {}
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEJ2.json ===');
}
