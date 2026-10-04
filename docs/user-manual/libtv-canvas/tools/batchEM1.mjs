// Batch EM-1：把「全画布只有 2 枚控件悬停读不出名字」这个**全局结论**补全。
//   20-reference.md 那句的普查只覆盖了「默认画布 + 图片节点卡片 + 图片节点大编辑器」，
//   ⛔ 视频 / 文本 / 音频 / 智能剪辑 / 导演台 5 类节点的参数条**从来没普查过**
//   ⇒ 「全画布只有 2 枚」是个悬空结论。本轮把 11 个节点逐个过一遍。
//
// 判据沿用 EL 轮定稿的「阴性结论自证三步法」：
//   ① elementFromPoint 验落点归属  ② 读按钮悬停态底色变化  ③ 配阳性对照
// ⛔ 本脚本**只点节点本体**让它展开，**绝不点卡片里的任何按钮**。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEM1.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

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
  await page.waitForTimeout(3500);
  记(`开局坐标偏差：${JSON.stringify(await 核对坐标(page))}`);

  // ---- 节点台账：id → 类型标签（读节点头部的小标题）
  const 台账 = await page.evaluate((ids) => ids.map(id => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!n) return { id, 缺失: true };
    const r = n.getBoundingClientRect();
    const 头 = n.innerText.replace(/\s+/g, ' ').trim().slice(0, 30);
    return { id, 头部文字: 头, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }), BASE);
  记('\n⭐ 节点台账：');
  for (const n of 台账) 记(`　${n.id}  "${n.头部文字}" box=${JSON.stringify(n.box)}`);
  结果.读数.台账 = 台账;

  // ⭐ 逐个节点：铁律② 找安全落点 → 点开 → 普查 → 只对「无名控件」做悬停
  const 逐节点 = [];
  for (const 节点 of 台账) {
    if (节点.缺失) { 记(`\n—— 跳过 ${节点.id}（不在 DOM 里）`); continue; }
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
    }, 节点.id);
    if (!落点) { 记(`\n—— 跳过 ${节点.id}（被完全遮住，铁律② 拦下）`); 逐节点.push({ ...节点, 状态: '被遮住' }); continue; }

    await page.mouse.click(落点[0], 落点[1]);
    await page.waitForTimeout(2400);
    const 选中 = await page.evaluate((id) => {
      const s = [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id'));
      return { s, 对: s.length === 1 && s[0] === id };
    }, 节点.id);
    if (!选中.对) { 记(`\n—— 跳过 ${节点.id}（点中了 ${JSON.stringify(选中.s)}，不是我）`); 逐节点.push({ ...节点, 状态: '落点被抢', 实际选中: 选中.s }); continue; }

    const 普查 = await page.evaluate((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!n) return [];
      const 出 = [], 集 = new Set();
      for (const e of n.querySelectorAll('button,[role="button"],div[class*="size-7"],div[class*="size-8"]')) {
        if (集.has(e)) continue;
        const r = e.getBoundingClientRect();
        if (r.width < 12 || r.width > 400 || r.height < 12 || r.height > 90) continue;
        集.add(e);
        const attrs = {}; for (const a of e.attributes) attrs[a.name] = a.value;
        const cx = Math.round(r.left + r.width / 2), cy = Math.round(r.top + r.height / 2);
        const top = document.elementFromPoint(cx, cy);
        出.push({
          tag: e.tagName,
          cls: String(e.className || '').slice(0, 110),
          attrs,
          文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
          aria: attrs['aria-label'] || '',
          title: attrs.title || '',
          box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
          中心: [cx, cy],
          顶层: top ? (top === e ? '自己' : (top.closest('button,[role="button"]') ? '内部' : '外层:' + top.tagName)) : 'null',
          背景: getComputedStyle(e).backgroundColor,
          svg: [...e.querySelectorAll('path')].map(p => (p.getAttribute('d') || '').slice(0, 28))[0] || '',
        });
      }
      return 出;
    }, 节点.id);

    // ⭐ 只挑「三种来源都读不出名字」的
    const 无名 = 普查.filter(x => !x.文字 && !x.aria && !x.title);
    记(`\n———— ${节点.id} "${节点.头部文字}" ————`);
    记(`　小控件 ${普查.length} 个，其中**文字/aria/title 三者全空**的有 ${无名.length} 个`);
    for (const b of 无名) 记(`　　box=${JSON.stringify(b.box)} 顶层=${b.顶层} 背景=${b.背景} svg=${b.svg || '（无）'} cls=${b.cls.slice(0, 52)}`);

    const 逐枚 = [];
    for (const b of 无名) {
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
      const 背后 = await page.evaluate((p) => { const e = document.elementFromPoint(p[0], p[1]); const b = e && e.closest('button,[role="button"]'); return b ? getComputedStyle(b).backgroundColor : ''; }, b.中心);
      记(`　　悬停 box=${JSON.stringify(b.box)} 底色 ${b.背景} → ${背后} ${b.背景 !== 背后 ? '✅变' : '⛔没变'}｜气泡 ${新.length ? JSON.stringify(新.map(n => n.文本)) : '⛔ 0 个'}`);
      await page.screenshot({ path: EVID + `em1-${节点.id}-${b.box[0]}x${b.box[1]}.png` });
      逐枚.push({ box: b.box, cls: b.cls, svg: b.svg, 顶层: b.顶层, 背景前: b.背景, 背后, 底色变了: b.背景 !== 背后, 气泡: 新.map(n => n.文本) });
    }
    if (无名.length === 0) 记('　　（本节点无「三处都空」的控件）');
    else if (逐枚.every(p => p.气泡.length === 0)) 记('　　⛔ 判据自检：本节点没有气泡读出，**这些阴性结果不作数**（需另配阳性对照）');

    await page.screenshot({ path: EVID + `em1-${节点.id}-展开.png` });
    逐节点.push({ id: 节点.id, 头部文字: 节点.头部文字, 状态: '已普查', 控件数: 普查.length, 无名数: 无名.length, 逐枚 });

    await page.keyboard.press('Escape');
    await page.waitForTimeout(1200);
  }
  结果.读数.逐节点 = 逐节点;
  记('\n✅ 11 个节点普查完毕');
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
  console.log('\n=== 已写 tools/batchEM1.json ===');
}
