// 批次 84 · B：a 轮的关键格没测到 —— `keyGuard` 挡住了我要观测的那次按键。
//
// a 轮流程：点开抽屉 → 点输入框 → `keyGuard(p)` 返回 **safe:false**
// （焦点在 `DIV aria="说说你的想法或任务…"`）⇒ `if (g1.safe)` 分支整段跳过，
// `gInDrawer` / `fInDrawer` **根本没产出**。
//
// 🔑 这就是批次 82 那条「**门能变红才有价值**」的镜像：
//    守卫的用途是**保护我不误按**，而这一次我要观测的恰恰是「按了会怎样」。
//    ⇒ 观测「焦点在别处时快捷键失效」**必须绕过守卫**。
//    绕过是有代价的（键可能进输入框变成文字），所以必须**同时读输入框内容**，
//    用来区分「键被输入框吃掉了」和「键到了画布但画布没反应」——**这两种都表现为静默**。
//
// 本轮三个对照格，全部**绕过 keyGuard**：
//   ① 焦点在 **prompt-composer**（Agent 输入框）→ 按 G / 按 F
//   ② 焦点在 **canvas-sidecar-launcher**（点「收起」之后的落点）→ 按 G
//   ③ 焦点在 **canvas-main-region**（按 ⌘/ 关闭之后的落点）→ 按 G
//
// 🔑 ②③ 之所以要对照：a 轮发现**两条关闭路径的焦点落点不同**——
//    点「收起」钮 → 焦点回右下角启动钮；
//    按 ⌘/ → 批次 82 实测回 `SECTION[canvas-main-region] aria="Canvas editing area"`。
//    如果只有 ②③ 之一有效，结论就会是「收起之后快捷键不能用」；
//    两者都有效则是「**任何时候焦点都不在画布上时都不能用**」。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const selCount = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const toast = () => p.evaluate(() => { const c = Array.from(document.querySelectorAll('div,span'))
    .filter((x) => /此快捷键当前不可用/.test((x.innerText || '').trim()) && x.children.length <= 2);
  const e = c.sort((a, b2) => b2.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
  if (!e) return null; const r = e.getBoundingClientRect();
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, text: (e.innerText || '').trim() }; });
const visCount = () => p.evaluate(() => { let n = 0;
  for (const e of document.querySelectorAll('*')) { const r = e.getBoundingClientRect(); if (r.width > 0 && r.height > 0) n++; } return n; });
const fsDialog = () => p.evaluate(() => { const e = document.querySelector('[data-testid="text-editor-fullscreen-dialog"]');
  if (!e) return null; const r = e.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; });
const focusInfo = () => keyGuard(p);
/** 🔑 读输入框内容 + 读画布侧栏开合，用来区分「键被吃了」还是「键到了画布」。 */
const pmText = () => p.evaluate(() => { const e = document.querySelector('[data-testid="prompt-composer"] .ProseMirror');
  return e ? { text: (e.innerText || '').replace(/\n/g, '|').slice(0, 24), html: (e.innerHTML || '').slice(0, 90) } : null; });
const drawerOpen = () => p.evaluate(() => {
  const s = document.querySelector('[data-testid="canvas-feature-sidecar"]'); if (!s) return null;
  const r = s.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; });
const waitToast = async () => { for (const d of [300, 700, 1500]) { await p.waitForTimeout(d); const t = await toast(); if (t) return { toast: t, afterMs: d }; } return { toast: null, afterMs: 2500 }; };

/** 🔑 绕过 keyGuard 直接按一个字母键，同时记录「输入框拿到了什么」和「画布有没有反应」。 */
const pressRaw = async (key) => {
  const before = { sel: await selCount(), vis: await visCount(), fs: await fsDialog(), pm: await pmText(), drawer: await drawerOpen() };
  await p.keyboard.press(key);                       // 故意不过 keyGuard
  const w = await waitToast();
  const after = { sel: await selCount(), vis: await visCount(), fs: await fsDialog(), pm: await pmText(), drawer: await drawerOpen() };
  const all = Object.fromEntries(Object.keys(before).map((k) =>
    [k, JSON.stringify(before[k]) === JSON.stringify(after[k]) ? '同'
      : `${JSON.stringify(before[k])}→${JSON.stringify(after[k])}`]));
  return { key, before, after, toast: w.toast, toastAfterMs: w.afterMs, sampledToMs: 2500,
    changed: Object.entries(all).filter(([, v]) => v !== '同') };
};

