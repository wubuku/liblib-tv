// Batch DV-1：把 DU 的结论从「风格广场」扩到「特效广场」，并做反向核对的抽样。
//
// ⭐ 为什么要做这一轮：DU 批坐实「卡面数字 = `runCount`」时，
//   **样本全部取自风格广场**（`风格库` 页签）。而特效广场的卡面**也带**漏斗数字
//   （DN 批实测 `3500` / `1500`）⇒ **风格侧成立不代表特效侧成立**。
//   ⚠️ 不验就是以偏概全。本轮专门跑特效广场。
//
// ⭐ 同时反向抽验一条：DU 说「另外 62 个字段一个都没命中」——
//   本轮在**另一个页签**上重复这个对照，看结论是否稳定。
//
// ⛔ 安全边界：只读。不点击、不搜索、不收藏、不应用。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 特效: null, 风格复验: null, 字段名差异: null };
const SAVE = () => writeFileSync(new URL('./batchDV1.json', import.meta.url), JSON.stringify(out, null, 2));

const 进 = async () => {
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
  // ⛔ DV-1 第一版漏了这一步 ⇒ 广场**根本没打开**（抓 0 条记录、
  //    「高亮按钮」读出来是顶栏的「开通会员/20/TV Director」）。
  //    切页签用的是 `?.click()`，按钮不存在时**静默失败**，不会报错 ——
  //    ⭐ 阴性读数里最危险的一种：看着像「没有数据」，其实是「没开始」。
  await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
  await page.waitForTimeout(5000);
  // ⭐ 开完必须**自证**：读回当前页签名，别靠假设
  const 开成功 = await page.evaluate(() => {
    const on = [...document.querySelectorAll('button')].filter((x) => { const c = getComputedStyle(x).backgroundColor; return c && c !== 'rgba(0, 0, 0, 0)'; }).map((x) => (x.innerText || '').trim());
    return on.some((t) => t === '风格广场' || t === '特效广场' || t === '我的收藏' || t === '最近使用');
  });
  if (!开成功) LOG('⛔ 广场页签没高亮 ⇒ 素材广场没打开，后续读数全部作废');
  else LOG('✅ 广场已打开（页签高亮自证通过）');
};
// ⛔ DV-1 第一版切页签失败的原因：**广场内的页签叫「特效广场」，不叫「特效库」**。
//   「风格库 / 特效库」是**侧栏抽屉里的入口按钮**（点开广场之后就收起来了），
//   广场内真正的页签是 `风格广场 / 特效广场 / 我的收藏 / 最近使用`。
//   用 `?.click()` 找不到就**静默失败**，然后把风格卡当成特效卡分析 ——
//   ⭐ 最危险的一种错：**数据是真的，只是贴错了标签**。
const 切广场 = async (页签名) => {
  await page.evaluate((名) => {
    const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === 名);
    if (b) b.click();
  }, 页签名);
  await page.waitForTimeout(5000);
  // ⭐ 自证：读回**精确页签名**的高亮状态（不靠「非透明背景」那种宽判据 ——
  //    画布顶栏一堆按钮都有背景色，会把画布顶栏读成广场页签）
  const 态 = await page.evaluate((名) => {
    const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === 名);
    if (!b) return '按钮不存在';
    const c = getComputedStyle(b).backgroundColor;
    return (c && c !== 'rgba(0, 0, 0, 0)') ? '高亮' : '存在但未高亮';
  }, 页签名);
  if (态 !== '高亮') LOG(`⛔ 页签「${页签名}」${态} ⇒ 切页签失败，本轮读数作废`);
  else LOG(`✅ 页签「${页签名}」已高亮`);
  return 态;
};

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

await 进();
await 切广场('特效广场');
LOG(`抓到 ${收.size} 条记录`);
// ⭐ 自证：抽 3 个卡名出来 —— 特效卡的名字和风格卡**长得不一样**，
//    一眼就能看出拿到的是哪一边的数据
LOG(`卡名样本: ${JSON.stringify([...收.values()].slice(0, 3).map((r) => r.name))}`);

const 转 = (s) => { const w = /^(\d+(?:\.\d+)?)w$/.exec(s); if (w) return Math.round(parseFloat(w[1]) * 10000); const n = Number(s); return Number.isFinite(n) ? n : null; };
const 找记录 = (文本) => { let best = null; for (const r of 收.values()) { if (!r.name) continue; if (文本.includes(r.name) || r.name.includes(文本.slice(0, 10))) if (!best || r.name.length > best.name.length) best = r; } return best; };

