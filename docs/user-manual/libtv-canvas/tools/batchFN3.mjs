// ⭐⭐⭐⭐⭐ Batch FN-3：⛔ **撤回 Batch FI 的结论**——广场入口不是不可达，是 FI 的判据失效
//
// FN-2 已经证明：底栏「素材库」点开是一个**浮层**，里面有
//   `风格库 NEW` / `特效库 NEW` / `打开工具箱`
// 而 FI（`921095cc`）写进 asset-library.md 的是「两处都空空如也，广场三项没出现」。
// ⛔ 那不是账号状态差异，是**点的时候面板被上一个面板盖住了**（缺陷 449）。
//
// FN-3 做三件事：
//   ① 精确读数：三项逐条的 box / innerText / 子结构（副标题还在不在）
//   ② **真的走一遍** `底栏素材库 → 风格库 → 风格广场`，看广场到底能不能开
//   ③ 另一条路径复核：添加节点面板里那一行点开是不是同一个浮层
//
// ⛔ 安全边界：只做**面板/页签导航**，⛔ 不点任何卡片（点卡片 = 新建节点）。
import { launch, closePromos, ORIGIN, shotHighlighted, injectHighlight, HIGHLIGHT_JS } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFN3.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

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

/** 落点自证 + 点：只有 elementFromPoint 读回同一个按钮才算点得中（缺陷 449 治法）。 */
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
  if (b.命中 !== aria) { 记(`   ❌ 「${aria}」落点被别的元素挡住了（属主 ${b.命中}）`); return false; }
  await page.mouse.click(b.点[0], b.点[1]);
  await page.waitForTimeout(2500);
  return true;
};

