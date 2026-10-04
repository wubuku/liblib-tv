// Batch EM-4：二维平移，把最后两个「卡在画面右边」的节点弄进视口。
//   EM-3 只做了纵向平移（dir 写死 -1），音频节点和右侧文本节点的控件跑到
//   x=1448~1636，超出 1440 的视口宽度 ⇒ 悬停点仍在视口外。
//   本轮按「节点左上角挪到 (200,150)」算二维位移，并在干净点里挑**行程够用**的起点。
// ⭐ 守卫区分「真的被移动」和「没渲染」——后者是 React Flow 只渲染视口内节点的正常现象。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEM4.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 待测 = [
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
      const k = 'T|' + t + '|' + Math.round(r.left); if (已.has(k)) continue; 已.add(k);
      出.push({ 文本: t.slice(0, 60), Tip: true, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }); continue;
    }
    if (t && t.length <= 16 && r.height < 60 && r.width < 300) {
      const k = 'N|' + t + '|' + Math.round(r.left); if (已.has(k)) continue; 已.add(k);
      出.push({ 文本: t, Tip: false, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
    }
  }
  return 出;
});

const 指针在否 = (page, 中心) => page.evaluate((p) => {
  const chain = [...document.querySelectorAll(':hover')];
  const 在视口内 = p[0] >= 0 && p[1] >= 0 && p[0] <= innerWidth && p[1] <= innerHeight;
  if (!chain.length) return { 在视口内, 命中: false, 链尾: '(空)' };
  const 顶 = chain[chain.length - 1];
  const 小件 = chain.find(e => { const r = e.getBoundingClientRect(); return r.width >= 8 && r.width <= 60 && r.height >= 8 && r.height <= 60; });
  const r = 小件 ? 小件.getBoundingClientRect() : null;
  return {
    在视口内, 命中: !!小件,
    链尾: 顶.tagName + '.' + String(顶.className).slice(0, 40),
    命中框: r ? [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] : null,
    命中svg: 小件 ? ([...小件.querySelectorAll('path')].map(p => (p.getAttribute('d') || '').slice(0, 28))[0] || '') : '',
  };
}, 中心);

// ⭐ 找干净起点，并按需要的位移方向算「够不够走」
const 找起点 = (page, dx, dy) => page.evaluate((d) => {
  const 好 = [];
  for (let y = 130; y <= 690; y += 20) {
    for (let x = 130; x <= 1310; x += 20) {
      const e = document.elementFromPoint(x, y);
      if (!e) continue;
      if (e.closest('.react-flow__node')) continue;
      if (e.closest('button,[role="button"],input,textarea,select,a')) continue;
      const r = e.getBoundingClientRect();
      if (r.width < innerWidth && r.height < innerHeight) continue;
      if (!/react-flow/i.test(String(e.className)) && !/canvas/i.test(String(e.className))) continue;
      let 净 = 0;
      for (let a = -40; a <= 40; a += 20) for (let b = -40; b <= 40; b += 20) {
        const p = document.elementFromPoint(x + b, y + a);
        if (p && !p.closest('.react-flow__node') && !p.closest('button,[role="button"]')) 净++;
      }
      // 沿需要的方向能走多远
      const 走X = d.dx < 0 ? x - 10 : (1310 - x);
      const 走Y = d.dy < 0 ? y - 10 : (690 - y);
      const 够 = Math.min(走X / Math.max(1, Math.abs(d.dx)), 走Y / Math.max(1, Math.abs(d.dy)));
      好.push({ x, y, 净, 走X, 走Y, 够 });
    }
  }
  if (!好.length) return null;
  好.sort((a, b) => (b.够 - a.够) || (b.净 - a.净));
  return 好[0];
}, { dx, dy });

