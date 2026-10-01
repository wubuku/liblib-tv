// 批次 56：复核手册两条**从未做控制变量**的强结论
//
// 手册原文（organize-group-layout.md）：
//   「**框选是唯一可靠的多选手势**：⌘A 全选不存在，
//     Shift+点选实测反而会**取消**已选中的节点（1 选中 → 0 选中）」
//
// 这两条对读者影响很大（「想全选就用框选」「别用 Shift 加选」），
// 但从没有人在**断言过前置状态**的前提下重测过。
// 本批做受控复测，每一步都先断言前置条件：
//   「1 选中 → 0 选中」这句话的前提是「点之前确实有 1 个选中」；
//   若前置就没成立，这条记录本身就不可信。
//
// 测的动作（全部本地、不扣分）：
//   A1 框选 2 个 → 按 ⌘A
//   A2 框选 2 个 → Shift+点**未选中**的第 3 个
//   A3 框选 2 个 → Shift+点**已在选中**里的第 1 个
//   A4 框选 2 个 → 普通点击其中一个（不带 Shift）
//   A5 单击空白 → 看是否清空选中
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
import { keyGuard, canvasBaseline, diffNodePositions, pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OTHERS = Object.keys(BASELINE.nodes);

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('canvas page not found'); process.exit(1); }
await pinViewport(p);
const reset = async () => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); } };
const real = (l) => l.filter((x) => !String(x).startsWith('__group-resize-chrome__'));
const ids = async () => real(await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id'))));
const selIds = async () => real(await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id'))));
const statusLine = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['(none)'])[0]);
const isEmpty = (x, y) => p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); if (!el) return true;
  if (el.closest('.react-flow__node')) return false;
  if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"]')) return false;
  return true; }, [x, y]);
const findEmpty = async () => { for (let y = 110; y <= 630; y += 20) for (let x = 80; x <= 1250; x += 20) { if (x > 1150 && y > 600) continue; if (await isEmpty(x, y)) return { x, y }; } return null; };
const setTool = async (want) => { const cur = await p.evaluate(() => (document.querySelector('[data-testid="canvas-pointer-tool-toggle"]') || {}).getAttribute?.('aria-label'));
  if (cur !== want) { await p.evaluate(() => document.querySelector('[data-testid="canvas-pointer-tool-toggle"]').click()); await p.waitForTimeout(600); } };
const drag = async (from, tdx, tdy) => { const steps = Math.max(1, Math.ceil(Math.max(Math.abs(tdx), Math.abs(tdy)) / 130));
  await p.mouse.move(from.x, from.y); await p.mouse.down(); await p.waitForTimeout(120);
  for (let i = 1; i <= steps; i++) { await p.mouse.move(from.x + (tdx * i) / steps, from.y + (tdy * i) / steps); await p.waitForTimeout(45); }
  await p.mouse.up(); await p.waitForTimeout(650); };
const panTo = async (CX, CY) => { for (let r = 0; r < 20; r++) {
  const v = await p.evaluate(() => { const e = document.querySelector('.react-flow__viewport'); const m = e && /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/.exec(e.style.transform); return m ? { tx: +m[1], ty: +m[2], scale: +m[3] } : null; });
  if (!v) return false;
  const dx = (640 - CX * v.scale) - v.tx, dy = (480 - CY * v.scale) - v.ty;
  if (Math.abs(dx) < 4 && Math.abs(dy) < 4) return true;
  const s = await findEmpty(); if (!s) return false;
  await drag(s, Math.max(-130, Math.min(130, dx)), Math.max(-90, Math.min(90, dy))); } return false; };
