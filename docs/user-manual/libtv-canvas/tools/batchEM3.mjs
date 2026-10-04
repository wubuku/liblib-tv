// Batch EM-3：用**平移**把边缘节点的卡片弄进视口，补完最后三个节点。
//   EM-2 试了「缩到 50%」——缩放以**视口中心**为锚点，
//   画布内容从中心向外展开，右下角的节点只会离中心更远，**没用**。
//
// 本轮做法：
//   ① 程序化找一块**确属空白画布**的起点（elementFromPoint 不落在任何 react-flow__node 里）
//   ② 从那里拖到「把目标节点挪进视口中央」所需的位置（不按 Shift —— 按了会变框选）
//   ③ 落点/起点都逐点复核，**绝不在节点上起手**
// ⛔ 只做视图平移，不碰任何节点的画布坐标，末尾仍用「核对坐标」复核。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEM3.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 待测 = [
  { id: 't-2AK3Ukyxj3', 名: '文本节点 1（左下）' },
  { id: 'a-GgqvrVz0pw', 名: '音频节点 1（右下）' },
  { id: 't-UtVx3lZmrV', 名: '文本节点 1（右）' },
];

const 读气泡 = (page) => page.evaluate(() => {
  const 出 = [], 已 = new Set();
  for (const e of document.querySelectorAll('body *')) {
    const cls = (e.className || '').toString();
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    const r = e.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (/Tooltip|tooltip/.test(cls)) {
      const k = 'T|' + t + '|' + Math.round(r.left);
      if (已.has(k)) continue; 已.add(k);
      出.push({ 文本: t.slice(0, 60), Tip: true, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }); continue;
    }
    if (t && t.length <= 16 && r.height < 60 && r.width < 300) {
      const k = 'N|' + t + '|' + Math.round(r.left);
      if (已.has(k)) continue; 已.add(k);
      出.push({ 文本: t, Tip: false, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
    }
  }
  return 出;
});

const 指针在否 = (page, 中心) => page.evaluate((p) => {
  const chain = [...document.querySelectorAll(':hover')];
  const 在视口内 = p[0] >= 0 && p[1] >= 0 && p[0] <= innerWidth && p[1] <= innerHeight;
  if (!chain.length) return { 在视口内, 命中: false, 链长: 0, 链尾: '(空)' };
  const 顶 = chain[chain.length - 1];
  const 小件 = chain.find(e => { const r = e.getBoundingClientRect(); return r.width >= 8 && r.width <= 60 && r.height >= 8 && r.height <= 60; });
  const r = 小件 ? 小件.getBoundingClientRect() : null;
  return {
    在视口内, 命中: !!小件, 链长: chain.length,
    链尾: 顶.tagName + '.' + String(顶.className).slice(0, 40),
    命中框: r ? [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] : null,
    命中svg: 小件 ? ([...小件.querySelectorAll('path')].map(p => (p.getAttribute('d') || '').slice(0, 28))[0] || '') : '',
  };
}, 中心);

// ⭐ 找一块空白画布：不在任何节点 / 面板 / 底栏里的点。
//    dir=-1 表示要把内容往上挪 ⇒ 起点必须选**最靠下**的干净点（否则行程不够，
//    我第一版就是死在这儿：把 dy 从 -846 钳成了 -10，拖了 10 像素就松手）。
const 找空白 = (page, dir) => page.evaluate((d) => {
  const 好 = [];
  for (let y = 120; y <= 700; y += 20) {
    for (let x = 120; x <= 1320; x += 20) {
      const e = document.elementFromPoint(x, y);
      if (!e) continue;
      if (e.closest('.react-flow__node')) continue;
      if (e.closest('button,[role="button"],input,textarea,select,a')) continue;
      const r = e.getBoundingClientRect();
      if (r.width < innerWidth && r.height < innerHeight) continue;  // 排除铺满的根容器
      if (!/react-flow/i.test(String(e.className)) && !/canvas/i.test(String(e.className))) continue;
      let 净 = 0; // 周围 40px 内有多少空白
      for (let dy = -40; dy <= 40; dy += 20) for (let dx = -40; dx <= 40; dx += 20) {
        const p = document.elementFromPoint(x + dx, y + dy);
        if (p && !p.closest('.react-flow__node') && !p.closest('button,[role="button"]')) 净++;
      }
      好.push({ x, y, 净 });
    }
  }
  if (!好.length) return null;
  const 行程 = (p) => (d < 0 ? p.y - 10 : (700 - p.y));
  好.sort((a, b) => (行程(b) - 行程(a)) || (b.净 - a.净));  // 行程优先，其次干净度
  return { ...好[0], 可走: Math.max(0, 行程(好[0])) };
}, dir);

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

  const 逐节点 = [];
  for (const t of 待测) {
    记(`\n———— ${t.id} ${t.名} ————`);
    const 前框 = await page.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; }, t.id);
    if (!前框) { 记('　节点不在 DOM'); continue; }
    记(`　平移前视口框 ${JSON.stringify(前框)}`);

    // 卡片大致从节点底部往下延伸 ~340px（实测），目标是让「节点底部 + 340」落在视口内
    const 目标底Y = 770;
    let 剩余 = 前框[1] + 前框[3] + 340 - 目标底Y;
    记(`　需要把内容上移 ${Math.round(剩余)}px`);

    // ⭐ 分段平移：一段拖不完就松手、重新找起点、再拖（一次拖不出 800px 的行程）
    for (let 段 = 0; 段 < 6 && 剩余 > 12; 段++) {
      const 空白 = await 找空白(page, -1);
      if (!空白) { 记('　　找不到干净起点，停'); break; }
      const 复核 = await page.evaluate((p) => { const e = document.elementFromPoint(p.x, p.y); return { 空白: !!e && !e.closest('.react-flow__node') && !e.closest('button,[role="button"]'), tag: e ? e.tagName + '.' + String(e.className).slice(0, 34) : 'null' }; }, 空白);
      if (!复核.空白) { 记(`　　起点 ${JSON.stringify([空白.x, 空白.y])} 不干净，停（${复核.tag}）`); break; }
      const 本段 = -Math.min(Math.round(剩余), 空白.可走);
      if (本段 > -12) { 记('　　行程不够，停'); break; }
      记(`　　第 ${段 + 1} 段：从 (${空白.x},${空白.y}) **中键**拖 ${本段}px（可走 ${空白.可走}px，干净度 ${空白.净}）`);
      // ⭐ 裸左键拖**拖不动画布**（手册实测只挪 +16.3px），必须中键拖
      await page.mouse.move(空白.x, 空白.y);
      await page.mouse.down({ button: 'middle' });
      for (let i = 1; i <= 12; i++) await page.mouse.move(空白.x, 空白.y + (本段 * i / 12));
      await page.mouse.up({ button: 'middle' });
      await page.waitForTimeout(1600);
      剩余 += 本段;
      // ⭐ 守卫要区分「真的被移动」和「根本没渲染」——
      //   React Flow 只渲染视口内的节点，平移后被推出视口的节点不在 DOM 里，
      //   拿「读不到」当「坐标变了」会误报（EM-3 第一版就误报 4 个）。
      const 现 = await 读全部坐标(page);
      const 真动 = Object.keys(坐标).filter(id => 现[id] && (Math.abs(现[id][0] - 坐标[id][0]) > 1.5 || Math.abs(现[id][1] - 坐标[id][1]) > 1.5));
      const 未渲染 = BASE.filter(id => !现[id]);
      记(`　　本段后：已渲染 ${Object.keys(现).length}/11，未渲染 ${未渲染.length} 个（${未渲染.join(',') || '无'}），真的被移动 ${真动.length} 个`);
      if (真动.length) { 记(`　　⛔ 真的移动了 ${JSON.stringify(真动)}，立即停止`); throw new Error('平移动了节点，立即中止'); }
    }
    const 后框 = await page.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; }, t.id);
    记(`　平移后视口框 ${JSON.stringify(后框)}｜已渲染节点 ${Object.keys(await 读全部坐标(page)).length}/11`);
    await page.screenshot({ path: EVID + `em3-${t.id}-平移后.png` });

    const 落点 = await page.evaluate((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!n) return null;
      const r = n.getBoundingClientRect();
      for (let i = 1; i < 10; i++) for (let j = 1; j < 10; j++) {
        const x = Math.round(r.left + r.width * i / 10), y = Math.round(r.top + r.height * j / 10);
        if (x < 5 || y < 5 || x > 1435 || y > 805) continue;
        const e = document.elementFromPoint(x, y);
        const g = e && e.closest('.react-flow__node');
        if (g && g.getAttribute('data-id') === id) return [x, y];
      }
      return null;
    }, t.id);
    if (!落点) { 记('　⛔ 找不到安全落点'); 逐节点.push({ ...t, 状态: '无落点' }); continue; }
    await page.mouse.click(落点[0], 落点[1]);
    await page.waitForTimeout(2600);
    const 选中 = await page.evaluate((id) => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')), t.id);
    if (选中.length !== 1 || 选中[0] !== t.id) { 记(`　⛔ 点中了 ${JSON.stringify(选中)}`); 逐节点.push({ ...t, 状态: '落点被抢', 实际选中: 选中 }); await page.keyboard.press('Escape'); await page.waitForTimeout(1000); continue; }

    const 无名 = await page.evaluate((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!n) return [];
      const 出 = [], 集 = new Set();
      for (const e of n.querySelectorAll('button,[role="button"],div[class*="size-7"],div[class*="size-8"]')) {
        if (集.has(e)) continue;
        const r = e.getBoundingClientRect();
        if (r.width < 8 || r.width > 400 || r.height < 8 || r.height > 90) continue;
        集.add(e);
        const attrs = {}; for (const a of e.attributes) attrs[a.name] = a.value;
        const cx = Math.round(r.left + r.width / 2), cy = Math.round(r.top + r.height / 2);
        if ((e.innerText || '').trim() || attrs['aria-label'] || attrs.title) continue;
        出.push({
          box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 中心: [cx, cy],
          视口内: cx >= 0 && cy >= 0 && cx <= innerWidth && cy <= innerHeight,
          背景: getComputedStyle(e).backgroundColor,
          svg: [...e.querySelectorAll('path')].map(p => (p.getAttribute('d') || '').slice(0, 28))[0] || '',
        });
      }
      return 出;
    }, t.id);
    记(`　三处全空的控件 ${无名.length} 个`);

    const 逐枚 = [];
    for (const b of 无名) {
      if (!b.视口内) { 记(`　　box=${JSON.stringify(b.box)} ⛔ 仍不在视口内，跳过`); continue; }
      await page.mouse.move(20, 800);
      await page.waitForTimeout(1100);
      const 前 = await 读气泡(page);
      for (const d of [[-5, -5], [5, 5], [0, 0], [2, -2], [0, 0]]) { await page.mouse.move(b.中心[0] + d[0], b.中心[1] + d[1]); await page.waitForTimeout(380); }
      await page.waitForTimeout(3200);
      const 后 = await 读气泡(page);
      const 新 = 后.filter(y => !前.some(x => x.文本 === y.文本 && Math.abs(x.box[0] - y.box[0]) < 4));
      const 针 = await 指针在否(page, b.中心);
      记(`　　box=${JSON.stringify(b.box)} svg=${b.svg || '（无）'}`);
      记(`　　　:hover ${针.命中 ? `✅命中 ${JSON.stringify(针.命中框)} svg=${针.命中svg}` : '⛔未命中'}｜气泡 ${新.length ? JSON.stringify(新.map(n => n.文本)) : '⛔ 0 个'}`);
      await page.screenshot({ path: EVID + `em3-${t.id}-${b.box[0]}x${b.box[1]}.png` });
      逐枚.push({ box: b.box, svg: b.svg, 指针命中: 针.命中, 命中框: 针.命中框, 命中svg: 针.命中svg, 气泡: 新.map(n => n.文本) });
    }
    if (逐枚.length && 逐枚.every(p => p.气泡.length === 0)) 记('　　⛔ 判据自检：本节点无一读出气泡，**阴性结果不作数**');
    await page.screenshot({ path: EVID + `em3-${t.id}-展开.png` });
    逐节点.push({ id: t.id, 名: t.名, 状态: '已普查', 无名数: 无名.length, 逐枚 });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1200);
  }
  结果.读数.逐节点 = 逐节点;
  记('\n✅ 补测完毕');
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  try {
    记('⏳ 静置 15s 后复核坐标（三铁律③）…');
    await page.waitForTimeout(15000);
    记(`⭐ 收尾坐标偏差：${JSON.stringify(await 核对坐标(page))}`);
  } catch (e) { console.error(e); }
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEM3.json ===');
}
