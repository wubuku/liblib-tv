// Batch DR-3：把「仅看可商用」到底筛掉多少张测出来（关态 + 开态成对）。
//
// ⛔ DR-2 为什么读数全 0（一句话）：**它点了已经选中的分类。**
//   DR-1 收工时广场停在「风格插画」，DR-2 进来后又点了一次「风格插画」
//   ⇒ 同一个 tab 再点是 no-op，前端不发任何请求 ⇒ 监听器收到 0 页。
//   阴性读数还差点被当成结论，是靠阳性对照（0 vs 738 ⛔）当场抓住的。
//   ⭐ 教训：**「读到 0」先查自己有没有真的触发状态变化**，再谈结论。
//
// ⭐⭐ 本轮三处结构性修正：
//   ① `page.on('response')` 注册在 `open()` **之前** —— 全新加载的 page=1 必定被捕获。
//   ② 归属靠**数据自证**：`tagIds === 本类`（属分类）且 `modelLicense` 的有无（属状态）。
//      起点只负责「不漏 page=1」：等「看到该状态下的 page=1」，不靠固定 sleep。
//   ③ ⭐ **每个 page 号只取首条**。前端在同一页号上可能重发（重试/跳页），
//      DR-1 的开态就是被这个污染的：逐页求和 738 ≠ uuid 去重 777。
//
// ⭐ 阳性对照（判据必须自证）：关闭态结果必须 **等于 DM 批独立测过的 738**。
//   对不上 ⇒ 本轮数据作废，结论不写进手册。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const 本类 = '520047,520048,520049,520050,520051,520052,520053,510011,510012,510013,510014,510015,510016,510017';
const 真值 = 738; // DM 批独立测得
const out = { 归属键: 本类, 真值, 默认分类: null, 关态: null, 开态: null, 对照: null, 收尾勾选: null };
const SAVE = () => writeFile(new URL('./batchDR3.json', import.meta.url), JSON.stringify(out, null, 2));

const { browser, page } = await launch();

// ---------- ① 监听器：必须在 open() 之前 ----------
const 全部响应 = [];
page.on('response', async (resp) => {
  try {
    if (!/model\/feed\/stream/.test(resp.url())) return;
    let bj = {}; try { bj = JSON.parse(resp.request().postData() || '{}'); } catch { /* 忽略 */ }
    const t = await resp.text(); if (!t) return;
    let j; try { j = JSON.parse(t); } catch { return; }
    const arr = (j?.data?.data) || [];
    if (!arr.length) return;
    全部响应.push({
      page: j?.data?.page, hasMore: j?.data?.hasMore, 条数: arr.length,
      tagIds: Array.isArray(bj.tagIds) ? bj.tagIds.join(',') : '(无)',
      有许可参数: Object.prototype.hasOwnProperty.call(bj, 'modelLicense'),
      modelLicense: bj.modelLicense ?? null,
      uuid: arr.map((r) => r.uuid), 名字: arr.map((r) => r.name),
      到达序: 全部响应.length,
    });
    SAVE();
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

// ⛔ DR-3 第一版读到 0 条响应的原因：**忘了打开素材广场**。
//   素材库是侧栏抽屉，必须两步才开得起来（DR-1/DR-2 都有这两步，本轮漏抄）：
//   ① 点 `[data-sidebar-btn="open-asset"]` 展开侧栏 → ② 点「风格库」页签。
//   漏了这两步时 DOM 里根本没有分类按钮，「没找到分类按钮」就是最早的信号。
//   ⭐ 又一条：**阴性读数先查前置条件是否真的就绪**。
await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(5000);

// ---------- ② 切分类 ----------
// ⭐ 关键：先读出「当前是哪个分类」。若已经是风格插画，就必须换走再换回来，
//    否则点同一个 tab 是 no-op（DR-2 就是栽在这里，⛔ 读到 0 页）。
const 当前分类 = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].filter((x) => {
    const t = (x.innerText || '').replace(/\s+/g, ' ').trim();
    return ['推荐', '平面设计', '创意玩法', '动漫游戏', '小说推文', '风格插画', '文创周边', '摄影写真', '建筑及室内设计', '电商营销'].includes(t);
  });
  const on = b.filter((x) => {
    const c = getComputedStyle(x).backgroundColor;
    return c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent';
  });
  return on.length ? (on[0].innerText || '').trim() : (b[0] ? '全部按钮无高亮' : '没找到分类按钮');
});
out.默认分类 = 当前分类;
LOG(`\n进页面后的当前分类: ${当前分类}`);
const 首次 = 全部响应[0];
LOG(`首次响应: page=${首次?.page} tagIds=${首次?.tagIds} 有许可参数=${首次?.有许可参数} 条数=${首次?.条数}`);
SAVE();

