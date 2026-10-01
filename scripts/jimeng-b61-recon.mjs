// 批次 61 侦察：进入「从画布选择」之后，**画布上到底还有什么可点**？
//
// v2 的四轮全部「未被接受」，而且**点击后目标节点的 aria 读成了 null**
// —— 意味着 `.react-flow__node[data-id=...]` 在拾取模式下**根本不在 DOM 里**。
// 我点的是进入前的旧坐标，落在 1280×720 的遮罩上。
//
// 🔑 这正是批次 50–55 那条纪律的又一次应验：
//   **阴性结果先问「我找的是不是同一个东西」。**
//   我在找一个已经不在那里的东西。
//
// 本轮只做一件事：进入拾取模式后，把**帧里到底渲染了什么**完整倒出来。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OUT = new URL('./_tmp-b61-recon.json', import.meta.url);
const MINE = [];

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);
const reset = async () => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); } };
const selIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const credit = () => p.evaluate(() => (document.body.innerText.match(/(\d[\d,]*)\s*基础会员/) || [])[1] || null);
const statusLine = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const nodeIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const isEmpty = (x, y) => p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); if (!el) return true;
  if (el.closest('.react-flow__node')) return false;
  if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"]')) return false;
  return true; }, [x, y]);
const findEmpty = async () => { for (let y = 110; y <= 630; y += 20) for (let x = 80; x <= 1250; x += 20) { if (x > 1150 && y > 600) continue; if (await isEmpty(x, y)) return { x, y }; } return null; };
const deselect = async () => { await reset(); const e = await findEmpty();
  if (e) { await p.mouse.click(e.x, e.y); await p.waitForTimeout(600); }
  for (let i = 0; i < 3 && (await selIds()).length; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  return (await selIds()).length === 0; };
const selectByScan = async (id) => {
  const pts = await p.evaluate((vid) => { const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return [];
    const r = n.getBoundingClientRect(); const out = [];
    for (let fy = 0.10; fy <= 0.92; fy += 0.06) for (let fx = 0.10; fx <= 0.92; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y);
      if (!el || !el.closest(`.react-flow__node[data-id="${vid}"]`)) continue;
      if (el.closest('button,a,[role="button"],input,textarea,select,[role="menu"],[contenteditable="true"]')) continue;
      out.push({ x, y }); } return out; }, id);
  for (const pt of pts) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(550);
    const s = await selIds(); if (s.length === 1 && s[0] === id) return { ok: true }; }
  return { ok: false };
};
const makeNode = async (kind) => {
  await deselect();
  const rb = await p.evaluate((nm) => { const e = Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button'))
      .find((x) => (x.getAttribute('aria-label') || '').startsWith(nm)); if (!e) return null;
    const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }, kind);
  if (!rb) return { err: `左栏找不到「${kind}」` };
  const pre = await nodeIds();
  await p.mouse.click(rb.cx, rb.cy); await p.waitForTimeout(3000);
  const made = (await nodeIds()).filter((x) => !pre.includes(x));
  if (made.length !== 1) return { err: `新增 ${made.length} 个` };
  MINE.push(made[0]); return { id: made[0] };
};
const deleteById = async (id) => {
  if (!(await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"]`), id))) return 'absent';
  await reset(); if (!(await selectByScan(id)).ok) return 'notselected';
  await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return;
    const r = e.getBoundingClientRect();
    e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 14) })); }, id);
  await p.waitForTimeout(900);
  const ok = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop(); if (!m) return false;
    const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (!it) return false; it.click(); return true; });
  await p.waitForTimeout(1400); await reset(); return ok ? 'deleted' : 'noclick';
};

const out = { startedAt: new Date().toISOString(), rounds: [] };
console.log('=== 批次 61 侦察：拾取模式里到底有什么 ===\n');
console.log('起点:', await statusLine(), '| 积分', await credit(), '\n');

await deselect();
// 造一个「带内容的图片」和一个「空视频」，两者类型不同、空/满不同
const c1 = await makeNode('图片');
await reset();
const c2 = await makeNode('视频');
await reset();
const host = await makeNode('图片');
console.log('候选:', c1.id, '（空图片）', c2.id, '（空视频）', '| 宿主:', host.id, '\n');

