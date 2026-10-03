// 批次 122 · a 轮（只读）：钉死 `canvas-editor-menu` 到底是什么。
//
// 🔴 靶子是**手册内部的一处矛盾**：
//   · `canvas-context.md:49,53`：「更多」是**顶栏唯一没有 `data-testid` 的按钮**（`28×28@1065`）
//   · `use-node-toolbar.md:515` + `SOURCE_OBSERVATIONS.md:8451` + `PROGRESS.md:2312`：
//     「`canvas-editor-menu` **恒 1 个 `36×36@1061,12`**、在顶栏右侧 ⇒ **顶栏按钮**」
//   · 批次 120 的 testid 普查也读到 `canvas-editor-menu` `[1061,12,36,36]`
//   ⇒ 两条说法不可能同时对：**要么「更多」按钮其实有 testid，
//     要么 `canvas-editor-menu` 不是那个按钮**（是包裹它的壳？还是「更多」菜单的宿主？）。
//   而 `30-concepts.md:786-787` 恰好记着这个坑已经**现身三次**
//   （批次 105 / 107 / 又一次），并写明判据要加 **owner 归属**。
//
// 本轮只读：把「顶栏里每一个元素」的 testid 逐个列出，
// 并把 `canvas-editor-menu` 的**标签、class、aria、祖先、后代、中心点命中**一次读全。
// 不点任何按钮。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b122a.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);

out.start = { zoom: await zoom(), credits: await credits(), status: await status() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

// ============================================================
// ① 顶栏逐元素普查：标签 / testid / aria / 矩形 / 可见 / 命中
// ============================================================
out.topbar = await p.evaluate(() => {
  const bar = document.querySelector('[data-testid="canvas-top-bar"]');
  if (!bar) return { __err: 'no-topbar' };
  const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const list = [];
  for (const e of bar.querySelectorAll('*')) {
    const q = e.getBoundingClientRect();
    if (!q.width || !q.height) continue;
    // 只记「可交互或带身份」的那些，避免整条祖先链刷屏
    const tid = e.getAttribute('data-testid');
    const aria = e.getAttribute('aria-label');
    const isBtn = e.tagName === 'BUTTON' || e.getAttribute('role') === 'button' || e.tagName === 'A';
    if (!tid && !aria && !isBtn) continue;
    const cx = Math.round(q.x + q.width / 2), cy = Math.round(q.y + q.height / 2);
    const hit = document.elementFromPoint(cx, cy);
    list.push({ tag: e.tagName, tid, aria, 矩形: r(e),
      cls: (e.getAttribute('class') || '').toString().slice(0, 56),
      在顶栏内: bar.contains(e), 中心命中: hit ? (hit === e ? '自己' : hit.tagName + ' tid=' + hit.getAttribute('data-testid') + ' aria=' + hit.getAttribute('aria-label')) : null,
      中心命中是自己或含自己: hit ? (hit === e || e.contains(hit)) : false,
      子元素数: e.children.length, 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) });
  }
  return { 顶栏矩形: r(bar), 数量: list.length, 列表: list };
});
log('\n=== ① 顶栏可交互/带身份元素（' + out.topbar.数量 + ' 个）===');
out.topbar.列表.forEach((d) => log(`   <${d.tag}> ${JSON.stringify(d.rect || d.矩形)} tid=${JSON.stringify(d.tid)} aria=${JSON.stringify(d.aria)} 文字=${JSON.stringify(d.文字)}\n        中心命中=${d.中心命中}｜命中落回自己=${d.中心命中是自己或含自己}｜子=${d.子元素数}`));
save();