if (当前分类 === '风格插画') {
  LOG('⛔ 当前就在风格插画 —— 换到「平面设计」再换回来（否则是 no-op）');
  await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '平面设计'); if (b) b.click(); });
  await page.waitForTimeout(3000);
}
await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '风格插画'); if (b) b.click(); });
await page.waitForTimeout(2000);

// ---------- ③ 归属 + 去重 ----------
// 归属：tagIds 属分类 ∧ modelLicense 的有无属状态
// ⭐ 去重：每个 page 号只取「最早到达」的一条，治 DR-1 开态的重复页
const 归属 = (要许可) => {
  const seen = new Set(); const out2 = [];
  for (const p of 全部响应) {
    if (p.tagIds !== 本类 || !p.uuid.length || p.有许可参数 !== 要许可) continue;
    if (seen.has(p.page)) continue;
    seen.add(p.page); out2.push(p);
  }
  return out2;
};

const 等首页 = async (标签) => {
  const 要许可 = 标签 === '打开态';
  for (let i = 0; i < 40; i += 1) {
    if (归属(要许可).some((p) => p.page === 1)) { LOG(`  ✅ ${标签} 等到 page=1（第 ${i + 1} 次探测）`); return true; }
    await page.waitForTimeout(500);
  }
  LOG(`  ⛔ ${标签}：15 秒内没等到 page=1（收到的总响应 ${全部响应.length} 条）`);
  LOG(`     收到的 tagIds 分布: ${JSON.stringify([...new Set(全部响应.map((p) => p.tagIds))].slice(0, 5))}`);
  return false;
};

const 收全 = async (标签) => {
  const 要许可 = 标签 === '打开态';
  let 轮 = 0; let 无新 = 0;
  for (let i = 1; i <= 60; i += 1) {
    const 前 = 归属(要许可).length;
    await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = v.scrollHeight; });
    await page.waitForTimeout(2100);
    轮 = i;
    const 我的 = 归属(要许可);
    const 末 = 我的[我的.length - 1];
    const 到底 = await page.evaluate(() => {
      const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600);
      return v ? Math.round(v.scrollTop) >= Math.round(v.scrollHeight) - Math.round(v.clientHeight) - 8 : null;
    });
    if (我的.length === 前) 无新 += 1; else 无新 = 0;
    LOG(`   ${标签} 轮${轮}: ${我的.length} 页 / DOM ${await page.evaluate(() => document.querySelectorAll('[data-id]').length)} / 到底=${到底} / 无新=${无新}`);
    if (到底 && 末?.hasMore === false && 无新 >= 2) break;
    if (无新 >= 5) break;
  }
  const 我的 = 归属(要许可);
  const 页序 = [...new Set(我的.map((p) => p.page))].sort((a, b) => a - b);
  const uu = new Set(我的.flatMap((p) => p.uuid));
  const 末页 = 我的.find((p) => p.page === Math.max(...页序));
  const 求和 = 页序.reduce((acc, p) => acc + (我的.find((x) => x.page === p)?.条数 || 0), 0);
  const 原始条 = 我的.reduce((a, p) => a + p.条数, 0);
  const rec = {
    滚了轮数: 轮, 页数: 页序.length, 页序头尾: [页序[0], 页序[页序.length - 1]],
    末页: 末页?.page, 末页条数: 末页?.条数, 末页hasMore: 末页?.hasMore,
    uuid去重: uu.size, 逐页求和: 求和, 自检一致: 求和 === uu.size,
    名字去重: new Set(我的.flatMap((p) => p.名字 || [])).size,
    每页条数: 页序.map((p) => 我的.find((x) => x.page === p)?.条数),
    uuid: [...uu], 名字全: 我的.flatMap((p) => p.名字 || []),
  };
  LOG(`  ${标签}: ${rec.页数} 页（${JSON.stringify(rec.页序头尾)}）末页 ${rec.末页}(${rec.末页条数}条,hasMore=${rec.末页hasMore})`);
  LOG(`     uuid去重 ${rec.uuid去重} | 逐页求和 ${rec.逐页求和} | ${rec.自检一致 ? '✅自检通过' : '⛔自检不符'}`);
  return rec;
};