const centerMine = async (myIds) => { for (let r = 0; r < 8; r++) {
  const u = await p.evaluate((I) => { const rs = I.map((id) => { const e = document.querySelector(`.react-flow__node[data-id="${id}"]`); return e ? e.getBoundingClientRect() : null; }).filter(Boolean);
    if (rs.length !== I.length) return null; const x0 = Math.min(...rs.map((r) => r.x)), x1 = Math.max(...rs.map((r) => r.right)), y0 = Math.min(...rs.map((r) => r.y)), y1 = Math.max(...rs.map((r) => r.bottom));
    return { cx: (x0 + x1) / 2, cy: (y0 + y1) / 2 }; }, myIds);
  if (!u) return false; const dx = 640 - u.cx, dy = 480 - u.cy;
  if (Math.abs(dx) < 6 && Math.abs(dy) < 6) return true;
  const s = await findEmpty(); if (!s) return false; await drag(s, Math.max(-130, Math.min(130, dx)), Math.max(-130, Math.min(130, dy))); } return false; };
const deleteById = async (id) => { if (!(await ids()).includes(id)) return 'absent';
  const pt = await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return null; const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 16) }; }, id);
  if (!pt) return 'nobox';
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(650);
  if (await p.evaluate((v) => { const s = document.querySelector('.react-flow__node.selected'); return !s || s.getAttribute('data-id') !== v; }, id)) {
    await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return; const r = e.getBoundingClientRect();
      for (const t of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) e.dispatchEvent(new MouseEvent(t, { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 16) })); }, id);
    await p.waitForTimeout(650); }
  if (await p.evaluate((v) => { const s = document.querySelector('.react-flow__node.selected'); return !s || s.getAttribute('data-id') !== v; }, id)) return 'notselected';
  await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return; const r = e.getBoundingClientRect(); e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 12) })); }, id);
  await p.waitForTimeout(700);
  const ok = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop(); if (!m) return false;
    const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (!it) return false; it.click(); return true; });
  await p.waitForTimeout(1300); return ok ? 'deleted' : 'noclick'; };
