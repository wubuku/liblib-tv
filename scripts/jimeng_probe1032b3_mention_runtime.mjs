/**
 * 1032-②b-3 运行时探针：重拍面板 / 视频编辑态里那两枚「提及主体」@ 钮，
 * 点了**到底有没有发生事**。
 *
 * ⭐⭐⭐⭐⭐ **这一批修的糊弄形态**：两枚 @ 钮此前**整枚没有 onClick**
 *   （1032 静态门抓得到 ⇒ DEAD_NO_HANDLER）。
 *   ⇒ 但**光看「有 onClick」不够** —— 那只是把死按钮变成「点了没反应」。
 *   ⇒ 所以本门验的是「**某个可观察的东西变了**」。
 *
 * ⭐⭐⭐⭐⭐ **判据（每条都是可观察的）**：
 *   1. 点「提及主体」⇒ ⇒ **面板真的出现**（`[data-testid="mention-panel"]`）
 *   2. 面板是一级 listbox，aria 逐字 **`可能@的内容`**（SOURCE_FACT 批次 33）
 *   3. 一级有 **4 个 role=option**：主体 / 图片 / 视频 / 音频
 *      （SOURCE_FACT 批次 34：视频宿主 ⇒ 4 类）
 *   4. 点某一级类别 ⇒ ⇒ **二级子菜单出现**（`[data-testid="mention-submenu"]`）
 *   5. 二级列出**有可用资源**的节点；**没有资源时逐字 `暂无相关节点`**
 *      （SOURCE_FACT 批次 33 的空态 / 批次 114 的「只列有资源的」）
 *   6. 选中一条 ⇒ ⇒ **提示词行多出一个引用 chip**（可观察的 DOM 变化）
 *   7. ⭐ **负控**：**没有主体节点**时，「主体」这一级的二级**必须**是
 *      `暂无相关节点` ⇒ ⇒ 证明「有候选才列」这条规则真的在生效
 *   8. ⭐ **负控**：面板开着时按 Esc ⇒ ⇒ 面板**关掉**、提示词**保留**
 *      （SOURCE_FACT 手册「退出路径」表：Esc → 面板关、提示词保留）
 *
 * 纪律：
 *   · 跑在**本地复刻**上（localhost:4317），不碰源站，不消耗任何积分
 *   · **绝不点生成/发送/购买/充值**
 *   · **产物里不许出现随机量**（节点 id / 时间戳 / 耗时）
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
  process.env.JIMENG_B3_JSON ||
  resolve(REPO_ROOT, 'docs/research/jimeng-canvas/inputs/mention-runtime-1032b3.json');
mkdirSync(dirname(OUT), { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const pageErrors = [];
page.on('pageerror', (e) => pageErrors.push(String(e).slice(0, 200)));

// ⭐⭐⭐⭐⭐ **仪器故障与「数据有问题」必须用不同的退出码**（本仓纪律：
//   「门红了」和「探针崩了」必须有不同的退出码）⇒ ⇒ 这里：**检查失败 = 1，仪器崩了 = 2**。
// ⭐⭐⭐⭐⭐ 而「仪器崩了」**必须写产物** —— 不写的话，契约门会去读**上一轮留下的旧读数**
//   ⇒ ⇒ 那就把「本轮没跑」伪装成「本轮跑过了」⇒ ⇒ 门报绿 ⇒ ⇒ **假绿**。
const _writeCrash = (msg) => {
  try {
    writeFileSync(OUT, JSON.stringify({
      generated_by: 'jimeng_probe1032b3_mention_runtime.mjs',
      note: '⭐ 本轮**仪器故障**（不是产品坏了）—— 判据没跑成。',
      crashed: true,
      error: String(msg).slice(0, 300),
      checks: {},
      n_checks: 0,
      n_failed: 0,
      pageerrors: [],
    }, null, 1));
  } catch (e) { /* 写不出去就算了 */ }
  console.log('INSTRUMENT_CRASH :: ' + String(msg).slice(0, 200));
  process.exit(2);
};
process.on('uncaughtException', (e) => _writeCrash(e));
process.on('unhandledRejection', (e) => _writeCrash(e));