const before = await p.evaluate(() => ({
  nodes: Array.from(document.querySelectorAll('.react-flow__node')).map((e) => { const r = e.getBoundingClientRect();
    return { id: e.getAttribute('data-id'), cls: Array.from(e.classList).filter((c) => c.startsWith('react-flow__node-')).join(''),
      aria: e.getAttribute('aria-label'), box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)}` }; }),
  formAria: (document.querySelector('[data-testid="generation-form"]') || {}).getAttribute?.('aria-label'),
}));
console.log('进入前 .react-flow__node 共', before.nodes.length, '个:');
for (const n of before.nodes) console.log('   ', n.id, n.cls, n.box, JSON.stringify(n.aria));

const addRef = await p.$('button[aria-label="添加参考"]');
if (!addRef) { console.error('ABORT: 没有「添加参考」'); await b.close(); process.exit(2); }
await addRef.click(); await p.waitForTimeout(1100);
await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
  const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /从画布选择/.test(x.innerText || '')); if (it) it.click(); });
await p.waitForTimeout(1500);

const inPicker = await p.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1; };
  const mask = document.querySelector('[data-testid="canvas-source-picker-canvas-mask"]');
  const frame = document.querySelector('[data-testid="canvas-source-picker-canvas-frame"]');
  const dump = (root, label) => root ? {
    label, box: (() => { const r = root.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; })(),
    pe: getComputedStyle(root).pointerEvents, z: getComputedStyle(root).zIndex,
    text: (root.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200),
    children: Array.from(root.children).map((c) => { const r = c.getBoundingClientRect();
      return { tag: c.tagName, tid: c.getAttribute('data-testid'), cls: String(c.className || '').slice(0, 50),
        aria: c.getAttribute('aria-label'), role: c.getAttribute('role'), vis: vis(c),
        box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)}`,
        text: (c.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) }; }),
    // 所有后代里带 aria / data-testid / role 的（可能就是「可选素材」的渲染）
    notable: Array.from(root.querySelectorAll('[data-testid],[aria-label],[role]')).map((e) => { const r = e.getBoundingClientRect();
      return { tag: e.tagName, tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), role: e.getAttribute('role'),
        vis: vis(e), box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)}`,
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) }; }).slice(0, 40),
  } : { label, missing: true };
  return {
    reactFlowNodes: Array.from(document.querySelectorAll('.react-flow__node')).map((e) => { const r = e.getBoundingClientRect();
      return { id: e.getAttribute('data-id'), box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)}` }; }),
    mask: dump(mask, 'mask'), frame: dump(frame, 'frame'),
    srOnly: Array.from(document.querySelectorAll('[class*="sr-only"]')).map((e) => (e.textContent || '').trim()).filter(Boolean).slice(0, 8),
  };
});
console.log('\n进入拾取模式后：');
console.log('  .react-flow__node 数量 =', inPicker.reactFlowNodes.length, inPicker.reactFlowNodes.map((n) => n.id).join(','));
console.log('  mask:', JSON.stringify({ box: inPicker.mask.box, pe: inPicker.mask.pe, z: inPicker.mask.z, kids: inPicker.mask.children.length }, null, 1));
console.log('  frame:', JSON.stringify({ box: inPicker.frame.box, pe: inPicker.frame.pe, z: inPicker.frame.z, kids: inPicker.frame.children.length }, null, 1));
if (inPicker.frame.notable) { console.log('  frame 内 notable 元素:'); for (const n of inPicker.frame.notable) console.log('     ', JSON.stringify(n)); }
console.log('  sr-only:', JSON.stringify(inPicker.srOnly));
console.log('  状态行:', await statusLine());
out.rounds.push({ before, inPicker });

await reset();
for (const id of MINE) console.log('删', id, await deleteById(id));
for (let t = 0; t < 3; t++) { const z = await zoomOf();
  if (z && z.includes('60%')) { console.log('缩放归位 ok:', z); break; }
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
  const s = 'input[data-testid="canvas-zoom-percent-input"]';
  if (await p.$(s)) { await p.fill(s, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); }
  else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  if (t === 2) console.log('缩放归位 FAILED:', await zoomOf()); }
await reset();
const fin = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
  const mm = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
  return [e.getAttribute('data-id'), mm ? [Math.round(parseFloat(mm[1]) * 100) / 100, Math.round(parseFloat(mm[2]) * 100) / 100] : null]; })));
console.log('终态:', await statusLine(), '| 缩放', await zoomOf(), '| 节点', Object.keys(fin).length, '| 积分', await credit());
console.log('剩余待删:', JSON.stringify(MINE.filter((id) => fin[id])));
out.end = { status: await statusLine(), zoom: await zoomOf(), coords: fin, mineLeft: MINE.filter((id) => fin[id]) };
writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log('写入', OUT.pathname);
await b.close();
