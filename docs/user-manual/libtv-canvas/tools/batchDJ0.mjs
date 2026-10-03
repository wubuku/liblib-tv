// Batch DJ-0：从**网络层**找卡面那个数字的字段名。
//
// DG-1 已经把 DOM 那条路走死了：
//   · 祖先链逐层量到第 6 层：无 `data-*`、无 `aria-label`、无 `title`；
//   · 内嵌 RSC payload 里搜 12 个候选键名，只命中 i18n 文案表的 `viewCount`/`hotCount`，
//     **与卡面数字不同源**；
//   · 关键：那次带数字列表重搜时，**数字列表本身是空的**（判据没抓到卡）。
//
// ⭐ 但**还有一条路完全没走过：接口响应体**。
//   广场的卡片数据必然来自某个 JSON 接口，字段名就在里面。
//   做法：⭐ **先在界面上读出确切数值**，再去响应体里找**同值**，报告它的**键路径**。
//   （不用猜键名 —— 猜键名正是 DG-1 踩的坑。）
//
// ⭐ 两个换算关系要同时试：
//   · 带 `w` 的 `535.7w` ⇒ 原始值可能是 `5357000` 或 `535.7` 或 `5357`（万/千两种口径）；
//   · 不带 `w` 的 `62` ⇒ 原始值就是 `62`。
//
// ⚠️ 只读响应体，不发任何请求、不点任何卡片（点卡会建节点）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
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

// ---------- 1. 先读界面上的确切数值 ----------
await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(4500);

out.界面数值 = await page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  const modals = [...document.querySelectorAll('.mantine-Modal-inner')].filter(vis);
  if (!modals.length) return { 找到: false };
  const root = modals.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
  // ⭐ 用 DI-1 验过的两层：第 3 层 = 整张卡
  const 卡 = [];
  const seen = new Set();
  for (const D of root.querySelectorAll('button[aria-label="详情"]')) {
    let L3 = null;
    for (let p = D.parentElement, j = 0; p && j < 6; p = p.parentElement, j += 1) {
      const r = p.getBoundingClientRect();
      if (r.width > 150 && r.width < 260 && r.height > 260) { L3 = p; break; }
    }
    if (!L3) continue;
    const cr = L3.getBoundingClientRect();
    if (cr.y < 0 || cr.y > 620) continue;
    const k = `${Math.round(cr.x)},${Math.round(cr.y)}`;
    if (seen.has(k)) continue; seen.add(k);
    const 数字 = [...L3.querySelectorAll('*')].filter((e) => e.children.length === 0 && vis(e) && /^\d+(\.\d+)?w?$/.test((e.innerText || '').trim()))
      .map((e) => ({ 文字: (e.innerText || '').trim(), rect: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() }));
    卡.push({ 卡名: (L3.innerText || '').split('\n')[0].slice(0, 20), 数字 });
  }
  return { 找到: true, 卡数: 卡.length, 卡 };
});
LOG(`视口内整卡 ${out.界面数值.卡数} 张`);
const 所有数字 = [];
for (const c of (out.界面数值.卡 || [])) for (const d of c.数字) 所有数字.push(d);
LOG(`读到的数字: ${JSON.stringify(所有数字.map((d) => d.文字))}`);
out.所有数字 = 所有数字;

// ---------- 2. 重新加载广场，抓响应体 ----------
out.响应 = [];
page.on('response', async (resp) => {
  try {
    const ct = (resp.headers()['content-type'] || '');
    if (!/json/i.test(ct)) return;
    const url = resp.url();
    if (/analytics|log|track|beacon|report/i.test(url)) return;
    const body = await resp.text();
    if (!body || body.length < 40) return;
    if (body.length > 4_000_000) return;
    out.响应.push({ url: url.slice(-90), 长度: body.length, body });
  } catch { /* 响应体读不到就算了 */ }
});

LOG('\n⭐ 重新进广场，抓 JSON 响应…');
await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(6000);
// ⭐ 切几个分类，多抓几批
for (const 名 of ['摄影写真', '电商营销']) {
  await page.evaluate((n) => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim() === n)?.click(), 名);
  await page.waitForTimeout(3500);
}

LOG(`抓到 JSON 响应 ${out.响应.length} 个`);
for (const r of out.响应) LOG(`  ${r.长度}字  …${r.url}`);

// ---------- 3. 在响应体里找「同值」 ----------
out.命中 = [];
for (const r of out.响应) {
  let j; try { j = JSON.parse(r.body); } catch { continue; }
  const 目标 = new Set();
  for (const d of 所有数字) {
    const t = d.文字;
    if (t.endsWith('w')) {
      const n = parseFloat(t.slice(0, -1));
      // 试遍所有可能的「万」口径
      目标.add(n); 目标.add(n * 10000); 目标.add(Math.round(n * 10000));
      目标.add(Math.round(n * 1000)); 目标.add(n * 1000);
      目标.add(n * 100); 目标.add(Math.round(n * 100));
      目标.add(n * 10); 目标.add(Math.round(n * 10));
    } else { 目标.add(Number(t)); }
  }
  const walk = (node, path, 深度) => {
    if (深度 > 12 || node === null || typeof node !== 'object') return;
    for (const [k, v] of Object.entries(node)) {
      const p = path ? `${path}.${k}` : k;
      if (typeof v === 'number' && 目标.has(v)) {
        // ⭐ 命中时把**这个对象的其它键**也带出来（字段名的同义词往往就在旁边）
        const 兄弟 = {};
        if (node && typeof node === 'object') for (const [k2, v2] of Object.entries(node)) if (typeof v2 !== 'object') 兄弟[k2] = String(v2).slice(0, 40);
        out.命中.push({ url: r.url.slice(-60), 键路径: p, 值: v, 兄弟 });
      } else if (typeof v === 'object') { walk(v, p, 深度 + 1); }
    }
  };
  walk(j, '', 0);
}
LOG(`\n⭐ 命中（同值出现在哪些键路径）：${out.命中.length} 处`);
const 按键 = {};
for (const h of out.命中) { const k = h.键路径.split('.').slice(-1)[0]; 按键[k] = (按键[k] || 0) + 1; }
LOG(`按末段键名汇总: ${JSON.stringify(按键, null, 1)}`);
for (const h of out.命中.slice(0, 20)) LOG(`  ${h.键路径} = ${h.值}   @…${h.url}`);

// 响应体别整份写出去，只写元数据
const 精简 = { 界面数值: out.界面数值, 所有数字: out.所有数字, 响应列表: out.响应.map((r) => ({ url: r.url, 长度: r.长度 })), 命中: out.命中.slice(0, 60), 按键 };
await writeFile(new URL('./batchDJ0.json', import.meta.url), JSON.stringify(精简, null, 2));
LOG('\n=== 已写 tools/batchDJ0.json ===');
await browser.close();
