/**
 * 1032-②b-2 运行时探针：图片 / 音频的「生成」点了**到底有没有发生事**。
 *
 * ⭐⭐⭐⭐⭐ **这一批修的不是同一类糊弄**
 *   · 图片生成面板的「生成」：此前**整枚没有 onClick** ⇒ 静态门看得见（死按钮）
 *   · 音频生成面板的「生成」：此前**有 onClick，但函数体是空的**
 *     ⇒ ⇒ 静态门把它算成 `WIRED` ⇒ ⇒ **静态门看不见这一类**
 *     ⇒ ⇒ 只有运行时门能抓它
 *
 * ⭐ 判据一律写成「**某个可观察的东西变了**」：
 *   · 点「生成」⇒ ⇒ 页面上出现「生成中…」（节点上的处理态覆盖层）
 *   · 3s 后 ⇒ ⇒ 图片节点里**真的多了一张 `<img>`**；音频节点上**真的出现时长徽标**
 *   · ⭐ **负控**：提示词为空时点「生成」⇒ ⇒ **什么也不该发生**
 *     （这条是双向判据的另一半 —— 只验「该发生时发生」不够，
 *       还得验「不该发生时**不**发生」，否则一个恒真的按钮也能过）
 *
 * 纪律：
 *   · 跑在**本地复刻**上（localhost:4317），不碰源站，不消耗任何积分
 *   · 只点本批新接的「生成」；**绝不点生成/发送/购买/充值**（指源站）
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
  process.env.JIMENG_B2_JSON ||
  resolve(REPO_ROOT, 'docs/research/jimeng-canvas/inputs/gen-runtime-1032b2.json');
mkdirSync(dirname(OUT), { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
const pageErrors = [];
page.on('pageerror', (e) => pageErrors.push(String(e).slice(0, 200)));

await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForTimeout(6000);

const out = {
  generated_by: 'jimeng_probe1032b2_gen_runtime.mjs',
  note: '⭐ 判据是「某个可观察的东西变了」；负控验「不该发生时**不**发生」。',
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

const selectNode = async (kind, idx = 0) => {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(250);
  const n = page.locator('.react-flow__node-' + kind);
  const c = await n.count();
  if (!c) return false;
  await n.nth(Math.min(idx, c - 1)).click({ position: { x: 6, y: 6 } });
  await page.waitForTimeout(900);
  return true;
};

/** 「生成中…」覆盖层是否可见（图片侧 / 音频侧各一个 testid）。
 *  ⭐ 选择器写成**字面量**：verifier 的 DD993V.1 要在**源码里**认这几枚 testid，
 *  ⇒ ⇒ 若这里用字符串拼接（`'[data-jimeng-' + tid + ']'`）⇒ ⇒ 源码里就**没有**那串字面量
 *  ⇒ ⇒ ⇒ verifier 的标记检查会**误判成「探针没做这件事」** ⇒ ⇒ 门恒红。 */
const IMG_GEN_SEL = '[data-jimeng-image-generating]';
const AUDIO_GEN_SEL = '[data-jimeng-audio-generating]';

const generatingVisible = async (sel) =>
  page.evaluate(
    (s) => {
      const el = document.querySelector(s);
      if (!el) return false;
      const b = el.getBoundingClientRect();
      return b.width > 0 && b.height > 0;
    },
    sel
  );

// ── 0) 塞一个空图片节点（左栏「图片」入口）────────────────────────────
{
  const before = await nodeCount();
  const rail = page.locator('button[aria-label="图片"]');
  let clicked = false;
  if (await rail.count()) {
    clicked = await clickSafe(rail.first());
  }
  const after = await nodeCount();
  record('image_node_inserted', { ok: clicked && after === before + 1, before, after });
}

// ── 1) 图片「生成」：负控（空提示词 ⇒ 什么都不该发生）─────────────────
{
  const okSel = await selectNode('image');
  const ta = page.locator('textarea[aria-label="图片生成提示词"]');
  const taOk = (await ta.count()) > 0;
  if (taOk) {
    await ta.first().fill('');
    await page.waitForTimeout(300);
  }
  const btn = await visibleBtnIn('.react-flow__node-image', '请输入提示词');
  const clicked = await clickSafe(btn);
  await page.waitForTimeout(900);
  const gen = await generatingVisible(IMG_GEN_SEL);
  record('image_gen_empty_prompt_does_nothing', {
    ok: okSel && taOk && clicked && gen === false,
    selected: okSel,
    textarea_found: taOk,
    clicked,
    generating_visible: gen,
  });
}

