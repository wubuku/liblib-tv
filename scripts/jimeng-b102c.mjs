// 批次 102 · c 轮：把 b 轮的两处判据错误查清，并补一条手册从没写过的能力。
//
// 🔴 **b 轮的判据取错了对象**：
//   b 轮用 `document.querySelector('input[type=file]')` —— 拿的是**文档里的第一个**，
//   读到 **23 条 / 10 个扩展名**（只有 image）；
//   a 轮用 `filechooser.element()` —— 拿的是**触发这次选择的那个**，
//   读到 **~90 条**（image + video + audio + text 四类）。
//   ⇒ 这块画布上有**多个 `input[type=file]`，`accept` 各不相同**。
//   📌 与批次 99「判断某面板有几个控件要查容器后代」同族：
//      **「取第一个 X」和「取触发这次动作的那个 X」是两回事。**
//      正确写法只有一个：`p.on('filechooser', fc => fc.element())`。
//
// 🔴 **第二条判据陷阱：子菜单「在 DOM 里」≠「打开着」**。
//   a 轮在**还没悬停**时就读到子菜单 `200×404`、9 项、几何非零；
//   而触发项的 `aria-expanded` 当时是 **`false`**。
//   ⇒ **`getBoundingClientRect()` 非零不能证明可见** —— 得看 `visibility/opacity/display`
//      或 `aria-expanded`。这与批次 98「必须判非零高度的真身」是同一个陷阱的镜像。
//
// 本轮三问：
//   A 全文档有几个 `input[type=file]`？各自的 `accept` 与**归属哪个入口**？
//   B 子菜单在悬停前后的**计算样式**逐项对比（把上面那条陷阱钉死）
//   C 手册从没写过：**`.txt` 在 `accept` 白名单里**（`text/plain,.txt`）⇒ 能不能上传成节点？
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);

// ================= A 全文档的 file input =================
log('=== A 全文档 input[type=file] ===');
out.inputs = await p.evaluate(() => Array.from(document.querySelectorAll('input[type=file]')).map((e, i) => {
  const toks = (e.getAttribute('accept') || '').split(',').map((s) => s.trim()).filter(Boolean);
  const pre = {};
  for (const t of toks) { const k = t.startsWith('.') ? '(ext)' : t.split('/')[0]; pre[k] = (pre[k] || 0) + 1; }
  // 往上找带 aria-label / data-testid 的祖先，判归属
  const chain = [];
  for (let a = e.parentElement; a && chain.length < 6; a = a.parentElement) {
    chain.push(`${a.tagName}${a.getAttribute('aria-label') ? `[${a.getAttribute('aria-label')}]` : ''}${a.getAttribute('data-testid') ? '#' + a.getAttribute('data-testid') : ''}${a.id ? '#' + a.id : ''}`);
  }
  const r = e.getBoundingClientRect();
  return { i, tokens: toks.length, byPrefix: pre, multiple: e.hasAttribute('multiple'),
    display: getComputedStyle(e).display, rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    acceptHead: (e.getAttribute('accept') || '').slice(0, 110), chain };
}));
for (const i of out.inputs) log(`  #${i.i} ${i.tokens} 条 ${JSON.stringify(i.byPrefix)} multiple=${i.multiple} display=${i.display} ${i.rect}\n      祖先链: ${i.chain.join(' ← ')}\n      accept 开头: ${i.acceptHead}`);

// ================= B 子菜单的可见性陷阱 =================
log('\n=== B 子菜单：悬停前 / 后 ===');
const readSubs = () => p.evaluate(() => {
  const trig = document.getElementById('context-menu-submenu-trigger-add-node');
  const sub = document.getElementById('context-menu-submenu-add-node');
  const d = (e) => { if (!e) return null; const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return { rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      display: cs.display, visibility: cs.visibility, opacity: cs.opacity,
      pointerEvents: cs.pointerEvents, ariaHidden: e.getAttribute('aria-hidden'),
      expanded: trig ? trig.getAttribute('aria-expanded') : null,
      n: e.querySelectorAll('[role=menuitem]').length }; };
  // 再看子菜单第一项
  const first = sub ? sub.querySelector('[role=menuitem]') : null;
  const df = first ? (() => { const r = first.getBoundingClientRect(); const cs = getComputedStyle(first);
    return { rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      visibility: cs.visibility, opacity: cs.opacity, pointerEvents: cs.pointerEvents }; })() : null;
  // 命中测试：子菜单中心那个点，实际拿到谁
  let hit = null;
  if (sub) { const r = sub.getBoundingClientRect();
    if (r.width > 0 && r.height > 0) { const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + 40);
      const el = document.elementFromPoint(x, y);
      hit = { at: [x, y], tag: el ? el.tagName : null, text: el ? (el.textContent || '').trim().slice(0, 20) : null,
        role: el ? el.getAttribute('role') : null, inSub: !!(el && sub.contains(el)) }; } }
  return { trigger: d(trig), submenu: d(sub), firstItem: df, hit };
});
{
  const blank = await p.evaluate(() => {
    const bad = (x, y) => { const el = document.elementFromPoint(x, y);
      if (!el || el.closest('.react-flow__node')) return true;
      if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
      if (el.closest('button,[role=button],input,a')) return true; return false; };
    for (let y = 280; y < 620; y += 16) for (let x = 260; x < 1100; x += 16) if (!bad(x, y)) return [x, y];
    return null; });
  await p.mouse.move(blank[0], blank[1]); await p.waitForTimeout(400);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1000);
  out.subBefore = await readSubs();
  log('悬停前：', JSON.stringify(out.subBefore, null, 1));

  const nj = await p.evaluate(() => { const it = document.getElementById('context-menu-submenu-trigger-add-node');
    if (!it) return null; const r = it.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (nj) { await p.mouse.move(nj[0], nj[1]); await p.waitForTimeout(400); await p.mouse.move(nj[0] + 4, nj[1]); await p.waitForTimeout(1200); }
  out.subAfter = await readSubs();
  log('悬停后：', JSON.stringify(out.subAfter, null, 1));
  out.trapConfirmed = out.subBefore && out.subAfter &&
    out.subBefore.submenu && out.subAfter.submenu &&
    out.subBefore.submenu.rect === out.subAfter.submenu.rect &&
    out.subBefore.submenu.expanded === 'false' && out.subAfter.submenu.expanded === 'true';
  log('⇒ 「几何不变 + aria-expanded 翻转」这条陷阱成立？', out.trapConfirmed ? '✅' : '否');
}

out.end = { nodes: await nodeN() };
log('\n终态 nodes：', out.end.nodes);
writeFileSync(new URL('./_tmp-b102c.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
