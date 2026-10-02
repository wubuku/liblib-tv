// 批次 80 · C：定点排三件事。
// ① 点 `Rename <名>` 之后**到底出现了什么** —— b80b 实测点下去节点里没有 `<input>`，
//    页面第 103 行「点击后标题变为输入框」需要核实。
//    办法：**全文档**扫 input / textarea / contenteditable / 焦点元素，别只看节点内部。
// ② `[data-testid="node-toolbar"]` 量到 `0×0` —— 老坑重蹈（单数选择器撞 0×0 常驻占位）。
//    办法：把**所有**同名元素的尺寸都列出来，并按面积排序取最大的那个。
// ③ 编辑态那条 8 按钮工具条 —— 上版靠「position:absolute + 8 button + 200~500 宽」猜，没猜到。
//    办法：直接从按钮 aria 往上回溯共同祖先，别猜样式。
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
const out = { at: new Date().toISOString() };
let mine = null;
const isSel = (v) => p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  return n ? /(^|\s)selected(\s|$)/.test(n.className) : null; }, v);
try {
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3000);
  const made = (await ids()).filter((x) => !pre.includes(x));
  if (made.length !== 1) throw new Error('新建异常');
  mine = made[0]; log('新建', mine, '自动选中 =', await isSel(mine));

  // ———— ② node-toolbar 到底有几个、多大 ————
  out.toolbars = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).map((e) => {
    const b = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return { box: `${b.width.toFixed(1)}x${b.height.toFixed(1)}@${Math.round(b.x)},${Math.round(b.y)}`,
      display: cs.display, visibility: cs.visibility, opacity: cs.opacity,
      buttons: e.querySelectorAll('button,[role="button"]').length,
      inNode: e.closest('.react-flow__node') ? e.closest('.react-flow__node').getAttribute('data-id') : null,
      parentTestId: e.parentElement ? e.parentElement.getAttribute('data-testid') : null,
      parentCls: e.parentElement ? (e.parentElement.getAttribute('class') || '').slice(0, 50) : null };
  }));
  log('node-toolbar 全部：', JSON.stringify(out.toolbars, null, 1));
  // 全文档里所有「像工具条」的容器（按按钮数排）
  out.toolbarLike = await p.evaluate(() => {
    const seen = new Map();
    for (const btn of document.querySelectorAll('button[aria-label]')) {
      const a = btn.getAttribute('aria-label');
      if (!/背景色|全屏|下载|Text style|加粗|无序列表/.test(a)) continue;
      for (let e = btn; e && e !== document.body; e = e.parentElement) {
        const b = e.getBoundingClientRect();
        if (b.width < 100 || b.height < 20) continue;
        const key = `${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`;
        if (!seen.has(key)) seen.set(key, { box: key, tag: e.tagName, tid: e.getAttribute('data-testid') || '',
          cls: (e.getAttribute('class') || '').slice(0, 46), pos: getComputedStyle(e).position,
          buttons: e.querySelectorAll('button').length, inNode: !!e.closest('.react-flow__node') });
        break;
      }
    }
    return Array.from(seen.values());
  });
  log('像工具条的容器：', JSON.stringify(out.toolbarLike, null, 1));

  // ———— ① 点 Rename 之后全文档扫可编辑元素 ————
  const rb = await p.evaluate(() => { const el = document.querySelector('button[aria-label^="Rename"]'); if (!el) return null;
    const r = el.getBoundingClientRect(); return { aria: el.getAttribute('aria-label'), x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
      outer: el.outerHTML.slice(0, 200) }; });
  out.renameBtn = rb; log('Rename 钮', JSON.stringify(rb));
  if (!rb) throw new Error('Rename 钮不出现');
  out.before = await p.evaluate(() => ({ inputs: document.querySelectorAll('input').length,
    ce: document.querySelectorAll('[contenteditable="true"]').length,
    active: document.activeElement.tagName + '.' + (document.activeElement.className || '').slice(0, 24) }));
  await p.mouse.click(rb.x, rb.y); await p.waitForTimeout(1200);
  out.after = await p.evaluate((v) => {
    const desc = (e) => { const b = e.getBoundingClientRect();
      return { tag: e.tagName, type: e.getAttribute('type'), tid: e.getAttribute('data-testid') || '',
        cls: (e.getAttribute('class') || '').slice(0, 50), aria: e.getAttribute('aria-label') || '',
        value: 'value' in e ? String(e.value).slice(0, 40) : null,
        text: (e.innerText || '').trim().slice(0, 30),
        box: `${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`,
        inNode: e.closest('.react-flow__node') ? e.closest('.react-flow__node').getAttribute('data-id') : null,
        focused: document.activeElement === e }; };
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
    return { inputs: Array.from(document.querySelectorAll('input')).map(desc),
      textareas: Array.from(document.querySelectorAll('textarea')).map(desc),
      editables: Array.from(document.querySelectorAll('[contenteditable="true"]')).map(desc),
      active: { tag: document.activeElement.tagName, cls: (document.activeElement.className || '').slice(0, 40),
        aria: document.activeElement.getAttribute ? document.activeElement.getAttribute('aria-label') : null,
        value: 'value' in document.activeElement ? String(document.activeElement.value).slice(0, 40) : null },
      nodeTitleHTML: n ? (n.querySelector('[data-testid=flow-node-title]') || {}).outerHTML?.slice(0, 300) : null };
  }, mine);
  log('点 Rename 之后（全文档）：', JSON.stringify(out.after, null, 1));
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
  writeFileSync(new URL('./_tmp-b80c.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
