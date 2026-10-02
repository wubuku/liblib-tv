// 批次 86 · A：审计 `assets-and-upload.md`（普查下一名，停在批次 64）。
//
// 这一页 154 行，**取证密度不低**，但有两个明显的空白与一个很可复验的读数：
//
//   空白 ① **模态整体尺寸从来没记过** —— 页面只记了里面零星几个元素
//           （搜索框 200×36、时间 28×28、筛选 28×28、✕ 36×36@(981,74)、
//             确认禁用态的 `sr-only` 文字 1×1@(263,628)）。
//   空白 ② **「确认」按钮本身的尺寸没记**，而它是这一页最常被讨论的元素。
//
//   可复验读数：`sr-only` 那句「请先选择素材」实测 **1×1 像素 @ (263,628)**，
//   住在 `canvas-asset-library-footer` 里、是「确认」的**兄弟**不是子节点。
//   `x=263` 很小、`y=628` 很靠下 ⇒ 它应该在模态**左下角附近**，
//   而 ✕ 在 `x=981` ⇒ **模态不是水平居中的**（或模态很宽）。
//   ⇒ 这一条能同时验出「模态多宽」和「它靠哪边」，页面都没写。
//
// ⛔ 不点：任何素材、**确认**、新建/上传文件（文件选择器在 connectOverCDP 下会挂住）。
//    只开模态、切页签、展开筛选浮层、Esc 关。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const esc = async (ms = 1100) => { await p.keyboard.press('Escape'); await p.waitForTimeout(ms); };
/** 只在画布空白上点一下，不碰节点。 */
const focusCanvas = async () => { await esc(700);
  const e = await p.evaluate(() => { const pane = document.querySelector('.react-flow__pane'); if (!pane) return null;
    for (let y = 110; y < 660; y += 24) for (let x = 210; x < 1240; x += 32) { const h = document.elementFromPoint(x, y); if (h && pane.contains(h)) return { x, y }; }
    return null; });
  if (e) { await p.mouse.click(e.x, e.y); await p.waitForTimeout(700); } return e; };
const clickLeft = async (name) => { const pt = await p.evaluate((n) => {
    const el = Array.from(document.querySelectorAll('button,[role="button"],[data-testid^="canvas-left"],nav button'))
      .find((x) => { const a = (x.getAttribute('aria-label') || '').trim(); const t = (x.innerText || '').trim();
        return a === n || t === n; });
    if (!el) return null; const r = el.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, testid: el.getAttribute('data-testid') }; }, name);
  if (!pt) return { ok: false, why: `左栏找不到 aria/文本 逐字等于「${name}」的按钮` };
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(2600);
  return { ok: true, ...pt }; };

