// Batch EY-2：⭐⭐⭐ 点进「特效库」，正面找 `特效详情` / `lensDetail` 的入口
//
// EY-1 已经**推翻了我自己的臆想**：素材库浮层里根本没有「特效广场」这个页签，
// 只有三个入口 —— `风格库` / `特效库` / `打开工具箱`。
// ⇒ 「特效广场」「我的收藏」「最近使用」这三个名字是我从 i18n 键名里脑补的，界面上不存在。
//
// 所以本轮先点 `特效库`，看它到底开出一个什么面板，再用**差分法**找新元素。
//
// ⛔ 绝不点卡片本体 —— 手册实测「点卡片本体」= 新建节点（画布 12→13）。
//    只做 hover，不做 click。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEY2.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

/** 全页签名：只看「有 rect 且可见」的元素，够用来做差分
 *  ⚠️ 第一版把这段函数体写在了 Node 作用域 ⇒ `location is not defined`。
 *     浏览器里的 DOM API 一律要包进 page.evaluate。 */
const 签名 = () => page.evaluate(() => ({
  url: location.href,
  元素: Array.from(document.querySelectorAll('*')).map((e) => {
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return null;
    const cs = getComputedStyle(e);
    if (cs.visibility === 'hidden' || cs.display === 'none') return null;
    if (parseFloat(cs.opacity) === 0) return null;
    const t = (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 60);
    return {
      tag: e.tagName.toLowerCase(),
      role: e.getAttribute('role'),
      aria: e.getAttribute('aria-label'),
      title: e.getAttribute('title'),
      cls: (e.getAttribute('class') || '').split(/\s+/).filter(Boolean).slice(0, 3).join('.'),
      zi: cs.zIndex,
      cur: cs.cursor,
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      t,
    };
  }).filter(Boolean),
}));

const 键 = (e) => `${e.tag}|${e.role}|${e.aria}|${e.title}|${e.box.join(',')}`;

/** 枚举浮层里所有「看起来可交互」的元素：cursor:pointer / button / role */
const 可交互 = () => page.evaluate(() => Array.from(document.querySelectorAll('*')).filter((e) => {
  const r = e.getBoundingClientRect();
  if (r.width < 6 || r.height < 6) return false;
  if (r.top < 0 || r.left < 0 || r.bottom > innerHeight || r.right > innerWidth) return false;
  const cs = getComputedStyle(e);
  if (cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return false;
  return cs.cursor === 'pointer' || e.tagName === 'BUTTON' || e.getAttribute('role') === 'button';
}).map((e) => {
  const r = e.getBoundingClientRect();
  return {
    tag: e.tagName.toLowerCase(),
    文字: (e.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 50),
    aria: e.getAttribute('aria-label'),
    title: e.getAttribute('title'),
    box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
    中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
    svg数: e.querySelectorAll(':scope > svg').length,
    path头: (e.querySelector('path')?.getAttribute('d') || '').slice(0, 40),
    禁用: e.disabled === true || e.getAttribute('aria-disabled') === 'true',
    op: getComputedStyle(e).opacity,
    cur: getComputedStyle(e).cursor,
    cls: (e.getAttribute('class') || '').split(/\s+/).filter(Boolean).slice(0, 3).join('.'),
  };
}));

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  const 开局偏差 = await 核对坐标(page);
  记('开局坐标偏差：' + JSON.stringify(开局偏差));

  // ---- 步骤 1：开素材库浮层 ----
  const 素材库点 = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find((x) => x.getAttribute('aria-label') === '素材库');
    if (!b) return null;
    const r = b.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
  });
  if (!素材库点) throw new Error('找不到素材库按钮');
  await page.mouse.move(素材库点[0], 素材库点[1]);
  await page.waitForTimeout(500);
  const 自证1 = await page.evaluate(([x, y]) => {
    const b = document.elementFromPoint(x, y)?.closest('button');
    return b?.getAttribute('aria-label') || null;
  }, 素材库点);
  记('点素材库前自证=' + 自证1);
  if (自证1 !== '素材库') throw new Error('落点不对');
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(1200);
  await page.mouse.move(700, 250);
  await page.waitForTimeout(700);

  const 浮层前 = await 签名();
  const 浮层元素 = await 可交互();
  记('素材库浮层里的条目：' + JSON.stringify(浮层元素.filter((e) => e.box[0] >= 560 && e.box[0] <= 800 && e.box[1] >= 550 && e.box[1] <= 740).map((e) => ({ t: e.文字, box: e.box }))));

  // ---- 步骤 2：点「特效库」 ----
  const 特效库 = 浮层元素.find((e) => e.文字.startsWith('特效库'));
  if (!特效库) throw new Error('浮层里找不到「特效库」');
  await page.mouse.move(特效库.中心[0], 特效库.中心[1]);
  await page.waitForTimeout(500);
  const 自证2 = await page.evaluate(([x, y]) => {
    const e = document.elementFromPoint(x, y);
    const b = e?.closest('button,[role=button],div');
    return { 文字: (b?.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 30), path: e?.tagName };
  }, 特效库.中心);
  记('点特效库前自证=' + JSON.stringify(自证2));
  if (!自证2.文字.startsWith('特效库')) throw new Error('特效库落点不对：' + JSON.stringify(自证2));
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(2500);
  await page.mouse.move(720, 120);
  await page.waitForTimeout(1500);

  const 后 = await 签名();
  记('URL：' + CANVAS_URL + '  ==>  ' + 后.url);

  // ---- 步骤 3：差分找新增 ----
  const 前键 = new Set(浮层前.元素.map(键));
  const 新增 = 后.元素.filter((e) => !前键.has(键(e)));
  记(`⭐ 差分：全页 ${后.元素.length} 个元素，新增 ${新增.length} 个`);

  // 新增里挑「容器」（z-index 高 / 面积大 / 有文字）
  const 容器 = 新增.filter((e) => e.t || (e.box[2] > 200 && e.box[3] > 200)).slice(0, 60);
  记('⭐ 新增且带文字或大尺寸的元素：');
  for (const e of 容器) {
    记(`   zi=${e.zi} cur=${e.cur} box=[${e.box}] tag=${e.tag} role=${e.role} aria=${e.aria} cls=${e.cls} | ${e.t}`);
  }

  const 交互2 = await 可交互();
  记(`⭐ 打开后全页可交互元素 ${交互2.length} 个`);
  落盘({ 前浮层: 浮层元素, 新增, 打开后可交互: 交互2 }, OUT.replace('.json', '.raw.json'));

  await page.screenshot({ path: EVID + 'ey2-特效库打开.png' });
  记('已拍 ey2-特效库打开.png');

  // ---- 步骤 4：全文搜「详情」 ----
  const 详情命中 = 交互2.filter((e) => (e.文字 + (e.aria || '') + (e.title || '')).includes('详情'));
  记('可交互元素里含「详情」：' + JSON.stringify(详情命中.map((e) => ({ 文字: e.文字, aria: e.aria, box: e.box }))));

  // 全页文本搜「详情」（不限可交互）
  const 全页详情 = 后.元素.filter((e) => e.t.includes('详情'));
  记('全页含「详情」的元素：' + JSON.stringify(全页详情.slice(0, 20).map((e) => ({ tag: e.tag, box: e.box, t: e.t }))));

  结果.读数.详情命中 = 详情命中;
  结果.读数.全页详情 = 全页详情.slice(0, 30);

  await page.keyboard.press('Escape');
  await page.waitForTimeout(1200);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1200);
  await page.screenshot({ path: EVID + 'ey2-关闭后.png' });
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
  console.log('\n=== 已写 tools/batchEY2.json ===');
}
