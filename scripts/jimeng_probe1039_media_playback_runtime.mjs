/**
 * 1032-⑫ 运行时探针：媒体播放页的**当前行为**（复刻侧）。
 *
 * 这道探针回答的是「用户手册 10-tasks/media-playback.md 描述的那套操作，
 * 在**当前这版复刻**上到底成不成立」。
 *
 * ⚠️⚠️ 三条纪律：
 *  ① 产物里**不许出现随机量**（时间戳 / currentTime / pid / 耗时）
 *     ⇒ ⇒ 凡是会随时间漂的读数，一律折成**布尔**或**计数**；
 *  ② 只点**本地**控件；**绝不点生成 / 发送 / 购买 / 充值**；
 *  ③ 定位节点**不能**靠 `data-jimeng-node-selected` / `data-group-id`
 *     —— 未选中的节点**这两个属性都不渲染** ⇒ 上一版探针因此报
 *     「页面里没有 <video>」（**探针自己的错**，不是页面的）。
 *     ⇒ ⇒ 一律用 `.react-flow__node`。
 *
 * 产物：docs/research/jimeng-canvas/inputs/media-playback-runtime-1039.json
 */
import pw from '/Users/yangjiefeng/node_modules/playwright/index.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';
import { createRequire } from 'module';
import os from 'os';

// ⚠️ typescript 从**仓库自己的** node_modules 解析（不写死绝对路径 ⇒ 换机不炸）
const require = createRequire(import.meta.url);
const ts = require('typescript');

const { chromium } = pw;
const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, '..');
const OUT = process.env.JIMENG_MEDIA_JSON
  || resolve(REPO_ROOT, 'docs/research/jimeng-canvas/inputs/media-playback-runtime-1039.json');
fs.mkdirSync(dirname(OUT), { recursive: true });

const URL = 'http://localhost:4317/jimeng/canvas/demo';

/* ── 浏览器侧读数（每次 evaluate 都是自包含函数） ─────────────────── */
const SNAP = `() => {
  const rect = (el) => { if (!el) return null; const r = el.getBoundingClientRect();
    return [Math.round(r.width * 100) / 100, Math.round(r.height * 100) / 100]; };
  const v = document.querySelector('video[data-testid="jimeng-video-element"]');
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const base = { n_rf_nodes: nodes.length, n_video_elements: document.querySelectorAll('video[data-testid="jimeng-video-element"]').length };
  if (!v) return { ...base, found: false };
  const node = v.closest('.react-flow__node');
  const wrap = node.querySelector('[data-jimeng-video-has-media], [data-jimeng-node-selected]');
  const central = node.querySelector('button[aria-label="播放"], button[aria-label="暂停"]');
  const bar = [...node.querySelectorAll('div')].find((d) =>
    String(d.className).includes('from-black/55'));
  const timeSpan = [...node.querySelectorAll('span')].find((s) =>
    /\\d:\\d\\d\\s*\\/\\s*\\d:\\d\\d/.test(s.textContent || ''));
  return { ...base, found: true,
    selected_attr: wrap ? (wrap.getAttribute('data-jimeng-node-selected') || 'false') : null,
    has_media_anchor: !!(node.querySelector('[data-jimeng-video-has-media]')),
    video_paused: v.paused,
    video_muted: v.muted,
    central_aria: central ? central.getAttribute('aria-label') : null,
    central_screen_px: rect(central),
    bar_present: !!bar,
    bar_opacity: bar ? getComputedStyle(bar).opacity : null,
    time_text_present: !!timeSpan,
    time_text_shape: timeSpan ? (timeSpan.innerText || '').replace(/[0-9]/g, '#') : null,
    node_button_arias: [...node.querySelectorAll('button')].map((b) => b.getAttribute('aria-label') || ''),
  };
}`;

/** 画布缩放：屏上像素 ÷ 缩放 = 100% 档的「画布像素」（源站读数用的就是这套单位）。 */
const SCALE = `() => {
  const vp = document.querySelector('.react-flow__viewport');
  if (!vp) return null;
  const t = getComputedStyle(vp).transform;
  if (!t || t === 'none') return 1;
  const m = t.match(/matrix\\(([^,]+)/);
  return m ? parseFloat(m[1]) : null;
}`;

