// Batch EF-10：⭐ 精确定位「当前使用」徽标 —— 截图已确认它在卡面**左下角**（不是左上角）。
//
// EF-1~EF-9 连续九轮读不到，三次判据各自不同地错：
//   ① 向上找背景爬到 <body>；② class 含 current 命中 Tailwind 的 text-current；
//   ③ 只找「近白底」而它不是近白；④ 以为它在画布节点上（实际在广场卡面上）。
// 本步不再猜背景色，直接**按坐标取那一小块元素**，把它的一切读数原样打印。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE, 允许删除 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEF10.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };
const 目标ID = 'i-sODTbgLUm1';

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1200);
  await page.evaluate(() => { for (const b of document.querySelectorAll('button')) if ((b.innerText || '').trim() === '知道了') { b.click(); return; } });
  await page.waitForTimeout(600);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  // ⭐ 先看画布上有没有上轮建出来的 `素材-风格-Seedream 5.0` 节点
  const 画布 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map(n => ({
    id: n.getAttribute('data-id'),
    名: (n.innerText || '').split('\n').filter(Boolean)[0] || '',
  })));
  结果.读数.画布节点 = 画布;
  记(`画布 ${画布.length} 个（基线 ${BASE.length}）；新增：${JSON.stringify(画布.filter(n => !BASE.includes(n.id)).map(n => n.名))}`);

  // 选图片节点 → 点「替换」开广场
  const 标题 = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    const t = [...n.querySelectorAll('*')].find(e => /图片节点/.test(e.innerText || '') && e.children.length === 0);
    const r = (t || n).getBoundingClientRect();
    return [r.left + r.width / 2, r.top + r.height / 2];
  }, 目标ID);
  await page.mouse.click(标题[0], 标题[1]);
  await page.waitForTimeout(1500);
  await page.evaluate(() => {
    const 编辑器 = [...document.querySelectorAll('div')].find(e => {
      const r = e.getBoundingClientRect();
      const t = e.innerText || '';
      if (r.width < 250 || r.height < 150) return false;
      if (!/参考/.test(t) || !/Lib Image/.test(t)) return false;
      for (const c of e.children) { const cr = c.getBoundingClientRect(); if (cr.width >= 250 && cr.height >= 150 && /参考/.test(c.innerText || '')) return false; }
      return true;
    });
    if (!编辑器) return;
    for (const 文 of ['替换', '风格']) {
      const el = [...编辑器.querySelectorAll('*')].find(e => e.children.length === 0 && (e.innerText || '').trim() === 文);
      if (el) { el.click(); return; }
    }
  });
  await page.waitForTimeout(2800);
  记('已开风格广场');

  // ⭐⭐ 按坐标取：首张卡的左下角
  const 精确 = await page.evaluate(() => {
    const 广场 = [...document.querySelectorAll('.mantine-Modal-content, .mantine-Drawer-content')]
      .find(e => /风格广场|我的收藏|最近使用/.test(e.innerText || ''));
    if (!广场) return { 错: '广场没开' };
    // 找卡：带图、尺寸合理
    const imgs = [...广场.querySelectorAll('img')].filter(i => {
      const r = i.getBoundingClientRect();
      return r.width > 100 && r.height > 100;
    });
    const 首图 = imgs[0];
    if (!首图) return { 错: '没找到卡图' };
    const 卡 = 首图.closest('[class*="group"]') || 首图.parentElement.parentElement;
    const cr = 卡.getBoundingClientRect();
    // ⭐ 左下角：x = 卡左 + 12, y = 卡底 - 22
    const 探针 = [cr.left + 30, cr.bottom - 20];
    const 栈 = document.elementsFromPoint(探针[0], 探针[1]).slice(0, 6).map(e => {
      const r = e.getBoundingClientRect();
      const cs = getComputedStyle(e);
      return {
        tag: e.tagName,
        text: (e.innerText || '').trim().slice(0, 20),
        bg: cs.backgroundColor, color: cs.color, fontSize: cs.fontSize,
        borderRadius: cs.borderRadius, padding: cs.padding,
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        cls: e.className.toString().slice(0, 120),
        html: e.outerHTML.slice(0, 300),
      };
    });
    return {
      卡名: (卡.innerText || '').split('\n').filter(Boolean)[0],
      卡box: [Math.round(cr.left), Math.round(cr.top), Math.round(cr.width), Math.round(cr.height)],
      探针, 栈,
    };
  });
  结果.读数.精确 = 精确;
  if (精确.栈) {
    console.log(`\n═══ 卡「${精确.卡名}」box=${JSON.stringify(精确.卡box)} ═══`);
    console.log('  探针点:', JSON.stringify(精确.探针), '（左下角）');
    精确.栈.forEach((e, i) => {
      console.log(`\n  [${i}] <${e.tag}> "${e.text}"`);
      console.log(`      bg=${e.bg} color=${e.color} 字号=${e.fontSize} 圆角=${e.borderRadius} padding=${e.padding}`);
      console.log(`      box=${JSON.stringify(e.box)}`);
      if (i <= 2) console.log(`      html=${e.html.slice(0, 200)}`);
    });
  } else {
    console.log('  ', JSON.stringify(精确));
  }
  await page.screenshot({ path: '.evidence/batchEF10-当前使用徽标精确读数.png' });
  落盘(结果);
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEF10.json ===');
}
