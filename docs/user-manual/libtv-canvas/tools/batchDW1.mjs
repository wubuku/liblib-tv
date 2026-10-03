// Batch DW-1：把广场页签的**真实 DOM** 定位出来，并补验特效广场的 `runCount`。
//
// ⛔ DV-1 / DV-2 连着失败，根因都是**用猜的坐标范围和猜的文字去找页签**：
//   · 找「特效库」—— 那是侧栏抽屉里的入口，广场打开后就收起来了
//   · 找「特效广场」—— 按钮不存在（i18n 文案 ≠ 实际 DOM 文字）
//   · 探针取 `y 130~290` —— 页签候选 0 个（页签实际在 y<130）
//
// ⭐ 本轮的做法：**用已知文字反查**，不猜坐标也不猜标签名。
//   DN 批早就逐字读过那一排是 `风格广场 / 特效广场 / 我的收藏 / 最近使用` ——
//   ⭐ 如果按这些文字**一个都找不到**，那就说明：**文字不是节点的 `innerText`**，
//      得去看它们被拆成了什么子节点。这才是真正的定位思路。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 反查: null, 顶栏全量: null, 特效: null };
const SAVE = () => writeFileSync(new URL('./batchDW1.json', import.meta.url), JSON.stringify(out, null, 2));

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
await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(5500);

// ---------- ① 已知文字反查 ----------
const 反查 = await page.evaluate(() => {
  const 目标 = ['风格广场', '特效广场', '我的收藏', '最近使用'];
  const 全 = [...document.querySelectorAll('button,[role="tab"],a,span,div,li')];
  const 命中 = [];
  for (const w of 目标) {
    const 找 = 全.filter((e) => (e.innerText || '').replace(/\s+/g, ' ').trim() === w);
    命中.push({
      文字: w, 找到几个: 找.length,
      节点: 找.slice(0, 3).map((e) => {
        const r = e.getBoundingClientRect(); const c = getComputedStyle(e);
        return { tag: e.tagName.toLowerCase(), role: e.getAttribute('role') || '', aria: e.getAttribute('aria-label') || '', selected: e.getAttribute('aria-selected'), 背景: c.backgroundColor, 位置: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 子元素: e.children.length, html: (e.innerHTML || '').slice(0, 90) };
      }),
    });
  }
  return 命中;
});
out.反查 = 反查;
LOG('══════ ① 已知文字反查 ══════');
for (const h of 反查) {
  LOG(`「${h.文字}」找到 ${h.找到几个} 个`);
  for (const n of h.节点) LOG(`    [${n.tag}${n.role ? '/' + n.role : ''}] bg=${n.背景} @${n.位置.join(',')} 子${n.子元素} ${n.aria ? 'aria=' + n.aria : ''}${n.selected ? ' selected=' + n.selected : ''}`);
}

// ---------- ② 顶栏全量（y<160，不限长度，看清结构）----------
const 顶 = await page.evaluate(() => {
  const 行 = [];
  for (const e of document.querySelectorAll('button,[role="tab"],a')) {
    const r = e.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    if (r.y < 0 || r.y > 200) continue;
    const c = getComputedStyle(e);
    行.push({ tag: e.tagName.toLowerCase(), role: e.getAttribute('role') || '', 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24), aria: e.getAttribute('aria-label') || '', 背景: c.backgroundColor, 位置: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
  }
  return 行;
});
out.顶栏全量 = 顶;
LOG(`\n══════ ② 顶栏全量（y<200 的 button/tab/a）${顶.length} 个 ══════`);
for (const b of 顶) LOG(`   [${b.tag}${b.role ? '/' + b.role : ''}] 「${b.文字}」 bg=${b.背景} @${b.位置.join(',')}${b.aria ? ' aria=' + b.aria : ''}`);
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDW1.json ===');