const CTX = `() => {
  const m = document.querySelector('[data-testid="canvas-context-menu"]');
  if (!m) return { present: false };
  const b = m.getBoundingClientRect();
  const items = [...m.querySelectorAll('[role="menuitem"]')].map((n) => ({
    text: (n.innerText || '').replace(/\\s+/g, ' ').trim(),
    disabled: n.disabled === true || n.getAttribute('aria-disabled') === 'true',
  }));
  return { present: true, box: [Math.round(b.width), Math.round(b.height)], items };
}`;

const PREVIEW = `() => {
  const layer = document.querySelector('[data-testid="video-fullscreen-preview"]');
  if (!layer) return { present: false };
  const v = layer.querySelector('video[data-testid="jimeng-video-preview-element"]');
  const sl = layer.querySelector('[role="slider"]');
  return { present: true,
    has_video_element: !!v,
    video_paused: v ? v.paused : null,
    n_sliders: layer.querySelectorAll('[role="slider"]').length,
    slider_aria_label: sl ? sl.getAttribute('aria-label') : null,
    slider_aria_min: sl ? sl.getAttribute('aria-valuemin') : null,
    slider_aria_max: sl ? sl.getAttribute('aria-valuemax') : null,
    slider_aria_now: sl ? sl.getAttribute('aria-valuenow') : null,
    slider_screen_px: sl ? (() => { const r = sl.getBoundingClientRect();
      return [Math.round(r.width * 100) / 100, Math.round(r.height * 100) / 100]; })() : null,
    buttons: [...layer.querySelectorAll('button')].map((b) => b.getAttribute('aria-label') || ''),
  };
}`;

const VOL = `() => {
  const sl = document.querySelector('[data-testid="preview-volume-slider"]');
  const v = document.querySelector('video[data-testid="jimeng-video-preview-element"]');
  return { valuenow: sl ? sl.getAttribute('aria-valuenow') : null,
           video_volume: v ? v.volume : null };
}`;

const out = { generated_by: 'scripts/jimeng_probe1039_media_playback_runtime.mjs', pageerrors: [] };
const errors = [];

/* ── 静态普查：带交互 ARIA role 却**零事件处理器**的元素 ─────────────
 *  ⭐⭐⭐⭐⭐ 为什么单独立一条：
 *   1034 的假交互扫描器 R1 只扫**带事件属性**的元素 ⇒
 *   ⇒ **一个处理器都没有的元素压根不在候选集里** ⇒
 *   ⇒ 此前那枚「音量滑杆」（role="slider" + 写死 aria-valuenow + 零 handler）
 *   ⇒ ⇒ 假交互普查**结构上**看不见它。
 *   ⇒ ⇒ 这里补一条**独立**判据把这个盲区盖住。
 */
const ARIA_WIDGET_ROLES = new Set([
  'slider', 'spinbutton', 'checkbox', 'radio', 'switch', 'tab', 'option',
  'menuitem', 'menuitemcheckbox', 'menuitemradio', 'treeitem', 'scrollbar',
  'textbox', 'searchbox',
]);
const EVENT_ATTRS = new Set([
  'onClick', 'onDoubleClick', 'onPointerDown', 'onPointerMove', 'onPointerUp',
  'onPointerCancel', 'onMouseDown', 'onMouseUp', 'onMouseMove', 'onKeyDown',
  'onKeyUp', 'onChange', 'onInput', 'onTouchStart', 'onTouchMove', 'onDragStart',
]);
/* ⭐ 祖先**委托**只认「指针/键盘类」处理器：
 *   祖先只有 onClick/onDoubleClick ⇒ **接不住**滑杆的拖动
 *   ⇒ ⇒ 不算「活的」（否则媒体卡外层的 onDoubleClick 会把死滑杆洗白）。
 */
