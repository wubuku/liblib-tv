// ⭐⭐⭐⭐⭐ Batch FN-2：修掉**第三个判据陷阱**——「点得到按钮」≠「面板真切了」
//
// FN-1 抓到的 `fn1-02-素材库.png` ⛔ **根本不是素材库，是角色造型室**：
// 上一轮打开的角色造型室面板没关，它横着铺开 5904px，把底栏按钮**盖住了**，
// 于是 `page.mouse.click(660, 757)` 点在了角色造型室的空白处 ——
// `开底栏()` 只断言「按钮的 rect 找得到」，断言照样通过，**截图却张冠李戴**。
//
// ⛔ 缺陷 449：`开底栏()` 的断言太弱，只验「能点」，不验「面板确实切了」。
//
// ⭐ 本轮把「面板确实切了」写成**三条硬断言**，全部在 `evaluate` 里量，不靠人眼：
//   ① **落点自证**：点击前 `document.elementFromPoint(x, y).closest('button')`
//      的 aria-label 必须就是目标按钮 —— 被浮层盖住时它会读出别的东西，直接失败。
//   ② **开面板后**：上一个面板的**独占文案**必须消失（角色造型室的 `我的角色库`）。
//   ③ **关面板后**：独占文案必须不再出现（证明确实关掉了，不是被别的盖住）。
//
// ⭐ 顺带把 FI（`921095cc`）那条「素材库广场入口只读出空态」的**证据基础重新核实一遍**：
// FI 只看了面板内的空态文本、没有全页 dump，也可能根本没切面板。
//
// ⛔ 安全边界：只读。全程只开/关底栏面板，不点任何素材卡片（那会新建节点）。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFN2.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

let 断言次数 = 0, 失败 = 0;
const 断言 = (条件, 说明, 数据) => {
  断言次数++;
  if (!条件) { 失败++; 记('   ❌ 断言失败：' + 说明 + (数据 !== undefined ? '｜数据 ' + JSON.stringify(数据) : '')); return false; }
  记('   ✅ 断言通过：' + 说明);
  return true;
};

const 浏览器 = await launch();
const page = 浏览器.page;

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

const 归一 = (s) => s.replace(/[\s　]+/g, '');

/** ⭐ 三条断言①：找按钮 + 落点自证。返回点击点，被挡住就返回 null。 */
const 找可点按钮 = (aria) => page.evaluate((a) => {
  for (const x of document.querySelectorAll('button')) {
    if ((x.getAttribute('aria-label') || '') !== a) continue;
    const r = x.getBoundingClientRect();
    if (!(r.width > 0 && r.top > 700)) continue;
    const cx = Math.round(r.left + r.width / 2), cy = Math.round(r.top + r.height / 2);
    const el = document.elementFromPoint(cx, cy);
    const btn = el && el.closest('button');
    return {
      框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      点: [cx, cy],
      命中标签: btn ? btn.getAttribute('aria-label') : null,
      命中类名: el ? String(el.className || '').slice(0, 70) : null,
      命中文字: el ? (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 30) : null,
    };
  }
  return null;
}, aria);

/** ⭐ 断言②：开面板。`必须消失` = 上一个面板的独占文案。 */
const 开底栏 = async (aria, { 必须消失 = [] } = {}) => {
  const b = await 找可点按钮(aria);
  if (!b) { 记(`   ⛔ 找不到可点的「${aria}」`); return false; }
  记(`   「${aria}」框 ${JSON.stringify(b.框)}｜落点 ${JSON.stringify(b.点)}｜落点属主 aria-label=${JSON.stringify(b.命中标签)}｜class=${JSON.stringify(b.命中类名)}`);
  if (!断言(b.命中标签 === aria, `「${aria}」的落点属主就是它自己（没被浮层盖住）`, b)) return false;
  await page.mouse.click(b.点[0], b.点[1]);
  await page.waitForTimeout(4000);
  const w = (await 全页文字()).map(归一);
  const 集 = new Set(w);
  if (必须消失.length) {
    断言(必须消失.every((m) => !集.has(归一(m))), `打开「${aria}」后，上一面板的独占文案 ${JSON.stringify(必须消失)} 已消失`, w.filter((t) => 必须消失.map(归一).includes(t)));
  }
  return true;
};

