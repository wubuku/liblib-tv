// Batch DE-1：修判据重跑 DE-0 的两个读数。
//
// DE-0 出的两个数都**不能用**，两个都是判据的错：
//
// ① 「顶部条 0 个可交互元素」
//    ⛔ 错在：`广场rect=[0,0,1440,810]` ⇒ 广场顶就在 `y=0`，
//    而我按 `r.y < rr.y + 80` 判「在顶部条」⇒ **833 个元素全被判在下方**。
//    ⇒ 「0 个」是**判据自证的空集**，不是产品事实。
//    治法：⭐ **不预设「顶部条」是几 px** —— 直接**按 y 排序**列出最上面那一批，
//          让人眼能看出工具条在哪、到哪结束。
//    ⭐ 阳性对照已经在 DE-0 里过了（枚举抓到了 2 个「全部」）⇒ 枚举范围本身没问题。
//
// ② 「特效广场 4 个元素含排序类词」
//    ⛔ 全是**误报**：卡片名叫「**子弹时间**」，命中的是「时间」。
//    ⇒ **纯文字包含匹配**会撞上卡名、人名、作品名。
//    治法：⭐ 只在**排除了卡片容器之后**的**控件**里找排序入口，
//          并且**把命中的原文打印出来**（让人能一眼看出是撞车还是真命中）。
//
// 遗留 2（适配模型最多几个）DE-0 读数是有效的：视口内 12 张带左上格的卡里
//   2 张是 ✧ 入口，分别列 **2 个**和 **5 个**模型；10 张徽标卡**全部无面板**
//   （这就是反向对照）。⇒ 已知最大 5，样本太小，本步扩到**滚动后**再采一轮。
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

async function openTab(名字) {
  await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
  await page.waitForTimeout(2000);
  await page.evaluate((n) => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith(n))?.click(), 名字);
  await page.waitForTimeout(3500);
}

// ⭐ 按 y 排序列出最上面一排控件（不预设「顶部条」是几 px）
const topControls = () => page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  const modals = [...document.querySelectorAll('.mantine-Modal-inner')].filter(vis);
  if (!modals.length) return { 有广场: false };
  const root = modals.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
  const all = [];
  for (const e of root.querySelectorAll('*')) {
    if (!vis(e)) continue;
    const tag = e.tagName.toLowerCase();
    if (tag === 'script' || tag === 'style') continue;
    const r = e.getBoundingClientRect();
    let pointer = false;
    try { pointer = getComputedStyle(e).cursor === 'pointer'; } catch { pointer = false; }
    const isCtl = tag === 'button' || tag === 'input' || tag === 'select' || e.getAttribute('role') === 'button' || pointer;
    if (!isCtl) continue;
    // ⭐ 判定「这是不是卡片容器」：面积够大且下面还套着更多元素
    const isCardLike = r.width > 150 && r.height > 150;
    const ds = {}; for (const a of e.attributes) if (a.name.startsWith('data-')) ds[a.name] = a.value;
    all.push({
      tag, 文字: (e.innerText || e.placeholder || '').replace(/\s+/g, ' ').trim().slice(0, 30) || null,
      aria: e.getAttribute('aria-label'), title: e.getAttribute('title'), role: e.getAttribute('role'),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      isCardLike, data: ds, class: (e.className || '').toString().slice(0, 50),
    });
  }
  all.sort((a, b) => a.rect[1] - b.rect[1] || a.rect[0] - b.rect[0]);
  return { 有广场: true, 元素数: all.length, 最上20: all.slice(0, 20), 非卡片控件: all.filter((x) => !x.isCardLike) };
});

const 排序词 = ['排序', '最新', '最热', '热门', '时间', '价格', '热度', '人气', '升序', '降序'];

// =============== A 风格广场 ===============
LOG('══════════ A 风格广场：按 y 排最上面 20 个控件 ══════════');
await openTab('风格库');
out.风格 = await topControls();
LOG(`可交互元素 ${out.风格.元素数} 个，其中非卡片 ${out.风格.非卡片控件.length} 个`);
LOG('\n最上面 20 个（按 y 排序）:');
for (const i of out.风格.最上20) LOG(`  y=${String(i.rect[1]).padStart(4)} <${i.tag}> ${JSON.stringify(i.rect)} 「${i.文字 || ''}」 aria=${i.aria} title=${i.title} ${i.isCardLike ? '(卡片级)' : ''}`);
LOG('\n⭐ 非卡片控件按 y 排序（前 30）:');
const 非卡 = out.风格.非卡片控件.slice().sort((a, b) => a.rect[1] - b.rect[1] || a.rect[0] - b.rect[0]);
for (const i of 非卡.slice(0, 30)) LOG(`  y=${String(i.rect[1]).padStart(4)} <${i.tag}> ${JSON.stringify(i.rect)} 「${i.文字 || ''}」 aria=${i.aria} title=${i.title}`);
const 风格命中 = 非卡.filter((i) => 排序词.some((w) => `${i.文字 || ''}${i.aria || ''}${i.title || ''}`.includes(w)));
LOG(`\n⭐ 非卡片控件里含排序类词: ${风格命中.length} 个`);
for (const i of 风格命中) LOG(`  「${i.文字}」 aria=${i.aria} title=${i.title} @${JSON.stringify(i.rect)}`);

