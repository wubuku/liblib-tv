/**
 * 1032-②b-1 运行时探针：**真的点一遍**这批「修好的按钮」，量它们到底有没有发生事。
 *
 * ⭐⭐⭐⭐⭐ **为什么必须有这一层**
 *   1032 的静态门只验「有没有接线」⇒ ⇒ 「有 onClick」**不等于**「用户点了有反应」。
 *   本批接的每个按钮都必须产生一个**可观察的状态变化**，否则就还是糊弄
 *   （只是从「死按钮」变成了「空 handler」—— 那更坏）。
 *   ⇒ ⇒ 所以每条判据都写成「**某个可观察的东西变了**」，不是「按钮有 onClick」。
 *
 * 纪律：
 *   · 量法照仓里已验证的写法（`waitUntil:'domcontentloaded'` + `waitForTimeout`
 *     + 真实鼠标事件）；host 用 `localhost`
 *   · **产物里不许出现随机量**（时间戳 / pid / 耗时 / 节点 id）
 *   · 只读 + 点本批新接的那些按钮；**绝不点生成 / 发送 / 购买 / 充值**
 */
import pw from '/Users/yangjiefeng/node_modules/playwright/index.js';
import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const { chromium } = pw;

const URL = 'http://localhost:4317/jimeng/canvas/demo';
const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, '..');
const OUT =
  process.env.JIMENG_B1_JSON ||
  resolve(REPO_ROOT, 'docs/research/jimeng-canvas/inputs/wired-runtime-1032b1.json');
mkdirSync(dirname(OUT), { recursive: true });

const UPLOAD_FILE = '/tmp/jm-upload-sample-1032b1.png';
/* ⭐⭐⭐⭐⭐ 1032-⑬ 修：**夹具不许靠 /tmp 里的「 leftovers」**。
 *
 *   此前这个夹具是**手工**放进 /tmp 的 ⇒ ⇒ 一次 /tmp 清理就没了
 *   ⇒ ⇒ `chooser.setFiles(不存在的路径)` 抛 ENOENT ⇒ **上传根本没发生**
 *   ⇒ ⇒ ⇒ 于是 3 条上传判据（gen_panel / repaint / video_edit）全红
 *   ⇒ ⇒ ⇒ 而那个红**长得极像产品回归**（“上传功能坏了”）⇒ ⇒ 其实只是夹具没了。
 *
 *   ⇒ 现在：**夹具缺失就现造**（1×1 合法 PNG，够走通 FileReader → poster 那条路）
 *   ⇒ ⇒ 于是这道探针**不再依赖任何机器上的残留状态**。
 */
if (!existsSync(UPLOAD_FILE)) {
  writeFileSync(UPLOAD_FILE, Buffer.from(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
    'base64'));
}

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ acceptDownloads: true });
const pageErrors = [];
page.on('pageerror', (e) => pageErrors.push(String(e).slice(0, 200)));

await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForTimeout(6000);

const out = {
  generated_by: 'jimeng_probe1032b1_wired_runtime.mjs',
  note: '⭐ 判据一律是「某个可观察的东西变了」，不是「按钮有 onClick」。',
  checks: {},
};
const record = (name, value) => {
  out.checks[name] = value;
  console.log((value.ok ? '  OK  ' : '  FAIL') + '  ' + name + ' :: ' + JSON.stringify(value));
};

const nodeCount = () =>
  page.evaluate(() => document.querySelectorAll('.react-flow__node').length);

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

const btn = (aria) => page.locator('button[aria-label="' + aria + '"]');
const visible = async (aria) => {
  const n = btn(aria);
  const c = await n.count();
  for (let i = 0; i < c; i++) {
    if (await n.nth(i).isVisible()) return true;
  }
  return false;
};
const clickBtn = async (aria, idx = 0) => {
  const n = btn(aria);
  const c = await n.count();
  let k = 0;
  for (let i = 0; i < c; i++) {
    if (await n.nth(i).isVisible()) {
      if (k === idx) {
        // ⚠️⭐⭐ **一条判据点不动，不该让整个探针崩掉** ——
        //   崩掉 ⇒ 后面所有判据都没跑 ⇒ 报出来的读数是「半份」
        //   ⇒ ⇒ 点不动 ⇒ 记 FAIL，继续跑下一条。
        try {
          await n.nth(i).click({ timeout: 12000 });
        } catch (e) {
          return false;
        }
        await page.waitForTimeout(700);
        return true;
      }
      k++;
    }
  }
  return false;
};

