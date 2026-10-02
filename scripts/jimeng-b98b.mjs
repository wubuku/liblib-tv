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

// ================= 护栏：自建一个主体节点 =================
// 画布上**一个主体节点都没有**（别的会话删了）⇒ 只读部分做不了，只能自建。
// 建在自己的节点上，风险由三重护栏兜住（批次 97 事故换来的）：
//   ① 建前存全画布 id 集合
//   ② 建后差集**恰好一个**，且它**同时**是 `.selected`（建节点自动选中）
//   ③ 删除前**再确认目标仍 selected**；事后核对「本轮消失的 id」恰好只有 SELF
//
// 🔴 主体节点**选中即自动获焦**（本页第 41–63 行）⇒ 本轮**不按任何字母/数字键**，
//    只读 `activeElement`。

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));

await p.keyboard.press('Meta+0'); await p.waitForTimeout(2000);
out.fit = { label: await zoomLabel(), scale: await scaleNow() };
log('适配：', JSON.stringify(out.fit));

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
if (!rail.length) log('🔴 找不到左栏主体入口 ⇒ 停止（不建不删）');
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
  out.selfInfo = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const r = n.getBoundingClientRect();
    return { aria: n.getAttribute('aria-label'), cls: n.className, translate: n.style.transform,
      screen: `${Math.round(r.width * 100) / 100}×${Math.round(r.height * 100) / 100}@${Math.round(r.x)},${Math.round(r.y)}` }; }, SELF);
  log('自建主体节点：', JSON.stringify(out.selfInfo));

  // ---- P1：结构清点（一个实例，但逐层量）----
  out.p1 = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const s = (() => { const e = document.querySelector('.react-flow__viewport');
      const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; })();
    const r = n.getBoundingClientRect();
    // 逐层量：把每一层「可见后代」都量一遍（批次 79 的做法，用来证伪某个层是 310）
    const layers = [];
    n.querySelectorAll('*').forEach((e) => {
      const b = e.getBoundingClientRect();
      if (b.width <= 0 || b.height <= 0) return;
      const cs = getComputedStyle(e);
      if (cs.visibility === 'hidden' || cs.display === 'none') return;
      layers.push({ tag: e.tagName, tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
        screen: `${Math.round(b.width)}×${Math.round(b.height)}`,
        canvas: s ? `${Math.round((b.width / s) * 100) / 100}×${Math.round((b.height / s) * 100) / 100}` : null,
        dep: (() => { let d = 0, c = e; while ((c = c.parentElement)) if (c === n) break; else d++; return d; })() });
    });
    return { scale: s, node: { screen: `${Math.round(r.width * 100) / 100}×${Math.round(r.height * 100) / 100}`,
      canvas: s ? Math.round((r.width / s) * 100) / 100 : null },
      innerText: n.innerText.replace(/\s+/g, ' ').trim(),
      innerTestids: Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')),
      innerAria: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
      buttons: n.querySelectorAll('button').length, inputs: n.querySelectorAll('input,textarea').length,
      mediaTags: Array.from(new Set(Array.from(n.querySelectorAll('audio,video,canvas,img')).map((e) => e.tagName))),
      layerCount: layers.length, layers: layers.slice(0, 40) };
  }, SELF);
  log('P1 节点本体：', JSON.stringify(out.p1.node), '｜scale', out.p1.scale);
  log('   innerText：', JSON.stringify(out.p1.innerText));
  log('   内部 testid：', JSON.stringify(out.p1.innerTestids));
  log('   内部 aria：', JSON.stringify(out.p1.innerAria));
  log('   按钮/输入框/媒体：', out.p1.buttons, out.p1.inputs, JSON.stringify(out.p1.mediaTags));
  log(`   可见后代 ${out.p1.layerCount} 层，逐层 canvas 尺寸（前 20）：`);
  out.p1.layers.slice(0, 20).forEach((l) => log(`     d${l.dep} <${l.tag}> ${l.screen} canvas=${l.canvas} tid=${l.tid} aria=${l.aria}`));
  const distinctCanvas = [...new Set(out.p1.layers.map((l) => l.canvas))];
  log('   所有可见层的 canvas 尺寸取值集合：', JSON.stringify(distinctCanvas),
      '｜含 310 的层：', distinctCanvas.filter((c) => c && c.startsWith('310')).length);

  // ---- P3：手柄热区 ----
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
  }, SELF);
  log('P3 手柄 source：', JSON.stringify(out.handles.src));
  log('P3 手柄 target：', JSON.stringify(out.handles.tgt));

  // ---- P4：工具条的三种判据 ----
  const toolbarProbe = (label) => p.evaluate((l) => {
    const n = document.querySelector(`.react-flow__node[data-id="${l.id}"]`);
    const list = (sel) => Array.from(document.querySelectorAll(sel)).map((e) => {
      const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return { screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
        visible: r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && cs.opacity !== '0',
        pe: cs.pointerEvents, op: cs.opacity, childBtns: e.querySelectorAll('button').length,
        inThisNode: n ? n.contains(e) : false }; });
    return { label: l.label, selected: n ? n.classList.contains('selected') : null,
      sel: document.body.innerText.match(/(\d+) selected/)?.[1] ?? '0',
      byTestid: list('[data-testid="node-toolbar"]'),
      byClass: list('.react-flow__node-toolbar'),
      bySelToolbar: list('[data-testid="selection-context-toolbar"]'),
      bySelSurface: list('[data-testid="selection-context-toolbar-surface"]'),
      featureHost: list('[data-testid="node-toolbar-feature-host"]'),
      popupHost: list('[data-testid="selection-context-toolbar-popup-host"]'),
      visibleToolbarish: Array.from(document.querySelectorAll('div,section,aside'))
        .filter((e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
          return r.width > 0 && r.height >= 30 && r.width >= 100
            && /toolbar|context-toolbar|node-toolbar/i.test(String(e.className) + ' ' + (e.getAttribute('data-testid') || ''))
            && cs.visibility !== 'hidden' && cs.opacity !== '0'; })
        .map((e) => { const r = e.getBoundingClientRect();
          return { tid: e.getAttribute('data-testid'), cls: String(e.className).slice(0, 50),
            screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; }).slice(0, 8),
      activeElement: (() => { const a = document.activeElement;
        return { tag: a ? a.tagName : null, aria: a ? a.getAttribute('aria-label') : null,
          type: a ? a.getAttribute('type') : null, value: a ? a.value : null,
          inSubject: n ? n.contains(a) : false }; })() };
  }, { label, id: SELF });

  out.probe = [];
  const probe = async (label) => { const r = await toolbarProbe(label); out.probe.push(r);
    log(`P4 ${label}: selected=${r.selected} sel=${r.sel}`);
    log(`   testid(${r.byTestid.length}) ${JSON.stringify(r.byTestid.map((x) => ({ s: x.screen, v: x.visible, inN: x.inThisNode, btns: x.childBtns })))}`);
    log(`   class(${r.byClass.length}) ${JSON.stringify(r.byClass.map((x) => ({ s: x.screen, v: x.visible, inN: x.inThisNode, btns: x.childBtns })))}`);
    log(`   selToolbar=${JSON.stringify(r.bySelToolbar.map((x) => x.screen))} selSurface=${JSON.stringify(r.bySelSurface.map((x) => x.screen))}`);
    log(`   featureHost=${JSON.stringify(r.featureHost.map((x) => x.screen))} popupHost=${JSON.stringify(r.popupHost.map((x) => x.screen))}`);
    log(`   任何可见 toolbarish：${JSON.stringify(r.visibleToolbarish)}`);
    log(`   activeElement：${JSON.stringify(r.activeElement)}`);
    return r; };

  // ① 取消选中态
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  await probe('①未选中');

  // ② 点中（会触发「选中即自动获焦」）
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
  out.pt = pt;
  log('落点：', JSON.stringify(pt));
  if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1700); await probe('②选中后'); }

  // ---- P5：右键菜单 ----
  if (pt) {
    await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(300);
    await p.mouse.down({ button: 'right' }); await p.waitForTimeout(280); await p.mouse.up({ button: 'right' });
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
  }
}


// ================= 收尾：只删 SELF =================
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
    log(`  第 ${attempt} 次：落点=${JSON.stringify(pt)} 选中=${isSel}`);
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
    log(`  删除尝试 ${attempt}：${res}｜SELF仍在=${still}`);
    if (!still) break;
  }
  const idsNow = await allIds();
  out.selfLeft = idsNow.includes(SELF);
  out.missing = (out.guard ? [] : []).concat(idsNow.length ? [] : []);
  out.missing = await p.evaluate((c) => c, null).catch(() => []);
  out.idsNowCount = idsNow.length;
  log('自建残留：', out.selfLeft, '｜当前 id 数：', idsNow.length, '（建前', out.idsBefore, '）');
}
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }
out.restore = { ok: await setZoom(60) };
out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow(), tool: await toolAria() };
log('缩放归位：', out.restore.ok ? '✅' : '🔴');
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b98b.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
