// Batch EY-6：⭐⭐⭐ 矛盾探针 —— 卡上写着「取消收藏」，收藏列表却是空的
//
// EY-5 的逐卡读数：风格广场 30 张卡，详情 30 枚，收藏星 `aria="收藏"` 29 枚 +
// **`aria="取消收藏"` 1 枚**（#0 `Seedream 5.0 pro` / 热点推荐官）。**没有一张卡缺星。**
// 而 EY-4 同一天读风格广场「我的收藏」= **「暂无素材」0 张**。
//
// ⇒ 两个读数互相矛盾：**卡面显示它已被收藏，收藏列表里却没有它。**
//
// 两种可能，本轮用**图标形状**分辨（判据不依赖 aria 文字）：
//   A) 星形**是实心的** ⇒ 它真的在收藏列表里，那 EY-4 的「暂无素材」读错了
//   B) 星形**和别的卡一模一样（描边空心）** ⇒ 只是 aria 文案不一致，收藏列表才是对的
//
// ⭐ 再顺带把 #0 的 `取消收藏` 按钮**完整 outerHTML** 打出来，不靠猜。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEY6.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

/** 读一张卡上所有按钮的完整 outerHTML（形状判据，不看 aria） */
const 读卡 = (序) => page.evaluate((k) => {
  const 框 = [...document.querySelectorAll('[role=dialog]')]
    .sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
  if (!框) return null;
  const 候选 = Array.from(框.querySelectorAll('[class*="bg-canvas-controls-hover"]'))
    .filter((e) => e.classList.contains('hover:bg-canvas-controls-hover'));
  const 真卡 = 候选.filter((e) => !候选.some((o) => o !== e && e.contains(o)));
  const e = 真卡[k];
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return {
    文字: (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 46),
    box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
    按钮: [...e.querySelectorAll('button')].map((b) => ({
      aria: b.getAttribute('aria-label'),
      文字: (b.innerText || '').trim().slice(0, 14),
      box: [Math.round(b.getBoundingClientRect().left), Math.round(b.getBoundingClientRect().top), Math.round(b.getBoundingClientRect().width), Math.round(b.getBoundingClientRect().height)],
      path全: b.querySelector('path')?.getAttribute('d') || null,
      圆点数: b.querySelectorAll('circle').length,
      html: b.outerHTML.length > 700 ? b.outerHTML.slice(0, 700) + '…' : b.outerHTML,
    })),
  };
}, 序);

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  await page.mouse.move(676, 773); await page.waitForTimeout(400);
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(1200);
  await page.mouse.move(720, 300); await page.waitForTimeout(600);
  const 入口 = await page.evaluate(() => {
    const all = [...document.querySelectorAll('div')].filter((e) => {
      const r = e.getBoundingClientRect();
      if (r.left < 555 || r.left > 800 || r.top < 545 || r.top > 745) return false;
      if (getComputedStyle(e).cursor !== 'pointer') return false;
      return (e.innerText || '').trim().startsWith('风格库');
    }).map((e) => e.getBoundingClientRect()).sort((a, b) => (b.width * b.height) - (a.width * a.height));
    return all.length ? [Math.round(all[0].left + all[0].width / 2), Math.round(all[0].top + all[0].height / 2)] : null;
  });
  await page.mouse.move(入口[0], 入口[1]); await page.waitForTimeout(500);
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(3000);
  await page.mouse.move(720, 780); await page.waitForTimeout(1000);

  const c0 = await 读卡(0);
  const c1 = await 读卡(1);
  记('⭐ #0：' + JSON.stringify(c0 && c0.文字));
  记('⭐ #1：' + JSON.stringify(c1 && c1.文字));
  const 存 = (c) => (c.按钮 || []).find((b) => b.aria === '收藏' || b.aria === '取消收藏');
  const s0 = 存(c0), s1 = 存(c1);
  记('⭐ #0 的星：aria=' + (s0 && s0.aria) + ' path=' + (s0 && s0.path全));
  记('⭐ #1 的星：aria=' + (s1 && s1.aria) + ' path=' + (s1 && s1.path全));
  记('⭐⭐ 两个 path 相同？ ' + (s0 && s1 && s0.path全 === s1.path全));
  结果.读数.星对比 = { 卡0: s0, 卡1: s1, 相同: !!(s0 && s1 && s0.path全 === s1.path全) };
  结果.读数.卡0 = c0; 结果.读数.卡1 = c1;

  // 拍下 #0 整张卡和它的星
  if (c0) {
    await page.mouse.move(c0.box[0] + 95, c0.box[1] + 100); await page.waitForTimeout(700);
    await page.screenshot({ path: EVID + 'ey6-卡0-已收藏态.png', clip: { x: c0.box[0] - 8, y: c0.box[1] - 8, width: c0.box[2] + 16, height: 120 } });
    记('已拍 ey6-卡0-已收藏态.png（只看卡面上半截）');
    if (c1) {
      await page.mouse.move(c1.box[0] + 95, c1.box[1] + 100); await page.waitForTimeout(700);
      await page.screenshot({ path: EVID + 'ey6-卡1-未收藏态.png', clip: { x: c1.box[0] - 8, y: c1.box[1] - 8, width: c1.box[2] + 16, height: 120 } });
      记('已拍 ey6-卡1-未收藏态.png（同样的位置，用来比星的形状）');
    }
  }

  // 再读一次「我的收藏」
  const 页签 = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').trim() === '我的收藏');
    if (!b) return null;
    const r = b.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
  });
  await page.mouse.move(页签[0], 页签[1]); await page.waitForTimeout(500);
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(2000);
  await page.mouse.move(720, 780); await page.waitForTimeout(700);
  const 收藏页 = await page.evaluate(() => {
    const 框 = [...document.querySelectorAll('[role=dialog]')].sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
    if (!框) return null;
    const 候选 = Array.from(框.querySelectorAll('[class*="bg-canvas-controls-hover"]')).filter((e) => e.classList.contains('hover:bg-canvas-controls-hover'));
    const 真卡 = 候选.filter((e) => !候选.some((o) => o !== e && e.contains(o)));
    return { 卡片数: 真卡.length, 文字: 真卡.slice(0, 3).map((e) => (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 30)), 全文: (框.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 120) };
  });
  记('⭐⭐ 再读「我的收藏」：' + JSON.stringify(收藏页));
  结果.读数.我的收藏 = 收藏页;
  await page.screenshot({ path: EVID + 'ey6-风格-我的收藏-复测.png' });
  记('已拍 ey6-风格-我的收藏-复测.png');

  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0'); await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  结果.收尾 = { 偏差, 已渲染: Object.keys(await 读全部坐标(page)).length };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  落盘(结果);
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchEY6.json ===');
}
