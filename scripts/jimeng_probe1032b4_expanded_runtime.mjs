/**
 * 1032-②b-4 运行时探针：「**已展开的生成器**」浮层
 * —— 点「展开面板」到底有没有发生事。
 *
 * ⭐⭐⭐⭐⭐ **这一批修的是最后一类死按钮**（静态门 DEAD_NO_HANDLER）：
 *   三条「展开面板」+ 一条「展开视频生成器」此前**整枚没有 onClick**
 *   ⇒ ⇒ 静态门抓得到 ⇒ ⇒ 死按钮 4 → 0。
 *
 * ⭐⭐⭐⭐⭐ 但**「有 onClick」不等于「点了有反应」** ⇒ ⇒ 所以本门
 * **不查源码里有没有 onClick**，而是**真点一遍**，验「某个可观察的东西变了」：
 *
 *  ⓪ ⭐ **仪器自检**：本轮探针**真的跑成了**（画布挂上了？节点在？浮层此刻不在？）
 *  ① 点「展开面板」⇒ ⇒ 浮层真的出现（`[data-testid="expanded-gen-layer"]`）
 *  ② 浮层是 `role="dialog"`、aria 逐字 **`已展开的视频生成器`**
 *     （SOURCE_FACT 批次 1032-②b-1 实测）
 *  ③ 几何：**920×480** / radius **20px** / `position: fixed` / z **50** / **相对视口居中**
 *     ⇒ ⇒ **不是全屏遮罩，是一个居中的浮动面板**
 *  ④ ⭐ 浮层内**没有 input/textarea** ⇒ 提示词区是 **contenteditable**
 *  ⑤ 5 枚 42×36 的普通按钮：全部 / 图片 / 视频 / 音频 / 文本
 *     ⇒ ⇒ **没有** `role=tab`（源站浮层内没有 role=tab/option/radio）
 *  ⑥ 点一枚类型钮 ⇒ ⇒ 「引用参考」的 aria-label **真的变了**（可观察）
 *  ⑦ ⭐ **负控**：提示词为空点「生成」⇒ ⇒ **什么也不该发生**
 *  ⑧ 打了字点「生成」⇒ ⇒ 视频节点**真的出现「生成中…」**
 *  ⑨ 点「折叠视频生成器」⇒ ⇒ 浮层关
 *  ⑩ ⭐ `Esc` ⇒ ⇒ 浮层关、**且那个节点还在选中态**（编辑态**没退**）
 *     ⇒ ⇒ 这是「分级的退出路径」在复刻里的落点
 *  ⑪ ⭐ 点浮层外面的透明点击层 ⇒ ⇒ 浮层关
 *  ⑫ 页面无 JS 错误
 *
 * ⚠️⭐⭐⭐ **本探针量的几何必须不受「CSS 构建产物陈旧」影响**：
 *   本仓 dev server（Next.js + Tailwind v4 + **PostCSS**）**不监听新出现的内容文件**
 *   ⇒ ⇒ 新建组件里的类名，要等「CSS 文件自身发生内容变化」才会被重新扫描并生成
 *   ⇒ ⇒ 一旦某个类名缺失，量到的是**陈旧 CSS** ⇒ **假阴性**（「量错了 ≠ 产品坏了」）。
 *   ⇒ ⇒ 复刻侧把所有**源站实测尺寸**都写成了 **inline style**（不走 className）
 *   ⇒ ⇒ 于是本探针量的尺寸**不依赖 CSS 构建产物**。
 *   ⚠️ 本批真的踩到了：`w-[42px]` 没进 CSS ⇒ 5 枚类型钮量到 24px（内容宽）而不是 42px，
 *   一度被当成「复刻做错了」⇒⇒ **先判是门错还是数据错**。
 *
 * ⚠️ 诚实标注边界（源站规格只覆盖**视频**这一种）：
 *   图片 / 音频两种浮层的具体规格**未在源站实测** ⇒ 复刻侧是 CLONE_DECISION。
 *
 * 纪律：
 *   · 跑在**本地复刻**上（localhost:4317），不碰源站，不消耗任何积分
 *   · **绝不点生成/发送/购买/充值**（指源站）；复刻侧的「生成」是 mock
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
  process.env.JIMENG_B4_JSON ||
  resolve(REPO_ROOT, 'docs/research/jimeng-canvas/inputs/expanded-runtime-1032b4.json');
mkdirSync(dirname(OUT), { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const pageErrors = [];
page.on('pageerror', (e) => pageErrors.push(String(e).slice(0, 200)));

// ⭐⭐⭐⭐⭐ **仪器故障与「数据有问题」必须用不同的退出码** ⇒ ⇒ 1 = 数据有问题、
//   2 = 仪器崩了、0 = 全绿。而「仪器崩了」**必须写产物** —— 不写的话，契约门会去读
//   **上一轮留下的旧读数** ⇒ ⇒ 那就把「本轮没跑」伪装成「本轮跑过了」⇒ ⇒ 假绿。
const _writeCrash = (msg) => {
  try {
    writeFileSync(OUT, JSON.stringify({
      generated_by: 'jimeng_probe1032b4_expanded_runtime.mjs',
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
//   ⇒ ⇒ 契约门把 `probe_run` 写成 `rc=1 stderr=…` ⇒ ⇒ 产物多出 200 多字节
//   ⇒ ⇒ ⇒ **可复现性门立刻报 drift** ⇒ ⇒ 而真相是「仪器抖了一下」。
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
  generated_by: 'jimeng_probe1032b4_expanded_runtime.mjs',
  note: '⭐ 判据是「某个可观察的东西变了」；负控验「不该发生时**不**发生」。' +
    '浮层规格 = SOURCE_FACT 批次 1032-②b-1（**只覆盖视频这一种**）。',
  checks: {},
};
const record = (name, value) => {
  out.checks[name] = value;
  console.log((value.ok ? '  OK  ' : '  FAIL') + '  ' + name + ' :: ' + JSON.stringify(value));
};

const nodeCount = () =>
  page.evaluate(() => document.querySelectorAll('.react-flow__node').length);

/** 在某个节点容器内找「可见的」某 aria-label 按钮；找不到再退回全局。 */
const visibleBtnIn = async (scopeSel, aria) => {
  const scope = page.locator(scopeSel);
  const c = await scope.count();
  for (let i = 0; i < c; i++) {
    const n = scope.nth(i).locator('button[aria-label="' + aria + '"]');
    const k = await n.count();
    for (let j = 0; j < k; j++) {
      if (await n.nth(j).isVisible()) return n.nth(j);
    }
  }
  const g = page.locator('button[aria-label="' + aria + '"]');
  const gc = await g.count();
  for (let i = 0; i < gc; i++) {
    if (await g.nth(i).isVisible()) return g.nth(i);
  }
  return null;
};