/** ⭐ 工具条条目（局部重拍/视频编辑…）的**可访问名来自文案**，没有 aria-label
 *  ⇒ 只按 aria-label 找会**一个都找不到** ⇒ 「量错了 ≠ 产品坏了」又一处。 */
const clickBtnByText = async (text) => {
  const n = page.locator('button', { hasText: text });
  const c = await n.count();
  for (let i = 0; i < c; i++) {
    if (await n.nth(i).isVisible()) {
      try {
        await n.nth(i).click({ timeout: 12000 });
      } catch (e) {
        return false;
      }
      await page.waitForTimeout(700);
      return true;
    }
  }
  return false;
};

/** ⭐⭐⭐ 把目标按钮**平移进视口**再点。
 *  视频编辑面板挂在节点**下方**（`absolute top-full`），而演示画布里那个
 *  带画面的视频节点在视口**底部** ⇒ ⇒ 面板整体落在视口外（y=768 > vh=720）
 *  ⇒ ⇒ Playwright 点不到（页面本身不滚动，滚动的是画布视口）。
 *  ⇒ ⇒ 这里用**滚轮平移画布**（React Flow 的 wheel = 平移）把它挪进来。
 *  ⚠️ 这也是「量错了 ≠ 产品坏了」的一处：点不动**不等于**没接线。 */
const ensureInViewport = async (aria) => {
  for (let attempt = 0; attempt < 6; attempt++) {
    const box = await page
      .locator('button[aria-label="' + aria + '"]')
      .first()
      .boundingBox()
      .catch(() => null);
    if (!box) return false;
    const vh = page.viewportSize().height;
    const vw = page.viewportSize().width;
    // ⚠️⭐⭐ **「在视口里」还不够**：左下角的 `.jimeng-bottom-dock` 会**盖住**
    //   画布左下区域 ⇒ ⇒ 按钮明明可见，点下去却「intercepts pointer events」
    //   ⇒ ⇒ 所以判据要求它落在**上方安全区**（离底 ≥ 140px）。
    const safeBottom = vh - 140;
    const inSafe =
      box.y >= 40 &&
      box.y + box.height <= safeBottom &&
      box.x >= 0 &&
      box.x + box.width <= vw;
    if (inSafe) return true;
    const canvas = await page.locator('.jimeng-canvas').first().boundingBox();
    const cx = canvas ? canvas.x + canvas.width / 2 : vw / 2;
    const cy = canvas ? canvas.y + canvas.height / 2 : vh / 2;
    await page.mouse.move(cx, cy);
    // ⚠️ 滚轮方向：wheel(+, delta) 把画布内容**往上**挪（实测 y 768 → 638）
    await page.mouse.wheel(0, box.y + box.height / 2 > vh / 2 ? 260 : -260);
    await page.waitForTimeout(500);
  }
  return false;
};

const bannerUp = () => page.locator('[data-testid="canvas-pick-banner"]').count();
const cancelPick = async () => {
  const c = page.locator('button[aria-label="取消从画布选择"]');
  if (await c.count()) {
    await c.first().click();
    await page.waitForTimeout(500);
  }
};

/** 引用类按钮的判据：点它 ⇒ 画布进入「从画布选择」点选模式（横幅出现）⇒ 取消后横幅消失 */
const checkRefPick = async (name, aria, idx) => {
  const up0 = await bannerUp();
  const clicked = await clickBtn(aria, idx);
  const up1 = await bannerUp();
  await cancelPick();
  const up2 = await bannerUp();
  record(name, {
    ok: clicked && up1 > up0 && up2 === up0,
    clicked,
    banner_before: up0,
    banner_after_click: up1,
    banner_after_cancel: up2,
  });
};

