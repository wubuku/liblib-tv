// 批次 84 · C：① 清掉 b 轮留在 Agent 输入框里的「gf」两个字母；
//                ② 用**真实鼠标点击**做阳性对照（b 轮的 `pane.dispatchEvent` 没生效）。
//
// b 轮的三格已经把机制测清了，本轮只补两件事：
//   ① **清脏**：b 轮为了观测「键去了哪」故意绕过 keyGuard，结果 `g`、`f` 两个字母
//     真的打进了 Agent 输入框（`"<p></p>"` → `"<p>gf</p>"`）。
//     这是**我自己的临时状态**，必须清掉，不能留在共享画布上。
//     用退格逐字删（页面已记：⌘A 在这个输入框里不能全选，会变成在光标处插入）。
//   ② **阳性对照**：b 轮格④ 试图用 `pane.dispatchEvent(new MouseEvent(...))` 把焦点
//     移回画布，**没生效**（焦点仍停在 `ASIDE[canvas-feature-sidecar]`），
//     于是格④ 实际还是「焦点在 ASIDE」而不是「焦点在画布」。
//     本轮用**真实鼠标点击**画布空白，并**断言 `elementFromPoint` 落在 `.react-flow__pane`**，
//     再按 G —— 必须拿到「此快捷键当前不可用」才算对照成立。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard, pressLetter } from './jimeng-safe-keys.mjs';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const selCount = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const zoomLabel = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const zoomPct = async () => { const l = await zoomLabel(); return l ? Number((l.match(/(\d+)%/) || [])[1]) : null; };
const toast = () => p.evaluate(() => { const c = Array.from(document.querySelectorAll('div,span'))
    .filter((x) => /此快捷键当前不可用/.test((x.innerText || '').trim()) && x.children.length <= 2);
  const e = c.sort((a, b2) => b2.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
  if (!e) return null; const r = e.getBoundingClientRect();
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, text: (e.innerText || '').trim() }; });
const pmText = () => p.evaluate(() => { const e = document.querySelector('[data-testid="prompt-composer"] .ProseMirror');
  return e ? { text: (e.innerText || '').replace(/\n/g, '|').slice(0, 24), html: (e.innerHTML || '').slice(0, 80) } : null; });
const drawerOpen = () => p.evaluate(() => { const s = document.querySelector('[data-testid="canvas-feature-sidecar"]'); if (!s) return null;
  const r = s.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; });
const setZoom = async (t0) => { for (let t = 1; t <= 3; t++) { if (await zoomPct() === t0) return { ok: true, how: 'already' };
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
    if (!await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t0);
    await p.waitForTimeout(1300); await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    const a = await zoomPct(); await p.waitForTimeout(900); const c = await zoomPct();
    if (a === c && a === t0) return { ok: true, how: 'input', pct: a }; }
  return { ok: false, pct: await zoomPct() }; };
const waitToast = async () => { for (const d of [300, 700, 1500]) { await p.waitForTimeout(d); const t = await toast(); if (t) return { toast: t, afterMs: d }; } return { toast: null, afterMs: 2500 }; };

try {
  // ══════ ① 清脏：把 b 轮留下的「gf」删掉 ══════
  out.clean = { steps: [] };
  let st = await drawerOpen();
  if (st && st.startsWith('200x')) { await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1700); }
  st = await drawerOpen(); log('抽屉', st, '输入框', JSON.stringify(await pmText()));
  const pt = await p.evaluate(() => { const e = document.querySelector('[data-testid="prompt-composer"] .ProseMirror'); if (!e) return null;
    const r = e.getBoundingClientRect(); return { x: Math.round(r.x + 20), y: Math.round(r.y + 20) }; });
  if (pt) {
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(800);
    for (let k = 0; k < 8; k++) {
      const t = await pmText();
      out.clean.steps.push({ k, ...t });
      if (!t || !t.text.replace(/\|/g, '').trim()) break;
      await p.keyboard.press('Backspace'); await p.waitForTimeout(500);
    }
  }
  out.clean.after = await pmText();
  out.clean.drawer = await drawerOpen();
  log('清脏结果', JSON.stringify(out.clean.after), '抽屉', out.clean.drawer);
  // 收起抽屉（回到默认终态）
  const cb = await p.evaluate(() => { const s = document.querySelector('[data-testid="canvas-feature-sidecar"]'); if (!s) return null;
    const x = Array.from(s.querySelectorAll('button,[role="button"]')).find((e) => /收起|折叠|collapse/i.test((e.getAttribute('aria-label') || '') + (e.innerText || '')));
    if (!x) return null; const r = x.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (cb) { await p.mouse.click(cb.x, cb.y); await p.waitForTimeout(1600); }
  out.clean.collapsed = await drawerOpen();
  log('收起后', out.clean.collapsed, '输入框', JSON.stringify(await pmText()));

  // ══════ ② 阳性对照：真实鼠标点画布空白 + 断言落点在 pane ══════
  out.control = {};
  const e = await p.evaluate(() => { const pane = document.querySelector('.react-flow__pane'); if (!pane) return null;
    for (let y = 110; y < 660; y += 20) for (let x = 210; x < 1240; x += 28) {
      const h = document.elementFromPoint(x, y);
      if (h && h === pane) return { x, y, hit: h.className }; }   // 🔑 必须是 pane 本身，不只是「在 pane 里」
    return null; });
  out.control.point = e; log('空白落点', JSON.stringify(e));
  if (e) {
    await p.mouse.click(e.x, e.y); await p.waitForTimeout(900);
    const g = await keyGuard(p);
    out.control.focus = g;
    out.control.sel = await selCount();
    log('焦点', JSON.stringify(g.where), '选中', out.control.sel);
    if (g.safe) {
      const before = { sel: await selCount(), pm: await pmText() };
      await pressLetter(p, 'g');
      const w = await waitToast();
      out.control.G = { before, toast: w.toast, afterMs: w.afterMs, after: { sel: await selCount(), pm: await pmText() } };
      log('阳性对照 按 G →', JSON.stringify(out.control.G));
      // F 对照
      await pressLetter(p, 'f');
      const w2 = await waitToast();
      out.control.F = { toast: w2.toast, afterMs: w2.afterMs,
        fs: await p.evaluate(() => { const x = document.querySelector('[data-testid="text-editor-fullscreen-dialog"]'); if (!x) return null; const r = x.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}`; }) };
      log('阳性对照 按 F →', JSON.stringify(out.control.F));
      await p.keyboard.press('Escape'); await p.waitForTimeout(900);
    } else out.control.void = 'keyGuard 拒绝';
  }
  out.zoom = await setZoom(60);
  out.end = { status: await status(), zoom: await zoomLabel(), drawer: await drawerOpen(), pm: await pmText(), sel: await selCount() };
  log('终态', JSON.stringify(out.end));
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
writeFileSync(new URL('./_tmp-b84c.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
