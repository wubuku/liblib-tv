// Batch DS-2：把详情浮层的第二个分区「其余适配模型」真正拍到。
//
// ⭐ 判据（DS-1 实测出来的，不是猜的）：
//   卡记录 `baseType` 字段的长度 = 该风格适配的模型数。
//   风格插画首屏 121 张的分布：
//     长度 1 → 80 张（单模型，浮层只渲染「首选推荐模型」）
//     长度 2 → 22 张   长度 3 → 5 张
//     长度 4 → 1 张    长度 5 → 7 张   长度 6 → 6 张
//   ⇒ 41/121 是多模型卡。⭐ 这也**解释了 DR-2 为什么没拍到那一栏**：
//     DR-2 那张 `Seedream 5.0 pro` 是单模型卡。
//
// 本轮目标：找一张 **6 模型**卡（`一键国漫CGV2` / `赛璐璐光影` /
// `天宫东方传统美学超现实神话元素奇幻概念艺`，baseType 长度 6），
// 打开详情浮层 ⇒ 「首选推荐模型」1 项 + 「其余适配模型」5 项。
//
// ⛔ 安全边界：只**读**。不点「使用」、不点「收藏」、不应用风格。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const 目标 = '（自动挑选视口内的多模型卡）';
const out = { 目标卡: 目标, 判据: 'baseType 长度 = 适配模型数', 定位: null, 浮层: null, 节点数: null };
const SAVE = () => writeFileSync(new URL('./batchDS2.json', import.meta.url), JSON.stringify(out, null, 2));

const { browser, page } = await launch();
// ⭐⭐ 定位策略换掉（DS-2 第一版失败）：**不能按卡名去找卡**。
//   广场是虚拟滚动，DOM 里只常驻 25~54 张卡（DL 批查实），
//   `一键国漫CGV2` 虽在接口数据里，**DOM 里根本没渲染它** ⇒ 找 7 轮都找不到。
//   ⭐ 正解：**接口判据 × DOM 交叉** ——
//     ① 从 feed 响应建 `卡名 → baseType 长度` 的映射（数据自证）
//     ② 读**当前视口里真实渲染出来的**卡名
//     ③ 两者取交集，找 `baseType.length >= 2` 的那张 ⭐（这才是多模型卡）
//     ④ 点它的 ⤢ ⇒ 浮层里必然有「其余适配模型」
const 卡映射 = new Map();
page.on('response', async (resp) => {
  try {
    if (!/model\/feed\/stream/.test(resp.url())) return;
    const t = await resp.text(); if (!t) return;
    let j; try { j = JSON.parse(t); } catch { return; }
    for (const r of (j?.data?.data) || []) {
      if (r && r.name && Array.isArray(r.baseType) && !卡映射.has(r.name)) 卡映射.set(r.name, r.baseType);
    }
  } catch { /* 忽略 */ }
});
await open(page, URL_);
await closePromos(page);
await page.waitForTimeout(1500);
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2800);
for (let i = 0; i < 3; i += 1) {
  const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
  if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(600);
}
const pk = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
  if (!b) return null; const r = b.getBoundingClientRect();
  return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
});
if (pk) { await page.mouse.click(pk[0], pk[1]); await page.waitForTimeout(1200); }
await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(5000);
const 当前 = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].filter((x) => /^(推荐|平面设计|风格插画|文创周边)$/.test((x.innerText || '').trim()));
  const on = b.filter((x) => { const c = getComputedStyle(x).backgroundColor; return c && c !== 'rgba(0, 0, 0, 0)'; });
  return on.length ? (on[0].innerText || '').trim() : '?';
});
LOG(`进场分类: ${当前}`);
if (当前 === '风格插画') {
  await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').trim() === '平面设计'); if (b) b.click(); });
  await page.waitForTimeout(3000);
}
await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '风格插画'); if (b) b.click(); });
await page.waitForTimeout(3500);

// ---- 在当前视口里找「已渲染 + 多模型」的那张卡 ----
const 视口定位 = async () => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden'; };
  // 卡名 = 叶子节点里的短文本
  const 叶 = [...document.querySelectorAll('p,h3,span,div')].filter((e) => {
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    return t && t.length >= 2 && t.length <= 40 && e.children.length === 0 && vis(e);
  });
  const 名集 = [...new Set(叶.map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()))];
  return 名集;
});

const 找多模型卡 = async () => {
  const 名集 = await 视口定位();
  const 命中 = 名集.filter((n) => { const bt = 卡映射.get(n); return Array.isArray(bt) && bt.length >= 2; });
  return { 视口卡数: 名集.length, 多模型候选: 命中, 已映射卡数: 卡映射.size };
};

let 探 = await 找多模型卡();
LOG(`\n视口卡名 ${探.视口卡数} 个 / 接口已映射 ${探.已映射卡数} 个 / 其中多模型 ${探.多模型候选.length} 个`);
if (探.多模型候选.length) LOG(`  候选: ${JSON.stringify(探.多模型候选)}`);

