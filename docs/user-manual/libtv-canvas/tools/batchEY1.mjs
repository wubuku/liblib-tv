// Batch EY-1：⭐⭐ 正面结掉 `特效详情` / `lensDetail` 这条 📖。
//
// 现状：i18n 文案表里有 `特效详情`（key `lensDetail`），但**界面上从没捕捉到**。
// 手册里有一句相关记录：「特效广场的卡**没有** `⤢ 详情`，而且 12/12 张全是多模型卡」。
//
// ⭐ 那条 12/12 的样本太小。本轮正面回答两个问题：
//   ① **到底存不存在单模型特效卡？**（`baseType` 长度 1）
//      · 不存在 ⇒ 每一张都多模型 ⇒ 「没有 `⤢ 详情」」是**必然**，`lensDetail` 也就没有入口；
//      · 存在  ⇒ 得去看那张卡到底有没有 `⤢`，`lensDetail` 可能只是没点开过。
//   ② **每张特效卡上到底有哪些可交互元素？**（不只看 `⤢`）
//      万一详情藏在别的图标后面，只查 `⤢` 就会漏。
//
// ⛔ **绝不点卡片本体** —— 手册实测过「点卡片本体」= 直接**新建一个节点**（画布 12→13）。
//    本轮**只读不点卡片**，只在抽屉内部切页签。
//
// ⭐ 阳性/对照：同一个抽屉里的 `风格广场` 是已知能出 `⤢ 详情` 的，
//    同一套手法在那边能读到，两边一比才有意义。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEY1.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

/** 点底栏那枚「素材库」—— 按 aria 定位并自证 */
const 开素材库 = async () => {
  const p = await page.evaluate(() => {
    for (const e of document.querySelectorAll('button')) {
      if (e.getAttribute('aria-label') !== '素材库') continue;
      const r = e.getBoundingClientRect();
      if (r.width < 8) continue;
      return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
    }
    return null;
  });
  if (!p) return { ok: false };
  const 验 = await page.evaluate(([x, y]) => document.elementFromPoint(x, y)?.closest('button')?.getAttribute('aria-label'), p);
  await page.mouse.click(p[0], p[1]);
  await page.waitForTimeout(2500);
  return { ok: 验 === '素材库', 点: p, 自证: 验 };
};

/** 在抽屉里按可见文字点页签 */
const 点文字 = async (t) => {
  const p = await page.evaluate((w) => {
    for (const e of document.querySelectorAll('button,[role="tab"],[role="button"],div,span')) {
      if (e.children.length) continue;
      if ((e.textContent || '').trim() !== w) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 8 || r.height < 8) continue;
      const b = e.closest('button,[role="tab"],[role="button"]') || e;
      const rb = b.getBoundingClientRect();
      return { 点: [Math.round(rb.left + rb.width / 2), Math.round(rb.top + rb.height / 2)], box: [Math.round(rb.left), Math.round(rb.top), Math.round(rb.width), Math.round(rb.height)] };
    }
    return null;
  }, t);
  if (!p) return { ok: false, 原因: '没找到「' + t + '」' };
  await page.mouse.click(p.点[0], p.点[1]);
  await page.waitForTimeout(2500);
  return { ok: true, ...p };
};

/** ⭐ 扫当前广场：每张卡上列出所有可交互元素 + 该卡列了几个模型 */
const 扫卡 = (page) => page.evaluate(() => {
  const 出 = [];
  // 卡片：挑「含有 ⤢ 或模型行」的那种网格子项
  // ⭐ 不猜 class：先枚举所有 button / [role=button]，再按几何聚成「每张卡」
  const 全部 = [...document.querySelectorAll('button,[role="button"],[role="tab"]')];
  const 可见 = 全部.filter((e) => {
    const r = e.getBoundingClientRect();
    return r.width > 6 && r.height > 6 && r.right > 0 && r.left < innerWidth && r.bottom > 0 && r.top < innerHeight;
  });
  for (const e of 可见) {
    const r = e.getBoundingClientRect();
    出.push({
      文字: (e.innerText || '').trim().slice(0, 22),
      aria: e.getAttribute('aria-label'),
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
      svg数: e.querySelectorAll('svg').length,
      path头: (() => { const p = e.querySelector('path'); return p ? String(p.getAttribute('d') || '').slice(0, 40) : null; })(),
      disabled: e.disabled === true,
    });
  }
  return 出;
});

