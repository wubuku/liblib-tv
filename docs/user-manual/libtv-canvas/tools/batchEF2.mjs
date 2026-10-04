// Batch EF-2：⭐ 定位并读全「当前使用」白底徽标（EF-1b 已在截图里看到它了）。
//
// EF-1b 的结论：全文搜「当前使用」只命中 <script> 里的 SSR 注水数据 ——
// 因为**广场里的卡要等它所在的弹层打开后才在 DOM 里**，且徽标在**图片上、左上角**。
// EF-2 换判据：不搜文字，**直接找那枚白底胶囊**（`bg-white` + 13px 图标 + 12px 黑字）。
//
// ⭐ 已从截图看到：卡 `Seedream 5 pro` 左上角就是它。源码判据：
//   W = typeof a === 'string' ? a === e.uuid : a?.has(e.uuid) ?? false
//   a = 当前节点正在用的风格 uuid
//
// ⛔ 纯只读：只开弹层、读 DOM、ESC 关掉。**不点任何卡**（那会换风格）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEF2.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = { 读数: {} };

/** 在已打开的风格广场里，逐卡枚举「徽标位」上有什么。 */
const 读卡面徽标 = (page) => page.evaluate(() => {
  const 广场 = [...document.querySelectorAll('.mantine-Modal-content, .mantine-Drawer-content')]
    .find(e => /风格广场|我的收藏|最近使用/.test(e.innerText || ''));
  if (!广场) return { 错: '没找到风格广场容器' };

  const 卡 = [...广场.querySelectorAll('[class*="group"]')].filter(e => {
    const r = e.getBoundingClientRect();
    return r.width > 120 && r.width < 320 && r.height > 150;
  });

  const 结果 = [];
  for (const c of 卡) {
    const r = c.getBoundingClientRect();
    // 徽标位：卡片左上角那一小块
    const 左上 = {
      x: r.left + 8, y: r.top + 8, w: 120, h: 28,
    };
    // 找落在这个区域、且有白底或半透明底的元素
    const els = document.elementsFromPoint(左上.x + 30, 左上.y + 10) || [];
    const 徽标 = [];
    for (const e of els) {
      if (!广场.contains(e)) break;
      const cs = getComputedStyle(e);
      if (cs.backgroundColor === 'rgba(0, 0, 0, 0)') continue;
      if (e.getBoundingClientRect().width > 200) continue;
      徽标.push({
        tag: e.tagName, text: (e.innerText || '').trim().slice(0, 20),
        bg: cs.backgroundColor, color: cs.color,
        cls: e.className.toString().slice(0, 70),
        box: (() => { const b = e.getBoundingClientRect(); return [Math.round(b.left), Math.round(b.top), Math.round(b.width), Math.round(b.height)]; })(),
      });
    }
    const 卡名 = (c.innerText || '').split('\n').filter(Boolean)[0] || '';
    结果.push({ 卡名: 卡名.slice(0, 30), 卡box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 徽标位: 徽标.slice(0, 3) });
  }
  return { 卡数: 卡.length, 明细: 结果 };
});

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6000 });
  await closePromos(page);
  await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1600);

  // 选中图片节点 i-sODTbgLUm1（EF-1 里成功弹出风格广场的那个）
  const 节点 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map(n => {
    const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), cls: n.className.toString(), box: [r.left, r.top, r.width, r.height] };
  }));
  const 目标 = 节点.find(n => n.id === 'i-sODTbgLUm1') || 节点.find(n => /node-image/.test(n.cls));
  console.log('目标节点:', 目标.id);
  await page.mouse.click(目标.box[0] + 目标.box[2] / 2, 目标.box[1] + 目标.box[3] / 2);
  await page.waitForTimeout(1200);

  const 开了 = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === '风格');
    if (!b) return false; b.click(); return true;
  });
  console.log('点「风格」:', 开了);
  await page.waitForTimeout(2000);

  const 读数 = await 读卡面徽标(page);
  结果.读数.卡面徽标 = 读数;
  console.log('\n═══ 广场里识别到', 读数.卡数, '张卡 ═══');
  for (const c of (读数.明细 || [])) {
    console.log(`\n  卡「${c.卡名}」:`);
    if (!c.徽标位.length) console.log('    （徽标位空）');
    for (const b of c.徽标位) console.log(`    [${b.tag}] "${b.text}" bg=${b.bg} color=${b.color} box=${JSON.stringify(b.box)}`);
  }
  落盘(结果);

  // ⭐ 精确抓「当前使用」那枚：白底 + 黑字 + 13px 图标
  const 精确 = await page.evaluate(() => {
    const out = [];
    for (const e of document.querySelectorAll('span,div')) {
      if ((e.innerText || '').trim() !== '当前使用') continue;
      if (e.querySelector('span,div')) continue;      // 只要叶子
      const r = e.getBoundingClientRect();
      const cs = getComputedStyle(e);
      if (r.width === 0) continue;
      const 胶囊 = e.parentElement;
      const pcs = getComputedStyle(胶囊);
      const pr = 胶囊.getBoundingClientRect();
      out.push({
        文本: '当前使用',
        文本盒: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        字号: cs.fontSize, 文字色: cs.color,
        胶囊tag: 胶囊.tagName, 胶囊class: 胶囊.className.toString(),
        胶囊bg: pcs.backgroundColor, 胶囊box: [Math.round(pr.left), Math.round(pr.top), Math.round(pr.width), Math.round(pr.height)],
        图标数: 胶囊.querySelectorAll('svg').length,
        所属卡名: (胶囊.closest('[class*="group"]')?.innerText || '').split('\n').filter(Boolean)[0] || '',
        html: 胶囊.outerHTML.slice(0, 400),
      });
    }
    return out;
  });
  结果.读数.精确徽标 = 精确;
  console.log('\n═══ ⭐「当前使用」精确读数:', 精确.length, '枚 ═══');
  for (const p of 精确) {
    console.log('  卡名:', p.所属卡名);
    console.log('  胶囊:', p.胶囊box, 'bg=', p.胶囊bg, 'class=', p.胶囊class);
    console.log('  文本:', p.文本盒, '字号=', p.字号, '色=', p.文字色, 'svg 数=', p.图标数);
    console.log('  html:', p.html);
  }
  落盘(结果);

  if (精确.length) await page.screenshot({ path: '.evidence/batchEF2-当前使用徽标.png' });
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEF2.json ===');
}
