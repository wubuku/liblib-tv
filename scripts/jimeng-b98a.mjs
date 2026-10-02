// 批次 98 · a 轮：**只读**清点主体节点。靶子 `subject-node.md`（普查 79，237 行）。
//
// 🔑 **主靶点是一个判据问题**：本页第 29 行写「**选中它不会出现浮动工具条** ——
//    这是它与视频、图片、文本节点最大的区别」。但「不会出现」是**按什么判的**？
//    批次 93 已钉过：`[data-testid="node-toolbar"]` 在别的节点上命中 **2** 个
//    （1 真身 + 1 `0×0` 占位），`.react-flow__node-toolbar` 命中 **3** 个。
//    ⇒ 如果本页当年是按 **testid 计数**判的「没有」，那句话就站不住 ——
//    **应该改成「没有**可见**工具条」，并给出可核对的判据**。
//    本轮实测主体节点选中态的这几个命中数与几何。
//
// 另外三条只读清点（弹药都是别的批次刚钉的契约）：
//   🔑 **手柄热区**：批次 91 钉「元素本体 `pe:none`、热区在 `::before` 40×80」，
//      批次 97 第四次确认（音频 31/31）。本页第 35 行只说「左右各有一个连接手柄」，
//      没说**能不能拖**。⇒ 读 `::before` 的 `pointer-events`。
//   🔑 **右键菜单**：批次 97 刚证明「**不同类型节点共用同一套右键菜单模板**」
//      （音频 7 项与文本 7 项逐字同序同尺寸）。主体节点是不是也在模板内？本页**整节缺失**。
//   🔑 **canvas 尺寸**：本页记 `352×352`（批次 79 订正过 310×310），本轮复核并做多实例对照。
//
// 🔴 共享画布纪律：主体节点**选中即自动获焦**（本页第 41–63 行），
//    所以本轮**点它之前先想清楚**：点完焦点会进标题输入框。
//    本轮**不按任何字母/数字键**，只读 `activeElement`。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };

const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const nodeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]');
  return e ? e.getAttribute('aria-label') : null; });
const zoomLabel = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return e ? e.getAttribute('aria-label') : null; });
const scaleNow = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });
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

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow(), tool: await toolAria() };
log('起点：', JSON.stringify(out.start));
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }
await setZoom(60);
const sc0 = await scaleStable0();
async function scaleStable0() { const a = await scaleNow(); await p.waitForTimeout(400); const c = await scaleNow();
  return { a, c, stable: a === c }; }
out.zoom = { label: await zoomLabel(), ...(await scaleStable0()) };
log('缩放：', JSON.stringify(out.zoom));

// ---- P1：全画布主体节点清点（离屏可量）----
out.p1 = await p.evaluate((s) => {
  const rows = [];
  for (const n of document.querySelectorAll('.react-flow__node-subject')) {
    const r = n.getBoundingClientRect();
    const m = /translate\(([^)]+)\)/.exec(n.style.transform || '');
    rows.push({ id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
      screen: { w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100 },
      canvas: s ? { w: Math.round((r.width / s) * 100) / 100, h: Math.round((r.height / s) * 100) / 100 } : null,
      translate: m ? m[1] : null,
      inView: r.right > 0 && r.bottom > 0 && r.left < 1280 && r.top < 720,
      innerText: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 70),
      innerTestids: Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')),
      innerAria: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]'))
        .map((e) => e.getAttribute('aria-label')))).slice(0, 16),
      buttons: n.querySelectorAll('button').length,
      inputs: n.querySelectorAll('input,textarea').length,
      mediaTags: Array.from(new Set(Array.from(n.querySelectorAll('audio,video,canvas,img'))
        .map((e) => e.tagName))) });
  }
  return rows;
}, out.zoom.a);
log(`P1 主体节点 ${out.p1.length} 个：`, JSON.stringify(out.p1.map((r) => ({ aria: r.aria, canvas: r.canvas, inView: r.inView, translate: r.translate }))));
if (out.p1.length) {
  const tidF = {}; out.p1.forEach((r) => r.innerTestids.forEach((t) => { tidF[t] = (tidF[t] || 0) + 1; }));
  const ariaF = {}; out.p1.forEach((r) => r.innerAria.forEach((a) => { ariaF[a] = (ariaF[a] || 0) + 1; }));
  log('   内部 testid 频次：', JSON.stringify(tidF));
  log('   内部 aria 频次：', JSON.stringify(ariaF));
  log('   内部按钮/输入框/媒体：', JSON.stringify(out.p1.map((r) => ({ b: r.buttons, i: r.inputs, m: r.mediaTags }))));
}