/** 素材库浮层：把三项逐条量出来。 */
const 量素材库 = () => page.evaluate(() => {
  const 归 = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const 可见 = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const 三项 = ['风格库', '特效库', '打开工具箱'];
  const out = [];
  for (const 名 of 三项) {
    // ⭐ 缺陷 155 的治法：先按可点元素筛，文字只做二次确认；⛔ 不要用「文字前缀」扫全部元素
    for (const el of document.querySelectorAll('button,[role="button"],a')) {
      if (!可见(el)) continue;
      const t = 归(el.innerText);
      if (!t.startsWith(名)) continue;
      const r = el.getBoundingClientRect();
      out.push({
        名,
        框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        innerText: t,
        aria: el.getAttribute('aria-label'),
        title: el.getAttribute('title'),
        子节点: [...el.querySelectorAll('*')].filter((c) => c.childNodes.length && [...c.childNodes].some((n) => n.nodeType === 3 && 归(n.textContent))).map((c) => ({ tag: c.tagName, class: String(c.className || '').slice(0, 60), 字: 归(c.innerText).slice(0, 30) })).slice(0, 8),
      });
      break;
    }
  }
  // 浮层外壳
  const 行 = out[0] ? out[0].框[1] : null;
  const 壳 = [...document.querySelectorAll('div')].filter((el) => {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return r.width > 160 && r.width < 600 && r.height > 120 && r.height < 500 && r.bottom > 700 && cs.position === 'absolute' && el.innerText && el.innerText.includes('风格库') && el.innerText.includes('打开工具箱');
  }).map((el) => { const r = el.getBoundingClientRect(); return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], class: String(el.className || '').slice(0, 120), z: getComputedStyle(el).zIndex, 标题: 归(el.innerText).split('\n')[0] }; }).sort((a, b) => a.框[2] * a.框[3] - b.框[2] * b.框[3])[0] || null;
  return { 三项: out, 壳, 行 };
});

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 110));
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);

  // ——— ① 底栏素材库 → 精确读数 ———
  记('—— ① 底栏「素材库」——');
  断言(await 点底栏('素材库'), '「素材库」点得中（落点自证通过）');
  let w = new Set((await 全页文字()).map(归一));
  断言(['风格库', '特效库', '打开工具箱'].every((m) => w.has(归一(m))), '⭐ 三项全在界面上 —— 推翻 FI 的「空空如也」', [...w].filter((t) => /风格库|特效库|工具箱/.test(t)));
  const 量 = await 量素材库();
  R.读数.素材库三项 = 量;
  记('   ' + JSON.stringify(量, null, 1).slice(0, 2000));
  await injectHighlight(page).catch(() => {});
  await page.screenshot({ path: EVID + 'fn3-01-素材库浮层.png' });

  // ——— ② Escape 能不能关掉这个浮层 ———
  const 前 = await 全页文字();
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1500);
  const 后 = new Set((await 全页文字()).map(归一));
  const 还在 = 后.has(归一('风格库'));
  R.读数.Escape关浮层 = { 关掉: !还在 };
  断言(!还在, 'Escape 能关掉素材库浮层（与角色造型室不同：那个 Escape 关不掉）', 前.length);
  await page.waitForTimeout(800);

  // ——— ③ ⭐ 真的走一遍：素材库 → 风格库 → 风格广场 ———
  记('—— ③ 走「风格库」进广场（⛔ 不点任何卡片）——');
  断言(await 点底栏('素材库'), '重新打开素材库');
  const 风格库点 = await page.evaluate(() => {
    for (const el of document.querySelectorAll('button,[role="button"]')) {
      const t = (el.innerText || '').replace(/\s+/g, ' ').trim();
      if (!t.startsWith('风格库')) continue;
      const r = el.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) continue;
      const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
      const hit = document.elementFromPoint(x, y);
      const hb = hit && hit.closest('button,[role="button"]');
      return { 点: [x, y], 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 命中文字: hb ? (hb.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) : null };
    }
    return null;
  });
  记('   风格库落点 ' + JSON.stringify(风格库点));
  断言(风格库点 && String(风格库点.命中文字 || '').startsWith('风格库'), '「风格库」的落点属主是它自己（CV-0 那次点成了「特效库」）', 风格库点);
  await page.mouse.click(风格库点.点[0], 风格库点.点[1]);
  await page.waitForTimeout(5000);
  w = new Set((await 全页文字()).map(归一));
  const 广场词 = ['风格广场', '我的收藏', '最近使用', '推荐', '摄影写真', '电商营销', '动漫游戏', '风格插画', '平面设计', '建筑及室内设计', '创意玩法', '文创周边', '小说推文', '仅看可商用'];
  const 广场命中 = 广场词.filter((m) => w.has(归一(m)));
  R.读数.风格广场 = { 命中: 广场命中.length, 总: 广场词.length, 样本: 广场命中 };
  断言(广场命中.length >= 5, '⭐⭐ 风格广场**真的开了**，FI 的「广场入口不可达」正式作废', 广场命中);
  await page.screenshot({ path: EVID + 'fn3-02-风格广场.png' });

  // 我的收藏（只切页签，不点卡片）
  const 收藏页签 = await page.evaluate(() => {
    for (const el of document.querySelectorAll('button,[role="button"]')) {
      if ((el.innerText || '').replace(/\s+/g, '').trim() !== '我的收藏') continue;
      const r = el.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) continue;
      return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    }
    return null;
  });
  if (收藏页签) {
    await page.mouse.click(收藏页签[0], 收藏页签[1]);
    await page.waitForTimeout(3500);
    const 收藏文字 = (await 全页文字()).map(归一).filter((t) => t.length < 40);
    R.读数.我的收藏 = { 命中数: 收藏文字.length, 样本: 收藏文字.filter((t) => !/^[\d\s.%]+$/.test(t)).slice(0, 30) };
    记('   我的收藏页命中 ' + 收藏文字.length + ' 条：' + 收藏文字.filter((t) => !/^[\d\s.%]+$/.test(t)).slice(0, 18).join(' | '));
    await page.screenshot({ path: EVID + 'fn3-03-风格广场-我的收藏.png' });
  } else 记('   ⛔ 找不到「我的收藏」页签');
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);

  // ——— ④ 另一条路径：添加节点面板里的「素材库」 ———
  记('—— ④ 复核「添加节点」面板里那一行 ——');
  断言(await 点底栏('添加节点'), '打开添加节点面板');
  const 行 = await page.evaluate(() => {
    for (const el of document.querySelectorAll('button,[role="button"],[data-menu-item],li,div')) {
      const t = (el.innerText || '').replace(/\s+/g, '').trim();
      if (!t.startsWith('素材库')) continue;
      const r = el.getBoundingClientRect();
      if (!(r.width > 40 && r.height > 10 && r.top > 200 && r.top < 740)) continue;
      return { tag: el.tagName, class: String(el.className || '').slice(0, 50), 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 文字: t.slice(0, 20) };
    }
    return null;
  });
  记('   添加节点面板里的「素材库」行 ' + JSON.stringify(行));
  if (行) {
    await page.mouse.click(行.框[0] + 30, 行.框[1] + 行.框[3] / 2);
    await page.waitForTimeout(2500);
    const 后 = new Set((await 全页文字()).map(归一));
    R.读数.添加节点里的素材库 = { 打开风格库: 后.has(归一('风格库')), 打开特效库: 后.has(归一('特效库')), 打开工具箱: 后.has(归一('打开工具箱')) };
    断言(后.has(归一('风格库')) || 后.has(归一('打开工具箱')), '添加节点面板里那一行点开也是同一个三项浮层', R.读数.添加节点里的素材库);
    await page.screenshot({ path: EVID + 'fn3-04-添加节点里的素材库.png' });
  }

  记(`—— 共跑了 ${断言次数} 条断言，失败 ${失败} 条 ——`);
} catch (e) {
  记('❌ ' + (e && e.message ? e.message : String(e)));
} finally {
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}
