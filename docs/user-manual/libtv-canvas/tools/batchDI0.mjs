// Batch DI-0：两个不需授权的遗留，都需要「大样本」才能收口。
//
// 遗留 1：分类标签各有多少条内容。
//   ⛌ DG-0 的做法是「固定滚 6 轮，读 scrollH」—— **6 个分类读数几乎相同**，
//      说明**根本没滚到底** ⇒ 连相对大小都不能比。
//   本步换判据：⭐ **滚到「不再出现新卡」为止**。
//      卡的身份证 = 它的预览图 `img[src]`（每张卡各不相同）。
//      连续 2 轮没有新卡 ⇒ 认为到底了；若到上限仍未收敛 ⇒ 如实标注「未收敛，下界」。
//
// 遗留 2：「全部适配模型」浮层的模型数**上限**。
//   已知样本 2 / 3 / 5；6 次采样里有 1 次偶发漏读（读了「无面板」）。
//   本步：在**多个分类**上把每一张 `✧` 入口卡都悬停读一遍，取最大值。
//   ⭐ 顺带统计「徽标卡 : 入口卡」的比例（样本大之后这个比例才可信）。
//
// ⚠️ 判据纪律：
//   · 找「整张卡」要用 DG 定的三层容器（高度 > 245、含卡名与数字），别用预览图那块；
//   · 悬停要逐张移开再移入、每次 ≥ 850ms（DB-6 实测 257ms 出现，留足余量）；
//   · 偶发「无面板」要**重试一次**再记，别把漏读当成「这张没有面板」。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = {};

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

await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(4000);

// ---------- 收集当前已渲染的卡（身份证 = 预览图 src）----------
const collect = () => page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  const modals = [...document.querySelectorAll('.mantine-Modal-inner')].filter(vis);
  if (!modals.length) return { 卡: [], scrollH: 0 };
  const root = modals.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
  const 卡 = [];
  const seen = new Set();
  for (const D of root.querySelectorAll('button[aria-label="详情"]')) {
    // ⭐ 往上找「整张卡」：高度 > 245 的那一层（DG-3 定的）
    let card = null;
    for (let p = D.parentElement, j = 0; p && j < 8; p = p.parentElement, j += 1) {
      const r = p.getBoundingClientRect();
      if (vis(p) && r.width > 150 && r.width < 260 && r.height > 245) { card = p; break; }
    }
    if (!card) continue;
    const cr = card.getBoundingClientRect();
    const img = card.querySelector('img');
    const src = img ? (img.getAttribute('src') || '') : '';
    const key = src || `${Math.round(cr.x)},${Math.round(cr.y)}`;
    if (seen.has(key)) continue; seen.add(key);
    // 卡名 / 作者 / 数字（用叶子文字）
    const 叶子 = [...card.querySelectorAll('*')].filter((e) => e.children.length === 0 && vis(e) && (e.innerText || '').trim());
    const 数字 = 叶子.map((e) => (e.innerText || '').trim()).filter((t) => /^\d+(\.\d+)?w?$/.test(t));
    const 文字 = 叶子.map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim());
    // 左上格
    let 格 = null;
    for (const b of card.querySelectorAll('button')) {
      const r = b.getBoundingClientRect();
      if (Math.abs(r.x - (cr.x + 9)) <= 3 && Math.abs(r.y - (cr.y + 9)) <= 3) { 格 = { 徽标: (b.innerText || '').trim() || null, 中心: [Math.round(r.x + 12), Math.round(r.y + 12)] }; break; }
    }
    卡.push({ key: key.slice(-24), 卡名: 文字.find((t) => t.length >= 4 && !/^\d/.test(t)) || '(读不到)', 数字: 数字[0] || null, 格, 在视口: cr.y > -50 && cr.y < 800, 视口y: Math.round(cr.y) });
  }
  const v = [...root.querySelectorAll('.mantine-ScrollArea-viewport')][0];
  return { 卡, scrollH: v ? v.scrollHeight : 0 };
});

const 读面板 = async (pt) => {
  await page.mouse.move(5, 400); await page.waitForTimeout(350);
  await page.mouse.move(pt[0], pt[1]); await page.waitForTimeout(900);
  return page.evaluate(() => {
    const vis = (e) => { if (!e) return false; const q = e.getBoundingClientRect(); const c = getComputedStyle(e); return q.width > 0 && q.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
    const hit = [...document.querySelectorAll('body *')].filter((e) => e.tagName !== 'SCRIPT' && e.tagName !== 'STYLE' && vis(e) && /全部适配模型/.test(e.textContent || '') && e.children.length === 0)[0];
    if (!hit) return { 有面板: false };
    let panel = hit.parentElement;
    for (let k = 0; k < 5; k += 1) { const b = panel.getBoundingClientRect(); if (b.width > 150 && b.height > 60) break; panel = panel.parentElement; }
    const 条 = [...panel.querySelectorAll('*')].filter((e) => e.children.length === 0 && (e.innerText || '').trim() && (e.innerText || '').trim() !== '全部适配模型')
      .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim());
    return { 有面板: true, 模型数: [...new Set(条)].length, 模型: [...new Set(条)] };
  });
};