// ── 0) 先塞一个图片节点（左栏「图片」入口）──────────────────────────
{
  const before = await nodeCount();
  await page.locator('button[aria-label="图片"]').first().click();
  await page.waitForTimeout(1200);
  const after = await nodeCount();
  record('image_node_inserted', { ok: after === before + 1, before, after });
}

// ── 1) 图片生成面板：添加参考 / 引用参考 ×2 ───────────────────────────
{
  const okSel = await selectNode('image');
  record('image_panel_opens', {
    ok: okSel && (await visible('添加参考')),
    selected: okSel,
    add_ref_button_visible: await visible('添加参考'),
  });
  await checkRefPick('image_add_ref_enters_pick_mode', '添加参考', 0);
  await checkRefPick('image_quote_ref_0_enters_pick_mode', '引用参考', 0);
  await checkRefPick('image_quote_ref_1_enters_pick_mode', '引用参考', 1);
}

// ── 2) 视频生成面板：「上传参考图」⇒ 真 file input ⇒ 真落节点 ─────────
{
  const okSel = await selectNode('video', 1); // 第 2 个 = 空视频节点
  const before = await nodeCount();
  let chooserSeen = false;
  let uploadOk = false;
  try {
    const [chooser] = await Promise.all([
      page.waitForEvent('filechooser', { timeout: 6000 }),
      btn('上传参考图').first().click(),
    ]);
    chooserSeen = true;
    await chooser.setFiles(UPLOAD_FILE);
    await page.waitForTimeout(1200);
    const after = await nodeCount();
    uploadOk = after === before + 1;
  } catch (e) {
    uploadOk = false;
  }
  record('gen_panel_upload_adds_node', {
    ok: chooserSeen && uploadOk,
    selected: okSel,
    filechooser_fired: chooserSeen,
    nodes_before: before,
    nodes_after: await nodeCount(),
  });
}

// ── 3) 音频生成面板：添加参考 / 引用参考 ×2 / 显示折扣详情 ────────────
{
  const okSel = await selectNode('audio');
  record('audio_panel_opens', {
    ok: okSel && (await visible('添加参考')),
    selected: okSel,
    add_ref_button_visible: await visible('添加参考'),
  });
  await checkRefPick('audio_add_ref_enters_pick_mode', '添加参考', 0);
  await checkRefPick('audio_quote_ref_0_enters_pick_mode', '引用参考', 0);
  await checkRefPick('audio_quote_ref_1_enters_pick_mode', '引用参考', 1);

  // 显示折扣详情 ⇒ 详情层出现（data-testid）
  const d0 = await page.locator('[data-testid="audio-discount-detail"]').count();
  const clicked = await clickBtn('显示折扣详情', 0);
  const d1 = await page.locator('[data-testid="audio-discount-detail"]').count();
  record('audio_discount_detail_opens', {
    ok: clicked && d1 > d0,
    clicked,
    detail_before: d0,
    detail_after: d1,
  });
}

// ── 4) 文本节点「下载」⇒ 真触发一次下载 ──────────────────────────────
{
  const okSel = await selectNode('text');
  let downloaded = false;
  let suggested = '';
  try {
    const [dl] = await Promise.all([
      page.waitForEvent('download', { timeout: 8000 }),
      btn('下载').first().click(),
    ]);
    downloaded = true;
    suggested = dl.suggestedFilename();
  } catch (e) {
    downloaded = false;
  }
  record('text_node_download_fires', {
    ok: downloaded && /\.html$/.test(suggested),
    selected: okSel,
    download_fired: downloaded,
    filename_is_html: /\.html$/.test(suggested),
  });
}

