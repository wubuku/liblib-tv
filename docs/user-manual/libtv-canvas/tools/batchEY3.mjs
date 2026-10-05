// Batch EY-3：⭐⭐⭐ `⋯` 菜单是不是 `lensDetail` 的入口？
//
// EY-2 已经把最强的一条阴性钉死了：
// **全页文本级搜「详情」= 0**（不是「可见 0 枚」，是连 DOM 里都没有）。
// 比 Batch BO 的「可见详情按钮 0 枚」强一档 —— BO 那次没排除「按钮在但藏起来了」。
//
// 剩下**唯一没试过的一条路**：特效卡左上角那枚常驻 `⋯`。
// 风格卡上是模型徽标/`✧`，特效卡上是 `⋯`（BO 记的 12/12）。
// 如果 `lensDetail` 真有入口，最可能就是它。
//
// ⭐⭐ **本轮自带阳性对照**：同一会话、同一套检测器，最后去风格广场数一遍 `详情` 按钮。
//    读数 >0 ⇒ 特效广场那个 0 是真的 0，不是检测器坏了。
//
// ⛔ 绝不点卡片本体（= 新建节点）。只点 `⋯` 本身。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEY3.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

/** 广场面板里的卡片：`hover:bg-canvas-controls-hover.group.relative` */
const 卡诊断 = () => page.evaluate(() => ({
  dialog: document.querySelectorAll('[role=dialog]').length,
  卡数: (() => {
    const 框 = [...document.querySelectorAll('[role=dialog]')]
      .sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
    return 框 ? [...框.querySelectorAll('[class*="bg-canvas-controls-hover"]')].filter((e) => { const r = e.getBoundingClientRect(); return r.width >= 120 && r.height >= 150; }).length : 0;
  })(),
  全页该类: document.querySelectorAll('.hover\\:bg-canvas-controls-hover').length,
  页签: [...document.querySelectorAll('button')].map((b) => (b.innerText || '').trim()).filter((t) => ['特效广场', '风格广场', '我的收藏', '最近使用'].includes(t)),
}));
// ⚠️⚠️ 第三版才写对：`hover:bg-canvas-controls-hover` 这个 Tailwind 类
// **画布上本来就有 30 个**（不点开广场也有）——全局查会把它们算成「卡片」。
// ⇒ 卡片判据必须**收进 `[role=dialog]` 里**，再叠尺寸下限（广场卡 `191×240`）。
const 卡 = () => page.evaluate(() => {
  const 框 = [...document.querySelectorAll('[role=dialog]')]
    .sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
  if (!框) return [];
  // `[class*="…"]` 会把**卡片的内层容器**一起算进来（实测 42 = 12~14 张 × 3 层）。
  // ⇒ 改成**按 classList 精确 contains** + 尺寸 `191×240` 那一档 + **排除内含同类元素的**。
  const 候选 = Array.from(框.querySelectorAll('[class*="bg-canvas-controls-hover"]'))
    .filter((e) => e.classList.contains('hover:bg-canvas-controls-hover'));
  return 候选
    .filter((e) => !候选.some((o) => o !== e && e.contains(o)))
    .map((e) => {
    const r = e.getBoundingClientRect();
    if (r.width < 150 || r.height < 190) return null;
    return {
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      文字: (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 40),
      按钮: Array.from(e.querySelectorAll('button')).map((b) => {
        const br = b.getBoundingClientRect();
        return {
          aria: b.getAttribute('aria-label'), title: b.getAttribute('title'),
          文字: (b.innerText || '').trim().slice(0, 12),
          box: [Math.round(br.left), Math.round(br.top), Math.round(br.width), Math.round(br.height)],
          中心: [Math.round(br.left + br.width / 2), Math.round(br.top + br.height / 2)],
          svg数: b.querySelectorAll('svg').length,
          path: (b.querySelector('path')?.getAttribute('d') || '').slice(0, 36),
          op: getComputedStyle(b).opacity,
          dis: b.disabled === true,
        };
      }),
    };
  }).filter(Boolean);
});

