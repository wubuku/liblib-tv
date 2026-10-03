// Batch DL-0：从**接口层**拿分类的真实数量 —— 别再死磕无限滚动了。
//
// DI 的教训：滚动只能给下界，因为 `scrollHeight` 顶到 17016 就不动了。
// ⭐ 但 DJ 抓到了卡片数据的来源：`api2.liblib.art/api/www/model/feed/stream`
//   （单次响应 400KB+）。**翻页元数据里通常有权威总数** —— `total` / `hasMore` / `pageSize`。
//
// 本步两件事：
//   ① ⭐ 解析 feed 响应的**结构**（只打键名与标量，不打数组体），找出：
//      · 顶层/分页字段（有没有 total）
//      · **一条卡记录的全部字段名**（这对手册也很有用：界面上还有哪些字段没显示）
//   ② ⭐⭐ 关键：把**请求 URL 的查询参数**也抓下来 —— 切分类时请求参数会变，
//      ⭐ 那个参数就是**分类标识**，而且**每个分类可以单独发一次请求**，
//      用返回的 total 就是那个分类的权威数量。
//      ⚠️ 只读：我不自己发请求（那要构造 URL、可能触发写/限流），
//         而是**切分类触发页面自己发**，然后读它的响应。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 分类: [], 字段: [], 错误: [] };

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

// ---------- 挂响应收集器 ----------
const 收集 = [];
page.on('response', async (resp) => {
  try {
    const url = resp.url();
    if (!/model\/feed\/stream/.test(url)) return;
    const body = await resp.text();
    if (!body || body.length < 100) return;
    收集.push({ url, 长度: body.length, body, 时间: Date.now() });
  } catch { /* 读不到就算了 */ }
});

await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(5000);

// ---------- 逐个分类切，抓每次的响应 ----------
const 分类 = ['推荐', '摄影写真', '电商营销', '动漫游戏', '风格插画', '平面设计', '建筑及室内设计', '创意玩法', '文创周边', '小说推文'];
for (const 名 of 分类) {
  const 起点 = 收集.length;
  const ok = await page.evaluate((n) => {
    const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === n);
    if (!b) return false; b.click(); return true;
  }, 名);
  if (!ok) { LOG(`⛔ 找不到「${名}」`); continue; }
  await page.waitForTimeout(4000);
  const 新 = 收集.slice(起点);
  const rec = { 分类: 名, 收到响应: 新.length };
  if (新.length) {
    const r = 新[新.length - 1];
    rec.请求URL = r.url;
    rec.响应长度 = r.长度;
    let j; try { j = JSON.parse(r.body); } catch (e) { rec.解析失败 = String(e).slice(0, 60); }
    if (j) {
      // ⭐ 找分页/总数类字段（递归但只看键名与标量，限深）
      const 找 = (node, path, 深) => {
        if (深 > 6 || node === null || typeof node !== 'object') return;
        for (const [k, v] of Object.entries(node)) {
          const p = path ? `${path}.${k}` : k;
          if (typeof v !== 'object') {
            if (/^(total|count|totalCount|totalNum|size|hasMore|noMore|page|pageSize|pageNum|cursor|lastId|isEnd|finished)$/i.test(k)) {
              (rec.分页 ||= []).push({ 键路径: p, 值: String(v).slice(0, 40) });
            }
          } else if (Array.isArray(v)) {
            (rec.数组 ||= []).push({ 键路径: p, 长度: v.length });
            if (v.length && typeof v[0] === 'object' && !rec.首条字段) rec.首条字段 = Object.keys(v[0]);
          } else 找(v, p, 深 + 1);
        }
      };
      找(j, '', 0);
    }
  }
  out.分类.push(rec);
  LOG(`\n【${名}】响应 ${rec.收到响应} 个`);
  if (rec.请求URL) LOG(`  URL: ${rec.请求URL.slice(0, 200)}`);
  if (rec.分页) for (const p of rec.分页) LOG(`  ⭐ ${p.键路径} = ${p.值}`);
  if (rec.数组) for (const a of rec.数组) LOG(`  数组 ${a.键路径} 长度 ${a.长度}`);
  await writeFile(new URL('./batchDL0.json', import.meta.url), JSON.stringify({ 分类: out.分类, 字段: out.字段 }, null, 2));
}

// ---------- 一条卡记录的全部字段 ----------
LOG('\n══════════ 一条卡记录的全部字段 ══════════');
if (收集.length) {
  let j; try { j = JSON.parse(收集[收集.length - 1].body); } catch { j = null; }
  if (j) {
    const walk = (node, path, 深, acc) => {
      if (深 > 6 || node === null || typeof node !== 'object') return;
      if (Array.isArray(node)) { if (node.length && typeof node[0] === 'object') walk(node[0], `${path}[0]`, 深 + 1, acc); return; }
      for (const [k, v] of Object.entries(node)) {
        const p = path ? `${path}.${k}` : k;
        if (typeof v === 'object' && v !== null) { if (深 < 4) walk(v, p, 深 + 1, acc); }
        else acc.push({ 键路径: p, 类型: typeof v, 样例: String(v).slice(0, 36) });
      }
    };
    const acc = []; walk(j, '', 0, acc);
    out.字段 = acc;
    LOG(`共 ${acc.length} 个叶子字段；打前 60 个：`);
    for (const f of acc.slice(0, 60)) LOG(`   ${f.键路径}  (${f.类型})  ${f.样例}`);
  }
}

await writeFile(new URL('./batchDL0.json', import.meta.url), JSON.stringify({ 分类: out.分类, 字段: out.字段.slice(0, 400) }, null, 2));
LOG('\n=== 已写 tools/batchDL0.json ===');
await browser.close();