// ⭐⭐⭐⭐⭐ goto **要重试**：1015 会串行跑二十多个浏览器探针，dev server 在负载下
//   首次编译可能超过 60s ⇒ ⇒ 一次超时就抛未捕获 rejection ⇒ ⇒ 栈进 stderr
//   ⇒ ⇒ 契约门把 `probe_run` 写成 `rc=1 stderr=…` ⇒ ⇒ **产物多出 200 多字节**
//   ⇒ ⇒ ⇒ **可复现性门立刻报 drift** ⇒ ⇒ 而真相是「仪器抖了一下」，不是「产品变了」。
let _gotoOk = false;
for (let _try = 1; _try <= 3 && !_gotoOk; _try++) {
  try {
    await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 120000 });
    _gotoOk = true;
  } catch (e) {
    console.log('goto 第 %d 次失败: ' + String(e).slice(0, 160));
    await page.waitForTimeout(3000);
  }
}
if (!_gotoOk) _writeCrash('goto 连续 3 次失败');
await page.waitForTimeout(6000);

const out = {
  generated_by: 'jimeng_probe1032b3_mention_runtime.mjs',
  note:
    '⭐ 判据是「某个可观察的东西变了」；负控验「不该发生时**不**发生」。' +
    '面板规格 = SOURCE_FACT 手册批次 33/34/113/114。',
  checks: {},
};
const record = (name, value) => {
  out.checks[name] = value;
  console.log((value.ok ? '  OK  ' : '  FAIL') + '  ' + name + ' :: ' + JSON.stringify(value));
};

const nodeCount = () =>
  page.evaluate(() => document.querySelectorAll('.react-flow__node').length);

/** 在某个容器内找「可见的」某 aria-label 按钮；找不到再退回全局。
 *  ⚠️⚠️ **别把 scope 限死在 `.react-flow__node-video`**：
 *   重拍/编辑态的面板挂在 **`.react-flow__node-toolbar`** 里（xyflow 的
 *   NodeToolbar 是节点**兄弟**而不是后代）⇒ ⇒ 限定在节点内 ⇒ **一个都找不到**。
 *   ⇒ 这里用「全局找第一个可见的」就够（同一时刻只有一处重拍/编辑态）。 */
const visibleBtnIn = async (scopeSel, aria) => {
  if (scopeSel) {
    const scope = page.locator(scopeSel);
    const c = await scope.count();
    for (let i = 0; i < c; i++) {
      const n = scope.nth(i).locator('button[aria-label="' + aria + '"]');
      const k = await n.count();
      for (let j = 0; j < k; j++) {
        if (await n.nth(j).isVisible()) return n.nth(j);
      }
    }
  }
  const g = page.locator('button[aria-label="' + aria + '"]');
  const gc = await g.count();
  for (let i = 0; i < gc; i++) {
    if (await g.nth(i).isVisible()) return g.nth(i);
  }
  return null;
};

const clickSafe = async (loc) => {
  if (!loc) return false;
  try {
    await loc.click({ timeout: 12000 });
    await page.waitForTimeout(700);
    return true;
  } catch (e) {
    // ⭐⭐⭐ **先问「它是不是其实已经生效了」**，再决定要不要重试。
    //   为什么必须先问：某些点击**第一次就成功了**，但 Playwright 随后
    //   因为**元素被卸载**（例如选中候选 ⇒ 面板自动收起 ⇒ 元素从 DOM 消失）
    //   而**判定这次 click 失败** ⇒ ⇒ 兜底重试时元素已不存在
    //   ⇒ ⇒ `evaluate` 一直等到超时 ⇒ ⇒ 报「没点上」
    //   ⇒ ⇒ **真实结果（点击已生效）被报成了失败**。
    //   ⇒ ⇒ 判据句柄：先量「这个动作**应该**造成的可观察变化」。
    const stillThere = await loc
      .count()
      .then((c) => c > 0)
      .catch(() => false);
    if (!stillThere) {
      // 元素不在了 ⇒ 多半是「点完就卸载」⇒ 视为已生效
      await page.waitForTimeout(700);
      return true;
    }
    // 元素还在 ⇒ 确实没点上 ⇒ 改用 DOM 派发（绕开「元素必须稳定」检查）
    try {
      await loc.evaluate((el) => el.click());
      await page.waitForTimeout(700);
      return true;
    } catch (e2) {
      return false;
    }
  }
};

const count = (sel) => page.evaluate((s) => document.querySelectorAll(s).length, sel);
const visible = (sel) =>
  page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) return false;
    const b = el.getBoundingClientRect();
    return b.width > 0 && b.height > 0;
  }, sel);

const PANEL_EL = '[data-testid="mention-panel"]';
const SUBMENU_EL = '[data-testid="mention-submenu"]';

