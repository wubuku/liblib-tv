// 批次 62 收尾取证：有效的遮挡对照 + 收起态/两个浮层的配图 + 视口与缩放归位。
//
// 两个自伤要在这里一并记账：
//   ① `scrollIntoView` 会把**画布视口**一起滚走 —— 探测三里 6 个节点的屏幕坐标
//      全部跑到负数（`视频 1` 跑到 (-481,-189)），遮挡探针四个点全打空。
//      **canvas 坐标与缩放都没变**（Δ=0 / 60%），所以没有实质损坏，
//      但它把「屏幕坐标不可用于位置判断」这条又演示了一遍 —— `jimeng-safe-keys.mjs`
//      早就写了这句注释，我这批还是踩了。
//   ② 遮挡对照**不能靠搬别人的节点**去制造重叠（共享画布纪律）。
//      改用零成本的对照法：**同一个坐标，比展开态与收起态的 `elementFromPoint`**。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const OUT = new URL('./_tmp-b62-shots.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);

const statusLine = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const canvasPos = () => p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
  return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
const sidecar = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-feature-sidecar"]');
  if (!e) return { st: 'ABSENT' }; const r = e.getBoundingClientRect();
  const panel = e.querySelector('[data-testid="canvas-agent-panel"]');
  return { st: panel ? 'EXPANDED' : 'COLLAPSED', box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    pe: getComputedStyle(e).pointerEvents, z: getComputedStyle(e).zIndex,
    visKids: Array.from(e.querySelectorAll('*')).filter((x) => { const b = x.getBoundingClientRect(); return b.width > 1 && b.height > 1; }).length }; });
const pops = () => p.evaluate(() => Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"],[data-testid="agent-skill-menu"]'))
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { tid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
      box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      inSidecar: !!e.closest('[data-testid="canvas-feature-sidecar"]'), text: (e.innerText || '').replace(/\s+/g, ' ').trim() }; }));
// 🔑 遮挡对照：同一批坐标，在展开态与收起态各打一次。
// 收起态侧栏 pointer-events:none ⇒ elementFromPoint 应当**穿透**。
const probePts = (pts) => p.evaluate((ps) => ps.map(([x, y]) => { const t = document.elementFromPoint(x, y);
  if (!t) return { x, y, hit: 'null' };
  const sc = t.closest('[data-testid="canvas-feature-sidecar"]');
  return { x, y, hit: `${t.tagName}${t.getAttribute('data-testid') ? '[' + t.getAttribute('data-testid') + ']' : ''}`,
    inSidecar: !!sc, aria: (t.getAttribute('aria-label') || '').slice(0, 40) }; }), pts);
const clickCollapse = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-agent-session-collapse"]');
  if (!e || e.getBoundingClientRect().width < 1) return 'no-btn';
  const r = e.getBoundingClientRect();
  const o = (document.elementFromPoint(Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)) || {}).closest?.('button');
  if (o !== e) return 'occluded'; e.click(); return 'clicked'; });
const openDrawer = async () => { if ((await sidecar()).st === 'EXPANDED') return 'already';
  const rb = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button'))
    .find((x) => /与\s*AI\s*对话/.test(x.getAttribute('aria-label') || '')); if (!e) return null;
    const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
  if (!rb) return 'nobtn'; await p.mouse.click(rb.cx, rb.cy); await p.waitForTimeout(1600); return 'ok'; };
const clearComposer = async () => { await p.evaluate(() => { const c = document.querySelector('.tiptap.ProseMirror[contenteditable="true"]');
  if (!c) return; c.focus(); document.execCommand('selectAll', false, null); document.execCommand('delete', false, null);
  if ((c.innerText || '').trim()) { c.innerHTML = ''; c.dispatchEvent(new InputEvent('input', { bubbles: true, data: '', inputType: 'deleteContentBackward' })); } });
  await p.waitForTimeout(400); return p.evaluate(() => { const c = document.querySelector('.tiptap.ProseMirror[contenteditable="true"]');
    return { text: c ? (c.innerText || '') : null, chips: c ? c.querySelectorAll('[data-testid="agent-skill-chip"]').length : 0 }; }); };
