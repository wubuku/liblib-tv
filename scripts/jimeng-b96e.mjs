// 批次 96 · e 轮：修掉 d 轮暴露的**落点判据缺陷**，补上「选择工具 + 单击 → 选中」这条基线。
//
// d 轮三条干净结论：
//   ✅ **抓手态下左键单击节点 → 不选中**（独占节点 9/9、点前 0ms 校验、点后回执）
//   🔴 **抓手态下右键节点 → 会选中、菜单会弹出，且工具态不变**（`sel=1`、`ctxMenu=true`、
//      `pointer` 仍是「抓手工具」）⇒ 「抓手态下点不中」**只对左键成立** —— 这是对批次 90 的补充
//   ✅ **V 键不切工具**：连按三次，工具态恒为「选择工具」（批次 90 复核通过）
//      ⇒ c 轮格 ⑦ 读到的「抓手→选择工具」是**时序串扰**：⑥ 的双击异步切回了工具，
//         效果落在了下一格的读数上。**格子边界会串扰。**
//
// 🔴 d 轮 G5 失败的原因查明了，是个**判据缺陷**而不是产品行为：
//      落点回执写着 `tag: "BUTTON"` —— 时间线节点**内部有按钮**，
//      点它触发的是**那个按钮**，当然不会选中整个节点。
//      ⇒ 「落点归属哪个节点」这**一半**校验不够，还得看**落点上是什么元素**。
//      本轮加一条：**落点上若是 `BUTTON`/`INPUT`/`A`/`TEXTAREA`/`[role=button]`，直接换档**。
//
// 顺带把 c 轮格 ② 那个「选择工具单击没选中」记为 **VOID**（密集区节点被大面积覆盖，
// 详见 `_tmp-b96c-diag.json`：那个节点 7 个采样点只有 1 个归自己），
// 本轮用独占节点重新拿这条基线。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), cells: [] };
let TID = null;

const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const nodeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomLabel = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return e ? e.getAttribute('aria-label') : null; });
const scaleNow = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });
const toolAria = () => p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return t ? t.getAttribute('aria-label') : null; });

// 独占 + 落点上不是可交互元素，两个条件同时满足才用
const findGood = () => p.evaluate(() => {
  const INTERACTIVE = 'BUTTON,INPUT,A,TEXTAREA,SELECT,[role="button"],[contenteditable="true"]';
  const rows = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const r = n.getBoundingClientRect();
    if (r.width < 16 || r.height < 16) continue;
    if (r.right < 60 || r.bottom < 60 || r.left > 1180 || r.top > 640) continue;
    let self = 0, tot = 0, badTag = null, goodPt = null;
    for (let i = 1; i <= 3; i++) for (let j = 1; j <= 3; j++) {
      const x = Math.round(r.x + (r.width * i) / 4), y = Math.round(r.y + (r.height * j) / 4);
      if (x < 1 || y < 1 || x > 1279 || y > 719) continue;
      tot++;
      const e = document.elementFromPoint(x, y);
      const o = e && e.closest('.react-flow__node');
      if (o && o.getAttribute('data-id') === n.getAttribute('data-id')) {
        self++;
        if (!e.closest(INTERACTIVE)) { if (!goodPt) goodPt = { x, y }; }
        else if (!badTag) badTag = e.tagName;
      }
    }
    rows.push({ id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
      w: Math.round(r.width), h: Math.round(r.height), self, tot, goodPt, badTag,
      x: Math.round(r.x), y: Math.round(r.y) });
  }
  return rows.filter((r) => r.self === r.tot && r.tot >= 9 && r.goodPt)
    .sort((a, c) => c.w * c.h - a.w * a.h);
});

const read = (label) => p.evaluate((l) => {
  const n = l.id ? document.querySelector(`.react-flow__node[data-id="${l.id}"]`) : null;
  const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return { label: l.label, sel: document.body.innerText.match(/(\d+) selected/)?.[1] ?? '0',
    targetSelected: n ? n.classList.contains('selected') : null, targetPresent: !!n,
    pointer: { aria: t ? t.getAttribute('aria-label') : null, pressed: t ? t.getAttribute('aria-pressed') : null },
    ctxMenu: !!document.querySelector('[data-testid="canvas-context-menu"]'),
    editable: document.querySelectorAll('[contenteditable="true"],.ProseMirror').length };
}, { label, id: TID });
const cell = async (label) => { const c = await read(label); out.cells.push(c);
  log(`${label}: sel=${c.sel} 目标选中=${c.targetSelected} 抓手=${c.pointer.aria} 右键菜单=${c.ctxMenu} 编辑=${c.editable}`);
  return c; };