const restoreZoom = async () => {
  await reset(); await setTool('选择工具');
  await p.mouse.click(700, 150); await p.waitForTimeout(500);
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(600);
  const z = 'input[data-testid="canvas-zoom-percent-input"]';
  if (await p.$(z)) { await p.fill(z, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(900); }
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(600);
  await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-zoom-menu"]'); const it = m && Array.from(m.querySelectorAll('button,[role="menuitem"]')).find((e) => /适配画布/.test(e.innerText || '')); if (it) it.click(); });
  await p.waitForTimeout(1400);
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  await p.mouse.click(700, 150); await p.waitForTimeout(700);
  // 🔑 「填 60 + Enter」这一步**会偶发不生效**（菜单没真正打开时 p.$ 返回 null 就跳过了），
  //    表现为收尾停在 57%/49%。所以必须**读回来验证**，不行就重试（批次 56 踩过）。
  for (let i = 0; i < 3; i++) {
    const z = await p.evaluate(() => { const b = document.querySelector('button[aria-label^="Zoom options"]'); const m = /([\d.]+)%/.exec(b ? b.getAttribute('aria-label') || '' : ''); return m ? m[1] : null; });
    if (z === '60') return true;
    console.log(`    缩放归位重试 ${i + 1}：当前 ${z}%`);
    await p.keyboard.press('Escape'); await p.waitForTimeout(400);
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
    const inp = 'input[data-testid="canvas-zoom-percent-input"]';
    if (await p.$(inp)) { await p.fill(inp, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1000); }
    await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  }
  return false;
};
// 框选：前后都断言
const frameSelect = async (want) => {
  await reset();
  const mine = await p.evaluate((I) => I.map((id) => { const r = document.querySelector(`.react-flow__node[data-id="${id}"]`).getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; }), want);
  const others = await p.evaluate((I) => I.map((id) => { const e = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!e) return null; const r = e.getBoundingClientRect(); return { id, x: r.x, y: r.y, w: r.width, h: r.height }; }).filter(Boolean), OTHERS);
  const sx = Math.round(Math.min(...mine.map((m) => m.x)) - 28), sy = Math.round(Math.min(...mine.map((m) => m.y)) - 28);
  const ex = Math.round(Math.max(...mine.map((m) => m.x + m.w)) + 24), ey = Math.round(Math.max(...mine.map((m) => m.y + m.h)) + 24);
  const hit = others.filter((o) => o.x < ex && o.x + o.w > sx && o.y < ey && o.y + o.h > sy);
  if (hit.length) { console.log('  ❌ 框选矩形与他人节点相交', hit.map((o) => o.id).join(',')); return false; }
  if ((await selIds()).length) { console.log('  ❌ 框选前已有选中'); return false; }
  if (!(await isEmpty(sx, sy))) { console.log(`  ❌ 起点(${sx},${sy})不空`); return false; }
  await p.mouse.move(sx, sy); await p.mouse.down();
  for (let i = 1; i <= 10; i++) { await p.mouse.move(sx + ((ex - sx) * i) / 10, sy + ((ey - sy) * i) / 10); await p.waitForTimeout(55); }
  await p.mouse.up(); await p.waitForTimeout(800);
  const post = (await selIds()).sort(), w = [...want].sort();
  const ok = post.length === w.length && post.every((v, i) => v === w[i]);
  console.log(`  框选 ${want.length} 个 → 选中 ${post.length} 个 ${ok ? '✅ 前置条件成立' : '❌ 不一致'}: ${post.join(',') || '(空)'}`);
  return ok;
};
// 在目标节点上点一下（可带 Shift）。
// 🔑 批次 56 实测的坑：**多选状态下不能用 elementFromPoint 定位节点** ——
//    react-flow 的 `react-flow__nodesselection-rect`（选区矩形）盖在节点之上，
//    实测 25 个采样点 100% 命中它，`closest('.react-flow__node')` 为 null。
//    所以这里改成「直接点在节点可见中心」—— 那也正是真人会做的动作，
//    命中选区矩形还是节点都如实反映产品行为。
const clickNode = async (id, mod) => {
  const info = await p.evaluate((v) => {
    const e = document.querySelector(`.react-flow__node[data-id="${v}"]`);
    if (!e) return null;
    const r = e.getBoundingClientRect();
    let x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
    // 落点夹到安全区，避免点到视口外或被顶栏/底栏/dock 吃掉
    const cx = Math.max(120, Math.min(1200, x)), cy = Math.max(140, Math.min(600, y));
    const el = document.elementFromPoint(cx, cy);
    const n = el && el.closest('.react-flow__node');
    return { x: cx, y: cy, clipped: [x, y] !== [cx, cy], hitId: n ? n.getAttribute('data-id') : null,
      hitTag: el ? `${el.tagName}.${String(el.className).slice(0, 40)}` : 'null' };
  }, id);
  if (!info) { console.log(`  ❌ 找不到节点 ${id}`); return false; }
  console.log(`    落点(${info.x},${info.y})${info.clipped ? ' [已夹到安全区]' : ''} 顶层元素: ${info.hitTag} → 归属 ${JSON.stringify(info.hitId)}`);
  if (mod) await p.keyboard.down(mod);
  await p.mouse.click(info.x, info.y);
  if (mod) await p.keyboard.up(mod);
  await p.waitForTimeout(900);
  return true;
};

