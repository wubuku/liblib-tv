#!/usr/bin/env node
/**
 * TDCanvas 界面元素「可发现性」探针（M129 建立，M132 全面重写）
 *
 * **要回答的问题**：手册里写的某个按钮名，读者在界面上能不能找到？
 *
 * **为什么值得做成脚本**：M125–M128、M132 四批都在这上面栽过跟头，而且**每次栽的方式不同**。
 * 这七条判据全部来自实踩的坑，写在这里是为了让下一批不再重犯：
 *
 * 1. **DOM 里有文字 ≠ 读者看得见**（M127 的第 61 次否证）
 *    Agent 面板 7 个按钮里确实存在「对话」「历史」这些文字节点，
 *    但 `getBoundingClientRect()` 全是 **0×0**。只判 `textContent` 会得出完全相反的结论。
 *    → 判可见性**必须**读 `getBoundingClientRect()` 的宽高。
 *    （M132 又见到一个更隐蔽的同族：顶栏主题按钮里的文字是 **1×1**。）
 *
 * 2. **原生 `title` 提示用 JS 读不到**（M127）
 *    它由浏览器渲染、不是 DOM 元素，`[role=tooltip]` 必然查不到。
 *    → 判「有没有提示」= **`title` 非空 OR 悬停后新出现的可见文本非空**。
 *
 * 3. **取持久化数据必须先 parse，且要认准 key**（M124 连错三次）
 *    - `getAllKeys()[0]` 取到的是 `tdcanvas:asset_store`，不是 `canvas_store`；
 *    - **`canvas_store` 的值不是对象，是一段 JSON 字符串**，不先 `JSON.parse`
 *      就 `v.state` 全是 `undefined`。
 *    - 三个坑的共同点：**失败时返回「空」而不是报错**，空读数长得像「产品没这个功能」。
 *
 * 4. **「元素存在且有几何」≠「用户看得见」**（M117 的 opacity:0、M127 的 0×0）
 *    → 一律走 `isReallyVisible()`：同时看自身尺寸、祖先 opacity/visibility/display。
 *
 * 5. **★ 悬停提示不能按 class 名找**（M132 的第 63 次否证，代价最大的一条）
 *    同一个左侧区域里**并存两种浮层实现**：
 *      - Dock 的按钮 → 自定义浮层，class 是
 *        `pointer-events-none absolute left-[calc(100%+8px)]`，**里面没有 tooltip / tip 任何字样**；
 *      - 视图控制、顶栏多数按钮 → antd 原生浮层 `div.ant-tooltip`。
 *    M126 及此前所有版本都按 `.ant-tooltip` / `[class*="tooltip"]` 找，
 *    于是**把 Dock 全部 8 个按钮读成「没有任何提示」**——而截图上浮层清清楚楚写着「清空画布」。
 *    → **本脚本改用「悬停前后可见文本增量」**：悬停前拍一张全页可见文本集合，
 *      悬停后取**差集**。这个判据不依赖任何 class 名。
 *    **教训：阴性读数先怀疑判据，别先怀疑产品。判据集合必须从实际数据数出来。**
 *
 * 6. **★ 自己造的数据会被自己过滤掉**（M132 第三版自己栽的）
 *    判「有没有提示」时写了 `新文本.filter(t => t !== aria).join()`，
 *    想着「浮层文字和 aria 一样不算新证据」——**结果把最常见的合法情况整个删光**，
 *    8 个有浮层的按钮全被判成「无提示」。
 *    → 过滤证据之前先问：**这条证据是不是恰恰因为「与已知值相同」才有意义？**
 *    报告里只允许出现**原始读数**，任何"清洗"都要在原始读数旁边并列显示。
 *
 * 7. **★ 阳性对照要证明"指针真的落在目标上"，而且别把自己的对照截断**（M132 第一版）
 *    判「无提示」之前必须先证明：悬停之后 `document.querySelectorAll(':hover')` 的链里
 *    **确实包含那个按钮**。M132 第一版在 `chain.length > 8` 时 `break`，
 *    而链正好有 8 层，**按钮永远落在截断线之外**——阳性对照自己废掉了。
 *    → `:hover` 链**不许截断**；同批里已知有浮层的按钮必须照样出浮层，否则整轮读数作废。
 *
 * 7b. **判据自己有洞，读数就不可信——用几何判「指针命中」，别用 aria 判**（M132 收尾）
 *     M132 新探针第一版拿「:hover 链里有没有这个按钮的 aria 名字」当命中判据，
 *     顶栏三个**没有 aria** 的按钮（画布名、版本号）于是全被误报成「没悬停到」。
 *     → 命中判据改成读链末端元素的 `getBoundingClientRect()`，看它是否落在按钮矩形内。
 *     **「我的判据有洞」和「产品有问题」要分开查，前者更常见。**
 *
 * 7c. **元素可能在视口外，鼠标压根进不去**（M132 顺带发现）
 *     顶栏「调整右侧面板宽度」那条把手宽 16px，因为带 `translate-x-1/2`，
 *     **有 9px 落在视口右缘之外**，脚本把鼠标移到它中心时已在屏幕外，
 *     `:hover` 链为空——**这条读数是「鼠标没进去」，不是「它没有提示」**。
 *     → 命中失败时先看末端几何是不是根本不在视口内。
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
//
// ★ 注意 `page.evaluate` 的两种传法完全不同：
//   - 传**字符串**  → 在页面上下文里求值，本文件所有浏览器端代码都走这条；
//   - 传**函数/对象**→ 在 Node 侧求值或序列化后再送进去。传 Promise 对象会直接报
//     `indexedDB is not defined`（那是 Node 作用域），传函数会报
//     `Attempting to serialize unexpected value`。
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
// 判据 1+4：全页可见文本与几何的快照（悬停前后各拍一张，取差集 = 判据 5）
// ─────────────────────────────────────────────────────────────
const SNAP = `(() => {
  const vis = (e) => {
    const r = e.getBoundingClientRect();
    if (!(r.width > 1 && r.height > 1)) return false;
    let p = e, depth = 0;
    while (p && depth < 12) {
      const cs = getComputedStyle(p);
      if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.05) return false;
      p = p.parentElement; depth++;
    }
    return true;
  };
  const texts = new Set();
  const floaters = [];
  for (const e of document.querySelectorAll('body *')) {
    if (!vis(e)) continue;
    const t = (e.textContent || '').trim();
    const kidHasSame = Array.from(e.children).some((c) => vis(c) && (c.textContent || '').trim() === t);
    if (!kidHasSame && t && t.length <= 40) texts.add(t);
    const r = e.getBoundingClientRect();
    // 「浮层状」：小、扁、不在按钮/工具区里面
    if (r.width > 20 && r.height > 10 && r.height < 60 && t && t.length <= 24
        && !e.closest('[data-canvas-tool],[data-canvas-view-control],[data-canvas-no-zoom],button,[role="button"]')) {
      floaters.push(Math.round(r.x) + ',' + Math.round(r.y) + ',' + Math.round(r.width) + 'x' + Math.round(r.height)
        + ' ' + e.tagName + '.' + (e.className || '').toString().slice(0, 50) + ' text=' + JSON.stringify(t));
    }
  }
  return { texts: Array.from(texts).sort(), floaters };
})()`;

// ─────────────────────────────────────────────────────────────
// 一批按钮的静态读数（不悬停）
// ─────────────────────────────────────────────────────────────
const READ_BATCH = (region) => {
  const vis = (e) => {
    const r = e.getBoundingClientRect();
    if (!(r.width > 1 && r.height > 1)) return { ok: false, why: '自身尺寸 ' + Math.round(r.width) + 'x' + Math.round(r.height) };
    let p = e, depth = 0;
    while (p && depth < 12) {
      const cs = getComputedStyle(p);
      if (cs.display === 'none') return { ok: false, why: p.tagName + ' 的 display:none' };
      if (cs.visibility === 'hidden') return { ok: false, why: p.tagName + ' 的 visibility:hidden' };
      if (parseFloat(cs.opacity) < 0.05) return { ok: false, why: p.tagName + ' 的 opacity:' + cs.opacity };
      p = p.parentElement; depth++;
    }
    return { ok: true, why: '' };
  };
  const hit = (b, r) => {
    if (region === 'dock') return !!b.closest('.td-canvas-dock');
    if (region === 'viewctrl') return !!b.closest('[data-canvas-view-control],[data-canvas-no-zoom]');
    if (region === 'topbar') return r.y < 120;
    if (region === 'bar') return !!b.closest('[data-canvas-node-hover-toolbar]');
    return false;
  };
  const list = Array.from(document.querySelectorAll('button, [role="button"]'))
    .map((b) => ({ b, r: b.getBoundingClientRect() }))
    .filter((x) => x.r.x >= 0 && x.r.y >= 0 && x.r.x < innerWidth && x.r.y < innerHeight && x.r.width > 0)
    .filter((x) => hit(x.b, x.r))
    .map((x) => x.b);
  return list.map((b) => {
    const r = b.getBoundingClientRect();
    const bv = vis(b);
    const spans = Array.from(b.querySelectorAll('span')).filter((s) => (s.textContent || '').trim()).map((s) => {
      const v = vis(s); const sr = s.getBoundingClientRect();
      return { text: (s.textContent || '').trim(), 读者看得见: v.ok, 原因: v.why, 尺寸: Math.round(sr.width) + 'x' + Math.round(sr.height) };
    });
    const svg = b.querySelector('svg');
    return {
      aria: b.getAttribute('aria-label'),
      title: b.getAttribute('title'),
      图标: svg ? (((svg.getAttribute('class') || '').match(/lucide-([a-z0-9-]+)/) || [])[1] || 'svg') : null,
      自身可见: bv.ok,
      文字: spans,
      尺寸: Math.round(r.width) + 'x' + Math.round(r.height),
      _w: Math.round(r.width), _h: Math.round(r.height),
      x: Math.round(r.x), y: Math.round(r.y),
    };
  }).sort((a, b) => (a.y - b.y) || (a.x - b.x));
};

/** 判据 7：悬停后读 :hover 链。**不许截断**——M132 第一版就是在这里废掉阳性对照的。 */
const HOVER_CHAIN = `(() => {
  const chain = Array.from(document.querySelectorAll(':hover'));
  const last = chain[chain.length - 1];
  let box = null;
  if (last) { const r = last.getBoundingClientRect(); box = [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; }
  return {
    链长: chain.length,
    末端: last ? last.tagName + (last.getAttribute('aria-label') ? '«' + last.getAttribute('aria-label') + '»' : '') : '(空)',
    末端几何: box,
  };
})()`;