// ---- P2：找一个独占的主体节点（批次 96 的判据）----
await p.keyboard.press('Meta+0'); await p.waitForTimeout(2000);
out.fit = { label: await zoomLabel(), scale: await scaleNow() };
log('适配：', JSON.stringify(out.fit));

const findExcl = () => p.evaluate(() => {
  const INTERACTIVE = 'BUTTON,INPUT,A,TEXTAREA,SELECT,[role="button"],[contenteditable="true"]';
  const rows = [];
  for (const n of document.querySelectorAll('.react-flow__node-subject')) {
    const r = n.getBoundingClientRect();
    if (r.width < 16 || r.height < 16) continue;
    if (r.right < 60 || r.bottom < 60 || r.left > 1180 || r.top > 640) continue;
    let self = 0, tot = 0, goodPt = null;
    for (let i = 1; i <= 3; i++) for (let j = 1; j <= 3; j++) {
      const x = Math.round(r.x + (r.width * i) / 4), y = Math.round(r.y + (r.height * j) / 4);
      if (x < 1 || y < 1 || x > 1279 || y > 719) continue;
      tot++;
      const e = document.elementFromPoint(x, y);
      const o = e && e.closest('.react-flow__node');
      if (o && o.getAttribute('data-id') === n.getAttribute('data-id')) { self++; if (!e.closest(INTERACTIVE) && !goodPt) goodPt = { x, y }; }
    }
    rows.push({ id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
      w: Math.round(r.width), h: Math.round(r.height), self, tot, goodPt, x: Math.round(r.x), y: Math.round(r.y) });
  }
  return rows.filter((r) => r.self === r.tot && r.tot >= 9 && r.goodPt);
});
out.cands = await findExcl();
log('独占主体节点：', JSON.stringify(out.cands));
const TID = out.cands[0]?.id;
out.pick = out.cands[0] || null;

