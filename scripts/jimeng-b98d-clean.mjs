// 批次 98 · d 轮：事故清理。
//
// 🔴 **事故经过**：b98c 里为了「把焦点挪出主体节点」执行了
//    `p.mouse.click(40, 200)` 想点画布空白，但 `(40,200)` **落在左栏里**
//    （`canvas-fixed-toolbar-left-rail` = `160×632@12,72`）⇒ 点中了**左栏的「文本」按钮**
//    ⇒ **建了一个文本节点**。画布 45 → 47。
//    实测读数直接暴露了它：`点空白后 activeElement: {"tag":"BUTTON","aria":"文本"}` ——
//    **点击后立刻读 activeElement 就能发现「我以为点的是空白，实际点的是按钮」**。
//
// 🔑 **两条纪律**：
//   ① **「点画布空白」不是无风险的**。左栏 `160×632@12,72`、底部 dock `164×36@12,668`、
//      右下角 AI 按钮都在视口内。**点空白必须挑一个明确不属于任何固定面板的坐标**，
//      并且**点完立刻读 `activeElement`** 确认没有点中按钮。
//   ② 事故的另一半是 b98c 的采样点扫描拿到 **0 个可用落点**（节点 `80×80@600,329`
//      被别的节点完全盖住）⇒ 主体节点在 45 节点的画布上**不可直接操作**，
//      这也是需要 `Meta+0` 之外手段的原因。
//
// 清理顺序：① 先试 **⌘Z** 撤销那次「建文本节点」（它是最近一次入撤销栈的用户操作，
//         Esc 与工具态切换不入栈）；② 再按已知 id 删主体节点 `node_ek4gvj4ekf`。
//         ⚠️ **绝不用「取最后一个节点」来识别** —— 批次 97 的事故正是死在那一招上。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { readFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const SUBJECT = 'node_ek4gvj4ekf';

const allNodes = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
  const r = e.getBoundingClientRect();
  return { id: e.getAttribute('data-id'), aria: e.getAttribute('aria-label'),
    translate: e.style.transform, screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; }));
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

out.before = { nodes: await nodeN(), list: await allNodes() };
log('清理前：', out.before.nodes, '个节点');
out.before.list.forEach((n) => { if (/主体|文本/.test(n.aria || '')) log('   ', n.id, n.aria, n.translate); });

// ① 先试 ⌘Z 撤销「建文本节点」
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
const g = await keyGuard(p);
out.keyGuard = g;
log('keyGuard：', JSON.stringify(g));
if (g.safe) {
  const beforeIds = new Set(out.before.list.map((n) => n.id));
  for (let k = 1; k <= 3; k++) {
    await p.keyboard.press('Meta+z');
    await p.waitForTimeout(1700);
    const now = await allNodes();
    const gone = [...beforeIds].filter((id) => !now.some((n) => n.id === id));
    const added = now.filter((n) => !beforeIds.has(n.id)).map((n) => n.id);
    log(`⌘Z 第 ${k} 次：节点数 ${out.before.list.length} → ${now.length}｜消失 ${JSON.stringify(gone)}｜新增 ${JSON.stringify(added)}`);
    out[`undo${k}`] = { count: now.length, gone, added };
    if (gone.length === 1 && added.length === 0) { out.undoneId = gone[0]; break; }
    if (now.length < out.before.list.length) break;
    if (k === 3) break;
  }
}
log('⌘Z 结果：', out.undoneId ? `撤销了 ${out.undoneId}` : '未确定');

// ② 按已知 id 删主体节点
out.subjectDelete = { target: SUBJECT, attempts: [] };
for (let attempt = 1; attempt <= 3; attempt++) {
  const alive = await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), SUBJECT);
  if (!alive) { out.subjectDelete.alreadyGone = true; log('主体节点已不在'); break; }
  for (let k = 0; k < 2; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
  const pt = await p.evaluate((i) => {
    const INTERACTIVE = 'BUTTON,INPUT,A,TEXTAREA,SELECT,[role="button"],[contenteditable="true"]';
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
    const r = n.getBoundingClientRect();
    for (let a = 1; a <= 3; a++) for (let c = 1; c <= 3; c++) {
      const x = Math.round(r.x + (r.width * a) / 4), y = Math.round(r.y + (r.height * c) / 4);
      if (x < 2 || y < 2 || x > 1278 || y > 718) continue;
      const e = document.elementFromPoint(x, y);
      if (e && e.closest('.react-flow__node') === n && !e.closest(INTERACTIVE)) return { x, y }; }
    return null; }, SUBJECT);
  if (!pt) { await p.keyboard.press('Meta+0'); await p.waitForTimeout(2000); continue; }
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1300);
  const isSel = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    return n ? n.classList.contains('selected') : false; }, SUBJECT);
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
    if (!it) return 'no-item'; it.click(); return 'clicked'; }, SUBJECT);
  await p.waitForTimeout(1900);
  const still = await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), SUBJECT);
  out.subjectDelete.attempts.push({ attempt, res, still });
  log(`  删除尝试 ${attempt}：${res}｜仍在=${still}`);
  if (!still) break;
}

// ③ 终态核对：与基线节点集合比对
out.after = { nodes: await nodeN(), list: await allNodes() };
log('清理后：', out.after.nodes, '个节点');
out.subjectLeft = out.after.list.some((n) => n.id === SUBJECT);
log('主体节点残留：', out.subjectLeft);
out.after.list.forEach((n) => { if (/主体/.test(n.aria || '')) log('   仍存在主体节点：', n.id, n.aria); });

for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }
out.restore = { ok: await setZoom(60) };
out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), tool: await toolAria() };
log('缩放归位：', out.restore.ok ? '✅' : '🔴');
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b98d-clean.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
