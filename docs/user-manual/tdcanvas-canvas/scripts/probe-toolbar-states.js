#!/usr/bin/env node
/**
 * TDCanvas 节点工具条探针（M138 建立）
 *
 * 与 `probe-discoverability.js` 分工：那个管「按钮认不认得出」，
 * 这个管「**点了会变成什么样**」——每个按钮做 A/B 两态，逐个比对四个状态信号。
 *
 * **为什么单独做成脚本**：M136 与 M137 连续两批在这里栽了跟头，而且**两次栽法不同**。
 * 这几条写在这里是为了让下一批不再重犯：
 *
 * 1. **★ 不可逆操作必须先列白名单**（M136 立，M193 补全）
 *    M136 第一版逐个点击工具条上的 13 个按钮，**第二个就是「移除节点」——
 *    节点被脚本自己删了**，后面 11 个读数全部作废。
 *    M 系列的既有纪律只写了「不触发付费生成」，**没覆盖「删除」这一类同样不可逆的本地操作**。
 *    → 本脚本的 `DESTRUCTIVE` 是一道**硬闸**，命中就跳过。
 *    → **跳过也必须留痕**：报告里明确写出「哪几个没测、为什么没测」，
 *      **不能让读数看起来是完整的**。
 *    ★ **M193 补：原名单四项全是画布页文案，漏了首页那两个**（运行时扫五个非画布页得到，
 *      危险动词筛选后只剩「删除」「删除全部」两个文案，提示词库 / 配置 / ComfyUI 本地为 0）。
 *      **漏项比过宽更危险**——过宽只是少测，漏项是「后果最重的按钮被当成安全按钮」。
 *      M192 正是栽在「删除全部」上（它不在名单里，却比名单里任何一项都重）。
 *
 * 2. **★ 节点默认全部叠在画布中心**（M137 第一版栽在这）
 *    按 DOM 顺序取「最后一个」的中心点点选，**命中的永远是最上层那一个**。
 *    症状：七种类型数出来全是同一个节点的按钮，**按钮文字逐轮往后挪一位**。
 *    **长得像「产品有个统一的工具条」，实际是探针一直在数同一个节点。**
 *    → 三道保险：① 每轮先清空画布，保证一次只有一个节点；
 *      ② 点选前用 **`elementFromPoint` 阳性对照**确认那个点确实落在目标节点上；
 *      ③ 同时读节点标题，与目标不符立刻判作废。
 *
 * 3. **★ 浮层坐标要实测读出来，不能按间距推**（M137 第一版）
 *    按「面板高 352、每项 40、间距 42」推出七项的 y，整体偏了 42px，
 *    点「文本」建出了**图片节点**——**症状与第 2 条一模一样：数出来是别的节点的按钮**。
 *    → 先开一次面板把每项的真实 y 读出来再用。
 *
 * 4. **★ `page.evaluate` 传函数的两种形式，结果完全不同**
 *    - 传**字符串** → 在页面上下文求值；字符串里写箭头函数的话，
 *      求值出来是「一个函数对象」，序列化回去是 **`undefined`**。
 *    - 传**函数 + 第二个参数** → 标准用法，按值传参。
 *    症状是 `undefined`，**看起来像「探针坏了」**。
 *
 * 5. **★ IndexedDB 写入的两个坑**（M136，见 SOURCE_OBSERVATIONS）
 *    - `app_state` 用 **out-of-line keys**，`put` **必须显式传 key**：`os.put(value, K)`。
 *    - 应用跑在 **Vite dev** 下、且同仓库有别的 agent 正在改源码时，
 *      HMR 不断触发整页重载，**任何跨几百毫秒的 `page.evaluate` 都会撞上
 *      `Execution context was destroyed`**。解法是把写入放进 **`page.addInitScript`**。
 *    **两条的失败症状都长得像「产品没这功能」或「探针写错了」。**
 *
 * 6. **★ 「按钮本身没有状态变化」≠「这个功能没有状态」**（M136 读法纪律）
 *    本脚本读的是**按钮元素**上的 `aria-pressed` / `aria-expanded` /
 *    `aria-checked` / `aria-current` 与图标类名。
 *    像「隐藏连线」那种开关，状态是显示在**按钮外观**上的，不在这些属性里。
 *    **写进手册时必须把这条读法边界一起写上，否则会被读成「这个功能没有状态」。**
 *
 * **用法**
 *   node scripts/probe-toolbar-states.js [画布URL]
 *   profile 取 TD_PROBE_PROFILE 或 /tmp/m124-profile（**默认不碰共享 profile**）。
 *
 * **它不是什么**：不是门禁。每条读数都要人工读过再决定改不改手册。
 */