const 读屏 = () => page.evaluate(() => {
  const 盒 = [];
  for (const e of document.querySelectorAll('div')) {
    const r = e.getBoundingClientRect();
    if (!(r.width >= 150 && r.width <= 340 && r.height >= 180 && r.height <= 460)) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 90) continue;
    if (e.querySelectorAll('button').length < 1) continue;
    if (盒.some((b) => b.文本 === t)) continue;
    盒.push({ 文本: t });
  }
  return 盒;
});

const 分析 = (屏, 标签) => {
  let 对上 = 0, 总 = 0, 定位失败 = 0; const 样本 = [];
  for (const c of 屏) {
    const tok = (c.文本.match(/(?<![\d.])\d+(?:\.\d+)?w?(?![\w])/g) || []).filter((x) => /\d/.test(x));
    if (!tok.length) continue;
    const 末 = tok[tok.length - 1];
    const 卡面 = 转(末);
    if (卡面 == null) continue;
    const r = 找记录(c.文本);
    if (!r) { 定位失败 += 1; continue; }
    总 += 1;
    // 精确相等 或 落在 toFixed(1) 的 ±0.5% 内
    const 精确 = r.runCount === 卡面;
    const 近似 = r.runCount >= 10000 && 卡面 === Math.round((r.runCount / 10000).toFixed(1) * 10000);
    const 符合 = 精确 || 近似;
    if (符合) 对上 += 1;
    样本.push({ 卡面文本: 末, 卡面推算: 卡面, 卡名: r.name, runCount: r.runCount, 精确, 近似, 符合, 其他计数字段: Object.fromEntries(Object.entries(r).filter(([k, v]) => typeof v === 'number' && /Count$|heat|score/.test(k))) });
  }
  LOG(`\n[${标签}] 可分析 ${总} 张（定位失败 ${定位失败}）｜符合 runCount ${对上}`);
  for (const s of 样本) LOG(`   ${s.符合 ? '✅' : '⛔'} 卡面「${s.卡面文本}」(${s.卡面推算}) vs runCount=${s.runCount} ${s.精确 ? '精确' : s.近似 ? '缩写一致' : '都不符'} ｜ ${s.卡名.slice(0, 24)}`);
  return { 标签, 可分析: 总, 符合: 对上, 定位失败, 全部符合: 总 > 0 && 对上 === 总, 样本 };
};

const 特效屏 = await 读屏();
const 特效 = 分析(特效屏, '特效广场');
out.特效 = 特效;

// 特效侧记录里有没有 runCount 这个字段
const 特效首 = [...收.values()][0];
out.特效.字段总数 = 特效首 ? Object.keys(特效首).length : 0;
out.特效.有runCount = 特效首 ? Object.prototype.hasOwnProperty.call(特效首, 'runCount') : null;
LOG(`\n特效记录顶层字段 ${out.特效.字段总数} 个，有 runCount: ${out.特效.有runCount}`);

// ---- 回到风格广场复验（换页签 = 换一批数据）----
收 = new Map();
await 切广场('风格广场');
const 风格屏 = await 读屏();
const 风格 = 分析(风格屏, '风格广场(复验)');
out.风格复验 = 风格;
const 风首 = [...收.values()][0];
out.风格复验.字段总数 = 风首 ? Object.keys(风首).length : 0;

// ⭐ 两个广场的字段名差异
if (风首 && 特效首) {
  const a = new Set(Object.keys(风首)); const b = new Set(Object.keys(特效首));
  out.字段名差异 = { 风格独有: [...a].filter((k) => !b.has(k)), 特效独有: [...b].filter((k) => !a.has(k)), 交集个数: [...a].filter((k) => b.has(k)).length };
  LOG(`\n══════ 字段名差异 ══════`);
  LOG(`  风格独有 ${JSON.stringify(out.字段名差异.风格独有)}`);
  LOG(`  特效独有 ${JSON.stringify(out.字段名差异.特效独有)}`);
  LOG(`  共有 ${out.字段名差异.交集个数} 个`);
}
SAVE();
out.最终节点数 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDV1.json ===');
