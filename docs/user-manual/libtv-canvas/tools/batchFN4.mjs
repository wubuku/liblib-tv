// ⭐⭐⭐⭐⭐ Batch FN-4：把 FN-3 的两个失败点修掉，再走完「素材库 → 风格广场」
//
// FN-3 实测出的两件事（都不是 bug，是产品行为）：
//   ① ⭐⭐ **Escape 关不掉素材库浮层**；再点一次底栏那枚「素材库」才关 —— 它是个**开关**。
//      FN-3 以为 Escape 关掉了、于是又点一次「素材库」，结果那次点的是**关闭**，浮层没了。
//   ② ⭐⭐⭐ 副标题 `新增风格节点` 的 class 是 **`text-fg-muted text-[12px] leading-snug opacity-0 transition-…`**
//      ⇒ **它默认是透明的，鼠标悬停上去才淡入**。
//      这解释了为什么文字对账脚本会漏掉它（`opacity<=0.01` 的元素被我过滤掉了），
//      也解释了为什么老截图里明明有这行字、而纯文本 dump 里没有。
//
// ⛔ 安全边界：只做面板/页签导航；⛔ 不点任何卡片。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFN4.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

let 断言次数 = 0, 失败 = 0;
const 断言 = (条件, 说明, 数据) => {
  断言次数++;
  if (!条件) { 失败++; 记('   ❌ 断言失败：' + 说明 + (数据 !== undefined ? '｜数据 ' + JSON.stringify(数据) : '')); return false; }
  记('   ✅ 断言通过：' + 说明);
  return true;
};

const 浏览器 = await launch();
const page = 浏览器.page;
const 归一 = (s) => (s || '').replace(/[\s　]+/g, '');

const 全页文字 = () => page.evaluate(() => {
  const 可见 = (el) => {
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) return false;
    const cs = getComputedStyle(el);
    return cs.visibility !== 'hidden' && cs.display !== 'none' && Number(cs.opacity) > 0.01;
  };
  const 集 = new Set();
  for (const el of document.querySelectorAll('body *')) {
    if (!可见(el)) continue;
    for (const n of el.childNodes) {
      if (n.nodeType === 3) { const t = (n.textContent || '').replace(/\s+/g, ' ').trim(); if (t) 集.add(t); }
    }
    for (const a of ['aria-label', 'title', 'placeholder', 'alt']) {
      const v = (el.getAttribute && el.getAttribute(a)) || '';
      if (v && v.trim()) 集.add(v.trim());
    }
  }
  return [...集];
});

const 点底栏 = async (aria) => {
  const b = await page.evaluate((a) => {
    for (const x of document.querySelectorAll('button')) {
      if ((x.getAttribute('aria-label') || '') !== a) continue;
      const r = x.getBoundingClientRect();
      if (!(r.width > 0 && r.top > 700)) continue;
      const cx = Math.round(r.left + r.width / 2), cy = Math.round(r.top + r.height / 2);
      const el = document.elementFromPoint(cx, cy);
      const btn = el && el.closest('button');
      return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 点: [cx, cy], 命中: btn ? btn.getAttribute('aria-label') : null };
    }
    return null;
  }, aria);
  if (!b) return false;
  if (b.命中 !== aria) { 记(`   ❌ 「${aria}」落点属主是 ${b.命中}，被挡住了`); return false; }
  await page.mouse.click(b.点[0], b.点[1]);
  await page.waitForTimeout(2500);
  return true;
};

