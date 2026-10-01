// 批次 57 配图：两条配图把「标题行几何在类型间不统一」拍成可见的对照
//
// 读数结论（60% 缩放，scale 0.6，屏幕 px）：
//   文本节点  `Rename 文本 N`  35.5~38.1 × **24**  底-卡片顶 = **-8**（悬在上方，有空隙）
//   视频节点  `Rename 视频 1`  35.5 × 32           底-卡片顶 = **+0.6**（压在卡片顶边上）
// 两张图都把 `Rename` 按钮和**卡片上沿**各画一个橙色高亮框，
// 空隙在图上就是「两个橙框之间那一条黑缝」。
import { chromium } from 'playwright';
import { createHash } from 'node:crypto';
import { writeFileSync } from 'node:fs';
import { readFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const DIR = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);
const reset = async () => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); } };
const selIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
const isEmpty = (x, y) => p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); if (!el) return true;
  if (el.closest('.react-flow__node')) return false;
  if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"]')) return false;
  return true; }, [x, y]);
const findEmpty = async () => { for (let y = 110; y <= 630; y += 20) for (let x = 80; x <= 1250; x += 20) { if (x > 1150 && y > 600) continue; if (await isEmpty(x, y)) return { x, y }; } return null; };
const deselect = async () => { await reset(); const e = await findEmpty();
  if (e) { await p.mouse.click(e.x, e.y); await p.waitForTimeout(600); }
  for (let i = 0; i < 3 && (await selIds()).length; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  return (await selIds()).length === 0; };
const coords = () => p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
  return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null];
})));

// 细网格试点选节点（三个文本节点互相重叠，矩形中心会选错 —— 批次 56 已记）
const selectByScan = async (id) => {
  const pts = await p.evaluate((vid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return [];
    const r = n.getBoundingClientRect(); const out = [];
    for (let fy = 0.10; fy <= 0.92; fy += 0.06) for (let fx = 0.10; fx <= 0.92; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y);
      if (!el || !el.closest(`.react-flow__node[data-id="${vid}"]`)) continue;
      if (el.closest('button,a,[role="button"],input,textarea,select,[role="menu"],[contenteditable="true"]')) continue;
      out.push({ x, y, fx: +fx.toFixed(2), fy: +fy.toFixed(2) });
    } return out;
  }, id);
  for (const pt of pts) {
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(550);
    const s = await selIds();
    if (s.length === 1 && s[0] === id) return { ok: true, pt, n: pts.length };
  }
  return { ok: false, n: pts.length };
};

// 注入橙色高亮框：Rename 按钮一个框、卡片上沿一条 2px 横线
const markUp = (id) => p.evaluate((vid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`);
  const ren = Array.from(n.querySelectorAll('[aria-label]')).find((e) => /^(Rename|Edit)\s/.test(e.getAttribute('aria-label') || '') && e.getBoundingClientRect().width > 1);
  const nr = n.getBoundingClientRect();
  if (!ren) return null;
  const rr = ren.getBoundingClientRect();
  const host = document.createElement('div');
  host.id = '__b57_markup__';
  host.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:2147483647';
  const box = document.createElement('div');
  box.style.cssText = `position:absolute;left:${rr.x - 3}px;top:${rr.y - 3}px;width:${rr.width + 6}px;height:${rr.height + 6}px;border:2px solid rgb(255,162,30);border-radius:3px`;
  const line = document.createElement('div');
  line.style.cssText = `position:absolute;left:${nr.x - 8}px;top:${nr.y - 1}px;width:${nr.width + 16}px;height:2px;background:rgb(255,162,30)`;
  const card = document.createElement('div');
  card.style.cssText = `position:absolute;left:${nr.x - 3}px;top:${nr.y - 3}px;width:${nr.width + 6}px;height:${nr.height + 6}px;border:2px solid rgba(255,162,30,0.55);border-radius:4px`;
  host.append(box, line, card); document.body.appendChild(host);
  return { renameAria: ren.getAttribute('aria-label'),
    rename: { w: +rr.width.toFixed(1), h: +rr.height.toFixed(1), y: +rr.y.toFixed(1), bottom: +rr.bottom.toFixed(1) },
    card: { w: +nr.width.toFixed(1), h: +nr.height.toFixed(1), y: +nr.y.toFixed(1) },
    dBottom: +(rr.bottom - nr.y).toFixed(1), dTop: +(rr.top - nr.y).toFixed(1),
    clip: { x: Math.max(0, Math.round(nr.x - 24)), y: Math.max(0, Math.round(nr.y - 58)),
            width: Math.round(nr.width + 48), height: Math.round(nr.height + 84) } };
}, id);
const markDown = () => p.evaluate(() => { const e = document.getElementById('__b57_markup__'); if (e) e.remove(); return true; });

const out = [];
for (const [id, name, expect] of [
  ['node_3bfb9r79qe', '99-node-title-text-gap.png', '文本'],
  ['node_236ctpehgg', '100-node-title-video-flush.png', '视频'],
]) {
  await deselect();
  const sel = await selectByScan(id);
  if (!sel.ok) { console.error(`ABORT: ${id} 选不中（试了 ${sel.n} 个落点）`); markDown(); await b.close(); process.exit(3); }
  const m = await markUp(id);
  if (!m) { console.error(`ABORT: ${id} 选中后仍找不到 Rename 元素`); markDown(); await b.close(); process.exit(4); }
  console.log(`\n${expect}节点 ${id} 选中落点 ${JSON.stringify(sel.pt)}（候选 ${sel.n}）`);
  console.log(`   ${JSON.stringify(m.renameAria)}  ${m.rename.w}×${m.rename.h}  顶-卡片顶=${m.dTop}  底-卡片顶=${m.dBottom}`);
  const buf = await p.screenshot({ type: 'png', clip: m.clip });
  const file = new URL(name, DIR);
  writeFileSync(file, buf);
  const sha = createHash('sha256').update(buf).digest('hex');
  console.log(`   截图 ${name}  ${buf.length} 字节  clip=${JSON.stringify(m.clip)}  sha256=${sha}`);
  out.push({ id, name, ...m, sha, bytes: buf.length });
  markDown();
  await reset();
}

await deselect();
const after = await coords();
const moved = Object.keys(after).filter((id) => { const bs = BASELINE.nodes[id]; return !bs || !after[id] ||
  Math.abs(after[id][0] - bs.canvas[0]) > 0.01 || Math.abs(after[id][1] - bs.canvas[1]) > 0.01; });
console.log('\n配图结束。相对基线有位移的节点:', JSON.stringify(moved));
writeFileSync(new URL('./_tmp-b57-shots.json', import.meta.url), JSON.stringify({ shots: out, moved, after }, null, 1));
await b.close();
