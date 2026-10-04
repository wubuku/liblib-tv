// Batch EM-2：收尾 EM-1 里**作废**的那部分，并换掉一个弱判据。
//
// ⛔ EM-1 的两个坑：
//   ① 卡片溢出视口时，控件中心的 y/x 跑到 810 之外，
//      `elementFromPoint` 返回 null、「底色前后对比」拿空串去比 ⇒ **假阳性**，
//      害得 a-GgqvrVz0pw / t-2AK3Ukyxj3 / t-UtVx3lZmrV 三个节点的阴性结果全废；
//   ② 「读 background-color 变化」证明指针在不在，**对没有悬停态的按钮无效**
//      （展开箭头 bg 恒为 rgb(38,38,38)，生成键恒为白底）。
//
// 本轮两处修正：
//   ⭐ 换用 **`document.querySelectorAll(':hover')` 链**证明指针真的在元素上
//      —— 这是浏览器自己算的，不依赖元素有没有悬停样式；
//   ⭐ 先把画布**缩到 50%**，让所有卡片都进得了视口。
//      缩放不改节点在画布坐标系里的位置，末尾仍要用「核对坐标」复核。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEM2.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

// ⭐ 要重测的：EM-1 里因视口外溢而作废的三个节点 + 视频节点那枚 15×15 徽标
const 待测 = [
  { id: 'a-GgqvrVz0pw', 名: '音频节点 1（右）' },
  { id: 't-2AK3Ukyxj3', 名: '文本节点 1（左下）' },
  { id: 't-UtVx3lZmrV', 名: '文本节点 1（右）' },
  { id: 'v-eMpqKtiLlx', 名: '视频节点 3（左，被压）' },
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

// ⭐ 指针是否真的在这个元素上：用浏览器自己的 :hover 链判定
const 指针在否 = (page, 中心) => page.evaluate((p) => {
  const chain = [...document.querySelectorAll(':hover')];
  if (!chain.length) return { 在视口内: false, 命中: false, 链长: 0 };
  const 顶 = chain[chain.length - 1];
  const rect = { x: 0, y: 0, w: innerWidth, h: innerHeight };
  const 在视口内 = p[0] >= 0 && p[1] >= 0 && p[0] <= rect.w && p[1] <= rect.h;
  // 从 :hover 链里找是不是有个 32×32 / 28×28 / 15×15 的小方块
  const 小件 = chain.find(e => { const r = e.getBoundingClientRect(); return r.width >= 10 && r.width <= 60 && r.height >= 10 && r.height <= 60; });
  return {
    在视口内,
    命中: !!小件,
    链尾: 顶.tagName + '.' + String(顶.className).slice(0, 40),
    命中框: 小件 ? [Math.round(小件.getBoundingClientRect().left), Math.round(小件.getBoundingClientRect().top), Math.round(小件.getBoundingClientRect().width), Math.round(小件.getBoundingClientRect().height)] : null,
    命中svg: 小件 ? ([...小件.querySelectorAll('path')].map(p => (p.getAttribute('d') || '').slice(0, 28))[0] || '') : '',
  };
}, 中心);

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

  // ---- ⭐ 缩到 50%：让所有卡片都进得了视口
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  记(`⌘0 后坐标偏差：${JSON.stringify(await 核对坐标(page))}`);
  const 缩放钮 = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button,[role="button"]')].find(x => /^\d+%$/.test((x.innerText || '').trim()));
    if (!b) return null;
    const r = b.getBoundingClientRect();
    return { 文字: (b.innerText || '').trim(), 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
  });
  记(`缩放按钮：${JSON.stringify(缩放钮)}`);
  if (!缩放钮) throw new Error('找不到缩放按钮');
  await page.mouse.click(缩放钮.中心[0], 缩放钮.中心[1]);
  await page.waitForTimeout(1200);
  await page.screenshot({ path: EVID + 'em2-缩放菜单.png' });
  // ⛔ 菜单项文字是「缩放至50%」，不是「50%」——按精确文本匹配会一个都找不到
  const 选50 = await page.evaluate(() => {
    const 候选 = [...document.querySelectorAll('button,div,[role="menuitem"],[role="button"],li,span')]
      .filter(e => /^缩放至\s*50\s*%$/.test((e.innerText || '').trim()))
      .filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
    if (!候选.length) return null;
    候选.sort((a, b) => a.getBoundingClientRect().width * a.getBoundingClientRect().height - b.getBoundingClientRect().width * b.getBoundingClientRect().height);
    const e = 候选[0], r = e.getBoundingClientRect();
    return { 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], tag: e.tagName, 文字: (e.innerText || '').trim() };
  });
  记(`50% 档：${JSON.stringify(选50)}`);
  if (!选50) throw new Error('缩放菜单里没有 50%');
  await page.mouse.click(选50.中心[0], 选50.中心[1]);
  await page.waitForTimeout(2500);
  const 现在缩放 = await page.evaluate(() => { const b = [...document.querySelectorAll('button,[role="button"]')].find(x => /^\d+%$/.test((x.innerText || '').trim())); return b ? (b.innerText || '').trim() : '?'; });
  记(`⭐ 缩放现在是 ${现在缩放}`);
  记(`缩放后坐标偏差：${JSON.stringify(await 核对坐标(page))}`);
  await page.screenshot({ path: EVID + 'em2-缩放50.png' });

  const 逐节点 = [];
  for (const t of 待测) {
    const 落点 = await page.evaluate((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!n) return null;
      const r = n.getBoundingClientRect();
      for (let i = 1; i < 10; i++) for (let j = 1; j < 10; j++) {
        const x = Math.round(r.left + r.width * i / 10), y = Math.round(r.top + r.height * j / 10);
        const e = document.elementFromPoint(x, y);
        const g = e && e.closest('.react-flow__node');
        if (g && g.getAttribute('data-id') === id) return [x, y];
      }
      return null;
    }, t.id);
    if (!落点) { 记(`\n—— 跳过 ${t.id}（仍被完全遮住）`); 逐节点.push({ ...t, 状态: '被遮住' }); continue; }
    await page.mouse.click(落点[0], 落点[1]);
    await page.waitForTimeout(2600);
    const 选中 = await page.evaluate((id) => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')), t.id);
    if (选中.length !== 1 || 选中[0] !== t.id) { 记(`\n—— 跳过 ${t.id}（点中了 ${JSON.stringify(选中)}）`); 逐节点.push({ ...t, 状态: '落点被抢', 实际选中: 选中 }); continue; }

    const 普查 = await page.evaluate((id) => {
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
        出.push({
          tag: e.tagName, cls: String(e.className || '').slice(0, 110), attrs,
          文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
          aria: attrs['aria-label'] || '', title: attrs.title || '',
          box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
          中心: [cx, cy],
          视口内: cx >= 0 && cy >= 0 && cx <= innerWidth && cy <= innerHeight,
          背景: getComputedStyle(e).backgroundColor,
          svg: [...e.querySelectorAll('path')].map(p => (p.getAttribute('d') || '').slice(0, 28))[0] || '',
        });
      }
      return 出;
    }, t.id);

    const 无名 = 普查.filter(x => !x.文字 && !x.aria && !x.title);
    记(`\n———— ${t.id} ${t.名} ————（小控件 ${普查.length}，三处全空 ${无名.length}）`);
    const 逐枚 = [];
    for (const b of 无名) {
      if (!b.视口内) { 记(`　　box=${JSON.stringify(b.box)} ⛔ 仍在视口外，跳过`); continue; }
      await page.mouse.move(20, 800);
      await page.waitForTimeout(1100);
      const 前 = await 读气泡(page);
      for (const d of [[-5, -5], [5, 5], [0, 0], [2, -2], [0, 0]]) {
        await page.mouse.move(b.中心[0] + d[0], b.中心[1] + d[1]);
        await page.waitForTimeout(380);
      }
      await page.waitForTimeout(3200);
      const 后 = await 读气泡(page);
      const 新 = 后.filter(y => !前.some(x => x.文本 === y.文本 && Math.abs(x.box[0] - y.box[0]) < 4));
      const 针 = await 指针在否(page, b.中心);
      记(`　　box=${JSON.stringify(b.box)} svg=${b.svg || '（无）'}`);
      记(`　　　:hover 链 ${针.在视口内 ? '' : '⛔不在视口 '}${针.命中 ? `✅命中 ${JSON.stringify(针.命中框)} svg=${针.命中svg}` : '⛔未命中小控件'}｜链尾=${针.链尾}`);
      记(`　　　气泡 ${新.length ? JSON.stringify(新.map(n => n.文本)) : '⛔ 0 个'}`);
      await page.screenshot({ path: EVID + `em2-${t.id}-${b.box[0]}x${b.box[1]}.png` });
      逐枚.push({ box: b.box, svg: b.svg, 指针命中: 针.命中, 命中框: 针.命中框, 命中svg: 针.命中svg, 气泡: 新.map(n => n.文本) });
    }
    if (逐枚.length && 逐枚.every(p => p.气泡.length === 0)) 记('　　⛔ 判据自检：本节点无一读出气泡，**阴性结果不作数**');
    await page.screenshot({ path: EVID + `em2-${t.id}-展开.png` });
    逐节点.push({ id: t.id, 名: t.名, 状态: '已普查', 控件数: 普查.length, 无名数: 无名.length, 逐枚 });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1300);
  }
  结果.读数.逐节点 = 逐节点;
  记('\n✅ 重测完毕');
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
  console.log('\n=== 已写 tools/batchEM2.json ===');
}
