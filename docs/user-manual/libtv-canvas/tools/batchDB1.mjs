// Batch DB-1：重测「新功能：支持真人」标记 —— DB-0 那轮广场**没加载完**，读数作废。
//
// DB-0 的读数：广场容器 1 个（1440×810 对，阳性对照的容器部分通过），
//   ⛔ 但**可见详情按钮只有 1 枚**（CZ 那轮是 30/30），
//   且 `scrollH=2265` 正好是 CZ 记录的第一档（2265 → 4462 → 6659）
//   ⇒ **广场刚打开、第一屏还没铺完**。
// ⇒ 「标记命中 0」和「标记还没加载出来」读数**完全一样** ⇒ 按纪律只能输出「没测到」。
//
// 本步：⭐ 先**轮询等广场加载完**（详情按钮数稳定），再找标记。
// 判据不能只看「数够不够」—— 要看**连续两次采样不再增长**。
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

const visExpr = `const vis=(e)=>{if(!e)return false;const r=e.getBoundingClientRect();const s=getComputedStyle(e);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&+s.opacity>0;};`;

async function openPlaza() {
  await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
  await page.waitForTimeout(2000);
  await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
  await page.waitForTimeout(2500);
}
await openPlaza();

// ---------------- 等广场加载完 ----------------
LOG('══════════ 0：等广场加载完（连续两次采样不再增长）══════════');
out.加载过程 = [];
let prev = -1;
for (let i = 0; i < 12; i += 1) {
  const s = await page.evaluate((vx) => {
    const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
    return {
      详情按钮: [...document.querySelectorAll('button[aria-label="详情"]')].filter(vis).length,
      收藏星: [...document.querySelectorAll('button[aria-label="收藏"],button[aria-label="取消收藏"]')].filter(vis).length,
      scrollH: [...document.querySelectorAll('.mantine-ScrollArea-viewport')].filter(vis).map((e) => e.scrollHeight),
      含真人: [...document.querySelectorAll('body *')].filter((e) => vis(e) && (e.textContent || '').includes('真人')).length,
    };
  });
  out.加载过程.push(s);
  LOG(`  采样${i}: 详情=${s.详情按钮} 收藏=${s.收藏星} scrollH=${JSON.stringify(s.scrollH)} 含真人=${s.含真人}`);
  if (s.详情按钮 === prev && s.详情按钮 > 0) { LOG(`  ⭐ 连续两次相同(${s.详情按钮}) ⇒ 认为加载完成`); break; }
  prev = s.详情按钮;
  await page.waitForTimeout(2000);
}

// ---------------- 找标记 ----------------
LOG('\n══════════ 1：找「新功能：支持真人」标记 ══════════');
out.标记 = await page.evaluate((vx) => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  const hits = [];
  // ⭐ 三个口径一起报，避免「一次筛到 0 就以为没有」
  const 口径 = {
    逐字相等叶子: 0, 含真人可见: 0, 含新功能可见: 0,
  };
  const 含真人 = [...document.querySelectorAll('body *')].filter((e) => vis(e) && (e.textContent || '').includes('真人'));
  const 含新功能 = [...document.querySelectorAll('body *')].filter((e) => vis(e) && (e.textContent || '').includes('新功能'));
  口径.含真人可见 = 含真人.length;
  口径.含新功能可见 = 含新功能.length;

  for (const e of document.querySelectorAll('body *')) {
    const t = (e.textContent || '').replace(/\s+/g, ' ').trim();
    if (t !== '新功能：支持真人') continue;
    const 有子含 = [...e.children].some((c) => (c.textContent || '').includes('支持真人'));
    if (有子含) continue;
    口径.逐字相等叶子 += 1;
    const r = e.getBoundingClientRect();
    const 链 = [];
    for (let p = e, i = 0; p && i < 9; p = p.parentElement, i += 1) {
      const b = p.getBoundingClientRect();
      const c = getComputedStyle(p);
      const ds = {};
      for (const a of p.attributes) if (a.name.startsWith('data-')) ds[a.name] = a.value;
      链.push({ tag: p.tagName.toLowerCase(), 文字: (p.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40), rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)], 可见: vis(p), aria: p.getAttribute('aria-label'), pos: c.position, z: c.zIndex, overflow: c.overflow, data: ds, class: (p.className || '').toString().slice(0, 70) });
    }
    let btn = null;
    for (let p = e; p; p = p.parentElement) { if (p.tagName === 'BUTTON') { btn = p; break; } }
    hits.push({
      自身rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      自身可见: vis(e),
      祖先链: 链,
      最近button祖先: btn ? (() => { const b = btn.getBoundingClientRect(); return { 文字: (btn.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40), aria: btn.getAttribute('aria-label'), rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] }; })() : null,
      兄弟: e.parentElement ? [...e.parentElement.children].filter((c) => c !== e).map((c) => (c.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24)).filter(Boolean) : [],
    });
  }
  return {
    口径, 命中数: hits.length, hits,
    含真人样本: 含真人.slice(0, 10).map((e) => { const r = e.getBoundingClientRect(); return { tag: e.tagName.toLowerCase(), 文字: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }),
    含新功能样本: 含新功能.slice(0, 10).map((e) => { const r = e.getBoundingClientRect(); return { tag: e.tagName.toLowerCase(), 文字: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }),
  };
}, visExpr);
LOG(`三口径: ${JSON.stringify(out.标记.口径)}`);
LOG(`命中数: ${out.标记.命中数}`);
LOG(`含「真人」样本: ${JSON.stringify(out.标记.含真人样本, null, 1)}`);
LOG(`含「新功能」样本: ${JSON.stringify(out.标记.含新功能样本, null, 1)}`);
for (const h of out.标记.hits ?? []) {
  LOG(`\n--- 命中 @${JSON.stringify(h.自身rect)} 可见=${h.自身可见}`);
  LOG(`  最近 button 祖先: ${h.最近button祖先 ? `「${h.最近button祖先.文字}」 aria=${h.最近button祖先.aria} @${JSON.stringify(h.最近button祖先.rect)}` : '⛔ 没有 button 祖先'}`);
  LOG(`  兄弟: ${JSON.stringify(h.兄弟)}`);
  for (const c of h.祖先链) LOG(`    <${c.tag}> ${JSON.stringify(c.rect)} vis=${c.可见} pos=${c.pos} z=${c.z} aria=${c.aria} data=${JSON.stringify(c.data)} 「${c.文字}」`);
}

await writeFile(new URL('./batchDB1.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n已写 tools/batchDB1.json');
await browser.close();