const 守卫 = async (page, 段) => {
  const 现 = await 读全部坐标(page);
  const 真动 = Object.keys(坐标).filter(id => 现[id] && (Math.abs(现[id][0] - 坐标[id][0]) > 1.5 || Math.abs(现[id][1] - 坐标[id][1]) > 1.5));
  const 未渲染 = BASE.filter(id => !现[id]);
  记(`　　${段}：已渲染 ${Object.keys(现).length}/11，未渲染 ${未渲染.length}，**真的被移动 ${真动.length}** ${JSON.stringify(真动)}`);
  if (真动.length) throw new Error('平移真的移动了节点，立即中止');
  return { 现, 真动, 未渲染 };
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
  await page.waitForTimeout(3200);
  await 守卫(page, '开局');

  const 逐节点 = [];
  for (const t of 待测) {
    记(`\n———— ${t.id} ${t.名} ————`);
    // 目标：把节点左上角挪到 (200, 150)，这样右侧 + 下方的卡片也能进视口
    for (let 段 = 0; 段 < 6; 段++) {
      const 框 = await page.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; }, t.id);
      if (!框) { 记('　节点不在 DOM'); break; }
      const dx = 200 - 框[0], dy = 150 - 框[1];
      if (Math.abs(dx) < 12 && Math.abs(dy) < 12) { 记(`　　第 ${段} 段：已到位 ${JSON.stringify(框)}`); break; }
      const 起 = await 找起点(page, dx, dy);
      if (!起) { 记('　找不到干净起点，停'); break; }
      const 本X = Math.round(Math.max(-起.走X, Math.min(起.走X, dx)));
      const 本Y = Math.round(Math.max(-起.走Y, Math.min(起.走Y, dy)));
      if (Math.abs(本X) < 10 && Math.abs(本Y) < 10) { 记(`　　行程不足（需要 ${dx},${dy}，可走 ${起.走X},${起.走Y}），停`); break; }
      记(`　　第 ${段 + 1} 段：从 (${起.x},${起.y}) 中键拖 (${本X},${本Y})｜需要 (${dx},${dy})｜干净度 ${起.净}`);
      await page.mouse.move(起.x, 起.y);
      await page.mouse.down({ button: 'middle' });
      for (let i = 1; i <= 12; i++) await page.mouse.move(起.x + 本X * i / 12, 起.y + 本Y * i / 12);
      await page.mouse.up({ button: 'middle' });
      await page.waitForTimeout(1700);
      await 守卫(page, '本段后');
    }
    const 终框 = await page.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; }, t.id);
    记(`　平移后视口框 ${JSON.stringify(终框)}`);
    await page.screenshot({ path: EVID + `em4-${t.id}-平移后.png` });

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
    if (!落点) { 记('　⛔ 无安全落点'); 逐节点.push({ ...t, 状态: '无落点' }); continue; }
    await page.mouse.click(落点[0], 落点[1]);
    await page.waitForTimeout(2600);
    const 选中 = await page.evaluate((id) => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')), t.id);
    if (选中.length !== 1 || 选中[0] !== t.id) { 记(`　⛔ 点中了 ${JSON.stringify(选中)}`); 逐节点.push({ ...t, 状态: '落点被抢', 实际选中: 选中 }); await page.keyboard.press('Escape'); await page.waitForTimeout(1000); continue; }
    记('　✅ 选中正确');

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
          svg: [...e.querySelectorAll('path')].map(p => (p.getAttribute('d') || '').slice(0, 28))[0] || '',
        });
      }
      return 出;
    }, t.id);
    记(`　三处全空的控件 ${无名.length} 个`);

    const 逐枚 = [];
    for (const b of 无名) {
      if (!b.视口内) { 记(`　　box=${JSON.stringify(b.box)} ⛔ 仍不在视口内`); 逐枚.push({ box: b.box, 跳过: '视口外' }); continue; }
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
      await page.screenshot({ path: EVID + `em4-${t.id}-${b.box[0]}x${b.box[1]}.png` });
      逐枚.push({ box: b.box, svg: b.svg, 指针命中: 针.命中, 命中框: 针.命中框, 命中svg: 针.命中svg, 气泡: 新.map(n => n.文本) });
    }
    const 有效 = 逐枚.filter(p => !p.跳过);
    if (有效.length && 有效.every(p => !p.气泡 || p.气泡.length === 0)) 记('　　⛔ 判据自检：本节点无一读出气泡，阴性结果不作数');
    await page.screenshot({ path: EVID + `em4-${t.id}-展开.png` });
    逐节点.push({ id: t.id, 名: t.名, 状态: '已普查', 无名数: 无名.length, 逐枚 });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1200);
  }
  结果.读数.逐节点 = 逐节点;
  记('\n✅ 二维平移补测完毕');
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  try {
    记('⏳ ⌘0 复位 + 静置 15s（三铁律③）…');
    await page.keyboard.press('Meta+0');
    await page.waitForTimeout(15000);
    记(`⭐ 复位后坐标：${JSON.stringify(await 读全部坐标(page))}`);
    记(`⭐ 收尾核对（未渲染的节点不计入）：${JSON.stringify((await 读全部坐标(page)) && [])}`);
    const 现 = await 读全部坐标(page);
    const 真动 = Object.keys(坐标).filter(id => 现[id] && (Math.abs(现[id][0] - 坐标[id][0]) > 1.5 || Math.abs(现[id][1] - 坐标[id][1]) > 1.5));
    记(`⭐ 真的被移动：${真动.length} 个 ${JSON.stringify(真动)}`);
    结果.读数.真动 = 真动;
  } catch (e) { console.error(e); }
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEM4.json ===');
}
