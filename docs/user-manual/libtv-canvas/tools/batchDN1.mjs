// Batch DN-1：**只读**摸清广场顶部三个页签和「仅看可商用」勾选框。
//
// ⭐ 为什么挑这三个：它们在**每一张截图里都看得见**，却几乎没被验过 ——
//   · `仅看可商用` 手册只记了「checked 在 false↔true 之间变」⇒ **完全没测它筛不筛**
//   · `最近使用` 页**一次都没点过**
//   · `我的收藏` 页只记了「空时写暂无素材」「卡上没有收藏星」
//
// ⛔ **全程只读**：不点收藏星（那会写账户数据）、不点卡片、不提交任何东西。
//    只切页签、只切勾选框、只读 DOM 和请求参数。
//
// ⭐ 判据设计（DN 要回答的是「有没有变」，所以每项都要有对照）：
//   对照组 = 同一分类、勾选**关闭**时的卡名列表 + 请求体
//   实验组 = 勾选**打开**后重读同样的两样
//   ⚠️ 只比「DOM 卡数」不够 —— 虚拟滚动会让那玩意在 25~54 之间乱跳。
//      **要比卡名集合**，那才对应真实内容。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 页签: [], 勾选: [], 请求: [] };
const SAVE = () => writeFile(new URL('./batchDN1.json', import.meta.url), JSON.stringify(out, null, 2));

const { browser, page } = await launch();
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

// 请求侧：只记 feed/stream 的关键参数，用来回答「勾选框到底传了什么」
page.on('response', async (resp) => {
  try {
    if (!/model\/feed\/stream/.test(resp.url())) return;
    let body = ''; try { body = resp.request().postData() || ''; } catch { body = ''; }
    let bj = {}; try { bj = JSON.parse(body); } catch { /* 保留原文 */ }
    const t = await resp.text(); if (!t) return;
    let j; try { j = JSON.parse(t); } catch { return; }
    const arr = (j?.data?.data) || [];
    out.请求.push({ page: j?.data?.page, 条数: arr.length, 键: Object.keys(bj), 请求体: bj });
    SAVE();
  } catch { /* 忽略 */ }
});

await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(5000);

// ---------- 通用读取：卡名集合（比 DOM 张数可靠）+ 勾选框状态 + 空态文案 ----------
const 读 = () => page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  const modals = [...document.querySelectorAll('.mantine-Modal-inner')].filter(vis);
  const root = modals.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
  if (!root) return { 有弹层: false };
  // 卡容器 = 详情按钮往上第 3 层（191×302）
  const 卡 = new Set();
  for (const D of root.querySelectorAll('button[aria-label="详情"]')) {
    for (let p = D.parentElement, j = 0; p && j < 6; p = p.parentElement, j += 1) {
      const r = p.getBoundingClientRect();
      if (r.width > 150 && r.width < 260 && r.height > 260) { 卡.add(p); break; }
    }
  }
  const 名 = [...卡].map((e) => (e.innerText || '').split('\n')[0].trim().slice(0, 20));
  // 找勾选框：label 文本是「仅看可商用」的那个 input
  let 勾 = null;
  for (const lb of root.querySelectorAll('label,div,span')) {
    if (/仅看可商用/.test(lb.textContent || '') && lb.children.length <= 2) {
      const inp = lb.querySelector('input[type="checkbox"]') || (lb.previousElementSibling && lb.previousElementSibling.querySelector && lb.previousElementSibling.querySelector('input[type="checkbox"]'));
      if (inp) { 勾 = { checked: inp.checked, 元素: { w: Math.round(inp.getBoundingClientRect().width), h: Math.round(inp.getBoundingClientRect().height) } }; break; }
    }
  }
  // 三个页签当前哪个高亮
  const 页签态 = ['风格广场', '我的收藏', '最近使用'].map((名2) => {
    const b = [...root.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === 名2);
    if (!b) return { 名: 名2, 存在: false };
    const cs = getComputedStyle(b);
    return { 名: 名2, 存在: true, 背景: cs.backgroundColor, 颜色: cs.color, class: (b.className || '').slice(0, 70) };
  });
  // 空态文案
  const 空态 = [...root.querySelectorAll('*')].filter((e) => e.children.length === 0 && /暂无|还没有|空/.test((e.textContent || '').trim()) && vis(e)).map((e) => (e.textContent || '').trim()).slice(0, 5);
  // 收藏星有几个（aria-label 含「收藏」）
  const 星 = [...root.querySelectorAll('button[aria-label*="收藏"]')].length;
  return { 有弹层: true, DOM卡数: 卡.size, 卡名: 名, 勾选框: 勾, 页签态, 空态, 收藏星数: 星 };
});

// ---------- ① 「仅看可商用」：关 → 开 → 关，逐次记卡名集合 ----------
LOG('=== ① 「仅看可商用」勾选框 ===');
await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '风格插画'); if (b) b.click(); });
await page.waitForTimeout(4000);
await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = 0; });
await page.waitForTimeout(1500);

const 前请求 = out.请求.length;
const 基线 = await 读();
LOG(`基线（未勾选）: DOM ${基线.DOM卡数} 张 | 勾选框 ${JSON.stringify(基线.勾选框)} | 收藏星 ${基线.收藏星数}`);
LOG(`   前 5 张卡名: ${JSON.stringify(基线.卡名.slice(0, 5))}`);
out.勾选.push({ 阶段: '关闭', ...基线, 请求起: 前请求, 请求止: out.请求.length });
SAVE();

