// Batch DX-1：从**侧栏的另一个入口**进特效广场，验它的卡面数字是不是也是 `runCount`。
//
// ⭐ DW 批查清了：风格广场里只有 3 个页签，`特效广场` **不在其中**
//   （反查 0 命中）⇒ 它是**另一个独立广场**，得从底栏「素材库」侧栏的另一个入口进。
//   ⇒ DV 批「切页签切不过去」的根因就在这里，路径本轮换掉。
//
// ⭐ 本轮要回答的（DV 留的 📖）：**特效广场的卡面数字是不是也等于 `runCount`**。
//   风格侧已累计 57 个样本坐实；特效侧一例未验 ⇒ 不验就是以偏概全。
//
// ⭐⭐ 自证三连（DV-1 的教训：数据真、标签错的错最难发现）：
//   ① 入口按钮点了没有（读侧栏里实际存在的按钮文字）
//   ② 当前广场是哪一个（读页签名的高亮）
//   ③ **卡名样本**—— 风格卡和特效卡的题材一眼能分
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 侧栏按钮: null, 页签: null, 特效: null };
const SAVE = () => writeFileSync(new URL('./batchDX1.json', import.meta.url), JSON.stringify(out, null, 2));

const { browser, page } = await launch();
let 收 = new Map();
page.on('response', async (resp) => {
  try {
    if (!/model\/feed\/stream/.test(resp.url())) return;
    const t = await resp.text(); if (!t) return;
    let j; try { j = JSON.parse(t); } catch { return; }
    for (const r of (j?.data?.data) || []) if (r && r.uuid && !收.has(r.uuid)) 收.set(r.uuid, r);
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

// ---------- ① 只开侧栏，先把里面**实际存在**的按钮全读出来 ----------
await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2500);
const 侧栏 = await page.evaluate(() => {
  // ⛔ 第一版用 `.mantine-Drawer-inner` 限定容器 ⇒ 读到 0 个。
  //   广场**不是** Mantine Drawer（它是自己那层），限定容器把按钮全过滤掉了。
  //   ⭐ 教训：限定容器前先确认它真的存在，别假设。
  return [...document.querySelectorAll('button,[role="tab"],a')].map((e) => {
    const r = e.getBoundingClientRect();
    return { tag: e.tagName.toLowerCase(), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), aria: e.getAttribute('aria-label') || '', 可见: r.width > 0 && r.height > 0, 位置: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }).filter((x) => x.可见);
});
out.侧栏按钮 = 侧栏;
LOG('══════ ① 侧栏里可见的按钮 ══════');
for (const b of 侧栏) LOG(`   [${b.tag}] 「${b.文字}」${b.aria ? ' aria=' + b.aria : ''} @${b.位置.join(',')}`);

// ---------- ② 点「特效库」入口 ----------
const 点了 = await page.evaluate(() => {
  const 全部 = [...document.querySelectorAll('button')];
  // ⛔ 第一版判据 `t.length <= 6` 把入口滤掉了 —— 因为它的真实文案是
  //   「特效库 新增特效节点 NEW」（**11 字**，带副标题和 NEW 徽标），不是光秃秃的「特效库」。
  const 候选 = 全部.filter((b) => { const t = (b.innerText || '').replace(/\s+/g, ' ').trim(); const r = b.getBoundingClientRect(); return /^(特效库|风格库)/.test(t) && r.width > 0 && r.height > 0; });
  const 特效 = 候选.find((b) => /^特效库/.test((b.innerText || '').replace(/\s+/g, ' ').trim()));
  if (!特效) return { 成功: false, 候选文字: 候选.map((b) => (b.innerText || '').trim()) };
  const t = (特效.innerText || '').trim();
  特效.click();
  return { 成功: true, 点的: t };
});
LOG(`\n② 点入口: ${JSON.stringify(点了)}`);
await page.waitForTimeout(6000);
if (!点了.成功) { LOG('⛔ 侧栏里找不到特效入口'); SAVE(); await browser.close(); process.exit(0); }

// ---------- ③ 自证：页签 + 卡名样本 ----------
const 页签读 = await page.evaluate(() => {
  const 目标 = ['风格广场', '特效广场', '我的收藏', '最近使用'];
  return 目标.map((w) => {
    const e = [...document.querySelectorAll('button,[role="tab"]')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === w);
    if (!e) return { 文字: w, 找到: false };
    const r = e.getBoundingClientRect(); const c = getComputedStyle(e);
    return { 文字: w, 找到: true, 高亮: c.backgroundColor !== 'rgba(0, 0, 0, 0)' && c.backgroundColor !== 'transparent', 背景: c.backgroundColor, 位置: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  });
});
out.页签 = 页签读;
LOG('\n══════ ③ 页签读数 ══════');
for (const p of 页签读) LOG(`   ${p.文字}: ${p.找到 ? `${p.高亮 ? '✅高亮' : '未高亮'} bg=${p.背景} @${p.位置.join(',')}` : '⛔ 不存在'}`);
const 高亮的 = 页签读.filter((p) => p.高亮).map((p) => p.文字);
LOG(`⭐ 当前广场 = ${JSON.stringify(高亮的)}`);
LOG(`⭐ 卡名样本: ${JSON.stringify([...收.values()].slice(0, 4).map((r) => r.name))}`);
const 首 = [...收.values()][0];
LOG(`卡记录 ${收.size} 条，顶层字段 ${首 ? Object.keys(首).length : 0} 个，有 runCount: ${首 ? Object.prototype.hasOwnProperty.call(首, 'runCount') : null}`);
out.当前广场 = 高亮的;
out.记录数 = 收.size;
out.字段总数 = 首 ? Object.keys(首).length : 0;
out.有runCount = 首 ? Object.prototype.hasOwnProperty.call(首, 'runCount') : null;
out.卡名样本 = [...收.values()].slice(0, 5).map((r) => r.name);

// ---------- ④ 逐卡对照 ----------
const 转 = (s) => { const w = /^(\d+(?:\.\d+)?)w$/.exec(s); if (w) return Math.round(parseFloat(w[1]) * 10000); const n = Number(s); return Number.isFinite(n) ? n : null; };
const 找记录 = (文本) => { let best = null; for (const r of 收.values()) { if (!r.name) continue; if (文本.includes(r.name) || r.name.includes(文本.slice(0, 10))) if (!best || r.name.length > best.name.length) best = r; } return best; };
const 屏 = await page.evaluate(() => {
  const 盒 = [];
  for (const e of document.querySelectorAll('div')) {
    const r = e.getBoundingClientRect();
    if (!(r.width >= 150 && r.width <= 340 && r.height >= 180 && r.height <= 460)) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 90) continue;
    if (e.querySelectorAll('button').length < 1) continue;
    if (盒.some((b) => b.文本 === t)) continue;
    盒.push({ 文本: t });
  }
  return 盒;
});
let 符合 = 0, 总 = 0, 失败 = 0; const 样本 = [];
for (const c of 屏) {
  const tok = (c.文本.match(/(?<![\d.])\d+(?:\.\d+)?w?(?![\w])/g) || []).filter((x) => /\d/.test(x));
  if (!tok.length) continue;
  const 卡面 = 转(tok[tok.length - 1]);
  if (卡面 == null) continue;
  const r = 找记录(c.文本);
  if (!r) { 失败 += 1; continue; }
  总 += 1;
  const 精确 = r.runCount === 卡面;
  const 近似 = r.runCount >= 10000 && 卡面 === Math.round((r.runCount / 10000).toFixed(1) * 10000);
  const 行 = 精确 || 近似;
  if (行) 符合 += 1;
  样本.push({ 卡面: tok[tok.length - 1], 推算: 卡面, 卡名: r.name, runCount: r.runCount, 精确, 近似, 符合: 行 });
}
out.特效 = { 可分析: 总, 符合, 定位失败: 失败, 全部符合: 总 > 0 && 符合 === 总, 样本 };
LOG(`\n══════ ④ 卡面数字对照 ══════\n可分析 ${总}（定位失败 ${失败}）｜符合 runCount ${符合}`);
for (const s of 样本) LOG(`   ${s.符合 ? '✅' : '⛔'} 「${s.卡面}」(${s.推算}) vs runCount=${s.runCount} ${s.精确 ? '精确' : s.近似 ? '缩写一致' : '都不符'} ｜ ${s.卡名.slice(0, 26)}`);
out.最终节点数 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDX1.json ===');
