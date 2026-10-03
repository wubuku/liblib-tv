// Batch DN-2：把「仅看可商用」到底筛什么，测出来。
//
// DN-1 拿到了参数（勾选后请求多一个 `modelLicense:["1"]`），
// 但**首屏 30 张卡名一个没变** ⇒ 阳性对照不充分，两种可能：
//   ① 那个分类首屏**恰好全是可商用卡** ⇒ 筛了也看不出差别
//   ② 筛选**根本没生效**
// ⇒ **分不清就是没测到。** 本步先解决「①还是②」。
//
// ⭐ 方法：先**盘出各分类里有多少张卡带「商用」徽标**，
//    找到一个混得开的分类，再在它上面做「关→开→关」对照，
//    而且**两边都滚到底**比完整卡名集合（只比首屏 30 张不够）。
//
// ⚠️ DN-1 的一个取数缺陷先修掉：它只取 `innerText.split('\n')[0]` 当卡名，
//    而「商用」徽标**没被抓到**（读出来 0 个含「商用」）——
//    说明卡名那一行不止一个片段。本步先打印**完整 innerText** 看清结构。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 结构样本: null, 各分类商用统计: [], 对照: null };
const SAVE = () => writeFile(new URL('./batchDN2.json', import.meta.url), JSON.stringify(out, null, 2));

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

const 请求队列 = [];
page.on('response', async (resp) => {
  try {
    if (!/model\/feed\/stream/.test(resp.url())) return;
    let bj = {}; try { bj = JSON.parse(resp.request().postData() || '{}'); } catch { /* 忽略 */ }
    const t = await resp.text(); if (!t) return;
    let j; try { j = JSON.parse(t); } catch { return; }
    请求队列.push({ page: j?.data?.page, 条数: (j?.data?.data || []).length, modelLicense: bj.modelLicense ?? null, tagIds: bj.tagIds ?? null });
  } catch { /* 忽略 */ }
});

await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(5000);

// ---------- 完整读法：整张卡的 innerText 全量 + 逐行 ----------
const 读 = () => page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  const modals = [...document.querySelectorAll('.mantine-Modal-inner')].filter(vis);
  const root = modals.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
  if (!root) return { 有弹层: false };
  const 卡 = new Set();
  for (const D of root.querySelectorAll('button[aria-label="详情"]')) {
    for (let p = D.parentElement, j = 0; p && j < 6; p = p.parentElement, j += 1) {
      const r = p.getBoundingClientRect();
      if (r.width > 150 && r.width < 260 && r.height > 260) { 卡.add(p); break; }
    }
  }
  const 全部 = [...卡];
  return {
    DOM卡数: 全部.length,
    全文: 全部.map((e) => (e.innerText || '').replace(/ /g, ' ')),
    行集: 全部.map((e) => (e.innerText || '').split('\n').map((s) => s.trim()).filter(Boolean)),
  };
});

const 切 = async (名) => { await page.evaluate((n) => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === n); if (b) b.click(); }, 名); await page.waitForTimeout(3800); };
const 勾选 = () => page.evaluate(() => {
  for (const lb of document.querySelectorAll('label,div,span')) {
    if (/仅看可商用/.test(lb.textContent || '') && lb.children.length <= 2) {
      const inp = lb.querySelector('input[type="checkbox"]');
      if (inp) { inp.click(); return inp.checked; }
    }
  }
  return null;
});

// ---------- ① 先看卡的结构（拿到完整 innerText） ----------
const s = await 读();
LOG('=== ① 卡的结构样本（前 3 张，完整 innerText 按行拆）===');
for (let i = 0; i < Math.min(3, s.行集.length); i += 1) {
  LOG(`  卡${i + 1}: ${JSON.stringify(s.行集[i])}`);
}
out.结构样本 = s.行集.slice(0, 5);
LOG(`  全文样本: ${JSON.stringify(s.全文.slice(0, 3))}`);
SAVE();

// ---------- ② 盘各分类的「商用」徽标比例 ----------
LOG('\n=== ② 各分类首屏「商用」徽标比例 ===');
for (const 名 of ['推荐', '摄影写真', '电商营销', '动漫游戏', '风格插画', '平面设计', '建筑及室内设计', '创意玩法', '文创周边', '小说推文']) {
  await 切(名);
  await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = 0; });
  await page.waitForTimeout(1200);
  const r = await 读();
  const 有商用 = r.全文.filter((t) => /商用/.test(t)).length;
  const rec = { 分类: 名, 首屏DOM: r.DOM卡数, 含商用文案: 有商用, 无商用: r.DOM卡数 - 有商用 };
  out.各分类商用统计.push(rec);
  LOG(`  ${名}: DOM ${r.DOM卡数} | 含「商用」 ${有商用} | 不含 ${r.DOM卡数 - 有商用}`);
  SAVE();
}

