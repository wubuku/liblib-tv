// Batch DM-2：诊断 **`推荐` 分类采到 0 页**。
//
// ⛔ 现象：DM-1 里 `推荐` 抓到 **0 个** feed/stream 响应、uuid 去重 0 ——
//    但**同屏 DOM 有 30~54 张卡** ⇒ 卡片确实在。
//    ⇒ 这不是「推荐分类没有内容」，是**我的过滤器把它滤掉了**。
//
// ⭐ 我的判据 ③ 写的是「只累积 tagIds 匹配该分类的页」，而 `推荐` 是**不筛选**的分类，
//    它的请求**很可能不带 tagIds**（DL-0 里 `推荐` 也是 `收到响应 0`）。
//    ⇒ 「推荐无 tagIds」⇒ 我拿 `推荐` 自己的 tagIds 当特征去匹配 ⇒ 自己把自己滤没了。
//
// 但**这只是假设**。本步不去猜，直接把广场打开后发出的**所有**请求捞出来：
//   URL + 方法 + POST body 前 300 字符 + 响应长度 + 响应里像不像卡片列表
// 阳性对照：同时滚 3 轮，确认这些请求**确实随滚动增加**。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 请求: [], 轮: [] };
const SAVE = () => writeFile(new URL('./batchDM2.json', import.meta.url), JSON.stringify(out, null, 2));

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

// ---------- 捞**所有** XHR/fetch（不筛 feed/stream），这才是诊断的关键 ----------
page.on('response', async (resp) => {
  try {
    const rq = resp.request();
    const rt = rq.resourceType();
    if (rt !== 'xhr' && rt !== 'fetch') return;
    const url = resp.url();
    if (!/api2\.liblib\.art|api\.liblib\.tv/.test(url)) return;   // 只看自家 API
    let body = ''; try { body = rq.postData() || ''; } catch { body = ''; }
    const text = await resp.text().catch(() => '');
    out.请求.push({
      时刻: out.请求.length,
      方法: rq.method(),
      url: url.replace(/^https?:\/\//, '').slice(0, 110),
      postBody前300: body.slice(0, 300),
      响应长度: text.length,
      响应前200: text.slice(0, 200),
    });
    SAVE();
  } catch { /* 忽略 */ }
});

await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(6000);

// ⭐ 确认当前停在哪个分类（应当是 `推荐`，因为我们没点任何分类标签）
const 当前 = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '推荐');
  if (!b) return null; const cs = getComputedStyle(b);
  return { 有推荐按钮: true, 高亮: /rgb\(/.test(cs.backgroundColor) ? cs.backgroundColor : null, class含active: /active|selected/i.test(b.className || '') };
});
LOG(`当前停在「推荐」？ ${JSON.stringify(当前)}`);
out.当前分类 = 当前;

const 度量 = () => page.evaluate(() => {
  const modals = [...document.querySelectorAll('.mantine-Modal-inner')].filter((e) => {
    const r = e.getBoundingClientRect(); const c = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && +c.opacity > 0;
  });
  if (!modals.length) return { 有弹层: false };
  const root = modals.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
  const 卡 = new Set();
  for (const D of root.querySelectorAll('button[aria-label="详情"]')) {
    for (let p = D.parentElement, j = 0; p && j < 6; p = p.parentElement, j += 1) {
      const r = p.getBoundingClientRect();
      if (r.width > 150 && r.width < 260 && r.height > 260) { 卡.add(p); break; }
    }
  }
  let vp = [...卡][0] ? [...卡][0].closest('.mantine-ScrollArea-viewport') : null;
  return {
    DOM卡数: 卡.size,
    容器: vp ? { scrollTop: Math.round(vp.scrollTop), scrollHeight: Math.round(vp.scrollHeight) } : null,
    首卡: 卡.size ? ([...卡][0].innerText || '').split('\n')[0].slice(0, 16) : null,
  };
});

LOG(`基线: ${JSON.stringify(await 度量())}`);
for (let i = 1; i <= 4; i += 1) {
  const 前 = out.请求.length;
  await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = v.scrollHeight; });
  await page.waitForTimeout(2600);
  const m = await 度量();
  out.轮.push({ 轮: i, 新请求: out.请求.length - 前, ...m });
  LOG(`轮 ${i}: 新请求 ${out.请求.length - 前} | DOM ${m.DOM卡数} | top ${m.容器?.scrollTop}/${m.容器?.scrollHeight}`);
  SAVE();
}

LOG(`\n══════ 抓到的自家 API 请求（共 ${out.请求.length} 个）══════`);
for (const r of out.请求) {
  const isFeed = /model\/feed\/stream/.test(r.url);
  LOG(`\n[${r.时刻}] ${r.方法} ${r.url}`);
  LOG(`   响应长度 ${r.响应长度}`);
  if (r.postBody前300) LOG(`   POST: ${r.postBody前300}`);
  else LOG(`   POST: (无请求体)`);
  if (isFeed) {
    LOG(`   ⭐ 这是 feed/stream`);
  } else {
    LOG(`   响应前200: ${r.响应前200}`);
  }
}
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDM2.json ===');
