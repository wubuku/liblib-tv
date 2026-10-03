// Batch DR-2：两件事，判据都基于 DR-1 的教训。
//
// ⭐ ① 把归属判据补全：DR-1 只按 `tagIds` 归属，开态仍被污染 —— 因为
//      **同一分类、同一 tagIds，但 modelLicense 不同**（勾选前后的响应都带同一 tagIds），
//      于是同一个 page 号有两个响应，求和只取了第一个 ⇒ 自检 738≠777。
//    ⇒ 归属必须是**两个条件同时成立**：
//         关闭态 = `tagIds === 本类` **且** `modelLicense` 不存在
//         打开态 = `tagIds === 本类` **且** `modelLicense === ["1"]`
//    ⇒ 「这页属于哪个条件下的哪个状态」由**数据自证**，与时序无关。
//    ⭐ 阳性对照：关闭态必须仍等于 DM 批独立测得的 **738**。
//
// ⭐⭐ ② 实测**素材详情浮层**（卡上那枚 ⤢ 按钮）。
//    DP 批把那几条文案标成「界面上没捕捉到」，DR-2 纯文本查清它们**都有调用点**：
//      `generatedContentCommercialUsable` ⭐ 条件 `privilege.includes("1")`
//      `preferredRecommendedModel` + `otherAdaptedModels` ⭐ 详情浮层里的**两个分区**
//      `currentlyInUse` ⭐ 白底黑字徽标
//    而 DN-4 实测：**640/641 张卡的 `privilege` 都含 `"1"`**
//    ⇒ 这些行**应该就在详情浮层里**，是本手册没读全，不是界面没有。
//
// ⛔ 安全边界：点 `⤢` **只开/关浮层**（DN 那轮已验证：点完浮层连同压暗层一起消失，
//    画布节点数不变）；**点卡片本体才会建节点** —— 本轮绝不点卡片本体。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const 本类 = '520047,520048,520049,520050,520051,520052,520053,510011,510012,510013,510014,510015,510016,510017';
const out = { 归属键: 本类, 关态: null, 开态: null, 对照: null, 详情浮层: null };
const SAVE = () => writeFile(new URL('./batchDR2.json', import.meta.url), JSON.stringify(out, null, 2));

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

// ---------- ① 素材详情浮层（先做，趁浏览器还干净） ----------
await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(5000);

const 基线节点数 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
LOG(`=== ① 素材详情浮层（当前画布节点数 ${基线节点数}）===\n`);

// 找卡上那枚 ⤢ 详情按钮（靠 aria-label，不按坐标）
const 详 = page.locator('button[aria-label="详情"]').first();
if (!(await 详.count())) {
  LOG('⛔ 没找到详情按钮');
} else {
  // 先 hover 让它显形，再点
  const box = await 详.boundingBox();
  if (box) await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.waitForTimeout(900);
  await 详.click();
  await page.waitForTimeout(2200);

  const 浮层 = await page.evaluate(() => {
    const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
    // 详情浮层 = 覆盖在广场之上的那个 modal
    const modals = [...document.querySelectorAll('.mantine-Modal-inner')].filter(vis);
    if (!modals.length) return { 有浮层: false };
    const 大 = modals.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; });
    const 详情 = 大.find((m) => {
      const t = m.innerText || '';
      return /风格详情|特效详情|适配模型|生成内容可商用|首选推荐|当前使用/.test(t);
    }) || 大[0];
    const b = 详情.getBoundingClientRect();
    // 逐行读：叶子节点 + 分区标题
    const 行 = [...详情.querySelectorAll('*')].filter((e) => {
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      if (!t || t.length > 70) return false;
      return e.children.length === 0 || /^(p|div|span|button)$/.test(e.tagName.toLowerCase());
    }).map((e) => {
      const r = e.getBoundingClientRect(); const c = getComputedStyle(e);
      return {
        文字: (e.innerText || '').replace(/\s+/g, ' ').trim(),
        tag: e.tagName.toLowerCase(),
        尺寸: [Math.round(r.width), Math.round(r.height)],
        位置: [Math.round(r.x), Math.round(r.y)],
        可见: vis(e), 颜色: c.color, 字号: c.fontSize,
      };
    });
    return { 有浮层: true, 尺寸: [Math.round(b.width), Math.round(b.height)], 位置: [Math.round(b.x), Math.round(b.y)], 行, 全文: (详情.innerText || '').replace(/\n+/g, ' | ').slice(0, 600) };
  });

  out.详情浮层 = 浮层;
  if (浮层.有浮层) {
    LOG(`浮层尺寸 ${浮层.尺寸.join('×')} @${浮层.位置.join(',')}`);
    LOG(`全文: ${浮层.全文}`);
    LOG(`\n关键分区是否出现：`);
    for (const kw of ['风格详情', '生成内容可商用', '首选推荐模型', '其余适配模型', '当前使用', '全部适配模型', '商用']) {
      const 有 = 浮层.行.some((r) => r.文字.includes(kw));
      LOG(`   ${有 ? '✅' : '⛔'} ${kw}`);
    }
    await shot(page, 'DR-a-素材详情浮层.png');
    LOG('📸 DR-a');
  } else {
    LOG('⛔ 点 ⤢ 后没找到详情浮层');
  }
}

// 关掉浮层（点右上角的缩小 / 按 ESC）
const 关前节点数 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
await page.keyboard.press('Escape');
await page.waitForTimeout(1200);
let 关后节点数 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
if (关后节点数 !== 关前节点数) {
  // ESC 没关掉，按记忆里的办法：点右上角 aria-label="缩小"
  const c = page.locator('button[aria-label="缩小"]').first();
  if (await c.count()) { await c.click(); await page.waitForTimeout(1200); }
  关后节点数 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
}
LOG(`\n⭐ 节点数 ${基线节点数} → 打开浮层 ${关前节点数} → 关掉后 ${关后节点数} ${关后节点数 === 基线节点数 ? '✅ 零残留' : '⛔ 有变化！'}`);
out.节点数 = { 基线: 基线节点数, 打开后: 关前节点数, 关闭后: 关后节点数 };
SAVE();

