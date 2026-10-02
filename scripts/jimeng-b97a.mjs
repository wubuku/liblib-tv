// 批次 97 · a 轮：**只读**清点音频节点。画布上有 31+ 个音频节点（别的会话建的），
// 是做多实例对照的天然样本 —— 批次 94 用「双时间线」赢过一次，这批样本更多。
//
// 本页（`audio-node-voice.md`，普查 79）有三个空白：
//   🔑 **音频节点的右键菜单** —— 文本（`edit-text-node.md` 7 项）、时间线、导演台都有表，
//      **唯独音频没有**。而「不同类型节点的右键菜单是否一样」本身就是个问题。
//   🔑 **音频节点的连接手柄** —— 批次 91 全画布清点时 `source` 比 `target` 少一个（时间线），
//      音频**没有**被单独记过。
//   ⚠️ **本页第 22 行「面板 DOM 为 data-testid="node-toolbar"」** —— 批次 93 已钉
//      该 testid 命中 **2**（1 真身 + 1 `0×0` 占位），批次 95 又发现**编辑态下命中 0**。
//      ⇒ 这个定位符**需要加限定**，本轮实测确认。
//
// 🔴 共享画布纪律：本轮**全程只读**（只切换选中态与工具态，测完归位），
//    **不建节点、不点 `Play`/`Add`**（那会改节点内容）、不点任何扣费按钮。
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
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomLabel = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return e ? e.getAttribute('aria-label') : null; });
const scaleNow = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });
const toolAria = () => p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return t ? t.getAttribute('aria-label') : null; });

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow(), tool: await toolAria() };
log('起点：', JSON.stringify(out.start));

// ---- P1：全画布音频节点清点（离屏可量，批次 95 §4.15.5 的简化）----
const sc = await scaleNow();
out.p1 = await p.evaluate((s) => {
  const rows = [];
  for (const n of document.querySelectorAll('.react-flow__node-audio')) {
    const r = n.getBoundingClientRect();
    const m = /translate\(([^)]+)\)/.exec(n.style.transform || '');
    rows.push({ id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
      screen: { w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100 },
      canvas: s ? { w: Math.round((r.width / s) * 100) / 100, h: Math.round((r.height / s) * 100) / 100 } : null,
      translate: m ? m[1] : null,
      inView: r.right > 0 && r.bottom > 0 && r.left < 1280 && r.top < 720,
      innerText: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 40),
      // 节点**内部**的子元素（区分静态结构与选中态 chrome）
      innerTestids: Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')),
      innerAria: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]'))
        .map((e) => e.getAttribute('aria-label')))).slice(0, 12),
      buttons: n.querySelectorAll('button').length,
      mediaTags: Array.from(new Set(Array.from(n.querySelectorAll('audio,video,canvas'))
        .map((e) => e.tagName))) });
  }
  return rows;
}, sc);
log(`P1 音频节点共 ${out.p1.length} 个：`);
const canvasSet = [...new Set(out.p1.map((r) => r.canvas ? `${r.canvas.w}×${r.canvas.h}` : '?'))];
log('   canvas 尺寸取值集合：', JSON.stringify(canvasSet));
log('   样例：', JSON.stringify(out.p1.slice(0, 3).map((r) => ({ aria: r.aria, screen: r.screen, canvas: r.canvas, innerTestids: r.innerTestids, buttons: r.buttons, mediaTags: r.mediaTags }))));
const tidFreq = {};
out.p1.forEach((r) => r.innerTestids.forEach((t) => { tidFreq[t] = (tidFreq[t] || 0) + 1; }));
log('   节点内部 testid 频次：', JSON.stringify(tidFreq));
const ariaFreq = {};
out.p1.forEach((r) => r.innerAria.forEach((a) => { ariaFreq[a] = (ariaFreq[a] || 0) + 1; }));
log('   节点内部 aria 频次（前 12）：', JSON.stringify(Object.entries(ariaFreq).sort((x, y) => y[1] - x[1]).slice(0, 12)));

// ---- P2：全画布手柄清点（按节点类型）----
out.p2 = await p.evaluate(() => {
  const byType = {};
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const cls = n.className.split(/\s+/).filter((c) => c.startsWith('react-flow__node-'))[0] || 'other';
    const src = n.querySelectorAll('.react-flow__node-source-handle, [data-testid="flow-node-source-handle"]').length;
    const tgt = n.querySelectorAll('.react-flow__node-target-handle, [data-testid="flow-node-target-handle"]').length;
    byType[cls] = byType[cls] || { n: 0, withSrc: 0, withTgt: 0 };
    byType[cls].n++;
    if (src) byType[cls].withSrc++;
    if (tgt) byType[cls].withTgt++;
  }
  return byType;
});
log('P2 按类型的手柄清点：', JSON.stringify(out.p2, null, 0));

