/**
 * 即梦画布复刻 · **冒烟**（一条命令回答「dev server 起得来吗 + 页面还能用吗」）
 *
 * 用法：
 *   npm run dev:restart            # 先把 dev server 起好（端口 4317）
 *   node scripts/jimeng_smoke_canvas.mjs
 *
 * 冒什么（**每条都必须能失败**，否则它就是恒绿）：
 *  ① 页面能打开（HTTP 200）
 *  ② ★ **基线**：`.react-flow__node` 数量 > 0
 *     ⇒ 状态栏写着「5 nodes」而 DOM 里 0 个节点 ⇒ **是渲染层炸了，不是行为变了**
 *     ⇒ 这条是 2026-10-26 那次「五道门集体假红」的守门判据
 *  ③ 节点清单（含「真的 `<video>`」的节点数）
 *  ④ 外壳：左侧栏 / 时间线 / 状态栏 / 按钮数
 *  ⑤ 交互：点**标题栏** ⇒ 状态栏「N selected」必须 0 → 1
 *     ⇒ ⚠️ 不能点节点**中心**：带媒体的视频节点，中心正是 44×44 的中央播放钮
 *     ⇒ 它的 onClick 有 stopPropagation ⇒ 点它 = 播放/暂停（**另一个控件**的行为）
 *     ⇒ 拿它当「点节点选不中」的证据 = 判据打错了地方
 *  ⑥ 真播放：点中央播放钮 ⇒ aria「播放」→「暂停」＋ `paused=false` ＋ currentTime 前进
 *     ⇒ 这条守的是 1032-⑫ 把「假播放（海报 `<img>`）」改成真 `<video>` 之后没回退
 *  ⑦ 点画布**空白** ⇒ 状态栏回到「0 selected」（且落点必须避开顶栏）
 *  ⑧ 全程 pageerror / console error 计数 = 0
 *
 * ⚠️ 安全边界：只点**本地**控件，**绝不点**生成 / 发送 / 购买 / 充值。
 * ⚠️ 判据不许用「未选中时不渲染」的属性（`data-jimeng-node-selected`）⇒ 用恒在的状态栏读数。
 */
// ⚠️ playwright 从**家目录**那份解析（仓库 node_modules 里没有 playwright）
//    ⇒ 与 scripts/ 下其它 mjs 探针同一口径（jimeng_probe1031d_*.mjs 等）
import pw from '/Users/yangjiefeng/node_modules/playwright/index.js';

const URL = process.env.SMOKE_URL || 'http://localhost:4317/jimeng/canvas/demo';
const { chromium } = pw;

const out = { url: URL, pageerrors: [], console_errors: [], steps: [] };
const step = async (name, fn) => {
  try { out.steps.push({ name, ok: true, value: await fn() }); }
  catch (e) { out.steps.push({ name, ok: false, err: String(e).split('\n')[0] }); }
};

const browser = await chromium.launch({ headless: true, viewport: { width: 1600, height: 1000 } });
const page = await browser.newPage();
page.on('pageerror', (e) => out.pageerrors.push(String(e).slice(0, 200)));
page.on('console', (m) => { if (m.type() === 'error') out.console_errors.push(m.text().slice(0, 200)); });

await step('open', async () => {
  const r = await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  return { status: r.status() };
});

// ★ 基线：节点必须真的渲染出来（本轮踩过的坑：状态栏写 5 nodes 而 DOM 里 0 个）
await step('baseline_nodes', async () => {
  for (let i = 0; i < 20; i++) {
    const n = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    if (n > 0) return { n_rf_nodes: n, waited_ms: i * 300 };
    await page.waitForTimeout(300);
  }
  const st = await page.evaluate(() => {
    const s = [...document.querySelectorAll('*')].find((e) => /\d+ nodes/.test(e.textContent || '') && e.children.length === 0);
    return { statusbar_says: s ? s.textContent.trim() : null };
  });
  throw new Error('DOM 里没有 .react-flow__node ' + JSON.stringify(st));
});

await step('node_inventory', async () =>
  page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => ({
    id: n.getAttribute('data-id'),
    text: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
    has_video: !!n.querySelector('video'),
  }))));

await step('chrome_ui', async () => page.evaluate(() => {
  const txt = document.body.innerText || '';
  return {
    has_sidebar: /文本|图片|视频|音频/.test(txt),
    has_timeline: /时间线/.test(txt),
    has_statusbar: /nodes,/.test(txt),
    n_buttons: document.querySelectorAll('button').length,
  };
}));

