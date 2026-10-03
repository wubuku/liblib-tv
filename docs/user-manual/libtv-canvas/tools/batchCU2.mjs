// Batch CU-2：修 CU-1 的两个作废面。
//
// CU-1 的结果分三档，如实分开：
//   ✅ 面① 节点卡片 —— **有效**。全画布只有 **2 枚**控件三处都读不出名
//   ⛔ 面④ 大编辑器 —— **作废**。`document.querySelector('body > *')` 只返回
//      **第一个** body 子元素，不是大编辑器 ⇒ 扫出 0 个。
//      治法：全页扫 + 用「祖先链里有没有 z-601」来归属。
//   ⛔ 面②③ 广场 / 详情浮层 —— **没测到**。广场那 59 个里，
//      20 个是画布自己的（顶栏 4 + 底栏 7 + 参数条 5 + 小地图 4），
//      广场卡片自己的按钮一个都没扫到；`⤢` 落点是 null。
//
// 本步：
//   ① 大编辑器内部全量扫（含收拢箭头 —— 它在面① 里是「全无名」那两枚之一）
//   ② 用正确路径打开风格详情浮层，扫它内部，⭐ 重点是右上角那枚 `⤡`
//      （手册记的是「读到图标，按钮无文字」，这轮要它有没有气泡）
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

// ⭐ 全页扫 + 按「祖先链里有 z-601 / 在抽屉里 / 在模态里」归属
const listAll = (page) => page.evaluate(() => {
  const zOf = (e) => { for (let p = e; p; p = p.parentElement) { const z = getComputedStyle(p).zIndex; if (z && z !== 'auto') return z; } return null; };
  const inModal = (e) => { for (let p = e; p; p = p.parentElement) if (getComputedStyle(p).zIndex === '601') return true; return false; };
  const inDrawer = (e) => !!e.closest('.mantine-Drawer-content,.mantine-Drawer-inner,[class*="Drawer"]');
  const inModalBox = (e) => { for (let p = e; p; p = p.parentElement) if (p.classList?.contains('mantine-Modal-content')) return true; return false; };
  const out = [];
  for (const e of document.querySelectorAll('button,[role="button"],[role="tab"],[role="menuitem"]')) {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) continue;
    const r = e.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    if (r.x + r.width < 0 || r.x > 1440 || r.y + r.height < 0 || r.y > 810) continue;
    out.push({
      在哪: inModal(e) ? '大编辑器' : inModalBox(e) ? '模态' : inDrawer(e) ? '抽屉' : '画布',
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 26),
      aria: e.getAttribute('aria-label'),
      title: e.getAttribute('title'),
      data: Object.fromEntries([...e.attributes].filter((a) => a.name.startsWith('data-')).map((a) => [a.name, a.value])),
      svgPaths: [...e.querySelectorAll('svg path')].map((p) => (p.getAttribute('d') || '').slice(0, 44)),
      cls: (e.className || '').toString().slice(0, 64),
    });
  }
  return out;
});
const readTips = (page) => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  return [...new Set([...document.querySelectorAll('[role="tooltip"],.mantine-Tooltip-tooltip')].filter(vis)
    .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter(Boolean))];
});
const sweep = async (page, 面, 只看) => {
  const all = await listAll(page);
  const items = all.filter((it) => (只看 ? it.在哪 === 只看 : true) && !it.text);
  LOG(`\n########## ${面}：视口内 ${all.length} 个可交互元素，其中**无文字** ${items.length} 个 ##########`);
  const rows = [];
  for (const it of items) {
    await page.mouse.move(700, 300);
    await page.waitForTimeout(210);
    const base = await readTips(page);
    const [x, y, w, h] = it.rect;
    await page.mouse.move(Math.round(x + w / 2), Math.round(y + h / 2));
    await page.waitForTimeout(760);
    const novel = (await readTips(page)).filter((t) => !base.includes(t));
    rows.push({ ...it, 气泡: novel });
    LOG(`  @${JSON.stringify(it.rect).padEnd(22)} aria=${JSON.stringify(it.aria)} title=${JSON.stringify(it.title)} 气泡=${novel.length ? `「${novel.join('/')}」` : '⛔无'} data=${JSON.stringify(it.data)}`);
  }
  const 无名 = rows.filter((r) => !r.aria && !r.title && !r.气泡.length);
  LOG(`  —— 有气泡 ${rows.filter((r) => r.气泡.length).length} / ${rows.length}；⭐ 三处都没有 = ${无名.length} 个`);
  for (const r of 无名) LOG(`     ⛔ @${JSON.stringify(r.rect)} cls=${r.cls} svg=${JSON.stringify(r.svgPaths)}`);
  return rows;
};

const { browser, page } = await launch();
await boot(page);
const out = {};

// ---- ① 大编辑器内部 -----------------------------------------------------------
await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  n.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: n.getBoundingClientRect().x + 40, clientY: n.getBoundingClientRect().y + 20 }));
}, IMG);
await page.waitForTimeout(1500);
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
if (fp) { await page.mouse.click(fp[0], fp[1]); await page.waitForTimeout(2000); }
const 在 = await page.evaluate(() => { for (const e of document.body.children) { if (getComputedStyle(e).zIndex === '601') { const r = e.getBoundingClientRect(); if (r.width > 0) return true; } } return false; });
LOG(`大编辑器开着: ${在}`);
if (在) out.大编辑器 = await sweep(page, '面④ 大编辑器内部', '大编辑器');

// ---- ② 风格详情浮层 -----------------------------------------------------------
// 先关大编辑器（点右上角收拢箭头本身）
await page.evaluate(() => {
  for (const e of document.body.children) {
    if (getComputedStyle(e).zIndex === '601') {
      const b = [...e.querySelectorAll('button')].find((x) => { const c = (x.className || '').toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
      if (b) b.click();
    }
  }
});
await page.waitForTimeout(1200);
LOG(`关掉后大编辑器还在: ${await page.evaluate(() => { for (const e of document.body.children) { if (getComputedStyle(e).zIndex === '601') { const r = e.getBoundingClientRect(); if (r.width > 0) return true; } } return false; })}`);

const oa = await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); const r = b.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
await page.mouse.click(oa[0], oa[1]);
await page.waitForTimeout(2200);
const 广场 = await page.evaluate(() => {
  const t = document.body.innerText || '';
  return { 有风格库: /风格库/.test(t), 卡片数: document.querySelectorAll('[class*="ard"]').length, 抽屉: !!document.querySelector('.mantine-Drawer-content,.mantine-Drawer-inner') };
});
LOG(`广场状态: ${JSON.stringify(广场)}`);
out.广场候选 = await page.evaluate(() => {
  // 把广场区域内的所有可交互元素按位置列出来，找那枚 ⤢（size-7 且 x>600）
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  return [...document.querySelectorAll('button,[role="button"]')].filter(vis)
    .map((b) => { const r = b.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), cls: (b.className || '').toString().slice(0, 50), aria: b.getAttribute('aria-label'), text: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14) }; })
    .filter((b) => b.x > 500 && b.y > 100)
    .slice(0, 40);
});
LOG(`广场区域(x>500,y>100)的可交互元素:\n${JSON.stringify(out.广场候选, null, 1)}`);

await writeFile(new URL('./batchCU2.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n已写 tools/batchCU2.json');
await browser.close();