// ---------- ③ 找一个混得开的分类，做「关→开」全量对照 ----------
const 混 = out.各分类商用统计.find((x) => x.含商用文案 > 0 && x.无商用 > 0) || out.各分类商用统计[0];
LOG(`\n=== ③ 选「${混.分类}」做全量对照（首屏 ${混.含商用文案} 含商用 / ${混.无商用} 不含）===\n`);

const 收全 = async () => {
  // 滚到底，累积出现过的卡名集合
  const 见过 = new Set();
  for (let i = 0; i < 26; i += 1) {
    const r = await 读();
    for (const t of r.全文) 见过.add(t.split('\n')[0].trim());
    const m = await page.evaluate(() => {
      const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600);
      if (!v) return null;
      const 到 = Math.round(v.scrollTop) >= Math.round(v.scrollHeight) - Math.round(v.clientHeight) - 8;
      v.scrollTop = v.scrollHeight;
      return { 到, 请求数: 0 };
    });
    await page.waitForTimeout(1500);
    if (m && m.到 && i > 3) break;
  }
  return [...见过];
};

await 切(混.分类);
await 勾选(); // 关闭状态：先确保关（如果原来是开就再点一次）
await page.waitForTimeout(500);
const 关态 = await 勾选();
if (关态) { await page.waitForTimeout(2000); }  // 它刚点了，需要重新读
const 当前 = await page.evaluate(() => {
  for (const lb of document.querySelectorAll('label,div,span')) {
    if (/仅看可商用/.test(lb.textContent || '') && lb.children.length <= 2) {
      const inp = lb.querySelector('input[type="checkbox"]');
      if (inp) return inp.checked;
    }
  }
  return null;
});
LOG(`确认当前勾选状态: ${当前}`);
if (当前) { await 勾选(); await page.waitForTimeout(3000); }   // 关掉

const 关请求 = 请求队列.length;
const 关集 = await 收全();
LOG(`关闭态: 累计卡名 ${关集.length} 个（发了 ${请求队列.length - 关请求} 个请求）`);

await 勾选();   // 打开
await page.waitForTimeout(3500);
const 开请求 = 请求队列.length;
const 开集 = await 收全();
LOG(`打开态: 累计卡名 ${开集.length} 个（发了 ${请求队列.length - 开请求} 个请求）`);

const A = new Set(关集); const B = new Set(开集);
const 被筛掉 = 关集.filter((x) => !B.has(x));
const 新出现 = 开集.filter((x) => !A.has(x));
LOG(`\n⭐⭐ 对照结果: 关闭 ${A.size} / 打开 ${B.size} | ⛔被筛掉 ${被筛掉.length} | 新出现 ${新出现.length}`);
if (被筛掉.length) LOG(`   被「仅看可商用」筛掉的卡（前 12）: ${JSON.stringify(被筛掉.slice(0, 12))}`);
if (新出现.length) LOG(`   打开后新出现的卡: ${JSON.stringify(新出现.slice(0, 12))}`);

const 关许可 = 请求队列.slice(关请求).map((r) => r.modelLicense);
const 开许可 = 请求队列.slice(开请求).map((r) => r.modelLicense);
LOG(`   关闭态请求的 modelLicense: ${JSON.stringify([...new Set(关许可.map(String))])}`);
LOG(`   打开态请求的 modelLicense: ${JSON.stringify([...new Set(开许可.map(String))])}`);
LOG(`   关闭态总条数: ${请求队列.slice(关请求).reduce((a, b) => a + b.条数, 0)} | 打开态总条数: ${请求队列.slice(开请求).reduce((a, b) => a + b.条数, 0)}`);

out.对照 = { 分类: 混.分类, 关闭卡名数: 关集.length, 打开卡名数: 开集.length, 被筛掉, 新出现, 关闭态modelLicense: [...new Set(关许可.map(String))], 打开态modelLicense: [...new Set(开许可.map(String))] };

await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = 0; });
await page.waitForTimeout(1500);
await shot(page, 'DN-d-仅看可商用打开后.png');
LOG('📸 DN-d');
// 收工前改回关闭
await page.evaluate(() => {
  for (const lb of document.querySelectorAll('label,div,span')) {
    if (/仅看可商用/.test(lb.textContent || '') && lb.children.length <= 2) {
      const inp = lb.querySelector('input[type="checkbox"]');
      if (inp && inp.checked) { inp.click(); return true; }
    }
  }
  return false;
});
await page.waitForTimeout(2000);
const 收尾 = await page.evaluate(() => {
  for (const lb of document.querySelectorAll('label,div,span')) {
    if (/仅看可商用/.test(lb.textContent || '') && lb.children.length <= 2) {
      const inp = lb.querySelector('input[type="checkbox"]');
      if (inp) return inp.checked;
    }
  }
  return null;
});
LOG(`收工时勾选状态: ${收尾}（应为 false）`);
out.收尾勾选 = 收尾;
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDN2.json ===');