// ============================================================
// ② canvas-editor-menu 的身份 + 祖先链 + 后代
// ============================================================
out.editor = await p.evaluate(() => {
  const els = Array.from(document.querySelectorAll('[data-testid="canvas-editor-menu"]'));
  const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const desc = (e) => { const q = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return { tag: e.tagName, tid: e.getAttribute('data-testid'), id: e.id || null,
      cls: (e.getAttribute('class') || '').toString().slice(0, 80), aria: e.getAttribute('aria-label'), role: e.getAttribute('role'),
      矩形: r(e), z: cs.zIndex, pos: cs.position, pe: cs.pointerEvents, disp: cs.display, op: cs.opacity,
      文字: (e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40), 子元素数: e.children.length,
      后代testid: Array.from(e.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')),
      后代aria: Array.from(e.querySelectorAll('[aria-label]')).map((x) => x.getAttribute('aria-label')).filter(Boolean) }; };
  const chain = (e) => { const out2 = []; let cur = e; for (let k = 0; k < 6 && cur; k++) {
    out2.push({ tag: cur.tagName, tid: cur.getAttribute('data-testid'), id: cur.id || null, cls: (cur.getAttribute('class') || '').toString().slice(0, 60), 矩形: r(cur) }); cur = cur.parentElement; } return out2; };
  return { 命中数: els.length, 元素: els.map((e) => ({ 自身: desc(e), 祖先链: chain(e),
    中心命中: (() => { const q = e.getBoundingClientRect(); const h = document.elementFromPoint(Math.round(q.x + q.width / 2), Math.round(q.y + q.height / 2));
      return h ? (h === e ? '自己' : h.tagName + ' tid=' + h.getAttribute('data-testid') + ' aria=' + h.getAttribute('aria-label')) : null; })(),
    // 它内部有没有可点的角色
    内含menuitem: e.querySelectorAll('[role=menuitem]').length, 内含菜单: e.querySelectorAll('[role=menu]').length })) };
});
log('\n=== ② canvas-editor-menu ===');
log('  全文档命中数：', out.editor.命中数);
out.editor.元素.forEach((e, i) => { log(`  -- [${i}] 中心命中=${e.中心命中}｜内含 menuitem=${e.内含menuitem} / menu=${e.内含菜单}`); log('     自身：', JSON.stringify(e.自身, null, 1)); log('     祖先链：', JSON.stringify(e.祖先链)); });
save();

// ============================================================
// ③「更多」按钮本体：逐个候选找它，看它有没有 testid
// ============================================================
out.more = await p.evaluate(() => {
  const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const cands = [];
  for (const e of document.querySelectorAll('button,[role=button],a,[aria-label]')) {
    const a = (e.getAttribute('aria-label') || '').trim();
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!/^更多$/.test(a) && !/^更多$/.test(t) && !/^⋯$/.test(t)) continue;
    const q = e.getBoundingClientRect();
    if (!q.width || !q.height) continue;
    cands.push({ tag: e.tagName, tid: e.getAttribute('data-testid'), aria: a || null, 文字: t, 矩形: r(e),
      cls: (e.getAttribute('class') || '').toString().slice(0, 60),
      父: e.parentElement ? e.parentElement.tagName + ' tid=' + e.parentElement.getAttribute('data-testid') + ' cls=' + (e.parentElement.className || '').toString().slice(0, 44) : null,
      父矩形: e.parentElement ? r(e.parentElement) : null,
      内含testid: Array.from(e.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')),
      在editorMenu内: !!e.closest('[data-testid="canvas-editor-menu"]') });
  }
  return { 候选数: cands.length, 候选: cands };
});
log('\n=== ③「更多」按钮候选 ===');
log('  候选数：', out.more.候选数);
out.more.候选.forEach((d) => log(`   <${d.tag}> ${JSON.stringify(d.矩形)} tid=${JSON.stringify(d.tid)} aria=${JSON.stringify(d.aria)} 文字=${JSON.stringify(d.文字)}\n        父=${d.父} 父矩形=${JSON.stringify(d.父矩形)}\n        内含testid=${JSON.stringify(d.内含testid)}｜自身在 canvas-editor-menu 内=${d.在editorMenu内}`));
save();

out.end = { zoom: await zoom(), status: await status() };
save();
log('\n终点：', JSON.stringify(out.end));
log('\nDONE a');
process.exit(0);
