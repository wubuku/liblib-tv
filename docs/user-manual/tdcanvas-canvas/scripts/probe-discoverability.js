#!/usr/bin/env node
/**
 * TDCanvas 界面元素「可发现性」探针（M129 建立）
 *
 * **要回答的问题**：手册里写的某个按钮名，读者在界面上能不能找到？
 *
 * **为什么值得做成脚本**：M125–M128 四批都在这上面栽过跟头，而且**每次栽的方式不同**。
 * ���四条判据全部来自实踩的坑，写在这里是为了让下一批不再重犯：
 *
 * 1. **DOM 里有文字 ≠ 读者看得见**（M127 的第 61 次否证）
 *    Agent 面板 7 个按钮里确实存在「对话」「历史」这些文字节点，
 *    但 `getBoundingClientRect()` 全是 **0×0**——`opacity: 1`、`visibility: visible`、
 *    祖先链一切正常，**却占不了任何地方**。只判 `textContent` 会得出完全相反的结论。
 *    → 判可见性**必须**读 `getBoundingClientRect()` 的宽高。
 *
 * 2. **原生 `title` 提示用 JS 读不到**（M127）
 *    它由浏览器渲染、不是 DOM 元素，`[role=tooltip]` 必然查不到。
 *    → 判「有没有提示」= **`title` 非空 OR 自定义浮层非空**，不能只看浮层。
 *
 * 3. **取持久化数据必须先 parse，且要认准 key**（M124 连错三次）
 *    - `getAllKeys()[0]` 取到的是 `tdcanvas:asset_store`，不是 `canvas_store`；
 *    - **`canvas_store` 的值不是对象，是一段 JSON 字符串**，不先 `JSON.parse`
 *      就 `v.state` 全是 `undefined`。
 *    - 三个坑的共同点：**失败时返回「空」而不是报错**，空读数长得像「产品没这个功能」。
 *    → 本脚本的 `readStore` 已把这三处封死，且**缺 key / 解析失败一律显式抛错**。
 *
 * 4. **「元素存在且有几何」≠「用户看得见」**（M117 的 opacity:0、M128 的 0×0）
 *    → 一律走 `isReallyVisible()`：同时看自身尺寸、祖先 opacity/visibility/display。
 *
 * **用法**
 *   node scripts/probe-discoverability.js [画布URL]
 *   默认连 http://localhost:3000/canvas/<第一个有图片节点的画布>，
 *   profile 取 TD_PROBE_PROFILE 或 /tmp/m124-profile（**默认不碰共享 profile**）。
 *
 * **它不是什么**：不是门禁。它输出的是**候选读数**，和 audit-trouble-to-tasks.py 一样，
 * 每一条都要人工读过再决定改不改手册。
 */

const PW = process.env.TD_PW ||
  '/Users/yangjiefeng/.nvm/versions/node/v24.6.0/lib/node_modules/@playwright/test/node_modules/playwright/index.js';
const PROFILE = process.env.TD_PROBE_PROFILE || '/tmp/m124-profile';
const APP = process.env.TD_APP || 'http://localhost:3000';

// ─────────────────────────────────────────────────────────────
// 判据 3：读 canvas_store（key 要写死，值必须先 parse）
// ─────────────────────────────────────────────────────────────
const readStore = `new Promise((resolve, reject) => {
  const KEY = 'tdcanvas:canvas_store';            // 不用 getAllKeys()[0]（那是 asset_store）
  const req = indexedDB.open('tdcanvas');
  req.onerror = () => reject(new Error('open 失败：' + req.error));
  req.onsuccess = () => {
    let tx;
    try { tx = req.result.transaction('app_state', 'readonly'); }
    catch (e) { return reject(new Error('取 app_state 失败：' + e.message)); }
    const g = tx.objectStore('app_state').get(KEY);
    g.onerror = () => reject(new Error('get ' + KEY + ' 失败：' + g.error));
    g.onsuccess = () => {
      const raw = g.result;
      if (raw === undefined) return reject(new Error(KEY + ' 不存在——**这是真读不到，别当成「数据为空」**'));
      if (typeof raw !== 'string') return reject(new Error(KEY + ' 不是字符串（是 ' + typeof raw + '），本脚本的 parse 假设已失效，请复核'));
      let obj;
      try { obj = JSON.parse(raw); }          // ← 不 parse 的话下面全是 undefined
      catch (e) { return reject(new Error(KEY + ' 不是合法 JSON：' + e.message)); }
      const state = obj && obj.state ? obj.state : obj;
      resolve({
        bytes: raw.length,
        version: obj && obj.version,
        stateKeys: Object.keys(state || {}),
        projectCount: (state.projects || []).length,
        projects: (state.projects || []).slice(-3).map((p) => ({ id: p.id, name: p.name, nodes: (p.nodes || []).length })),
      });
    };
  };
})`;