// ── 5) 会员页：计费 tab 真能切 + 计费 CTA 真的禁用 ────────────────────
{
  await page.locator('[data-testid="canvas-commerce-entry"]').first().click();
  await page.waitForTimeout(900);
  const modalUp = await page.locator('[data-testid="jimeng-member-modal"]').count();
  // 横幅第二行的文案
  const readBanner = () =>
    page.evaluate(() => {
      const m = document.querySelector('[data-testid="jimeng-member-modal"]');
      if (!m) return null;
      const ps = Array.from(m.querySelectorAll('p')).map((p) => (p.textContent || '').trim());
      return ps.filter(Boolean).slice(0, 8);
    });
  const b0 = await readBanner();
  // 点第一个 tab（连续包年 限时5折）
  const tab = page.locator('[data-testid="jimeng-member-modal"] [role="tab"]').first();
  let tabClicked = false;
  if (await tab.count()) {
    await tab.click();
    await page.waitForTimeout(600);
    tabClicked = true;
  }
  const b1 = await readBanner();
  const selectedNow = await page.evaluate(() => {
    const m = document.querySelector('[data-testid="jimeng-member-modal"]');
    if (!m) return null;
    const t = m.querySelector('[role="tab"][aria-selected="true"]');
    return t ? (t.textContent || '').trim() : null;
  });
  record('member_tab_switches_state', {
    ok: modalUp > 0 && tabClicked && JSON.stringify(b0) !== JSON.stringify(b1),
    modal_open: modalUp > 0,
    tab_clicked: tabClicked,
    banner_changed: JSON.stringify(b0) !== JSON.stringify(b1),
    selected_tab: selectedNow,
  });

  // 计费 CTA 必须**禁用**（不能是「能点没反应」）
  const ctaState = await page.evaluate(() => {
    const m = document.querySelector('[data-testid="jimeng-member-modal"]');
    if (!m) return null;
    const btns = Array.from(m.querySelectorAll('button')).filter((b) =>
      ['购买积分', '订阅管理'].includes((b.textContent || '').trim()),
    );
    return {
      n: btns.length,
      all_disabled: btns.length === 2 && btns.every((b) => b.disabled),
    };
  });
  record('member_billing_cta_disabled', {
    ok: !!(ctaState && ctaState.all_disabled),
    cta: ctaState,
  });
  await page.keyboard.press('Escape');
  await page.waitForTimeout(600);
}