// =============== B 特效广场：同一枚举 ===============
LOG('\n══════════ B 特效广场：同一枚举 ══════════');
await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
await openTab('特效库');
out.特效 = await topControls();
LOG(`可交互元素 ${out.特效.元素数} 个，其中非卡片 ${out.特效.非卡片控件.length} 个`);
const 特非卡 = out.特效.非卡片控件.slice().sort((a, b) => a.rect[1] - b.rect[1] || a.rect[0] - b.rect[0]);
LOG('\n⭐ 非卡片控件按 y 排序（前 30）:');
for (const i of 特非卡.slice(0, 30)) LOG(`  y=${String(i.rect[1]).padStart(4)} <${i.tag}> ${JSON.stringify(i.rect)} 「${i.文字 || ''}」 aria=${i.aria} title=${i.title}`);
const 特效命中 = 特非卡.filter((i) => 排序词.some((w) => `${i.文字 || ''}${i.aria || ''}${i.title || ''}`.includes(w)));
LOG(`\n⭐ 特效广场非卡片控件含排序类词: ${特效命中.length} 个`);
for (const i of 特效命中) LOG(`  「${i.文字}」 aria=${i.aria} title=${i.title} @${JSON.stringify(i.rect)}`);
await shot(page, 'DE-b-特效广场非卡片控件.png', { clip: { x: 0, y: 0, width: 1440, height: 320 } });
LOG('📸 DE-b');

// =============== C 适配模型：滚到底再采一轮，扩大样本 ===============
LOG('\n══════════ C 适配模型：滚动后扩大样本 ══════════');
await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
await openTab('风格库');
out.适配 = [];
for (const 轮 of [0, 1, 2]) {
  if (轮 > 0) {
    await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop += 400; });
    await page.waitForTimeout(2500);
  }
  const list = await page.evaluate(() => {
    const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
    const res = [];
    for (const D of document.querySelectorAll('button[aria-label="详情"]')) {
      let card = null;
      for (let p = D.parentElement, j = 0; p && j < 8; p = p.parentElement, j += 1) { const r = p.getBoundingClientRect(); if (r.width > 150 && r.height > 150) { card = p; break; } }
      if (!card) continue;
      const cr = card.getBoundingClientRect();
      if (cr.y < 0 || cr.y > 700) continue;
      for (const b of card.querySelectorAll('button')) {
        const r = b.getBoundingClientRect();
        if (Math.abs(r.x - (cr.x + 9)) <= 3 && Math.abs(r.y - (cr.y + 9)) <= 3) {
          if (!(b.innerText || '').trim()) res.push([Math.round(r.x + 12), Math.round(r.y + 12)]);
          break;
        }
      }
    }
    return res;
  });
  for (const pt of list) {
    await page.mouse.move(5, 400); await page.waitForTimeout(350);
    await page.mouse.move(pt[0], pt[1]); await page.waitForTimeout(850);
    const r = await page.evaluate(() => {
      const vis = (e) => { if (!e) return false; const q = e.getBoundingClientRect(); const c = getComputedStyle(e); return q.width > 0 && q.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
      const hit = [...document.querySelectorAll('body *')].filter((e) => e.tagName !== 'SCRIPT' && e.tagName !== 'STYLE' && vis(e) && /全部适配模型/.test(e.textContent || '') && e.children.length === 0)[0];
      if (!hit) return { 有面板: false };
      let panel = hit.parentElement;
      for (let k = 0; k < 5; k += 1) { const b = panel.getBoundingClientRect(); if (b.width > 150 && b.height > 60) break; panel = panel.parentElement; }
      const 条 = [...panel.querySelectorAll('*')].filter((e) => e.children.length === 0 && (e.innerText || '').trim() && (e.innerText || '').trim() !== '全部适配模型')
        .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim());
      return { 有面板: true, 模型数: [...new Set(条)].length, 模型: [...new Set(条)] };
    });
    out.适配.push({ 轮, ...r });
    LOG(`  轮${轮} → ${r.有面板 ? `${r.模型数} 个: ${JSON.stringify(r.模型)}` : '⛔ 无面板'}`);
  }
}
const 有面板 = out.适配.filter((x) => x.有面板);
LOG(`\n⭐ 共 ${out.适配.length} 次采样，有面板 ${有面板.length} 次`);
LOG(`⭐ 模型数分布: ${JSON.stringify(有面板.map((x) => x.模型数))}`);
LOG(`⭐ 最多 ${有面板.length ? Math.max(...有面板.map((x) => x.模型数)) : '无'} 个`);
const 全部模型 = [...new Set(有面板.flatMap((x) => x.模型))];
LOG(`⭐ 出现过的模型名: ${JSON.stringify(全部模型)}`);

await writeFile(new URL('./batchDE1.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDE1.json ===');
await browser.close();
