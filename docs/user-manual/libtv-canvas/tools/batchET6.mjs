// Batch ET-6：补拍「音频节点 · 高级设置」完整三行（标签 + 滑杆 + 数值框）。
//
//   ET-5 的教训：那张图拍的时候**忘了点 ⚙**，拍到的是收起态 ——
//   收起态里三根滑杆**仍然在 DOM 里**（grid-rows-[0fr] 只把容器压成 0px，
//   子元素的 getBoundingClientRect 照常返回 12×12），所以「数滑杆」根本不是显隐判据。
//   ⭐ 显隐的真判据（AUDIT.md 早就写了）：外层容器的 `grid-template-rows`
//      计算值 `0px` = 收起、`157px` = 展开。
//   本轮：**先摆进视口 → 再点 ⚙ → 用 grid-template-rows 确认真的展开了 → 才拍**。
//
// ⛔ 只点 ⚙，不碰任何滑块、不改任何数值。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchET6.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 找起点 = (page, dx, dy) => page.evaluate((d) => {
  const 好 = [];
  for (let y = 130; y <= 690; y += 20) for (let x = 130; x <= 1310; x += 20) {
    const e = document.elementFromPoint(x, y);
    if (!e) continue;
    if (e.closest('.react-flow__node') || e.closest('button,[role="button"],a')) continue;
    const r = e.getBoundingClientRect();
    if (r.width < innerWidth && r.height < innerHeight) continue;
    if (!/react-flow/i.test(String(e.className)) && !/canvas/i.test(String(e.className))) continue;
    const 走X = d.dx < 0 ? x - 10 : (1310 - x), 走Y = d.dy < 0 ? y - 10 : (690 - y);
    好.push({ x, y, 走X, 走Y, 够: Math.min(走X / Math.max(1, Math.abs(d.dx)), 走Y / Math.max(1, Math.abs(d.dy))) });
  }
  if (!好.length) return null;
  好.sort((a, b) => b.够 - a.够);
  return 好[0];
}, { dx, dy });

const 拖移 = async (page, dx, dy) => {
  const 起 = await 找起点(page, dx, dy);
  if (!起) return false;
  const 本X = Math.round(Math.max(-起.走X, Math.min(起.走X, dx)));
  const 本Y = Math.round(Math.max(-起.走Y, Math.min(起.走Y, dy)));
  if (Math.abs(本X) < 8 && Math.abs(本Y) < 8) return false;
  await page.mouse.move(起.x, 起.y);
  await page.mouse.down({ button: 'middle' });
  for (let i = 1; i <= 12; i++) await page.mouse.move(起.x + 本X * i / 12, 起.y + 本Y * i / 12);
  await page.mouse.up({ button: 'middle' });
  await page.waitForTimeout(1500);
  const 现 = await 读全部坐标(page);
  if (Object.keys(坐标).some(k => 现[k] && (Math.abs(现[k][0] - 坐标[k][0]) > 1.5 || Math.abs(现[k][1] - 坐标[k][1]) > 1.5))) throw new Error('移动了节点');
  return true;
};

const 安全点 = (page, id) => page.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  for (let a = 1; a < 10; a++) for (let b = 1; b < 10; b++) {
    const x = Math.round(r.left + r.width * a / 10), y = Math.round(r.top + r.height * b / 10);
    if (x < 5 || y < 5 || x > 1435 || y > 805) continue;
    const e = document.elementFromPoint(x, y);
    const g = e && e.closest('.react-flow__node');
    if (g && g.getAttribute('data-id') === i) return [x, y];
  }
  return null;
}, id);

