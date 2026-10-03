// Batch DE-0：两个遗留，都不需要授权。
//
// 遗留 1：广场真正的排序入口（按时间 / 热度 / 价格）。
//   已知：`全部 ▾` 是**按模型筛**（已结案）。所以排序入口还没找到。
//   ⭐ 旧账说「本轮把广场面板工具条**整个枚举**过一遍，没找到」——
//     但那是**阴性结论**，得先验「枚举范围」到底有多大。
//   本步：① 完整列出**广场内所有可交互元素**（不预设位置），
//     逐个报 tag / 文字 / aria / title / data-* / 尺寸；
//     ② ⭐ 对照：**同一个枚举脚本在特效广场跑一遍** ——
//        如果风格广场「没有」而特效广场「有」，那就有得说；
//        两边都没有 ⇒ 才成立「界面上没有」。
//
// 遗留 2：「全部适配模型」浮层最多能列几个模型？
//   已知样本：风格 2 个、风格 5 个、特效 3 个。
//   本步：对**每一张带 ✧ 入口的可见卡**都悬停读一次，报分布。
//   ⚠️ 悬停要逐张移动鼠标并等 ≥257ms（DB-6 实测），不能并发。
//
// ⚠️ 方法纪律：
//   · 数东西用 DOM 总数；
//   · 阴性结论必须配**阳性对照**（这里用「特效广场同样枚举」+「已知存在的 `全部 ▾` 能不能被枚举到」）；
//   · 搜文字排除 SCRIPT/STYLE。
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

// ---------- 广场内**所有**可交互元素（不预设位置）----------
const enumerate = () => page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  // 广场容器 = 可见的 .mantine-Modal-inner 里最大的那个
  const modals = [...document.querySelectorAll('.mantine-Modal-inner')].filter(vis);
  if (!modals.length) return { 有广场: false };
  const root = modals.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
  const rr = root.getBoundingClientRect();
  const items = [];
  for (const e of root.querySelectorAll('*')) {
    if (!vis(e)) continue;
    const r = e.getBoundingClientRect();
    // 只看可交互的：button / [role] / 有 cursor:pointer / input / select
    const tag = e.tagName.toLowerCase();
    const isBtn = tag === 'button' || tag === 'input' || tag === 'select' || e.getAttribute('role') === 'button';
    let pointer = false;
    try { pointer = getComputedStyle(e).cursor === 'pointer'; } catch { pointer = false; }
    if (!isBtn && !pointer) continue;
    const ds = {}; for (const a of e.attributes) if (a.name.startsWith('data-')) ds[a.name] = a.value;
    items.push({
      tag,
      文字: (e.innerText || e.placeholder || '').replace(/\s+/g, ' ').trim().slice(0, 24) || null,
      aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
      role: e.getAttribute('role'),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      在顶部条: r.y < rr.y + 80,
      data: ds,
      class: (e.className || '').toString().slice(0, 50),
    });
  }
  return { 有广场: true, 广场rect: [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)], 元素数: items.length, items };
});

// =============== A 风格广场：穷举 + 适配模型采样 ===============
LOG('══════════ A 风格广场 ══════════');
await openTab('风格库');
out.风格枚举 = await enumerate();
LOG(`广场rect=${JSON.stringify(out.风格枚举.广场rect)} 可交互元素 ${out.风格枚举.元素数} 个`);
const 顶部 = out.风格枚举.items.filter((i) => i.在顶部条);
LOG(`\n⭐ 顶部条（y < 广场顶 +80）上的可交互元素 ${顶部.length} 个：`);
for (const i of 顶部) LOG(`  <${i.tag}> ${JSON.stringify(i.rect)} 「${i.文字 || ''}」 aria=${i.aria} title=${i.title} data=${JSON.stringify(i.data)} ${i.class}`);

const 排序词 = ['排序', '最新', '最热', '热门', '时间', '价格', '热度', '人气', '升序', '降序'];
const 命中 = out.风格枚举.items.filter((i) => {
  const blob = `${i.文字 || ''} ${i.aria || ''} ${i.title || ''}`;
  return 排序词.some((w) => blob.includes(w));
});
LOG(`\n⭐ 含排序类词的元素: ${命中.length} 个`);
for (const i of 命中) LOG(`  「${i.文字}」 aria=${i.aria} title=${i.title} @${JSON.stringify(i.rect)}`);

// ⭐ 阳性对照：`全部 ▾` 是**已知存在**的筛选项，必须能被这个枚举抓到
const 阳性 = out.风格枚举.items.filter((i) => (i.文字 || '').includes('全部'));
LOG(`\n⭐ 阳性对照：枚举里能抓到「全部」吗 → ${阳性.length} 个 ${JSON.stringify(阳性.map((i) => i.文字))}`);

// ---------- 适配模型：逐张悬停读模型数 ----------
LOG('\n══════════ 逐张悬停，读「全部适配模型」列几个模型 ══════════');
const 入口列表 = await page.evaluate(() => {
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
        res.push({ 有文字: !!(b.innerText || '').trim(), 文字: (b.innerText || '').trim() || null, 中心: [Math.round(r.x + 12), Math.round(r.y + 12)] });
        break;
      }
    }
  }
  return res;
});
LOG(`视口内带左上格的卡 ${入口列表.length} 张，其中无文字（✧ 入口）${入口列表.filter((x) => !x.有文字).length} 张`);

out.适配 = [];
for (const [i, it] of 入口列表.entries()) {
  await page.mouse.move(5, 400); await page.waitForTimeout(400);
  await page.mouse.move(it.中心[0], it.中心[1]);
  await page.waitForTimeout(900);
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
  out.适配.push({ 序: i, 徽标: it.文字, ...r });
  LOG(`  卡${i} ${it.文字 ? `徽标「${it.文字}」` : '✧入口'} → ${r.有面板 ? `${r.模型数} 个: ${JSON.stringify(r.模型)}` : '⛔ 无面板'}`);
}
const 面板样本 = out.适配.filter((x) => x.有面板);
LOG(`\n⭐ 有面板的 ${面板样本.length} 张，模型数分布: ${JSON.stringify(面板样本.map((x) => x.模型数))}`);
LOG(`⭐ 最多: ${面板样本.length ? Math.max(...面板样本.map((x) => x.模型数)) : '无样本'} 个`);

// =============== B 特效广场：同一枚举（阴性结论的阳性对照）===============
LOG('\n══════════ B 特效广场（同一枚举）══════════');
await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
await openTab('特效库');
out.特效枚举 = await enumerate();
LOG(`广场rect=${JSON.stringify(out.特效枚举.广场rect)} 可交互元素 ${out.特效枚举.元素数} 个`);
const 特效命中 = out.特效枚举.items.filter((i) => {
  const blob = `${i.文字 || ''} ${i.aria || ''} ${i.title || ''}`;
  return 排序词.some((w) => blob.includes(w));
});
LOG(`⭐ 特效广场含排序类词: ${特效命中.length} 个`);
for (const i of 特效命中) LOG(`  「${i.文字}」 aria=${i.aria} title=${i.title} @${JSON.stringify(i.rect)}`);
const 特效阳性 = out.特效枚举.items.filter((i) => (i.文字 || '').includes('全部'));
LOG(`⭐ 阳性对照：特效广场枚举里抓到「全部」→ ${特效阳性.length} 个 ${JSON.stringify(特效阳性.map((i) => i.文字))}`);

await shot(page, 'DE-a-特效广场面板工具条.png', { clip: { x: 0, y: 0, width: 1440, height: 300 } });
LOG('📸 DE-a');

await writeFile(new URL('./batchDE0.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDE0.json ===');
await browser.close();