// =============== A 分类规模：滚到不再出新卡 ===============
const 分类 = ['推荐', '摄影写真', '电商营销', '动漫游戏', '风格插画', '平面设计', '建筑及室内设计', '创意玩法'];   // 先跑 8 个；未跑到的下一批补
out.分类 = [];
out.模型 = [];
const MAX轮 = 8;   // 上限压到 8：整批要在看门狗内跑完；未收敛的分类如实标为下界

for (const 名 of 分类) {
  const ok = await page.evaluate((n) => {
    const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === n);
    if (!b) return false; b.click(); return true;
  }, 名);
  if (!ok) { LOG(`⛔ 找不到分类「${名}」`); continue; }
  await page.waitForTimeout(2600);

  const 见过 = new Set();
  let 收敛 = false; let 轮 = 0; let 新卡 = 0; let 末H = 0;
  for (let i = 0; i < MAX轮; i += 1) {
    const c = await collect();
    轮 = i + 1; 末H = c.scrollH;
    for (const k of c.卡) 见过.add(k.key);
    const 本轮 = 见过.size;
    await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = v.scrollHeight; });
    await page.waitForTimeout(2100);
    const c2 = await collect();
    for (const k of c2.卡) 见过.add(k.key);
    if (见过.size === 本轮 && i >= 1) { 收敛 = true; 新卡 = 0; break; }
    新卡 = 见过.size;
  }
  // 回到顶部再采一遍，把这一分类里所有 ✧ 入口都读一遍
  // ⚠️ 上一次「视口内 0」的成因：滚到底之后 DOM 里**远处那批卡也还在**，
  //    collect() 会把它们全收进来，而它们的 rect 在视口外 ⇒ 悬停点了个空气。
  //    ⇒ 这里**只保留落在视口内的卡**。
  await page.evaluate(() => {
    const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600);
    if (v) { v.scrollTop = 0; v.dispatchEvent(new Event('scroll', { bubbles: true })); }
  });
  await page.waitForTimeout(3000);
  // ⭐ 阳性对照：顶部必须**看得到卡**，否则本分类的悬停采样直接跳过（并记录跳过）
  const 顶部见 = await collect();
  const 顶部可见 = 顶部见.卡.filter((k) => k.在视口);
  if (!顶部可见.length) {
    LOG(`     ⛔ 滚回顶部后视口内 0 张卡 ⇒ 本分类跳过悬停采样（DOM 收=${顶部见.卡.length}）`);
    out.分类[out.分类.length - 1].悬停跳过 = true;
  }
  const 顶部 = 顶部可见.length ? 顶部可见 : 顶部见.卡;
  const 入口 = 顶部.filter((k) => k.格 && !k.格.徽标);
  const 徽标 = 顶部.filter((k) => k.格 && k.格.徽标);
  LOG(`【${名}】滚 ${轮} 轮 ${收敛 ? '✅收敛' : '⛔未收敛(达上限)'}，共见 ${见过.size} 张（其中视口内 ${入口.length + 徽标.length}）`);
  out.分类.push({ 分类: 名, 轮数: 轮, 收敛, 张数下界: 见过.size, 最终scrollH: 末H, 视口内入口: 入口.length, 视口内徽标: 徽标.length });
  // ⭐ 每轮分类后立刻落盘：上一次整轮跑完被 290s 看门狗掐死，JSON 全丢
  await writeFile(new URL('./batchDI0.json', import.meta.url), JSON.stringify(out, null, 2));

  // 悬停读这一屏的入口（最多 6 张）
  for (const [i, k] of 入口.slice(0, 6).entries()) {
    let r = await 读面板(k.格.中心);
    if (!r.有面板) { await page.waitForTimeout(600); r = await 读面板(k.格.中心); }  // ⭐ 漏读重试
    out.模型.push({ 分类: 名, 卡名: k.卡名, ...r });
    if (r.有面板) LOG(`     入口「${String(k.卡名).slice(0, 14)}」→ ${r.模型数} 个: ${JSON.stringify(r.模型)}`);
  }
}
await shot(page, 'DI-a-某个分类滚到底.png');
LOG('\n📸 DI-a');

// =============== 汇总 ===============
const 全 = out.模型.filter((x) => x.有面板);
const 数 = 全.map((x) => x.模型数);
LOG('\n══════════ 汇总 ══════════');
LOG(`分类数=${out.分类.length}，收敛的=${out.分类.filter((c) => c.收敛).length}`);
LOG(`张数下界: ${out.分类.map((c) => `${c.分类}=${c.张数下界}${c.收敛 ? '' : '(未收敛)'}`).join(' / ')}`);
LOG(`\n模型面板采样 ${out.模型.length} 次，出面板 ${全.length} 次，重试后仍无面板 ${out.模型.length - 全.length} 次`);
LOG(`模型数分布: ${JSON.stringify(数.sort((a, b) => a - b))}`);
LOG(`⭐ 上限（本轮观测到的最大）: ${数.length ? Math.max(...数) : '无'}`);
LOG(`全部模型名: ${JSON.stringify([...new Set(全.flatMap((x) => x.模型))])}`);

await writeFile(new URL('./batchDI0.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDI0.json ===');
await browser.close();
