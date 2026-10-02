// 批次 96 · d 轮：在**独占节点**上受控复测，判定两件事。
//
// c 轮暴露了两个问题，读数都不能直接用：
//
//   🔴 **共享画布上的节点在动**：c 轮 ⑬ 的落点是 `(304,190)`，而 diag 轮同一个坐标属于
//      **导演台** `node_pxvkay973v`；c 轮 ② 的落点是 `(274,160)`。
//      ⇒ 「点不中」和「点得中」都可能是**点下去的那一瞬间节点已经挪了**。
//      ⇒ 判据：必须找**独占节点**（rect 内 3×3 共 9 个采样点**全部**归属自己），
//         并在**点击前 0ms** 校验归属、**点击后**立即回执。
//
//   🔴 **按 V 键**：c 轮格 ⑦ 读数是「抓手态 → 按 V → 变成选择工具」，
//      而**批次 90 明确记过「V 键不切工具」**。两条互相矛盾，必须判清 V 到底是
//      **切换**（选择→抓手→选择）还是**复位**（只在抓手下有效）。
//      还要排除一种可能：⑦ 之前刚做过「抓手态双击」，**双击自己改了工具态**。
//      ⇒ 本轮把「按 V」单独成格，前后各读一次，**不夹带任何点击**。
//
// 取证对象：独占节点。9 点全 SELF 是硬前置，不满足就换下一个。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

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

// 「独占节点」判据：rect 内 3×3 共 9 点全部 SELF，且尺寸够点
const findExclusive = () => p.evaluate(() => {
  const rows = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const r = n.getBoundingClientRect();
    if (r.width < 16 || r.height < 16) continue;
    if (r.right < 40 || r.bottom < 40 || r.left > 1240 || r.top > 680) continue;
    let self = 0, tot = 0;
    for (let i = 1; i <= 3; i++) for (let j = 1; j <= 3; j++) {
      const x = Math.round(r.x + (r.width * i) / 4), y = Math.round(r.y + (r.height * j) / 4);
      if (x < 1 || y < 1 || x > 1279 || y > 719) continue;
      tot++;
      const e = document.elementFromPoint(x, y);
      const o = e && e.closest('.react-flow__node');
      if (o && o.getAttribute('data-id') === n.getAttribute('data-id')) self++;
    }
    rows.push({ id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
      w: Math.round(r.width), h: Math.round(r.height), self, tot,
      x: Math.round(r.x), y: Math.round(r.y), cls: n.className });
  }
  rows.sort((a, c) => (c.self / Math.max(c.tot, 1)) - (a.self / Math.max(a.tot, 1)) || c.w - a.w);
  return rows;
});

const read = (label) => p.evaluate((l) => {
  const n = l.id ? document.querySelector(`.react-flow__node[data-id="${l.id}"]`) : null;
  const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return { label: l.label, sel: document.body.innerText.match(/(\d+) selected/)?.[1] ?? '0',
    targetSelected: n ? n.classList.contains('selected') : null, targetPresent: !!n,
    selectedIds: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')),
    editable: document.querySelectorAll('[contenteditable="true"],.ProseMirror').length,
    pointer: { count: document.querySelectorAll('[data-testid="canvas-pointer-tool-toggle"]').length,
      aria: t ? t.getAttribute('aria-label') : null, pressed: t ? t.getAttribute('aria-pressed') : null },
    ctxMenu: !!document.querySelector('[data-testid="canvas-context-menu"]'),
    viewportTransform: document.querySelector('.react-flow__viewport')?.style.transform ?? null };
}, { label, id: TID });
const cell = async (label) => { const c = await read(label); out.cells.push(c);
  log(`${label}: sel=${c.sel} 目标选中=${c.targetSelected} 抓手=${c.pointer.aria}(${c.pointer.pressed}) 右键菜单=${c.ctxMenu} 编辑=${c.editable}`);
  return c; };

// 点击：**点前 0ms** 校验 + **点后**回执
const clickVerify = async (why) => {
  const pt = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
    if (x < 2 || y < 2 || x > 1278 || y > 718) return null;
    const e = document.elementFromPoint(x, y);
    const o = e && e.closest('.react-flow__node');
    return { x, y, owner: o ? o.getAttribute('data-id') : null, tag: e ? e.tagName : null };
  }, TID);
  if (!pt) return { ok: false, why: '点不到' };
  if (pt.owner !== TID) return { ok: false, why: `落点归属是 ${pt.owner}，不是目标 ⇒ 记 VOID`, pt };
  await p.mouse.click(pt.x, pt.y);
  await p.waitForTimeout(1300);
  const after = await p.evaluate((c) => {
    const e = document.elementFromPoint(c.x, c.y);
    const o = e && e.closest('.react-flow__node');
    const n = document.querySelector(`.react-flow__node[data-id="${c.id}"]`);
    return { owner: o ? o.getAttribute('data-id') : null,
      sel: document.body.innerText.match(/(\d+) selected/)?.[1] ?? '0',
      targetSelected: n ? n.classList.contains('selected') : null }; }, { x: pt.x, y: pt.y, id: TID });
  return { ok: true, pt, after, why };
};

