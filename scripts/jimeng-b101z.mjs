// 批次 101 · 收尾：① 补最后一个只读读数（选中态浮动工具条里有没有「全屏/下载」）
//                     ② 按 id **精确删除**自建节点（批次 97 事故后立的三重护栏）
//                     ③ 归位缩放 / 工具态 / 选中数
//
// 🔴 **三重护栏（批次 97 事故后立的，删别人的节点就是那次事故）**：
//   ① `SELF` **只能**来自「删前 id 集合 − 删后 id 集合」的差集，且差集**恰好一个**
//   ② 事后核对「本轮消失的 id」**恰好只有 SELF**
//   ③ **绝不用**「取最后一个」「取 selected 的」猜
//
// 删法：**右键菜单 → 删除**（批次 95 结论：`Delete` 键无效）。
//   ⚠️ 编辑态下右键菜单弹不出来 ⇒ 若节点已选中，必须先 `Esc` 两次回到「未选中」再点一次选中。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), selfId: 'node_fxhrsbbfrz' };
const SELF = out.selfId;

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const selN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]');
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

// ---------- ① 选中态浮动工具条的内容（只读；手册第 29 行说尾部有「全屏/下载」） ----------
out.toolbar = await p.evaluate(() => {
  const tbs = Array.from(document.querySelectorAll('.react-flow__node-toolbar'));
  return tbs.map((t) => {
    const r = t.getBoundingClientRect();
    return { rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      buttons: Array.from(t.querySelectorAll('button,[role=button],[role=menuitem]')).map((e) => {
        const q = e.getBoundingClientRect();
        return { tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
          txt: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
          w: Math.round(q.width), h: Math.round(q.height) }; }) };
  });
});
log('浮动工具条：', JSON.stringify(out.toolbar, null, 1));

// ---------- ② 护栏 ①：记下删前全画布 id ----------
out.idsBefore = await allIds();
const before = new Set(out.idsBefore);
log('删前 id 数：', out.idsBefore.length, '｜含 SELF？', before.has(SELF));

// ---------- 确保 SELF 处于「已选中但不是编辑态」 ----------
for (let k = 0; k < 2; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); }
out.idsAfterEsc = await allIds();
log('Esc 两次后 SELF 还在？', out.idsAfterEsc.includes(SELF), '｜id 数', out.idsAfterEsc.length);

const cur = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { gone: true };
  const s = n.querySelector('[data-testid="video-flow-node-surface"]').getBoundingClientRect();
  const x = Math.round(s.x + s.width / 2), y = Math.round(s.y + s.height * 0.2);
  const el = document.elementFromPoint(x, y);
  return { selected: n.classList.contains('selected'), point: [x, y],
    insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)), hitTag: el ? el.tagName : null }; }, SELF);
