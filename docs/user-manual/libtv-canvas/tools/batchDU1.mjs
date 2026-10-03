// Batch DU-1：卡面右下角那个数字，到底取自卡记录的哪个字段？
//
// ⭐ 为什么用这个办法：翻 chunk 挖不出来 ——
//   `downloadCount` / `imageCount` / `score` 在渲染 chunk `3-mou5v69wxmq.js` 里
//   **各 0 处**，`runCount` 的 9 处全是**协作回放冲突**（`tripped`/`threshold`），
//   和素材卡无关。⇒ 卡面那个数字要么在别的 chunk，要么经过格式化函数间接取。
//   ⭐ 改用**数据自证**：把每张卡的**界面数字**与**卡记录里每一个数值字段**
//   格式化后逐一对照 —— 对得上的那个就是来源。
//
// ⭐ 数字格式（从 DN 批实测反推）：`1.1w` / `6300` / `536.9w` / `309` / `2.3w`
//   ⇒ `>= 10000` 显示成 `x.xw`，否则原样。这个规则本轮要用读数**验证**，不假设。
//
// ⭐ 顺带：`delay7dDownCount` 在**全部 152 个 chunk（19MB）里 0 命中**
//   ⇒ 纯后端字段，前端不使用 ⇒ 它对用户不可见。查卡记录里到底有没有它。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 卡: [], 字段统计: null, 来源判定: null, delay7d: null };
const SAVE = () => writeFileSync(new URL('./batchDU1.json', import.meta.url), JSON.stringify(out, null, 2));

const { browser, page } = await launch();
const 收 = new Map(); // uuid -> 记录
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
await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(5500);

// ---- 读首屏每张卡：卡名 + 右下角那个数字 ----
const 屏上 = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width >= 150 && r.width <= 340 && r.height >= 180 && r.height <= 460 && s.visibility !== 'hidden'; };
  const 卡盒 = [];
  for (const e of document.querySelectorAll('div')) {
    if (!vis(e)) continue;
    const r = e.getBoundingClientRect();
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 90) continue;
    if (e.querySelectorAll('button').length < 2) continue;
    if (卡盒.some((b) => b.x === Math.round(r.x) && b.y === Math.round(r.y))) continue;
    卡盒.push({ x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height), 文本: t });
  }
  return 卡盒;
});
LOG(`首屏卡片盒 ${屏上.length} 个`);

// 从每张卡的文本里拆出：卡名（第一行）+ 数字（最后那个形如 1.1w / 6300 的 token）
const 拆 = (t) => {
  const m = t.match(/(?:^|\s)(\d+(?:\.\d+)?w?)(\s|$)/g);
  const 数 = m ? m.map((x) => x.trim()).filter((x) => /^\d+(\.\d+)?w?$/.test(x)) : [];
  return { 卡文本: t, 候选数字: 数 };
};
const 样本 = 屏上.map((c) => 拆(c.文本)).filter((s) => s.候选数字.length);
LOG(`带数字的卡 ${样本.length} 个`);
for (const s of 样本.slice(0, 6)) LOG(`   ${s.卡文本.slice(0, 60)} → ${JSON.stringify(s.候选数字)}`);

// ---- 建立「卡名 → uuid → 记录」映射 ----
const 按名 = new Map();
for (const [uuid, r] of 收) if (r.name && !按名.has(r.name)) 按名.set(r.name, { uuid, r });
LOG(`接口记录 ${收.size} 条，命名 ${按名.size} 条`);

const 转数字 = (s) => {
  if (typeof s === 'number') return s;
  if (typeof s !== 'string') return null;
  const w = /^\d+(\.\d+)?w$/.test(s);
  if (!w) { const n = Number(s); return Number.isFinite(n) ? n : null; }
  return Math.round(parseFloat(s) * 10000);
};

let 命中 = 0; const 字段命中 = {}; const 未能定位 = [];
for (const s of 样本) {
  // 卡名 = 文本里最长的一段非数字（通常是第一个 token 之前的标题）
  const 名 = s.卡文本.split(/\s{1,}/)[0];
  const 命中项 = [名, ...s.卡文本.split(/\s+/).slice(0, 3)].map((n) => 按名.get(n)).find(Boolean);
  if (!命中项) { 未能定位.push(s.卡文本.slice(0, 40)); continue; }
  const { uuid, r } = 命中项;
  const 卡面数 = s.候选数字.map(转数字).filter((x) => x != null);
  if (!卡面数.length) continue;
  // 卡记录里所有数值字段
  const 数值字段 = {};
  for (const [k, v] of Object.entries(r)) if (typeof v === 'number' && Number.isFinite(v)) 数值字段[k] = v;
  const 对上 = [];
  for (const [k, v] of Object.entries(数值字段)) for (const d of 卡面数) if (v === d) 对上.push(`${k}=${v}`);
  if (对上.length) { 命中 += 1; for (const x of 对上) { const f = x.split('=')[0]; 字段命中[f] = (字段命中[f] || 0) + 1; } }
  out.卡.push({ 卡名: 名, uuid, 卡面数字: s.候选数字, 数值字段, 对上 });
}
out.字段统计 = 字段命中;
out.未能定位数 = 未能定位.length;
LOG(`\n⭐ 对上号的卡: ${命中} / ${样本.length}`);
LOG(`⭐ 各字段命中次数: ${JSON.stringify(字段命中)}`);
LOG(`⛔ 没能按名定位的卡: ${未能定位.length} ${JSON.stringify(未能定位.slice(0, 5))}`);

// ---- delay7dDownCount 在卡记录里有没有 ----
const 首个 = [...收.values()][0];
out.字段总数 = 首个 ? Object.keys(首个).length : 0;
out.全部字段名 = 首个 ? Object.keys(首个) : [];
out.delay7d = {
  chunk命中: 0,
  记录里有这个字段: 首个 ? Object.prototype.hasOwnProperty.call(首个, 'delay7dDownCount') : null,
  相似字段: 首个 ? Object.keys(首个).filter((k) => /7d|delay|count|down/i.test(k)) : [],
};
LOG(`\n卡记录顶层字段 ${out.字段总数} 个`);
LOG(`含 7d/delay/count/down 的字段: ${JSON.stringify(out.delay7d.相似字段)}`);
LOG(`delay7dDownCount 在记录里: ${out.delay7d.记录里有这个字段}`);

// 来源判定
const 排序 = Object.entries(字段命中).sort((a, b) => b[1] - a[1]);
out.来源判定 = 排序.length ? { 字段: 排序[0][0], 次数: 排序[0][1] } : null;
LOG(`\n══════ ⭐ 判定 ══════`);
LOG(`卡面数字最可能来自: ${排序.length ? JSON.stringify(排序.slice(0, 3)) : '⛔ 没对上任何字段'}`);
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDU1.json ===');