// ─────────────────────────────────────────────────────────────

const REGIONS = [
  ['dock', '左侧 Dock（.td-canvas-dock）'],
  ['viewctrl', '视图控制与快捷键（data-canvas-view-control / data-canvas-no-zoom）'],
  ['topbar', '顶栏（y<120）'],
];

/**
 * 判据 5+6+7 的一轮完整测量：
 * 悬停前拍快照 → 移过去 → 读 :hover 链（阳性对照）→ 读新文本。
 * ★ 报告里原样输出新文本，**不做任何"清洗"**（判据 6）。
 */
async function measureRegion(page, region, rows) {
  for (const r of rows) {
    await page.mouse.move(900, 600);
    await page.waitForTimeout(300);
    const before = await page.evaluate(SNAP);
    await page.mouse.move(r.x + Math.max(4, r._w / 2), r.y + Math.max(4, r._h / 2), { steps: 4 });
    await page.waitForTimeout(1300);
    const chain = await page.evaluate(HOVER_CHAIN);
    const after = await page.evaluate(SNAP);
    const at = new Set(before.texts);
    r.悬停新增文本 = after.texts.filter((t) => !at.has(t));
    r.悬停新浮层 = after.floaters.filter((f) => !before.floaters.includes(f));
    r._链 = chain;
    // ★ 指针是否真的落在按钮上：**用几何判，不用 aria 判**。
    //   M132 第一版拿 :hover 链里的 aria 名字匹配，顶栏三个「无 aria」的按钮
    //   （画布名、版本号）一律误报成「没悬停到」——**判据自己有洞，读数就不可信**。
    const b = chain.末端几何;
    r._指针命中 = !!b && b[0] >= r.x - 2 && b[1] >= r.y - 2 && b[0] < r.x + r._w + 2 && b[1] < r.y + r._h + 2;
  }
  return rows;
}