// 把自建节点拖开 —— 三个节点默认**互相重叠**（级联 40/80 画布像素），
// 不分开就没法「只框选其中 2 个」，A1–A4 的前置条件永远不成立。
const separate = async (myIds) => {
  const others = await p.evaluate((I) => I.map((id) => { const e = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!e) return null; const r = e.getBoundingClientRect(); return { id, x: r.x, y: r.y, w: r.width, h: r.height }; }).filter(Boolean), OTHERS);
  const nw = await p.evaluate((v) => { const r = document.querySelector(`.react-flow__node[data-id="${v}"]`).getBoundingClientRect(); return [r.width, r.height]; }, myIds[0]);
  const targets = [[300, 300], [660, 300], [1000, 300]];
  for (let i = 0; i < myIds.length; i++) {
    const id = myIds[i], [tx, ty] = targets[i];
    const box = { x: tx - nw[0] / 2, y: ty - nw[1] / 2, w: nw[0], h: nw[1] };
    const hit = others.filter((o) => o.x < box.x + box.w && o.x + o.w > box.x && o.y < box.y + box.h && o.y + o.h > box.y);
    if (hit.length) { console.log(`  ❌ 落点(${tx},${ty})与他人节点相交 ${hit.map((o) => o.id).join(',')}`); return false; }
    if (!(await isEmpty(tx, ty))) { console.log(`  ❌ 落点(${tx},${ty})不空`); return false; }
    const from = await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = e.getBoundingClientRect();
      for (let fy = 0.12; fy <= 0.9; fy += 0.08) for (let fx = 0.12; fx <= 0.9; fx += 0.08) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        const el = document.elementFromPoint(x, y); const n = el && el.closest('.react-flow__node');
        if (n && n.getAttribute('data-id') === v) return { x, y }; }
      return null; }, id);
    if (!from) { console.log(`  ❌ 找不到 ${id} 的可拖起点`); return false; }
    const read = () => p.evaluate((v) => { const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(document.querySelector(`.react-flow__node[data-id="${v}"]`).style.transform); return m ? [+m[1], +m[2]] : null; }, id);
    const before = await read();
    await p.mouse.move(from.x, from.y);
    await p.mouse.down();
    await p.waitForTimeout(150);
    for (let k = 1; k <= 8; k++) { await p.mouse.move(from.x + ((tx - from.x) * k) / 8, from.y + ((ty - from.y) * k) / 8); await p.waitForTimeout(45); }
    await p.mouse.up();
    await p.waitForTimeout(800);
    const after = await read();
    const moved = before && after && (Math.abs(after[0] - before[0]) > 5 || Math.abs(after[1] - before[1]) > 5);
    console.log(`  拖 ${id} → 屏幕(${tx},${ty})：canvas ${JSON.stringify(before)} → ${JSON.stringify(after)} ${moved ? '✅' : '❌ 没动'}`);
    if (!moved) return false;
  }
  return true;
};

