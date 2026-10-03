// Batch CU-1：把「hover 读气泡」推到另外四个面。
//
// CU-0 覆盖的是**默认画布视口内的 46 个可交互元素**，
// 结论是 **L4「无文字 + 无 aria-label + 无 title」= 0 个**，
// 而 15 个「无文字但有 aria」的控件**hover 气泡 15/15 全读出真名**。
//
// ⭐ 但那只说明**默认画布**。手册里「无文字无 aria」的记法大多在别的面上：
//   ① 节点卡片（选中展开后的参数条 + 卡片自身按钮）
//   ② 资产库广场的卡片
//   ③ 风格详情浮层（右上角那枚 `⤡` 一直记着「读到图标，按钮无文字」）
//   ④ 节点大编辑器内部
//
// 本步四个面逐个扫，每个可交互元素同时报 `aria-label` / `[title]` / hover 气泡，
// ⭐ 重点是**比对三者的差异** —— 差异处往往就是手册记错的地方。
//
// ⛔ **一个都不点。** 只 hover。
// ⚠️ 关抽屉用 `button[aria-label="关闭"]`，**不要点画布空白**（CT-2 的教训：
//    点空白可能落在压暗遮罩上，把整个浮层关掉）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const IMG = 'i-9nlG6HdjK2';
const LOG = console.log;

const boot = async (page) => {
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
  const p = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
    if (!b) return null; const r = b.getBoundingClientRect();
    return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
  });
  if (p) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1200); }
};

// 枚举某个「根」下的可交互元素。rootSel 为空则全页。
const listIn = (page, rootSel) => page.evaluate((sel) => {
  const root = sel ? document.querySelector(sel) : document.body;
  if (!root) return [];
  const out = [];
  for (const e of root.querySelectorAll('button,[role="button"],[role="tab"],[role="menuitem"]')) {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) continue;
    const r = e.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    if (r.x + r.width < 0 || r.x > 1440 || r.y + r.height < 0 || r.y > 810) continue;
    out.push({
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 26),
      aria: e.getAttribute('aria-label'),
      title: e.getAttribute('title'),
      data: Object.fromEntries([...e.attributes].filter((a) => a.name.startsWith('data-')).map((a) => [a.name, a.value])),
      svgPaths: [...e.querySelectorAll('svg path')].map((p) => (p.getAttribute('d') || '').slice(0, 40)),
      hasImg: !!e.querySelector('img'),
      cls: (e.className || '').toString().slice(0, 60),
    });
  }
  return out;
}, rootSel);

const readTips = (page) => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  return [...new Set([...document.querySelectorAll('[role="tooltip"],.mantine-Tooltip-tooltip')].filter(vis)
    .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter(Boolean))];
});

// ⭐ 逐个 hover，报告 aria / title / 气泡 三者的差异
const sweep = async (page, 面, rootSel) => {
  const items = await listIn(page, rootSel);
  LOG(`\n########## ${面}：${items.length} 个可交互元素 ##########`);
  const rows = [];
  for (const it of items) {
    if (it.text) { rows.push({ ...it, 气泡: [], 跳过: '有文字' }); continue; }
    await page.mouse.move(700, 400);
    await page.waitForTimeout(220);
    const base = await readTips(page);
    const [x, y, w, h] = it.rect;
    await page.mouse.move(Math.round(x + w / 2), Math.round(y + h / 2));
    await page.waitForTimeout(760);
    const novel = (await readTips(page)).filter((t) => !base.includes(t));
    rows.push({ ...it, 气泡: novel });
    const 三者 = `aria=${JSON.stringify(it.aria)} title=${JSON.stringify(it.title)} 气泡=${novel.length ? `「${novel.join('/')}」` : '⛔无'}`;
    LOG(`  @${JSON.stringify(it.rect).padEnd(22)} ${三者}  data=${JSON.stringify(it.data)}`);
  }
  const 无名 = rows.filter((r) => !r.text && !r.aria && !r.title && !r.气泡.length);
  const 有气泡 = rows.filter((r) => r.气泡.length);
  LOG(`  —— 有气泡 ${有气泡.length} / 无文字 ${rows.filter((r) => !r.text).length}；⭐ **三处都没有、hover 也读不出 = ${无名.length} 个**`);
  for (const r of 无名) LOG(`     ⛔ 全无名: @${JSON.stringify(r.rect)} data=${JSON.stringify(r.data)} cls=${r.cls} svg=${JSON.stringify(r.svgPaths)}`);
  return rows;
};

