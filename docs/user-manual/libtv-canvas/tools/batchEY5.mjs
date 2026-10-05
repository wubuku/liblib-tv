// Batch EY-5：⭐⭐⭐ 风格广场「30 张卡 / 30 枚详情 / 只有 29 枚收藏星」—— 差的那一张是谁？
//
// EY-4 同一次读数：风格广场默认态 卡片 `30`、详情按钮 `30`、收藏星 `29`。
// ⛔ 三个数不等，**不许含糊过去**。两种可能，必须分辨：
//   A) 有一张卡**没有收藏星**（比如「热点推荐官」那种无徽标卡型）
//   B) 有一张卡**已经处于收藏态** ⇒ 它的 `aria-label` 是「取消收藏」而不是「收藏」
//   （测试账号上留着前几批点过收藏的风格，也是 B 的一种）
//
// ⭐ 判据：逐卡点名 + 对每张卡同时数「详情」和「收藏/取消收藏」两种 aria。
//    再用 `我的收藏` 页是不是空的来把 B 排掉。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEY5.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 逐卡 = () => page.evaluate(() => {
  const 框 = [...document.querySelectorAll('[role=dialog]')]
    .sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
  if (!框) return null;
  const 候选 = Array.from(框.querySelectorAll('[class*="bg-canvas-controls-hover"]'))
    .filter((e) => e.classList.contains('hover:bg-canvas-controls-hover'));
  const 真卡 = 候选.filter((e) => !候选.some((o) => o !== e && e.contains(o)));
  return 真卡.map((e, i) => {
    const r = e.getBoundingClientRect();
    const 按钮 = [...e.querySelectorAll('button')].map((b) => {
      const br = b.getBoundingClientRect();
      return { aria: b.getAttribute('aria-label'), 可见: br.width > 0 && br.height > 0, box: [Math.round(br.left), Math.round(br.top), Math.round(br.width), Math.round(br.height)], op: getComputedStyle(b).opacity, path: (b.querySelector('path')?.getAttribute('d') || '').slice(0, 26) };
    });
    return {
      i,
      文字: (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 46),
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      在视口内: r.top >= 0 && r.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth,
      有商用: /商用/.test(e.innerText || ''),
      有热点: /热点推荐官/.test(e.innerText || ''),
      详情: 按钮.filter((b) => b.aria === '详情').length,
      收藏: 按钮.filter((b) => b.aria === '收藏').length,
      取消收藏: 按钮.filter((b) => b.aria === '取消收藏').length,
      无名按钮: 按钮.filter((b) => !b.aria).length,
      按钮,
    };
  });
});

const 浏览器 = await launch();
const page = 浏览器.page;
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
    if (!all.length) return null;
    return [Math.round(all[0].left + all[0].width / 2), Math.round(all[0].top + all[0].height / 2)];
  });
  if (!入口) throw new Error('找不到风格库入口');
  await page.mouse.move(入口[0], 入口[1]); await page.waitForTimeout(500);
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(3000);
  await page.mouse.move(720, 780); await page.waitForTimeout(800);

  const 卡 = await 逐卡();
  记(`⭐ 面板 DOM 里 ${卡.length} 张卡，其中在视口内 ${卡.filter((c) => c.在视口内).length} 张`);
  const 汇 = {
    总数: 卡.length,
    有详情: 卡.filter((c) => c.详情 > 0).length,
    有收藏星: 卡.filter((c) => c.收藏 > 0).length,
    已收藏态: 卡.filter((c) => c.取消收藏 > 0).length,
    无收藏星: 卡.filter((c) => c.收藏 === 0 && c.取消收藏 === 0).map((c) => ({ i: c.i, 文字: c.文字, 有商用: c.有商用, 有热点: c.有热点, 无名按钮: c.无名按钮, box: c.box })),
  };
  记('⭐ 汇总：' + JSON.stringify(汇, null, 1));
  结果.读数.汇总 = 汇;
  结果.读数.逐卡 = 卡;

  记('--- 逐卡点名（视口内）---');
  for (const c of 卡.filter((x) => x.在视口内)) {
    记(`  #${String(c.i).padStart(2)} "${c.文字}" box=${JSON.stringify(c.box)} 详情=${c.详情} 收藏=${c.收藏} 取消=${c.取消收藏} 无名=${c.无名按钮} 商用=${c.有商用} 热点=${c.有热点}`);
  }

  if (汇.无收藏星.length) {
    const t = 汇.无收藏星[0];
    const x = t.box[0] + t.box[2] - 20, y = t.box[1] + 20;
    await page.mouse.move(x, y); await page.waitForTimeout(800);
    await page.screenshot({ path: EVID + 'ey5-没有收藏星的那张卡.png', clip: { x: t.box[0] - 8, y: t.box[1] - 8, width: t.box[2] + 16, height: t.box[3] + 16 } });
    记(`已拍 ey5-没有收藏星的那张卡.png（"${t.文字}"）`);
    const 悬停后 = await 逐卡();
    const 同一 = 悬停后.find((c) => c.i === t.i);
    记('悬停后这张卡的按钮：' + JSON.stringify(同一 && 同一.按钮));
  }

  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  结果.收尾 = { 偏差, 已渲染: Object.keys(await 读全部坐标(page)).length };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  落盘(结果);
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchEY5.json ===');
}
