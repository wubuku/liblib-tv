// 批次 98 · c 轮：只补一件事 —— **「选中主体节点，标题输入框自动获焦」**（本页第 41–63 行）。
//
// 🔴 b 轮那一格**没测到**：`②选中后` 的 `activeElement` 是 `<DIV aria="Canvas">`，
//    与本页「选中即自动获焦」**矛盾**。最可能的原因不是结论错，而是**落点不对** ——
//    b 轮点的是节点**中心**（23% 下的几何中心），而主体节点中心落在**空态导入区**，
//    标题在卡片顶部。本轮改**逐点测试**：把节点内所有「落点非交互元素」的采样点
//    **逐个点一遍**，每点一次读一次 `activeElement` 与该点的元素身份。
//    ⇒ 这样能**定位到「哪一块区域会触发自动获焦」**，而不是只拿到一个总结果。
//
// 🔴 纪律：主体节点获焦后**绝不能按任何字母/数字键**（本页明写会直接改标题，
//    而节点标题是共享数据）。本轮**只读不写**，不按任何键。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const nodeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]');
  return e ? e.getAttribute('aria-label') : null; });
const zoomLabel = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return e ? e.getAttribute('aria-label') : null; });
const toolAria = () => p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return t ? t.getAttribute('aria-label') : null; });
const setZoom = async (t) => { for (let k = 1; k <= 4; k++) {
  const zl = await zoomLabel(); if (zl && new RegExp(`, ${t}%`).test(zl)) return true;
  await p.click('[data-testid="canvas-zoom-percent"]'); await p.waitForTimeout(1000);
  if (await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) {
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true }));
      i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t);
    await p.waitForTimeout(1700);
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
  return false; };

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), tool: await toolAria() };
log('起点：', JSON.stringify(out.start));
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }
await setZoom(60);
await p.keyboard.press('Meta+0'); await p.waitForTimeout(2000);
out.fit = { zoom: await zoomLabel() };
log('适配：', JSON.stringify(out.fit));

// 护栏 ①
const idsBefore = new Set(await allIds());
out.idsBefore = idsBefore.size;
log('建前 id 数：', idsBefore.size);

const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role="button"]'))
  .map((e) => { const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.aria === '主体' && x.w > 0 && x.h > 0));
out.rail = rail;
log('左栏主体入口：', JSON.stringify(rail));

let SELF = null;
if (!rail.length) log('🔴 找不到入口 ⇒ 停止（不建不删）');
else {
  const r0 = rail[0];
  await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(700);
  await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2);
  await p.waitForTimeout(3000);
  const idsAfter = await allIds();
  const created = idsAfter.filter((id) => !idsBefore.has(id));
  const selIds = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
  const newSel = selIds.filter((id) => !idsBefore.has(id));
  out.guard = { before: idsBefore.size, after: idsAfter.length, created, selIds, newSel };
  log('护栏：', JSON.stringify(out.guard));
  SELF = created.length === 1 && newSel.length === 1 && newSel[0] === created[0] ? created[0] : null;
  out.selfId = SELF;
  log('SELF =', SELF, SELF ? '✅' : '🔴 判失败 ⇒ 不测不删');
}