// ── 6) 资产库：时间 / 筛选 两枚图标钮真能开菜单、真改状态 ─────────────
{
  await page.locator('button[aria-label="资产库"]').first().click();
  await page.waitForTimeout(900);
  const modalUp = await page.locator('[data-testid="jimeng-assets-modal"]').count();
  const readEmpty = () =>
    page.evaluate(() => {
      const e = document.querySelector('[data-testid="assets-empty"]');
      return e ? (e.textContent || '').trim() : null;
    });
  // ⭐⭐⭐⭐⭐ Batch 1032-④-B 续（判据修复）：**「呈现」有两个面** —— 空态文案
  //   **或** 素材条数 ⇒ ⇒ 只量其中一个 ⇒ ⇒ 在另一种状态下就「读不到」
  //   ⇒ ⇒ 而 `null !== "…"` 恰好为真 ⇒ ⇒ **「读失败」被当成了「有变化」**
  //   ⇒ ⇒ ⇒ 而 ④-B 之后画布**真的有素材** ⇒ ⇒ 切到「视频」后列表非空、
  //   空态元素**根本不存在** ⇒ ⇒ 旧判据「空态文案变了」从此读不到。
  const readCount = () =>
    page.evaluate(() => document.querySelectorAll('[data-testid="assets-item"]').length);
  const e0 = await readEmpty();
  const n0 = await readCount();
  // 时间 → 菜单 → 最近 7 天
  let timeMenu = false;
  let e1 = e0;
  let n1 = n0;
  const timeBtn = btn('时间');
  if (await timeBtn.count()) {
    await timeBtn.first().click();
    await page.waitForTimeout(400);
    const items = page.locator('[aria-label="时间范围"] [role="menuitemradio"]');
    if (await items.count()) {
      timeMenu = true;
      await items.nth(1).click(); // 最近 7 天
      await page.waitForTimeout(500);
      e1 = await readEmpty();
      n1 = await readCount();
    }
  }
  record('assets_time_filter_changes_state', {
    ok: modalUp > 0 && timeMenu && (e0 !== e1 || n0 !== n1),
    modal_open: modalUp > 0,
    menu_opened: timeMenu,
    empty_before: e0,
    empty_after: e1,
    n_items_before: n0,
    n_items_after: n1,
  });

  // 筛选 → 菜单 → 视频（筛选行高亮移动）
  const filtBtn = btn('筛选');
  let filtMenu = false;
  let activeFilter = null;
  let emptyAfterType = null;
  let nAfterType = null;
  // ⭐⭐⭐⭐⭐ before 必须在**同一个 check 内**自采 ⇒ ⇒ 否则判据只能去比
  //   **另一个 check** 的字段 ⇒ ⇒ 而那个字段未必存在 ⇒ ⇒ `None != None`
  //   ⇒ ⇒ ⇒ 恒假 ⇒ ⇒ ⇒ 那不是「产品坏了」，是**判据在比一个不存在的东西**。
  const emptyBeforeType = await readEmpty();
  const nBeforeType = await readCount();
  if (await filtBtn.count()) {
    await filtBtn.first().click();
    await page.waitForTimeout(400);
    const items = page.locator('[aria-label="素材类型"] [role="menuitemradio"]');
    if (await items.count()) {
      filtMenu = true;
      await items.nth(1).click(); // 视频
      await page.waitForTimeout(500);
      activeFilter = await page.evaluate(() => {
        const m = document.querySelector('[data-testid="jimeng-assets-modal"]');
        if (!m) return null;
        // ⚠️⭐⭐ 读「当前高亮的那个」而不是「第一个」——
        //   筛选行永远是 图片/视频/音频/文档 四个，取第一个永远得到「图片」
        //   ⇒ ⇒ 那不是产品没变，是**量错了**（「量错了 ≠ 产品坏了」）。
        //   复刻侧的高亮标记 = 按钮里那枚 active 下划线 span。
        const btns = Array.from(m.querySelectorAll('[data-testid^="assets-filter-"]'));
        const active = btns.find((b) => b.querySelector('span.absolute'));
        return active ? (active.textContent || '').trim() : null;
      });
      emptyAfterType = await readEmpty();
      nAfterType = await readCount();
    }
  }
  record('assets_type_filter_changes_state', {
    ok: modalUp > 0 && filtMenu && activeFilter === '视频'
        && (emptyAfterType !== emptyBeforeType || nAfterType !== nBeforeType),
    modal_open: modalUp > 0,
    menu_opened: filtMenu,
    active_filter_row: activeFilter,
    empty_before: emptyBeforeType,
    empty_after_type_switch: emptyAfterType,
    n_items_before: nBeforeType,
    n_items_after: nAfterType,
  });
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
}