// ── 0) 造一个**有资源的图片节点**（左栏上传一张图 ⇒ 落成带 poster 的图片节点）
// ⭐⭐⭐ **为什么必须上传，不能只点左栏「图片」**：
//   左栏「图片」插入的是**空图片节点**（`data` 里**没有 poster**）
//   ⇒ ⇒ 按源站规则「只列有可用资源的节点」（批次 114）⇒ 它**不该**被列出
//   ⇒ ⇒ 若门只点「图片」再去看二级，就只能读到「暂无相关节点」
//   ⇒ ⇒ 那是**判据样本选错**，不是产品坏了。
{
  const before = await nodeCount();
  // 1x1 PNG（本地内联，不读用户媒体）
  const PNG_1PX = Buffer.from(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
    'base64'
  );
  const input = page.locator('[data-testid="rail-upload-input"]');
  const nInput = await input.count();
  if (nInput) {
    await input.first().setInputFiles({
      name: 'mention-probe.png',
      mimeType: 'image/png',
      buffer: PNG_1PX,
    });
    await page.waitForTimeout(1200);
  }
  const after = await nodeCount();
  record('image_node_with_resource_inserted', {
    ok: nInput > 0 && after === before + 1,
    input_found: nInput > 0,
    before,
    after,
  });
}

// ── 1) 造一个**主体节点**（左栏「主体」入口）⇒ 用来验「主体」这一级
{
  const before = await nodeCount();
  const rail = page.locator('button[aria-label="主体"]');
  let clicked = false;
  if (await rail.count()) clicked = await clickSafe(rail.first());
  await page.waitForTimeout(600);
  const after = await nodeCount();
  record('subject_node_inserted', { ok: clicked && after === before + 1, before, after });
}

// ── 2) 选中「有资源的视频节点」⇒ 进重拍态 ─────────────────────────
// ⭐⭐⭐ **判据锚点**：用 `[data-jimeng-video-has-media]`（1032-②b-3 新加，
//   直接反映 `d.hasMedia`）来挑「有资源的」那个视频节点。
//   ⚠️⚠️ **不要按「找 `<video>` 元素」定位** —— 复刻的视频节点里**没有** `<video>`
//   （媒体卡是背景图）⇒ ⇒ 那样定位 ⇒ 永远挑不到节点 ⇒ ⇒ 门恒红
//   ⇒ ⇒ 这正是「量程不够 ⇒ 假否定」的形态。
const enterRepaint = async () => {
  const vids = page.locator('.react-flow__node-video:has([data-jimeng-video-has-media])');
  const n = await vids.count();
  if (!n) return false;
  for (let i = 0; i < n; i++) {
    const cand = vids.nth(i);
    await cand.click({ position: { x: 8, y: 8 } });
    await page.waitForTimeout(900);
    // ⭐⭐⭐ **按文本定位，不按 aria-label** ——
    //   复刻的工具条条目**没有 aria-label**（可访问名来自文案「局部重拍」）
    //   ⇒ ⇒ 按 `button[aria-label="局部重拍"]` 找 ⇒ ⇒ **一个都找不到**
    //   ⇒ ⇒ 于是「进不去重拍态」⇒ ⇒ 后面每一条判据连锁红。
    const tb = page.locator('button', { hasText: '局部重拍' });
    if (await tb.count()) {
      await tb.first().click({ timeout: 12000 });
      await page.waitForTimeout(900);
      return true;
    }
  }
  return false;
};

const inRepaint = await enterRepaint();
record('entered_repaint_mode', { ok: inRepaint });

// ── 3) 点「提及主体」⇒ 面板真的出现 ────────────────────────────────
{
  const btn = await visibleBtnIn('.react-flow__node-video', '提及主体');
  const clicked = await clickSafe(btn);
  const n = await count(PANEL_EL);
  const vis = await visible(PANEL_EL);
  record('mention_panel_opens', {
    ok: inRepaint && clicked && n === 1 && vis,
    entered: inRepaint,
    clicked,
    panel_count: n,
    panel_visible: vis,
  });
}

// ── 4) 面板是一级 listbox，aria 逐字「可能@的内容」─────────────────
{
  const info = await page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) return null;
    return {
      role: el.getAttribute('role') || '',
      aria: el.getAttribute('aria-label') || '',
      n_options: el.querySelectorAll('[role="option"]').length,
    };
  }, PANEL_EL);
  record('mention_panel_is_listbox_may_at_content', {
    ok: !!info && info.role === 'listbox' && info.aria === '可能@的内容',
    role: info ? info.role : null,
    aria: info ? info.aria : null,
    n_options: info ? info.n_options : -1,
  });
}

// ── 5) 一级有 4 个 option：主体 / 图片 / 视频 / 音频 ────────────────
{
  const labels = await page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) return [];
    return [...el.querySelectorAll('[role="option"]')].map((o) =>
      (o.getAttribute('aria-label') || '').replace('可能@的内容: ', '')
    );
  }, PANEL_EL);
  const want = ['主体', '图片', '视频', '音频'];
  const ok =
    labels.length === 4 && want.every((w) => labels.includes(w));
  record('mention_panel_has_four_categories', {
    ok,
    labels,
    expected: want,
  });
}