if (SELF) {
  // 建完立刻读一次 activeElement（它建出来就是选中态，焦点可能在左栏按钮上）
  out.afterCreate = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const a = document.activeElement;
    return { selected: n ? n.classList.contains('selected') : null,
      active: { tag: a ? a.tagName : null, aria: a ? a.getAttribute('aria-label') : null,
        tid: a ? a.getAttribute('data-testid') : null, inSubject: n ? n.contains(a) : false } }; }, SELF);
  log('建完（未点画布）activeElement：', JSON.stringify(out.afterCreate));

  // 先点画布空白把焦点挪走，再逐点测试
  await p.mouse.click(40, 200); await p.waitForTimeout(1100);
  out.beforeSweep = await p.evaluate(() => { const a = document.activeElement;
    return { tag: a ? a.tagName : null, aria: a ? a.getAttribute('aria-label') : null }; });
  log('点空白后 activeElement：', JSON.stringify(out.beforeSweep));

  // 列出节点内所有可点的采样点（含元素身份与 aria）
  const pts = await p.evaluate((i) => {
    const INTERACTIVE = 'BUTTON,INPUT,A,TEXTAREA,SELECT,[role="button"],[contenteditable="true"]';
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
    const r = n.getBoundingClientRect();
    const rows = [];
    for (let a = 1; a <= 5; a++) for (let c = 1; c <= 5; c++) {
      const x = Math.round(r.x + (r.width * a) / 6), y = Math.round(r.y + (r.height * c) / 6);
      if (x < 2 || y < 2 || x > 1278 || y > 718) continue;
      const e = document.elementFromPoint(x, y);
      if (!e || e.closest('.react-flow__node') !== n) continue;
      if (e.closest(INTERACTIVE)) continue;
      // 往上找最近的带 aria 或 testid 的祖先，好认位置
      let c2 = e, label = null;
      while (c2 && c2 !== n) {
        const ar = c2.getAttribute('aria-label'), td = c2.getAttribute('data-testid');
        if (ar || td) { label = (ar ? `aria=${ar}` : '') + (td ? ` tid=${td}` : ''); break; }
        c2 = c2.parentElement;
      }
      rows.push({ x, y, tag: e.tagName, label, text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18) });
    }
    return { rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }, rows };
  }, SELF);
  out.pts = pts;
  log(`节点内可点采样点 ${pts?.rows?.length ?? 0} 个（rect ${JSON.stringify(pts?.rect)}）：`);

  // 🔑 逐点点击，读每次的 activeElement
  out.sweep = [];
  const seen = new Set();
  for (const pt of pts?.rows ?? []) {
    const key = `${pt.x},${pt.y}`;
    await p.mouse.click(pt.x, pt.y);
    await p.waitForTimeout(700);
    const r = await p.evaluate((c) => {
      const a = document.activeElement;
      const n = document.querySelector('.react-flow__node.selected');
      return { activeTag: a ? a.tagName : null, activeAria: a ? a.getAttribute('aria-label') : null,
        activeTid: a ? a.getAttribute('data-testid') : null,
        activeType: a ? a.getAttribute('type') : null,
        activeValue: a && 'value' in a ? String(a.value).slice(0, 30) : null,
        activePlaceholder: a ? a.getAttribute('placeholder') : null,
        activeInSelectedNode: n ? n.contains(a) : null,
        activeIsInput: a ? (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA' || a.isContentEditable) : false,
        sel: document.body.innerText.match(/(\d+) selected/)?.[1] ?? '0' }; });
    out.sweep.push({ pt: key, tag: pt.tag, label: pt.label, text: pt.text, ...r });
    if (r.activeIsInput) log(`   🔑 ${key} <${pt.tag}> ${pt.label || pt.text} → 焦点进了 ${r.activeTag} aria=${r.activeAria} value=${JSON.stringify(r.activeValue)} 占位=${r.activePlaceholder}`);
    seen.add(`${r.activeTag}|${r.activeAria}|${r.activeIsInput}`);
  }
  log('逐点结果汇总（去重后按点击顺序）：');
  out.sweep.forEach((s) => log(`   ${s.pt} <${s.tag}> ${s.label || s.text || ''} → active=${s.activeTag} aria=${s.activeAria} isInput=${s.activeIsInput} inNode=${s.activeInSelectedNode} value=${JSON.stringify(s.activeValue)}`));
  out.focusKinds = [...seen];
  log('焦点种类：', JSON.stringify(out.focusKinds));

  // 标题元素本身：结构与是否可点
  out.title = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const hdr = n.querySelector('[data-testid="subject-header"]');
    const ren = n.querySelector('[aria-label^="Rename "]');
    const g = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
      return { screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; };
    return { header: g(hdr), headerAria: hdr ? hdr.getAttribute('aria-label') : null,
      headerText: hdr ? hdr.innerText.replace(/\s+/g, ' ').trim() : null,
      rename: g(ren), renameAria: ren ? ren.getAttribute('aria-label') : null,
      inputsNow: n.querySelectorAll('input,textarea').length,
      inputAria: Array.from(n.querySelectorAll('input,textarea')).map((e) => ({ aria: e.getAttribute('aria-label'),
        type: e.getAttribute('type'), ph: e.getAttribute('placeholder'), value: e.value })) };
  }, SELF);
  log('标题结构：', JSON.stringify(out.title));
}

// 收尾：只删 SELF
out.cleanup = { target: SELF, attempts: [] };
if (SELF) {
  for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
  for (let attempt = 1; attempt <= 3; attempt++) {
    const pt = await p.evaluate((i) => {
      const INTERACTIVE = 'BUTTON,INPUT,A,TEXTAREA,SELECT,[role="button"],[contenteditable="true"]';
      const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
      const r = n.getBoundingClientRect();
      for (let a = 1; a <= 3; a++) for (let c = 1; c <= 3; c++) {
        const x = Math.round(r.x + (r.width * a) / 4), y = Math.round(r.y + (r.height * c) / 4);
        if (x < 2 || y < 2 || x > 1278 || y > 718) continue;
        const e = document.elementFromPoint(x, y);
        if (e && e.closest('.react-flow__node') === n && !e.closest(INTERACTIVE)) return { x, y }; }
      return null; }, SELF);
    if (!pt) { await p.keyboard.press('Meta+0'); await p.waitForTimeout(1900); continue; }
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1300);
    const isSel = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      return n ? n.classList.contains('selected') : false; }, SELF);
    if (!isSel) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); continue; }
    await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(300);
    await p.mouse.down({ button: 'right' }); await p.waitForTimeout(280); await p.mouse.up({ button: 'right' });
    await p.waitForTimeout(1500);
    const res = await p.evaluate((i) => {
      const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      if (!n || !n.classList.contains('selected')) return 'target-not-selected';
      const m = document.querySelector('[data-testid="canvas-context-menu"]'); if (!m) return 'no-menu';
      const it = Array.from(m.querySelectorAll('[role="menuitem"]'))
        .find((x) => /^删除/.test(x.innerText.replace(/\s+/g, ' ').trim()) && x.getAttribute('aria-disabled') !== 'true');
      if (!it) return 'no-item'; it.click(); return 'clicked'; }, SELF);
    await p.waitForTimeout(1900);
    const still = await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), SELF);
    out.cleanup.attempts.push({ attempt, res, still });
    log(`  删除尝试 ${attempt}：${res}｜仍在=${still}`);
    if (!still) break;
  }
  out.idsAfterAll = (await allIds()).length;
  out.selfLeft = await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), SELF);
  log('自建残留：', out.selfLeft, '｜当前 id 数：', out.idsAfterAll, '（建前', out.idsBefore, '）');
}
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }
out.restore = { ok: await setZoom(60) };
out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), tool: await toolAria() };
log('缩放归位：', out.restore.ok ? '✅' : '🔴');
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b98c.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