// ---- P3：找一个独占的音频节点（批次 96 的判据），读三态 ----
await p.keyboard.press('Meta+0'); await p.waitForTimeout(2000);
out.fit = { zoom: await zoomLabel(), scale: await scaleNow() };
log('适配：', JSON.stringify(out.fit));

const findExcl = () => p.evaluate(() => {
  const INTERACTIVE = 'BUTTON,INPUT,A,TEXTAREA,SELECT,[role="button"],[contenteditable="true"]';
  const rows = [];
  for (const n of document.querySelectorAll('.react-flow__node-audio')) {
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
  return rows.filter((r) => r.self === r.tot && r.tot >= 9 && r.goodPt).sort((x, y) => y.w * y.h - x.w * x.h);
});
out.cands = await findExcl();
log('独占音频节点候选：', JSON.stringify(out.cands.slice(0, 4)));
const TID = out.cands[0] ? out.cands[0].id : null;
out.pick = out.cands[0] || null;
log('锁定：', TID);

if (TID) {
  const read = (label) => p.evaluate((l) => {
    const n = document.querySelector(`.react-flow__node[data-id="${l.id}"]`);
    const cnt = (t) => document.querySelectorAll(`[data-testid="${t}"]`).length;
    const geo = (t) => { const e = document.querySelector(`[data-testid="${t}"]`); if (!e) return null;
      const r = e.getBoundingClientRect(); return `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; };
    return { label: l.label, selected: n ? n.classList.contains('selected') : null,
      sel: document.body.innerText.match(/(\d+) selected/)?.[1] ?? '0',
      editable: document.querySelectorAll('[contenteditable="true"],.ProseMirror').length,
      srcHandle: document.querySelectorAll('.flow-node-source-handle,[data-testid="flow-node-source-handle"]').length,
      tgtHandle: document.querySelectorAll('.flow-node-target-handle,[data-testid="flow-node-target-handle"]').length,
      tids: { nodeToolbar: cnt('node-toolbar'), featureHost: cnt('node-toolbar-feature-host'),
        audioForm: cnt('audio-generation-form'), promptEditor: cnt('generation-prompt-editor'),
        submit: cnt('generation-submit-icon'), selToolbar: cnt('selection-context-toolbar'),
        selSurface: cnt('selection-context-toolbar-surface'), resize: cnt('text-node-resize-controls'),
        chromeHost: cnt('node-feature-chrome-host'), srcConnBtn: cnt('flow-node-source-connection-menu-button') },
      geo: { nodeToolbar: geo('node-toolbar'), selSurface: geo('selection-context-toolbar-surface'),
        selToolbar: geo('selection-context-toolbar'), audioForm: geo('audio-generation-form'),
        promptEditor: geo('generation-prompt-editor'), submit: geo('generation-submit-icon') },
      nodeInnerAria: n ? Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]'))
        .map((e) => e.getAttribute('aria-label')))) : null };
  }, { label, id: TID });
  const cell = async (label) => { const c = await read(label); out.cells = out.cells || []; out.cells.push(c);
    log(`${label}: sel=${c.sel} 选中=${c.selected} nodeToolbar=${c.tids.nodeToolbar} form=${c.tids.audioForm} ` +
        `surface=${c.geo.selSurface} src=${c.srcHandle} tgt=${c.tgtHandle}`);
    return c; };

  out.p3 = [];
  out.p3.push(await cell('①未选中'));
  // 点一次选中
  await p.mouse.click(out.pick.goodPt.x, out.pick.goodPt.y); await p.waitForTimeout(1400);
  out.p3.push(await cell('②选中'));
  // 右键菜单
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
          disabled: x.getAttribute('aria-disabled') }; }) };
  });
  log('③右键菜单：', out.menu ? `${out.menu.screen}` : 'null');
  if (out.menu) { out.menu.items.forEach((i, n) => log(`   ${n + 1}. ${i.text}  ${i.w}×${i.h} disabled=${i.disabled}`)); }
  out.p3.push(await cell('③右键后'));
  if (out.menu) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  out.p3.push(await cell('④Esc后'));
  out.selectedNodeAria = out.p3[1]?.nodeInnerAria;
}

// 收尾：Esc + 工具态 + 缩放
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }
out.restore = {};
for (let k = 1; k <= 4; k++) {
  const zl = await zoomLabel();
  if (zl && /, 60%$/.test(zl)) { out.restore = { ok: true, tries: k - 1 }; break; }
  await p.click('[data-testid="canvas-zoom-percent"]'); await p.waitForTimeout(1000);
  if (await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) {
    await p.evaluate(() => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, '60');
      i.dispatchEvent(new Event('input', { bubbles: true }));
      i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); });
    await p.waitForTimeout(1700);
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  if (k === 4) out.restore = { ok: false, tries: 4 };
}
out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow(), tool: await toolAria() };
log('缩放归位：', JSON.stringify(out.restore), out.restore.ok ? '✅' : '🔴');
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b97a.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
