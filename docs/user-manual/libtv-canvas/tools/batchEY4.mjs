// Batch EY-4：⭐⭐⭐ `我的收藏` / `最近使用` 两个页签从没被读过 + 收藏往返
//
// EY-3 结掉的：
//   ⭐⭐⭐ 特效广场 **0 枚** `aria="详情"`，风格广场 **30/30 张卡各 1 枚**（同会话同检测器）
//   ⭐⭐ 特效卡上只有两枚控件：`⋯`（三点，aria=null，常驻）+ `收藏`（悬停 0→1）
//   ⭐⭐ 点 `⋯` **不产生任何菜单**（innerHTML 只少了 89 字符 = hover 类名）
//
// 但 EY-3 切两个页签失败（`Escape` 把整个广场关了）。
// ⛔ **未读的还剩两块**：`我的收藏` / `最近使用` —— 它们的卡数据来源和「广场」不同，
//    理论上可能出现广场里没有的控件。**没读过就不能说它们也没有详情。**
//
// 本轮：① 两个页签各读一遍（卡片数 / 空态文案 / 详情按钮数）
//      ② 收藏一张 → 再读「我的收藏」→ **取消收藏复原**
//      ③ 风格广场「我的收藏」做对照
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEY4.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 自证 = (中心, 必须含) => page.evaluate(([x, y, w]) => {
  const e = document.elementFromPoint(x, y);
  if (!e) return null;
  const b = e.closest('button,[role=button]');
  const 文字 = (b?.innerText || e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 30);
  return { tag: e.tagName, 文字, aria: b?.getAttribute('aria-label') || null, 命中: (文字 + (b?.getAttribute('aria-label') || '')).includes(w) };
}, [中心[0], 中心[1], 必须含]);

/** ⭐ 唯一的点击入口：先 move 回目标 → 自证 → 才 down/up。
 *  ⛔ `elementFromPoint` 验的是「那个坐标上是什么」，验不出「鼠标不在那儿」——
 *     EY-3 前四版全栽在这（清场 move 之后直接 down，点到了画布）。 */
const 点击 = async (位置, 期望串 = '') => {
  await page.mouse.move(位置[0], 位置[1]);
  await page.waitForTimeout(450);
  const v = await 自证(位置, 期望串);
  if (期望串 && (!v || !v.命中)) throw new Error(`落点自证失败：期望含「${期望串}」，实得 ${JSON.stringify(v)}`);
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(1200);
  await page.mouse.move(720, 780);
  await page.waitForTimeout(600);
  return v;
};

const 弹窗 = () => page.evaluate(() => [...document.querySelectorAll('[role=dialog]')]
  .sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0] || null);

const 卡 = () => page.evaluate(() => {
  const 框 = [...document.querySelectorAll('[role=dialog]')]
    .sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
  if (!框) return [];
  const 候选 = Array.from(框.querySelectorAll('[class*="bg-canvas-controls-hover"]'))
    .filter((e) => e.classList.contains('hover:bg-canvas-controls-hover'));
  return 候选.filter((e) => !候选.some((o) => o !== e && e.contains(o)))
    .map((e) => {
      const r = e.getBoundingClientRect();
      if (r.width < 150 || r.height < 190) return null;
      return {
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
        文字: (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 40),
        按钮: Array.from(e.querySelectorAll('button')).map((b) => {
          const br = b.getBoundingClientRect();
          return { aria: b.getAttribute('aria-label'), box: [Math.round(br.left), Math.round(br.top), Math.round(br.width), Math.round(br.height)], 中心: [Math.round(br.left + br.width / 2), Math.round(br.top + br.height / 2)], op: getComputedStyle(b).opacity };
        }),
      };
    }).filter(Boolean);
});