// 归位：Esc 到底 + 工具态归位
out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow(), tool: await toolAria() };
log('起点：', JSON.stringify(out.start));
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1200); }
out.toolFixed = await toolAria();
log('工具态：', out.start.tool, '→', out.toolFixed);

// 适配全画布，让候选节点都进视野
await p.keyboard.press('Meta+0'); await p.waitForTimeout(2000);
out.fit = { zoom: await zoomLabel(), scale: await scaleNow() };
log('适配：', JSON.stringify(out.fit));

// 找一个独占节点（连量两次，两次结果相同才用）
out.cands = await findExclusive();
log('候选（按独占率排序，前 5）：');
out.cands.slice(0, 5).forEach((c) => log(`   ${c.aria} ${c.w}×${c.h}@${c.x},${c.y} 独占 ${c.self}/${c.tot}`));
const pick = out.cands.find((c) => c.self === c.tot && c.tot >= 9);
out.candsTwice = await findExclusive();
const pick2 = out.candsTwice.find((c) => c.self === c.tot && c.tot >= 9);
out.pick = pick2 || pick;
TID = out.pick ? out.pick.id : null;
log('锁定独占节点：', TID, JSON.stringify(out.pick));

if (!TID) { log('🔴 画布上找不到 9/9 独占的节点，本轮记 VOID'); }
else {
  // ---- 实验一：V 键是「切换」还是「复位」（不夹带任何点击）----
  out.expV = [];
  await cell('V0-起点(选择工具)');
  let g = await keyGuard(p);
  if (g.safe) { await p.keyboard.press('v'); await p.waitForTimeout(1200);
    const c1 = await cell('V1-选择工具态按V'); out.expV.push({ from: '选择工具', to: c1.pointer.aria }); }
  else { log('⛔ keyGuard 拒绝：', JSON.stringify(g)); out.expV.push({ from: '选择工具', refused: true }); }

  g = await keyGuard(p);
  if (g.safe) { await p.keyboard.press('v'); await p.waitForTimeout(1200);
    const c2 = await cell('V2-再按一次V'); out.expV.push({ from: out.expV[0]?.to ?? '?', to: c2.pointer.aria }); }
  else { log('⛔ keyGuard 拒绝：', JSON.stringify(g)); out.expV.push({ refused: true }); }

  g = await keyGuard(p);
  if (g.safe) { await p.keyboard.press('v'); await p.waitForTimeout(1200);
    const c3 = await cell('V3-第三次按V'); out.expV.push({ from: '?', to: c3.pointer.aria }); }
  else log('⛔ keyGuard 拒绝：', JSON.stringify(g));

  // 无论上面走到哪个态，**用点 toggle 归位到选择工具**，再切抓手（不靠按键）
  if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1200); }
  await cell('V4-点toggle归位到选择工具');

  // ---- 实验二：抓手态下 左键 / 右键 对节点的影响 ----
  await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1200);
  const g1 = await cell('G1-切到抓手');
  out.inGrab = g1.pointer.aria === '抓手工具';

  out.clickGrab = await clickVerify('抓手态单击');
  await p.waitForTimeout(400);
  const g2 = await cell('G2-抓手-单击');
  out.grabLeftClickSelects = g2.targetSelected === true;
  log('   抓手单击回执：', JSON.stringify(out.clickGrab));

  // 抓手态右键（分两段：先按后停再放）
  await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const r = n.getBoundingClientRect(); window.__pt = { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, TID);
  const rp = await p.evaluate(() => window.__pt);
  await p.mouse.move(rp.x, rp.y); await p.waitForTimeout(250);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1500);
  const g3 = await cell('G3-抓手-右键');
  out.grabRightClickSelects = g3.targetSelected === true;
  out.grabRightClickMenu = g3.ctxMenu;
  if (g3.ctxMenu) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); }

  // ---- 实验三：退出抓手态后左键是否恢复 ----
  if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1200); }
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  const g4 = await cell('G4-退出抓手-Esc后(未选中)');
  out.clickAfterExit = await clickVerify('退出抓手后单击');
  await p.waitForTimeout(400);
  const g5 = await cell('G5-退出抓手-单击');
  out.afterExitSelects = g5.targetSelected === true;
  log('   退出后单击回执：', JSON.stringify(out.clickAfterExit));
}

// 收尾：工具态 + 选中态 + 缩放 三项归位
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
const t0 = await toolAria();
if (t0 !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }
out.restore = {};
for (let k = 1; k <= 4; k++) {
  const zl = await zoomLabel();
  if (zl && /, 60%$/.test(zl)) { out.restore = { ok: true, tries: k - 1 }; break; }
  await p.click('[data-testid="canvas-zoom-percent"]'); await p.waitForTimeout(1000);
  const has = await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'));
  if (has) {
    await p.evaluate(() => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, '60');
      i.dispatchEvent(new Event('input', { bubbles: true }));
      i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); });
    await p.waitForTimeout(1700);
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  if (k === 4) out.restore = { ok: false, tries: 4, note: '弹层无 canvas-zoom-percent-input' };
}
out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow(), tool: await toolAria() };
log('缩放归位：', JSON.stringify(out.restore), out.restore.ok ? '✅' : '🔴');
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b96d.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
