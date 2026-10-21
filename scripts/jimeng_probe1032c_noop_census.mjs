/**
 * 1032-②b-c 运行时探针 v3：**场景化**逐个真点，画布上每一个可点元素到底有没有发生事。
 *
 * ⭐⭐⭐⭐⭐ **为什么必须是「场景化」的**
 *   1032-① 的静态审计只枚举了**初始页面**的 36 个可点元素 ⇒ ⇒ 而糊弄最严重的
 *   全在**弹层里**（初始不在 DOM）⇒ ⇒ 所以本探针的做法是：
 *   **先开层 / 先选中节点 / 再枚举 / 再逐个点**。
 *
 * ⭐⭐⭐⭐⭐ **这一批要抓的那一类糊弄：NOOP —— 有 onClick，但函数体是空的**
 *   静态门把它算成 WIRED ⇒ ⇒ **静态门看不见这一类** ⇒ ⇒ 只有运行时能抓。
 *   ⭐ 而「点了只弹一句 toast」也是同一族（FAKE_SUCCESS）⇒ ⇒ 一并量出来。
 *
 * ⭐⭐⭐⭐⭐ **量法：逐个按钮量「某个可观察的东西变了」**
 *   ① 点击前挂一个 `MutationObserver`（attributes + childList + subtree）⇒ ⇒ 数**变动次数**
 *   ② 点击前后各取一次**结构指纹**（节点数 / 可见按钮数 / dialog 数 / listbox 数 /
 *      可输入元素数 / toast 数 / 正文长度）⇒ ⇒ 取**差集**
 *   ③ 分类：
 *      - `NOOP`       ⇒ **零变动、零差集** ⇒ 「点了什么也没发生」
 *      - `TOAST_ONLY` ⇒ **只多了一个 toast** ⇒ 「点了一下，弹了句话，什么也没变」
 *      - `REAL`       ⇒ 其它 ⇒ 「有可观察的状态变化」
 *      - `NAVIGATED`  ⇒ 点了之后页面跳走了
 *      - `ERROR`      ⇒ 点了之后抛了未捕获异常
 *
 * ⭐⭐⭐⭐⭐⭐⭐ **v2 的第一版为什么被判「假零」**（这一条是本探针自己的教训）
 *   第一版用 Playwright 的 `locator.click()`（带可操作性检查）⇒ ⇒ 某个点击打开了
 *   一层遮罩 ⇒ ⇒ **后面 178 个按钮全被盖住** ⇒ ⇒ 点击全部超时
 *   ⇒ ⇒ 而分类里没有「点击失败」这一档 ⇒ ⇒ ⇒ **它们既不是 NOOP 也不是 REAL**
 *   ⇒ ⇒ ⇒ 普查于是报「NOOP 0 个」—— **一个只点了 30/208 就敢下的结论**
 *   ⇒ ⇒⇒⇒ **「0 个 NOOP」在这种读数下是假零，比不报更坏。**
 *   ⇒ ⇒⇒⇒ 处置三条：① **点之前重载到干净态**（每个按钮一次）；
 *   ② **用 DOM 派发点击**（绕开命中测试 —— 这里要验的是「这个 handler 有没有做事」，
 *      不是「用户能不能点到」，后者由 ②b-1 的真实鼠标探针管）；
 *   ③ **把「点击失败数」做成读数**，并由契约门断言它为 0。
 *
 * ⚠️ 纪律：
 *   · 跑在**本地复刻**上（localhost:4317），不碰源站
 *   · **绝不点生成 / 发送 / 购买 / 充值**（复刻侧也是跳过并记录原因）
 *   · **产物里不许出现随机量**（节点 id / 时间戳 / 耗时）⇒ ⇒ 节点 id 不进产物
 */
import pw from '/Users/yangjiefeng/node_modules/playwright/index.js';
import { writeFileSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const { chromium } = pw;

const URL = 'http://localhost:4317/jimeng/canvas/demo';
const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, '..');
const OUT =
  process.env.JIMENG_C4_JSON ||
  resolve(REPO_ROOT, 'docs/research/jimeng-canvas/inputs/noop-census-1032c.json');
mkdirSync(dirname(OUT), { recursive: true });

