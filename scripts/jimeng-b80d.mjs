// 批次 80 · D：把「行内重命名」的**完整交互序列**走一遍。
// 已知（b80c）：单击 `Rename <名>` 之后
//   - 全文档**没有**任何 input / textarea / contenteditable；
//   - 焦点仍在那个 BUTTON 上；
//   - 按钮上多了 `data-node-title-selected="true"`，标题进入「被选中」态。
// ⇒ 页面第 103 行「点击后标题变为输入框」**与实测不符**，需要查清真正的入口。
// 逐步记录：单击 → 再单击 → 双击标题 → （有条件才）直接打字。
// 🔒 打字前置条件：只有当文档里**真的出现了可编辑元素或焦点落在标题区内**才打，
//    否则记 VOID 绝不盲打（防误触画布快捷键）。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), steps: [] };
let mine = null;
const isSel = (v) => p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  return n ? /(^|\s)selected(\s|$)/.test(n.className) : null; }, v);
const snap = (label, v) => p.evaluate(([id, lb]) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  const t = n.querySelector('[data-testid=flow-node-title]');
  const btn = document.querySelector('button[aria-label^="Rename"]');
  const editables = Array.from(document.querySelectorAll('input:not([type="file"]),textarea,[contenteditable="true"]'));
  const a = document.activeElement;
  return { step: lb,
    titleText: t ? (t.innerText || '').trim() : null,
    titleAttrs: t ? Object.fromEntries(Array.from(t.attributes).map((x) => [x.name, x.value.slice(0, 60)])) : null,
    titleIsContentEditable: t ? t.getAttribute('contenteditable') : null,
    renameBtnAttrs: btn ? { sel: btn.getAttribute('data-node-title-selected'), dragging: btn.getAttribute('data-node-title-dragging'), aria: btn.getAttribute('aria-label') } : null,
    editableCount: editables.length,
    editables: editables.slice(0, 4).map((e) => { const b = e.getBoundingClientRect();
      return { tag: e.tagName, type: e.getAttribute('type'), value: 'value' in e ? String(e.value).slice(0, 30) : null,
        box: `${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`,
        inThisNode: !!e.closest('.react-flow__node') && e.closest('.react-flow__node').getAttribute('data-id') === id,
        focused: document.activeElement === e }; }),
    active: { tag: a.tagName, cls: (a.className || '').slice(0, 34), aria: a.getAttribute ? a.getAttribute('aria-label') : null,
      inTitleArea: !!(t && (a === t || t.contains(a))), isRenameBtn: a === btn },
    nodeAria: n.getAttribute('aria-label') };
}, [v, label]);
try {
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3000);
  const made = (await ids()).filter((x) => !pre.includes(x));
  if (made.length !== 1) throw new Error('新建异常');
  mine = made[0]; log('新建', mine, '自动选中 =', await isSel(mine));
  const rb = await p.evaluate(() => { const el = document.querySelector('button[aria-label^="Rename"]'); if (!el) return null;
    const r = el.getBoundingClientRect(); return { aria: el.getAttribute('aria-label'), x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (!rb) throw new Error('Rename 钮不出现');
  out.steps.push(await snap('0 起点', mine));
  await p.mouse.click(rb.x, rb.y); await p.waitForTimeout(1100);
  out.steps.push(await snap('1 单击 Rename', mine));
  await p.mouse.click(rb.x, rb.y); await p.waitForTimeout(1100);
  out.steps.push(await snap('2 再单击一次', mine));
  // 双击标题行
  const tr = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); const r = n.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y - 16) }; }, mine);
  await p.mouse.dblclick(tr.x, tr.y); await p.waitForTimeout(1200);
  out.steps.push(await snap('3 双击标题行', mine));
  // 只有真的出现可编辑元素才打字
  const last = out.steps[out.steps.length - 1];
  const canType = last.editableCount > 0 && last.editables.some((e) => e.focused);
  out.canType = canType;
  log('可以打字吗 =', canType, '| editables =', JSON.stringify(last.editables));
  if (canType) {
    await p.keyboard.press('Meta+A'); await p.waitForTimeout(200);
    await p.keyboard.type('改名测试80'); await p.waitForTimeout(500);
    out.steps.push(await snap('4 打字后', mine));
    await p.keyboard.press('Enter'); await p.waitForTimeout(1400);
    out.steps.push(await snap('5 Enter 后', mine));
  } else {
    out.typingSkipped = '没有出现聚焦的可编辑元素 ⇒ 不盲打（防误触画布快捷键），记 VOID';
    log('⚠️', out.typingSkipped);
  }
  for (const s of out.steps) log(s.step.padEnd(18), 'title=', JSON.stringify(s.titleText),
    '| btn.sel=', s.renameBtnAttrs && s.renameBtnAttrs.sel, '| editables=', s.editableCount,
    '| active=', s.active.tag, s.active.inTitleArea ? '(标题区内)' : '', s.active.isRenameBtn ? '(Rename 钮)' : '');
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  for (let i = 0; i < 2; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(450); }
  if (mine) {
    for (let a = 1; a <= 3 && (await ids()).includes(mine); a++) {
      const q = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
        const r = n.getBoundingClientRect();
        for (const f of [[0.5, 0.5], [0.5, 0.2], [0.25, 0.5], [0.75, 0.5], [0.5, 0.8]]) { const x = Math.round(r.x + r.width * f[0]), y = Math.round(r.y + r.height * f[1]);
          const h = document.elementFromPoint(x, y); if (h && n.contains(h) && !h.closest('[role="menu"]')) return { x, y }; } return null; }, mine);
      if (!q) break;
      await p.mouse.click(q.x, q.y, { button: 'right' }); await p.waitForTimeout(1000);
      await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
        const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
      await p.waitForTimeout(1500);
    }
    log('清理', mine, (await ids()).includes(mine) ? '🔴 仍在' : '✅');
  }
  writeFileSync(new URL('./_tmp-b80d.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