const POINTER_ATTRS = new Set([
  'onPointerDown', 'onPointerMove', 'onPointerUp', 'onPointerCancel',
  'onMouseDown', 'onMouseUp', 'onMouseMove', 'onTouchStart', 'onTouchMove',
  'onKeyDown', 'onKeyUp', 'onChange', 'onInput', 'onDragStart',
]);
function ariaDeadCensus(rootDir) {
  const out = [];
  const walk = (dir) => {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) walk(p);
      else if (e.name.endsWith('.tsx')) {
        const text = fs.readFileSync(p, 'utf8');
        const sf = ts.createSourceFile(p, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
        const rel = path.relative(rootDir, p);
        const visit = (node, ancPointer) => {
          // ⭐⭐⭐⭐⭐ **自闭合元素也是 JSX 元素** —— 第一版只判 `isJsxElement`
          //   ⇒ ⇒ `<span role="slider" ... />`（自闭合）**整类被漏掉**
          //   ⇒ ⇒ 而整改前那枚音量滑杆**恰恰是自闭合的**
          //   ⇒ ⇒ 阳性对照（合成死滑杆）当场把这条打红了 ⇒ 才修掉。
          const open = ts.isJsxElement(node) ? node.openingElement
            : (ts.isJsxSelfClosingElement(node) ? node : null);
          let ownPointer = false;
          if (open) {
            const tag = open.tagName.getText();
            let role = null, hasEvent = false, hasSpread = false, label = '';
            for (const a of open.attributes.properties) {
              if (ts.isJsxSpreadAttribute(a)) { hasSpread = true; continue; }
              const nm = a.name.getText();
              if (EVENT_ATTRS.has(nm)) hasEvent = true;
              if (POINTER_ATTRS.has(nm)) ownPointer = true;
              if (nm === 'role' && a.initializer && ts.isStringLiteral(a.initializer)) {
                role = a.initializer.text;
              }
              if (nm === 'aria-label' && a.initializer && ts.isStringLiteral(a.initializer)) {
                label = a.initializer.text;
              }
            }
            // ⭐ button/a 归 1034 的 R1 管（它们天然可点），本普查只看**非按钮**的 ARIA 控件
            if (role && ARIA_WIDGET_ROLES.has(role) && !hasEvent && !hasSpread
                && !ownPointer && !ancPointer && tag !== 'button' && tag !== 'a') {
              const { line } = sf.getLineAndCharacterOfPosition(open.getStart(sf));
              out.push({ file: rel, line: line + 1, tag, role, aria_label: label });
            }
          }
          const next = ancPointer || ownPointer;
          for (const ch of node.getChildren()) visit(ch, next);
        };
        visit(sf, false);
      }
    }
  };
  walk(path.join(rootDir, 'src/components/jimeng'));
  out.sort((a, b) => (a.file + a.line).localeCompare(b.file + b.line));
  return out;
}
out.aria_dead_census = ariaDeadCensus(REPO_ROOT);

/* ⭐⭐⭐⭐⭐ 普查器自身的**阳性对照**：
 *   「这条判据能不能失败」必须当场证明 ⇒
 *   ⇒ 在**临时副本**里塞一枚**合成的死滑杆**（role=slider + 零处理器）
 *   ⇒ ⇒ 普查必须把它捞出来（捞不出来 ⇒ 这条判据是瞎的）。
 * ⚠️ 只在**副本**上做 ⇒ 仓库里的文件一个字节都不动。
 * ⚠️ 产物里只记**布尔与计数** ⇒ 临时路径不进产物。
 */
out.aria_dead_census_selftest = (() => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'jimeng-aria-selftest-'));
  try {
    const src = path.join(REPO_ROOT, 'src/components/jimeng');
    // ⚠️ 副本必须落在**同样的相对路径**上（普查器按 `<root>/src/components/jimeng` 走）
    const dst = path.join(tmp, 'src/components/jimeng');
    fs.mkdirSync(path.dirname(dst), { recursive: true });
    fs.cpSync(src, dst, { recursive: true });
    fs.writeFileSync(
      path.join(dst, '__selftest_dead_widget.tsx'),
      'export const SelftestDead = () => (\n'
      + '  <span role="slider" aria-label="合成死滑杆" aria-valuenow={1} />\n'
      + ');\n\n'
      // 阴性对照：祖先**有**指针处理器 ⇒ 这枚滑杆是**活的**（委托给祖先）
      // ⇒ 普查**不许**把它算成死的（否则就是过报 ⇒ 假红）。
      + 'export const SelftestDelegated = () => (\n'
      + '  <div onPointerDown={() => {}}>\n'
      + '    <span role="slider" aria-label="合成委托滑杆" aria-valuenow={1} />\n'
      + '  </div>\n'
      + ');\n',
      'utf8',
    );
    const cands = ariaDeadCensus(tmp);
    const hit = cands.filter((c) => c.file.includes('__selftest_dead_widget')
      && c.aria_label === '合成死滑杆');
    const delegated = cands.filter((c) => c.aria_label === '合成委托滑杆');
    return {
      detects_dead_widget: hit.length > 0,
      ignores_delegated_widget: delegated.length === 0,
      n_candidates_in_copy: cands.length,
      detected_role: hit.length ? hit[0].role : null,
      note: '⭐ 合成坏样本只在临时副本里 ⇒ 仓库零污染；本字段只记布尔与计数。',
    };
  } catch (e) {
    return { detects_dead_widget: false, error: String(e).slice(0, 160) };
  } finally {
    try { fs.rmSync(tmp, { recursive: true, force: true }); } catch (e) { /* 清理失败不致命 */ }
  }
})();