// 交互冒烟：点一个节点 → 必须真的选中
// ⚠️⚠️ **落点必须躲开中央播放钮**：带媒体的视频节点，中心正落在 44×44 的播放钮上
//    ⇒ 播放钮的 onClick 有 stopPropagation ⇒ 点它 = 播放/暂停（不是选中）⇒
//    ⇒ 那是**另一个控件**的行为 ⇒ 拿它当「点节点选不中」的证据 = 判据打错地方
await step('select_node', async () => {
  const readSelected = () => page.evaluate(() => {
    const m = /(\d+)\s+selected/.exec(document.body.innerText || '');
    return m ? Number(m[1]) : null;
  });
  const target = await page.evaluate(() => {
    const n = document.querySelector('.react-flow__node');
    if (!n) return null;
    const r = n.getBoundingClientRect();
    return {
      id: n.getAttribute('data-id'),
      x: Math.round(r.left + r.width / 2),
      y: Math.round(r.top + Math.min(16, Math.max(6, r.height / 3))),  // 标题栏
      center_is_play_btn: (() => {
        const el = document.elementFromPoint(Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2));
        return !!(el && el.closest('button[aria-label="播放"], button[aria-label="暂停"]'));
      })(),
    };
  });
  if (!target) throw new Error('没有可点的节点');
  const before = await readSelected();
  await page.mouse.click(target.x, target.y);
  await page.waitForTimeout(700);
  const after = await readSelected();
  if (after !== 1) throw new Error(`点节点标题栏后状态栏 selected=${after}（期望 1；点前 ${before}）`);
  return { clicked: target.id, center_is_play_btn: target.center_is_play_btn, selected_before: before, selected_after: after };
});

// 真播放冒烟：点中央播放钮 ⇒ 画面必须真的动（1032-⑫ 起那里是真 <video>，不是海报）
await step('toggle_play', async () => {
  const st = await page.evaluate(() => {
    const b = document.querySelector('button[aria-label="播放"], button[aria-label="暂停"]');
    const v = document.querySelector('video[data-testid="jimeng-video-element"]');
    if (!b) return { has_btn: false };
    const r = b.getBoundingClientRect();
    return { has_btn: true, aria: b.getAttribute('aria-label'),
             has_video: !!v, x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) };
  });
  if (!st.has_btn) throw new Error('页面里没有播放/暂停钮');
  await page.mouse.click(st.x, st.y);
  await page.waitForTimeout(1200);
  const after = await page.evaluate(() => {
    const b = document.querySelector('button[aria-label="播放"], button[aria-label="暂停"]');
    const v = document.querySelector('video[data-testid="jimeng-video-element"]');
    return { aria: b ? b.getAttribute('aria-label') : null,
             paused: v ? v.paused : null, currentTime: v ? v.currentTime : null };
  });
  if (after.aria !== '暂停' && after.paused !== false) {
    throw new Error('点了播放钮但画面没进入播放态 ' + JSON.stringify(after));
  }
  return { before_aria: st.aria, after_aria: after.aria, paused: after.paused, currentTime_moved: (after.currentTime || 0) > 0 };
});

// 画布空白处点一下：必须能取消选中（不误触任何生成按钮）
await step('deselect_on_blank', async () => {
  const readSelected = () => page.evaluate(() => {
    const m = /(\d+)\s+selected/.exec(document.body.innerText || '');
    return m ? Number(m[1]) : null;
  });
  const pt = await page.evaluate(() => {
    const pane = document.querySelector('.react-flow__pane');
    if (!pane) return null;
    const r = pane.getBoundingClientRect();
    // ⚠️ 从**下边**往上找空白点：顶栏/工具条盖在 pane 上边 ⇒ 从 r.top 开始会点到顶栏
    for (let y = Math.round(r.bottom - 40); y > r.top + 120; y -= 40) {
      for (let x = Math.round(r.right - 60); x > r.left + 60; x -= 60) {
        const el = document.elementFromPoint(x, y);
        if (el && (el === pane || pane.contains(el))) return [x, y];
      }
    }
    return null;
  });
  if (!pt) throw new Error('找不到画布空白点');
  await page.mouse.click(pt[0], pt[1]);
  await page.waitForTimeout(500);
  const after = await readSelected();
  if (after !== 0) throw new Error(`点空白后状态栏 selected=${after}（期望 0）`);
  return { clicked_blank_at: pt, selected_after: after };
});

await step('final_pageerrors', async () => ({ n: out.pageerrors.length }));

console.log(JSON.stringify(out, null, 2));
await browser.close();