/** 全局找「可见的」某 aria-label 按钮。
 *  ⭐ 生成面板挂在 xyflow 的 <NodeToolbar> 里 —— 而 **NodeToolbar 是节点的
 *    「兄弟」不是后代** ⇒ ⇒ 按 `.react-flow__node[data-id=…]` 去找按钮
 *    **必然找不到** ⇒ ⇒ 这里只能在全局找，并靠「此刻只有一个节点被选中」
 *    这条前置判据来保证找到的按钮就是那个节点的。 */
const visibleBtnGlobal = async (aria) => {
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
    return false;
  }
};

// ⭐ 选择器写成**字面量常量** ⇒ verifier 的标记检查按「源码里有没有那串字面量」
//   判定探针是否真做了事 ⇒ ⇒ 拼接写法会让门恒红。
const LAYER_SEL = '[data-testid="expanded-gen-layer"]';
const PROMPT_SEL = '[data-testid="expanded-gen-prompt"]';
const VIDEO_GEN_SEL = '[data-jimeng-video-generating]';

const layerCount = () => page.locator(LAYER_SEL).count();
const layerVisible = () =>
  page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) return false;
    const b = el.getBoundingClientRect();
    return b.width > 0 && b.height > 0;
  }, LAYER_SEL);
const generatingVisible = () =>
  page.evaluate(
    (s) => {
      const el = document.querySelector(s);
      if (!el) return false;
      const b = el.getBoundingClientRect();
      return b.width > 0 && b.height > 0;
    },
    VIDEO_GEN_SEL
  );