// ── 7) 局部重拍面板：模型钮 / 时长钮 / 添加参考图 ────────────────────
{
  // 局部重拍要先进「有画面」的视频节点的工具条
  const okSel = await selectNode('video', 0);
  const repaintClicked = await clickBtnByText('局部重拍');
  await page.waitForTimeout(900);
  const panelUp = await visible('添加参考图');

  // 模型钮：真开下拉、真换模型（触发钮的可访问名来自它自己的文案）
  const modelTrigger = page.locator('button', { hasText: '即梦 Seedance 2.5' });
  // （触发钮的可访问名来自它自己的文案「即梦 Seedance 2.5」，没有 aria-label）
  let modelList = 0;
  let modelText = null;
  if (await modelTrigger.count()) {
    await modelTrigger.first().click();
    await page.waitForTimeout(450);
    const opts = page.locator('[aria-label="重拍模型"] [role="option"]');
    modelList = await opts.count();
    if (modelList >= 2) {
      await opts.nth(1).click();
      await page.waitForTimeout(450);
      modelText = await page.evaluate(() => {
        const m = document.querySelector('[aria-label="重拍模型"]');
        return m ? null : null;
      });
      modelText = await page.evaluate(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const t = btns.find((b) => (b.textContent || '').includes('Seedance 2.0'));
        return t ? (t.textContent || '').trim().slice(0, 24) : null;
      });
    }
  }
  record('repaint_model_switches', {
    ok: panelUp && modelList >= 2 && !!modelText,
    panel_open: panelUp,
    n_options: modelList,
    trigger_text_after: modelText,
    repaint_clicked: repaintClicked,
  });

  // 时长钮：真开档、真换时长
  const durTrigger = page.locator('button', { hasText: /^\s*6s\s*$/ });
  let durList = 0;
  let durText = null;
  if (await durTrigger.count()) {
    await durTrigger.first().click();
    await page.waitForTimeout(450);
    const opts = page.locator('[aria-label="重拍时长"] [role="option"]');
    durList = await opts.count();
    if (durList >= 2) {
      await opts.nth(0).click();
      await page.waitForTimeout(450);
      durText = await page.evaluate(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const t = btns.find((b) => (b.textContent || '').trim() === '4s');
        return t ? '4s' : null;
      });
    }
  }
  record('repaint_duration_switches', {
    ok: panelUp && durList >= 2 && durText === '4s',
    panel_open: panelUp,
    n_options: durList,
    duration_after: durText,
  });

  // 添加参考图 ⇒ 真 file input ⇒ 真落节点
  const before = await nodeCount();
  let chooserSeen = false;
  let added = false;
  try {
    const [chooser] = await Promise.all([
      page.waitForEvent('filechooser', { timeout: 6000 }),
      btn('添加参考图').first().click(),
    ]);
    chooserSeen = true;
    await chooser.setFiles(UPLOAD_FILE);
    await page.waitForTimeout(1200);
    added = (await nodeCount()) === before + 1;
  } catch (e) {
    added = false;
  }
  record('repaint_upload_adds_node', {
    ok: chooserSeen && added,
    filechooser_fired: chooserSeen,
    nodes_before: before,
    nodes_after: await nodeCount(),
  });

  await page.keyboard.press('Escape');
  await page.waitForTimeout(600);
}

// ── 8) 视频编辑模式：上传参考内容 / 引用参考 ──────────────────────────
{
  const okSel = await selectNode('video', 0);
  const editClicked = await clickBtnByText('视频编辑');
  await page.waitForTimeout(900);
  const panelUp = await visible('上传参考内容');
  const inView = await ensureInViewport('上传参考内容');

  const before = await nodeCount();
  let chooserSeen = false;
  let added = false;
  try {
    const [chooser] = await Promise.all([
      page.waitForEvent('filechooser', { timeout: 8000 }),
      btn('上传参考内容').first().click({ timeout: 12000 }),
    ]);
    chooserSeen = true;
    await chooser.setFiles(UPLOAD_FILE);
    await page.waitForTimeout(1200);
    added = (await nodeCount()) === before + 1;
  } catch (e) {
    added = false;
  }
  record('video_edit_upload_adds_node', {
    ok: chooserSeen && added,
    panel_open: panelUp,
    panned_into_viewport: inView,
    edit_clicked: editClicked,
    filechooser_fired: chooserSeen,
    nodes_before: before,
    nodes_after: await nodeCount(),
  });

  await ensureInViewport('引用参考');
  await checkRefPick('video_edit_quote_ref_enters_pick_mode', '引用参考', 0);

  await page.keyboard.press('Escape');
  await page.waitForTimeout(600);
}

out.pageerrors = [...new Set(pageErrors)];
out.n_checks = Object.keys(out.checks).length;
out.n_failed = Object.values(out.checks).filter((c) => !c.ok).length;
writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log(
  '\nchecks=%d failed=%d pageerrors=%d -> %s',
  out.n_checks,
  out.n_failed,
  out.pageerrors.length,
  OUT,
);
await browser.close();
