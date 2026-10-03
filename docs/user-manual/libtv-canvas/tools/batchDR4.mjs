// Batch DR-4：「打开后新出现 39 张」是稳定行为，还是分页/时序噪音？
//
// ⭐⭐ DR-3 首次把「仅看可商用」的计数测出来了：
//   关闭态 738（19 页，阳性对照 == DM 批的 738 ✅）
//   打开态 681（18 页，自检一致 ✅）⇒ 保留率 92.3%
//   但对账时出现一个**不能直接写进手册的异常**：
//   |关\开| = 96（被筛掉）      |开\关| = 39（"新出现"）  ⇒ ⛔ 不是子集关系
//   交集 642 + 39 = 681 ✅ 算式自洽，说明数据本身没坏。
//
// ⛔ 两种解释，必须分开：
//   (a) 后端在开态下**确实换了召回/排序**（新出现的那 39 张是真实结果）
//   (b) 无限滚动的页不稳定（库里实时在变 / 翻页错位），39 张是噪音
//   只跑一次区分不了。**本轮把开态跑两遍**，看集合是否稳定。
//
// ⭐ 判据（必须自证，不靠时序）：
//   · 归属 = tagIds 匹配 ∧ modelLicense 有无符合状态   （数据自证）
//   · 同一阶段内按 page 号只取首条                     （治重复页）
//   · 阶段切换时清 seen，两次开态互不干扰               （本轮新增）
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const 本类 = '520047,520048,520049,520050,520051,520052,520053,510011,510012,510013,510014,510015,510016,510017';
const out = { 归属键: 本类, 阶段标记: [], 关态: null, 开态1: null, 开态2: null, 对账: null };
const SAVE = () => writeFile(new URL('./batchDR4.json', import.meta.url), JSON.stringify(out, null, 2));

let 阶段 = '进场';
const 全部响应 = [];

const { browser, page } = await launch();

page.on('response', async (resp) => {
  try {
    if (!/model\/feed\/stream/.test(resp.url())) return;
    let bj = {}; try { bj = JSON.parse(resp.request().postData() || '{}'); } catch { /* 忽略 */ }
    const t = await resp.text(); if (!t) return;
    let j; try { j = JSON.parse(t); } catch { return; }
    const arr = (j?.data?.data) || [];
    if (!arr.length) return;
    全部响应.push({
      阶段, page: j?.data?.page, hasMore: j?.data?.hasMore, 条数: arr.length,
      tagIds: Array.isArray(bj.tagIds) ? bj.tagIds.join(',') : '(无)',
      有许可参数: Object.prototype.hasOwnProperty.call(bj, 'modelLicense'),
      uuid: arr.map((r) => r.uuid), 名字: arr.map((r) => r.name),
    });
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

// 切分类：先确认当前不是风格插画（DR-2 踩过 no-op）
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
await page.waitForTimeout(2000);

// 归属：按 阶段 + page 去重
const 归属 = (阶段名, 要许可) => {
  const seen = new Set(); const r = [];
  for (const p of 全部响应) {
    if (p.阶段 !== 阶段名) continue;
    if (p.tagIds !== 本类 || !p.uuid.length || p.有许可参数 !== 要许可) continue;
    if (seen.has(p.page)) continue;
    seen.add(p.page); r.push(p);
  }
  return r;
};

const 等首页 = async (阶段名, 要许可) => {
  for (let i = 0; i < 40; i += 1) {
    if (归属(阶段名, 要许可).some((p) => p.page === 1)) { LOG(`  ✅ ${阶段名} page=1 已到`); return true; }
    await page.waitForTimeout(500);
  }
  LOG(`  ⛔ ${阶段名}：没等到 page=1`); return false;
};

const 收全 = async (阶段名, 要许可) => {
  let 轮 = 0; let 无新 = 0;
  for (let i = 1; i <= 60; i += 1) {
    const 前 = 归属(阶段名, 要许可).length;
    await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = v.scrollHeight; });
    await page.waitForTimeout(2100);
    轮 = i;
    const 我的 = 归属(阶段名, 要许可);
    const 末 = 我的[我的.length - 1];
    const 到底 = await page.evaluate(() => {
      const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600);
      return v ? Math.round(v.scrollTop) >= Math.round(v.scrollHeight) - Math.round(v.clientHeight) - 8 : null;
    });
    if (我的.length === 前) 无新 += 1; else 无新 = 0;
    if (到底 && 末?.hasMore === false && 无新 >= 2) break;
    if (无新 >= 5) break;
  }
  const 我的 = 归属(阶段名, 要许可);
  const 页序 = [...new Set(我的.map((p) => p.page))].sort((a, b) => a - b);
  const uu = new Set(我的.flatMap((p) => p.uuid));
  const 求和 = 页序.reduce((acc, p) => acc + (我的.find((x) => x.page === p)?.条数 || 0), 0);
  LOG(`  ${阶段名}: ${页序.length} 页（${JSON.stringify([页序[0], 页序[页序.length - 1]])}）去重 ${uu.size} | 求和 ${求和} | ${求和 === uu.size ? '✅自检' : '⛔自检不符'}`);
  return { 页数: 页序.length, uuid去重: uu.size, 逐页求和: 求和, 自检一致: 求和 === uu.size, uuid: [...uu], 名字全: 我的.flatMap((p) => p.名字 || []) };
};

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