/** ⭐ 绝不点这一族（复刻侧也守：生成 / 发送 / 购买 / 充值）
 *
 *  ⚠️⚠️ **第一版这条正则太粗**（`/(生成|发送|购买|充值)/`）⇒ ⇒ 它把
 *  「生成模式: 全能参考」「选择视频生成时长: 4s」「创作类型: 音频生成」
 * 「音频生成: 全能配音」这些**参数下拉**也跳过了 ⇒ ⇒ **它们根本没被量**
 * ⇒ ⇒ ⇒ **量程不足 ⇒ 假否定**（它们里若藏着 NOOP，普查看不见）
 * ⇒ ⇒⇒ 处置：只跳**动作**按钮（「生成」/「发送」本身）与付费词，
 *         参数下拉**一律要量**。 */
const SKIP_RE = /^生成$|^发送$|生成历史|购买|充值|支付|下单|续费/;

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ acceptDownloads: true });
let pageErrors = [];
page.on('pageerror', (e) => pageErrors.push(String(e).slice(0, 160)));
// ⭐ 文件选择器：无人接管时它会挂住 ⇒ 统一取消
//   ⚠️ 这版 Playwright 的 FileChooser **没有 `cancel()`** ⇒ ⇒ 用 `setFiles([])` 取消
//   （第一版写了 `fc.cancel()` ⇒ ⇒ 点「上传」那枚直接抛 `fc.cancel is not a function`
//     ⇒ ⇒ 整轮普查崩掉 ⇒ ⇒ **「仪器崩了」必须与「产品坏了」分开** —— 退出码 2）
page.on('filechooser', (fc) => {
  try {
    const p = fc.setFiles([]);
    if (p && typeof p.catch === 'function') p.catch(() => {});
  } catch (e) { /* 取消失败就算了 */ }
});

const _writeCrash = (msg) => {
  try {
    writeFileSync(OUT, JSON.stringify({
      generated_by: 'jimeng_probe1032c_noop_census.mjs',
      note: '⭐ 本轮**仪器故障**（不是产品坏了）—— 判据没跑成。',
      crashed: true,
      error: String(msg).slice(0, 300),
      scenarios: {},
      n_buttons: 0,
      n_noop: 0,
      n_click_failed: 0,
    }, null, 1));
  } catch (e) { /* 写不出去就算了 */ }
  console.log('INSTRUMENT_CRASH :: ' + String(msg).slice(0, 200));
  process.exit(2);
};
process.on('uncaughtException', (e) => _writeCrash(e));
process.on('unhandledRejection', (e) => _writeCrash(e));

/** 打开页面并等到画布真的挂上（不睡固定时长） */
async function loadCanvas() {
  for (let _try = 1; _try <= 3; _try++) {
    try {
      await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 120000 });
      await page.waitForSelector('.react-flow__node', { timeout: 25000 });
      await page.waitForTimeout(600);
      return true;
    } catch (e) {
      console.log('loadCanvas 第 %d 次失败: ' + String(e).slice(0, 140));
      await page.waitForTimeout(3000);
    }
  }
  return false;
}
if (!(await loadCanvas())) _writeCrash('画布连续 3 次没挂上');

const out = {
  generated_by: 'jimeng_probe1032c_noop_census.mjs',
  note: '⭐ 场景化逐个真点；分类 NOOP / TOAST_ONLY / REAL / NAVIGATED / ERROR；'
    + '每个按钮前重载到干净态并用 DOM 派发点击。',
  scenarios: {},
};
let nButtons = 0;
let nNoop = 0;
let nClickFailed = 0;
let nToastOnly = 0;
/** 全局去重：(名称, 区域) ⇒ 只量一次 */
const measured = new Set();

const FINGERPRINT = () =>
  page.evaluate(() => {
    const vis = (el) => {
      const r = el.getBoundingClientRect();
      if (r.width <= 0 || r.height <= 0) return false;
      const cs = getComputedStyle(el);
      return cs.visibility !== 'hidden' && cs.display !== 'none';
    };
    let toast = 0;
    document.querySelectorAll('[role="status"]').forEach((el) => {
      if ((el.className || '').toString().includes('z-[300]')) toast++;
    });
    let visibleButtons = 0;
    document.querySelectorAll('button, [role="button"]').forEach((b) => {
      if (vis(b)) visibleButtons++;
    });
    return {
      nodes: document.querySelectorAll('.react-flow__node').length,
      visible_buttons: visibleButtons,
      dialogs: document.querySelectorAll('[role="dialog"]').length,
      listboxes: document.querySelectorAll('[role="listbox"]').length,
      inputs: document.querySelectorAll('input, textarea, [contenteditable="true"]').length,
      toast,
      body_len: document.body.innerText.length,
    };
  });

