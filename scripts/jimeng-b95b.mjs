// 批次 95 · 收尾第 2 轮：只剩 `node_ce47a7tnzq`。
// 上一轮对它试了 3 次，**每次都「点得中但右键菜单弹不出来」** ⇒ 与编辑态无关（编辑态已确认清零）。
// 这一轮先**只诊断不删**，把原因查清楚再动手：它到底在不在 DOM、rect 在哪、被谁盖住、
// 点中之后选中的是谁、右键那一刻 `elementFromPoint` 是什么、有没有别的菜单容器。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const ID = 'node_ce47a7tnzq';
const out = { at: new Date().toISOString(), target: ID };

// 候选：菜单不一定挂在 `canvas-context-menu` 这个 testid 下（批次 91 就有 testid 陷阱）。
// 这里把**所有**可能的菜单容器一并登记，免得重蹈「找错 testid ⇒ 判 null ⇒ 收尾崩掉」。
const MENU_TIDS = ['canvas-context-menu', 'node-context-menu', 'context-menu', 'canvas-node-context-menu',
  'flow-node-context-menu', 'react-flow-context-menu', 'canvas-menu', 'contextmenu'];

out.probe0 = await p.evaluate(() => ({
  editable: document.querySelectorAll('[contenteditable="true"],.ProseMirror').length,
  allMenuTids: Array.from(document.querySelectorAll('[data-testid]'))
    .map((e) => e.getAttribute('data-testid')).filter((t) => /menu|context/i.test(t)),
  allRoleMenu: document.querySelectorAll('[role="menu"],[role="menuitem"]').length,
  nodes: document.querySelectorAll('.react-flow__node').length,
}));
log('P0 起点：', JSON.stringify(out.probe0));

out.rect = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  const m = /translate\(([^)]+)\)/.exec(n.style.transform || '');
  return {
    aria: n.getAttribute('aria-label'), text: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 60),
    screen: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
    inlineTransform: n.style.transform, parsed: m ? m[1] : null,
    classes: n.className,
  };
}, ID);
log('P1 节点本体：', JSON.stringify(out.rect));

if (!out.rect) { log('🔴 节点已不在 DOM 里'); }
else {
  // 落点扫描：和上一轮同一套（逐级 fx/fy 网格 + elementFromPoint 归属校验），
  // 但这次**同时记下每个档位是被谁盖住的**，好解释「点得中但菜单不弹」。
  out.scan = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const r = n.getBoundingClientRect();
    const rows = [];
    for (let fx = 0.05; fx <= 0.95; fx += 0.05) for (let fy = 0.05; fy <= 0.95; fy += 0.05) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      if (x < 0 || y < 0 || x > 1280 || y > 720) continue;
      const el = document.elementFromPoint(x, y);
      if (!el) { rows.push({ fx, fy, x, y, by: 'null' }); continue; }
      if (el.closest('.react-flow__node') === n) { rows.push({ fx, fy, x, y, by: 'SELF' }); continue; }
      const owner = el.closest('.react-flow__node');
      rows.push({ fx, fy, x, y, by: 'other', other: owner ? owner.getAttribute('data-id') : el.className || el.tagName });
    }
    const self = rows.filter((r) => r.by === 'SELF');
    return {
      inRect: { w: Math.round(r.width), h: Math.round(r.height) },
      sampled: rows.length, self: self.length, first: self[0] || null,
      blockers: Array.from(new Set(rows.filter((r) => r.by === 'other').map((r) => r.other))).slice(0, 8),
    };
  }, ID);
  log('P2 落点扫描：', JSON.stringify(out.scan));
}

log('browser=', JSON.stringify(out.probe0.allMenuTids));
writeFileSync(new URL('./_tmp-b95b.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
