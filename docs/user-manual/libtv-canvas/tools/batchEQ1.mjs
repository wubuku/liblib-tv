// Batch EQ-1：收 EP 批的两个尾巴。
//   ① ⓘ 问号图标那条「新功能:」提示 —— EP 的截图里它自己冒出来了，文案没读全
//   ② 音频节点参数面板的逐项 —— EP 只拿到面板全文
//
// ⭐⭐ 本轮用 EP §120.3 找到的**正确判据**读面板：
//     `font-weight ≥ 500` 且 `cursor ≠ pointer` ⇒ **分组标题**（不可点）
//     否则 ⇒ **可点项**
//   之前三轮用「看起来像项」的白名单，把 border-width:0 / border-radius:0 的选项全滤掉了。
// ⛔ 只读，不点任何一项。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEQ1.json';
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

const 平移到左上 = async (page, id) => {
  for (let 段 = 0; 段 < 6; 段++) {
    const 框 = await page.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null; const r = n.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; }, id);
    if (!框) return false;
    const dx = 200 - 框[0], dy = 150 - 框[1];
    if (Math.abs(dx) < 12 && Math.abs(dy) < 12) return true;
    const 起 = await 找起点(page, dx, dy);
    if (!起) return false;
    const 本X = Math.round(Math.max(-起.走X, Math.min(起.走X, dx)));
    const 本Y = Math.round(Math.max(-起.走Y, Math.min(起.走Y, dy)));
    if (Math.abs(本X) < 10 && Math.abs(本Y) < 10) return false;
    await page.mouse.move(起.x, 起.y);
    await page.mouse.down({ button: 'middle' });
    for (let i = 1; i <= 12; i++) await page.mouse.move(起.x + 本X * i / 12, 起.y + 本Y * i / 12);
    await page.mouse.up({ button: 'middle' });
    await page.waitForTimeout(1600);
    const 现 = await 读全部坐标(page);
    if (Object.keys(坐标).some(k => 现[k] && (Math.abs(现[k][0] - 坐标[k][0]) > 1.5 || Math.abs(现[k][1] - 坐标[k][1]) > 1.5))) throw new Error('移动了节点');
  }
  return true;
};

const 找面板 = (page) => page.evaluate(() => {
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
    if (!最佳 || +cs.zIndex > +最佳.z) 最佳 = { z: cs.zIndex, 全文: t, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }
  return 最佳;
});

// ⭐ 修正后的判据：面板内「**能承载文字的最内层盒子**」全要
//    （不用「看起来像项」的白名单），标题与项交给「字重 + 光标」区分
const 读面板项 = (page, 框) => page.evaluate((B) => {
  const [x0, y0, x1, y1] = B;
  const 出 = [], 见过 = new Set();
  for (const e of document.querySelectorAll('body *')) {
    if (e.closest('.react-flow__node') || e.closest('.react-flow__nodes')) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 16 || r.width > 400 || r.height < 14 || r.height > 200) continue;
    if (r.left < x0 - 6 || r.top < y0 - 6 || r.right > x1 + 6 || r.bottom > y1 + 6) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 16) continue;
    // 只要「没有同样文字的子元素」的 —— 即最内层承载者
    if ([...e.children].some(c => (c.innerText || '').replace(/\s+/g, ' ').trim() === t)) continue;
    const k = t + '|' + Math.round(r.left) + '|' + Math.round(r.top);
    if (见过.has(k)) continue; 见过.add(k);
    const cs = getComputedStyle(e);
    // ⭐ 标题 vs 项
    const 是标题 = +cs.fontWeight >= 500 && cs.cursor !== 'pointer';
    出.push({
      文本: t, 是标题, 角色: 是标题 ? '标题' : '可点项',
      字重: cs.fontWeight, 光标: cs.cursor,
      边框: cs.borderColor + ' ' + cs.borderWidth, 背景: cs.backgroundColor,
      白边: cs.borderColor === 'rgb(255, 255, 255)',
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
    });
  }
  出.sort((a, b) => (a.box[1] - b.box[1]) || (a.box[0] - b.box[0]));
  return 出;
}, 框);