LOG('\n=== ① 关闭态 ===');
await 等首页('关闭态');
const 关 = await 收全('关闭态');
out.关态 = 关;
out.对照结果 = { 阳性对照: 关.uuid去重 === 真值, 差: 关.uuid去重 - 真值 };
LOG(`⭐ 阳性对照: ${关.uuid去重} vs DM 批的 ${真值} → ${关.uuid去重 === 真值 ? '✅ 吻合' : '⛔ 差 ' + (关.uuid去重 - 真值)}`);
SAVE();

// ---------- ④ 勾「仅看可商用」 ----------
const 翻勾选 = async () => {
  await page.evaluate(() => {
    for (const lb of document.querySelectorAll('label,div,span')) {
      if (/仅看可商用/.test(lb.textContent || '') && lb.children.length <= 2) {
        const inp = lb.querySelector('input[type="checkbox"]');
        if (inp) { inp.click(); return; }
      }
    }
  });
  await page.waitForTimeout(3500);
  return page.evaluate(() => {
    for (const lb of document.querySelectorAll('label,div,span')) {
      if (/仅看可商用/.test(lb.textContent || '') && lb.children.length <= 2) {
        const inp = lb.querySelector('input[type="checkbox"]');
        if (inp) return inp.checked;
      }
    }
    return null;
  });
};
LOG(`\n=== ② 打开态 ===`);
LOG(`  勾选后重读: ${await 翻勾选()}（应 true）`);
await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = 0; });
await page.waitForTimeout(1500);
await 等首页('打开态');
const 开 = await 收全('打开态');
out.开态 = 开;
SAVE();

const A = new Set(关.uuid); const B = new Set(开.uuid);
const 被筛掉 = [...A].filter((x) => !B.has(x));
const 新出现 = [...B].filter((x) => !A.has(x));
LOG(`\n══════ 对照 ══════`);
LOG(`关闭 ${A.size} | 打开 ${B.size}`);
LOG(`⭐ 被「仅看可商用」筛掉: ${被筛掉.length} 张`);
LOG(`⭐ 打开后新出现: ${新出现.length} 张 ${新出现.length ? '⛔ 不是子集关系' : '✅ 子集关系成立'}`);
LOG(`保留率: ${(B.size / A.size * 100).toFixed(1)}%`);
out.对照 = { 关闭: A.size, 打开: B.size, 被筛掉数: 被筛掉.length, 新出现数: 新出现.length, 保留率: (B.size / A.size * 100).toFixed(1) + '%' };
if (被筛掉.length) {
  const 名 = new Set();
  const 池 = [...归属(false), ...归属(true)];
  for (const p of 池) (p.名字 || []).forEach((n, i) => { if (p.uuid[i] && 被筛掉.includes(p.uuid[i])) 名.add(n); });
  LOG(`\n被筛掉的卡（前 12）: ${JSON.stringify([...名].slice(0, 12))}`);
  out.被筛掉的卡名 = [...名].slice(0, 40);
}
SAVE();

const 收尾 = await 翻勾选();
LOG(`\n收工勾选状态: ${收尾}（应 false）`);
out.收尾勾选 = 收尾;
out.最终节点数 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
out.收到的响应总数 = 全部响应.length;
out.重复页号 = 全部响应.length - 归属(false).length - 归属(true).length;
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDR3.json ===');
