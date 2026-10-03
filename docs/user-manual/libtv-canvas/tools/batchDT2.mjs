// Batch DT-2：扫多张多模型卡，把「baseType → 模型名」对照表在界面上凑出来。
//
// ⭐ 背景：
//   · DS 批：详情浮层的模型分区按 `baseType` 到 `styleModelList` 里 `find`，
//     **`赛璐璐光影` baseType 有 6 个值、浮层只列 5 个模型** ⇒ 有一个匹配不到。
//   · 源码里的 `styleModelList` 只有一张 **2 条兜底表**，线上走远程配置
//     （`useRemotePanelConfig` → `getRemoteConfig`），DT-1 抓接口 ⛔ 没抓到。
//   ⇒ **换一条路：从界面上把表读出来。**
//     每张多模型卡的浮层会列出它 `baseType` 能匹配上的那些模型，
//     ⭐ **扫多张卡取并集** = 这张表的实测切片。
//
// ⭐ 本轮同时验证 DS 批那条推断：
//   **baseType 里凡是表上没有的，浮层就少一项。**
//   已知：81 / 70 / 68 / 55 / 40 / 27 里有一个匹配不上（6 → 5）
//   已知：37 出现在兜底表里（qwen-image → Qwen Image）
//
// ⛔ 只读：开浮层 → 读 → ESC。**不点「使用」、不点「收藏」、不应用风格。**
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 判据: 'baseType 到 styleModelList 匹配', 卡: [], 并集: null, 对照: null };
const SAVE = () => writeFileSync(new URL('./batchDT2.json', import.meta.url), JSON.stringify(out, null, 2));

const { browser, page } = await launch();
const 卡映射 = new Map();
page.on('response', async (resp) => {
  try {
    if (!/model\/feed\/stream/.test(resp.url())) return;
    const t = await resp.text(); if (!t) return;
    let j; try { j = JSON.parse(t); } catch { return; }
    for (const r of (j?.data?.data) || []) if (r && r.name && Array.isArray(r.baseType) && !卡映射.has(r.name)) 卡映射.set(r.name, r.baseType);
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
if (当前 === '风格插画') {
  await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').trim() === '平面设计'); if (b) b.click(); });
  await page.waitForTimeout(3000);
}
await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '风格插画'); if (b) b.click(); });
await page.waitForTimeout(3500);

const 视口卡名 = () => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden'; };
  const 叶 = [...document.querySelectorAll('p,h3,span,div')].filter((e) => { const t = (e.innerText || '').replace(/\s+/g, ' ').trim(); return t && t.length >= 2 && t.length <= 40 && e.children.length === 0 && vis(e); });
  return [...new Set(叶.map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()))];
});

const 开浮层读 = async (卡名) => {
  const 盒 = await page.evaluate((名) => {
    const e = [...document.querySelectorAll('p,h3,span,div')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === 名 && x.children.length === 0);
    if (!e) return null;
    let c = e; for (let i = 0; i < 8 && c; i += 1) { const r = c.getBoundingClientRect(); if (r.width >= 150 && r.width <= 340 && r.height >= 180 && r.height <= 460) break; c = c.parentElement; }
    const r = c.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  }, 卡名);
  if (!盒) return { 卡名, 错: '定位不到卡片盒子' };
  await page.mouse.move(盒[0], 盒[1]);
  await page.waitForTimeout(800);
  const 点 = await page.evaluate((名) => {
    const e = [...document.querySelectorAll('p,h3,span,div')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === 名 && x.children.length === 0);
    if (!e) return '没找到卡名元素';
    let c = e; for (let i = 0; i < 8 && c; i += 1) { const r = c.getBoundingClientRect(); if (r.width >= 150 && r.width <= 340 && r.height >= 180 && r.height <= 460) break; c = c.parentElement; }
    const vis = (x) => { const r = x.getBoundingClientRect(); const s = getComputedStyle(x); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0.3; };
    const bs = [...c.querySelectorAll('button')].filter(vis);
    if (!bs.length) return '可见 button 0 枚';
    bs[bs.length - 1].click(); return 'ok';
  }, 卡名);
  if (点 !== 'ok') return { 卡名, 错: `点详情失败:${点}` };
  await page.waitForTimeout(2200);
  const 读 = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const 全 = [...document.querySelectorAll('div')].filter((e) => { const t = (e.innerText || '').replace(/\s+/g, ' '); return vis(e) && /风格详情/.test(t) && /使用/.test(t); });
    if (!全.length) return { 有浮层: false };
    const 详 = 全.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
    const 叶 = [...详.querySelectorAll('*')].filter((e) => { const t = (e.innerText || '').replace(/\s+/g, ' ').trim(); return t && t.length <= 60 && e.children.length === 0; })
      .map((e) => ({ 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), y: Math.round(e.getBoundingClientRect().y) }));
    return { 有浮层: true, 全文: (详.innerText || '').replace(/\n+/g, ' | ').slice(0, 800), 叶 };
  });
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1000);
  if (!读.有浮层) return { 卡名, 错: '点了但没浮层' };
  // 切出两个分区
  const y首 = 读.叶.find((r) => r.文字 === '首选推荐模型')?.y;
  const y其 = 读.叶.find((r) => r.文字 === '其余适配模型')?.y;
  const 首选 = 读.叶.filter((r) => r.y > (y首 ?? 1e9) && (y其 == null || r.y < y其)).map((r) => r.文字).filter((t) => t !== '首选推荐模型' && t.length <= 40);
  const 其余 = y其 == null ? [] : 读.叶.filter((r) => r.y > y其).map((r) => r.文字).filter((t) => t !== '其余适配模型' && !/^(收藏|取消收藏|使用)$/.test(t) && t.length <= 40);
  return { 卡名, baseType: 卡映射.get(卡名), 首选, 其余, 有其余分区: y其 != null, 全文: 读.全文 };
};