const 读气泡 = (page) => page.evaluate(() => {
  const 出 = [], 已 = new Set();
  for (const e of document.querySelectorAll('body *')) {
    const cls = (e.className || '').toString();
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    const r = e.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (/Tooltip|tooltip/.test(cls)) {
      const k = 'T|' + t + '|' + Math.round(r.left); if (已.has(k)) continue; 已.add(k);
      出.push({ 文本: t.slice(0, 120), Tip: true, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }); continue;
    }
    if (t && t.length <= 40 && r.height < 80 && r.width < 500) {
      const k = 'N|' + t + '|' + Math.round(r.left); if (已.has(k)) continue; 已.add(k);
      出.push({ 文本: t, Tip: false, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
    }
  }
  return 出;
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

  const 选并开面板 = async (id, 名) => {
    if (!(await page.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), id))) { await page.keyboard.press('Meta+0'); await page.waitForTimeout(2500); }
    if (!(await 平移到左上(page, id))) { 记(`　${名} 平移未成功`); return null; }
    const 落点 = await page.evaluate((i) => {
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
    if (!落点) { 记(`　${名} 无安全落点`); return null; }
    await page.mouse.click(落点[0], 落点[1]);
    await page.waitForTimeout(2600);
    const 选 = await page.evaluate((i) => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')), id);
    if (选.length !== 1 || 选[0] !== id) { 记(`　${名} 点中了 ${JSON.stringify(选)}`); await page.keyboard.press('Escape'); await page.waitForTimeout(1000); return null; }
    const 下拉 = await page.evaluate((i) => {
      const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      for (const b of n.querySelectorAll('button')) {
        const x = (b.innerText || '').replace(/\s+/g, ' ').trim();
        if (!x.includes('·')) continue;
        const r = b.getBoundingClientRect();
        if (r.bottom < 0 || r.top > innerHeight) continue;
        return { 文字: x, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
      }
      return null;
    }, id);
    if (!下拉) { 记(`　${名} 没有摘要下拉`); return null; }
    await page.mouse.click(下拉.中心[0], 下拉.中心[1]);
    await page.waitForTimeout(2000);
    const 面板 = await 找面板(page);
    if (!面板) { 记(`　${名} 没找到面板`); return null; }
    return { 下拉, 面板 };
  };

  // ---- ① 音频节点参数面板的逐项
  记('\n════ 音频节点 a-THmbuJXQj4：面板逐项（修正判据）════');
  const A = await 选并开面板('a-THmbuJXQj4', '音频');
  if (A) {
    记(`　摘要「${A.下拉.文字}」｜面板 ${JSON.stringify(A.面板.box)}｜全文「${A.面板.全文}」`);
    const 项 = await 读面板项(page, A.面板.box);
    记(`　读到 ${项.length} 个（标题 ${项.filter(x => x.是标题).length} / 可点项 ${项.filter(x => !x.是标题).length}）：`);
    for (const x of 项) 记(`　　【${x.角色}】「${x.文本}」 ${x.box[2]}×${x.box[3]} 字重=${x.字重} 光标=${x.光标} 边框=${x.边框} 背景=${x.背景}${x.白边 ? ' ⭐白边' : ''}`);
    记(`　⭐ 白边（当前值）：${JSON.stringify(项.filter(x => x.白边).map(x => x.文本))}`);
    const 摘要词 = A.下拉.文字.split(/[·\s]+/).filter(Boolean);
    记(`　⭐ 摘要 ${JSON.stringify(摘要词)} 逐个在面板里找：${摘要词.map(w => `${w}=${项.some(x => x.文本 === w)}`).join(' ')}`);
    await page.screenshot({ path: EVID + 'eq1-音频-面板.png' });
    结果.读数.音频 = { 摘要: A.下拉.文字, 框: A.面板.box, 全文: A.面板.全文, 项 };
    await page.keyboard.press('Escape'); await page.waitForTimeout(1300);
    await page.keyboard.press('Escape'); await page.waitForTimeout(900);
  }

  // ---- ② 智能剪辑面板逐项
  记('\n════ 智能剪辑 v-oZNpH99MtM：面板逐项（修正判据）════');
  const B = await 选并开面板('v-oZNpH99MtM', '智能剪辑');
  if (B) {
    记(`　摘要「${B.下拉.文字}」｜面板 ${JSON.stringify(B.面板.box)}｜全文「${B.面板.全文}」`);
    const 项 = await 读面板项(page, B.面板.box);
    记(`　读到 ${项.length} 个（标题 ${项.filter(x => x.是标题).length} / 可点项 ${项.filter(x => !x.是标题).length}）：`);
    for (const x of 项) 记(`　　【${x.角色}】「${x.文本}」 ${x.box[2]}×${x.box[3]} 字重=${x.字重} 光标=${x.光标} 边框=${x.边框} 背景=${x.背景}${x.白边 ? ' ⭐白边' : ''}`);
    记(`　⭐ 白边（当前值）：${JSON.stringify(项.filter(x => x.白边).map(x => x.文本))}`);
    const 摘要词 = B.下拉.文字.split(/[·\s]+/).filter(Boolean);
    记(`　⭐ 摘要 ${JSON.stringify(摘要词)} 逐个在面板里找：${摘要词.map(w => `${w}=${项.some(x => x.文本 === w || x.文本.includes(w))}`).join(' ')}`);
    await page.screenshot({ path: EVID + 'eq1-智能剪辑-面板.png' });
    结果.读数.智能剪辑 = { 摘要: B.下拉.文字, 框: B.面板.box, 全文: B.面板.全文, 项 };
    await page.keyboard.press('Escape'); await page.waitForTimeout(1300);

    // ---- ③ ⓘ 问号图标：悬停读「新功能:」提示
    记('\n════ 视频节点「生成音频 ⓘ」的问号图标 ————');
    await 平移到左上(page, 'v-v2hlWY4Br3');
    const C = await 选并开面板('v-v2hlWY4Br3', '视频');
    if (C) {
      const 问号 = await page.evaluate((B2) => {
        const [x0, y0, x1, y1] = B2;
        const 候选 = [];
        for (const e of document.querySelectorAll('body *')) {
          const r = e.getBoundingClientRect();
          if (r.width < 8 || r.width > 30 || r.height < 8 || r.height > 30) continue;
          if (r.left < x0 || r.top < y0 || r.right > x1 || r.bottom > y1) continue;
          const cs = getComputedStyle(e);
          if (cs.cursor !== 'pointer') continue;
          const svg = e.querySelector('svg');
          候选.push({ tag: e.tagName, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], 大小: [Math.round(r.width), Math.round(r.height)], svg路径: svg ? (svg.querySelector('path')?.getAttribute('d') || '').slice(0, 30) : '', cls: String(e.className).slice(0, 50) });
        }
        return 候选;
      }, C.面板.box);
      记(`　面板内小尺寸可点图标 ${问号.length} 个：${JSON.stringify(问号)}`);
      for (const [i, q] of 问号.entries()) {
        await page.mouse.move(20, 800); await page.waitForTimeout(1000);
        const 前 = await 读气泡(page);
        await page.mouse.move(q.中心[0] - 3, q.中心[1] - 3); await page.waitForTimeout(280);
        await page.mouse.move(q.中心[0], q.中心[1]); await page.waitForTimeout(3000);
        const 后 = await 读气泡(page);
        const 新 = 后.filter(y => !前.some(x => x.文本 === y.文本 && Math.abs(x.box[0] - y.box[0]) < 4));
        记(`　　[${i}] ${q.大小.join('×')} svg=${q.svg路径} → 新出现 ${新.length} 个：${JSON.stringify(新.map(n => n.文本))}`);
        await page.screenshot({ path: EVID + `eq1-问号-${i}.png` });
        结果.读数['问号' + i] = { 图标: q, 气泡: 新.map(n => n.文本) };
      }
    }
  }
  记('\n✅ 完成（未点任何一项）');
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
  console.log('\n=== 已写 tools/batchEQ1.json ===');
}