// ─────────────────────────────────────────────────────────────
// 判据 2：读一批按钮的「四者」
//
// ★ 用 Playwright 的参数传递（第二个参数），**不要**把 Node 作用域的变量
//   拼进回调字符串——M125 就栽在 `r0 => r0` 这种拿不到值的形参上，
//   症状同样是「读出来是空的」，很容易被当成产品行为。
// ─────────────────────────────────────────────────────────────
const READ_BATCH = (sel) => {
  const vis = (e) => {
    const r = e.getBoundingClientRect();
    if (!(r.width > 1 && r.height > 1)) {
      return { ok: false, why: '自身尺寸 ' + Math.round(r.width) + 'x' + Math.round(r.height) };
    }
    let p = e, depth = 0;
    while (p && depth < 10) {
      const cs = getComputedStyle(p);
      if (cs.display === 'none') return { ok: false, why: p.tagName + ' 的 display:none' };
      if (cs.visibility === 'hidden') return { ok: false, why: p.tagName + ' 的 visibility:hidden' };
      if (parseFloat(cs.opacity) < 0.05) return { ok: false, why: p.tagName + ' 的 opacity:' + cs.opacity };
      p = p.parentElement; depth++;
    }
    return { ok: true, why: '' };
  };
  const list = sel === '__bar__'
    ? Array.from((document.querySelector('[data-canvas-node-hover-toolbar]') || { querySelectorAll: () => [] }).querySelectorAll('[data-canvas-node-toolbar-action]'))
    : Array.from(document.querySelectorAll('button, [role="button"]'))
        .map((b) => ({ b, r: b.getBoundingClientRect() }))
        .filter((x) => x.r.x >= 0 && x.r.y >= 0 && x.r.x < innerWidth && x.r.y < innerHeight && x.r.width > 0)
        .filter((x) => x.r.x < 300 && x.r.width <= 80)
        .map((x) => x.b);
  return list.map((b) => {
    const r = b.getBoundingClientRect();
    const textNodes = Array.from(b.querySelectorAll('span'))
      .filter((s) => (s.textContent || '').trim())
      .map((s) => {
        const v = vis(s);
        const sr = s.getBoundingClientRect();
        return { text: (s.textContent || '').trim(), 读者看得见: v.ok, 原因: v.why, 尺寸: Math.round(sr.width) + 'x' + Math.round(sr.height) };
      });
    const svg = b.querySelector('svg');
    const lucide = svg ? ((svg.getAttribute('class') || '').match(/lucide-([a-z0-9-]+)/) || [])[1] || null : null;
    const bv = vis(b);
    return {
      aria: b.getAttribute('aria-label'),
      title: b.getAttribute('title'),      // 原生提示：读不到浮层，只能判属性在不在
      图标: lucide,
      自身可见: bv.ok,
      文字: textNodes,
      尺寸: Math.round(r.width) + 'x' + Math.round(r.height),
      x: Math.round(r.x), y: Math.round(r.y),
    };
  });
};

// ─────────────────────────────────────────────────────────────

async function hoverTip(page) {
  return page.evaluate(() => {
    const c = Array.from(document.querySelectorAll('[role="tooltip"], .ant-tooltip, [class*="tooltip"]'))
      .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
    return c.length ? (c[c.length - 1].innerText || '').trim() : null;
  });
}

/** 逐个悬停补上「悬停浮层」这一栏（title 那一栏脚本自己就读得到） */
async function attachTips(page, rows) {
  for (const r of rows) {
    await page.mouse.move(700, 700);
    await page.waitForTimeout(220);
    await page.mouse.move(r.x + 6, r.y + 6, { steps: 2 });
    await page.waitForTimeout(950);
    r.悬停浮层 = await hoverTip(page);
  }
  return rows;
}