try {
  await focusCanvas();
  out.canvas = { status: await status(), vw: await p.evaluate(() => innerWidth), vh: await p.evaluate(() => innerHeight) };
  log('画布', JSON.stringify(out.canvas));

  // ══════ 打开资产库模态 ══════
  const c = await clickLeft('资产库');
  out.open = c; log('打开', JSON.stringify(c));
  await p.waitForTimeout(1800);

  // ══════ 模态全量结构 ══════
  out.modal = await p.evaluate(() => {
    // 逐个候选容器，按面积降序
    const cands = Array.from(document.querySelectorAll('[role="dialog"],[aria-modal="true"],[data-testid*="asset"],[data-testid*="modal"],[data-testid*="dialog"]'))
      .map((e) => { const r = e.getBoundingClientRect();
        return { tag: e.tagName, testid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
          ariaModal: e.getAttribute('aria-modal'), ariaLabel: e.getAttribute('aria-label'),
          box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
          area: Math.round(r.width) * Math.round(r.height),
          lines: (e.innerText || '').split('\n').map((s) => s.trim()).filter(Boolean).slice(0, 30) }; })
      .filter((x) => x.box && !/^0x0@/.test(x.box)).sort((a, b) => b.area - a.area);
    return { top: cands.slice(0, 6) };
  });
  log('模态容器候选：');
  out.modal.top.forEach((m) => { log(`   ${m.testid || m.role} ${m.box} aria-modal=${m.ariaModal} aria=${JSON.stringify(m.ariaLabel)}`);
    (m.lines || []).slice(0, 12).forEach((l) => log('      ·', l.slice(0, 40))); });

  out.detail = await p.evaluate(() => {
    const q = (s) => document.querySelector(s);
    const bx = (e) => { if (!e) return null; const r = e.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; };
    const all = (s) => Array.from(document.querySelectorAll(s)).map((e) => ({ tag: e.tagName, t: (e.innerText || e.getAttribute('aria-label') || '').trim().replace(/\n/g, ' ').slice(0, 26),
      box: bx(e), testid: e.getAttribute('data-testid'), role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
      ariaSelected: e.getAttribute('aria-selected'), dataState: e.getAttribute('data-state'),
      disabled: e.getAttribute('aria-disabled'), cursor: getComputedStyle(e).cursor }));
    return {
      viewportTestids: all('[data-testid*="asset"],[data-testid*="library"]'),
      closeBtns: all('[aria-label*="Close"],[aria-label*="close"],[aria-label*="关闭"]').filter((x) => x.box && !/^0x/.test(x.box)),
      search: (() => { const e = q('input[aria-label="Search Dreamina assets"]') || Array.from(document.querySelectorAll('input')).find((x) => /Search|搜索/.test(x.getAttribute('aria-label') || x.placeholder || ''));
        return e ? { box: bx(e), aria: e.getAttribute('aria-label'), ph: e.getAttribute('placeholder'), testid: e.getAttribute('data-testid') } : null; })(),
      srOnly: Array.from(document.querySelectorAll('.sr-only')).map((e) => ({ t: (e.innerText || '').trim().slice(0, 30), box: bx(e), tag: e.tagName, parent: e.parentElement ? (e.parentElement.getAttribute('data-testid') || e.parentElement.tagName) : null })).filter((x) => x.box),
      tabs: all('[role="tab"]'),
      footer: (() => { const e = q('[data-testid="canvas-asset-library-footer"]');
        return e ? { box: bx(e), lines: (e.innerText || '').split('\n').map((s) => s.trim()).filter(Boolean),
          buttons: Array.from(e.querySelectorAll('button')).map((x) => ({ t: (x.innerText || '').trim(), box: bx(x), ariaDisabled: x.getAttribute('aria-disabled'), dataDisabled: x.getAttribute('data-disabled'), cursor: getComputedStyle(x).cursor, opacity: getComputedStyle(x).opacity })) } : null; })(),
      confirmBtn: (() => { const e = Array.from(document.querySelectorAll('button')).find((x) => (x.innerText || '').trim() === '确认');
        if (!e) return null; const cs = getComputedStyle(e);
        return { box: bx(e), ariaDisabled: e.getAttribute('aria-disabled'), dataDisabled: e.getAttribute('data-disabled'),
          cursor: cs.cursor, opacity: cs.opacity, color: cs.color, nativeDisabled: e.disabled,
          parent: e.parentElement ? (e.parentElement.getAttribute('data-testid') || e.parentElement.tagName) : null }; })(),
      viewportEl: bx(q('[data-testid="canvas-asset-library-viewport"]')) };
  });
  log('搜索框', JSON.stringify(out.detail.search));
  log('页签', JSON.stringify(out.detail.tabs));
  log('关闭钮', JSON.stringify(out.detail.closeBtns));
  log('footer', JSON.stringify(out.detail.footer));
  log('确认钮', JSON.stringify(out.detail.confirmBtn));
  log('sr-only', JSON.stringify(out.detail.srOnly));
  log('viewport 元素', JSON.stringify(out.detail.viewportEl));
  log('全部 asset/library testid：'); (out.detail.viewportTestids || []).slice(0, 14).forEach((t) => log('   ', JSON.stringify(t)));

  // ══════ 逐个二级页签：读空态 ══════
  out.tabs = {};
  for (const t of ['图片', '视频', '音频', '文档']) {
    const ok = await p.evaluate((n) => { const e = Array.from(document.querySelectorAll('[role="tab"]')).find((x) => (x.innerText || '').trim() === n);
      if (!e) return false; e.click(); return true; }, t);
    await p.waitForTimeout(1700);
    out.tabs[t] = { clicked: ok, ...(await p.evaluate(() => ({
      empty: (() => { const e = Array.from(document.querySelectorAll('div,span,p')).filter((x) => /暂无|没有可用/.test((x.innerText || '').trim()) && x.children.length <= 1)
        .sort((a, b) => (b.innerText || '').length - (a.innerText || '').length)[0];
        if (!e) return null; const r = e.getBoundingClientRect();
        return { t: (e.innerText || '').trim(), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; })(),
      viewportEl: (() => { const e = document.querySelector('[data-testid="canvas-asset-library-viewport"]'); if (!e) return null; const r = e.getBoundingClientRect();
        return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; })(),
      tabCount: document.querySelectorAll('[role="tab"]').length,
      tabs: Array.from(document.querySelectorAll('[role="tab"]')).map((x) => (x.innerText || '').trim()),
      selected: Array.from(document.querySelectorAll('[role="tab"]')).filter((x) => x.getAttribute('aria-selected') === 'true').map((x) => (x.innerText || '').trim()),
      footerLine: (() => { const e = document.querySelector('[data-testid="canvas-asset-library-footer"]'); return e ? (e.innerText || '').split('\n').map((s) => s.trim()).filter(Boolean) : null; })()
    }))) };
    log(`页签「${t}」`, JSON.stringify(out.tabs[t]));
  }
  // ══════ 「主体」页签 ══════
  const sub = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[role="tab"]')).find((x) => (x.innerText || '').trim() === '主体'); if (!e) return null; e.click(); return true; });
  await p.waitForTimeout(1900);
  out.subject = { clicked: sub, ...(await p.evaluate(() => ({
    tabs: Array.from(document.querySelectorAll('[role="tab"]')).map((x) => (x.innerText || '').trim()),
    selected: Array.from(document.querySelectorAll('[role="tab"]')).filter((x) => x.getAttribute('aria-selected') === 'true').map((x) => (x.innerText || '').trim()),
    lines: (() => { const m = Array.from(document.querySelectorAll('[role="dialog"],[aria-modal="true"]')).sort((a, b) => (b.getBoundingClientRect().width * b.getBoundingClientRect().height) - (a.getBoundingClientRect().width * a.getBoundingClientRect().height))[0];
      return m ? (m.innerText || '').split('\n').map((s) => s.trim()).filter(Boolean).slice(0, 16) : null; })(),
    viewportEl: (() => { const e = document.querySelector('[data-testid="canvas-asset-library-viewport"]'); if (!e) return null; const r = e.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}`; })()
  }))) };
  log('「主体」页签', JSON.stringify(out.subject));
  await esc(1400);
  out.afterClose = { status: await status(), dialogGone: await p.evaluate(() => document.querySelectorAll('[role="dialog"],[aria-modal="true"]').length) };
  log('关闭后', JSON.stringify(out.afterClose));
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
writeFileSync(new URL('./_tmp-b86a.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