/** 全页搜一个词（文本级，不限可交互） */
const 搜词 = (词) => page.evaluate((w) => Array.from(document.querySelectorAll('*'))
  .filter((e) => {
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    const own = Array.from(e.childNodes).some((n) => n.nodeType === 3 && n.textContent.includes(w));
    return own;
  })
  .map((e) => {
    const r = e.getBoundingClientRect();
    return { tag: e.tagName.toLowerCase(), aria: e.getAttribute('aria-label'), cls: (e.getAttribute('class') || '').slice(0, 60), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }), 词);

/** 枚举 aria 带某个词的按钮 */
const 按钮数 = (词) => page.evaluate((w) => Array.from(document.querySelectorAll('button'))
  .filter((b) => (b.getAttribute('aria-label') || '').includes(w) || (b.innerText || '').includes(w))
  .map((b) => {
    const r = b.getBoundingClientRect();
    return { aria: b.getAttribute('aria-label'), 文字: (b.innerText || '').trim().slice(0, 12), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], vis: r.width > 0 };
  }), 词);

/** ⭐⭐⭐ 全脚本**唯一**的点击入口：先 `mouse.move` 回目标 → 自证落点 → 才 `down/up`。
 *
 * 本轮前四版全栽在同一处：查完入口坐标后为了「清场」把指针移到 (720,300)，
 * 然后**直接 `mouse.down()`** —— 点的是画布，广场当然不开，连续两轮都报「点完入口没开」。
 * ⛔ 更要命的是 `elementFromPoint(入口)` **照样返回「特效库」**：
 * 它验的是「那个坐标上是什么」，**验不出「鼠标此刻根本不在那儿」**。
 * ⇒ 自证必须紧跟在一次真实的 `mouse.move` 之后，中间不许插任何别的动作。
 */
const 自证 = (中心, 必须含) => page.evaluate(([x, y, w]) => {
  const e = document.elementFromPoint(x, y);
  if (!e) return null;
  const b = e.closest('button,[role=button]');
  const 文字 = (b?.innerText || e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 30);
  return { tag: e.tagName, 文字, aria: b?.getAttribute('aria-label') || null, 命中: (文字 + (b?.getAttribute('aria-label') || '')).includes(w) };
}, [中心[0], 中心[1], 必须含]);

const 点击 = async (中心, 必须含) => {
  await page.mouse.move(中心[0], 中心[1]);
  await page.waitForTimeout(400);
  const v = await 自证(中心, 必须含);
  if (!v || !v.命中) throw new Error(`落点自证失败：期望含「${必须含}」，实得 ${JSON.stringify(v)}`);
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(1400);
  await page.mouse.move(720, 780);
  await page.waitForTimeout(600);
  return v;
};

