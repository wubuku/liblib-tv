// 批次 102 · g 轮：资产库模态的**第三次**全量对账（只读，不点任何素材、不点「确认」）。
//
// 批次 52 建结构、批次 86 第二次全量复核，两次都写「逐字一致」。
// 本轮是**第三次**。📌 纪律：**结论只认当次输出** —— 哪怕前两轮一模一样，
// 这一轮仍要自己重新读一遍，因为「复现过」不等于「现在还对」。
//
// ⚠️ 只读边界：模态里的页签**可以点**（只是切换视图）；
//    **素材卡片**（本画布为空，没有）与**「确认」**（会插入画布）**一律不点**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const selN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);

out.start = { nodes: await nodeN(), sel: await selN() };
log('起点：', JSON.stringify(out.start));

// ---- 打开模态：左栏「资产库」 ----
const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
  .map((e) => { const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.aria === '资产库' && x.w > 0 && x.h > 0));
out.rail = rail;
log('左栏资产库入口：', JSON.stringify(rail));
if (!rail.length) { log('🔴 找不到入口'); writeFileSync(new URL('./_tmp-b102g.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(1); }
{
  const r0 = rail[0];
  await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(500);
  await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(2200);
}

const dump = () => p.evaluate(() => {
  const d = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
  if (!d) return { none: true };
  const R = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`; };
  const want = ['canvas-asset-library-dialog', 'canvas-asset-library-surface', 'canvas-asset-library-operation-area',
    'canvas-asset-library-navigation-controls', 'canvas-asset-library-query-action-group', 'canvas-asset-library-viewport',
    'canvas-asset-library-footer', 'canvas-asset-library-import-status', 'canvas-asset-library-box-selection'];
  const layers = want.map((t) => ({ t, rect: R(d.querySelector(`[data-testid="${t}"]`)) || (t === 'canvas-asset-library-dialog' ? R(d) : null) }));
  const tabs = Array.from(d.querySelectorAll('[role=tab]')).map((e) => { const r = e.getBoundingClientRect();
    return { txt: (e.innerText || '').trim(), aria: e.getAttribute('aria-label'), selected: e.getAttribute('aria-selected'),
      rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }; });
  const vp = d.querySelector('[data-testid="canvas-asset-library-viewport"]');
  const foot = d.querySelector('[data-asset="x"], [data-testid="canvas-asset-library-footer"]');
  const confirm = Array.from(d.querySelectorAll('button')).find((e) => (e.innerText || '').trim() === '确认');
  const cr = confirm ? confirm.getBoundingClientRect() : null;
  const cs = confirm ? getComputedStyle(confirm) : null;
  const srOnly = Array.from(d.querySelectorAll('*')).filter((e) => e.className && String(e.className).includes('sr-only'))
    .map((e) => { const r = e.getBoundingClientRect();
      return { txt: (e.textContent || '').trim().slice(0, 24), rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
        parent: e.parentElement ? (e.parentElement.getAttribute('data-testid') || e.parentElement.tagName) : null,
        inConfirm: confirm ? confirm.contains(e) : false }; });
  return {
    dialog: { rect: R(d), role: d.getAttribute('role'), state: d.getAttribute('data-state') },
    layers, tabs,
    emptyText: vp ? (vp.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) : null,
    hasViewportEl: !!vp,
    footerText: foot ? (foot.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) : null,
    confirm: confirm ? { rect: `${Math.round(cr.x)},${Math.round(cr.y)} ${Math.round(cr.width)}×${Math.round(cr.height)}`,
      ariaDisabled: confirm.getAttribute('aria-disabled'), dataDisabled: confirm.getAttribute('data-disabled'),
      cursor: cs.cursor, color: cs.color, opacity: cs.opacity, nativeDisabled: confirm.disabled } : null,
    srOnly,
    globalSrOnlyCount: document.querySelectorAll('.sr-only').length,
  };
});

out.pass1 = await dump();
log('\n=== 第一次（资产/图片）===');
log(JSON.stringify(out.pass1, null, 1));

// ---- 逐个切第二级页签（只点页签，不点素材/确认） ----
out.tabs = [];
for (const name of ['视频', '音频', '文档']) {
  const t = await p.evaluate((nm) => { for (const e of document.querySelectorAll('[role=tab]')) {
      if ((e.getAttribute('aria-label') || '').trim() === nm) { const r = e.getBoundingClientRect();
        return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; } } return null; }, name);
  if (!t) { log(`  ${name}：页签找不到`); continue; }
  await p.mouse.move(t.x, t.y); await p.waitForTimeout(350);
  await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400);
  const d = await dump();
  out.tabs.push({ name, emptyText: d.emptyText, viewport: (d.layers.find((l) => l.t === 'canvas-asset-library-viewport') || {}).rect,
    footer: d.footerText, confirmRect: d.confirm && d.confirm.rect, selectedTabs: d.tabs.filter((x) => x.selected === 'true').map((x) => x.txt || x.aria) });
  log(`  ${name}：空态「${d.emptyText}」｜viewport ${(d.layers.find((l) => l.t === 'canvas-asset-library-viewport') || {}).rect}｜页脚「${d.footerText}」｜选中页签 ${JSON.stringify(out.tabs[out.tabs.length - 1].selectedTabs)}`);
}

// ---- 一级页签「主体」 ----
{
  const t = await p.evaluate(() => { for (const e of document.querySelectorAll('[role=tab]')) {
      if ((e.innerText || '').trim() === '主体') { const r = e.getBoundingClientRect();
        return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; } } return null; });
  if (t) { await p.mouse.move(t.x, t.y); await p.waitForTimeout(350); await p.mouse.click(t.x, t.y); await p.waitForTimeout(1500);
    const d = await dump();
    out.subjectTab = { emptyText: d.emptyText, hasViewportEl: d.hasViewportEl, tabs: d.tabs,
      selectedTabs: d.tabs.filter((x) => x.selected === 'true').map((x) => x.txt || x.aria), footerText: d.footerText };
    log('\n=== 主体页 ===');
    log(JSON.stringify(out.subjectTab, null, 1)); }
}

// ---- 关闭 ----
for (let k = 0; k < 2; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
out.closed = await p.evaluate(() => !document.querySelector('[data-testid="canvas-asset-library-dialog"]'));
log('\nEsc 关闭成功？', out.closed ? '✅' : '🔴');
out.end = { nodes: await nodeN(), sel: await selN() };
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b102g.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
