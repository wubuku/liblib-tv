// Batch DU-2：验证卡面数字的「w 缩写」规则，让「= runCount」这条结论覆盖带 w 的样本。
//
// ⭐ DU-1 已经坐实：卡面右下角那个数字 **= 卡记录的 `runCount`**（12/12 精确相等，
//   其余 62 个字段一个都没命中）。但 12 个样本全是 4 位数（没触发缩写），
//   像 `1.1w` / `2.4w` / `537.5w` 那几个**没按名定位到**，所以：
//   ⛔ 「>= 10000 显示成 x.xw」这条规则**本轮还没验证**。
//
// ⛔ DU-1 卡名提取的错：用 `文本.split(/\s+/)[0]` 取第一个 token
//   ⇒ `Qwen Image 妆造一体博主感写真 LoRA` 被截成 `Qwen`，只有无空格卡名才对上。
//   ⭐ 本轮改成**子串双向匹配**（DOM 文本 ⊇ 记录 name，或反过来）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 样本: [], 规则验证: null };
const SAVE = () => writeFileSync(new URL('./batchDU2.json', import.meta.url), JSON.stringify(out, null, 2));

const { browser, page } = await launch();
const 收 = new Map();
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

const 屏上 = await page.evaluate(() => {
  const 卡盒 = [];
  for (const e of document.querySelectorAll('div')) {
    const r = e.getBoundingClientRect();
    if (!(r.width >= 150 && r.width <= 340 && r.height >= 180 && r.height <= 460)) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 90) continue;
    if (e.querySelectorAll('button').length < 2) continue;
    if (卡盒.some((b) => b.x === Math.round(r.x) && b.y === Math.round(r.y))) continue;
    卡盒.push({ 文本: t });
  }
  return 卡盒;
});

const 转 = (s) => {
  const w = /^(\d+(?:\.\d+)?)w$/.exec(s);
  if (w) return Math.round(parseFloat(w[1]) * 10000);
  const n = Number(s); return Number.isFinite(n) ? n : null;
};
// ⭐ 子串双向匹配：DOM 文本里含记录名，或记录名里含 DOM 文本的某段
const 找记录 = (文本) => {
  let best = null;
  for (const r of 收.values()) {
    if (!r.name) continue;
    if (文本.includes(r.name) || r.name.includes(文本.slice(0, 12))) {
      if (!best || r.name.length > best.name.length) best = r;
    }
  }
  return best;
};

let 对上 = 0, 带w = 0, 带w对上 = 0, 定位失败 = 0;
const 规则样本 = [];
for (const c of 屏上) {
  const 数tok = (c.文本.match(/(?<![\d.])\d+(?:\.\d+)?w?(?![\w])/g) || []).filter((x) => /\d/.test(x));
  // 排除卡名里的数字（如 `Seedream 5.0`、`SD 2.5`）—— 只留末尾那个「计数位」的候选
  const 末 = 数tok[数tok.length - 1];
  if (!末) continue;
  const 卡面 = 转(末);
  if (卡面 == null) continue;
  const r = 找记录(c.文本);
  if (!r) { 定位失败 += 1; continue; }
  const rc = r.runCount;
  const 相同 = rc === 卡面;
  if (相同) 对上 += 1;
  if (/w$/.test(末)) { 带w += 1; if (相同) 带w对上 += 1; }
  规则样本.push({ 卡面文本: 末, 卡面推算值: 卡面, 卡名: r.name, runCount: rc, 相同 });
}
out.样本 = 规则样本;
LOG(`样本 ${规则样本.length} 个（定位失败 ${定位失败}）｜对上 ${对上}｜带 w 的 ${带w} 个，其中对上 ${带w对上}`);
LOG('\n=== 带 w 的样本（验证缩写规则）===');
for (const s of 规则样本.filter((x) => /w$/.test(x.卡面文本))) {
  LOG(`   卡面「${s.卡面文本}」→ 推算 ${s.卡面推算值} ｜ runCount=${s.runCount} ${s.相同 ? '✅' : '⛔'}`);
}
LOG('\n=== 对不上的（若有）===');
for (const s of 规则样本.filter((x) => !x.相同)) LOG(`   卡面「${s.卡面文本}」(${s.卡面推算值}) vs runCount=${s.runCount} ｜ ${s.卡名}`);

out.规则验证 = { 样本数: 规则样本.length, 对上, 带w, 带w对上, 定位失败, 结论: 对上 === 规则样本.length ? '全部等于 runCount' : `有 ${规则样本.length - 对上} 个对不上` };
LOG(`\n══════ ⭐ 判定 ══════\n${out.规则验证.结论}`);
out.最终节点数 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDU2.json ===');
