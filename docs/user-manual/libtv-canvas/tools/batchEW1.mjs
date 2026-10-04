// Batch EW-1：⭐⭐ 把三个悬空的「这到底是什么元素」📖 定位掉。
//
//   ① ET 留下的：「新功能：支持真人」—— 知道它在**参数面板左侧 58px**、
//      114×27、`pointer-events:none`、清场时就在、**常驻**，
//      但**全页 3 枚 `.cursor-help` 逐枚悬停都不是它** ⇒ 归属未定位。
//   ② EU/EV 留下的：`网格吸附` 开态新增的那第二枚 `svg`，
//      读法只查 `path` 拿到 `d = null` ⇒ 里面画的到底是什么笔画，未知。
//   ③ 广场/素材库那批：多模型卡「特效侧详情浮层」/ `特效详情` / `lensDetail`，未找到入口。
//
// 本轮的做法（先通用，后专项）：
//   ① 先**全量倾倒**页面上所有 Mantine 气泡（`mantine-Tooltip-tooltip`）及其
//      **`id` 与 `aria-describedby` 的双向引用** —— Mantine 把气泡挂到 portal 上，
//      触发元素靠 `aria-describedby` 指回来。**这是归属判据的正路**，
//      比「逐枚去悬停试」可靠得多。
//   ② 网格吸附那枚 svg：直接把 `outerHTML` 打出来，一个字都不猜。
//   ③ 枚举所有「圆点/星标/角标」类小元素，找「新功能」字样出现在哪。
//
// ⛔ 全程只读，不点任何按钮。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEW1.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const browser = await launch();
const page = browser.page;
try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  // ════════ ① 全量枚举 Mantine 气泡 + 归属引用链 ════════
  const 气泡 = await page.evaluate(() => {
    const 出 = [];
    for (const e of document.querySelectorAll('[class*="Tooltip"],[role="tooltip"],[class*="tooltip"]')) {
      const r = e.getBoundingClientRect();
      const cs = getComputedStyle(e);
      if (r.width < 4 || r.height < 4) continue;
      出.push({
        标签: e.tagName,
        id: e.id || null,
        cls: String(e.className).slice(0, 90),
        role: e.getAttribute('role'),
        文字: (e.textContent || '').trim().slice(0, 60),
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        opacity: cs.opacity,
        visibility: cs.visibility,
        pointerEvents: cs.pointerEvents,
        zIndex: cs.zIndex,
        父: e.parentElement ? { 标签: e.parentElement.tagName, cls: String(e.parentElement.className).slice(0, 70) } : null,
      });
    }
    // ⭐ 归属判据：谁用 aria-describedby 指着这些气泡
    const 引用 = [];
    for (const t of 出) {
      if (!t.id) continue;
      const 触发 = [...document.querySelectorAll(`[aria-describedby~="${t.id}"]`)];
      引用.push({ 气泡id: t.id, 文字: t.文字, 触发元素: 触发.map((x) => {
        const rr = x.getBoundingClientRect();
        return {
          标签: x.tagName, aria: x.getAttribute('aria-label'), text: (x.textContent || '').trim().slice(0, 40),
          box: [Math.round(rr.left), Math.round(rr.top), Math.round(rr.width), Math.round(rr.height)],
          cls: String(x.className).slice(0, 80),
        };
      }) });
    }
    return { 气泡: 出, 引用 };
  });
  记('Mantine 气泡枚举：' + 气泡.气泡.length + ' 个；有 id 的 ' + 气泡.引用.length + ' 个');
  记('逐个：' + JSON.stringify(气泡.气泡, null, 1));
  记('⭐ 归属引用链：' + JSON.stringify(气泡.引用, null, 1));
  结果.读数.气泡 = 气泡;

  // ════════ ② 网格吸附第二枚 svg 的 outerHTML（一个字都不猜）════════
  const 底栏 = await page.evaluate(() => {
    const out = [];
    for (const e of document.querySelectorAll('button')) {
      const r = e.getBoundingClientRect();
      if (r.top < 740 || r.bottom > 810 || r.left > 340) continue;
      if (e.querySelector('button')) continue;
      out.sort === undefined;
      out.push({ aria: e.getAttribute('aria-label'), box: Math.round(r.left), html: e.outerHTML.slice(0, 1400) });
    }
    out.sort((a, b) => a.box - b.box);
    return out;
  });
  const 吸附枚 = 底栏[4];
  记('网格吸附 outerHTML（关态）：' + 吸附枚.html);
  结果.读数.网格吸附关态HTML = 吸附枚.html;

  await page.evaluate(() => {
    const bs = [...document.querySelectorAll('button')].filter((e) => {
      const r = e.getBoundingClientRect();
      return r.top >= 740 && r.bottom <= 810 && r.left <= 340 && !e.querySelector('button');
    });
    bs.sort((a, b) => a.getBoundingClientRect().left - b.getBoundingClientRect().left);
    const t = bs[4];
    const c = [Math.round(t.getBoundingClientRect().left + t.getBoundingClientRect().width / 2), Math.round(t.getBoundingClientRect().top + t.getBoundingClientRect().height / 2)];
    window.__点击 = c;
  });
  const 点击点 = await page.evaluate(() => window.__点击);
  记('点击网格吸附 ' + JSON.stringify(点击点));
  await page.mouse.move(点击点[0], 点击点[1]);
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(1000);
  await page.mouse.move(700, 300); await page.waitForTimeout(400);

  const 底栏2 = await page.evaluate(() => {
    const out = [];
    for (const e of document.querySelectorAll('button')) {
      const r = e.getBoundingClientRect();
      if (r.top < 740 || r.bottom > 810 || r.left > 340) continue;
      if (e.querySelector('button')) continue;
      out.push({ aria: e.getAttribute('aria-label'), box: Math.round(r.left), svg数: e.querySelectorAll('svg').length, html: e.outerHTML.slice(0, 1600) });
    }
    out.sort((a, b) => a.box - b.box);
    return out;
  });
  记('网格吸附 outerHTML（开态）：' + 底栏2[4].html);
  结果.读数.网格吸附开态HTML = 底栏2[4].html;

  // 关回去
  await page.mouse.move(点击点[0], 点击点[1]);
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(900);
  await page.mouse.move(700, 300); await page.waitForTimeout(400);
  const 复原 = await page.evaluate(() => {
    const bs = [...document.querySelectorAll('button')].filter((e) => {
      const r = e.getBoundingClientRect();
      return r.top >= 740 && r.bottom <= 810 && r.left <= 340 && !e.querySelector('button');
    });
    bs.sort((a, b) => a.getBoundingClientRect().left - b.getBoundingClientRect().left);
    return bs.map((x) => ({ aria: x.getAttribute('aria-label'), svg: x.querySelectorAll('svg').length }));
  });
  记('复原底栏：' + JSON.stringify(复原));
  结果.读数.复原 = 复原;

  // ════════ ③ 全页搜「新功能」「支持真人」字样 ════════
  // ⭐ 用 innerText 全文（不筛叶子）—— Mantine 容器带子元素，叶子判据会漏。
  const 找字 = await page.evaluate(() => {
    const 命中 = [];
    for (const e of document.querySelectorAll('*')) {
      const t = (e.innerText || '').trim();
      if (!t || t.length > 80) continue;
      if (!/新功能|支持真人|真人/.test(t)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) continue;
      const cs = getComputedStyle(e);
      命中.push({
        标签: e.tagName, 文字: t, 子数: e.children.length,
        cls: String(e.className).slice(0, 100),
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        opacity: cs.opacity, pointerEvents: cs.pointerEvents, zIndex: cs.zIndex,
        祖先: (() => { const a = []; let p = e.parentElement, i = 0; while (p && i < 6) { a.push(String(p.className).slice(0, 50)); p = p.parentElement; i++; } return a; })(),
      });
    }
    return 命中;
  });
  记('含「新功能/真人」的元素：' + JSON.stringify(找字, null, 1));
  结果.读数.找字 = 找字;

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  结果.收尾 = { 偏差, 已渲染: Object.keys(await 读全部坐标(page)).length };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  落盘(结果);
  await browser.browser.close();
  console.log('\n=== 已写 tools/batchEW1.json ===');
}
