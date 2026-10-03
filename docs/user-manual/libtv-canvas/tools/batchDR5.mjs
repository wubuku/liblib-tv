// Batch DR-5：「仅看可商用」独立复现 —— 专治 DR-3 撞上、DR-4 没验完的那件事。
//
// ⭐⭐ DR-3 已经测出（阳性对照 + 自检双通过，判据可信）：
//   关态 738（19 页） / 开态 681（18 页） / 被筛掉 96 / ⛔但「开态独有 39 张」
//
// ⛔ DR-4 想复现「39 张」，却**自己把数据搞坏了**，两个坑：
//   ① ⭐⭐⭐ **阶段标签有竞态**（本批最重要的教训）
//      DR-4 用一个闭包变量 `阶段` 给每条响应打轮次标签，写在 push 的对象字面量里 ——
//      而 push 发生在 `await resp.text()` **之后**。切分类那一刻的 page=1
//      响应「开始处理」时 `阶段` 还是旧值，「读标签」时已经变了 ⇒ **page=1 被记成上一轮**。
//      结果：关态 698 = 738 − 40，**正好缺首页**（和 DN-4 那次一模一样的坑）。
//      ⇒ **我用「时序」替换掉「数据自证」，把 DR-3 做对的东西又弄坏了。**
//      ⭐ 正解：**任何标签都必须在第一个 `await` 之前同步快照**。
//   ② 第二轮「取消勾选再勾选」前端**没重置分页** ⇒ 开态2 = 0 页。
//      正解：**第二轮用全新的浏览器会话**，不留任何残留状态。
//
// ⭐ 本轮只回答一个问题：**开态的 681 张（含那 39 张独有卡）是否可复现？**
//   两个完全独立的会话，各跑关态 + 开态，比较两次的开态集合。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const 本类 = '520047,520048,520049,520050,520051,520052,520053,510011,510012,510013,510014,510015,510016,510017';
const out = { 归属键: 本类, 会话1: null, 会话2: null, 对账: null };
// ⭐ 同步落盘：DR-4 批 SAVE 用 await writeFile，进程崩溃时数据全丢（0 字节文件）。
//   长跑脚本**任何阶段的证据都要能在崩溃后活下来** ⇒ 同步写。
const { writeFileSync } = await import('node:fs');
const SAVE = () => writeFileSync(new URL('./batchDR5.json', import.meta.url), JSON.stringify(out, null, 2));

// ⭐ 一轮：全新会话 → 开广场 → 切风格插画 → 收关态 → 勾选 → 收开态
const 跑一轮 = async (轮次) => {
  const 全部 = [];
  const { browser, page } = await launch();

  page.on('response', async (resp) => {
    // ⭐⭐⭐ 快照必须在第一个 await 之前取，否则标签会串轮（DR-4 的坑）
    const URL_快照 = resp.url();
    if (!/model\/feed\/stream/.test(URL_快照)) return;
    let bj = {}; try { bj = JSON.parse(resp.request().postData() || '{}'); } catch { /* 忽略 */ }
    const t = await resp.text(); if (!t) return;
    let j; try { j = JSON.parse(t); } catch { return; }
    const arr = (j?.data?.data) || [];
    if (!arr.length) return;
    全部.push({
      page: j?.data?.page, hasMore: j?.data?.hasMore, 条数: arr.length,
      tagIds: Array.isArray(bj.tagIds) ? bj.tagIds.join(',') : '(无)',
      有许可参数: Object.prototype.hasOwnProperty.call(bj, 'modelLicense'),
      uuid: arr.map((r) => r.uuid), 名字: arr.map((r) => r.name),
    });
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
  LOG(`  [${轮次}] 进场分类: ${当前}`);
  if (当前 === '风格插画') {
    await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').trim() === '平面设计'); if (b) b.click(); });
    await page.waitForTimeout(3000);
  }
  await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '风格插画'); if (b) b.click(); });

  // ⭐ 归属纯靠数据：tagIds 属分类 ∧ modelLicense 有无属状态。**不用任何阶段标签。**
  const 归属 = (要许可) => {
    const seen = new Set(); const r = [];
    for (const p of 全部) {
      if (p.tagIds !== 本类 || !p.uuid.length || p.有许可参数 !== 要许可) continue;
      if (seen.has(p.page)) continue;
      seen.add(p.page); r.push(p);
    }
    return r;
  };
  const 等首页 = async (要许可) => {
    for (let i = 0; i < 40; i += 1) {
      if (归属(要许可).some((p) => p.page === 1)) return true;
      await page.waitForTimeout(500);
    }
    return false;
  };
  const 收全 = async (标签, 要许可) => {
    const 有首页 = await 等首页(要许可);
    let 无新 = 0;
    for (let i = 1; i <= 60; i += 1) {
      const 前 = 归属(要许可).length;
      await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = v.scrollHeight; });
      await page.waitForTimeout(2100);
      const 我的 = 归属(要许可);
      const 末 = 我的[我的.length - 1];
      const 到底 = await page.evaluate(() => {
        const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600);
        return v ? Math.round(v.scrollTop) >= Math.round(v.scrollHeight) - Math.round(v.clientHeight) - 8 : null;
      });
      if (我的.length === 前) 无新 += 1; else 无新 = 0;
      if (到底 && 末?.hasMore === false && 无新 >= 2) break;
      if (无新 >= 5) break;
    }
    const 我的 = 归属(要许可);
    const 页序 = [...new Set(我的.map((p) => p.page))].sort((a, b) => a - b);
    const uu = new Set(我的.flatMap((p) => p.uuid));
    const 求和 = 页序.reduce((acc, p) => acc + (我的.find((x) => x.page === p)?.条数 || 0), 0);
    LOG(`  [${轮次}] ${标签}: ${页序.length} 页（${JSON.stringify([页序[0], 页序[页序.length - 1]])}）去重 ${uu.size} | 求和 ${求和} | ${求和 === uu.size ? '✅自检' : '⛔自检不符'} | 有首页=${有首页}`);
    return { 页数: 页序.length, 页序头尾: [页序[0], 页序[页序.length - 1]], 有首页, uuid去重: uu.size, 逐页求和: 求和, 自检一致: 求和 === uu.size, uuid: [...uu], 名字全: 我的.flatMap((p) => p.名字 || []), 响应总数: 全部.length };
  };

  await page.waitForTimeout(2000);
  const 关 = await 收全('关态', false);
  await page.evaluate(() => {
    for (const lb of document.querySelectorAll('label,div,span')) {
      if (/仅看可商用/.test(lb.textContent || '') && lb.children.length <= 2) {
        const inp = lb.querySelector('input[type="checkbox"]');
        if (inp) { inp.click(); return; }
      }
    }
  });
  await page.waitForTimeout(3500);
  const 勾 = await page.evaluate(() => {
    for (const lb of document.querySelectorAll('label,div,span')) {
      if (/仅看可商用/.test(lb.textContent || '') && lb.children.length <= 2) {
        const inp = lb.querySelector('input[type="checkbox"]');
        if (inp) return inp.checked;
      }
    }
    return null;
  });
  LOG(`  [${轮次}] 勾选后重读: ${勾}（应 true）`);
  await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = 0; });
  await page.waitForTimeout(1500);
  const 开 = await 收全('开态', true);
  const 节点 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
  // 收尾：取消勾选，别把筛选状态留给下一轮
  await page.evaluate(() => {
    for (const lb of document.querySelectorAll('label,div,span')) {
      if (/仅看可商用/.test(lb.textContent || '') && lb.children.length <= 2) {
        const inp = lb.querySelector('input[type="checkbox"]');
        if (inp) { inp.click(); return; }
      }
    }
  });
  await page.waitForTimeout(2000);
  await browser.close();
  return { 关, 开, 勾选读数: 勾, 节点数: 节点 };
};

