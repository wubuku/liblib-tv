// 批次 62 第五轮：补两个浮层的几何读数，并关掉第四轮没收干净的抽屉。
//
// 第四轮最值钱的发现不是「`/` 和 `@` 能用」，而是：
//   **`/` 唤起的 `agent-skill-menu` 与「使用技能」按钮弹的 `canvas-agent-skill-picker` 是两个不同的东西。**
// 我前三轮一直拿 `skill-picker` 当判据 —— 如果没在第四轮顺手把 `pops()` 改成
// 「列出全部可见 dialog/listbox/menu」，这一批就会写成
// 「`/` 不唤起任何东西」的**假阴性**。
// 🔑 判据选错 ⇒ 结论反向，而且读数「干净」（no / no / no），看不出任何异常。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const OUT = new URL('./_tmp-b62-round5.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);
const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const statusLine = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const drawer = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-feature-sidecar"]');
  if (!e || e.getBoundingClientRect().width < 1) return null; const r = e.getBoundingClientRect();
  return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; });
const pops = () => p.evaluate(() => Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"],[data-testid="agent-skill-menu"]'))
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { tid: e.getAttribute('data-testid'), role: e.getAttribute('role'), cls: String(e.className || '').slice(0, 48),
      box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      inSidecar: !!e.closest('[data-testid="canvas-feature-sidecar"]'),
      kids: e.children.length, text: (e.innerText || '').replace(/\s+/g, ' ').trim() }; }));
const clearComposer = async () => { await p.evaluate(() => { const c = document.querySelector('.tiptap.ProseMirror[contenteditable="true"]');
  if (!c) return; c.focus(); document.execCommand('selectAll', false, null); document.execCommand('delete', false, null);
  if ((c.innerText || '').trim()) { c.innerHTML = ''; c.dispatchEvent(new InputEvent('input', { bubbles: true, data: '', inputType: 'deleteContentBackward' })); } });
  await p.waitForTimeout(400); return p.evaluate(() => (document.querySelector('.tiptap.ProseMirror[contenteditable="true"]') || {}).innerText); };
const focusEditor = async () => { const c = await p.evaluate(() => { const e = document.querySelector('.tiptap.ProseMirror[contenteditable="true"]'); if (!e) return null;
  const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + 24), cy: Math.round(r.y + 24) }; });
  if (!c) return false; await p.mouse.click(c.cx, c.cy); await p.waitForTimeout(450);
  return p.evaluate(() => !!(document.activeElement && document.activeElement.closest('.tiptap.ProseMirror'))); };
const closePops = async (max = 5) => { for (let i = 0; i < max; i++) { if (!(await pops()).length) return i; await p.keyboard.press('Escape'); await p.waitForTimeout(800); } return -1; };
const clickRe = async (re) => { const h = await p.evaluate((src) => { const rx = new RegExp(src);
    const e = Array.from(document.querySelectorAll('button,[role="button"]')).filter((x) => { const r = x.getBoundingClientRect(); return r.width > 1 && r.height > 1; })
      .find((x) => rx.test(x.getAttribute('aria-label') || '') || rx.test((x.innerText || '').trim()));
    if (!e) return null; const r = e.getBoundingClientRect();
    const o = (document.elementFromPoint(Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)) || {}).closest?.('button,[role="button"]');
    return { ok: !!o && (o === e || e.contains(o)) }; }, re.source);
  if (!h || !h.ok) return h; await p.mouse.click(h.cx || 0, h.cy || 0); return h; };

const out = { startedAt: new Date().toISOString() };
const c0 = await credit();
console.log('=== 批次 62 第五轮：两个浮层的几何 ===\n起点:', await statusLine(), '| 积分', c0, '| 抽屉 =', JSON.stringify(await drawer()));
out.creditStart = c0;

// 先处理第四轮的遗留：抽屉还开着
if (await drawer()) { const h = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button'))
    .find((x) => (x.getAttribute('aria-label') || '') === '收起'); if (!e) return null; const r = e.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
  console.log('抽屉还开着，定位「收起」=', JSON.stringify(h));
  if (h) { await p.mouse.click(h.cx, h.cy); await p.waitForTimeout(1400); }
  console.log('  点后抽屉 =', JSON.stringify(await drawer())); }
out.drawerClosed = (await drawer()) === null;
if (await drawer()) { await p.keyboard.press('Escape'); await p.waitForTimeout(1200); console.log('  Esc 后抽屉 =', JSON.stringify(await drawer())); }

// 重新打开抽屉，测 `/` 浮层
if (!(await drawer())) { const rb = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button'))
    .find((x) => /与\s*AI\s*对话/.test(x.getAttribute('aria-label') || '')); if (!e) return null;
    const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
  if (!rb) { console.error('ABORT: 找不到「与 AI 对话」'); await b.close(); process.exit(1); }
  await p.mouse.click(rb.cx, rb.cy); await p.waitForTimeout(1600); }