function report(label, rows) {
  console.log('\n' + '='.repeat(90));
  console.log(label);
  console.log('='.repeat(90));
  if (!rows.length) { console.log('  （没有扫到按钮）'); return; }
  for (const r of rows) {
    const visibleText = r.文字.filter((t) => t.读者看得见).map((t) => t.text);
    // ★ 判据 6：原始读数原样输出。**不过滤**「与 aria 相同」的新文本。
    const hasHint = Boolean(r.title || r.悬停新增文本 || r.悬停新浮层.length);
    console.log('  · ' + (r.aria || '(无 aria)') + '  @' + r.x + ',' + r.y + ' ' + r.尺寸 + ' 图标=' + (r.图标 || '-'));
    console.log('      title=' + (r.title === null ? 'null' : (r.title || '(空串)')));
    console.log('      悬停新增文本=' + JSON.stringify(r.悬停新增文本));
    if (r.悬停新浮层.length) console.log('      悬停新浮层=' + JSON.stringify(r.悬停新浮层.slice(0, 2)));
    console.log('      指针命中=' + (r._指针命中 ? '是' : '★否（这条读数不可用）')
      + '  :hover 链长=' + r._链.链长 + ' 末端=' + r._链.末端 + ' 末端几何=' + JSON.stringify(r._链.末端几何));
    if (visibleText.length) console.log('      可见文字=' + visibleText.join(' / '));
    for (const t of r.文字) if (!t.读者看得见) console.log('      ↳ 隐形文字 ' + JSON.stringify(t.text) + ' ' + t.尺寸 + ' —— ' + t.原因);
    console.log('      读者能认出来吗：' + (hasHint || visibleText.length ? '能' : '不能'));
  }
  const bad = rows.filter((r) => r._指针命中 && !(r.title || r.悬停新增文本 || r.悬停新浮层.length) && !r.文字.some((t) => t.读者看得见));
  console.log('  —— 指针确实落上去、但认不出的：' + (bad.length ? bad.map((r) => r.aria || '(无 aria)').join('、') : '无'));
  const missed = rows.filter((r) => !r._指针命中);
  if (missed.length) console.log('  ⚠️ 指针没命中（读数不可用，别当结论）：' + missed.map((r) => r.aria || '(无 aria)').join('、'));
}

