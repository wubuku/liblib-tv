// Batch DX-3：用**正确的接口**验特效广场的 `runCount`。
//
// ⭐⭐ 根因（DX-2 查到）：两个广场用**两个不同的接口**：
//   风格广场 → `/api/www/model/feed/stream`
//   特效广场 → `/api/www/model/**video**/stream`   ⭐ 不是 feed！
//   ⇒ DX-1 一直只监听 `feed/stream`，所以特效侧「卡记录 0 条」。
//
// ⭐ 本轮：两个接口都监听，先 dump 特效侧响应结构（可能与风格侧不同），
//   再做与 DU/DV 同一套「界面数字 × 全部数值字段」对照。
//
// ⭐ 自证两连（DX §247）：
//   ① 页签高亮的是 `特效广场` 而不是 `风格广场`
//   ② 卡名样本 —— 特效卡题材应当明显不同于风格卡
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 特效结构: null, 页签: null, 特效: null };
const SAVE = () => writeFileSync(new URL('./batchDX3.json', import.meta.url), JSON.stringify(out, null, 2));

const { browser, page } = await launch();
let 收 = new Map();
let 结构样本 = [];
page.on('response', async (resp) => {
  try {
    const u = resp.url();
    if (!/model\/(feed|video)\/stream/.test(u)) return;
    const t = await resp.text(); if (!t) return;
    let j; try { j = JSON.parse(t); } catch { return; }
    if (结构样本.length < 3) {
      const d = j?.data;
      结构样本.push({
        接口: /video/.test(u) ? 'model/video/stream' : 'model/feed/stream',
        顶层键: Object.keys(j || {}),
        data类型: Array.isArray(d) ? `数组(${d.length})` : typeof d,
        data键: d && typeof d === 'object' && !Array.isArray(d) ? Object.keys(d) : null,
      });
    }
    const arr = (j?.data?.data) || [];
    if (!arr.length) return;
    for (const r of arr) if (r && r.uuid && !收.has(r.uuid)) 收.set(r.uuid, r);
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
await page.waitForTimeout(2500);
const 点 = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].find((x) => { const t = (x.innerText || '').replace(/\s+/g, ' ').trim(); const r = x.getBoundingClientRect(); return /^特效库/.test(t) && r.width > 0; });
  if (!b) return null; b.click(); return (b.innerText || '').replace(/\s+/g, ' ').trim();
});
LOG(`点入口: ${JSON.stringify(点)}`);
await page.waitForTimeout(7000);

const 页签 = await page.evaluate(() => ['风格广场', '特效广场', '我的收藏', '最近使用'].map((w) => {
  const e = [...document.querySelectorAll('button,[role="tab"]')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === w);
  if (!e) return { 文字: w, 找到: false };
  const c = getComputedStyle(e);
  return { 文字: w, 找到: true, 高亮: c.backgroundColor !== 'rgba(0, 0, 0, 0)' && c.backgroundColor !== 'transparent' };
}));
out.页签 = 页签;
LOG(`页签: ${JSON.stringify(页签.filter((p) => p.高亮).map((p) => p.文字))}（高亮）`);

out.特效结构 = 结构样本;
LOG(`\n══════ 响应结构样本 ══════`);
for (const s of 结构样本) LOG(`   ${s.接口}: 顶层键=${JSON.stringify(s.顶层键)} data=${s.data类型} data键=${JSON.stringify(s.data键)}`);

LOG(`\n抓到 ${收.size} 条卡记录`);
LOG(`⭐ 卡名样本: ${JSON.stringify([...收.values()].slice(0, 5).map((r) => r.name))}`);
const 首 = [...收.values()][0];
if (首) {
  LOG(`顶层字段 ${Object.keys(首).length} 个，有 runCount: ${Object.prototype.hasOwnProperty.call(首, 'runCount')}`);
  LOG(`计数字段: ${JSON.stringify(Object.keys(首).filter((k) => /Count$|heat|score/i.test(k)))}`);
}
out.记录数 = 收.size;
out.字段总数 = 首 ? Object.keys(首).length : 0;
out.有runCount = 首 ? Object.prototype.hasOwnProperty.call(首, 'runCount') : null;
out.计数类字段 = 首 ? Object.keys(首).filter((k) => /Count$|heat|score/i.test(k)) : null;
out.卡名样本 = [...收.values()].slice(0, 5).map((r) => r.name);

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
LOG(`\n══════ ⭐ 特效广场卡面数字对照 ══════\n可分析 ${总}（定位失败 ${失败}）｜符合 runCount ${符合}`);
for (const s of 样本) LOG(`   ${s.符合 ? '✅' : '⛔'} 「${s.卡面}」(${s.推算}) vs runCount=${s.runCount} ${s.精确 ? '精确' : s.近似 ? '缩写一致' : '都不符'} ｜ ${s.卡名.slice(0, 26)}`);
out.最终节点数 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDX3.json ===');