const { browser, page } = await launch();
await boot(page);
const out = {};

// ---- 面 ①：节点卡片（选中后不点 ⤢，卡片就地展开）-----------------------------
await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  n.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: n.getBoundingClientRect().x + 40, clientY: n.getBoundingClientRect().y + 20 }));
}, IMG);
await page.waitForTimeout(1600);
out.节点卡片 = await sweep(page, '面① 节点卡片（图片节点 2 选中展开）', `.react-flow__node[data-id="${IMG}"]`);

// ---- 面 ④：大编辑器内部 --------------------------------------------------------
const fp = await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  const f = [...n.querySelectorAll('button')].find((b) => {
    const c = (b.className || '').toString();
    return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2');
  });
  if (!f) return null;
  const r = f.getBoundingClientRect();
  for (let dx = 4; dx < r.width; dx += 3) for (let dy = 4; dy < r.height; dy += 3) {
    const el = document.elementFromPoint(r.x + dx, r.y + dy);
    if (el && (el === f || f.contains(el) || el.contains(f))) return [Math.round(r.x + dx), Math.round(r.y + dy)];
  }
  return null;
}, IMG);
if (fp) { await page.mouse.click(fp[0], fp[1]); await page.waitForTimeout(1900); }
const 模态在 = await page.evaluate(() => {
  for (const e of document.body.children) { if (getComputedStyle(e).zIndex === '601') { const r = e.getBoundingClientRect(); if (r.width > 0) return true; } }
  return false;
});
LOG(`\n大编辑器开着: ${模态在}`);
if (模态在) out.大编辑器 = await sweep(page, '面④ 节点大编辑器（图片）', 'body > *');
// 关掉大编辑器：用右上角收拢箭头，不点画布空白
await page.evaluate(() => {
  for (const e of document.body.children) {
    if (getComputedStyle(e).zIndex === '601') {
      const b = [...e.querySelectorAll('button')].find((x) => { const r = x.getBoundingClientRect(); return r.y < 160 && r.x > 1000 && r.width <= 32; });
      if (b) b.click();
    }
  }
});
await page.waitForTimeout(1000);

// ---- 面 ②③：资产库广场 → 风格详情浮层 ------------------------------------------
const openAsset = await page.evaluate(() => {
  const b = document.querySelector('[data-sidebar-btn="open-asset"]');
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
});
if (openAsset) { await page.mouse.click(openAsset[0], openAsset[1]); await page.waitForTimeout(2000); }
const 广场在 = await page.evaluate(() => /风格库|风格广场|全部适配模型/.test(document.body.innerText || ''));
LOG(`\n资产库广场开着: ${广场在}`);
if (广场在) {
  out.广场 = await sweep(page, '面② 资产库广场（视口内）', null);
  // 进详情浮层
  const foldBtn = await page.evaluate(() => {
    // 卡上那枚 size-7 的 ⤢
    for (const c of document.querySelectorAll('.mantine-Modal-content *, [class*="card"] *, [class*="Card"] *')) {
      if (c.tagName !== 'BUTTON') continue;
      const cl = (c.className || '').toString();
      if (cl.includes('size-7')) { const r = c.getBoundingClientRect(); if (r.width > 0 && r.y > 60) return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }
    }
    return null;
  });
  LOG(`卡上那枚 ⤢ 落点: ${JSON.stringify(foldBtn)}`);
  if (foldBtn) { await page.mouse.click(foldBtn[0], foldBtn[1]); await page.waitForTimeout(1800); }
  const 详情在 = await page.evaluate(() => /风格详情/.test(document.body.innerText || ''));
  LOG(`详情浮层开着: ${详情在}`);
  if (详情在) out.详情浮层 = await sweep(page, '面③ 风格详情浮层', null);
}

await writeFile(new URL('./batchCU1.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n已写 tools/batchCU1.json');
await browser.close();