const 在界面上 = async (词) => {
  const s = new Set((await 全页文字()).map(归一));
  return 词.every((m) => s.has(归一(m)));
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 110));
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);

  // ——— ① 素材库浮层是「开关」：Escape 不管用，再点一次才关 ———
  记('—— ① 开关行为 ——');
  断言(await 点底栏('素材库'), '打开素材库');
  断言(await 在界面上(['风格库', '特效库', '打开工具箱']), '三项都在');
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1500);
  const Esc后 = await 在界面上(['风格库']);
  断言(!Esc后, '⭐ Escape **关不掉**素材库浮层', Esc后);
  断言(await 点底栏('素材库'), '再点一次「素材库」');
  const 再点后 = await 在界面上(['风格库']);
  断言(!再点后, '⭐ 再点一次同一枚按钮才关得掉（它是开关）', 再点后);
  R.读数.开关行为 = { Escape能关: false, 再点一次能关: true };

  // ——— ② 副标题是悬停才淡出来的 ———
  记('—— ② 副标题的 opacity ——');
  断言(await 点底栏('素材库'), '再次打开');
  const 副标题前 = await page.evaluate(() => {
    for (const el of document.querySelectorAll('button,[role="button"]')) {
      if (!(el.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库')) continue;
      const sp = [...el.querySelectorAll('span')].find((s) => (s.innerText || '').includes('新增风格节点'));
      if (!sp) return null;
      return { 字: sp.innerText, opacity: getComputedStyle(sp).opacity, class: String(sp.className), transition: getComputedStyle(sp).transitionDuration };
    }
    return null;
  });
  记('   悬停前 ' + JSON.stringify(副标题前));
  const 风格库点 = [565 + 111, 563 + 26];
  await page.mouse.move(风格库点[0] - 60, 风格库点[1]);
  await page.waitForTimeout(300);
  await page.mouse.move(风格库点[0], 风格库点[1]);
  await page.waitForTimeout(1200);
  const 副标题后 = await page.evaluate(() => {
    for (const el of document.querySelectorAll('button,[role="button"]')) {
      if (!(el.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库')) continue;
      const sp = [...el.querySelectorAll('span')].find((s) => (s.innerText || '').includes('新增风格节点'));
      return sp ? { opacity: getComputedStyle(sp).opacity, transition: getComputedStyle(sp).transitionDuration } : null;
    }
    return null;
  });
  记('   悬停后 ' + JSON.stringify(副标题后));
  R.读数.副标题 = { 悬停前: 副标题前, 悬停后: 副标题后 };
  断言(副标题前 && 副标题后 && Number(副标题前.opacity) < 0.05 && Number(副标题后.opacity) > 0.5,
    '⭐⭐ 副标题「新增风格节点」默认 opacity 0、悬停才淡入', { 前: 副标题前?.opacity, 后: 副标题后?.opacity });
  await page.screenshot({ path: EVID + 'fn4-01-素材库-悬停出副标题.png' });

  // ——— ③ 真的走一遍广场 ———
  记('—— ③ 「风格库」→ 风格广场 ——');
  const 落点 = await page.evaluate(() => {
    for (const el of document.querySelectorAll('button,[role="button"]')) {
      const t = (el.innerText || '').replace(/\s+/g, ' ').trim();
      if (!t.startsWith('风格库')) continue;
      const r = el.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) continue;
      const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
      const hb = document.elementFromPoint(x, y)?.closest('button,[role="button"]');
      return { 点: [x, y], 命中: hb ? (hb.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14) : null };
    }
    return null;
  });
  记('   落点自证 ' + JSON.stringify(落点));
  断言(落点 && String(落点.命中 || '').startsWith('风格库'), '「风格库」的落点属主是它自己（CV-0 那次点成了特效库）', 落点);
  await page.mouse.click(落点.点[0], 落点.点[1]);
  await page.waitForTimeout(6000);
  const 广场词 = ['风格广场', '我的收藏', '最近使用', '推荐', '摄影写真', '电商营销', '动漫游戏', '风格插画', '平面设计', '建筑及室内设计', '创意玩法', '文创周边', '小说推文', '仅看可商用'];
  const ws = new Set((await 全页文字()).map(归一));
  const 命中词 = 广场词.filter((m) => ws.has(归一(m)));
  R.读数.风格广场 = { 命中: 命中词.length, 总: 广场词.length, 词: 命中词, 全页文字数: ws.size };
  记(`   ⭐ 风格广场命中 ${命中词.length}/${广场词.length}：${命中词.join(' ')}`);
  断言(命中词.length >= 5, '⭐⭐ 风格广场真的开了 —— FI 的「广场入口不可达」正式作废', 命中词);
  await page.screenshot({ path: EVID + 'fn4-02-风格广场.png' });

  // 我的收藏（只切页签）
  const 收藏 = await page.evaluate(() => {
    for (const el of document.querySelectorAll('button,[role="button"]')) {
      if ((el.innerText || '').replace(/\s+/g, '').trim() !== '我的收藏') continue;
      const r = el.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) continue;
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    }
    return null;
  });
  if (收藏) {
    await page.mouse.click(收藏[0], 收藏[1]);
    await page.waitForTimeout(4000);
    const 文字 = (await 全页文字()).map(归一);
    R.读数.我的收藏 = { 全页文字: 文字.length, 广场区候选: 文字.filter((t) => t.length >= 2 && t.length <= 24).slice(0, 40) };
    记('   我的收藏：全页 ' + 文字.length + ' 条');
    await page.screenshot({ path: EVID + 'fn4-03-风格广场-我的收藏.png' });
  }
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);

  // ——— ④ 添加节点面板里那一行 ———
  记('—— ④ 添加节点面板里的「素材库」——');
  断言(await 点底栏('添加节点'), '打开添加节点面板');
  const 行 = await page.evaluate(() => {
    for (const el of document.querySelectorAll('button,[role="button"],li,div')) {
      const t = (el.innerText || '').replace(/\s+/g, '').trim();
      if (!t.startsWith('素材库')) continue;
      const r = el.getBoundingClientRect();
      if (!(r.width > 40 && r.height > 10 && r.top > 200 && r.top < 740)) continue;
      return { tag: el.tagName, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 文字: t.slice(0, 16) };
    }
    return null;
  });
  记('   面板里那一行 ' + JSON.stringify(行));
  if (行) {
    await page.mouse.click(行.框[0] + 30, 行.框[1] + 行.框[3] / 2);
    await page.waitForTimeout(3000);
    const r2 = { 风格库: await 在界面上(['风格库']), 特效库: await 在界面上(['特效库']), 工具箱: await 在界面上(['打开工具箱']) };
    R.读数.添加节点里的素材库 = r2;
    断言(r2.风格库 && r2.工具箱, '添加节点面板里那一行点开也是同一个三项浮层', r2);
    await page.screenshot({ path: EVID + 'fn4-04-添加节点里的素材库.png' });
  }

  记(`—— 共跑了 ${断言次数} 条断言，失败 ${失败} 条 ——`);
} catch (e) {
  记('❌ ' + (e && e.message ? e.message : String(e)));
} finally {
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}
