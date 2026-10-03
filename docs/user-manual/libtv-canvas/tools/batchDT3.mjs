// Batch DT-3：用**搜索框**定位卡，把「baseType → 模型名」对照表凑出来。
//
// ⛔ DT-2 为什么只测到 1 张：
//   靠「一屏一屏滚 + 读视口卡名」定位。第一屏视口提取到 112 个短文本、之后每屏 35 个，
//   但**滚动后那些名字一个都对不上接口映射** —— 虚拟滚动把卡回收又重建，
//   DOM 里的短文本不再稳定等于卡名。
//   ⇒ **换成确定性定位：搜索框。** 输入卡名 → 服务端过滤 → 结果里只剩这一张。
//   搜索不受虚拟滚动影响，这是这块广场里**唯一稳定**的定位方式。
//
// ⭐ 目标：验证 DS 批那条推断，并凑出「baseType → 模型名」的实测切片。
//   已知：赛璐璐光影 baseType=[81,70,68,55,40,27] → 浮层 5 个，**缺口 1**
//   兜底表里有 baseType 37（qwen-image → Qwen Image）、40（nebula-ultra → General image Pro）
//   ⭐ 本轮特意挑 **含 37 / 19 / 1** 的卡，看能不能带出兜底表那两个模型。
//
// ⛔ 只读：开浮层 → 读 → ESC。**不点「使用」、不点「收藏」、不应用风格、不下单。**
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 定位方式: '搜索框（不受虚拟滚动影响）', 卡池: [], 采样: [], 并集: null, 对照: null };
const SAVE = () => writeFileSync(new URL('./batchDT3.json', import.meta.url), JSON.stringify(out, null, 2));

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
LOG(`进场分类: ${当前}`);
if (当前 === '风格插画') {
  await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').trim() === '平面设计'); if (b) b.click(); });
  await page.waitForTimeout(3000);
}
await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '风格插画'); if (b) b.click(); });
await page.waitForTimeout(3500);

// 滚 3 页把卡池铺开
for (let i = 0; i < 4; i += 1) {
  await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = v.scrollHeight; });
  await page.waitForTimeout(2100);
}
LOG(`卡池: ${卡映射.size} 张`);
out.卡池 = [...卡映射.entries()].map(([名, bt]) => ({ 名, baseType: bt }));
SAVE();

// ⭐ 挑采样：优先 baseType 里含 37 / 19 / 1 的（兜底表那两个模型所在），再补不同的组合
const 全 = [...卡映射.entries()].filter(([, bt]) => bt.length >= 2);
const 打分 = (bt) => (bt.includes(37) ? 100 : 0) + (bt.includes(19) ? 50 : 0) + (bt.includes(1) ? 25 : 0) + bt.length;
const 排序 = 全.slice().sort((a, b) => 打分(b[1]) - 打分(a[1]));
const 采样 = []; const 用过组合 = new Set();
for (const [名, bt] of 排序) { const k = bt.join(','); if (用过组合.has(k)) continue; 用过组合.add(k); 采样.push({ 名, baseType: bt }); if (采样.length >= 5) break; }
LOG(`\n采样 ${采样.length} 张（baseType 组合互不相同）:`);
for (const s of 采样) LOG(`  ${s.名}  [${s.baseType}]`);

// ---- 搜索框定位 + 读浮层 ----
const 搜索定位 = async (名) => {
  const inp = page.locator('input[placeholder*="搜索风格"]').first();
  await inp.click({ timeout: 8000 });
  await inp.fill('');
  await page.waitForTimeout(500);
  await inp.fill(名);
  await page.waitForTimeout(3200);
  return page.evaluate((名) => {
    const e = [...document.querySelectorAll('p,h3,span,div')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === 名 && x.children.length === 0);
    if (!e) return { 找到: false };
    let c = e; for (let i = 0; i < 8 && c; i += 1) { const r = c.getBoundingClientRect(); if (r.width >= 150 && r.width <= 340 && r.height >= 180 && r.height <= 460) break; c = c.parentElement; }
    const r = c.getBoundingClientRect();
    if (r.width <= 0) return { 找到: false, 原因: '盒子尺寸 0（不在视口）' };
    return { 找到: true, 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], 卡片文本: (c.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 100) };
  }, 名);
};