LOG('=== 会话 1 ===');
const r1 = await 跑一轮(1);
out.会话1 = r1; SAVE();
LOG('=== 会话 2 ===');
const r2 = await 跑一轮(2);
out.会话2 = r2; SAVE();

const S = (u) => new Set(u);
const a1 = S(r1.关.uuid); const b1 = S(r1.开.uuid);
const a2 = S(r2.关.uuid); const b2 = S(r2.开.uuid);
// ⛔ DR-5 第一版在这里挂了：交(b1, b2) 传的是数组不是 Set ⇒ y.has is not a function
//    （表已经打出来了才炸，白跑两轮）。⇒ 交集/差集都自己兜底转 Set，别指望调用方传对。
const 转 = (y) => (y instanceof Set ? y : new Set(y));
const 差 = (x, y) => { const Y = 转(y); return [...x].filter((v) => !Y.has(v)); };
const 交 = (x, y) => { const Y = 转(y); return [...x].filter((v) => Y.has(v)); };
const 表 = {
  关1: a1.size, 开1: b1.size, 关2: a2.size, 开2: b2.size,
  关1减关2: 差(a1, a2).length, 关2减关1: 差(a2, a1).length,
  开1减开2: 差(b1, b2).length, 开2减开1: 差(b2, b1).length, 开1交开2: 交(b1, b2).length,
  关1减开1: 差(a1, b1).length, 开1减关1: 差(b1, a1).length, 关1交开1: 交(a1, b1).length,
  关2减开2: 差(a2, b2).length, 开2减关2: 差(b2, a2).length,
};
out.对账 = 表;
LOG('\n══════ 对账 ══════');
for (const [k, v] of Object.entries(表)) LOG(`  ${k}: ${v}`);

const 开态稳定 = 表.开1减开2 === 0 && 表.开2减开1 === 0;
const 关态稳定 = 表.关1减关2 === 0 && 表.关2减关1 === 0;
LOG(`\n⭐⭐ 关态是否稳定: ${关态稳定 ? '✅ 两会话完全一致' : '⛔ 不一致'}`);
LOG(`⭐⭐ 开态是否稳定: ${开态稳定 ? '✅ 两会话完全一致 ⇒ 那批独有卡是真实的后端结果' : '⛔ 不一致 ⇒ 有噪音，结论不能用'}`);

const only1 = 差(b1, a1); const only2 = 差(b2, a2);
const 共有 = 交(only1, only2);
LOG(`"开态独有"：会话1 ${only1.length} 张 / 会话2 ${only2.length} 张 / 两会话共有 ${共有.length} 张`);
out.开态独有 = { 会话1: only1.length, 会话2: only2.length, 共有: 共有.length, 共有uuid: 共有 };
if (共有.length) {
  const 名 = new Set();
  for (const n of r1.开.名字全) if (共有.includes(r1.开.uuid[[...new Set(r1.开.uuid)].indexOf(n)])) 名.add(n);
  out.开态独有卡名样本 = [...共有].slice(0, 20);
}
const cut1 = 差(a1, b1); const cut2 = 差(a2, b2);
out.被筛掉 = { 会话1: cut1.length, 会话2: cut2.length, 共有: 交(cut1, cut2).length };
LOG(`"被筛掉"  ：会话1 ${cut1.length} 张 / 会话2 ${cut2.length} 张 / 两会话共有 ${交(cut1, cut2).length} 张`);
SAVE();
LOG('\n=== 已写 tools/batchDR5.json ===');
