// 批次 139 c 轮探针：**先取证，后归位**。
//
// 🔴 a 轮点一次「编组」却出了 **2 个组**（状态行 `80 nodes`，DOM 81 个 `.react-flow__node`）。
//   在把共享画布清干净之前，先把这两个组的真身读出来 —— 归位之后就再也读不到了。
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import fs from 'node:fs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = {};
try {
  await keyGuard(p);
  await settle(p, R);
  rec.状态行 = await R.status();
  rec.选中 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
  rec.节点数 = await p.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  rec.组 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group')).map((g) => {
    const r = g.getBoundingClientRect();
    return {
      id: g.getAttribute('data-id'),
      aria: g.getAttribute('aria-label'),
      逐字: (g.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
      选中: g.classList.contains('selected'),
      屏上: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
      canvas: { w: g.offsetWidth, h: g.offsetHeight },
      style: { width: g.style.width, height: g.style.height, transform: g.style.transform },
      className: g.className,
      子节点: Array.from(g.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')),
      子节点数: g.querySelectorAll('.react-flow__node').length,
      resizeChrome: document.querySelectorAll('[class*="group-resize-chrome"]').length,
      匹配resizeChrome: g.getAttribute('data-id')
        ? document.querySelectorAll('.react-flow__node-group__group-resize-chrome__' + g.getAttribute('data-id')).length : -1,
      四角把手: Array.from(g.querySelectorAll('[aria-label^="Resize group from"]')).map((e) => e.getAttribute('aria-label')),
    };
  }));
  rec.工具条 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).map((e) => {
    const r = e.getBoundingClientRect();
    const inner = e.querySelector('[data-testid="selection-context-toolbar"]');
    return { 屏上: { w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10, x: Math.round(r.x), y: Math.round(r.y) },
      offsetWidth: e.offsetWidth, offsetHeight: e.offsetHeight,
      inner逐字: inner ? (inner.innerText || '').replace(/\s+/g, ' ').trim() : null,
      inner屏上: inner ? { w: Math.round(inner.getBoundingClientRect().width * 10) / 10, h: Math.round(inner.getBoundingClientRect().height * 10) / 10 } : null,
      按钮: Array.from(e.querySelectorAll('button,[role=button]')).map((b2) => {
        const rr = b2.getBoundingClientRect();
        return { 逐字: (b2.innerText || '').replace(/\s+/g, ' ').trim() || null, aria: b2.getAttribute('aria-label'),
          value: b2.getAttribute('data-toolbar-value'), 屏上: `${Math.round(rr.width * 10) / 10}×${Math.round(rr.height * 10) / 10}` };
      }) };
  }));
  rec.成员在不在顶层 = await p.evaluate(() => {
    const 顶层 = new Set(Array.from(document.querySelectorAll('.react-flow__node')).filter((n) => !n.closest('.react-flow__node')).map((n) => n.getAttribute('data-id')));
    return { 顶层节点数: 顶层.size, 顶层含组: Array.from(顶层).filter((x) => document.querySelector(`.react-flow__node-group[data-id="${x}"]`)) };
  });
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 500); }
fs.writeFileSync(new URL('./_tmp-b139c-probe.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify(rec, null, 1));
await b.close();