const 读一张 = async (名, baseType) => {
  const 定位 = await 搜索定位(名);
  if (!定位.找到) { LOG(`  ⛔ 搜索「${名}」后 DOM 里没有：${定位.原因 || ''}`); return { 名, baseType, 错: '搜索后定位不到' }; }
  await page.mouse.move(定位.中心[0], 定位.中心[1]);
  await page.waitForTimeout(800);
  const 点 = await page.evaluate((名) => {
    const e = [...document.querySelectorAll('p,h3,span,div')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === 名 && x.children.length === 0);
    if (!e) return '没找到卡名元素';
    let c = e; for (let i = 0; i < 8 && c; i += 1) { const r = c.getBoundingClientRect(); if (r.width >= 150 && r.width <= 340 && r.height >= 180 && r.height <= 460) break; c = c.parentElement; }
    const vis = (x) => { const r = x.getBoundingClientRect(); const s = getComputedStyle(x); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0.3; };
    const bs = [...c.querySelectorAll('button')].filter(vis);
    if (!bs.length) return `可见 button 0 枚（共 ${c.querySelectorAll('button').length}）`;
    bs[bs.length - 1].click(); return 'ok';
  }, 名);
  if (点 !== 'ok') { await page.keyboard.press('Escape'); return { 名, baseType, 错: `点详情:${点}` }; }
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
  if (!读.有浮层) return { 名, baseType, 错: '点了但没浮层' };
  const y首 = 读.叶.find((r) => r.文字 === '首选推荐模型')?.y;
  const y其 = 读.叶.find((r) => r.文字 === '其余适配模型')?.y;
  const 首选 = 读.叶.filter((r) => r.y > (y首 ?? 1e9) && (y其 == null || r.y < y其)).map((r) => r.文字).filter((t) => t !== '首选推荐模型' && t.length <= 40);
  const 其余 = y其 == null ? [] : 读.叶.filter((r) => r.y > y其).map((r) => r.文字).filter((t) => t !== '其余适配模型' && !/^(收藏|取消收藏|使用)$/.test(t) && t.length <= 40);
  return { 名, baseType, 首选, 其余, 全文: 读.全文, 列了几个: 首选.length + 其余.length };
};

for (const s of 采样) {
  LOG(`\n读「${s.名}」 baseType=[${s.baseType}]`);
  const r = await 读一张(s.名, s.baseType);
  out.采样.push(r);
  if (r.错) LOG(`  ⛔ ${r.错}`); else LOG(`  ✅ 列了 ${r.列了几个} 个：首选 ${JSON.stringify(r.首选)} | 其余 ${JSON.stringify(r.其余)}`);
  SAVE();
}

// 清空搜索，恢复原状
const inp = page.locator('input[placeholder*="搜索风格"]').first();
await inp.click({ timeout: 5000 }).catch(() => {});
await inp.fill('').catch(() => {});
await page.waitForTimeout(2000);

// ---- 汇总 ----
const 并集 = new Map();
for (const r of out.采样) { if (r.错) continue; for (const m of [...r.首选, ...r.其余]) { if (!并集.has(m)) 并集.set(m, []); 并集.get(m).push(r.名); } }
out.并集 = [...并集.entries()].map(([模型, 出现在]) => ({ 模型, 次数: 出现在.length, 出现在 }));
out.对照 = out.采样.map((r) => ({ 名: r.名, baseType: r.baseType, baseType个数: r.baseType?.length, 浮层列了: r.列了几个 ?? null, 缺口: r.错 ? null : r.baseType.length - r.列了几个 }));
LOG('\n══════ ⭐ baseType 个数 vs 浮层列出数 ══════');
for (const c of out.对照) LOG(`  ${c.名}: baseType ${c.baseType个数} [${c.baseType}] → 浮层 ${c.浮层列了} 缺口 ${c.缺口}`);
LOG('\n══════ 模型并集 ══════');
for (const m of out.并集) LOG(`  ${m.模型}  ${m.次数} 次`);
out.最终节点数 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDT3.json ===');