// 聚焦：点固定的输入卡坐标，**不用 scrollIntoView**（那会滚走画布视口）
const focusEditor = async () => { const c = await p.evaluate(() => { const e = document.querySelector('.tiptap.ProseMirror[contenteditable="true"]');
  if (!e) return null; const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + 24), cy: Math.round(r.y + 24) }; });
  if (!c) return false; await p.mouse.click(c.cx, c.cy); await p.waitForTimeout(450);
  return p.evaluate(() => !!(document.activeElement && document.activeElement.closest('.tiptap.ProseMirror'))); };
const shot = async (n, clip) => { await p.screenshot({ path: new URL(n, SHOTS).pathname, clip }); console.log('  📷', n, JSON.stringify(clip)); return n; };
const DRAWER = { x: 860, y: 8, width: 412, height: 700 };
const SHELL = { x: 1040, y: 340, width: 240, height: 380 };

const out = { startedAt: new Date().toISOString() };
const c0 = await credit();
console.log('=== 批次 62 收尾取证 ===\n起点:', await statusLine(), '| 积分', c0, '| 缩放', await zoomOf(), '| 侧栏', JSON.stringify(await sidecar()));
out.start = { status: await statusLine(), credit: c0, zoom: await zoomOf(), sidecar: await sidecar() };
out.canvasStart = await canvasPos();

await openDrawer();
// 展开态：取一批落在**侧栏范围内**的坐标
const sExp = await sidecar();
console.log('\n展开态侧栏:', JSON.stringify(sExp));
const sb = await p.evaluate(() => { const r = document.querySelector('[data-testid="canvas-feature-sidecar"]').getBoundingClientRect();
  return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; });
const PTS = [[sb.x + 20, sb.y + 60], [sb.x + 200, sb.y + 200], [sb.x + 100, sb.y + 400], [sb.x + 380, sb.y + 640], [sb.x + 380, sb.y + 100]];
console.log('对照坐标:', JSON.stringify(PTS));
const hitExp = await probePts(PTS);
console.log('展开态命中:'); for (const h of hitExp) console.log(`  (${h.x},${h.y}) ${h.hit}  在侧栏内=${h.inSidecar} ${h.aria}`);
out.hitExpanded = hitExp;
await shot('62-agent-expanded.png', DRAWER);

// 「/」浮层配图
console.log('\n清空 =', JSON.stringify(await clearComposer()), '| 聚焦 =', await focusEditor());
await p.keyboard.press('/');
await p.waitForTimeout(1500);
const pSlash = await pops();
console.log('`/` 后浮层:'); for (const x of pSlash) console.log(`  tid=${x.tid} role=${x.role} box=${x.box} 在侧栏内=${x.inSidecar}`); console.log('   text=', JSON.stringify(pSlash.map((x) => x.text.slice(0, 200))));
out.slash = pSlash;
await shot('62-agent-slash-menu.png', DRAWER);

// `@` 浮层配图
console.log('\n关浮层 =', (await p.keyboard.press('Escape'), await p.waitForTimeout(900), (await pops()).length === 0));
console.log('清空 =', JSON.stringify(await clearComposer()), '| 聚焦 =', await focusEditor());
await p.keyboard.press('@');
await p.waitForTimeout(1500);
const pAt = await pops();
console.log('`@` 后浮层:'); for (const x of pAt) console.log(`  tid=${x.tid} role=${x.role} box=${x.box} 在侧栏内=${x.inSidecar}`); console.log('   text=', JSON.stringify(pAt.map((x) => x.text)));
out.at = pAt;
await shot('62-agent-at-menu.png', DRAWER);

