// 批次 193 a 轮：先探「导演台」节点的 DOM，拿到**真实的选择器与几何**，再写截图脚本。
// （立规 67：写选择器之前先把真实属性值打出来。）
import fs from 'node:fs';
import { openCanvas, readers, setZoom, settle } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);
const NID = 'node_pxvkay973v';
const out = {};

// 静息态
out.静息前 = { 选中: await R.selCount(), zoom: await R.zoom() };
out.静息 = await p.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { 有: false };
  const r = n.getBoundingClientRect();
  const 盒 = (e) => { if (!e) return null; const q = e.getBoundingClientRect();
    return { tag: e.tagName, testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
      屏上: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)], cursor: getComputedStyle(e).cursor }; };
  return { 有: true, class: String(n.className), 屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    在视口内: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight,
    全部testid: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    全部aria: Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')),
    标题: 盒(n.querySelector('[data-testid="flow-node-title"]')),
    进入导演台_SPAN: 盒(n.querySelector('span[aria-label="进入导演台"]')),
    进入导演台_ANY: 盒(Array.from(n.querySelectorAll('*')).find((e) => (e.getAttribute('aria-label') || '') === '进入导演台') || null),
    手柄: Array.from(n.querySelectorAll('[data-testid$="handle"]')).map(盒),
    节点文字: (n.innerText || '').replace(/\s+/g, ' ').trim() };
}, NID);

// 选中它
const 落点 = await p.evaluate((nid) => { const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return null;
  const t = n.querySelector('[data-testid="flow-node-title"]') || n; const r = t.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }, NID);
if (落点) { await p.mouse.click(落点[0], 落点[1]); await p.waitForTimeout(1200); }
out.选中后 = { 选中: await R.selCount(), zoom: await R.zoom() };
out.选中 = await p.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`); if (!n) return { 有: false };
  const r = n.getBoundingClientRect();
  const 盒 = (e) => { if (!e) return null; const q = e.getBoundingClientRect();
    return { tag: e.tagName, testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
      屏上: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)], cursor: getComputedStyle(e).cursor,
      背景: getComputedStyle(e).backgroundColor, 边框: getComputedStyle(e).border }; };
  const rename = n.querySelector('[aria-label="Rename 导演台"]');
  const title = n.querySelector('[data-testid="flow-node-title"]');
  return { 有: true, 屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    全部testid: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    全部aria: Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')),
    Rename按钮: 盒(rename), 标题: 盒(title),
    Rename与标题同y: rename && title ? Math.round(rename.getBoundingClientRect().y) === Math.round(title.getBoundingClientRect().y) : null,
    进入导演台_ANY: 盒(Array.from(n.querySelectorAll('*')).find((e) => (e.getAttribute('aria-label') || '') === '进入导演台') || null),
    进入导演台_button: 盒(Array.from(n.querySelectorAll('button')).find((e) => (e.innerText || '').trim() === '进入导演台') || null),
    手柄: Array.from(n.querySelectorAll('[data-testid$="handle"]')).map(盒),
    nodeToolbar数: n.querySelectorAll('[data-testid="node-toolbar"]').length };
}, NID);
console.log(JSON.stringify(out, null, 1));
fs.writeFileSync('/tmp/b193a.json', JSON.stringify(out, null, 1));
// 收尾：取消选中
if (out.选中后.选中) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
const 空 = await p.evaluate(() => { const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
  for (let y = 120; y < innerHeight - 120; y += 20) for (let x = 340; x < innerWidth - 360; x += 20) {
    const h = document.elementFromPoint(x, y);
    if (h && h.classList && h.classList.contains('react-flow__pane') && !nodes.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return [x, y]; }
  return null; });
if (空) { await p.mouse.click(空[0], 空[1]); await p.waitForTimeout(900); }
console.log('收尾 =', JSON.stringify({ 状态行: await R.status(), 选中: await R.selCount(), zoom: await R.zoom(), credits: await R.credits() }));
await b.close();