if (TID) {
  // 🔑 P3：手柄热区（批次 91/97 判据）
  out.handles = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const one = (sel) => { const e = n.querySelector(sel); if (!e) return null;
      const cs = getComputedStyle(e), bs = getComputedStyle(e, '::before'), as = getComputedStyle(e, '::after');
      const r = e.getBoundingClientRect();
      return { testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
        screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
        self: { pe: cs.pointerEvents, op: cs.opacity },
        before: { pe: bs.pointerEvents, w: bs.width, h: bs.height, op: bs.opacity },
        after: { pe: as.pointerEvents, w: as.width, h: as.height, op: as.opacity } }; };
    return { src: one('.flow-node-source-handle,[data-testid="flow-node-source-handle"]'),
      tgt: one('.flow-node-target-handle,[data-testid="flow-node-target-handle"]') };
  }, TID);
  log('P3 手柄 source：', JSON.stringify(out.handles.src));
  log('P3 手柄 target：', JSON.stringify(out.handles.tgt));

  // 🔑 P4：「工具条」的三种判据逐个量（testid / class / 可见几何）
  const toolbarProbe = (label) => p.evaluate((l) => {
    const n = document.querySelector(`.react-flow__node[data-id="${l.id}"]`);
    const list = (sel) => Array.from(document.querySelectorAll(sel)).map((e) => {
      const r = e.getBoundingClientRect();
      const cs = getComputedStyle(e);
      return { screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
        visible: r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && cs.opacity !== '0',
        pe: cs.pointerEvents, op: cs.opacity, vis: cs.visibility, disp: cs.display,
        aria: e.getAttribute('aria-label'), childBtns: e.querySelectorAll('button').length,
        inThisNode: n ? n.contains(e) : false }; });
    return { label: l.label, selected: n ? n.classList.contains('selected') : null,
      sel: document.body.innerText.match(/(\d+) selected/)?.[1] ?? '0',
      byTestid: list('[data-testid="node-toolbar"]'),
      byClass: list('.react-flow__node-toolbar'),
      bySelToolbar: list('[data-testid="selection-context-toolbar"]'),
      bySelSurface: list('[data-testid="selection-context-toolbar-surface"]'),
      featureHost: list('[data-testid="node-toolbar-feature-host"]'),
      popupHost: list('[data-testid="selection-context-toolbar-popup-host"]'),
      // 🔑 主体节点是否有**任何**可见的工具条状元素
      anyVisibleToolbarish: Array.from(document.querySelectorAll('div,section,aside'))
        .filter((e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
          return r.width > 0 && r.height >= 30 && r.width >= 100
            && /toolbar|tool-bar|context-toolbar/i.test(String(e.className) + ' ' + (e.getAttribute('data-testid') || '')); })
        .map((e) => { const r = e.getBoundingClientRect();
          return { tid: e.getAttribute('data-testid'), cls: String(e.className).slice(0, 60),
            screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; }).slice(0, 8),
      activeElement: (() => { const a = document.activeElement;
        return { tag: a ? a.tagName : null, aria: a ? a.getAttribute('aria-label') : null,
          tid: a ? a.getAttribute('data-testid') : null, type: a ? a.getAttribute('type') : null,
          inSubject: n ? n.contains(a) : false }; })() };
  }, { label, id: TID });

  out.probe = [];
  const probe = async (label) => { const r = await toolbarProbe(label); out.probe.push(r);
    log(`P4 ${label}: selected=${r.selected} sel=${r.sel}`);
    log(`   byTestid(${r.byTestid.length}): ${JSON.stringify(r.byTestid)}`);
    log(`   byClass(${r.byClass.length}): ${JSON.stringify(r.byClass.map((x) => ({ s: x.screen, v: x.visible, inN: x.inThisNode, btns: x.childBtns })))}`);
    log(`   selToolbar=${JSON.stringify(r.bySelToolbar.map((x) => x.screen))} selSurface=${JSON.stringify(r.bySelSurface.map((x) => x.screen))}`);
    log(`   featureHost=${JSON.stringify(r.featureHost.map((x) => x.screen))} popupHost=${JSON.stringify(r.popupHost.map((x) => x.screen))}`);
    log(`   任何可见 toolbarish：${JSON.stringify(r.anyVisibleToolbarish)}`);
    log(`   activeElement：${JSON.stringify(r.activeElement)}`);
    return r; };

  await probe('①未选中');
  await p.mouse.click(out.pick.goodPt.x, out.pick.goodPt.y);
  await p.waitForTimeout(1600);
  await probe('②选中');

  // 🔑 P5：右键菜单
  await p.mouse.move(out.pick.goodPt.x, out.pick.goodPt.y); await p.waitForTimeout(250);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1500);
  out.menu = await p.evaluate(() => {
    const m = document.querySelector('[data-testid="canvas-context-menu"]');
    if (!m) return null;
    const r = m.getBoundingClientRect();
    return { screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      items: Array.from(m.querySelectorAll('[role="menuitem"]')).map((x) => { const b = x.getBoundingClientRect();
        return { text: x.innerText.replace(/\s+/g, ' ').trim(), w: Math.round(b.width), h: Math.round(b.height),
          disabled: x.getAttribute('aria-disabled') }; }) }; });
  log('P5 右键菜单：', out.menu ? out.menu.screen : 'null');
  if (out.menu) out.menu.items.forEach((i, n) => log(`   ${n + 1}. ${i.text}  ${i.w}×${i.h} disabled=${i.disabled}`));
  if (out.menu) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
}

// 收尾
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
out.restore = { ok: await setZoom(60) };
out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow(), tool: await toolAria() };
log('缩放归位：', out.restore.ok ? '✅' : '🔴');
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b98a.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
