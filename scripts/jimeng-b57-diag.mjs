// 批次 57 诊断：把被 tail 截掉的逐行读数捞回来 —— **一次点击都不做**。
//
// 批次 57 主脚本给出的结论段说：静息态下 7 种类型里 6 种
// **找不到任何 `/^(Rename|Edit)\s/` 的 aria 元素**（不是不可见，是不存在）。
// 这与批次 28「标题 Rename … **始终**可见」直接冲突，必须分清是
//   ① 读数方法错了（标题被 portal 挂在节点子树之外，querySelector 找不到）
// 还是
//   ② 读数对了（标题确实是 hover/选中才出现的，不是「始终」）。
// 判别法：**同时**扫「节点子树内」与「整篇文档里带该节点名的元素」，
// 整篇文档里没有 ⇒ 不是 portal 问题，是真的不存在。
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
import { canvasBaseline, diffNodePositions, pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);
for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); }

const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const scaleOf = () => p.evaluate(() => { const v = document.querySelector('.react-flow__viewport');
  const m = v && /scale\(([-\d.]+)\)/.exec(v.style.transform); return m ? +(+m[1]).toFixed(4) : null; });

// 归位缩放：**回读验证 + 最多重试 3 次**（批次 56 踩过「填了没生效」的坑）
const restoreZoom = async (want = '60') => {
  for (let r = 0; r < 3; r++) {
    const now = await zoomOf();
    if (now && now.includes(`${want}%`)) return `ok@第${r + 1}次 (${now})`;
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
    const z = 'input[data-testid="canvas-zoom-percent-input"]';
    if (await p.$(z)) { await p.fill(z, want); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); }
    else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  }
  return `FAILED (${await zoomOf()})`;
};

console.log('=== 批次 57 诊断（只读，零点击）===\n');
console.log('归位缩放:', await restoreZoom('60'), '| scale =', await scaleOf(), '\n');

const base = await canvasBaseline(p);
console.log('状态行:', base.status, '| 缩放读数:', base.zoom, '| 节点数:', base.nodes.length, '\n');

for (const n of base.nodes) {
  const r = await p.evaluate((vid) => {
    const node = document.querySelector(`.react-flow__node[data-id="${vid}"]`);
    if (!node) return null;
    const name = (node.getAttribute('aria-label') || '');
    // 节点自己的名字：优先 title testid，其次 innerText 首行
    const tEl = node.querySelector('[data-testid="flow-node-title"]');
    const own = tEl ? (tEl.innerText || '').trim() : ((node.innerText || '').split('\n').find((s) => s.trim()) || '').trim();
    const RR = (e) => { const r = e.getBoundingClientRect(); return `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)}`; };
    const inAria = Array.from(node.querySelectorAll('[aria-label]')).filter((e) => (e.getAttribute('aria-label') || '').length > 0)
      .map((e) => ({ a: e.getAttribute('aria-label'), t: e.getAttribute('data-testid'), r: RR(e), vis: e.getBoundingClientRect().width > 1 }));
    const inTid = Array.from(node.querySelectorAll('[data-testid]')).map((e) => ({ t: e.getAttribute('data-testid'), r: RR(e) }));
    // 整篇文档里有没有「带这个节点名」的标题按钮（用来判 portal）
    const docHits = Array.from(document.querySelectorAll('[aria-label]'))
      .filter((e) => /^(Rename|Edit)\s/.test(e.getAttribute('aria-label') || ''))
      .map((e) => ({ a: e.getAttribute('aria-label'), inNode: !!e.closest(`.react-flow__node[data-id="${vid}"]`), r: RR(e),
                     parentChain: (() => { let x = e, c = []; for (let i = 0; i < 5 && x; i++) { c.push(x.tagName + (x.getAttribute('data-testid') ? `[${x.getAttribute('data-testid')}]` : '') + (x.className && typeof x.className === 'string' ? '.' + x.className.split(' ')[0] : '')); x = x.parentElement; } return c.join(' < '); })() }));
    const r = node.getBoundingClientRect();
    return { name, own, cls: Array.from(node.classList).filter((c) => c.startsWith('react-flow__node-')).join(','),
      nodeRect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)}`,
      inAria, inTid, docHits, docRenameTotal: docHits.length };
  }, n.id);
  if (!r) { console.log(`${n.id} 不在 DOM`); continue; }
  console.log(`── ${n.id}  [${r.cls}]  名字=${JSON.stringify(r.own)}  卡片 ${r.nodeRect}`);
  console.log(`   节点 aria-label: ${JSON.stringify(r.name)}`);
  console.log(`   子树内带 aria 的元素: ${r.inAria.length}  |  带 data-testid 的元素: ${r.inTid.length}`);
  for (const e of r.inAria) console.log(`      aria=${JSON.stringify(e.a).padEnd(46)} testid=${String(e.t).padEnd(42)} ${e.r}${e.vis ? '' : '  (不可见)'}`);
  console.log(`   整篇文档里 ^(Rename|Edit) 元素共 ${r.docRenameTotal} 个；属于本节点的: ${r.docHits.filter((h) => h.inNode).length}`);
  for (const h of r.docHits) console.log(`      ${h.inNode ? '本节点内' : '别处    '} ${JSON.stringify(h.a)}  ${h.r}\n            ${h.parentChain}`);
  console.log('');
}

const drifted = await diffNodePositions(p, Object.fromEntries(Object.entries(BASELINE.nodes).map(([k, v]) => [k, v.canvas])));
console.log('他人节点位置偏离:', JSON.stringify(drifted), '| 终态缩放:', await zoomOf(), '| scale:', await scaleOf());
await b.close();
process.exit(0);