/** 页面上有没有出现「详情」两个字（全文，不筛叶子） */
const 找详情 = (page) => page.evaluate(() => {
  const 命中 = [];
  for (const e of document.querySelectorAll('*')) {
    const t = (e.innerText || '').trim();
    if (!t || t.length > 40) continue;
    if (!/详情/.test(t)) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    命中.push({ 标签: e.tagName, 文字: t, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
  }
  return 命中;
});

try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) {
      const t = (b.innerText || '').trim();
      if (t === '知道了' || t === '开启') { try { b.click(); } catch (e) {} }
    }
  });
  await page.waitForTimeout(1200);

  const 开 = await 开素材库();
  记('开素材库：' + JSON.stringify(开));
  if (!开.ok) throw new Error('开不了素材库');
  await page.screenshot({ path: EVID + 'ey1-素材库打开.png' });
  记('已拍 ey1-素材库打开.png');

  // 页签清单
  const 页签 = await page.evaluate(() => {
    const 出 = [];
    for (const e of document.querySelectorAll('button,[role="tab"]')) {
      const t = (e.innerText || '').trim();
      if (!t || t.length > 12) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 8 || r.height < 8) continue;
      出.push({ 文字: t, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], aria: e.getAttribute('aria-label') });
    }
    return 出;
  });
  记('页签/按钮清单（前 30）：' + JSON.stringify(页签.slice(0, 30)));
  结果.读数.页签 = 页签;

  // ① 特效广场
  const t1 = await 点文字('特效广场');
  记('切到特效广场：' + JSON.stringify(t1));
  await page.waitForTimeout(1500);
  const 特效卡 = await 扫卡(page);
  记(`特效广场：可见可交互元素 ${特效卡.length} 个`);
  记('  明细：' + JSON.stringify(特效卡.slice(0, 40)));
  const 特详 = await 找详情(page);
  记('  含「详情」的元素：' + JSON.stringify(特详));
  结果.读数.特效广场 = { 元素: 特效卡, 含详情: 特详 };
  await page.screenshot({ path: EVID + 'ey1-特效广场.png' });
  记('已拍 ey1-特效广场.png');

  // ② 风格广场（对照组：已知这里有 ⤢ 详情）
  const t2 = await 点文字('风格广场');
  记('切到风格广场：' + JSON.stringify(t2));
  await page.waitForTimeout(1500);
  const 风格卡 = await 扫卡(page);
  const 风详 = await 找详情(page);
  记(`风格广场：可见可交互元素 ${风格卡.length} 个；含「详情」的元素 ${风详.length} 个`);
  记('  含「详情」的元素：' + JSON.stringify(风详.slice(0, 6)));
  结果.读数.风格广场 = { 元素: 风格卡, 含详情: 风详 };
  await page.screenshot({ path: EVID + 'ey1-风格广场.png' });
  记('已拍 ey1-风格广场.png');

  // ③ 特效广场的另外两个页签
  for (const 名 of ['我的收藏', '最近使用']) {
    const r = await 点文字(名);
    if (!r.ok) { 记(`${名}：${r.原因}`); continue; }
    await page.waitForTimeout(1200);
    const el = await 扫卡(page);
    const d = await 找详情(page);
    记(`${名}：可交互元素 ${el.length} 个；含「详情」${d.length} 个`);
    结果.读数[名] = { 元素: el, 含详情: d };
  }

  // ④ 汇总：两个广场里带「⤢ 详情」那一类 path 的元素各有多少
  const 汇总 = (名称, 元素) => {
    const 详情类 = 元素.filter((e) => e.aria && /详情/.test(e.aria));
    return { 名称, 总数: 元素.length, 详情类: 详情类.map((e) => ({ aria: e.aria, box: e.box, path头: e.path头 })) };
  };
  结果.读数.汇总 = {
    特效: 汇总('特效广场', 特效卡),
    风格: 汇总('风格广场', 风格卡),
  };
  记('⭐ 汇总：' + JSON.stringify(结果.读数.汇总, null, 1));

  // 收尾：关抽屉
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1500);
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
  console.log('\n=== 已写 tools/batchEY1.json ===');
}