// ⭐ 用**点击真实 checkbox** 切换（不直接改属性，否则可能绕过真实事件链）
const 切了 = await page.evaluate(() => {
  for (const lb of document.querySelectorAll('label,div,span')) {
    if (/仅看可商用/.test(lb.textContent || '') && lb.children.length <= 2) {
      const inp = lb.querySelector('input[type="checkbox"]');
      if (inp) { inp.click(); return true; }
    }
  }
  return false;
});
LOG(`点勾选框: ${切了}`);
await page.waitForTimeout(4000);
const 勾上 = await 读();
LOG(`勾选后: DOM ${勾上.DOM卡数} 张 | 勾选框 ${JSON.stringify(勾上.勾选框)} | 收藏星 ${勾上.收藏星数}`);
LOG(`   前 5 张卡名: ${JSON.stringify(勾上.卡名.slice(0, 5))}`);
out.勾选.push({ 阶段: '打开', ...勾上 });
SAVE();
await shot(page, 'DN-a-勾上仅看可商用.png');
LOG('📸 DN-a');

// ⭐⭐ 关键判据：**卡名集合**有没有变
const 集合A = new Set(基线.卡名); const 集合B = new Set(勾上.卡名);
const 只在关 = [...集合A].filter((x) => !集合B.has(x));
const 只在开 = [...集合B].filter((x) => !集合A.has(x));
LOG(`\n⭐ 卡名集合对比: 关 ${集合A.size} 个 / 开 ${集合B.size} 个 | 只在关闭时 ${只在关.length} 个 | 只在打开时 ${只在开.length} 个`);
if (只在关.length) LOG(`   只在关闭时出现: ${JSON.stringify(只在关.slice(0, 10))}`);
if (只在开.length) LOG(`   只在打开时出现: ${JSON.stringify(只在开.slice(0, 10))}`);
// 「商用」徽标：卡面上有「商用」二字的
const 商用关 = 基线.卡名.filter((n) => /商用/.test(n)).length;
const 商用开 = 勾上.卡名.filter((n) => /商用/.test(n)).length;
LOG(`   卡名里含「商用」的: 关闭时 ${商用关} / 打开时 ${商用开}`);
// 勾选后新发的请求带什么参数
const 新请求 = out.请求.slice(前请求);
LOG(`   勾选后新发请求 ${新请求.length} 个，参数键: ${JSON.stringify([...new Set(新请求.flatMap((r) => r.键))])}`);
for (const r of 新请求.slice(0, 3)) LOG(`     page=${r.page} 条数=${r.条数} body=${JSON.stringify(r.请求体).slice(0, 240)}`);

// 改回关闭
await page.evaluate(() => {
  for (const lb of document.querySelectorAll('label,div,span')) {
    if (/仅看可商用/.test(lb.textContent || '') && lb.children.length <= 2) {
      const inp = lb.querySelector('input[type="checkbox"]');
      if (inp && inp.checked) { inp.click(); return true; }
    }
  }
  return false;
});
await page.waitForTimeout(2500);
const 改回 = await 读();
LOG(`\n已改回: 勾选框 ${JSON.stringify(改回.勾选框.勾选框 || 改回.勾选框)}`);
out.勾选.push({ 阶段: '改回关闭', ...改回 });
SAVE();

// ---------- ② 「我的收藏」页 ----------
LOG('\n=== ② 「我的收藏」页 ===');
await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '我的收藏'); if (b) b.click(); });
await page.waitForTimeout(4000);
const 收藏页 = await 读();
LOG(`DOM ${收藏页.DOM卡数} 张 | 空态 ${JSON.stringify(收藏页.空态)} | 收藏星 ${收藏页.收藏星数}`);
LOG(`   页签态: ${JSON.stringify(收藏页.页签态.map((x) => ({ 名: x.名, 背景: x.背景 })))}`);
if (收藏页.卡名.length) LOG(`   卡名: ${JSON.stringify(收藏页.卡名.slice(0, 10))}`);
await shot(page, 'DN-b-我的收藏页.png');
LOG('📸 DN-b');
out.页签.push({ 页签: '我的收藏', ...收藏页 });
SAVE();

// ---------- ③ 「最近使用」页 ----------
LOG('\n=== ③ 「最近使用」页 ===');
await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '最近使用'); if (b) b.click(); });
await page.waitForTimeout(4000);
const 最近 = await 读();
LOG(`DOM ${最近.DOM卡数} 张 | 空态 ${JSON.stringify(最近.空态)} | 收藏星 ${最近.收藏星数}`);
if (最近.卡名.length) LOG(`   卡名: ${JSON.stringify(最近.卡名.slice(0, 10))}`);
LOG(`   页签态: ${JSON.stringify(最近.页签态.map((x) => ({ 名: x.名, 背景: x.背景 })))}`);
await shot(page, 'DN-c-最近使用页.png');
LOG('📸 DN-c');
out.页签.push({ 页签: '最近使用', ...最近 });
SAVE();

// ---------- ④ 回到「风格广场」确认能回来 ----------
await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '风格广场'); if (b) b.click(); });
await page.waitForTimeout(3500);
const 回来 = await 读();
LOG(`\n=== ④ 回到「风格广场」: DOM ${回来.DOM卡数} 张 ===`);

SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDN1.json ===');