try {
  out.grids = {};
  // ══════ 格 ① 焦点在 Agent 输入框 ══════
  // 🔑 抽屉可能已经是折叠态（上一轮留下的）。先读状态，再决定是「开」还是「先开再点」。
  const st0 = await drawerOpen();
  log('进场抽屉', st0);
  if (st0 && st0.startsWith('200x348')) {                       // 折叠 ⇒ 先用 ⌘/ 展开
    await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1800);
    log('⌘/ 展开后', await drawerOpen());
  } else {                                                      // 已展开 ⇒ 用收起再展开，保证干净起点
    const cb0 = await p.evaluate(() => { const s = document.querySelector('[data-testid="canvas-feature-sidecar"]');
      const b = s && Array.from(s.querySelectorAll('button,[role="button"]')).find((x) => /收起|折叠|collapse/i.test((x.getAttribute('aria-label') || '') + (x.innerText || '')));
      if (!b) return null; const r = b.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
    if (cb0) { await p.mouse.click(cb0.x, cb0.y); await p.waitForTimeout(1600); log('收起后', await drawerOpen()); }
    await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1800); log('⌘/ 展开后', await drawerOpen());
  }
  out.openState = { drawer: await drawerOpen(), focus: await focusInfo() };
  log('抽屉打开', JSON.stringify(out.openState));
  const pt = await p.evaluate(() => { const e = document.querySelector('[data-testid="prompt-composer"] .ProseMirror');
    if (!e) return null; const r = e.getBoundingClientRect(); return { x: Math.round(r.x + 20), y: Math.round(r.y + 20) }; });
  if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1000); }
  out.grids['①焦点在输入框'] = { focus: await focusInfo(), pm: await pmText() };
  log('格① 前置', JSON.stringify(out.grids['①焦点在输入框']));
  out.grids['①按G'] = await pressRaw('g');
  log('格① 按 G →', JSON.stringify(out.grids['①按G']));
  out.grids['①按F'] = await pressRaw('f');
  log('格① 按 F →', JSON.stringify(out.grids['①按F']));

  // ══════ 格 ② 点「收起」→ 焦点在启动钮 ══════
  const cb = await p.evaluate(() => { const side = document.querySelector('[data-testid="canvas-feature-sidecar"]'); if (!side) return null;
    const b = Array.from(side.querySelectorAll('button,[role="button"]')).find((x) => /收起|折叠|collapse/i.test((x.getAttribute('aria-label') || '') + (x.innerText || '')));
    if (!b) return null; const r = b.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (cb) { await p.mouse.click(cb.x, cb.y); await p.waitForTimeout(1800); }
  out.grids['②收起后'] = { drawer: await drawerOpen(), focus: await focusInfo(), pm: await pmText() };
  log('格② 前置', JSON.stringify(out.grids['②收起后']));
  out.grids['②按G'] = await pressRaw('g');
  log('格② 按 G →', JSON.stringify(out.grids['②按G']));

  // ══════ 格 ③ 按 ⌘/ 关闭 → 焦点在画布主区 ══════
  await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1800);
  out.grids['③⌘/收起后'] = { drawer: await drawerOpen(), focus: await focusInfo(), pm: await pmText() };
  log('格③ 前置', JSON.stringify(out.grids['③⌘/收起后']));
  out.grids['③按G'] = await pressRaw('g');
  log('格③ 按 G →', JSON.stringify(out.grids['③按G']));
  out.grids['③按F'] = await pressRaw('f');
  log('格③ 按 F →', JSON.stringify(out.grids['③按F']));

  // ══════ 格 ④ 阳性对照：点画布空白 + 选中一个节点 + 焦点在画布 ══════
  await p.evaluate(() => { const pane = document.querySelector('.react-flow__pane');
    for (let y = 110; y < 660; y += 20) for (let x = 210; x < 1240; x += 28) { const h = document.elementFromPoint(x, y);
      if (h && pane.contains(h)) { pane.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: x, clientY: y }));
        pane.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, clientX: x, clientY: y })); return; } } });
  await p.waitForTimeout(900);
  out.grids['④点画布空白'] = { focus: await focusInfo(), sel: await selCount() };
  log('格④ 前置', JSON.stringify(out.grids['④点画布空白']));
  out.grids['④按G'] = await pressRaw('g');
  log('格④ 按 G →', JSON.stringify(out.grids['④按G']));

  out.end = { status: await status() };
  log('终态', JSON.stringify(out.end));
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
writeFileSync(new URL('./_tmp-b84b.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