/** 枚举当前可见的可点元素（按 DOM 顺序） */
const enumerateButtons = () =>
  page.evaluate(() => {
    const vis = (el) => {
      const r = el.getBoundingClientRect();
      if (r.width <= 0 || r.height <= 0) return false;
      const cs = getComputedStyle(el);
      return cs.visibility !== 'hidden' && cs.display !== 'none';
    };
    const rows = [];
    document.querySelectorAll('button, [role="button"]').forEach((b) => {
      if (!vis(b)) return;
      const name = (b.getAttribute('aria-label') || b.innerText || '')
        .trim().replace(/\s+/g, ' ').slice(0, 48);
      let where = 'other';
      const node = b.closest('.react-flow__node');
      if (node) {
        const m = node.className.match(/react-flow__node-([a-z]+)/);
        where = 'node:' + ((m && m[1]) || '?');
      } else if (b.closest('header, [class*="header"], [class*="topbar"]')) where = 'top';
      else if (b.closest('[class*="dock"]')) where = 'dock';
      else if (b.closest('[class*="rail"], nav')) where = 'rail';
      rows.push({
        name,
        where,
        ordinal: 0, // 同名同区的出现序号（后面算）
        disabled: b.disabled === true || b.getAttribute('aria-disabled') === 'true',
      });
    });
    const seen = new Map();
    for (const r of rows) {
      const k = r.name + '|' + r.where;
      const n = (seen.get(k) || 0);
      r.ordinal = n;
      seen.set(k, n + 1);
    }
    return rows;
  });

/** ⭐ DOM 派发点击：绕开命中测试（验的是「handler 有没有做事」） */
async function dispatchClick(name, where, ordinal) {
  return page.evaluate(
    ([nm, wh, od]) => {
      const vis = (el) => {
        const r = el.getBoundingClientRect();
        if (r.width <= 0 || r.height <= 0) return false;
        const cs = getComputedStyle(el);
        return cs.visibility !== 'hidden' && cs.display !== 'none';
      };
      const rows = [];
      document.querySelectorAll('button, [role="button"]').forEach((b) => {
        if (!vis(b)) return;
        const n = (b.getAttribute('aria-label') || b.innerText || '')
          .trim().replace(/\s+/g, ' ').slice(0, 48);
        let w = 'other';
        const node = b.closest('.react-flow__node');
        if (node) {
          const m = node.className.match(/react-flow__node-([a-z]+)/);
          w = 'node:' + ((m && m[1]) || '?');
        } else if (b.closest('header, [class*="header"], [class*="topbar"]')) w = 'top';
        else if (b.closest('[class*="dock"]')) w = 'dock';
        else if (b.closest('[class*="rail"], nav')) w = 'rail';
        rows.push({ b, n, w });
      });
      const hit = rows.filter((r) => r.n === nm && r.w === wh)[od];
      if (!hit) return 'NOT_FOUND';
      hit.b.click();
      return 'CLICKED';
    },
    [name, where, ordinal]
  );
}

const selectLast = async (kind) => {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(200);
  const n = page.locator('.react-flow__node-' + kind);
  const c = await n.count();
  if (!c) return false;
  await n.nth(c - 1).click({ position: { x: 6, y: 6 } });
  await page.waitForTimeout(700);
  return true;
};

const SCENARIOS = [
  { id: 'base', kind: null },
  { id: 'video', kind: 'video' },
  { id: 'text', kind: 'text' },
  { id: 'audio', kind: 'audio' },
  { id: 'timeline', kind: 'timeline' },
];

