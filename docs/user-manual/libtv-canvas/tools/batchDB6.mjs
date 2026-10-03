// Batch DB-6：坐实「全部适配模型」面板 —— 8 次未复现的那个遗留，本轮复现了。
//
// ⭐⭐ DB-5 的图上分明弹出了「全部适配模型 / General image V2 / General image Pro」，
//   而脚本读数是 `tooltip 元素=0` ⇒ **又是判据错了**：这不是 tooltip，
//   是 popover/dropdown。**role="tooltip" 找的是「纯提示」，找不到「可点的浮层」。**
//   ⚠️ 这与旧账「8 次采样未复现」是同一个坑：**面板确实在，采样方法把它滤掉了。**
//
// 本步：读出这个浮层的真实身份（role / class / 祖先链 / 挂在谁身上），
//   并查清「未复现」的历史读数到底错在哪（很可能是当时只等了一个固定时长）。
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
await page.waitForTimeout(3500);

const target = await page.evaluate(() => {
  const D = [...document.querySelectorAll('button[aria-label="详情"]')];
  for (let i = 0; i < D.length; i += 1) {
    let card = null;
    for (let p = D[i].parentElement, j = 0; p && j < 8; p = p.parentElement, j += 1) {
      const r = p.getBoundingClientRect();
      if (r.width > 150 && r.height > 150) { card = p; break; }
    }
    if (!card) continue;
    const cr = card.getBoundingClientRect();
    const b = [...card.querySelectorAll('button')].find((x) => {
      const r = x.getBoundingClientRect();
      return r.x >= cr.x - 2 && r.x <= cr.x + 60 && r.y >= cr.y - 2 && r.y <= cr.y + 60
        && !(x.innerText || '').trim() && x.querySelectorAll('svg').length === 1;
    });
    if (!b) continue;
    const r = b.getBoundingClientRect();
    if (r.y > 700) continue;
    return { 卡序: i, 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
  }
  return null;
});
LOG(`入口: ${JSON.stringify(target)}`);

// ============ 逐时刻采样：面板到底什么时候出现 ============
LOG('\n══════════ 逐时刻采样（找出它出现的时机）══════════');
await page.mouse.move(5, 400);
await page.waitForTimeout(600);
out.时间轴 = [];
const t0 = Date.now();
await page.mouse.move(target.中心[0], target.中心[1]);
for (const wait of [200, 300, 400, 500, 600, 800, 1000]) {
  await page.waitForTimeout(wait - (Date.now() - t0 > 0 ? 0 : 0));
  const s = await page.evaluate(() => {
    const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
    // ⭐ 判据换成「页面上有没有含『全部适配模型』这行字的可见元素」
    const hit = [...document.querySelectorAll('body *')].filter((e) => e.tagName !== 'SCRIPT' && vis(e) && /全部适配模型/.test(e.textContent || '') && e.children.length === 0);
    return { 可见适配面板文字: hit.length, 文字: hit.map((e) => (e.innerText || '').trim()).slice(0, 3) };
  });
  const dt = Date.now() - t0;
  out.时间轴.push({ 累计ms: dt, ...s });
  LOG(`  ${String(dt).padStart(5)}ms: 适配面板文字元素=${s.可见适配面板文字} ${JSON.stringify(s.文字)}`);
  if (s.可见适配面板文字) break;
}

// ============ 面板结构 ============
LOG('\n══════════ 面板结构与身份 ══════════');
out.面板 = await page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  const hit = [...document.querySelectorAll('body *')].filter((e) => e.tagName !== 'SCRIPT' && vis(e) && /全部适配模型/.test(e.textContent || '') && e.children.length === 0)[0];
  if (!hit) return { 找到: false };
  const r = hit.getBoundingClientRect();
  const 链 = [];
  for (let p = hit, i = 0; p && i < 8; p = p.parentElement, i += 1) {
    const b = p.getBoundingClientRect(); const c = getComputedStyle(p);
    const ds = {}; for (const a of p.attributes) if (a.name.startsWith('data-')) ds[a.name] = a.value;
    链.push({ tag: p.tagName.toLowerCase(), 文字: (p.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 50), rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)], pos: c.position, z: c.zIndex, role: p.getAttribute('role'), data: ds, class: (p.className || '').toString().slice(0, 80) });
  }
  // 面板里的条目
  let panel = hit.parentElement;
  for (let i = 0; i < 5; i += 1) {
    const b = panel.getBoundingClientRect();
    if (b.width > 150 && b.height > 60) break;
    panel = panel.parentElement;
  }
  const pr = panel.getBoundingClientRect();
  return {
    找到: true,
    标题rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    面板: { rect: [Math.round(pr.x), Math.round(pr.y), Math.round(pr.width), Math.round(pr.height)], class: (panel.className || '').toString().slice(0, 80) },
    祖先链: 链,
    面板内条目: [...panel.querySelectorAll('*')].filter((e) => e.children.length === 0 && (e.innerText || '').trim() && (e.innerText || '').trim() !== '全部适配模型')
      .map((e) => { const b = e.getBoundingClientRect(); return { 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30), rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)], svg: e.querySelectorAll('svg').length, cls: (e.className || '').toString().slice(0, 40) }; }).slice(0, 12),
    所有role: [...new Set([...document.querySelectorAll('[role]')].filter(vis).map((e) => e.getAttribute('role')))],
  };
});
if (out.面板.找到) {
  LOG(`标题: 「全部适配模型」@${JSON.stringify(out.面板.标题rect)}`);
  LOG(`面板: ${JSON.stringify(out.面板.面板)}`);
  LOG(`页面上可见 role: ${JSON.stringify(out.面板.所有role)}`);
  LOG(`祖先链:`);
  for (const c of out.面板.祖先链) LOG(`    <${c.tag}> ${JSON.stringify(c.rect)} pos=${c.pos} z=${c.z} role=${c.role} 「${c.文字}」 ${c.class}`);
  LOG(`面板内条目:`);
  for (const it of out.面板.面板内条目) LOG(`    「${it.文字}」 ${JSON.stringify(it.rect)} svg=${it.svg}`);
  await shot(page, 'DB-f-全部适配模型面板.png', { clip: { x: Math.max(0, out.面板.面板.rect[0] - 30), y: Math.max(0, out.面板.面板.rect[1] - 30), width: Math.min(500, out.面板.面板.rect[2] + 60), height: Math.min(340, out.面板.面板.rect[3] + 60) } });
  LOG('📸 DB-f');
} else LOG('⛔ 面板没找到');

await writeFile(new URL('./batchDB6.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDB6.json ===');
await browser.close();