// ── 0) ⭐ 仪器自检：本轮探针**真的跑成了** ───────────────────────────
//   ⭐⭐⭐ 一道门整体跑不起来时，它报的「红」**不是**「产品坏了」，是「仪器没跑」
//   ⇒ ⇒ 所以第一件事是量「我到底跑起来没有」：画布挂上了吗？节点在吗？
//   ⇒ ⇒ 基线里还要求「浮层此刻**不在**」—— 否则「点开浮层」这条判据永远为真。
{
  const nodes = await nodeCount();
  const layerAtStart = await layerCount();
  const errs = pageErrors.length;
  record('probe_actually_ran', {
    ok: nodes > 0 && layerAtStart === 0 && errs === 0,
    n_nodes: nodes, layer_at_start: layerAtStart, pageerrors: errs,
  });
}

// ── 0b) 塞一个**空视频节点**（左栏「视频」入口）⇒ 它会挂上生成面板 ────
{
  const before = await nodeCount();
  const rail = page.locator('button[aria-label="视频"]');
  let clicked = false;
  if (await rail.count()) clicked = await clickSafe(rail.first());
  const after = await nodeCount();
  record('empty_video_node_inserted', { ok: clicked && after === before + 1, before, after });
  await page.waitForTimeout(800);
}

// 选中那个新节点（生成面板只挂在**空**视频节点上）
{
  const n = page.locator('.react-flow__node-video');
  const c = await n.count();
  let ok = false;
  if (c) {
    // ⭐ 选**最后一个**（刚插入的那个落在视口中心）
    await n.nth(c - 1).click({ position: { x: 6, y: 6 } });
    await page.waitForTimeout(900);
    ok = true;
  }
  record('video_node_selected', { ok, n_video_nodes: c });
}

// ── 1) 点「展开面板」⇒ 浮层真的出现 ──────────────────────────────────
let layerOpened = false;
{
  const btn = await visibleBtnIn('.react-flow__node-video', '展开面板');
  const clicked = await clickSafe(btn);
  await page.waitForTimeout(600);
  const n = await layerCount();
  const vis = await layerVisible();
  layerOpened = clicked && n === 1 && vis;
  record('expand_button_opens_layer', {
    ok: layerOpened, clicked, layer_count: n, layer_visible: vis,
  });
}

// ── 2) 浮层是 dialog + aria 逐字「已展开的视频生成器」 ─────────────────
{
  const info = await page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) return null;
    const b = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return {
      role: el.getAttribute('role'),
      aria: el.getAttribute('aria-label'),
      w: Math.round(b.width),
      h: Math.round(b.height),
      position: cs.position,
      z_index: cs.zIndex,
      border_radius: cs.borderRadius,
    };
  }, LAYER_SEL);
  const ok = !!info && info.role === 'dialog' && info.aria === '已展开的视频生成器';
  record('layer_is_dialog_with_source_aria', { ok, ...(info || {}) });
}

// ── 3) 几何：920×480 / radius 20px / fixed / z 50 ─────────────────────
{
  const info = await page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) return null;
    const b = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return {
      w: Math.round(b.width), h: Math.round(b.height),
      position: cs.position, z_index: cs.zIndex, border_radius: cs.borderRadius,
      // ⭐ 源站 rect.x=296 rect.y=235（视口 1512×950）⇒ **相对视口居中**
      center_dx: Math.round(b.left + b.width / 2 - window.innerWidth / 2),
      center_dy: Math.round(b.top + b.height / 2 - window.innerHeight / 2),
    };
  }, LAYER_SEL);
  const ok = !!info && info.w === 920 && info.h === 480 &&
    info.position === 'fixed' && info.border_radius === '20px' &&
    String(info.z_index) === '50' &&
    Math.abs(info.center_dx) <= 1 && Math.abs(info.center_dy) <= 1;
  record('layer_geometry_matches_source', { ok, ...(info || {}) });
}