// 落点：**点前 0ms** 校验归属 + 元素类型
const clickVerify = async (why, button) => {
  const pt = await p.evaluate((i) => {
    const INTERACTIVE = 'BUTTON,INPUT,A,TEXTAREA,SELECT,[role="button"],[contenteditable="true"]';
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    const pts = [];
    for (let a = 1; a <= 3; a++) for (let b = 1; b <= 3; b++) {
      const x = Math.round(r.x + (r.width * a) / 4), y = Math.round(r.y + (r.height * b) / 4);
      if (x < 2 || y < 2 || x > 1278 || y > 718) continue;
      const e = document.elementFromPoint(x, y);
      const o = e && e.closest('.react-flow__node');
      if (o && o.getAttribute('data-id') !== i) continue;
      if (e.closest(INTERACTIVE)) continue;
      pts.push({ x, y, tag: e.tagName, owner: o ? o.getAttribute('data-id') : null });
    }
    return pts[0] || { blocked: true, w: Math.round(r.width), h: Math.round(r.height) };
  }, TID);
  if (!pt) return { ok: false, why: '节点不在 DOM' };
  if (pt.blocked) return { ok: false, why: `所有落点都落在可交互元素上（节点 ${pt.w}×${pt.h}）`, pt };
  if (button === 'right') {
    await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(250);
    await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
  } else {
    await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(150);
    await p.mouse.click(pt.x, pt.y);
  }
  await p.waitForTimeout(1400);
  const after = await p.evaluate((c) => {
    const n = document.querySelector(`.react-flow__node[data-id="${c.id}"]`);
    return { sel: document.body.innerText.match(/(\d+) selected/)?.[1] ?? '0',
      targetSelected: n ? n.classList.contains('selected') : null,
      ctxMenu: !!document.querySelector('[data-testid="canvas-context-menu"]'),
      pointer: (() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
        return { aria: t ? t.getAttribute('aria-label') : null }; })() }; }, { id: TID });
  return { ok: true, pt, after, why };
};

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow(), tool: await toolAria() };
log('起点：', JSON.stringify(out.start));
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1200); }
out.toolFixed = await toolAria();
await p.keyboard.press('Meta+0'); await p.waitForTimeout(2000);
out.fit = { zoom: await zoomLabel(), scale: await scaleNow() };
log('工具态', out.start.tool, '→', out.toolFixed, '｜适配', JSON.stringify(out.fit));

out.cands = await findGood();
log('合格候选（独占 9/9 + 落点非交互）：');
out.cands.slice(0, 5).forEach((c) => log(`   ${c.aria} ${c.w}×${c.h}@${c.x},${c.y} 落点${c.goodPt.x},${c.goodPt.y}`));
TID = out.cands[0] ? out.cands[0].id : null;
out.pick = out.cands[0] || null;
log('锁定：', TID);

if (!TID) log('🔴 没有合格候选，本轮记 VOID');
else {
  // ① 基线：选择工具 + 单击 → 应当选中
  await cell('①选择工具-起点');
  out.k1 = await clickVerify('选择工具+单击');
  out.k1c = await cell('②选择工具-单击');
  out.selectClickSelects = out.k1c.targetSelected === true;
  log('   回执：', JSON.stringify(out.k1));

  // ② 抓手 + 单击 → 应不选中
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  await cell('③Esc后');
  await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1200);
  await cell('④切到抓手');
  out.k2 = await clickVerify('抓手+单击');
  out.k2c = await cell('⑤抓手-单击');
  out.grabClickSelects = out.k2c.targetSelected === true;
  log('   回执：', JSON.stringify(out.k2));

  // ③ 抓手 + 右键 → 复核「会选中 + 菜单弹出」
  out.k3 = await clickVerify('抓手+右键', 'right');
  out.k3c = await cell('⑥抓手-右键');
  out.grabRightSelects = out.k3c.targetSelected === true;
  out.grabRightMenu = out.k3c.ctxMenu;
  log('   回执：', JSON.stringify(out.k3));
  if (out.k3c.ctxMenu) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); }

  // ④ 退出抓手 + Esc 两次 → 单击应当又选中（这条基线与 ② 对照才成闭环）
  if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1200); }
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  const c4 = await cell('⑦退出抓手-Esc两次(未选中)');
  out.k4 = await clickVerify('退出抓手+单击');
  out.k4c = await cell('⑧退出抓手-单击');
  out.afterExitSelects = out.k4c.targetSelected === true;
  log('   回执：', JSON.stringify(out.k4), '｜⑦前置 sel=', c4.sel, '目标选中=', c4.targetSelected);
}

// 收尾
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
const t0 = await toolAria();
if (t0 !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }
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
writeFileSync(new URL('./_tmp-b96e.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
