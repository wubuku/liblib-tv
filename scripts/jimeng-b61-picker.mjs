// 批次 61 v2：「从画布选择」拾取边界
//
// 🔴 v1 踩的三个坑（都已修）：
//   ① **宿主必须是媒体节点**。v1 的 R2 把「文本」当宿主去建，
//      文本节点**没有生成面板**，自然找不到「添加参考」按钮 ——
//      那不是「不可选」的读数，是**宿主类型选错了**。
//      ⇒ 本版宿主恒为**左栏新建的空图片节点**（自动选中、面板自动开），
//        被测的**类型**放在**候选**位上。
//   ② **点击必须走应用自己的命中测试**。v1 用 `el.dispatchEvent(click)`，
//      结果 `elementFromPoint` 在遮罩区域返回的是
//      `canvas-source-picker-canvas-mask/frame`（1280×720，盖在节点上），
//      过滤条件「必须落在某个节点里」把**所有**点都否掉了 → `no-clickable-point-in-mask`。
//      这与批次 56 的 `react-flow__nodesselection-rect` 是**同一族陷阱**：
//      **覆盖层盖住节点时，`elementFromPoint` 不能用来定位节点。**
//      ⇒ 改为 `p.mouse.click(x, y)` 打在节点中心，**让应用自己判定**。
//   ③ **失败路径也必须清理**。v1 的 R2/R4 在报错前 return，把 6 个节点留在共享画布上。
//      ⇒ 本版每轮 `try/finally`，无论成败都按 id 删宿主与候选。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OUT = new URL('./_tmp-b61-picker5.json', import.meta.url);
const UPLOAD = '/tmp/b22-upload.png';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);
const MINE = [];
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
    const s = await selIds(); if (s.length === 1 && s[0] === id) return { ok: true, pt }; }
  return { ok: false, n: pts.length };
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
  if (made.length !== 1) return { err: `新建「${kind}」新增 ${made.length} 个` };
  MINE.push(made[0]); return { id: made[0] };
};
const makeImageWithUpload = async () => {
  await deselect();
  const pre = await nodeIds();
  try {
    const [ch] = await Promise.all([p.waitForEvent('filechooser', { timeout: 12000 }), p.click('button[aria-label="上传"]')]);
    await ch.setFiles(UPLOAD); await p.waitForTimeout(3800);
  } catch (e) { return { err: `上传失败：${e.message}` }; }
  const made = (await nodeIds()).filter((x) => !pre.includes(x));
  if (made.length !== 1) return { err: `上传后新增 ${made.length} 个节点` };
  MINE.push(made[0]);
  const imgs = await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); return e ? e.querySelectorAll('img').length : -1; }, made[0]);
  return { id: made[0], imgs };
};
const deleteById = async (id) => {
  if (!(await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"]`), id))) return 'absent';
  await reset();
  const s = await selectByScan(id);
  if (!s.ok) return 'notselected';
  await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return;
    const r = e.getBoundingClientRect();
    e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 14) })); }, id);
  await p.waitForTimeout(900);
  const ok = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop(); if (!m) return false;
    const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (!it) return false; it.click(); return true; });
  await p.waitForTimeout(1400); await reset(); return ok ? 'deleted' : 'noclick';
};
const pickerState = () => p.evaluate(() => {
  const vis = (s) => Array.from(document.querySelectorAll(s)).filter((e) => e.getBoundingClientRect().width > 1).length;
  const form = document.querySelector('[data-testid="generation-form"]');
  return { mask: vis('[data-testid="canvas-source-picker-canvas-mask"]'), frame: vis('[data-testid="canvas-source-picker-canvas-frame"]'),
    chip: vis('[data-testid="generation-source-picker-chip"]'), closeBtn: vis('[data-testid="generation-source-picker-close"]'),
    formAria: form ? form.getAttribute('aria-label') : null };
});
const promptState = () => p.evaluate(() => {
  const form = document.querySelector('[data-testid="generation-form"]');
  if (!form) return null;
  const chips = Array.from(form.querySelectorAll('*')).filter((e) => {
    const t = e.getAttribute('data-testid') || ''; const c = String(e.className || '');
    return /chip|reference|source|attach/i.test(t + ' ' + c);
  }).map((e) => { const r = e.getBoundingClientRect();
    return { tid: e.getAttribute('data-testid'), cls: String(e.className || '').slice(0, 40),
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
      box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, vis: r.width > 1 }; });
  return { formAria: form.getAttribute('aria-label'),
    innerText: (form.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 140), chips, childCount: form.querySelectorAll('*').length };
});
const nodeAria = (id) => p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`);
  return e ? { aria: e.getAttribute('aria-label'), text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 50) } : null; }, id);
const centerOf = (id) => p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return null;
  const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), w: Math.round(r.width), h: Math.round(r.height) }; }, id);

// 🔑 v3 的关键修正：**落点必须先经 elementFromPoint 确认「属于目标节点」再点**。
// v2 直接点节点矩形中心，但新建节点**全部级联落在视口中心、互相重叠** ——
//   点「候选的中心」实际落在**后建的宿主**上（宿主盖在上面）。
//   而宿主很可能**正是被排除的那个**，于是四轮全读成「未被接受」，
//   看起来像「所有节点都不可选」，其实**一次都没点到候选**。
// 侦察还确认了两件事：
//   · 节点在拾取模式下**仍在 DOM 里**（v2 打印的 undefined 是**我字段名打错了**，不是节点消失）；
//   · `canvas-source-picker-canvas-mask` 与 `-frame` 的 **`pointer-events` 都是 `none`**、
//     **各 0 个子元素** —— 它们是**纯装饰，不吃点击**，点击直接穿透到画布。
//     所以「点不中」不是被遮罩挡了，是**点错了节点**。
const pointOwnedBy = (id) => p.evaluate((vid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return null;
  const r = n.getBoundingClientRect();
  const cands = [];
  // 从左上角开始扫：新建节点级联时，越靠左上越不容易被后建节点盖住
  for (let fy = 0.12; fy <= 0.88; fy += 0.06) for (let fx = 0.12; fx <= 0.88; fx += 0.06) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
    const el = document.elementFromPoint(x, y);
    if (!el || !el.closest(`.react-flow__node[data-id="${vid}"]`)) continue;
    if (el.closest('button,a,[role="button"],input,textarea,select,[role="menu"],[contenteditable="true"]')) continue;
    cands.push({ x, y, fx: +fx.toFixed(2), fy: +fy.toFixed(2), d: Math.abs(fx - 0.12) + Math.abs(fy - 0.12) });
  }
  cands.sort((u, v) => u.d - v.d);
  return cands[0] || null;
}, id);

// 把候选与宿主在**屏幕上**拉开：平移视口。
// ⚠️ 平移只改 `.react-flow__viewport` 的 translate，**不改任何节点的 canvas 坐标**
//    —— 对共享画布安全，也不会触发批次 45 记录的「删除节点改缩放」那类副作用。
const separate = async (candId, hostId) => {
  for (let r = 0; r < 14; r++) {
    const g = await p.evaluate(([c, h]) => {
      const cr = document.querySelector(`.react-flow__node[data-id="${c}"]`);
      const hr = document.querySelector(`.react-flow__node[data-id="${h}"]`);
      if (!cr || !hr) return null;
      const a = cr.getBoundingClientRect(), b = hr.getBoundingClientRect();
      const overlapX = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      const overlapY = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      return { overlapX: Math.round(overlapX), overlapY: Math.round(overlapY) };
    }, [candId, hostId]);
    if (!g) return false;
    if (g.overlapX < 8 || g.overlapY < 8) return true;   // 错开了
    const s = await findEmpty();
    if (!s) return false;
    await p.mouse.move(s.x, s.y); await p.mouse.down(); await p.waitForTimeout(120);
    for (let i = 1; i <= 6; i++) { await p.mouse.move(s.x + (260 * i) / 6, s.y); await p.waitForTimeout(45); }
    await p.mouse.up(); await p.waitForTimeout(600);
  }
  return false;
};

const result = { startedAt: new Date().toISOString(), zoom: await zoomOf(), rounds: [] };
console.log('=== 批次 61 v5：「从画布选择」拾取边界 ===\n');
console.log('起点:', await statusLine(), '| 积分', await credit(), '\n');

// v4 的轮次：**先把混淆变量分开**。
//   已测（v3）：R1 空视频**候选**→不可选；R3 **宿主自己**（也是空图片）→不可选；
//                R2 空文本候选→可选；R4 带内容图片候选→可选。
//   ⚠️ R3 里「空」与「宿主自己」两个变量**叠在一起**了 ——
//      它不可选，可能是「空媒体被排除」，也可能是「自己被排除」。
//      R1 已经证明「空媒体（视频）」这一支不可选，但**图片**这一支还没分离。
//   ⇒ v4 补上「空图片**候选**」把 R3 的混淆拆开，再把剩余类型补齐覆盖。
//   ⚠️ v4 里 R6/R8 报「找不到属于目标节点的落点」—— 候选被后建的宿主**完全盖住**，
//      细网格一个可用点都没有。⇒ v5 加一步 `separate()`：**平移视口**把两者拉开。
//      平移只改视口 translate，**不改任何节点的 canvas 坐标**，对共享画布安全。
const ROUNDS = [
  { id: 'R5-空图片候选', q: '空图片节点（**不是**宿主）能不能被选中？', mkCand: () => makeNode('图片') },
  { id: 'R9-空音频候选', q: '空音频节点能不能被选中？', mkCand: () => makeNode('音频') },
  { id: 'R10-主体候选', q: '空主体节点能不能被选中？', mkCand: () => makeNode('主体') },
  { id: 'R11-导演台候选', q: '空导演台节点能不能被选中？', mkCand: () => makeNode('导演台') },
];

for (const R of ROUNDS) {
  console.log(`\n──────── ${R.id}：${R.q}`);
  let cand = null, host = null;
  const rec = { id: R.id, q: R.q };
  try {
    await deselect();
    if (R.mkCand) { cand = await R.mkCand(); if (cand.err) throw new Error(`候选：${cand.err}`);
      console.log('  候选', cand.id, cand.imgs !== undefined ? `| img ${cand.imgs} 个` : ''); }
    host = await makeNode('图片'); if (host.err) throw new Error(`宿主：${host.err}`);
    console.log('  宿主', host.id, '(空图片，恒为媒体节点)');
    rec.hostId = host.id; rec.candId = cand ? cand.id : null;

    const target = R.self ? host.id : cand.id;
    rec.targetId = target;
    // 候选与宿主级联重叠时，先在屏幕上把它们拉开（只平移视口，不动 canvas 坐标）
    if (cand) { const sep = await separate(cand.id, host.id); rec.separated = sep; console.log('  分离候选与宿主:', sep ? '✅ 已错开' : '⚠️ 未能完全错开'); }
    rec.targetAriaBefore = await nodeAria(target);
    rec.targetAriaAfter = null;   // 点击后回填（v2 打印的是 nodeAriaAfter，字段名不一致，导致读出 undefined）
    const c0 = await credit();
    const n0 = (await nodeIds()).length;

    const addRef = await p.$('button[aria-label="添加参考"]');
    if (!addRef) throw new Error('宿主上找不到「添加参考」按钮');
    await addRef.click(); await p.waitForTimeout(1100);
    const menu = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
      if (!m) return null; const r = m.getBoundingClientRect();
      return { aria: m.getAttribute('aria-label'), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
        items: Array.from(m.querySelectorAll('[role="menuitem"]')).map((e) => (e.innerText || '').split('\n')[0].trim()) }; });
    rec.menu = menu; console.log('  菜单', JSON.stringify(menu));
    const hit = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop(); if (!m) return false;
      const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /从画布选择/.test(x.innerText || '')); if (!it) return false; it.click(); return true; });
    if (!hit) throw new Error('菜单里没有「从画布选择」');
    await p.waitForTimeout(1400);
    const pk0 = await pickerState(); rec.pickerBefore = pk0; console.log('  拾取模式', JSON.stringify(pk0));
    const pr0 = await promptState(); rec.promptBefore = pr0;
    console.log('  拾取前提示词:', JSON.stringify(pr0 && pr0.innerText));

    const pt = await pointOwnedBy(target);
    rec.clickAt = pt;
    rec.targetBox = await centerOf(target);
    if (!pt) throw new Error('找不到属于目标节点的落点（可能被完全遮住）');
    console.log(`  落点 @(${pt.x},${pt.y}) 归一化(${pt.fx},${pt.fy}) 目标节点 ${rec.targetBox.w}×${rec.targetBox.h} @${rec.targetBox.x},${rec.targetBox.y}`);
    await p.mouse.click(pt.x, pt.y);      // ← 落点已确认属于目标
    await p.waitForTimeout(1800);
    console.log(`  已点 (${pt.x},${pt.y})`);

    const pk1 = await pickerState(); rec.pickerAfter = pk1;
    const pr1 = await promptState(); rec.promptAfter = pr1;
    const c1 = await credit(); rec.creditBefore = c0; rec.creditAfter = c1;
    const n1 = (await nodeIds()).length;
    rec.nodeAriaAfter = await nodeAria(target);
    // 🔑 v4 修正判据：**选中后拾取模式不会退出**，chip 是直接插进提示词的。
    //   v2/v3 用「mask 归零」当接受信号，四轮因此全读成「未被接受」——
    //   **判据错了，不是产品没反应**。真正的接受信号是**提示词 innerText 变化**。
    const promptChanged = !!(pr1 && pr0 && pr1.innerText !== pr0.innerText);
    rec.promptChanged = promptChanged;
    rec.accepted = promptChanged;
    rec.creditDelta = c0 === c1 ? 0 : 1;
    console.log('  点击后拾取模式', JSON.stringify(pk1));
    console.log('  点击后提示词:', JSON.stringify(pr1 && pr1.innerText));
    if (pr1 && pr1.chips && pr1.chips.length) console.log('  🔑 chip:', JSON.stringify(pr1.chips, null, 1));
    console.log(`  🔴 积分 ${c0} → ${c1} ${c0 === c1 ? '（未扣费 ✅）' : '（⚠️ 变了）'} | 节点数 ${n0} → ${n1}`);
    console.log(`  目标节点 aria: ${JSON.stringify(rec.targetAriaBefore)} → ${JSON.stringify(rec.nodeAriaAfter)}`);
    console.log(`  ⇒ ${promptChanged ? '✅ 被接受（提示词出现 chip）' : '⛔ 未被接受（提示词逐字未变）'}`);
    result.rounds.push(rec);
  } catch (e) {
    console.log('  ⛔ 本轮失败:', e.message);
    rec.err = e.message; result.rounds.push(rec);
  } finally {
    await reset();
    if (cand && cand.id) console.log('  删候选', cand.id, await deleteById(cand.id));
    if (host && host.id) console.log('  删宿主', host.id, await deleteById(host.id));
    await reset();
  }
}

await reset();
for (let t = 0; t < 3; t++) { const z = await zoomOf();
  if (z && z.includes('60%')) { console.log('\n缩放归位 ok:', z); break; }
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
  const s = 'input[data-testid="canvas-zoom-percent-input"]';
  if (await p.$(s)) { await p.fill(s, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); }
  else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  if (t === 2) console.log('\n缩放归位 FAILED:', await zoomOf()); }
await reset();
const fin = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
  const mm = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
  return [e.getAttribute('data-id'), mm ? [Math.round(parseFloat(mm[1]) * 100) / 100, Math.round(parseFloat(mm[2]) * 100) / 100] : null]; })));
console.log('\n终态:', await statusLine(), '| 缩放', await zoomOf(), '| 节点', Object.keys(fin).length, '| 积分', await credit());
for (const [id, c] of Object.entries(fin)) { const bs = BASELINE.nodes[id];
  console.log(`  ${id} Δ=${JSON.stringify(bs ? [+(c[0] - bs.canvas[0]).toFixed(2), +(c[1] - bs.canvas[1]).toFixed(2)] : '(非基线!)')}`); }
console.log('剩余待删（本批创建）:', JSON.stringify(MINE.filter((id) => fin[id])));
result.end = { status: await statusLine(), zoom: await zoomOf(), coords: fin, credit: await credit(), mineLeft: MINE.filter((id) => fin[id]) };
writeFileSync(OUT, JSON.stringify(result, null, 1));
console.log('写入', OUT.pathname);
await b.close();