// ── 不可逆操作硬闸（M136 教训 1）────────────────────────────────
// M193：末尾两项是首页的（卡片上的「删除」与页面上的「删除全部」），
// 由运行时扫五个非画布页得到，不是抄来的。**「删除全部」一次删掉所有画布、不可恢复**，
// 是整个应用里后果最重的一个按钮——它此前不在名单里。
const DESTRUCTIVE = new Set(['移除节点', '清空画布', '删除当前画布', '删除选中', '删除', '删除全部']);

const PW = process.env.TD_PW ||
  '/Users/yangjiefeng/.nvm/versions/node/v24.6.0/lib/node_modules/@playwright/test/node_modules/playwright/index.js';
const PROFILE = process.env.TD_PROBE_PROFILE || '/tmp/m124-profile';
const APP = process.env.TD_APP || 'http://localhost:3000';

// 判据 5：读取面板里每一项的**真实**坐标，不按间距推
const READ_FLYOUT = `(() => {
  const f = document.querySelector('.td-canvas-flyout');
  if (!f) return null;
  return Array.from(f.querySelectorAll('button')).map((b) => {
    const r = b.getBoundingClientRect();
    return { 文字: (b.innerText || '').replace(/\\s+/g, ' ').trim(),
             x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
  });
})()`;

const NODES = `(() => Array.from(document.querySelectorAll('[data-node-id]')).map((e) => {
  const r = e.getBoundingClientRect();
  return { id: e.getAttribute('data-node-id'),
           title: (e.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 40),
           x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
}))()`;

const READ_BAR = `(() => {
  const bar = document.querySelector('[data-canvas-node-hover-toolbar]');
  if (!bar) return null;
  const btns = Array.from(bar.querySelectorAll('[data-canvas-node-toolbar-action]'));
  return {
    n: btns.length,
    名称: btns.map((b) => b.getAttribute('aria-label')),
    按钮文字: btns.map((b) => {
      const s = Array.from(b.querySelectorAll('span')).map((x) => (x.textContent || '').trim()).filter(Boolean);
      return s[0] || null;
    }),
    状态信号: btns.map((b) => ({
      pressed: b.getAttribute('aria-pressed'), expanded: b.getAttribute('aria-expanded'),
      checked: b.getAttribute('aria-checked'), current: b.getAttribute('aria-current'),
      disabled: b.getAttribute('disabled') !== null,
    })),
  };
})()`;

/** 判据 2：elementFromPoint 阳性对照（函数 + 第二个参数 = 标准传参） */
const hitTest = ([px, py, wantId]) => {
  const el = document.elementFromPoint(px, py);
  if (!el) return { 命中: null, 是目标: false, 元素: '(elementFromPoint 返回 null)' };
  const node = el.closest('[data-node-id]');
  return {
    命中: node ? node.getAttribute('data-node-id') : null,
    是目标: node ? node.getAttribute('data-node-id') === wantId : false,
    元素: el.tagName + '.' + String(el.className || '').slice(0, 40),
  };
};

async function clearCanvas(page) {
  const before = (await page.evaluate(NODES)).length;
  if (!before) return { before, after: 0, 弹窗: '(本来就空)' };
  await page.mouse.move(40, 609);
  await page.waitForTimeout(500);
  await page.mouse.click(40, 609);
  await page.waitForTimeout(1400);
  // 清空画布有确认弹窗（正文「清空画布？…取 消 清 空」，M130 逐字核过）
  const 弹窗 = await page.evaluate(`(() => {
    const d = document.querySelector('[role="dialog"]');
    if (!d) return '没有弹窗';
    const t = (d.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 60);
    const btns = Array.from(d.querySelectorAll('button'));
    const go = btns.find((b) => (b.className || '').includes('primary')) || btns[btns.length - 1];
    if (go) go.click();
    return t;
  })()`);
  await page.waitForTimeout(1800);
  return { before, after: (await page.evaluate(NODES)).length, 弹窗 };
}

async function selectNode(page, n) {
  await page.mouse.click(800, 780);
  await page.waitForTimeout(700);
  const hit = await page.evaluate(hitTest, [n.x + n.w / 2, n.y + n.h / 2, n.id]);
  if (!hit.是目标) return { ok: false, hit };
  await page.mouse.click(n.x + n.w / 2, n.y + n.h / 2);
  await page.waitForTimeout(1500);
  return { ok: true, hit };
}

