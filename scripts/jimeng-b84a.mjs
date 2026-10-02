// 批次 84 · A：复核 `ai-agent-drawer.md`（普查下一名，停在批次 62）。
//
// 这一页本身做得很扎实，本轮**不去重复它已经做过的取证**，
// 只做三件「别的批次提供了新弹药」的事：
//
// ① **几何复核**：页面所有尺寸测于 2026-10-01（当时画布节点少）。
//    关键一条：页面第 87 行写 `prompt-composer` **357×84 @ (890,554)** ——
//    而批次 82 独立测到的「污染全文档 ProseMirror 判据」那个元素
//    **恰好也是 357×84@890,554**。两者若同源，批次 82 的发现就得到了归因：
//    **那个 ProseMirror 就是本抽屉的输入框**，页面早就记了它的几何。
//
// ② 🔴 **补一个页面完全没写、但读者一定会踩的结论**（批次 82 撞出来的）：
//    **Agent 抽屉开着的时候，画布快捷键全部失效。**
//    原因是抽屉输入框会拿走键盘焦点。页面第 18-19 行只把 ⌘/ 当成「打开抽屉的快捷键」，
//    **没提醒它同时也是「让画布快捷键失灵」的那一下**。
//    症状极具误导性：按 G 什么也不发生、连「此快捷键当前不可用」都没有，
//    和「这个键没绑定」**长得一模一样**。
//
// ③ **计数口径并列**：页面写「内部可见元素 49 个」，
//    批次 82 写的「打开态 19~20」是 `[data-testid^="canvas-agent-"]` 前缀计数 ——
//    两者**不是同一个口径**，不是矛盾。三个口径都量一遍，把话说清楚。
//
// ⛔ 不点：发送消息（扣费边界）、技能选择器里的任何技能、管理技能。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard, pressLetter } from './jimeng-safe-keys.mjs';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const box = (e) => { const r = e.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; };
const esc = async (ms = 900) => { await p.keyboard.press('Escape'); await p.waitForTimeout(ms); };
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const zoomLabel = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const zoomPct = async () => { const l = await zoomLabel(); return l ? Number((l.match(/(\d+)%/) || [])[1]) : null; };
const selCount = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const toast = () => p.evaluate(() => { const c = Array.from(document.querySelectorAll('div,span'))
    .filter((x) => /此快捷键当前不可用/.test((x.innerText || '').trim()) && x.children.length <= 2);
  const e = c.sort((a, b2) => b2.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
  if (!e) return null; const r = e.getBoundingClientRect();
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, text: (e.innerText || '').trim() }; });
const visIn = (root) => p.evaluate((sel) => {
  const r = document.querySelector(sel); if (!r) return { err: '未找到 ' + sel };
  let all = 0; for (const e of r.querySelectorAll('*')) { const rr = e.getBoundingClientRect(); if (rr.width > 0 && rr.height > 0) all++; }
  const pr = r.getBoundingClientRect();
  return { box: `${Math.round(pr.width)}x${Math.round(pr.height)}@${Math.round(pr.x)},${Math.round(pr.y)}`,
    withArea: all, tag: r.tagName, aria: r.getAttribute('aria-label'), z: getComputedStyle(r).zIndex,
    pe: getComputedStyle(r).pointerEvents, display: getComputedStyle(r).display };
}, root);
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