/* ── 浏览器侧 ─────────────────────────────────────────────────────── */
const browser = await chromium.launch({ headless: true, viewport: { width: 1600, height: 1000 } });
const page = await browser.newPage();
page.on('pageerror', (e) => out.pageerrors.push(String(e).slice(0, 200)));

const step = async (name, fn) => {
  try { return await fn(); } catch (e) { errors.push({ step: name, err: String(e).split('\n')[0] }); return null; }
};
const snap = async (label) => {
  for (let i = 0; i < 8; i++) {
    const r = await page.evaluate(eval(SNAP)).catch(() => null);
    if (r && r.found) { r.label = label; return r; }
    await page.waitForTimeout(300);
  }
  const r = await page.evaluate(eval(SNAP)).catch(() => ({ found: false }));
  r.label = label; r.note = 'exhausted-retries';
  return r;
};

await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
await page.waitForSelector('video[data-testid="jimeng-video-element"]', { timeout: 30000 });
await page.waitForTimeout(900);

const states = [];
states.push(await snap('unselected'));

await step('click_play', async () => {
  await page.locator('button[aria-label="播放"]').first().click();
  await page.waitForTimeout(700);
});
states.push(await snap('playing'));

/* 播放中：currentTime 在走吗？（折成布尔，不落易变量） */
out.playing_advances = await step('advance', async () => {
  const a = await page.evaluate(() => document.querySelector('video[data-testid="jimeng-video-element"]').currentTime);
  await page.waitForTimeout(1000);
  const b = await page.evaluate(() => document.querySelector('video[data-testid="jimeng-video-element"]').currentTime);
  return { moved: Math.abs(b - a) > 0.05 };
});

await step('click_pause', async () => {
  await page.locator('button[aria-label="暂停"]').first().click();
  await page.waitForTimeout(400);
});
states.push(await snap('paused'));

/* 取消选中：停播？<video> 还在？ */
await step('deselect', async () => {
  const pt = await page.evaluate(() => {
    const pane = document.querySelector('.react-flow__pane');
    if (!pane) return null;
    const r = pane.getBoundingClientRect();
    for (let y = Math.round(r.top + 20); y < r.bottom - 20; y += 40) {
      for (let x = Math.round(r.left + 20); x < r.right - 20; x += 40) {
        const el = document.elementFromPoint(x, y);
        if (el && (el === pane || pane.contains(el))) return [x, y];
      }
    }
    return null;
  });
  if (!pt) throw new Error('no blank pane point');
  await page.mouse.click(pt[0], pt[1]);
  await page.waitForTimeout(500);
});
states.push(await snap('deselected'));
out.deselect_freezes = await step('freeze', async () => {
  const a = await page.evaluate(() => document.querySelector('video[data-testid="jimeng-video-element"]').currentTime);
  await page.waitForTimeout(900);
  const b = await page.evaluate(() => document.querySelector('video[data-testid="jimeng-video-element"]').currentTime);
  return { frozen: Math.abs(b - a) < 0.05 };
});
out.video_still_in_dom_after_deselect = await page.evaluate(
  () => !!document.querySelector('video[data-testid="jimeng-video-element"]'));

/* 右键菜单：带媒体的视频节点，「下载」是可用态吗？ */
await step('ctx_menu', async () => {
  await page.locator('video[data-testid="jimeng-video-element"]')
    .click({ button: 'right', position: { x: 8, y: 8 } });
  await page.waitForTimeout(500);
  out.ctx_menu = await page.evaluate(eval(CTX));
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);
});