log('当前状态：', JSON.stringify(cur));
if (cur.gone) { log('🔴 SELF 已不在（可能被别人删了）⇒ 跳过删除，直接归位'); }
else {
  if (!cur.selected) {
    await p.mouse.move(cur.point[0], cur.point[1]); await p.waitForTimeout(400);
    await p.mouse.click(cur.point[0], cur.point[1]); await p.waitForTimeout(1200);
    log('点选后 selected =', await p.evaluate((i) => document.querySelector(`.react-flow__node[data-id="${i}"]`).classList.contains('selected'), SELF));
  }
  // 右键菜单：必须 move → down → 停 260ms → up（批次 96 结论，DOM click() 打不开）
  const rc = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const s = n.querySelector('[data-testid="video-flow-node-surface"]').getBoundingClientRect();
    return [Math.round(s.x + s.width / 2), Math.round(s.y + s.height * 0.2)]; }, SELF);
  log('右键落点：', JSON.stringify(rc));
  await p.mouse.move(rc[0], rc[1]); await p.waitForTimeout(300);
  await p.mouse.move(rc[0], rc[1]); await p.waitForTimeout(200);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1000);
  out.menu = await p.evaluate(() => {
    const menus = Array.from(document.querySelectorAll('[role=menu]'));
    return menus.map((m) => { const r = m.getBoundingClientRect();
      return { rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
        items: Array.from(m.querySelectorAll('[role=menuitem]')).map((e) => {
          const q = e.getBoundingClientRect();
          return { txt: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
            disabled: e.getAttribute('aria-disabled') === 'true' || e.hasAttribute('disabled'),
            rect: `${Math.round(q.x)},${Math.round(q.y)} ${Math.round(q.width)}×${Math.round(q.height)}` }; }) }; });
  });
  log('右键菜单：', JSON.stringify(out.menu, null, 1));

  const del = await p.evaluate(() => {
    for (const m of document.querySelectorAll('[role=menu]')) {
      for (const it of m.querySelectorAll('[role=menuitem]')) {
        const t = (it.innerText || '').trim();
        if (t === '删除' || t.startsWith('删除')) { const r = it.getBoundingClientRect();
          return { point: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], txt: t,
            disabled: it.getAttribute('aria-disabled') === 'true' }; } } }
    return null; });
  log('删除项：', JSON.stringify(del));
  if (!del || del.disabled) { log('🔴 没找到可点的「删除」⇒ 不删（宁可留一个自建节点，也不误伤别人）'); }
  else {
    const land = await p.evaluate(([x, y, i]) => { const el = document.elementFromPoint(x, y);
      return { hitTag: el ? el.tagName : null, hitRole: el ? el.getAttribute('role') : null,
        txt: el ? (el.innerText || '').trim() : null,
        insideSelfNode: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)) }; }, [del.point[0], del.point[1], SELF]);
    log('删除项落点校验：', JSON.stringify(land));
    if (land.hitRole === 'menuitem' && land.txt === del.txt) {
      await p.mouse.move(del.point[0], del.point[1]); await p.waitForTimeout(350);
      await p.mouse.click(del.point[0], del.point[1]);
      await p.waitForTimeout(1800);
    } else log('  🔴 落点不对 ⇒ 不点');
  }
}

// ---------- 护栏 ③：核对「本轮消失的 id」 ----------
await p.waitForTimeout(1200);
out.idsAfter = await allIds();
const after = new Set(out.idsAfter);
out.vanished = out.idsBefore.filter((id) => !after.has(id));
out.appeared = out.idsAfter.filter((id) => !before.has(id));
log('护栏：删前', out.idsBefore.length, '→ 删后', out.idsAfter.length);
log('  本轮消失的 id：', JSON.stringify(out.vanished));
log('  本轮新增的 id：', JSON.stringify(out.appeared));
out.guardOk = out.vanished.length === 1 && out.vanished[0] === SELF;
log('  ⇒ 消失的**恰好只有 SELF**？', out.guardOk ? '✅' : `🔴 ${JSON.stringify(out.vanished)}`);

// ---------- ③ 归位 ----------
log('\n=== 归位 ===');
out.restore = { zoom: [], tool: null };
for (let k = 0; k < 3; k++) {
  await setZoom(60);
  const a = await scaleNow(); await p.waitForTimeout(900); const b2 = await scaleNow();
  const row = { k, pair: [a, b2], same: a !== null && a === b2, label: await zoomLabel() };
  out.restore.zoom.push(row); log(`  缩放第 ${k + 1} 次：`, JSON.stringify(row));
  if (row.same && a === 0.6) break;
}
if (await toolAria() !== '选择工具') {
  await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1200);
}
out.restore.tool = await toolAria();
log('  工具态：', out.restore.tool);
for (let k = 0; k < 2; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(),
  scale: await scaleNow(), tool: await toolAria(), hasSelf: out.idsAfter.includes(SELF) };
log('终态：', JSON.stringify(out.end));
out.clean = out.end.sel === '0' && out.end.scale === 0.6 && out.end.tool === '选择工具' && !out.end.hasSelf;
log('收尾干净？', out.clean ? '✅' : '🔴');

writeFileSync(new URL('./_tmp-b101z.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
