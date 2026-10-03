// Batch CW-0：测「缩小」那枚到底点下去会怎样。
//
// CV 结掉了「它叫什么」（`aria-label="缩小"` / 图标 path 与大编辑器收拢箭头
// 逐字相同），但**「它做什么」还是 📖** —— 正文只写了「缩到最小化」，
// 那是从图标猜的。本轮把它点下去看。
//
// 要读清四件事：
//   ① 点完之后详情浮层变成什么样（尺寸 / 位置 / 内容还在不在）
//   ② **怎么还原**（有没有还原入口？没有的话这个功能就是单向的，值得写进手册）
//   ③ `ESC` 能不能关（⭐ 和 CM 批次那条「大编辑器 ESC 不可靠」做对照 ——
//      两个都是 Mantine 模态，行为若不同就说明不能一概而论）
//   ④ 广场那层的 `minimize`（`40×40`）是不是同一套行为
//
// ⛔ 安全：最小化是纯 UI 操作，不写盘、不扣积分、不加节点。
// ⚠️ 若发现「怎么都还原不回来」，**当场记下来并关掉浏览器**，不做后续实验。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const evidence = [];

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

// ⭐ 读「当前最上层浮层」：z / 尺寸 / 可见文字 / 全部可交互元素
const topLayer = (page) => page.evaluate(() => {
  const cands = [];
  const walk = (e) => {
    const s = getComputedStyle(e); const r = e.getBoundingClientRect();
    const z = parseInt(s.zIndex, 10);
    if (!Number.isNaN(z) && z >= 200 && r.width > 150 && r.height > 100) {
      cands.push({ z, el: e, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
    }
    for (const c of e.children) walk(c);
  };
  walk(document.body);
  if (!cands.length) return null;
  cands.sort((a, b) => b.z - a.z);
  const top = cands[0];
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  return {
    z: top.z, rect: top.rect,
    cls: (top.el.className || '').toString().slice(0, 50),
    可见文字: (top.el.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 150),
    按钮: [...top.el.querySelectorAll('button,[role="button"]')].filter(vis).map((b) => {
      const r = b.getBoundingClientRect();
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], aria: b.getAttribute('aria-label'), text: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16) };
    }).sort((a, b) => a.rect[0] - b.rect[0]),
  };
});
// 所有 z>=200 的浮层（最小化后可能有多个小浮层）
const allLayers = (page) => page.evaluate(() => {
  const cands = [];
  const walk = (e) => {
    const s = getComputedStyle(e); const r = e.getBoundingClientRect();
    const z = parseInt(s.zIndex, 10);
    if (!Number.isNaN(z) && z >= 200 && r.width > 20 && r.height > 20) {
      cands.push({ z, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], cls: (e.className || '').toString().slice(0, 46), text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) });
    }
    for (const c of e.children) walk(c);
  };
  walk(document.body);
  return cands.sort((a, b) => b.z - a.z);
});

const out = { steps: [] };
const mark = async (label) => {
  const s = await topLayer(page);
  const all = await allLayers(page);
  out.steps.push({ label, top: s, all });
  LOG(`\n▸ ${label}`);
  LOG(`   全部 z>=200 的浮层 ${all.length} 个: ${JSON.stringify(all)}`);
  if (s) { LOG(`   最上层 z=${s.z} rect=${JSON.stringify(s.rect)}`); LOG(`   文字: ${JSON.stringify(s.可见文字)}`); LOG(`   按钮: ${JSON.stringify(s.按钮)}`); }
  else LOG(`   ⛔ 没有 z>=200 的浮层`);
  return s;
};

// ---- 走到详情浮层 ---------------------------------------------------------------
await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); b.click(); });
await page.waitForTimeout(1800);
const itemInfo = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'));
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
});
LOG(`「风格库」按钮: ${JSON.stringify(itemInfo)}`);
if (itemInfo) {
  await page.evaluate(() => [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
  await page.waitForTimeout(2600);
}
const detInfo = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button[aria-label="详情"]')].find((x) => { const r = x.getBoundingClientRect(); return r.width > 0; });
  if (!b) return null;
  b.click();
  return true;
});
if (detInfo) await page.waitForTimeout(2200);
const before = await mark('① 详情浮层（点「缩小」之前）');
await shot(page, 'CW-a-详情浮层-缩小之前.png'); evidence.push('CW-a-详情浮层-缩小之前.png');

// ---- ② 点「缩小」 ---------------------------------------------------------------
const shrinkInfo = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button[aria-label="缩小"]')].find((x) => { const r = x.getBoundingClientRect(); return r.width > 0; });
  if (!b) return null;
  const r = b.getBoundingClientRect();
  b.click();
  return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
});
LOG(`\n「缩小」按钮: ${JSON.stringify(shrinkInfo)}`);
if (shrinkInfo) await page.waitForTimeout(1600);
const after = await mark('② 点「缩小」之后');
await shot(page, 'CW-b-点缩小之后.png'); evidence.push('CW-b-点缩小之后.png');

// ---- ③ 能不能还原 ---------------------------------------------------------------
out.还原入口 = null;
if (after) {
  out.还原入口 = after.按钮.map((b) => ({ ...b, 像还原: /还原|展开|恢复|maximize|放大/i.test(`${b.aria || ''}${b.text || ''}`) }));
  LOG(`\n③ 缩小后的可交互元素里有没有「还原」:`);
  for (const b of after.按钮) LOG(`   @${JSON.stringify(b.rect)} aria=${JSON.stringify(b.aria)} text=${JSON.stringify(b.text)} ${b.像还原 ? '⭐ 像还原入口' : ''}`);
  // ⭐ 悬停所有按钮看气泡（可能有 tooltip 提示怎么还原）
  const readTips = () => page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
    return [...new Set([...document.querySelectorAll('[role="tooltip"]')].filter(vis).map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter(Boolean))];
  });
  for (const b of after.按钮) {
    await page.mouse.move(300, 400); await page.waitForTimeout(200);
    const base = await readTips();
    await page.mouse.move(b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2);
    await page.waitForTimeout(760);
    const t = (await readTips()).filter((x) => !base.includes(x));
    if (t.length) { b.气泡 = t; LOG(`   ⭐ 悬停 @${JSON.stringify(b.rect)} → 「${t.join('/')}」`); }
  }
  await shot(page, 'CW-c-缩小后悬停.png'); evidence.push('CW-c-缩小后悬停.png');
}

// ---- ④ ESC 能不能关 -------------------------------------------------------------
await page.keyboard.press('Escape');
await page.waitForTimeout(1200);
const afterEsc = await mark('④ 缩小状态下按 ESC');
out.ESC后浮层数 = afterEsc ? 1 : 0;

await writeFile(new URL('./batchCW0.json', import.meta.url), JSON.stringify(out, null, 2));
LOG(`\n已写 tools/batchCW0.json；证据图 ${evidence.length} 张`);
await browser.close();