/* 全屏预览 */
await step('preview', async () => {
  await page.locator('video[data-testid="jimeng-video-element"]').click({ position: { x: 8, y: 8 } });
  await page.waitForTimeout(400);
  await page.locator('button[aria-label="全屏预览"]').first().click();
  await page.waitForTimeout(800);
  out.preview = await page.evaluate(eval(PREVIEW));
});

/* 音量滑杆：真能拖吗？ */
out.volume_drag = await step('volume_drag', async () => {
  const before = await page.evaluate(eval(VOL));
  const sl = page.locator('[data-testid="preview-volume-slider"]');
  const b = await sl.boundingBox();
  if (!b) throw new Error('no volume slider box');
  await page.mouse.move(b.x + b.width * 0.8, b.y + b.height / 2);
  await page.mouse.down();
  await page.mouse.move(b.x + b.width * 0.2, b.y + b.height / 2, { steps: 8 });
  await page.mouse.up();
  await page.waitForTimeout(350);
  const after = await page.evaluate(eval(VOL));
  const b0 = Number(before.valuenow), a0 = Number(after.valuenow);
  return {
    aria_changed: before.valuenow !== after.valuenow,
    decreased: a0 < b0,
    /* 落点是否贴近 20%（容差 0.08：轨道的屏上宽度只有 ~38px） */
    landed_near_target: Math.abs(a0 - 0.2) < 0.08,
    video_volume_follows: after.video_volume !== null
      && Math.abs(after.video_volume - a0) < 0.02,
    video_volume_changed: before.video_volume !== after.video_volume,
  };
});

/* 音量滑杆：键盘也能调吗？（role=slider 语义要求可聚焦可操作） */
out.volume_keyboard = await step('volume_keyboard', async () => {
  const before = await page.evaluate(eval(VOL));
  await page.locator('[data-testid="preview-volume-slider"]').focus();
  await page.keyboard.press('ArrowRight');
  await page.waitForTimeout(250);
  const after = await page.evaluate(eval(VOL));
  return { aria_changed: before.valuenow !== after.valuenow,
           increased: Number(after.valuenow) > Number(before.valuenow) };
});

await step('close_preview', async () => {
  await page.locator('button[aria-label="退出全屏预览"]').first().click();
  await page.waitForTimeout(400);
});

/* 画布像素换算：中央播放钮 */
const scale = await page.evaluate(eval(SCALE)).catch(() => null);
out.viewport_scale = scale === null ? null : Math.round(scale * 1000) / 1000;
const un = states[0] || {};
if (un.central_screen_px && scale) {
  out.central_button_canvas_px = [
    Math.round((un.central_screen_px[0] / scale) * 10) / 10,
    Math.round((un.central_screen_px[1] / scale) * 10) / 10,
  ];
} else {
  out.central_button_canvas_px = null;
}
out.states = states.map((s) => ({
  label: s.label,
  selected_attr: s.selected_attr,
  has_media_anchor: s.has_media_anchor,
  central_aria: s.central_aria,
  central_screen_px: s.central_screen_px,
  bar_present: s.bar_present,
  bar_opacity: s.bar_opacity,
  time_text_present: s.time_text_present,
  time_text_shape: s.time_text_shape,
  node_button_arias: s.node_button_arias,
  video_paused: s.video_paused,
  video_muted: s.video_muted,
}));
out.errors = errors;

fs.writeFileSync(OUT, JSON.stringify(out, null, 1) + '\n', 'utf8');
console.log(JSON.stringify({
  central_button_canvas_px: out.central_button_canvas_px,
  playing_advances: out.playing_advances,
  deselect_freezes: out.deselect_freezes,
  video_still_in_dom_after_deselect: out.video_still_in_dom_after_deselect,
  ctx_menu: out.ctx_menu ? { n: out.ctx_menu.items.length,
    download: out.ctx_menu.items.find((i) => i.text.includes('下载')) } : null,
  preview: out.preview,
  volume_drag: out.volume_drag,
  volume_keyboard: out.volume_keyboard,
  aria_dead_census: out.aria_dead_census,
  pageerrors: out.pageerrors,
  errors,
}, null, 1));
await browser.close();
console.log('MEDIA_PLAYBACK_RUNTIME_DONE ->', OUT);