const CREATED = [];
try {
  await reset();
  const bad0 = await diffNodePositions(p, BASELINE.nodes, 1.5);
  if (bad0.length || (await ids()).length !== 6) throw new Error('起点与基线不一致');
  console.log('起点与基线一致 ✅');
  await restoreZoom();
  await setTool('抓手工具');
  if (!await panTo(1700, 400)) throw new Error('平移失败');
  await setTool('选择工具');
  for (let i = 0; i < 3; i++) {
    const before = await ids();
    await p.evaluate(() => { const t = Array.from(document.querySelectorAll('button,[role="button"]')).find((e) => e.getAttribute('aria-label') === '文本'); if (t) t.click(); });
    await p.waitForTimeout(1700);
    const f = (await ids()).filter((x) => !before.includes(x));
    if (f.length !== 1) throw new Error(`建文本节点异常 ${f.length}`);
    CREATED.push(f[0]);
  }
  console.log('自建 3 个文本节点:', JSON.stringify(CREATED));
  await restoreZoom();
  await setTool('抓手工具');
  if (!await centerMine(CREATED)) throw new Error('居中失败');
  await setTool('选择工具');
  console.log('\n########## 前置：把三个重叠的节点拖开 ##########');
  if (!await separate(CREATED)) throw new Error('节点拖开失败');
  const [n1, n2, n3] = CREATED;

  const recenter = async () => { await setTool('抓手工具'); const ok = await centerMine(CREATED); await setTool('选择工具'); return ok; };

  console.log('\n########## A1 框选 2 个 → 按 ⌘A ##########');
  if (!await recenter()) throw new Error('A1 前重新居中失败');
  if (await frameSelect([n1, n2])) {
    console.log('  按前焦点守卫:', (await keyGuard(p)).where);
    await p.keyboard.press('Meta+A');
    await p.waitForTimeout(900);
    const s = await selIds();
    console.log('  ⌘A 后选中数:', s.length, '→', JSON.stringify(s));
    console.log('  状态行:', await statusLine());
    console.log('  ⇒ 手册结论「⌘A 全选不存在」', s.length === 3 ? '🔴 **被推翻**（⌘A 真的全选了）' : (s.length === 2 ? '❌ 无变化' : `⚠️ 变成 ${s.length} 个`));
  }

  console.log('\n########## A2 框选 2 个 → Shift+点「未选中」的第 3 个 ##########');
  if (!await recenter()) throw new Error('A2 前重新居中失败');
  if (await frameSelect([n1, n2])) {
    const ok = await clickNode(n3, 'Shift');
    const s = await selIds();
    console.log('  Shift+点', n3, ok ? '已点' : '❌ 点不到', '→ 选中数', s.length, JSON.stringify(s));
    console.log('  ⇒ ', s.length === 3 ? '🔴 **Shift+点选是可用的加选**（手册说反了）' : (s.length === 2 ? '❌ 没加上，也没减' : `⚠️ 变成 ${s.length} 个`));
  }

  console.log('\n########## A3 框选 2 个 → Shift+点「已在选中」里的第 1 个 ##########');
  if (!await recenter()) throw new Error('A3 前重新居中失败');
  if (await frameSelect([n1, n2])) {
    const ok = await clickNode(n1, 'Shift');
    const s = await selIds();
    console.log('  Shift+点', n1, ok ? '已点' : '❌ 点不到', '→ 选中数', s.length, JSON.stringify(s));
    console.log('  ⇒ ', s.length === 1 ? '✅ **Shift+点已选中的项 = 取消选中它**（标准切换语义）' : `⚠️ 变成 ${s.length} 个`);
  }

  console.log('\n########## A4 框选 2 个 → 普通点击其中一个（不带 Shift） ##########');
  if (!await recenter()) throw new Error('A4 前重新居中失败');
  if (await frameSelect([n1, n2])) {
    const ok = await clickNode(n1, null);
    const s = await selIds();
    console.log('  普通点击', n1, ok ? '已点' : '❌ 点不到', '→ 选中数', s.length, JSON.stringify(s));
    console.log('  ⇒ ', s.length === 1 && s[0] === n1 ? '标准单选行为' : `⚠️ 变成 ${s.length} 个`);
  }

  console.log('\n########## A5 单击空白 → 是否清空选中 ##########');
  if (!await recenter()) throw new Error('A5 前重新居中失败');
  if (await frameSelect([n1, n2, n3])) {
    const pt = await findEmpty();
    if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(800); }
    const s = await selIds();
    console.log('  单击空白', JSON.stringify(pt), '→ 选中数', s.length, JSON.stringify(s));
    console.log('  ⇒ ', s.length === 0 ? '✅ 点空白清空选中' : `⚠️ 仍有 ${s.length} 个`);
  }
} catch (e) {
  console.error('ABORT:', e.message);
}

await reset();
// ⚠️ 顺序很重要：**先删自己的节点、再归位缩放**。
// 反过来的话「适配画布」会按「还没删干净」的更宽内容去算，
// 算出来的倍数删完就过时了（批次 56 踩过：归位后停在 49% 而非 60%）。
for (const id of CREATED) console.log('  删', id, '→', await deleteById(id));
await restoreZoom();
const fin = await canvasBaseline(p);
const bad = await diffNodePositions(p, BASELINE.nodes, 1.5);
const g = await keyGuard(p);
console.log('\n=== 收尾核对 ===');
console.log(' 焦点守卫:', g.safe ? '✅' : g.where, '| 节点数', fin.nodes.length, '| 真编组', (await p.evaluate(() => document.querySelectorAll('.react-flow__node-group').length)));
console.log(' 状态行:', fin.status, '| 积分', fin.credit, '| 缩放', fin.zoom);
console.log(' 位置偏离:', bad.length, bad.length ? bad.join(',') : '✅ 0', '| 剩余待删:', JSON.stringify(CREATED));
await b.close();