// ---------- ② 「仅看可商用」计数（归属判据补上 modelLicense） ----------
// 浮层已关，直接复用当前广场页
const 页 = [];
page.on('response', async (resp) => {
  try {
    if (!/model\/feed\/stream/.test(resp.url())) return;
    let bj = {}; try { bj = JSON.parse(resp.request().postData() || '{}'); } catch { /* 忽略 */ }
    const t = await resp.text(); if (!t) return;
    let j; try { j = JSON.parse(t); } catch { return; }
    const arr = (j?.data?.data) || [];
    页.push({
      page: j?.data?.page, hasMore: j?.data?.hasMore, 条数: arr.length,
      tagIds: Array.isArray(bj.tagIds) ? bj.tagIds.join(',') : '(无)',
      有许可参数: Object.prototype.hasOwnProperty.call(bj, 'modelLicense'),
      modelLicense: bj.modelLicense ?? null,
      uuid: arr.map((r) => r.uuid), 名字: arr.map((r) => r.name),
    });
  } catch { /* 忽略 */ }
});

// ⭐⭐ 归属 = tagIds 匹配 **且** modelLicense 的有无符合该状态
const 归属 = (要许可) => 页.filter((p) => p.tagIds === 本类 && p.uuid.length && p.有许可参数 === 要许可);

const 等首页 = async (标签) => {
  for (let i = 0; i < 30; i += 1) {
    if (归属(标签 === '打开态').some((p) => p.page === 1)) return true;
    await page.waitForTimeout(500);
  }
  LOG(`  ⚠️ ${标签}：没等到 page=1`);
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
    if (到底 && 末?.hasMore === false && 无新 >= 2) break;
    if (无新 >= 5) break;
  }
  const 我的 = 归属(要许可);
  const 页序 = [...new Set(我的.map((p) => p.page))].sort((a, b) => a - b);
  const uu = new Set(我的.flatMap((p) => p.uuid));
  const 末页 = 我的.find((p) => p.page === Math.max(...页序));
  const 求和 = 页序.reduce((acc, p) => acc + (我的.find((x) => x.page === p)?.条数 || 0), 0);
  const rec = {
    滚了轮数: 轮, 页数: 页序.length, 页序头尾: [页序[0], 页序[页序.length - 1]],
    末页: 末页?.page, 末页条数: 末页?.条数, 末页hasMore: 末页?.hasMore,
    uuid去重: uu.size, 逐页求和: 求和, 自检一致: 求和 === uu.size,
    名字去重: new Set(我的.flatMap((p) => p.名字 || [])).size,
    uuid: [...uu],
  };
  LOG(`  ${标签}: ${rec.页数} 页（${JSON.stringify(rec.页序头尾)}）末页 ${rec.末页}(${rec.末页条数}条,hasMore=${rec.末页hasMore})`);
  LOG(`     uuid去重 ${rec.uuid去重} | 逐页求和 ${rec.逐页求和} | ${rec.自检一致 ? '✅自检通过' : '⛔自检不符'} | 名字去重 ${rec.名字去重}`);
  return rec;
};

LOG('\n=== ② 「仅看可商用」计数（归属 = tagIds + modelLicense 双判据）===');
await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '风格插画'); if (b) b.click(); });
await page.waitForTimeout(2500);
await 等首页('关闭态');
const 关 = await 收全('关闭态');
out.关态 = 关;
LOG(`⭐ 阳性对照：${关.uuid去重} vs DM 批的 738 → ${关.uuid去重 === 738 ? '✅ 吻合' : '⛔ 差 ' + (关.uuid去重 - 738)}`);
SAVE();

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
LOG(`  点勾选后重读: ${await 翻勾选()}（应 true）`);
await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = 0; });
await page.waitForTimeout(2000);
await 等首页('打开态');
const 开 = await 收全('打开态');
out.开态 = 开; SAVE();

const A = new Set(关.uuid); const B = new Set(开.uuid);
const 被筛掉 = [...A].filter((x) => !B.has(x));
const 新出现 = [...B].filter((x) => !A.has(x));
LOG(`\n══════ 对照 ══════`);
LOG(`关闭 ${A.size} | 打开 ${B.size}`);
LOG(`⭐ 被「仅看可商用」筛掉: ${被筛掉.length} 张`);
LOG(`⭐ 打开后新出现: ${新出现.length} 张 ${新出现.length ? '（不是子集关系）' : '✅ 子集关系成立'}`);
LOG(`保留率: ${(B.size / A.size * 100).toFixed(1)}%`);
out.对照 = { 关闭: A.size, 打开: B.size, 被筛掉数: 被筛掉.length, 新出现数: 新出现.length, 保留率: (B.size / A.size * 100).toFixed(1) + '%' };
if (被筛掉.length) {
  const 名 = new Set();
  for (const p of 归属(false)) (p.名字 || []).forEach((n, i) => { if (p.uuid[i] && 被筛掉.includes(p.uuid[i])) 名.add(n); });
  LOG(`\n被筛掉的卡（前 12）: ${JSON.stringify([...名].slice(0, 12), null, 0)}`);
  out.被筛掉的卡名 = [...名].slice(0, 40);
}
SAVE();

const 收尾 = await 翻勾选();
LOG(`\n收工勾选状态: ${收尾}（应 false）`);
out.收尾勾选 = 收尾;
out.最终节点数 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDR2.json ===');