// ── 6) 点「视频」一级 ⇒ 二级子菜单出现，且列出**有资源**的视频节点 ──
//    ⭐⭐ 为什么用「视频」而不是「图片」做正向判据：
//   复刻侧**左栏上传一律落视频节点**（`addLocalUpload` 恒 `type:"video"`、
//   `hasMedia:true`）⇒ ⇒ 画布上**没有**图片节点 ⇒ ⇒ 「图片」级必然是空态。
//   ⇒ ⇒ 用「视频」级做正向判据，才真的验到「二级列出了有资源的节点」。
//    ⭐⭐ **顺序纪律**：这一条必须是**紧接「面板打开」之后的第一条下钻** ——
//   中间若插别的下钻 ⇒ ⇒ 浮层布局会回流 ⇒ ⇒ 随后的 click 可能落在旧位置上
//   ⇒ ⇒ 判据变成「量错了」而不是「产品坏了」。
{
  const cat = page.locator(PANEL_EL + ' [role="option"][aria-label="可能@的内容: 视频"]');
  const clicked = await clickSafe(cat);
  const n = await count(SUBMENU_EL);
  const vis = await visible(SUBMENU_EL);
  // 二级里列出的视频节点数
  const nItems = await page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) return -1;
    return el.querySelectorAll('[role="option"]').length;
  }, SUBMENU_EL);
  const emptyText = await page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) return '';
    const st = el.querySelector('[role="status"]');
    return st ? (st.innerText || '').trim() : '';
  }, SUBMENU_EL);
  record('mention_submenu_opens_with_resource_nodes', {
    ok: clicked && n === 1 && vis && nItems >= 1 && emptyText === '',
    clicked,
    submenu_count: n,
    submenu_visible: vis,
    n_items: nItems,
    empty_text: emptyText,
  });
}

// ── 7) 选中一条 ⇒ 提示词行多出一个引用 chip ────────────────────────
{
  const before = await count('[data-testid="repaint-mention-chip"]');
  // ⭐⭐ 用 **DOM 派发**（`el.click()`）而不是 Playwright 的 click：
  //   选中候选 ⇒ 面板**自动收起** ⇒ 元素从 DOM 卸载 ⇒ Playwright 的 click
  //   会在「动作已生效」之后**判定失败**（元素已消失 ⇒ 无法复查）
  //   ⇒ ⇒ 报「没点上」⇒ ⇒ **真实结果被报成了失败**。
  //   ⇒ ⇒ `el.click()` 是 React 能听见的**真事件**（走合成事件系统），
  //   不是 `dispatchEvent` 那种假事件。
  const clicked = await page.evaluate((s) => {
    const o = document.querySelector(s + ' [role="option"]');
    if (!o) return false;
    o.click();
    return true;
  }, SUBMENU_EL);
  await page.waitForTimeout(700);
  const after = await count('[data-testid="repaint-mention-chip"]');
  const panelAfter = await count(PANEL_EL);
  record('picking_candidate_inserts_chip', {
    ok: clicked && after === before + 1 && panelAfter === 0,
    clicked,
    chips_before: before,
    chips_after: after,
    panel_closed_after_pick: panelAfter === 0,
  });
}

// ── 8) 负控：点「主体」一级 ⇒ 二级是**空态**（那个主体节点 `imported` 为空
//     ⇒ 按「只列有可用资源的节点」规则（批次 114）⇒ 它不该被列出）
//     ⭐ 这是**负控**：证明「有资源才列」这条规则真的在生效。
{
  // 重新打开面板（上一条选完候选后自动收起了）
  const btn = await visibleBtnIn('.react-flow__node-video', '提及主体');
  await clickSafe(btn);
  await page.waitForTimeout(500);
  const cat = page.locator(PANEL_EL + ' [role="option"][aria-label="可能@的内容: 主体"]');
  const clicked = await clickSafe(cat);
  await page.waitForTimeout(500);
  const n = await count(SUBMENU_EL);
  const emptyText = await page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) return '';
    const st = el.querySelector('[role="status"]');
    return st ? (st.innerText || '').trim() : '';
  }, SUBMENU_EL);
  const nItems = await page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) return -1;
    return el.querySelectorAll('[role="option"]').length;
  }, SUBMENU_EL);
  record('subject_category_empty_when_no_resource', {
    ok: clicked && n === 1 && emptyText === '暂无相关节点' && nItems === 0,
    clicked,
    submenu_count: n,
    empty_text: emptyText,
    n_items: nItems,
  });
}