async function main() {
  const { chromium } = require(PW);
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    headless: true, viewport: { width: 1600, height: 950 }, args: ['--no-sandbox'],
  });
  const page = ctx.pages()[0] || (await ctx.newPage());
  page.setDefaultTimeout(25000);
  try {
    await page.goto(APP + '/canvas', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    const store = await page.evaluate(readStore);
    console.log('【判据 3】canvas_store 读数：');
    console.log('  字节数', store.bytes, '| version', store.version, '| 项目数', store.projectCount);
    console.log('  末尾项目：', JSON.stringify(store.projects));

    const target = process.argv[2] || (APP + '/canvas/' + (store.projects[store.projects.length - 1] || {}).id);
    console.log('\n目标画布：' + target + '   profile：' + PROFILE);
    await page.goto(target, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(4000);

    for (const [region, label] of REGIONS) {
      const rows = await page.evaluate(READ_BATCH, region);
      report('【判据 1+2+4+5+6+7】' + label, await measureRegion(page, region, rows));
    }

    console.log('\n**提醒**：本脚本只给读数，不判定对错。每条都要人工读过再决定改不改手册。');
    console.log('**再提醒**：浮层是间歇性出现的，读到「无」先按判据 7 确认指针命中，');
    console.log('          再考虑换判据（判据 5），最后才轮到怀疑产品。');
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