// ── 4) 浮层内**没有 input/textarea**（提示词区是 contenteditable）─────
{
  const info = await page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) return null;
    return {
      n_input: el.querySelectorAll('input').length,
      n_textarea: el.querySelectorAll('textarea').length,
      n_contenteditable: el.querySelectorAll('[contenteditable="true"]').length,
    };
  }, LAYER_SEL);
  const ok = !!info && info.n_input === 0 && info.n_textarea === 0 &&
    info.n_contenteditable >= 1;
  record('layer_has_no_input_or_textarea', { ok, ...(info || {}) });
}

// ── 5) 5 枚 42×36 的普通按钮（**没有** role=tab）──────────────────────
{
  const info = await page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) return null;
    const want = ['全部', '图片', '视频', '音频', '文本'];
    const found = [];
    const bad = [];
    for (const t of want) {
      const btns = Array.from(el.querySelectorAll('button')).filter(
        (b) => (b.innerText || '').trim() === t
      );
      if (!btns.length) { bad.push(t + ':missing'); continue; }
      const b = btns[0];
      const r = b.getBoundingClientRect();
      found.push({ t, w: Math.round(r.width), h: Math.round(r.height), role: b.getAttribute('role') });
      if (b.getAttribute('role')) bad.push(t + ':has-role');
    }
    return { found, bad, n_tab: el.querySelectorAll('[role="tab"]').length };
  }, LAYER_SEL);
  const ok = !!info && info.bad.length === 0 && info.n_tab === 0 &&
    info.found.length === 5 &&
    info.found.every((f) => f.w === 42 && f.h === 36);
  record('layer_has_five_ref_type_buttons', { ok, ...(info || {}) });
}

// ── 6) 点一枚类型钮 ⇒ 「引用参考」的 aria-label **真的变了** ─────────
{
  const before = await page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) return null;
    const b = el.querySelector('button[aria-label^="引用参考"]');
    return b ? b.getAttribute('aria-label') : null;
  }, LAYER_SEL);
  const clicked = await page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) return false;
    const b = Array.from(el.querySelectorAll('button')).find(
      (x) => (x.innerText || '').trim() === '视频'
    );
    if (!b) return false;
    b.click();
    return true;
  }, LAYER_SEL);
  await page.waitForTimeout(400);
  const after = await page.evaluate((s) => {
    const el = document.querySelector(s);
    if (!el) return null;
    const b = el.querySelector('button[aria-label^="引用参考"]');
    return b ? b.getAttribute('aria-label') : null;
  }, LAYER_SEL);
  record('ref_type_switch_is_observable', {
    ok: clicked && before !== null && after !== null && before !== after,
    clicked, aria_before: before, aria_after: after,
  });
}

// ── 7) ⭐ 负控：提示词为空点「生成」⇒ **什么也不该发生** ─────────────
{
  const gen = await page.locator(LAYER_SEL + ' button[aria-label="生成"]');
  const clicked = await clickSafe(gen.first());
  await page.waitForTimeout(900);
  const generating = await generatingVisible();
  record('empty_prompt_generate_does_nothing', {
    ok: clicked && generating === false, clicked, generating_visible: generating,
  });
}

