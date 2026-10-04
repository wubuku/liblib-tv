// Batch EL-4：给 EL-3 的阴性结果补上**够格的阳性对照**。
//   EL-3 的阳性对照选错了对象（`图生图` 是带文字的按钮，可能本来就没气泡），
//   所以「读出 0 个」分不清是「真没有」还是「判据又坏了」。
// 本轮：
//   ① 阳性对照 = 手册明写有气泡的 `文A 翻译提示词`（同一张卡片里）+ 底栏 `画布小地图`（EK 批结案过）
//   ② 每个悬停点先用 elementFromPoint 验证「该点最上层的确实是目标元素」，
//      再看悬停后**按钮自身背景色是否变化**（变了 = 鼠标真的在上面）
//   ③ 悬停时长加到 3.5s，并做小幅游走，逼出带 openDelay 的气泡
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEL4.json';
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
  await page.waitForTimeout(3500);
  记(`开局坐标偏差：${JSON.stringify(await 核对坐标(page))}`);

  const 被测 = 'i-sODTbgLUm1';
  const 落点 = await page.evaluate((id) => {
    const 节点 = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!节点) return null;
    const r = 节点.getBoundingClientRect();
    for (let i = 1; i < 10; i++) for (let j = 1; j < 10; j++) {
      const x = Math.round(r.left + r.width * i / 10), y = Math.round(r.top + r.height * j / 10);
      const e = document.elementFromPoint(x, y);
      const 归 = e && e.closest('.react-flow__node');
      if (归 && 归.getAttribute('data-id') === id) return [x, y];
    }
    return null;
  }, 被测);
  记(`铁律②复核：安全落点 = ${JSON.stringify(落点)}`);
  await page.mouse.click(落点[0], 落点[1]);
  await page.waitForTimeout(2500);
  const 选中了 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
  记(`点击后选中：${JSON.stringify(选中了)}`);
  if (选中了.length !== 1 || 选中了[0] !== 被测) throw new Error('选中对象不对，终止');

  // ---- 卡片底栏（y 在 630~660 那一行）完整清单
  const 底栏 = await page.evaluate((id) => {
    const 节点 = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!节点) return [];
    const 出 = [], 集 = new Set();
    for (const e of 节点.querySelectorAll('button,[role="button"]')) {
      if (集.has(e)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 10 || r.width > 400 || r.height < 10 || r.height > 90) continue;
      if (r.top < 600 || r.top > 700) continue;          // ⭐ 只看底栏那一行
      集.add(e);
      const attrs = {}; for (const a of e.attributes) attrs[a.name] = a.value;
      const cx = Math.round(r.left + r.width / 2), cy = Math.round(r.top + r.height / 2);
      const top = document.elementFromPoint(cx, cy);
      出.push({
        tag: e.tagName,
        文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 26),
        attrs,
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        中心: [cx, cy],
        顶层归属: top ? (top === e ? '就是它' : (top.closest('button') ? '它内部的' + top.closest('button').tagName : '别的:' + top.tagName + '.' + String(top.className).slice(0, 30))) : 'null',
        svg: [...e.querySelectorAll('path')].map(p => (p.getAttribute('d') || '').slice(0, 30))[0] || '',
        背景: getComputedStyle(e).backgroundColor,
      });
    }
    return 出;
  }, 被测);
  记(`\n⭐ 卡片底栏共 ${底栏.length} 枚（已验 elementFromPoint 归属）：`);
  for (const b of 底栏) {
    记(`　box=${JSON.stringify(b.box)} 文字="${b.文字}" 背景=${b.背景} 顶层=${b.顶层归属}`);
    记(`　　　aria-label=${b.attrs['aria-label'] ?? '⛔无'} title=${b.attrs.title ?? '⛔无'} 非class属性=${Object.keys(b.attrs).filter(k => k !== 'class' && k !== 'aria-label' && k !== 'title').join(',') || '（无）'}`);
    记(`　　　svg=${b.svg || '（无 path）'}`);
  }
  结果.读数.底栏 = 底栏;
  await page.screenshot({ path: EVID + 'el4-底栏清单.png' });

  const 气泡 = () => page.evaluate(() => {
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

  const 试悬停 = async (目标, 标签, 避到 = [20, 800]) => {
    await page.mouse.move(避到[0], 避到[1]);
    await page.waitForTimeout(1300);
    const 前 = await 气泡();
    const 背前 = await page.evaluate((p) => { const e = document.elementFromPoint(p[0], p[1]); return e ? getComputedStyle(e.closest('button') || e).backgroundColor : ''; }, 目标.中心);
    for (const d of [[-6, -6], [6, 6], [-3, 4], [0, 0], [2, -2], [0, 0]]) {
      await page.mouse.move(目标.中心[0] + d[0], 目标.中心[1] + d[1]);
      await page.waitForTimeout(420);
    }
    await page.waitForTimeout(3500);
    const 后 = await 气泡();
    const 新 = 后.filter(y => !前.some(x => x.文本 === y.文本 && Math.abs(x.box[0] - y.box[0]) < 4));
    const 背后 = await page.evaluate((p) => { const e = document.elementFromPoint(p[0], p[1]); return e ? getComputedStyle(e.closest('button') || e).backgroundColor : ''; }, 目标.中心);
    记(`\n　[${标签}] box=${JSON.stringify(目标.box)} 文字="${目标.文字 || ''}"`);
    记(`　　　悬停前后按钮背景：${背前} → ${背后} ${背前 !== 背后 ? '（变了 ⇒ 鼠标确实落在按钮上）' : '（没变）'}`);
    记(`　　　新出现气泡 ${新.length} 个：${新.length ? '' : '⛔ 0 个'}`);
    for (const n of 新) 记(`　　　　「${n.文本}」 ${JSON.stringify(n.box)} ${n.Tip ? '[Tooltip 容器]' : '[普通元素]'}`);
    const bx = 目标.中心[0], by = 目标.中心[1];
    await page.screenshot({ path: EVID + `el4-悬停-${标签}.png` });
    return { 标签, box: 目标.box, 文字: 目标.文字, 背前, 背后, 背景变了: 背前 !== 背后, 新: 新.map(n => n.文本), 新全: 新 };
  };

  // ---- 阳性对照 ①：文A 翻译提示词（手册明写图片节点上有气泡）
  const 阳性1 = 底栏.find(x => /M15\.52 7\.2c/.test(x.svg)) || 底栏.find(x => x.中心[0] > 1180 && x.中心[0] < 1240);
  记(`\n⭐ 阳性对照① 文A 翻译提示词：${阳性1 ? JSON.stringify({ box: 阳性1.box, svg: 阳性1.svg }) : '❌ 没定位到'}`);
  结果.读数.阳性1 = await 试悬停(阳性1 || { 中心: [0, 0], box: [0, 0], 文字: '' }, '阳性1-文A翻译提示词');

  // ---- 阳性对照 ②：底栏「画布小地图」（EK 批结案过有气泡）
  const 阳性2 = await page.evaluate(() => {
    const cands = [...document.querySelectorAll('button,[role="button"]')].filter(b => {
      const r = b.getBoundingClientRect();
      return r.top > 740 && r.width > 10 && r.width < 80 && r.height > 10 && r.height < 80;
    });
    return cands.map((b, i) => {
      const r = b.getBoundingClientRect();
      return { i, 文字: (b.innerText || '').trim().slice(0, 12), 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], cls: String(b.className).slice(0, 40) };
    });
  });
  记(`\n⭐ 底栏按钮 ${阳性2.length} 枚，取第 2 枚做阳性对照②：`);
  阳性2.forEach((b, i) => 记(`　[${i}] box=${JSON.stringify(b.box)} 文字="${b.文字}"`));
  const 阳性2选 = 阳性2[2] || 阳性2[0];
  结果.读数.阳性2 = await 试悬停(阳性2选, '阳性2-底栏按钮', [20, 300]);

  // ---- 被验对象
  const 滑块 = 底栏.find(x => x.svg.includes('M14 17H5M19 7h-9'));
  const 箭头 = await page.evaluate((id) => {
    const 节点 = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!节点) return null;
    const e = [...节点.querySelectorAll('button')].find(b => /bg-panel-background/.test(b.className) && /absolute right-2 top-2/.test(b.className));
    if (!e) return null;
    const r = e.getBoundingClientRect();
    const attrs = {}; for (const a of e.attributes) attrs[a.name] = a.value;
    return { 文字: '', box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], attrs, svg: '', 背景: getComputedStyle(e).backgroundColor };
  }, 被测);
  记(`\n⭐ 滑块 box=${JSON.stringify(滑块?.box)} 非class属性=${JSON.stringify(Object.fromEntries(Object.entries(滑块?.attrs || {}).filter(([k]) => k !== 'class')))}`);
  记(`⭐ 箭头 box=${JSON.stringify(箭头?.box)} 非class属性=${JSON.stringify(Object.fromEntries(Object.entries(箭头?.attrs || {}).filter(([k]) => k !== 'class')))}`);
  结果.读数.滑块 = 滑块 || null;
  结果.读数.箭头 = 箭头 || null;
  结果.读数.滑块悬停 = await 试悬停(滑块, '高级设置滑块');
  结果.读数.箭头悬停 = await 试悬停(箭头, '展开收起箭头');

  记('\n✅ 全部留下全视口截图（含阴性）');
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
  console.log('\n=== 已写 tools/batchEL4.json ===');
}