console.log('抽屉 =', JSON.stringify(await drawer()));

console.log('\n【`/` 浮层 · agent-skill-menu 完整读数】');
console.log('  清空 =', JSON.stringify(await clearComposer()), '| 关浮层轮数 =', await closePops());
console.log('  聚焦 =', await focusEditor());
await p.keyboard.press('/');
await p.waitForTimeout(1500);
let ps = await pops();
console.log('  浮层:');
for (const x of ps) { console.log(`    tid=${x.tid} role=${x.role} box=${x.box} 在侧栏内=${x.inSidecar} 子元素=${x.kids}`); console.log(`      cls=${x.cls}`); console.log(`      text=${x.text}`); }
out.slashPop = ps;
if (ps.length) {
  const detail = await p.evaluate((tid) => { const e = tid ? document.querySelector(`[data-testid="${tid}"]`) : document.querySelector('[data-testid="agent-skill-menu"]');
    if (!e) return null; const r = e.getBoundingClientRect();
    const rows = Array.from(e.querySelectorAll('*')).filter((x) => x.getBoundingClientRect().width > 1 && x.children.length === 0)
      .map((x) => { const b = x.getBoundingClientRect(); return { tag: x.tagName, tid: x.getAttribute('data-testid'), cls: String(x.className || '').slice(0, 40), box: `${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`, text: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) }; });
    return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, role: e.getAttribute('role'),
      overflowY: getComputedStyle(e).overflowY, scrollH: e.scrollHeight, clientH: e.clientHeight, leaves: rows }; }, ps[0].tid);
  console.log('  详情:', JSON.stringify(detail, null, 1).slice(0, 3000));
  out.slashDetail = detail;
}
await p.screenshot({ path: new URL('62-agent-slash-menu.png', new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url)).pathname, clip: { x: 860, y: 8, width: 412, height: 700 } });
console.log('  📷 62-agent-slash-menu.png');

console.log('\n【`@` 浮层 · listbox 完整读数】');
console.log('  关浮层轮数 =', await closePops(), '| 清空 =', JSON.stringify(await clearComposer()));
console.log('  聚焦 =', await focusEditor());
await p.keyboard.press('@');
await p.waitForTimeout(1400);
ps = await pops();
for (const x of ps) { console.log(`    tid=${x.tid} role=${x.role} box=${x.box} 在侧栏内=${x.inSidecar} 子元素=${x.kids}`); console.log(`      text=${x.text}`); }
out.atPop = ps;
if (ps.length) {
  const det = await p.evaluate(() => { const e = document.querySelector('[role="listbox"]'); if (!e) return null; const r = e.getBoundingClientRect();
    const items = Array.from(e.querySelectorAll('[role="option"],[role="menuitem"]')).map((x) => { const b = x.getBoundingClientRect();
      return { role: x.getAttribute('role'), aria: x.getAttribute('aria-label'), text: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30), box: `${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}` }; });
    return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, items }; });
  console.log('  选项明细:', JSON.stringify(det, null, 1));
  out.atDetail = det;
}
await p.screenshot({ path: new URL('62-agent-at-menu.png', new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url)).pathname, clip: { x: 860, y: 8, width: 412, height: 700 } });
console.log('  📷 62-agent-at-menu.png');

const c1 = await credit();
console.log('\n=== 积分全程 ===', c0, '->', c1, 'Δ=', c1 - c0);
out.creditEnd = c1;

// 收尾
console.log('关浮层轮数 =', await closePops());
const fin = await clearComposer();
console.log('收尾 editor 文本 =', JSON.stringify(fin), fin && fin.trim() ? '<< 残留 ✗' : '<< 已清空 ✓');
await p.evaluate(() => { const c = document.querySelector('.tiptap.ProseMirror[contenteditable="true"]'); if (c) c.blur(); });
await p.waitForTimeout(400);
const hz = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '收起');
  if (!e) return null; const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
if (hz) { await p.mouse.click(hz.cx, hz.cy); await p.waitForTimeout(1500); }
console.log('点「收起」后抽屉 =', JSON.stringify(await drawer()));
if (await drawer()) { await p.keyboard.press('Escape'); await p.waitForTimeout(1300); console.log('  Esc 后抽屉 =', JSON.stringify(await drawer())); }
for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(280); }
console.log('终态:', await statusLine(), '| 积分', await credit(), '| 抽屉 =', JSON.stringify(await drawer()), '| 浮层 =', JSON.stringify(await pops()));
out.end = { status: await statusLine(), credit: await credit(), drawer: await drawer(), pops: await pops(), residue: fin };
writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log('写入', OUT.pathname);
await b.close();