// ── 9) 负控：Esc ⇒ 面板关掉、提示词保留 ────────────────────────────
//    ⭐ SOURCE_FACT 手册「退出路径」表：`Esc` → 面板关、**提示词保留**。
//    ⚠️ 此刻面板是**关着的**（第 8 条选完候选后自动收起）⇒ ⇒ 先重新打开。
{
  // ⚠️ 面板此刻**可能已经开着**（上一条下钻到「主体」后没关）
  //   ⇒ ⇒ 先量，再决定要不要点 @ 钮（点 @ 钮是 toggle ⇒ 点多了会**关掉**它）
  let panelBefore = await count(PANEL_EL);
  if (panelBefore === 0) {
    const btn = await visibleBtnIn('.react-flow__node-video', '提及主体');
    await clickSafe(btn);
    await page.waitForTimeout(500);
    panelBefore = await count(PANEL_EL);
  }
  // 先在提示词里打一个字 ⇒ 用来验「Esc 不清空提示词」
  // ⚠️⚠️ **不能用 `fill()`**：重拍面板挂在 NodeToolbar 里，而**视频节点的
  //   `<img>`（海报）盖在它上面** ⇒ ⇒ Playwright 的命中测试判定
  //   「subtree intercepts pointer events」⇒ ⇒ fill 超时 ⇒ ⇒ 整条判据崩。
  //   ⇒ ⇒ 改用「原生 setter + input 事件」：它走 React 的 onChange，
  //      且**不依赖命中测试**（这不是伪造 —— 值真的进了 state）。
  const setPrompt = async (text) => {
    return page.evaluate((t) => {
      const el = document.querySelector('input[placeholder="描述你如何调整这一片段"]');
      if (!el) return false;
      const setter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype,
        'value'
      ).set;
      setter.call(el, t);
      el.dispatchEvent(new Event('input', { bubbles: true }));
      return true;
    }, text);
  };
  const typed = await setPrompt('保留我这个提示词');
  await page.waitForTimeout(400);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(600);
  const panelAfter = await count(PANEL_EL);
  // 提示词是否保留：重拍面板的提示词 input 的值
  const promptVal = await page.evaluate(() => {
    const el = document.querySelector('input[placeholder="描述你如何调整这一片段"]');
    return el ? el.value : null;
  });
  record('escape_closes_panel_and_keeps_prompt', {
    ok:
      typed &&
      panelBefore === 1 &&
      panelAfter === 0 &&
      promptVal === '保留我这个提示词',
    typed,
    panel_before: panelBefore,
    panel_after: panelAfter,
    prompt_value: promptVal,
  });
}

// ── 9) 视频编辑态那一枚 @ 钮也是活的 ──────────────────────────────
{
  // 退出重拍态，进视频编辑态
  await page.keyboard.press('Escape');
  await page.waitForTimeout(700);
  const vids = page.locator('.react-flow__node-video:has([data-jimeng-video-has-media])');
  const n = await vids.count();
  let entered = false;
  for (let i = 0; i < n; i++) {
    const cand = vids.nth(i);
    await cand.click({ position: { x: 8, y: 8 } });
    await page.waitForTimeout(900);
    // ⭐ **按文本定位**（工具条条目没有 aria-label）
    const tb = page.locator('button', { hasText: '视频编辑' });
    if (await tb.count()) {
      await tb.first().click({ timeout: 12000 });
      await page.waitForTimeout(900);
      entered = true;
      break;
    }
  }
  const btn = await visibleBtnIn('.react-flow__node-video', '提及主体');
  const clicked = await clickSafe(btn);
  const nPanel = await count(PANEL_EL);
  const vis = await visible(PANEL_EL);
  record('video_edit_mention_panel_opens', {
    ok: entered && clicked && nPanel === 1 && vis,
    entered,
    clicked,
    panel_count: nPanel,
    panel_visible: vis,
  });
}

// ── 10) 页面无 JS 错误 ────────────────────────────────────────────
record('no_page_errors', { ok: pageErrors.length === 0, n: pageErrors.length });

const names = Object.keys(out.checks);
out.n_checks = names.length;
out.n_failed = names.filter((n) => out.checks[n].ok !== true).length;
out.pageerrors = pageErrors;

writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log(
  `\nchecks=${out.n_checks} failed=${out.n_failed} pageerrors=${pageErrors.length}`
);
console.log('写入', OUT);
await browser.close();
process.exit(out.n_failed > 0 ? 1 : 0);