// ---- 一屏一屏扫，每屏取第一张多模型卡 ----
const 结果 = [];
const 已测 = new Set();
for (let 屏 = 0; 屏 < 10 && 结果.length < 5; 屏 += 1) {
  if (屏 > 0) {
    await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop += v.clientHeight * 0.9; });
    await page.waitForTimeout(1700);
  }
  const 名集 = await 视口卡名();
  const 候选 = 名集.filter((n) => { const bt = 卡映射.get(n); return Array.isArray(bt) && bt.length >= 2 && !已测.has(n); });
  LOG(`第 ${屏} 屏: 视口 ${名集.length} 卡 / 未测的多模型候选 ${候选.length}`);
  if (!候选.length) continue;
  for (const 名 of 候选.slice(0, 2)) {
    if (结果.length >= 5) break;
    LOG(`  读「${名}」 baseType=${JSON.stringify(卡映射.get(名))}`);
    const r = await 开浮层读(名);
    已测.add(名); 结果.push(r);
    if (r.错) LOG(`    ⛔ ${r.错}`); else LOG(`    首选 ${JSON.stringify(r.首选)} | 其余 ${JSON.stringify(r.其余)}`);
    SAVE();
    await page.mouse.move(20, 400);
    await page.waitForTimeout(500);
  }
}
out.卡 = 结果;

// ---- 汇总：模型名并集 + 与 baseType 的对应 ----
const 并集 = new Map();
for (const r of 结果) { if (r.错) continue; for (const m of [...(r.首选 || []), ...(r.其余 || [])]) if (!并集.has(m)) 并集.set(m, []); for (const m of [...(r.首选 || []), ...(r.其余 || [])]) 并集.get(m).push(r.卡名); }
out.并集 = [...并集.entries()].map(([模型, 出现在]) => ({ 模型, 出现在, 次数: 出现在.length }));

// ⭐ 逐卡核对：baseType 有几个能对上模型名
const 对照 = 结果.filter((r) => !r.错).map((r) => ({ 卡名: r.卡名, baseType: r.baseType, baseType个数: r.baseType.length, 浮层列了几个: (r.首选?.length || 0) + (r.其余?.length || 0), 首选: r.首选, 其余: r.其余, 缺口: r.baseType.length - ((r.首选?.length || 0) + (r.其余?.length || 0)) }));
out.对照 = 对照;
LOG('\n══════ ⭐ baseType 个数 vs 浮层列出数 ══════');
for (const c of 对照) LOG(`  ${c.卡名}: baseType ${c.baseType?.length} 个 [${c.baseType}] → 浮层 ${c.浮层列了几个} 个 缺口 ${c.缺口 > 0 ? c.缺口 : '0'}`);
LOG('\n══════ 模型并集 ══════');
for (const m of out.并集) LOG(`  ${m.模型}  出现 ${m.次数} 次`);
out.最终节点数 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDT2.json ===');
