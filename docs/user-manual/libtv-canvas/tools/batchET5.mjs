// Batch ET-5：出两张干净配图，顺带把两处「怎么摆进视口」的问题解决掉。
//
//   需要重拍的原因：
//     · M-143 上的音量数值框是 `1.0`，而 ET-3/ET-4 实测当前值是 `6.2`
//       ⇒ 旧图**名不副实**，必须换掉。
//     · 音频大编辑器 800 宽，选中节点时它**左边被挤出视口**（ET-3/ET-4 的图里
//       「语速/声调/音量」三个标签都被切掉，只剩滑杆和数值框）。
//   ⭐ 平移量用画布坐标驱动：把目标面板的**屏幕 left** 挪到 x=70，
//      需要的位移 = 70 - 现 left，然后用**中键拖**走这段位移。
//
//   两张图：
//     M-366 音频节点「高级设置」完整三行（标签 + 滑杆 + 数值框 1.00 / 0 / 6.2）
//     M-367 视频参数面板，并把 ⓘ 的气泡「为生成的视频添加音频内容」一起框进来
//
// ⛔ 只读：不动任何滑块、不改任何数值。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchET5.json';
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

/** 中键拖移画布，走完指定位移；每段后核对节点没被移动 */
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

  // ① 音频：把大编辑器完整摆进视口，再拍「高级设置」三行
  记('\n════ ① 音频节点：把大编辑器摆进视口 ════');
  await page.keyboard.press('Meta+0'); await page.waitForTimeout(2000);
  let 落 = await 安全点(page, 'a-THmbuJXQj4');
  if (落) {
    await page.mouse.click(落[0], 落[1]);
    await page.waitForTimeout(2500);
    const 选 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
    记(`　选中 ${JSON.stringify(选)}`);
    for (let 段 = 0; 段 < 5; 段++) {
      const 编辑器 = await page.evaluate(() => {
        const 候选 = [...document.querySelectorAll('body *')].filter(e => (e.innerText || '').includes('高级设置') && (e.innerText || '').includes('语速'));
        if (!候选.length) return null;
        候选.sort((a, b) => (a.innerText || '').length - (b.innerText || '').length);
        const r = 候选[0].getBoundingClientRect();
        return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
      });
      记(`　大编辑器 box ${JSON.stringify(编辑器)}`);
      if (!编辑器) break;
      if (编辑器[0] >= 60 && 编辑器[0] + 编辑器[2] <= 1400) break;
      await 拖移(page, 70 - 编辑器[0], 0);
    }
    const 最终 = await page.evaluate(() => {
      const 候选 = [...document.querySelectorAll('body *')].filter(e => (e.innerText || '').includes('高级设置') && (e.innerText || '').includes('语速'));
      候选.sort((a, b) => (a.innerText || '').length - (b.innerText || '').length);
      const r = 候选[0].getBoundingClientRect();
      return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
    });
    记(`　⭐ 最终 box ${JSON.stringify(最终)}`);
    const 读数 = await page.evaluate(() => [...document.querySelectorAll('[role="slider"]')].map(s => {
      const r = s.getBoundingClientRect();
      let 标签 = null, n = s.parentElement;
      for (let i = 0; i < 6 && n; i++) { const t = (n.innerText || '').replace(/\s+/g, ' ').trim(); if (t && t.length <= 8 && !/^[\d.]+$/.test(t) && t !== 's') { 标签 = t; break; } n = n.parentElement; }
      const 框 = [...document.querySelectorAll('div')].find(d => { const q = d.getBoundingClientRect(); return Math.abs(q.top - r.top) < 6 && q.left > r.left && q.left < r.left + 400 && /\d/.test(d.innerText || '') && (d.innerText || '').trim().length <= 6; });
      return { 标签, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], aria: [s.getAttribute('aria-valuemin'), s.getAttribute('aria-valuemax'), s.getAttribute('aria-valuenow')], 框文字: 框 ? (框.innerText || '').trim() : null, 轨: (() => { const t = s.closest('[class*="Slider-root"]') || s.parentElement; const q = t.getBoundingClientRect(); return [Math.round(q.left), Math.round(q.top), Math.round(q.width), Math.round(q.height)]; })() };
    }));
    for (const s of 读数) 记(`　　${s.标签}：aria=[${s.aria.join(' ~ ')}] now=${s.aria[2]}｜数值框「${s.框文字}」｜手柄中心 ${JSON.stringify(s.中心)} 轨道 ${JSON.stringify(s.轨)}｜位置比例=${(((s.中心[0] - s.轨[0]) / Math.max(1, s.轨[2]) * 100).toFixed(1))}%`);
    结果.读数.音频 = 读数;
    await page.mouse.move(1380, 790); await page.waitForTimeout(1200);
    await page.screenshot({ path: EVID + 'et5-音频-全景.png' });
  }

  // ② 视频参数面板 + ⓘ 气泡
  记('\n════ ② 视频参数面板：带上 ⓘ 的气泡 ════');
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  await page.keyboard.press('Meta+0'); await page.waitForTimeout(2200);
  落 = await 安全点(page, 'v-v2hlWY4Br3');
  if (落) {
    await page.mouse.click(落[0], 落[1]);
    await page.waitForTimeout(2500);
    const 下拉 = await page.evaluate((i) => {
      const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      for (const b of n.querySelectorAll('button')) { const x = (b.innerText || '').replace(/\s+/g, ' ').trim(); if (!x.includes('·')) continue; const r = b.getBoundingClientRect(); if (r.bottom < 0 || r.top > innerHeight) continue; return { 文字: x, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] }; }
      return null;
    }, 'v-v2hlWY4Br3');
    记(`　摘要下拉 ${JSON.stringify(下拉 && 下拉.文字)}`);
    if (下拉) {
      await page.mouse.click(下拉.中心[0], 下拉.中心[1]);
      await page.waitForTimeout(2300);
      const 面板 = await page.evaluate(() => {
        let 最佳 = null;
        for (const e of document.querySelectorAll('body *')) {
          if (e.closest('.react-flow__node') || e.closest('.react-flow__nodes') || e.closest('.react-flow__pane')) continue;
          const cs = getComputedStyle(e);
          if (cs.position !== 'absolute' && cs.position !== 'fixed') continue;
          if (+cs.zIndex < 200) continue;
          const r = e.getBoundingClientRect();
          if (r.width < 140 || r.height < 100) continue;
          const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
          if (t.length < 3) continue;
          if (!最佳 || +cs.zIndex > +最佳.z) 最佳 = { z: cs.zIndex, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
        }
        return 最佳;
      });
      记(`　面板 box ${JSON.stringify(面板 && 面板.box)}`);
      // 把面板整体挪到 x=70 附近，好完整入镜
      for (let 段 = 0; 段 < 4; 段++) {
        if (!面板) break;
        if (面板.box[0] >= 40) break;
        await 拖移(page, 40 - 面板.box[0], 0);
        const 再 = await page.evaluate(() => {
          let 最佳 = null;
          for (const e of document.querySelectorAll('body *')) {
            if (e.closest('.react-flow__node') || e.closest('.react-flow__nodes') || e.closest('.react-flow__pane')) continue;
            const cs = getComputedStyle(e);
            if (cs.position !== 'absolute' && cs.position !== 'fixed') continue;
            if (+cs.zIndex < 200) continue;
            const r = e.getBoundingClientRect();
            if (r.width < 140 || r.height < 100) continue;
            const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
            if (t.length < 3) continue;
            if (!最佳 || +cs.zIndex > +最佳.z) 最佳 = { z: cs.zIndex, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
          }
          return 最佳;
        });
        if (!再) break;
        面板 = 再;
      }
      记(`　⭐ 平移后面板 box ${JSON.stringify(面板 && 面板.box)}`);
      const 问号 = await page.evaluate(() => [...document.querySelectorAll('.cursor-help')].filter(e => (e.parentElement ? (e.parentElement.innerText || '').trim() : '') === '生成音频').map(e => { const r = e.getBoundingClientRect(); return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)]; }));
      记(`　ⓘ 中心 ${JSON.stringify(问号)}`);
      if (问号.length) {
        await page.mouse.move(问号[0][0] - 40, 问号[0][1] - 40); await page.waitForTimeout(600);
        await page.mouse.move(问号[0][0], 问号[0][1]); await page.waitForTimeout(1600);
        const 探 = await page.evaluate((c) => { const e = document.elementFromPoint(c[0], c[1]); return e ? e.tagName + '.' + String(e.className).slice(0, 30) : null; }, 问号[0]);
        const 气泡 = await page.evaluate(() => [...document.querySelectorAll('[class*="Tooltip-tooltip"]')].map(e => { const r = e.getBoundingClientRect(); return { 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }; }).filter(x => x.文字));
        记(`　　指针落点自证 ${JSON.stringify(探)}｜气泡 ${JSON.stringify(气泡)}`);
        结果.读数.视频气泡 = { 问号中心: 问号[0], 落点: 探, 气泡 };
        await page.screenshot({ path: EVID + 'et5-视频-面板带问号气泡.png' });
      }
      await page.keyboard.press('Escape'); await page.waitForTimeout(1300);
    }
  }

  记('\n✅ 完成（未拖滑块、未改数值）');
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
  console.log('\n=== 已写 tools/batchET5.json ===');
}