const 开广场 = async (入口名) => {
  await page.mouse.move(676, 773);
  await page.waitForTimeout(400);
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(1000);
  await page.mouse.move(720, 300);
  await page.waitForTimeout(500);
  // ⛔ 连续两次按「外层 222×52 容器」找入口都报「找不到入口 特效库」。
  //    dbg-flyout 实测：浮层里**带 `cursor:pointer` 的只有内层**
  //    （`112×36` / `164×19`，left 615），外层那一行 `222×52` 自己**没有 pointer 光标**
  //    —— EY-2 那次读到它是靠「**宽度 × 高度都不小于阈值**」兜底混进来的。
  //    ⇒ 判据写成「浮层区域里 cursor:pointer 且文字以入口名开头，取面积最大的一个」。
  const 入口 = await page.evaluate((w) => {
    const all = [...document.querySelectorAll('div')].filter((e) => {
      const r = e.getBoundingClientRect();
      if (r.left < 555 || r.left > 800 || r.top < 545 || r.top > 745) return false;
      if (getComputedStyle(e).cursor !== 'pointer') return false;
      if (!(e.innerText || '').trim().startsWith(w)) return false;
      return e.querySelector('div') === null || true;
    }).map((e) => ({ e, r: e.getBoundingClientRect() }))
      .sort((a, b) => (b.r.width * b.r.height) - (a.r.width * a.r.height));
    if (!all.length) return null;
    const r = all[0].r;
    return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
  }, 入口名);
  if (!入口) throw new Error('找不到入口 ' + 入口名);
  await 点击(入口, 入口名);
  // ⭐⭐ **点完入口 ≠ 广场开了** ⇒ 必须轮询读门牌，不能假设点击生效。
  let 开了 = false;
  for (let 轮 = 0; 轮 < 4 && !开了; 轮++) {
    await page.waitForTimeout(1200);
    const 门 = await page.evaluate(() => ({
      dialog: document.querySelectorAll('[role=dialog]').length,
      卡片: (() => {
        const 框 = [...document.querySelectorAll('[role=dialog]')]
          .sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
        if (!框) return 0;
        return [...框.querySelectorAll('[class*="bg-canvas-controls-hover"]')]
          .filter((e) => { const r = e.getBoundingClientRect(); return r.width >= 120 && r.height >= 150; }).length;
      })(),
    }));
    开了 = 门.dialog > 0 && 门.卡片 > 0;
    if (!开了) {
      记(`  第 ${轮 + 1} 次点入口后广场没开（dialog=${门.dialog} 卡=${门.卡片}），重试`);
      await page.keyboard.press('Escape');
      await page.waitForTimeout(600);
      await page.mouse.move(720, 300); await page.waitForTimeout(300);
      await 点击(676, 773);
      await 点击(入口, 入口名);
    }
  }
  await page.mouse.move(720, 120);
  await page.waitForTimeout(800);
  if (!开了) throw new Error('点完「' + 入口名 + '」广场始终没开');
  // ⭐⭐⭐ 新增判据自证：**点了入口 ≠ 广场开了。**
  // 第一版打完入口就往下走，结果 `卡()` 读到 0 张卡，日志却说「已开特效广场」——
  // 那是**假设点击生效**，不是读数。⇒ 每次开完广场必须自己验一遍门牌。
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

  // ============ 特效广场 ============
  await 开广场('特效库');
  记('已开特效广场');
  记('开完门牌自证：' + JSON.stringify(await 卡诊断()));
  结果.读数.特效广场 = {};
  const 卡列表0 = await 卡();
  记(`⭐ 视口内真卡片 ${卡列表0.length} 张`);
  结果.读数.特效广场.卡片 = 卡列表0;

  const 详情0 = await 按钮数('详情');
  const 详情文本0 = await 搜词('详情');
  记(`特效广场：aria/文字含「详情」的按钮 ${详情0.length} 个；自有文本节点含「详情」的元素 ${详情文本0.length} 个`);

  // ---- 第一张卡上的按钮点名 ----
  const c0 = 卡列表0[0];
  记('第 1 张卡：' + JSON.stringify(c0.文字) + ' box=' + JSON.stringify(c0.box));
  记('   卡内按钮：' + JSON.stringify(c0.按钮));

  // ---- 悬停显形（不点）----
  await page.mouse.move(c0.box[0] + 95, c0.box[1] + 95);
  await page.waitForTimeout(900);
  const 悬停后 = await 卡();
  const c0h = 悬停后.find((c) => Math.abs(c.box[0] - c0.box[0]) < 3 && Math.abs(c.box[1] - c0.box[1]) < 3);
  记('悬停后该卡按钮：' + JSON.stringify(c0h && c0h.按钮));
  await page.screenshot({ path: EVID + 'ey3-特效卡悬停.png', clip: { x: c0.box[0] - 6, y: c0.box[1] - 6, width: 203, height: 252 } });
  记('已拍 ey3-特效卡悬停.png');
  const 详情悬停 = await 按钮数('详情');
  记('悬停后 aria 含「详情」的按钮：' + JSON.stringify(详情悬停));

  // ---- 点 `⋯` ----
  const 省略 = (c0h?.按钮 || []).find((b) => b.box[0] < c0.box[0] + 30 && b.box[1] < c0.box[1] + 30);
  if (!省略) {
    记('⛔ 卡上找不到 `⋯`，本轮到此为止');
  } else {
    记(`点 \\u22ef 前：${JSON.stringify(省略)}`);
    const 前 = await page.evaluate(() => document.body.innerHTML.length);
    const v = await 自证(省略.中心, '');
    记('⋯ 自证=' + JSON.stringify(v));
    // 这里不能带文本要求（⋯ 是纯图标），只要求落点确实是一个按钮
    const 是按钮 = await page.evaluate(([x, y]) => !!document.elementFromPoint(x, y)?.closest('button'), 省略.中心);
    记('⋯ 落点是 button：' + 是按钮);
    if (是按钮) {
      await page.mouse.move(省略.中心[0], 省略.中心[1]);
      await page.waitForTimeout(450);
      await page.mouse.down(); await page.mouse.up();
      await page.waitForTimeout(1200);
      await page.mouse.move(720, 780);
      await page.waitForTimeout(600);
      const 后 = await page.evaluate(() => document.body.innerHTML.length);
      记(`点 ⋯ 后 innerHTML 长度 ${前} -> ${后}`);
      // 菜单项：只列新出现的可见文字
      const 菜单项 = await page.evaluate(() => {
        const 出 = [];
        for (const e of document.querySelectorAll('[role=menuitem],[role=option],li,button,div')) {
          const r = e.getBoundingClientRect();
          if (r.width < 40 || r.height < 20 || r.height > 60) continue;
          const cs = getComputedStyle(e);
          if (cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) continue;
          if (e.querySelector('button') || e.querySelector('div')) continue;
          const t = (e.innerText || '').trim();
          if (!t || t.length > 20) continue;
          出.push({ tag: e.tagName.toLowerCase(), role: e.getAttribute('role'), t, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], cur: cs.cursor });
        }
        return 出;
      });
      记('⭐ ⋯ 菜单里的条目：');
      for (const m of 菜单项) 记(`   [${m.tag}${m.role ? '/' + m.role : ''}] "${m.t}" box=${JSON.stringify(m.box)} cursor=${m.cur}`);
      await page.screenshot({ path: EVID + 'ey3-省略号菜单.png' });
      记('已拍 ey3-省略号菜单.png');
      结果.读数.省略号菜单 = 菜单项;
      const 详情菜单 = await 搜词('详情');
      记('开 ⋯ 菜单后，全页文本含「详情」的元素：' + JSON.stringify(详情菜单));
      结果.读数.菜单里的详情 = 详情菜单;
    }
  }

  await page.keyboard.press('Escape');
  await page.waitForTimeout(800);

  // ---- 切「我的收藏」/「最近使用」----
  for (const 页签 of ['我的收藏', '最近使用']) {
    const 命中 = await page.evaluate((w) => {
      const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').trim() === w);
      if (!b) return null;
      const r = b.getBoundingClientRect();
      return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
    }, 页签);
    if (!命中) { 记(`切 ${页签}：按钮不存在`); continue; }
    try { await 点击(命中, 页签); } catch (e) { 记(`切 ${页签} 落点不对：${e.message}`); continue; }
    await page.mouse.move(720, 780);
    await page.waitForTimeout(600);
    const 卡n = (await 卡()).length;
    const d1 = await 按钮数('详情');
    const d2 = await 搜词('详情');
    记(`【${页签}】卡片 ${卡n} 张；aria 含「详情」按钮 ${d1.length} 个；文本含「详情」元素 ${d2.length} 个`);
    await page.screenshot({ path: EVID + `ey3-${页签}.png` });
    记(`已拍 ey3-${页签}.png`);
    结果.读数[页签] = { 卡片数: 卡n, 详情按钮: d1, 详情文本: d2 };
  }

  await page.keyboard.press('Escape');
  await page.waitForTimeout(1200);

  // ============ ⭐⭐⭐ 阳性对照：风格广场必须有详情 ============
  await 开广场('风格库');
  const 风格详情 = await 按钮数('详情');
  const 风格文本 = await 搜词('详情');
  const 风格卡 = await 卡();
  记(`⭐⭐⭐【阳性对照·风格广场】卡片 ${风格卡.length} 张；aria 含「详情」按钮 ${风格详情.length} 个；文本含「详情」元素 ${风格文本.length} 个`);
  记('   前 3 枚详情按钮：' + JSON.stringify(风格详情.slice(0, 3)));
  结果.读数.阳性对照 = { 卡片数: 风格卡.length, 详情按钮数: 风格详情.length, 样例: 风格详情.slice(0, 3) };

  await page.keyboard.press('Escape');
  await page.waitForTimeout(1200);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1200);
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
  console.log('\n=== 已写 tools/batchEY3.json ===');
}
