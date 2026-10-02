// 批次 115 · z 轮：**清理 + 归位**（结构沿用批次 113 的 z 轮，靶子换成三个自建节点）。
//
// 本批次自建了 **2 个**节点，全部由本批次脚本亲手造、亲手认领：
//   node_cp2dh7fn7d  ← a 轮「空白右键 → 新建节点 → 音频」造的空音频节点
//                       护栏②：差集恰好一个 + 同时 `.selected` ✅
//   node_zvmkems3fe  ← b 轮「左栏上传 /tmp/jimeng-b104-test.wav」造的媒体音频节点
//                       护栏②：差集恰好一个 + 同时 `.selected` ✅
//
// 🔴 护栏第三道：**删除前再确认目标仍 selected**，事后核对「本轮消失的 id」
//    **恰好只有 SELF**。若差集里有别人的 id ⇒ 说明点错了，立刻停。
// 🔴 收尾顺序（不可颠倒）：先删节点 → 再归位缩放（回读验证 + 连读两次相同）→
//    再归位工具态 → 确认 sel=0。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, canvasBaseline } from './jimeng-safe-keys.mjs';

const TARGETS = [
  { id: 'node_7xjntrj1s5', by: 'a 轮 · 空白右键 → 新建节点 → 主体' },
];

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'z', targets: TARGETS };
const save = () => writeFileSync(new URL('./_tmp-b115z.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
// 🔑 缩放只能读 aria（`Zoom options, 60%`），**禁止** innerText.match(/(\d+)%/)
const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return e ? { aria: e.getAttribute('aria-label'), rect: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() } : null; });
const toolState = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return e ? { aria: e.getAttribute('aria-label'), pressed: e.getAttribute('aria-pressed'), tid: e.getAttribute('data-testid') } : null; });

out.start = { nodes: await nodeN(), credits: await credits(), zoom: await zoom(), tool: await toolState() };
const ids0 = await allIds();
out.ids0 = ids0.length;
log('起点：', JSON.stringify(out.start), '｜id 数', ids0.length);
log('自建节点是否都在：', TARGETS.map((t) => `${t.id}=${ids0.includes(t.id)}`).join(' '));
save();

out.deletions = [];
for (const T of TARGETS) {
  log(`\n=== 删 ${T.id}（${T.by}） ===`);
  if (!ids0.includes(T.id)) { log('  节点已不在（可能上一轮已删）⇒ 跳过'); out.deletions.push({ id: T.id, skipped: true }); save(); continue; }
  // ⚠️ c 轮结束时焦点停在 `TEXTAREA aria="描述"` 里（没输入任何内容，值仍是原值）。
  //    先 Esc 退出编辑态再删，避免把「编辑中」的状态带进删除。
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  const stillEditing = await p.evaluate(() => { const a = document.activeElement; return a ? (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA' || a.isContentEditable === true) : false; });
  log('  Esc 后仍在编辑面？', stillEditing);
  const before = await allIds();
  // ---- 选中：现算落点，命中元素必须落在目标内部 ----
  const selPt = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
    if (n.classList.contains('selected')) return { already: true, rect: (() => { const r = n.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() };
    const r = n.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 6; y < r.y + r.height - 6; y += 5)
      for (let x = Math.ceil(r.x) + 6; x < r.x + r.width - 6; x += 5) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
        const el = document.elementFromPoint(x, y); if (el && (el === n || n.contains(el))) return { x, y }; }
    return { __err: 'unreachable', rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }, T.id);
  log('  选中落点：', JSON.stringify(selPt));
  if (selPt.__err === 'gone') { log('  🔴 节点已消失'); out.deletions.push({ id: T.id, err: 'gone' }); save(); continue; }
  if (selPt.x) { await p.mouse.click(selPt.x, selPt.y); await p.waitForTimeout(1500); }

  // ---- 护栏③前半：删除前确认目标仍 selected ----
  const selChk = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return { present: false }; return { present: true, selected: n.classList.contains('selected') }; }, T.id);
  log('  护栏③前半：', JSON.stringify(selChk));
  if (!selChk.present || !selChk.selected) { log('  ⛔ 目标没选中 ⇒ 中止（不硬删）'); out.deletions.push({ id: T.id, aborted: 'not-selected', selChk }); save(); continue; }

  // ---- 右键 → 找「删除」→ 落点现算 → 点 ----
  const rc = selPt.already ? selPt.rect : (selPt.rect || (await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const r = n.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; }, T.id)));
  const rx = Math.round(rc[0] + rc[2] / 2), ry = Math.round(rc[1] + rc[3] / 2);
  await p.mouse.move(rx, ry); await p.waitForTimeout(450);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(300); await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1300);
  const del = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]')) {
    const cs = getComputedStyle(m); if (cs.visibility === 'hidden') continue;
    for (const it of m.querySelectorAll('[role=menuitem]')) {
      const t = (it.innerText || '').replace(/\s+/g, ' ').trim();
      if (!/^删除/.test(t)) continue;
      if (it.getAttribute('aria-disabled') === 'true' || it.hasAttribute('disabled')) return { t, disabled: true };
      const r = it.getBoundingClientRect(); if (r.width < 1) continue;
      const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
      const h = document.elementFromPoint(cx, cy);
      if (!h || !(h === it || it.contains(h))) return { t, hitFail: { tag: h ? h.tagName : null, txt: h ? (h.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) : null } };
      return { t, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], disabled: false, menuW: Math.round(m.getBoundingClientRect().width) }; } }
    return null; });
  log('  「删除」项：', JSON.stringify(del));
  if (!del || del.disabled || del.hitFail) { log('  🔴 拿不到可点的「删除」⇒ 中止'); await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    out.deletions.push({ id: T.id, aborted: 'no-del-btn', del }); save(); continue; }
  await p.mouse.click(del.rect[0] + del.rect[2] / 2, del.rect[1] + del.rect[3] / 2);
  log('  已点删除，等重渲染…');
  await p.waitForTimeout(2200);

  // ---- 护栏③后半：核对「本轮消失的 id」恰好只有 SELF ----
  const after = await allIds();
  const vanished = before.filter((id) => !after.includes(id));
  const verdict = { vanished, exactlySelf: vanished.length === 1 && vanished[0] === T.id,
    stillThere: after.includes(T.id), nBefore: before.length, nAfter: after.length };
  log('  本轮消失的 id：', JSON.stringify(vanished), '⇒ 恰好只有 SELF =', verdict.exactlySelf);
  if (!verdict.exactlySelf) log('  ⛔⛔ 消失集合不等于 {SELF} —— 记为异常，停止后续动作');
  out.deletions.push({ id: T.id, ...verdict, del });
  save();
  if (!verdict.exactlySelf) { log('DONE z-abort'); await b.close(); process.exit(4); }
}

