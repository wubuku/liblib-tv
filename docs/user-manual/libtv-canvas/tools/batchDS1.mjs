// Batch DS-1：找到「多模型卡」，把详情浮层的第二个分区补上。
//
// 目标：DR 批在正文里写了「其余适配模型」这一栏的显示条件，
//      但本轮那张 `Seedream 5.0 pro` 是单模型卡 ⇒ 那一栏没渲染出来 📖。
//      本轮要找一张**多模型卡**，把这一栏真正拍到。
//
// ⭐⭐⭐ 判据是从渲染 chunk 里挖出来的（`3-mou5v69wxmq.js`），**不用猜**：
//   let r = e.baseType;                                  // 卡记录的 baseType 字段
//   if (r == null) return { preferred: undefined, others: [] };
//   let a = Array.isArray(r) ? r : [r];
//   ... return { preferred: o[0], others: o.slice(1) };
//   ⇒ `baseType` 为 null/nullish  ⇒ 两个分区都不渲染
//   ⇒ `baseType` 是**单值**      ⇒ 只有「首选推荐模型」，others 为空
//   ⇒ ⭐ `baseType` 是**长度≥2 的数组** ⇒ 才会出现「其余适配模型」分区
//
// ⭐ 本脚本只做**发现**：把前几页卡的完整记录抓下来，统计 baseType 分布，
//   找出多模型卡的名字。**先确认这种卡存在，再开浮层拍**（§200 铁律：阴性不落结论）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const 本类 = '520047,520048,520049,520050,520051,520052,520053,510011,510012,510013,510014,510015,510016,510017';
const out = { 判据: 'baseType 是长度>=2 的数组 = 多模型卡', 分类: '风格插画', 卡: [], 分布: null, 多模型卡: null };
const SAVE = () => writeFileSync(new URL('./batchDS1.json', import.meta.url), JSON.stringify(out, null, 2));

const { browser, page } = await launch();
const 收 = [];
page.on('response', async (resp) => {
  try {
    if (!/model\/feed\/stream/.test(resp.url())) return;
    const t = await resp.text(); if (!t) return;
    let j; try { j = JSON.parse(t); } catch { return; }
    const arr = (j?.data?.data) || [];
    if (!arr.length) return;
    for (const r of arr) 收.push(r);
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
await page.waitForTimeout(3000);

// 抓 3 页就够做分布统计
for (let i = 0; i < 4; i += 1) {
  await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = v.scrollHeight; });
  await page.waitForTimeout(2300);
  LOG(`  已抓 ${收.length} 条卡记录`);
  if (收.length >= 120) break;
}

// ⛔ DS-1 第一版的错：拿 `r.tagIds` 归属 ⇒ 0 条。
//   `tagIds` 是**请求参数**，**卡记录里根本没有这个字段**（DR 批判的是请求体）。
//   ⭐ 这次不必再判分类：本脚本要回答的是「**有没有多模型卡**」，在哪个分类都行。
const 本类的 = 收;
LOG(`\n总抓 ${收.length} 条卡记录`);
if (收.length) {
  LOG(`一条卡的字段数: ${Object.keys(收[0]).length}`);
  LOG(`全部字段名: ${Object.keys(收[0]).join(', ')}`);
}
if (本类的.length) {
  const c0 = 本类的[0];
  LOG(`一条卡的顶层字段（${Object.keys(c0).length} 个）: ${Object.keys(c0).join(', ')}`);
}

// ---- baseType 分布 ----
const 判 = (b) => {
  if (b == null) return 'null/undefined';
  if (Array.isArray(b)) return `数组(${b.length})`;
  return `单值(${typeof b})`;
};
const 分布 = {};
for (const r of 本类的) { const k = 判(r.baseType); 分布[k] = (分布[k] || 0) + 1; }
out.分布 = 分布;
out.样本 = 本类的.slice(0, 3).map((r) => ({ name: r.name, baseType: r.baseType, modelNames: r.modelNames ?? null, models: r.models ?? null, adaptModels: r.adaptModels ?? null, keys: Object.keys(r).filter((k) => /model|type/i.test(k)) }));
LOG(`\n⭐ baseType 分布（风格插画 ${本类的.length} 张）:`);
for (const [k, v] of Object.entries(分布)) LOG(`   ${k}: ${v}`);
LOG(`\n模型相关的字段名: ${JSON.stringify(out.样本[0]?.keys ?? [])}`);
LOG(`样本: ${JSON.stringify(out.样本.slice(0, 2), null, 1)}`);

// ---- 多模型卡 ----
const 多 = 本类的.filter((r) => Array.isArray(r.baseType) && r.baseType.length >= 2);
out.多模型卡 = { 数量: 多.length, 前若干: 多.slice(0, 20).map((r) => ({ name: r.name, uuid: r.uuid, baseType: r.baseType })) };
LOG(`\n⭐⭐ 风格插画里的多模型卡: ${多.length} 张`);
LOG(JSON.stringify(多.slice(0, 10).map((r) => ({ name: r.name, baseType: r.baseType })), null, 1));
if (!多.length) LOG('⛔ 这一类里没有多模型卡 —— 需要换分类再试');
out.卡 = 本类的.map((r) => ({ name: r.name, uuid: r.uuid, baseType: r.baseType }));
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDS1.json ===');