/** 广场面板当前状态：页签高亮 / 空态文案 / 卡片数 / 详情按钮数 */
const 广场状态 = async (标签) => {
  const s = await page.evaluate(() => {
    const 框 = [...document.querySelectorAll('[role=dialog]')]
      .sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
    if (!框) return null;
    const 页签 = [...框.querySelectorAll('button')].filter((b) => ['特效广场', '风格广场', '我的收藏', '最近使用'].includes((b.innerText || '').trim()))
      .map((b) => ({ t: (b.innerText || '').trim(), 选中: b.getAttribute('data-active') !== null || /白|亮|bg-\[/.test(b.className) ? true : (b.className.includes('bg-canvas') ? true : false), cls: b.className.slice(0, 50) }));
    const 空态 = [...框.querySelectorAll('div,p,span')].filter((e) => e.children.length === 0 && /暂无|没有|空/.test((e.innerText || '')))
      .map((e) => (e.innerText || '').trim()).slice(0, 5);
    const 候选 = Array.from(框.querySelectorAll('[class*="bg-canvas-controls-hover"]')).filter((e) => e.classList.contains('hover:bg-canvas-controls-hover'));
    const 真卡 = 候选.filter((e) => !候选.some((o) => o !== e && e.contains(o)) && e.getBoundingClientRect().width >= 150 && e.getBoundingClientRect().height >= 190);
    return {
      页签, 空态,
      卡片数: 真卡.length,
      详情数: [...框.querySelectorAll('button[aria-label="详情"]')].length,
      收藏星: [...框.querySelectorAll('button[aria-label="收藏"]')].length,
      全文: (框.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 260),
    };
  });
  记(`【${标签}】卡片 ${s && s.卡片数}；详情按钮 ${s && s.详情数}；收藏星 ${s && s.收藏星}；空态 ${JSON.stringify(s && s.空态)}`);
  记(`        页签：${JSON.stringify(s && s.页签)}`);
  return s;
};

const 找页签 = (名) => page.evaluate((w) => {
  const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').trim() === w);
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
}, 名);

const 开广场 = async (入口名) => {
  await page.mouse.move(676, 773); await page.waitForTimeout(400);
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(1000);
  await page.mouse.move(720, 300); await page.waitForTimeout(500);
  const 入口 = await page.evaluate((w) => {
    const all = [...document.querySelectorAll('div')].filter((e) => {
      const r = e.getBoundingClientRect();
      if (r.left < 555 || r.left > 800 || r.top < 545 || r.top > 745) return false;
      if (getComputedStyle(e).cursor !== 'pointer') return false;
      return (e.innerText || '').trim().startsWith(w);
    }).map((e) => ({ r: e.getBoundingClientRect() })).sort((a, b) => (b.r.width * b.r.height) - (a.r.width * a.r.height));
    if (!all.length) return null;
    const r = all[0].r;
    return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
  }, 入口名);
  if (!入口) throw new Error('找不到入口 ' + 入口名);
  await 点击(入口, 入口名);
  let 开了 = false;
  for (let 轮 = 0; 轮 < 3 && !开了; 轮++) {
    await page.waitForTimeout(1200);
    const 门 = await page.evaluate(() => {
      const 框 = [...document.querySelectorAll('[role=dialog]')].sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
      if (!框) return { d: 0, c: 0 };
      const 候选 = Array.from(框.querySelectorAll('[class*="bg-canvas-controls-hover"]')).filter((e) => e.classList.contains('hover:bg-canvas-controls-hover'));
      return { d: 1, c: 候选.filter((e) => e.getBoundingClientRect().width >= 150 && e.getBoundingClientRect().height >= 190).length };
    });
    开了 = 门.d > 0 && 门.c > 0;
    if (!开了) { 记(`  第 ${轮 + 1} 次点入口没开（c=${门.c}），重试`); await page.keyboard.press('Escape'); await page.waitForTimeout(600); await 点击(676, 773); await 点击(入口, 入口名); }
  }
  if (!开了) throw new Error('点完「' + 入口名 + '」广场始终没开');
  await page.mouse.move(720, 120);
  await page.waitForTimeout(800);
};

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  // ================= 特效广场 =================
  await 开广场('特效库');
  结果.读数.特效广场 = await 广场状态('特效广场·默认');
  await page.screenshot({ path: EVID + 'ey4-特效广场.png' });
  记('已拍 ey4-特效广场.png');

  // ---- 我的收藏 ----
  const 收藏页签 = await 找页签('我的收藏');
  if (!收藏页签) throw new Error('找不到「我的收藏」页签');
  await 点击(收藏页签, '我的收藏');
  结果.读数.特效广场.我的收藏 = await 广场状态('特效广场·我的收藏');
  await page.screenshot({ path: EVID + 'ey4-特效-我的收藏-空.png' });
  记('已拍 ey4-特效-我的收藏-空.png');

  // ---- 最近使用 ----
  const 最近页签 = await 找页签('最近使用');
  if (!最近页签) throw new Error('找不到「最近使用」页签');
  await 点击(最近页签, '最近使用');
  结果.读数.特效广场.最近使用 = await 广场状态('特效广场·最近使用');
  await page.screenshot({ path: EVID + 'ey4-特效-最近使用.png' });
  记('已拍 ey4-特效-最近使用.png');

  // ---- 回特效广场，收藏一张，再读我的收藏 ----
  await 点击(收藏页签, '我的收藏');
  const 广场页签 = await 找页签('特效广场');
  await 点击(广场页签, '特效广场');
  const 卡列表 = await 卡();
  记('回到特效广场，真卡片 ' + 卡列表.length + ' 张');
  const 星 = 卡列表[0]?.按钮.find((b) => b.aria === '收藏');
  if (!星) throw new Error('第一张卡上没有「收藏」按钮');
  await page.mouse.move(星.中心[0], 星.中心[1]);
  await page.waitForTimeout(500);
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(1800);
  await page.mouse.move(720, 780); await page.waitForTimeout(600);
  const toast = await page.evaluate(() => [...document.querySelectorAll('div')]
    .filter((e) => e.children.length === 0 && /收藏/.test(e.innerText || '') && e.getBoundingClientRect().top > 600)
    .map((e) => (e.innerText || '').trim()).slice(0, 4));
  记('收藏后 toast：' + JSON.stringify(toast));
  await page.screenshot({ path: EVID + 'ey4-收藏成功.png' });
  记('已拍 ey4-收藏成功.png');

  await 点击(收藏页签, '我的收藏');
  结果.读数.特效广场.收藏后 = await 广场状态('特效广场·我的收藏（收藏 1 张之后）');
  await page.screenshot({ path: EVID + 'ey4-特效-我的收藏-有1张.png' });
  记('已拍 ey4-特效-我的收藏-有1张.png');

  // ---- ⛔ 复原：取消收藏 ----
  const 卡列表2 = await 卡();
  const 星2 = 卡列表2[0]?.按钮.find((b) => b.aria === '收藏' || b.aria === '取消收藏');
  记('收藏页里那张卡的按钮：' + JSON.stringify(卡列表2[0]?.按钮));
  if (星2) {
    await page.mouse.move(星2.中心[0], 星2.中心[1]);
    await page.waitForTimeout(500);
    await page.mouse.down(); await page.mouse.up();
    await page.waitForTimeout(1800);
    await page.mouse.move(720, 780); await page.waitForTimeout(600);
    const toast2 = await page.evaluate(() => [...document.querySelectorAll('div')]
      .filter((e) => e.children.length === 0 && /收藏/.test(e.innerText || '') && e.getBoundingClientRect().top > 600)
      .map((e) => (e.innerText || '').trim()).slice(0, 4));
    记('取消收藏后 toast：' + JSON.stringify(toast2));
  } else {
    记('⛔ 收藏页那张卡上没找到收藏/取消收藏按钮，未复原');
  }
  结果.读数.特效广场.取消收藏后 = await 广场状态('特效广场·我的收藏（取消收藏之后）');
  await page.screenshot({ path: EVID + 'ey4-特效-我的收藏-复原.png' });
  记('已拍 ey4-特效-我的收藏-复原.png');

  await page.keyboard.press('Escape');
  await page.waitForTimeout(1200);

  // ================= ⭐ 阳性对照：风格广场 =================
  await 开广场('风格库');
  结果.读数.风格广场 = await 广场状态('风格广场·默认');
  const 风收藏 = await 找页签('我的收藏');
  await 点击(风收藏, '我的收藏');
  结果.读数.风格广场.我的收藏 = await 广场状态('风格广场·我的收藏');
  await page.screenshot({ path: EVID + 'ey4-风格-我的收藏.png' });
  记('已拍 ey4-风格-我的收藏.png');

  await page.keyboard.press('Escape');
  await page.waitForTimeout(1000);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1000);
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
  console.log('\n=== 已写 tools/batchEY4.json ===');
}