// ── 8) 打了字点「生成」⇒ 视频节点**真的出现「生成中…」** ───────────
{
  const box = page.locator(PROMPT_SEL);
  const has = (await box.count()) > 0;
  let typed = false;
  if (has) {
    try {
      await box.first().fill('一只在雨里跑过水洼的橘猫', { timeout: 8000 });
      typed = true;
    } catch (e) { typed = false; }
  }
  await page.waitForTimeout(300);
  const gen = page.locator(LAYER_SEL + ' button[aria-label="生成"]');
  const clicked = await clickSafe(gen.first());
  // ⭐ mock 生成 **3s 后完成** ⇒ 节点会变成「有媒体」
  //   ⇒ ⇒ 不能睡一个固定时长（睡过头就看不到「生成中」了）
  //   ⇒ ⇒ 改成**轮询**，在 3s 完成之前命中即可
  let generating = false;
  for (let i = 0; i < 22 && !generating; i++) {
    await page.waitForTimeout(100);
    generating = await generatingVisible();
  }
  record('generate_enters_generating', {
    ok: has && typed && clicked && generating === true,
    contenteditable_found: has, typed, clicked, generating_visible: generating,
  });
}

// ── 9) 点「折叠视频生成器」⇒ 浮层关 ─────────────────────────────────
{
  const btn = page.locator(LAYER_SEL + ' button[aria-label="折叠视频生成器"]');
  const has = (await btn.count()) > 0;
  const clicked = await clickSafe(btn.first());
  await page.waitForTimeout(500);
  const n = await layerCount();
  record('collapse_button_closes_layer', { ok: has && clicked && n === 0, has, clicked, layer_count: n });
}

// ⭐ 最近一次插入的节点 id（供第 10/11 条精确定位用）
let insertedId = null;

// ── 10) ⭐ Esc ⇒ 浮层关、**且那个节点还在选中态**（编辑态**没退**）───
//   ⭐⭐⭐⭐⭐ **这一条第一次写的时候，红的是判据自己，不是产品** —— 记下来：
//   原判据断言「Esc 之后生成面板的『展开面板』钮还在可见」，
//   但 **mock 生成 3s 后完成** ⇒ 节点变成「有媒体」⇒ **生成面板合法卸载**
//   ⇒ ⇒ 「面板钮还在」这个**前提根本不成立** ⇒ 判据恒假。
//   ⇒ ⇒ 修法不是放宽判据，而是**换掉被依赖的状态**：
//   ⭐ 另插一个**新的空视频节点**（与 mock 生成完成态解耦），
//   ⭐ 断言改成「**那个节点仍在选中态**」—— 那才是「编辑态没退」的真实语义。
{
  // ⭐ 插一个**新的空视频节点**（此刻上一个节点还处于选中态 ⇒ 正是缺陷场景）
  //   ⭐ 新节点 id 用「插入前后 id 差集」确定，**不靠 DOM 顺序猜**
  const idsBefore = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.react-flow__node')).map((n) =>
      n.getAttribute('data-id')
    )
  );
  const rail = page.locator('button[aria-label="视频"]');
  if (await rail.count()) await clickSafe(rail.first());
  await page.waitForTimeout(1000);
  const newId = await page.evaluate((prev) => {
    const ids = Array.from(document.querySelectorAll('.react-flow__node')).map((n) =>
      n.getAttribute('data-id')
    );
    return ids.find((id) => !prev.includes(id)) || null;
  }, idsBefore);
  insertedId = newId;
  // ⭐⭐⭐ 插入后**只能有一个**节点处于选中态，且就是新节点。
  //   （此前 `addNodeAt` 不取消旧节点的选中态 ⇒ 两个 selected ⇒ `soloSelected`
  //     为 false ⇒ 按 SOURCE_FACT 批 62「多选时不显示生成面板」
  //     ⇒ **任何节点都不显示生成面板** ⇒ 新插的节点等于废掉 —— 真缺陷。）
  const selInfo = await page.evaluate((id) => {
    const sels = Array.from(document.querySelectorAll('.react-flow__node.selected'));
    return {
      n_selected: sels.length,
      n_selected_dom: sels.length,
      new_is_selected: !!id && !!document.querySelector(
        '.react-flow__node.selected[data-id="' + id + '"]'
      ),
    };
  }, newId);
  record('insert_selects_only_the_new_node', {
    ok: !!newId && selInfo.n_selected === 1 && selInfo.new_is_selected === true,
    // ⚠️⭐⭐ **产物里不许出现随机量** ⇒ ⇒ **节点 id 不进产物**
    //   （id 形如 `video-<毫秒时间戳>` ⇒ 每次跑都不同 ⇒ 一旦被可复现性门收录就会漂移）
    //   ⇒ ⇒ 只留「这个 id 确实是新增的」与「选中节点**个数**」。
    new_node_id_is_new: !!newId,
    n_selected: selInfo.n_selected,
    new_is_selected: selInfo.new_is_selected,
  });

  // 找「展开面板」按钮（⚠️ 必须在**全局**找：生成面板挂在 NodeToolbar 里，
  //   而 NodeToolbar 是节点的**兄弟**不是后代 ⇒ 按节点元素内找必然落空；
  //   「找到的按钮属于新节点」由上面那条「只有新节点被选中」保证）
  const btn = await visibleBtnGlobal('展开面板');
  const hasBtn = !!btn;
  const clicked = await clickSafe(btn);
  await page.waitForTimeout(500);
  const nOpen = await layerCount();
  await page.keyboard.press('Escape');
  await page.waitForTimeout(800);
  const nClosed = await layerCount();
  // ⭐ 那个节点**还在选中态**吗？（= 编辑态没退）
  const stillSelected = await page.evaluate((id) => {
    if (!id) return false;
    const el = document.querySelector('.react-flow__node.selected');
    return !!el && el.getAttribute('data-id') === id;
  }, newId);
  record('escape_closes_layer_but_keeps_edit_mode', {
    ok: clicked && nOpen === 1 && nClosed === 0 && stillSelected === true,
    clicked, has_btn: hasBtn, layer_before: nOpen, layer_after: nClosed,
    // ⚠️ 同上：**节点 id 不进产物**（随机量）
    node_still_selected: stillSelected,
  });
}