// 一屏一屏往下找（每屏都重读 DOM，不能按固定页号跳）
let 定位 = null;
for (let i = 0; i < 8 && !定位; i += 1) {
  if (i > 0) {
    await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop += v.clientHeight * 0.9; });
    await page.waitForTimeout(1800);
    探 = await 找多模型卡();
    LOG(`  往下第 ${i} 屏: 视口 ${探.视口卡数} 卡，多模型候选 ${JSON.stringify(探.多模型候选)}`);
  }
  if (探.多模型候选.length) { 定位 = { 卡名: 探.多模型候选[0], baseType: 卡映射.get(探.多模型候选[0]) }; break; }
}
if (!定位) {
  LOG('⛔ 8 屏内没找到多模型卡（**这是阴性结论，不能当「不存在」**）');
  out.阴性 = { 扫了几屏: 8, 视口卡名样本: 探.多模型候选, 已映射: 探.已映射卡数 };
  SAVE(); await browser.close(); process.exit(0);
}
LOG(`\n⭐ 选定多模型卡: 「${定位.卡名}」 baseType=${JSON.stringify(定位.baseType)}`);
SAVE();

out.定位 = 定位;
SAVE();
if (!定位) { LOG('⛔ 找不到目标卡，收工'); await browser.close(); process.exit(0); }

// ---- 悬停让 ⤢ 显形，再点开 ----
const 卡盒 = await page.evaluate((名) => { const e = [...document.querySelectorAll('p,h3,span,div')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === 名 && x.children.length === 0); if (!e) return null; let c = e; for (let i = 0; i < 8 && c; i += 1) { const r = c.getBoundingClientRect(); if (r.width >= 150 && r.width <= 340 && r.height >= 180 && r.height <= 460) break; c = c.parentElement; } const r = c.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, 定位.卡名);
if (!卡盒) { LOG('⛔ 拿到卡名但定位不到卡片盒子'); await browser.close(); process.exit(0); }
const 卡片中心 = 卡盒;
await page.mouse.move(卡片中心[0], 卡片中心[1]);
await page.waitForTimeout(900);
const 点开了 = await page.evaluate(({ 名 }) => {
  // 重新按文字定位，hover 后按钮 opacity 变 1
  const 全 = [...document.querySelectorAll('p,div,span,h3')];
  const 元素 = 全.find((e) => (e.innerText || '').trim() === 名 && e.children.length === 0);
  if (!元素) return '没找到卡名元素';
  let c = 元素; for (let i = 0; i < 8 && c; i += 1) { const r = c.getBoundingClientRect(); if (r.width >= 150 && r.width <= 340 && r.height >= 180 && r.height <= 460) break; c = c.parentElement; }
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0.3; };
  const bs = [...c.querySelectorAll('button')].filter(vis);
  if (!bs.length) return `卡内可见 button 0 枚（共 ${c.querySelectorAll('button').length} 枚）`;
  const b = bs[bs.length - 1];
  b.click();
  return `点了 aria-label="${b.getAttribute('aria-label') || ''}"`;
}, { 名: 定位.卡名 });
LOG(`\n点详情按钮: ${点开了}`);
await page.waitForTimeout(2500);

// ---- 读浮层 ----
const 浮层 = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden'; };
  const 全模 = [...document.querySelectorAll('[role="dialog"],.mantine-Modal-content,div')].filter((e) => {
    const t = (e.innerText || '').replace(/\s+/g, ' ');
    return vis(e) && /风格详情|特效详情/.test(t) && /使用/.test(t);
  });
  if (!全模.length) return { 有浮层: false };
  const 详 = 全模.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
  const b = 详.getBoundingClientRect();
  const 行 = [...详.querySelectorAll('*')].filter((e) => {
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 60) return false;
    return e.children.length === 0;
  }).map((e) => { const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return { 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), tag: e.tagName.toLowerCase(), 尺寸: [Math.round(r.width), Math.round(r.height)], 位置: [Math.round(r.x), Math.round(r.y)], 颜色: c.color, 字号: c.fontSize }; });
  return { 有浮层: true, 尺寸: [Math.round(b.width), Math.round(b.height)], 位置: [Math.round(b.x), Math.round(b.y)], 全文: (详.innerText || '').replace(/\n+/g, ' | ').slice(0, 900), 行 };
});
out.浮层 = 浮层;
LOG(`\n浮层: ${浮层.有浮层 ? `${浮层.尺寸.join('×')} @${浮层.位置.join(',')}` : '⛔ 没找到'}`);
if (浮层.有浮层) {
  LOG(`全文: ${浮层.全文}`);
  LOG('\n关键分区:');
  for (const kw of ['风格详情', '生成内容可商用', '首选推荐模型', '其余适配模型', '当前使用', '全部适配模型']) {
    const 命 = 浮层.行.filter((r) => r.文字 === kw);
    LOG(`   ${命.length ? '✅' : '⛔'} ${kw}${命.length ? `  ${JSON.stringify(命[0].尺寸)} @${命[0].位置} ${命[0].字号} ${命[0].颜色}` : ''}`);
  }
  await shot(page, 'DS-a-详情浮层-其余适配模型.png');
  LOG('📸 DS-a');
}
out.节点数 = { 打开后: await page.evaluate(() => document.querySelectorAll('[data-id]').length) };
SAVE();
await page.keyboard.press('Escape');
await page.waitForTimeout(1200);
out.节点数.关闭后 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDS2.json ===');