// ── 2) 图片「生成」：真点 ⇒ 进入「生成中…」──────────────────────────
{
  const okSel = await selectNode('image');
  const ta = page.locator('textarea[aria-label="图片生成提示词"]');
  const taOk = (await ta.count()) > 0;
  if (taOk) {
    await ta.first().fill('一只坐在窗台上的橘猫');
    await page.waitForTimeout(400);
  }
  const btn = await visibleBtnIn('.react-flow__node-image', '生成');
  const clicked = await clickSafe(btn);
  await page.waitForTimeout(600);
  const gen = await generatingVisible(IMG_GEN_SEL);
  record('image_gen_enters_generating', {
    ok: okSel && taOk && clicked && gen === true,
    selected: okSel,
    textarea_found: taOk,
    clicked,
    generating_visible: gen,
  });
}

// ── 3) 图片「生成」：3s 后**真的多了一张图**──────────────────────────
{
  await page.waitForTimeout(3800);
  const imgs = await page.evaluate(
    () => document.querySelectorAll('.react-flow__node-image img').length
  );
  const gen = await generatingVisible(IMG_GEN_SEL);
  record('image_gen_produces_poster', {
    ok: imgs >= 1 && gen === false,
    img_count: imgs,
    generating_visible: gen,
  });
}

// ── 4) 音频「生成」：负控（空提示词 ⇒ 什么都不该发生）─────────────────
{
  const okSel = await selectNode('audio');
  const ta = page.locator('textarea[aria-label="音频生成提示词"]');
  const taOk = (await ta.count()) > 0;
  if (taOk) {
    await ta.first().fill('');
    await page.waitForTimeout(300);
  }
  const btn = await visibleBtnIn('.react-flow__node-audio', '请输入提示词');
  const clicked = await clickSafe(btn);
  await page.waitForTimeout(900);
  const gen = await generatingVisible(AUDIO_GEN_SEL);
  record('audio_gen_empty_prompt_does_nothing', {
    ok: okSel && taOk && clicked && gen === false,
    selected: okSel,
    textarea_found: taOk,
    clicked,
    generating_visible: gen,
  });
}

// ── 5) 音频「生成」：真点 ⇒ 进入「生成中…」──────────────────────────
{
  const okSel = await selectNode('audio');
  const ta = page.locator('textarea[aria-label="音频生成提示词"]');
  const taOk = (await ta.count()) > 0;
  if (taOk) {
    await ta.first().fill('一段轻快的女声朗读');
    await page.waitForTimeout(400);
  }
  const btn = await visibleBtnIn('.react-flow__node-audio', '生成');
  const clicked = await clickSafe(btn);
  await page.waitForTimeout(600);
  const gen = await generatingVisible(AUDIO_GEN_SEL);
  record('audio_gen_enters_generating', {
    ok: okSel && taOk && clicked && gen === true,
    selected: okSel,
    textarea_found: taOk,
    clicked,
    generating_visible: gen,
  });
}

// ── 6) 音频「生成」：3s 后**真的出现时长徽标**────────────────────────
{
  await page.waitForTimeout(3800);
  const badge = await page.evaluate(() => {
    const el = document.querySelector('[data-jimeng-audio-generated-badge]');
    if (!el) return null;
    const b = el.getBoundingClientRect();
    return {
      visible: b.width > 0 && b.height > 0,
      text: (el.innerText || '').trim(),
    };
  });
  const gen = await generatingVisible(AUDIO_GEN_SEL);
  record('audio_gen_produces_duration_badge', {
    ok: !!(badge && badge.visible) && gen === false,
    badge_visible: !!(badge && badge.visible),
    badge_text: badge ? badge.text : null,
    generating_visible: gen,
  });
}

// ── 7) 页面无 JS 错误 ────────────────────────────────────────────────
record('no_page_errors', { ok: pageErrors.length === 0, n: pageErrors.length });

const names = Object.keys(out.checks);
out.n_checks = names.length;
out.n_failed = names.filter((n) => out.checks[n].ok !== true).length;
out.pageerrors = pageErrors;

writeFileSync(OUT, JSON.stringify(out, null, 1));
// ⭐⭐⭐⭐⭐ 2026-10-21 修正：这行原先写成 `console.log('...%d...' % (a, b, c))` ——
//   那是 **Python 的** `%` 格式化写法；**JS 里 `%` 是取模运算符**
//   ⇒ ⇒ `'...' % (...)` 求值成 **NaN** ⇒ ⇒ 整行只打印 "NaN"。
//   ⇒ ⇒ 教训（与 ②b-1 那次「门里 `%s:%s` % <一个字符串>」同族）：
//   **JS 里没有 `%` 格式化 ⇒ 想插值就用模板字符串。**
console.log(
  `\nchecks=${out.n_checks} failed=${out.n_failed} pageerrors=${pageErrors.length}`
);
console.log('写入', OUT);
await browser.close();
process.exit(out.n_failed > 0 ? 1 : 0);