// ── 11) ⭐ 点浮层外面的透明点击层 ⇒ 浮层关（复刻自带的 CLONE_DECISION）─
{
  const btn = await visibleBtnGlobal('展开面板');
  const hasBtn = !!btn;
  const clicked = await clickSafe(btn);
  await page.waitForTimeout(500);
  const nOpen = await layerCount();
  // ⚠️ 用 **DOM 派发**而不是 Playwright 的真实点击：
  //   真实点击要点在「没有别的元素盖住」的位置上，而透明层铺满视口、
  //   中心又被对话框压着 ⇒ ⇒ 真实点击会因「被别的元素截获」而假失败。
  //   这里要验的是**处理器真的接上了**，不是命中测试。
  const backdropClicked = await page.evaluate(
    (s) => {
      const el = document.querySelector(s);
      if (!el) return false;
      el.click();
      return true;
    },
    '[data-testid="expanded-gen-layer-backdrop"]'
  );
  await page.waitForTimeout(700);
  const nClosed = await layerCount();
  record('backdrop_click_closes_layer', {
    ok: clicked && nOpen === 1 && backdropClicked && nClosed === 0,
    has_btn: hasBtn,
    clicked, backdrop_clicked: backdropClicked,
    layer_before: nOpen, layer_after: nClosed,
  });
}

// ── 11) 页面无 JS 错误 ───────────────────────────────────────────────
record('no_page_errors', { ok: pageErrors.length === 0, n: pageErrors.length });

const names = Object.keys(out.checks);
out.n_checks = names.length;
out.n_failed = names.filter((n) => out.checks[n].ok !== true).length;
out.pageerrors = pageErrors;

writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log(`\nchecks=${out.n_checks} failed=${out.n_failed} pageerrors=${pageErrors.length}`);
console.log('写入', OUT);
await browser.close();
process.exit(out.n_failed > 0 ? 1 : 0);