// ---------- 三轮 ----------
LOG('\n=== ① 关闭态 ===');
阶段 = '关态';
await 等首页('关态', false);
const A = await 收全('关态', false);
out.关态 = { 页数: A.页数, uuid去重: A.uuid去重, 逐页求和: A.逐页求和, 自检一致: A.自检一致, uuid: A.uuid };

LOG('\n=== ② 打开态（第 1 次）===');
LOG(`  勾选: ${await 翻勾选()}（应 true）`);
阶段 = '开态1';
await 等首页('开态1', true);
const B1 = await 收全('开态1', true);
out.开态1 = { 页数: B1.页数, uuid去重: B1.uuid去重, 逐页求和: B1.逐页求和, 自检一致: B1.自检一致, uuid: B1.uuid };
SAVE();

LOG('\n=== ③ 取消勾选，再打开（第 2 次）===');
LOG(`  取消: ${await 翻勾选()}（应 false）`);
await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = 0; });
await page.waitForTimeout(2500);
LOG(`  再次勾选: ${await 翻勾选()}（应 true）`);
阶段 = '开态2';
await 等首页('开态2', true);
const B2 = await 收全('开态2', true);
out.开态2 = { 页数: B2.页数, uuid去重: B2.uuid去重, 逐页求和: B2.逐页求和, 自检一致: B2.自检一致, uuid: B2.uuid };
SAVE();

// ---------- 对账 ----------
const S = (u) => new Set(u);
const a = S(A.uuid); const b1 = S(B1.uuid); const b2 = S(B2.uuid);
const 差 = (x, y) => [...x].filter((v) => !y.has(v));
const 交 = (x, y) => [...x].filter((v) => y.has(v));
const 表 = {
  关态: a.size, 开态1: b1.size, 开态2: b2.size,
  开1减开2: 差(b1, b2).length, 开2减开1: 差(b2, b1).length, 开1交开2: 交(b1, b2).length,
  关减开1: 差(a, b1).length, 开1减关: 差(b1, a).length, 关交开1: 交(a, b1).length,
  关减开2: 差(a, b2).length, 开2减关: 差(b2, a).length, 关交开2: 交(a, b2).length,
};
out.对账 = 表;
LOG('\n══════ 对账 ══════');
for (const [k, v] of Object.entries(表)) LOG(`  ${k}: ${v}`);

const 稳定 = 开1减开2 === 0 && 开2减开1 === 0;
LOG(`\n⭐⭐ 开态集合是否稳定: ${稳定 ? '✅ 两次完全一致 ⇒ 39 张是真实的后端结果' : '⛔ 两次不一致 ⇒ 存在噪音，结论不能用'}`);

// 那 39 张两次都出现吗？
const 仅开 = 差(b1, a);
const 仅开2 = 差(b2, a);
const 共同 = 交(仅开, 仅开2);
LOG(`"只出现在开态"的：第1次 ${仅开.length} 张 / 第2次 ${仅开2.length} 张 / 两次都有 ${共同.length} 张`);
out.只开态 = { 第1次: 仅开.length, 第2次: 仅开2.length, 两次都有: 共同.length, 两次都有uuid: 共同 };

if (共同.length) {
  const 名 = new Set();
  for (const p of 全部响应) (p.名字 || []).forEach((n, i) => { if (p.uuid[i] && 共同.includes(p.uuid[i])) 名.add(n); });
  LOG(`两次都出现的（前 10）: ${JSON.stringify([...名].slice(0, 10))}`);
  out.两次都出现的卡名 = [...名].slice(0, 30);
}
out.阶段计数 = 全部响应.reduce((acc, p) => { const k = `${p.阶段}|许可${p.有许可参数}`; acc[k] = (acc[k] || 0) + 1; return acc; }, {});
out.最终节点数 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
out.收尾勾选 = await 翻勾选();
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDR4.json ===');
