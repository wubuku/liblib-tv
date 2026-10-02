// 批次 95 · 收尾第 4 轮：删 `node_ce47a7tnzq` + 把这一轮顺带钉下的新契约读准。
//
// 上一轮（b95c）的增量 diff 一次就把**文本节点选中态的完整控件树**照出来了，顺带解掉两个悬案：
//   ① 批次 93「`[data-testid=node-toolbar]` 命中 2：1 真身 + 1 `0×0` 占位」——
//      0×0 那个的真身身份就是同位置的 `node-toolbar-feature-host`（也是 0×0@640,476）。
//   ② 三层嵌套终于连上了：`selection-context-toolbar-surface`(192×40, 可见外壳)
//      ⊃ `selection-context-toolbar`(160×40, 内容) ⊃ `node-toolbar`(testid 命中 2 个)。
//      ⇒ 批次 93 记的「宽度 160/192/320」里的 192 属于 **surface**、160 属于**内容**。
//
// 这一轮：点中 → 右键 → 点最后一项「删除 ⌫」→ 回读确认 → 归位缩放。
// 顺带读 scale，把 192/200/24/178/10/36 这些屏上读数换算成 canvas 值。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const ID = 'node_ce47a7tnzq';
const out = { at: new Date().toISOString(), target: ID };

const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const nodeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
// 缩放连读两次，两次相同才算静止——**除数必须当场读，绝不写死 0.6**
const scale2 = async () => { const a = await p.evaluate(() => { const e = document.querySelector('.react-flow__viewport'); if (!e) return null;
    const m = /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });
  await p.waitForTimeout(350);
  const c = await p.evaluate(() => { const e = document.querySelector('.react-flow__viewport'); if (!e) return null;
    const m = /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });
  return { first: a, second: c, stable: a !== null && a === c }; };

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits() };
log('起点：', JSON.stringify(out.start));

if (!(await ids()).includes(ID)) { log('✅ 已不在'); writeFileSync(new URL('./_tmp-b95d.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(0); }

const pt = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  for (let fx = 0.05; fx <= 0.95; fx += 0.05) for (let fy = 0.05; fy <= 0.95; fy += 0.05) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    if (x < 0 || y < 0 || x > 1280 || y > 0 + 720) continue;
    if (document.elementFromPoint(x, y)?.closest('.react-flow__node') === n) return { x, y };
  }
  return null;
}, ID);
out.pt = pt;
log('落点：', JSON.stringify(pt));

await p.mouse.click(pt.x, pt.y);
await p.waitForTimeout(1100);
out.sel = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
log('选中：', JSON.stringify(out.sel));

// 选中态控件树 + scale 换算（画布上第一次量到 resize 控件，值得留证）
out.chrome = await p.evaluate((s) => {
  const g = (tid) => { const e = document.querySelector(`[data-testid="${tid}"]`); if (!e) return null;
    const r = e.getBoundingClientRect();
    return { screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      canvas: s ? { w: Math.round(r.width / s * 100) / 100, h: Math.round(r.height / s * 100) / 100 } : null }; };
  return { scaleUsed: s,
    controls: g('text-node-resize-controls'), outline: g('text-node-selection-outline'), host: g('node-feature-chrome-host'),
    surface: g('selection-context-toolbar-surface'), content: g('selection-context-toolbar'),
    featureHost: g('node-toolbar-feature-host'),
    ntCount: document.querySelectorAll('[data-testid="node-toolbar"]').length,
    corners: ['text-node-resize-top-left', 'text-node-resize-top-right', 'text-node-resize-bottom-left', 'text-node-resize-bottom-right']
      .map((t) => [t, g(t)]),
    edges: ['text-node-resize-top', 'text-node-resize-bottom', 'text-node-resize-left', 'text-node-resize-right']
      .map((t) => [t, g(t)]),
    affordance: g('textarea-resize-affordance') };
}, (await scale2()).first);
log('选中态控件树：', JSON.stringify(out.chrome));

// 右键 → 删
await p.mouse.move(pt.x, pt.y);
await p.waitForTimeout(200);
await p.mouse.down({ button: 'right' });
await p.waitForTimeout(260);
await p.mouse.up({ button: 'right' });
await p.waitForTimeout(1500);

out.menu = await p.evaluate(() => {
  const m = document.querySelector('[data-testid="canvas-context-menu"]');
  if (!m) return null;
  const r = m.getBoundingClientRect();
  return { screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    items: Array.from(m.querySelectorAll('[role="menuitem"]')).map((x) => {
      const b = x.getBoundingClientRect();
      return { text: x.innerText.replace(/\s+/g, ' ').trim(), w: Math.round(b.width), h: Math.round(b.height),
        disabled: x.getAttribute('aria-disabled') }; }) };
});
log('菜单：', JSON.stringify(out.menu));

out.deleted = await p.evaluate(() => {
  const m = document.querySelector('[data-testid="canvas-context-menu"]');
  if (!m) return 'no-menu';
  const it = Array.from(m.querySelectorAll('[role="menuitem"]'))
    .find((x) => /^删除/.test(x.innerText.replace(/\s+/g, ' ').trim()) && x.getAttribute('aria-disabled') !== 'true');
  if (!it) return 'no-item';
  it.click(); return 'clicked';
});
log('点删除：', out.deleted);
await p.waitForTimeout(1800);

out.left = (await ids()).includes(ID);
log(out.left ? '🔴 还在' : '✅ 已删除');
if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }

const sc = await scale2();
out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(), scale: sc };
log('终态：', JSON.stringify(out.end));
log('残留自建节点：', JSON.stringify((await ids()).filter((x) => ['node_ce47a7tnzq', 'node_tjf3grfajp'].includes(x))));
writeFileSync(new URL('./_tmp-b95d.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