// ── 折叠态：遮挡对照 + 配图
console.log('\n点收起 =', await clickCollapse());
await p.waitForTimeout(1500);
const sCol = await sidecar();
console.log('折叠态侧栏:', JSON.stringify(sCol));
const hitCol = await probePts(PTS);
console.log('折叠态命中:'); for (const h of hitCol) console.log(`  (${h.x},${h.y}) ${h.hit}  在侧栏内=${h.inSidecar} ${h.aria}`);
out.sidecarCollapsed = sCol; out.hitCollapsed = hitCol;
const passThrough = hitExp.filter((h) => h.inSidecar).length > 0 && hitCol.every((h) => !h.inSidecar);
console.log('  => 折叠态是否完全穿透:', passThrough ? 'YES（pointer-events:none 生效）' : 'no（要再看）');
out.passThrough = passThrough;
await shot('62-agent-collapsed-shell.png', SHELL);

// 折叠态能否点画布同坐标：拿一个「点下去会不会选中节点」做行为对照
console.log('\n行为对照：同一坐标点击，看节点能否被选中');
const c0sel = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
// 在侧栏范围外找一个真实节点
const nodePt = await p.evaluate(() => { for (const n of document.querySelectorAll('.react-flow__node')) {
  const r = n.getBoundingClientRect(); if (r.width < 1 || r.left < 4 || r.top < 4 || r.right > innerWidth - 4 || r.bottom > innerHeight - 4) continue;
  const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
  const t = document.elementFromPoint(x, y); if (!t || !t.closest('.react-flow__node')) continue;
  return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'), x, y }; } return null; });
console.log('  可点节点:', JSON.stringify(nodePt), '| 当前选中数 =', c0sel);
if (nodePt) { await p.mouse.click(nodePt.x, nodePt.y); await p.waitForTimeout(800);
  const c1sel = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
  console.log('  折叠态点它 → 选中:', JSON.stringify(c1sel), c1sel.length === 1 ? '<< 穿透生效' : '');
  out.clickThrough = { node: nodePt, selected: c1sel };
  for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(300); }
}

// ── 归位：视口平移（scrollIntoView 造成的）+ 缩放 60%
console.log('\n归位：视口 =', await p.evaluate(() => (document.querySelector('.react-flow__viewport') || {}).style?.transform));
const g = await keyGuard(p);
if (g.safe) { await p.keyboard.press('Shift+Digit1'); await p.waitForTimeout(1300); console.log('  ⇧1 适配画布后 缩放 =', await zoomOf(), '视口 =', await p.evaluate(() => (document.querySelector('.react-flow__viewport') || {}).style?.transform)); }
for (let t = 0; t < 3; t++) { const z = await zoomOf();
  if (z && z.includes('60%')) { console.log('  缩放归位 ok:', z); break; }
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
  const s = 'input[data-testid=canvas-zoom-percent-input]';
  if (await p.$(s)) { await p.fill(s, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); }
  else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  if (t === 2) console.log('  缩放归位 FAILED:', await zoomOf()); }
// 再看一眼缩放（回读验证）
console.log('  缩放回读 =', await zoomOf(), (await zoomOf()).includes('60%') ? '✓' : '✗');
for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(280); }

const fin = await canvasPos();
console.log('\n终态:', await statusLine(), '| 缩放', await zoomOf(), '| 侧栏', JSON.stringify(await sidecar()), '| 积分', await credit());
console.log('他人节点 canvas 位置核对:');
let dev = 0;
for (const [id, base] of Object.entries(BASE.nodes)) { const cur = fin[id];
  const d = cur && base.canvas ? [Math.round((cur[0] - base.canvas[0]) * 100) / 100, Math.round((cur[1] - base.canvas[1]) * 100) / 100] : 'MISSING';
  if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev++;
  console.log('  ', id, JSON.stringify(base.title), '基线', JSON.stringify(base.canvas), '现', JSON.stringify(cur), 'Δ', JSON.stringify(d)); }
console.log('  偏离节点数 =', dev, dev === 0 ? '✓' : '✗');
out.end = { status: await statusLine(), zoom: await zoomOf(), sidecar: await sidecar(), credit: await credit(), canvas: fin, dev };
writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log('写入', OUT.pathname);
await b.close();