try {
  out.zoom = await setZoom(60); log('缩放', JSON.stringify(out.zoom));
  out.before = { status: await status(), zoom: await zoomLabel() };
  log('进场', JSON.stringify(out.before));

  // ══════ ① 打开抽屉，点右下角「与 AI 对话」 ══════
  const lb = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-sidecar-launcher"]')
    || Array.from(document.querySelectorAll('button,[role="button"]')).find((x) => /与 AI 对话/.test((x.getAttribute('aria-label') || '') + (x.innerText || '')));
    if (!e) return null; const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; });
  out.launcher = lb; log('启动钮', JSON.stringify(lb));
  await p.mouse.click(lb.x, lb.y); await p.waitForTimeout(1900);

  // ══════ ② 展开态几何 + 三个计数口径 + prompt-composer 对账 ══════
  out.expanded = {};
  for (const sel of ['[data-testid="canvas-feature-sidecar"]', '[data-testid="canvas-agent-panel"]',
    '[data-testid="canvas-agent-session-composer"]', '[data-testid="prompt-composer"]']) {
    out.expanded[sel] = await visIn(sel);
    log('  ', sel, JSON.stringify(out.expanded[sel]));
  }
  out.counts = await p.evaluate(() => {
    const withArea = (root) => { let n = 0; for (const e of root.querySelectorAll('*')) { const r = e.getBoundingClientRect(); if (r.width > 0 && r.height > 0) n++; } return n; };
    const sidecar = document.querySelector('[data-testid="canvas-feature-sidecar"]');
    const panel = document.querySelector('[data-testid="canvas-agent-panel"]');
    const pref = document.querySelectorAll('[data-testid^="canvas-agent-"]');
    const prefArea = Array.from(pref).filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
    const pm = document.querySelector('.ProseMirror[contenteditable="true"]');
    const pr = pm ? pm.getBoundingClientRect() : null;
    return { sidecarUnique: document.querySelectorAll('[data-testid="canvas-feature-sidecar"]').length,
      sidecarWithArea: sidecar ? withArea(sidecar) : null,
      panelWithArea: panel ? withArea(panel) : null,
      prefixTotal: pref.length, prefixWithArea: prefArea.length,
      wholePageWithArea: (() => { let n = 0; for (const e of document.querySelectorAll('*')) { const r = e.getBoundingClientRect(); if (r.width > 0 && r.height > 0) n++; } return n; })(),
      pmInSidecar: !!document.querySelector('[data-testid="canvas-feature-sidecar"] .ProseMirror[contenteditable="true"]'),
      pmAnywhere: document.querySelectorAll('.ProseMirror[contenteditable="true"]').length,
      pmBox: pr ? `${Math.round(pr.width)}x${Math.round(pr.height)}@${Math.round(pr.x)},${Math.round(pr.y)}` : null,
      pmInNode: document.querySelectorAll('.react-flow__node .ProseMirror[contenteditable="true"]').length };
  });
  log('计数三口径', JSON.stringify(out.counts, null, 1));
  out.expandedFocus = await keyGuard(p);
  log('打开后焦点', JSON.stringify(out.expandedFocus));

  // ══════ ③ 🔴 抽屉开着时，画布快捷键是不是真的失效 ══════
  // 前置：焦点必须在输入框里（点 prompt-composer 内的占位符层能拿到编辑器）
  const pmPt = await p.evaluate(() => { const e = document.querySelector('[data-testid="prompt-composer"] .ProseMirror')
    || document.querySelector('[data-testid="prompt-composer"]'); if (!e) return null;
    const r = e.getBoundingClientRect(); return { x: Math.round(r.x + 20), y: Math.round(r.y + 20) }; });
  out.pmPoint = pmPt;
  if (pmPt) { await p.mouse.click(pmPt.x, pmPt.y); await p.waitForTimeout(900); }
  const g1 = await keyGuard(p);
  out.preShortcuts = { focus: g1.where, safe: g1.safe, sel: await selCount() };
  log('点输入框后焦点', JSON.stringify(out.preShortcuts));
  if (g1.safe) {
    out.gInDrawer = { before: { sel: await selCount(), vis: out.counts.wholePageWithArea } };
    await pressLetter(p, 'g');
    for (const d of [300, 700, 1500]) { await p.waitForTimeout(d); const t = await toast(); if (t) { out.gInDrawer.toast = t; out.gInDrawer.toastAfterMs = d; break; } }
    if (!out.gInDrawer.toast) out.gInDrawer.toast = null;
    out.gInDrawer.after = { sel: await selCount() };
    out.gInDrawer.sampledToMs = 2500;
    // 输入框里有没有被塞进字母 g
    out.gInDrawer.typedInto = await p.evaluate(() => {
      const e = document.querySelector('[data-testid="prompt-composer"] .ProseMirror');
      return e ? (e.innerText || '').trim().slice(0, 12) : null; });
    log('抽屉开着按 G →', JSON.stringify(out.gInDrawer));
  }
  // 同样在 F 上对照一次
  if (g1.safe) {
    await pressLetter(p, 'f');
    for (const d of [400, 900]) { await p.waitForTimeout(d); const t = await toast(); if (t) { out.fInDrawer = { toast: t }; break; } }
    if (!out.fInDrawer) out.fInDrawer = { toast: null };
    out.fInDrawer.fs = await p.evaluate(() => { const e = document.querySelector('[data-testid="text-editor-fullscreen-dialog"]'); if (!e) return null; const r = e.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}`; });
    log('抽屉开着按 F →', JSON.stringify(out.fInDrawer));
  }

  // ══════ ④ 点「收起」→ 折叠态 ══════
  const collapse = await p.evaluate(() => { const side = document.querySelector('[data-testid="canvas-feature-sidecar"]'); if (!side) return null;
    const b = Array.from(side.querySelectorAll('button,[role="button"]')).find((x) => /收起|折叠|collapse/i.test((x.getAttribute('aria-label') || '') + (x.innerText || '')));
    if (!b) return { err: '侧栏里找不到收起钮', btns: Array.from(side.querySelectorAll('button')).map((x) => (x.getAttribute('aria-label') || x.innerText || '').trim().slice(0, 12)) };
    const r = b.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), aria: b.getAttribute('aria-label') }; });
  out.collapseBtn = collapse; log('收起钮', JSON.stringify(collapse));
  if (collapse && collapse.x !== undefined) {
    await p.mouse.click(collapse.x, collapse.y); await p.waitForTimeout(1800);
    out.collapsed = {
      sidecar: await visIn('[data-testid="canvas-feature-sidecar"]'),
      panel: await visIn('[data-testid="canvas-agent-panel"]'),
      counts: await p.evaluate(() => {
        const withArea = (root) => { let n = 0; for (const e of root.querySelectorAll('*')) { const r = e.getBoundingClientRect(); if (r.width > 0 && r.height > 0) n++; } return n; };
        const side = document.querySelector('[data-testid="canvas-feature-sidecar"]');
        const pref = document.querySelectorAll('[data-testid^="canvas-agent-"]');
        return { sidecarWithArea: side ? withArea(side) : null,
          prefixTotal: pref.length,
          prefixWithArea: Array.from(pref).filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; }).length,
          pmAnywhere: document.querySelectorAll('.ProseMirror[contenteditable="true"]').length }; }),
      focus: await keyGuard(p) };
    log('折叠态', JSON.stringify(out.collapsed, null, 1));
  }
  // ══════ ⑤ ⌘/ 重新展开 → 焦点落点 ══════
  await esc(700);
  const g2 = await keyGuard(p);
  if (g2.safe) { await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1700);
    out.afterSlashOpen = { focus: await keyGuard(p), sidecar: await visIn('[data-testid="canvas-feature-sidecar"]') };
    log('⌘/ 展开后', JSON.stringify(out.afterSlashOpen));
    const g3 = await keyGuard(p);
    if (g3.safe) { await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1700);
      out.afterSlashClose = { focus: await keyGuard(p), sidecar: await visIn('[data-testid="canvas-feature-sidecar"]'),
        counts: await p.evaluate(() => ({ prefixTotal: document.querySelectorAll('[data-testid^="canvas-agent-"]').length,
          prefixWithArea: Array.from(document.querySelectorAll('[data-testid^="canvas-agent-"]')).filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; }).length,
          pmAnywhere: document.querySelectorAll('.ProseMirror[contenteditable="true"]').length })) };
      log('⌘/ 收起后', JSON.stringify(out.afterSlashClose, null, 1)); } }
  out.end = { status: await status(), zoom: await zoomLabel() };
  log('终态', JSON.stringify(out.end));
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
writeFileSync(new URL('./_tmp-b84a.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