/** ⭐ 断言③：关面板，验证独占文案真的不见了。 */
const 关面板 = async (独占) => {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1200);
  let w = new Set((await 全页文字()).map(归一));
  if (独占.every((m) => !w.has(归一(m)))) { 记('   ✅ Escape 就关掉了'); return true; }
  // Escape 不行就找面板右上角的关闭钮：aria-label 或一个纯 × 的按钮
  const c = await page.evaluate((独) => {
    const 归 = (s) => (s || '').replace(/\s+/g, '');
    for (const el of document.querySelectorAll('button')) {
      if (!独.some((m) => 归(el.closest('div')?.innerText || '').includes(归(m)))) continue;
      const t = 归(el.innerText) || el.getAttribute('aria-label') || 归(el.title);
      if (!t || t.length > 4) continue;
      const r = el.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) continue;
      return { 文字: t, 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    }
    return null;
  }, 独占);
  if (c) { 记(`   ⛔ Escape 无效，点关闭钮 ${JSON.stringify(c.文字)}`); await page.mouse.click(c.点[0], c.点[1]); await page.waitForTimeout(1200); }
  else 记('   ⛔ Escape 无效，也没找到短文案关闭钮');
  w = new Set((await 全页文字()).map(归一));
  return 断言(独占.every((m) => !w.has(归一(m))), `关面板后独占文案 ${JSON.stringify(独占)} 真的消失`, [...w].filter((t) => 独占.map(归一).includes(t)));
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 120));
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);

  // ——— ① 角色造型室：建立「独占文案」基准 ———
  记('—— ① 角色造型室（建立基准）——');
  const 角色独占 = ['我的角色库', '官方角色库', '创建新角色'];
  断言(await 开底栏('角色造型室'), '「角色造型室」打开成功');
  let w = await 全页文字();
  记(`   全页 dump ${w.length} 条`);
  断言(角色独占.every((m) => w.map(归一).includes(归一(m))), '角色造型室的独占文案确实在界面上（阳性对照）', w.length);
  await page.screenshot({ path: EVID + 'fn2-01-角色造型室.png' });

  // ——— ② 关掉它，并验证确实关掉了（FN-1 就是漏了这一步）——
  记('—— ② 关掉角色造型室 ——');
  R.读数.关面板 = { 成功: await 关面板(角色独占) };

  // ——— ③ ⭐ 干净状态下开素材库 ———
  记('—— ③ 干净状态下开「素材库」——');
  const 素材库开 = await 开底栏('素材库', { 必须消失: 角色独占 });
  R.读数.素材库打开 = 素材库开;
  w = await 全页文字();
  记(`   ⭐ 素材库状态下全页 dump ${w.length} 条`);
  R.读数.素材库文字 = w;
  await page.screenshot({ path: EVID + 'fn2-02-素材库-干净态.png' });

  // 面板容器 / 空态的真实读数
  const 结构 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ');
    const 面板 = [...document.querySelectorAll('div,section')].filter((el) => {
      const r = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      return r.width > 200 && r.height > 120 && r.top > 80 && r.top < 700 && cs.position === 'absolute' && cs.zIndex !== 'auto' && Number(cs.zIndex) > 5;
    }).map((el) => {
      const r = el.getBoundingClientRect();
      return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], z: getComputedStyle(el).zIndex, class: String(el.className || '').slice(0, 80), 文字: 归(el.innerText).slice(0, 400) };
    }).sort((a, b) => b.框[2] * b.框[3] - a.框[2] * a.框[3]).slice(0, 4);
    return 面板;
  });
  R.读数.素材库面板候选 = 结构;
  记('   候选浮层结构 ' + JSON.stringify(结构, null, 1).slice(0, 1400));
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);

  // ——— ④ 生成历史：同样干净地开一次 ———
  记('—— ④ 干净状态下开「生成历史」——');
  const 历史开 = await 开底栏('生成历史', { 必须消失: 角色独占 });
  R.读数.生成历史打开 = 历史开;
  const hw = await 全页文字();
  记(`   ⭐ 生成历史状态下全页 dump ${hw.length} 条`);
  R.读数.生成历史文字 = hw;
  await page.screenshot({ path: EVID + 'fn2-03-生成历史-干净态.png' });
  await page.keyboard.press('Escape'); await page.waitForTimeout(1000);

  记(`—— 共跑了 ${断言次数} 条断言，失败 ${失败} 条 ——`);
} catch (e) {
  记('❌ ' + (e && e.message ? e.message : String(e)));
} finally {
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}