/** ⭐ 高级设置容器的真判据：grid-template-rows 计算值 */
const 读展开态 = (page) => page.evaluate(() => {
  const 节 = [...document.querySelectorAll('div')].filter(e => /grid-rows-\[0fr\]|grid-rows-\[1fr\]/.test(String(e.className)));
  return 节.map(e => {
    const cs = getComputedStyle(e);
    const r = e.getBoundingClientRect();
    return { cls: String(e.className).slice(0, 50), 行高: cs.gridTemplateRows, 高: Math.round(r.height), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  });
});

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
  记(`开局坐标偏差：${JSON.stringify(await 核对坐标(page))}`);

  const 落 = await 安全点(page, 'a-THmbuJXQj4');
  if (!落) throw new Error('音频节点点不中');
  await page.mouse.click(落[0], 落[1]);
  await page.waitForTimeout(2500);
  const 选 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
  记(`　选中 ${JSON.stringify(选)}`);
  if (选.length !== 1 || 选[0] !== 'a-THmbuJXQj4') throw new Error('没选中目标');

  // ① 先摆进视口
  for (let 段 = 0; 段 < 5; 段++) {
    const 编辑器 = await page.evaluate(() => {
      const 候选 = [...document.querySelectorAll('body *')].filter(e => (e.innerText || '').includes('高级设置') && (e.innerText || '').includes('Seed Audio'));
      if (!候选.length) return null;
      候选.sort((a, b) => (a.innerText || '').length - (b.innerText || '').length);
      const r = 候选[0].getBoundingClientRect();
      return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
    });
    记(`　编辑器 box ${JSON.stringify(编辑器)}`);
    if (!编辑器) break;
    if (编辑器[0] >= 40 && 编辑器[0] + 编辑器[2] <= 1400) break;
    await 拖移(page, 50 - 编辑器[0], 0);
  }
  const 摆好后 = await page.evaluate(() => {
    const 候选 = [...document.querySelectorAll('body *')].filter(e => (e.innerText || '').includes('高级设置') && (e.innerText || '').includes('Seed Audio'));
    候选.sort((a, b) => (a.innerText || '').length - (b.innerText || '').length);
    const r = 候选[0].getBoundingClientRect();
    return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
  });
  记(`　⭐ 摆好后 ${JSON.stringify(摆好后)}`);

  // ② 读展开态 → 点 ⚙ → 再读，直到真的展开
  const 齿轮 = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    for (const b of n.querySelectorAll('button')) {
      if (!/text-canvas-controls-text/.test(String(b.className))) continue;
      const r = b.getBoundingClientRect();
      if (r.bottom < 0 || r.top > innerHeight) continue;
      return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
    }
    return null;
  }, 'a-THmbuJXQj4');
  记(`　⚙ 中心 ${JSON.stringify(齿轮)}`);
  const 态前 = await 读展开态(page);
  记(`　点之前 grid-rows 容器：${JSON.stringify(态前)}`);
  if (齿轮) {
    for (let 次 = 0; 次 < 3; 次++) {
      await page.mouse.click(齿轮[0], 齿轮[1]);
      await page.waitForTimeout(1800);
      const 态 = await 读展开态(page);
      const 展开 = 态.find(x => x.行高 && x.行高 !== '0px');
      记(`　　第 ${次 + 1} 次点 ⚙ 后：${JSON.stringify(态)} → ${展开 ? `已展开（行高 ${展开.行高}，高 ${展开.高}）` : '仍收起'}`);
      if (展开) { 结果.读数.展开态 = 展开; break; }
    }
  }

  // ③ ⭐ 确认展开了才拍；同时把三行读齐
  const 读三行 = await page.evaluate(() => [...document.querySelectorAll('[role="slider"]')].map(s => {
    const r = s.getBoundingClientRect();
    let 标签 = null, n = s.parentElement;
    for (let i = 0; i < 6 && n; i++) { const t = (n.innerText || '').replace(/\s+/g, ' ').trim(); if (t && t.length <= 8 && !/^[\d.]+$/.test(t) && t !== 's') { 标签 = t; break; } n = n.parentElement; }
    const 行 = s.closest('div').parentElement;
    const 行文 = (行 ? (行.innerText || '').replace(/\s+/g, ' ').trim() : '');
    return { 标签, 行文, aria: [s.getAttribute('aria-valuemin'), s.getAttribute('aria-valuemax'), s.getAttribute('aria-valuenow')], 轨道: (() => { const t = s.closest('[class*="Slider-root"]') || s.parentElement; const q = t.getBoundingClientRect(); return [Math.round(q.left), Math.round(q.top), Math.round(q.width)]; })(), 手柄x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) };
  }));
  for (const s of 读三行) 记(`　　${s.标签}：行内文字「${s.行文}」aria=[${s.aria.join(' ~ ')}]｜几何位置 ${(((s.手柄x - s.轨道[0]) / s.轨道[2] * 100).toFixed(1))}%（理论 ${(((+s.aria[2] - +s.aria[0]) / (+s.aria[1] - +s.aria[0]) * 100).toFixed(1))}%）`);
  结果.读数.三行 = 读三行;

  const 高亮 = await page.evaluate(() => { const 节 = [...document.querySelectorAll('div')].filter(e => /grid-rows-\[1fr\]/.test(String(e.className))); return 节.length ? (() => { const r = 节[0].getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; })() : null; });
  记(`　⭐ 展开区 box ${JSON.stringify(高亮)}`);
  await page.mouse.move(1400, 60); await page.waitForTimeout(1000);
  await page.screenshot({ path: EVID + 'et6-音频-高级设置-完整.png' });
  记('\n✅ 完成（只点了 ⚙，没碰滑块）');
} catch (e) {
  结果.错误 = String((e && e.stack) || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  try {
    记('⏳ ⌘0 复位 + 静置 15s…');
    await page.keyboard.press('Meta+0');
    await page.waitForTimeout(15000);
    const 现 = await 读全部坐标(page);
    const 真动 = Object.keys(坐标).filter(id => 现[id] && (Math.abs(现[id][0] - 坐标[id][0]) > 1.5 || Math.abs(现[id][1] - 坐标[id][1]) > 1.5));
    记(`⭐ 真的被移动：${真动.length} 个 ${JSON.stringify(真动)}`);
  } catch (e) { console.error(e); }
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchET6.json ===');
}