// ---- 归位缩放 ----
log('\n=== 归位缩放 ===');
out.zoom0 = await zoom();
log('当前：', JSON.stringify(out.zoom0));
const cur = out.zoom0 && (out.zoom0.aria || '').match(/(\d+)%/);
if (!cur || cur[1] !== '60') {
  const r = out.zoom0.rect;
  await p.mouse.click(r[0] + r[2] / 2, r[1] + r[3] / 2); await p.waitForTimeout(900);
  const inp = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent-input"]'); if (!e) return null;
    const b = e.getBoundingClientRect(); return { tag: e.tagName, type: e.type, value: e.value, rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] }; });
  log('缩放输入框：', JSON.stringify(inp));
  if (inp) {
    await p.mouse.click(inp.rect[0] + inp.rect[2] / 2, inp.rect[1] + inp.rect[3] / 2); await p.waitForTimeout(400);
    await p.keyboard.press('Meta+a'); await p.waitForTimeout(200);
    await p.keyboard.type('60', { delay: 120 }); await p.waitForTimeout(500);
    out.zoomTyped = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent-input"]'); return e ? e.value : null; });
    log('键入后输入框值 =', out.zoomTyped, '（键入不回车画面不动，这是已知行为）');
    await p.keyboard.press('Enter'); await p.waitForTimeout(2000);
  }
} else log('已是 60%，不动');
out.zoom1 = await zoom(); log('归位后第一次回读：', JSON.stringify(out.zoom1));
await p.waitForTimeout(1200);
out.zoom2 = await zoom(); log('归位后第二次回读：', JSON.stringify(out.zoom2));
out.zoomStable = JSON.stringify(out.zoom1) === JSON.stringify(out.zoom2);
log('  ⇒ 连读两次一致 =', out.zoomStable);
save();

// ---- 归位工具态 ----
log('\n=== 归位工具态 ===');
out.tool0 = await toolState();
log('当前：', JSON.stringify(out.tool0));
if (out.tool0 && /选择/.test(out.tool0.aria || '') === false) {
  const t = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]'); if (!e) return null;
    const b = e.getBoundingClientRect(); const cx = Math.round(b.x + b.width / 2), cy = Math.round(b.y + b.height / 2);
    const h = document.elementFromPoint(cx, cy); if (h && (h === e || e.contains(h))) return { x: cx, y: cy }; return null; });
  if (t) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1000); log('  已点工具切换'); }
  else log('  ⚠️ 点不到工具按钮');
} else log('  已是「选择工具」');
out.tool1 = await toolState();
log('归位后：', JSON.stringify(out.tool1));
save();

// ---- 终态 ----
out.end = { nodes: await nodeN(), credits: await credits(), zoom: await zoom(), tool: await toolState(),
  sel: await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length),
  edges: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length),
  leftovers: await p.evaluate((ids) => ids.filter((i) => document.querySelector(`.react-flow__node[data-id="${i}"]`)), TARGETS.map((t) => t.id)) };
log('\n终态：', JSON.stringify(out.end, null, 1));
log('遗留自建节点：', JSON.stringify(out.end.leftovers));
save();
log('\nDONE z');
process.exit(0);