for (const sc of SCENARIOS) {
  console.log('\n=== 场景 ' + sc.id + ' ===');
  if (!(await loadCanvas())) _writeCrash('场景 ' + sc.id + '：画布没挂上');
  if (sc.kind) {
    const ok = await selectLast(sc.kind);
    if (!ok) {
      out.scenarios[sc.id] = { available: false, note: '画布上没有这种节点', buttons: [] };
      console.log('  画布上没有这种节点 ⇒ 记为 not_applicable');
      continue;
    }
  }
  const list = await enumerateButtons();
  console.log('  可点元素 ' + list.length + ' 个');
  const rows = [];
  for (const b of list) {
    const key = b.name + '|' + b.where + '#' + b.ordinal;
    if (measured.has(key)) continue;          // ⭐ 全局去重
    measured.add(key);
    nButtons++;
    const label = b.name || '(无名字)';
    if (b.disabled) {
      rows.push({ name: label, where: b.where, ordinal: b.ordinal, cls: 'DISABLED', mutations: 0, deltas: {} });
      console.log('  [DISABLED ] ' + label);
      continue;
    }
    if (SKIP_RE.test(label)) {
      rows.push({ name: label, where: b.where, ordinal: b.ordinal, cls: 'SKIPPED_BY_POLICY', mutations: 0, deltas: {} });
      console.log('  [SKIPPED  ] ' + label);
      continue;
    }
    // ⭐ 每个按钮都从**干净态**重来（上一枚点出来的遮罩不能污染下一枚）
    if (!(await loadCanvas())) _writeCrash('重载失败');
    if (sc.kind) {
      const ok = await selectLast(sc.kind);
      if (!ok) { rows.push({ name: label, where: b.where, ordinal: b.ordinal, cls: 'SCENARIO_GONE', mutations: 0, deltas: {} }); continue; }
    }
    const errsBefore = pageErrors.length;
    const before = await FINGERPRINT();
    const urlBefore = page.url();
    await page.evaluate(() => {
      window.__mut = 0;
      window.__mo = new MutationObserver((recs) => { window.__mut += recs.length; });
      window.__mo.observe(document.body, {
        attributes: true, childList: true, subtree: true, characterData: true,
      });
    });
    let how = 'NONE';
    try {
      how = await dispatchClick(b.name, b.where, b.ordinal);
    } catch (e) {
      how = 'THREW';
    }
    await page.waitForTimeout(600);
    const after = await FINGERPRINT();
    const mutations = await page.evaluate(() => {
      const n = window.__mut;
      if (window.__mo) window.__mo.disconnect();
      return n;
    });
    const urlAfter = page.url();
    const deltas = {};
    for (const k of Object.keys(after)) {
      if (after[k] !== before[k]) deltas[k] = [before[k], after[k]];
    }
    let cls;
    if (how === 'NOT_FOUND' || how === 'THREW') cls = 'CLICK_FAILED';
    else if (urlAfter !== urlBefore) cls = 'NAVIGATED';
    else if (pageErrors.length > errsBefore) cls = 'ERROR';
    else if (mutations === 0 && Object.keys(deltas).length === 0) cls = 'NOOP';
    else if (deltas.toast && Object.keys(deltas).filter((k) => k !== 'toast' && k !== 'body_len').length === 0) cls = 'TOAST_ONLY';
    else cls = 'REAL';
    if (cls === 'NOOP') nNoop++;
    if (cls === 'TOAST_ONLY') nToastOnly++;
    if (cls === 'CLICK_FAILED' || cls === 'ERROR') nClickFailed++;
    rows.push({
      name: label, where: b.where, ordinal: b.ordinal, cls, mutations, deltas,
      click_result: how,
    });
    console.log('  [' + cls.padEnd(16) + '] ' + label + '  (' + how + ')');
  }
  out.scenarios[sc.id] = { available: true, n_buttons: rows.length, buttons: rows };
}

out.n_buttons = nButtons;
out.n_noop = nNoop;
out.n_toast_only = nToastOnly;
out.n_click_failed = nClickFailed;
out.n_by_class = {};
for (const sc of Object.values(out.scenarios)) {
  for (const r of sc.buttons || []) {
    out.n_by_class[r.cls] = (out.n_by_class[r.cls] || 0) + 1;
  }
}
out.pageerrors = pageErrors;

writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log('\n按钮合计 ' + nButtons + ' 个；分类 ' + JSON.stringify(out.n_by_class));
console.log('NOOP=' + nNoop + ' TOAST_ONLY=' + nToastOnly + ' CLICK_FAILED/ERROR=' + nClickFailed);
console.log('写入', OUT);
await browser.close();
process.exit(0);