async function main() {
  const { chromium } = require(PW);
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    headless: true, viewport: { width: 1600, height: 950 }, args: ['--no-sandbox'],
  });
  const page = ctx.pages()[0] || (await ctx.newPage());
  page.setDefaultTimeout(25000);
  const rows = [];
  try {
    const target = process.argv[2];
    if (!target) {
      console.log('用法：node scripts/probe-toolbar-states.js <画布URL>');
      console.log('（必须显式给 URL —— 本脚本会清空画布，不能随便指向一个项目）');
      process.exitCode = 1;
      return;
    }
    await page.goto(target, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(4500);

    // 判据 3：先读出面板每一项的真实坐标
    await page.mouse.move(40, 345); await page.waitForTimeout(600);
    await page.mouse.click(40, 345);
    await page.waitForTimeout(1700);
    const items = await page.evaluate(READ_FLYOUT);
    if (!items) { console.log('[面板没打开，先确认画布页加载正常]'); return; }
    await page.keyboard.press('Escape');
    await page.waitForTimeout(800);
    console.log('添加节点面板的实测坐标：');
    items.forEach((i) => console.log('  ' + i.文字.padEnd(16) + '@' + i.x + ',' + i.y + ' ' + i.w + 'x' + i.h));

    for (const item of items) {
      if (item.文字 === '上传素材') continue;   // 会弹文件选择器，headless 下无法完成
      console.log('\n  【' + item.文字 + '】');
      const cl = await clearCanvas(page);
      console.log('      清空 ' + cl.before + ' → ' + cl.after + '（' + cl.弹窗 + '）');

      await page.mouse.move(40, 345); await page.waitForTimeout(600);
      await page.mouse.click(40, 345);
      await page.waitForTimeout(1700);
      const still = await page.evaluate(READ_FLYOUT);
      if (!still) { console.log('      面板没打开，作废'); continue; }
      const real = still.find((x) => x.文字 === item.文字);
      if (!real) { console.log('      面板里没有「' + item.文字 + '」，作废'); continue; }
      await page.mouse.click(real.x + real.w / 2, real.y + real.h / 2);
      await page.waitForTimeout(2200);
      await page.keyboard.press('Escape');
      await page.waitForTimeout(1000);

      const nodes = await page.evaluate(NODES);
      if (nodes.length !== 1) {
        console.log('      ★期望 1 个节点，实际 ' + nodes.length + ' 个 —— 作废');
        console.log('        （节点默认全部叠在画布中心，数目不对说明建错了，别硬读）');
        continue;
      }
      const n = nodes[0];
      console.log('      节点 ' + JSON.stringify(n.title) + ' @' + n.x + ',' + n.y + ' ' + n.w + 'x' + n.h);
      const sel = await selectNode(page, n);
      if (!sel.ok) { console.log('      ★阳性对照失败（那个点命中的是 ' + sel.hit.命中 + '），作废'); continue; }
      console.log('      阳性对照 OK（' + sel.hit.元素 + '）');

      const bar = await page.evaluate(READ_BAR);
      if (!bar) { console.log('      选中后无工具条'); continue; }
      const hasState = bar.状态信号.filter((s) => s.pressed !== null || s.expanded !== null || s.checked !== null || s.current !== null).length;
      rows.push({ 类型: item.文字, 按钮数: bar.n, 名称: bar.名称, 按钮文字: bar.按钮文字, 带状态信号: hasState });
      console.log('      按钮数=' + bar.n + '  带 aria 状态信号的=' + hasState + '/' + bar.n);
      console.log('      ' + bar.按钮文字.join(' / '));
    }

    console.log('\n\n' + '='.repeat(84));
    console.log('=== 汇总：各类型工具条（' + rows.length + ' 种类型）===');
    console.log('='.repeat(84));
    const seen = {};
    for (const r of rows) (seen[r.按钮数] = seen[r.按钮数] || []).push(r.类型);
    Object.keys(seen).map(Number).sort((a, b) => a - b).forEach((k) => console.log('  ' + String(k).padStart(2) + ' 个按钮：' + seen[k].join('、')));
    console.log('  共 ' + Object.keys(seen).length + ' 种长度');
    const totalState = rows.reduce((s, r) => s + r.带状态信号, 0);
    const totalBtn = rows.reduce((s, r) => s + r.按钮数, 0);
    console.log('  带 aria-pressed/expanded/checked/current 的按钮：' + totalState + ' / ' + totalBtn);
    console.log('\n  ⚠️ 不可逆按钮（' + Array.from(DESTRUCTIVE).join('、') + '）本脚本从不点击。');
    console.log('  ⚠️ 「上传素材」会弹文件选择器，headless 下无法完成，已跳过。');
    console.log('\n**提醒**：本脚本只给读数。而且它会清空画布，**只在一次性探针画布上跑**。');
  } catch (e) {
    console.error('\n[失败] ' + e.message);
    process.exitCode = 1;
  } finally {
    try { await ctx.close(); } catch (_) {}
    setTimeout(() => process.exit(process.exitCode || 0), 300);
  }
}

main();
