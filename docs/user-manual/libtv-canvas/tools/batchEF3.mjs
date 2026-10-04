// Batch EF-3：EF-2 精确匹配 0 枚，但 EF-1 的截图里明确看到「当前使用」白底胶囊。
// ⇒ 问题在**判据**，不在现象。直接把首张卡左上角那块 DOM 原样 dump 出来。
//
// ⭐ 这一步不做任何筛选 —— 原样打印元素树，看到什么记什么。
// （ED 批教训：「读不到 ≠ 不存在」；EF-1b 教训：判据太宽/太窄都会骗人。）
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEF3.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = {};

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6000 });
  await closePromos(page);
  await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1600);

  const 节点 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map(n => {
    const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), cls: n.className.toString(), box: [r.left, r.top, r.width, r.height] };
  }));
  const 目标 = 节点.find(n => n.id === 'i-sODTbgLUm1') || 节点.find(n => /node-image/.test(n.cls));
  await page.mouse.click(目标.box[0] + 目标.box[2] / 2, 目标.box[1] + 目标.box[3] / 2);
  await page.waitForTimeout(1200);
  await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === '风格');
    if (b) b.click();
  });
  await page.waitForTimeout(2200);

  // ⭐ 广场容器 + 它里面所有可见文本节点的完整清单
  const 全面 = await page.evaluate(() => {
    const 广场 = [...document.querySelectorAll('.mantine-Modal-content, .mantine-Drawer-content')]
      .find(e => /风格广场|我的收藏|最近使用/.test(e.innerText || ''));
    if (!广场) return { 错: '无广场' };
    const pr = 广场.getBoundingClientRect();

    // 广场内**所有**文本节点（去重），带位置和可见性
    const 文本 = [];
    const w = document.createTreeWalker(广场, NodeFilter.SHOW_TEXT);
    const seen = new Set();
    let n;
    while ((n = w.nextNode())) {
      const t = (n.nodeValue || '').trim();
      if (!t || seen.has(t)) continue;
      seen.add(t);
      const p = n.parentElement;
      const r = p.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      文本.push({ t: t.slice(0, 24), tag: p.tagName, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
    }
    return {
      广场box: [Math.round(pr.left), Math.round(pr.top), Math.round(pr.width), Math.round(pr.height)],
      页签: [...广场.querySelectorAll('button')].slice(0, 5).map(b => b.innerText.trim()),
      文本数: 文本.length,
      含当前的: 文本.filter(x => /当前/.test(x.t)),
      前40条文本: 文本.slice(0, 40),
    };
  });
  结果.全面 = 全面;
  console.log('广场:', JSON.stringify(全面.广场box), '页签:', JSON.stringify(全面.页签));
  console.log('文本节点总数:', 全面.文本数);
  console.log('含「当前」的:', JSON.stringify(全面.含当前的));
  console.log('\n前 40 条文本:');
  for (const t of 全面.前40条文本) console.log(`  "${t.t}" [${t.tag}] ${JSON.stringify(t.box)}`);
  落盘(结果);

  // ⭐ 更狠的一招：直接找 src 含 CurrentUseCheck 的 svg（源码里的图标名）
  const 图标 = await page.evaluate(() => {
    const out = [];
    for (const svg of document.querySelectorAll('svg')) {
      const cls = svg.className.baseVal || svg.getAttribute('class') || '';
      if (!/current/i.test(cls)) continue;
      const r = svg.getBoundingClientRect();
      if (r.width === 0) continue;
      out.push({
        cls: cls.slice(0, 100),
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        父链: (() => { const c = []; for (let e = svg.parentElement; e && c.length < 5; e = e.parentElement) c.push(e.tagName + '.' + (typeof e.className === 'string' ? e.className.slice(0, 50) : '')); return c; })(),
        父innerText: (svg.closest('div')?.innerText || '').trim().slice(0, 20),
      });
    }
    return out;
  });
  结果.图标 = 图标;
  console.log('\n═══ ⭐ class 含 current 的 svg:', 图标.length, '个 ═══');
  for (const s of 图标) {
    console.log('  cls:', s.cls);
    console.log('  box:', JSON.stringify(s.box), '| 父链:', JSON.stringify(s.父链));
    console.log('  父 innerText:', JSON.stringify(s.父innerText));
  }
  落盘(结果);

  await page.screenshot({ path: '.evidence/batchEF3-广场首卡DOM.png' });
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEF3.json ===');
}