function report(label, rows) {
  console.log('\n' + '='.repeat(78));
  console.log(label);
  console.log('='.repeat(78));
  if (!rows.length) { console.log('  （没有扫到按钮）'); return; }
  console.log('  aria-label'.padEnd(26) + '图标'.padEnd(20) + '可见文字'.padEnd(14) + 'title'.padEnd(10) + '悬停浮层'.padEnd(14) + '认得出吗');
  console.log('  ' + '-'.repeat(74));
  for (const r of rows) {
    const visibleText = r.文字.filter((t) => t.读者看得见).map((t) => t.text).join('/');
    // ★ 判据只认真值，不认占位符。
    //   写成 `const hint = r.title || r.悬停浮层 || '(无)'` 再 `Boolean(hint)`，
    //   那个 '(无)' 是**非空字符串、truthy**，于是「有没有提示」恒判为有——
    //   **这与 M125–M128 反复栽的「把『没有』编码成 truthy 哨兵」是同一类错**
    //   （探针读数看着正常，结论却整个反过来）。显示时才补占位符。
    const hasHint = Boolean(r.title || r.悬停浮层);
    const hasVisible = visibleText.length > 0;
    const readable = hasHint || hasVisible;
    console.log('  ' +
      (r.aria || '(无 aria)').slice(0, 24).padEnd(26) +
      (r.图标 || '-').slice(0, 18).padEnd(20) +
      (hasVisible ? visibleText : '(无)').slice(0, 12).padEnd(14) +
      (r.title || '无').slice(0, 8).padEnd(10) +
      (r.悬停浮层 || '无').slice(0, 12).padEnd(14) +
      (readable ? '能' : '不能'));
    // 隐形文字要单独点名——这正是 M127 踩过的坑
    for (const t of r.文字) {
      if (!t.读者看得见) console.log('        ↳ 隐形文字 ' + JSON.stringify(t.text) + ' ' + t.尺寸 + ' —— ' + t.原因);
    }
  }
  const unread = rows.filter((r) => !(r.title || r.悬停浮层) && !r.文字.some((t) => t.读者看得见));
  console.log('  —— 认不出的（既无提示又无可见文字）：' + (unread.length ? unread.map((r) => r.aria || '(无 aria)').join('、') : '无'));
}

async function main() {
  const { chromium } = require(PW);
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    headless: true, viewport: { width: 1600, height: 950 }, args: ['--no-sandbox'],
  });
  const page = ctx.pages()[0] || (await ctx.newPage());
  page.setDefaultTimeout(25000);
  try {
    // 1) 先取一个能用的画布
    await page.goto(APP + '/canvas', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    const store = await page.evaluate(readStore);
    console.log('【判据 3】canvas_store 读数：');
    console.log('  字节数', store.bytes, '| version', store.version, '| 项目数', store.projectCount);
    console.log('  state 的键：', store.stateKeys.join('、'));
    console.log('  末尾项目：', JSON.stringify(store.projects));

    const target = process.argv[2] || (APP + '/canvas/' + (store.projects[store.projects.length - 1] || {}).id);
    console.log('\n目标画布：' + target + '   profile：' + PROFILE);
    await page.goto(target, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(4000);

    // 2) 左侧一列（Dock）：x < 300、宽 <= 80
    const dockRows = await attachTips(page, await page.evaluate(READ_BATCH, 'dock'));
    report('【判据 1+2+4】左侧 Dock（x<300、宽≤80）', dockRows);

    // 3) 节点工具条：必须先点选（纯悬停弹不出来）
    const hasNode = await page.evaluate(() => {
      const e = document.querySelector('[data-node-id]');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
    });
    if (hasNode) {
      await page.mouse.click(hasNode.x + hasNode.w / 2, hasNode.y + hasNode.h / 2);
      await page.waitForTimeout(1500);
      const barRows = await attachTips(page, await page.evaluate(READ_BATCH, '__bar__'));
      if (barRows.length) {
        report('【判据 1+2+4】节点悬浮工具条（点选后出现；纯悬停弹不出来）', barRows);
      } else {
        console.log('\n（点选后仍无工具条——先确认节点没被别的节点压住，再下结论）');
      }
    }

    console.log('\n**提醒**：本脚本只给读数，不判定对错。每条都要人工读过再决定改不改手册。');
  } catch (e) {
    console.error('\n[失败] ' + e.message);
    console.error('**读不到 ≠ 数据为空**——按判据 3 的说法，先确认 key 与 parse，别直接把空读数当结论。');
    process.exitCode = 1;
  } finally {
    try { await ctx.close(); } catch (_) {}
    setTimeout(() => process.exit(process.exitCode || 0), 300);
  }
}

main();
