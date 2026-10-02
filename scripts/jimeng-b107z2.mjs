// 批次 107 · z2 轮：删掉 `node_gmvz7secas` 并归位。
//
// z 轮正确地**中止了**（第四道护栏起作用：菜单里没读到「删除」项 ⇒ 不猜、不硬删）——
// 这就是它该有的行为。查了一下：右键菜单**确实没弹出来**
// （全页没有任何含「复制」的小浮层，`canvas-context-menu` 也不存在）。
//   最可能的原因：z 轮先左击选中（`selected` 翻转会触发重渲染），
//   紧接着就在同一点上右键，事件落在了重渲染后的新元素上。
//   ⇒ 本轮把「右键」与「点选」**彻底分开**，中间留足重渲染时间，
//     并且**在右键前重新校验一次落点**。
//
// 备用姿势（批次 30 实测更稳）：**在已选中的节点上直接派发 `contextmenu` 事件**。
// 本轮先试鼠标姿势，不行再走事件派发，并把实际用了哪条记下来。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), selfId: 'node_gmvz7secas' };
const SELF = out.selfId;
const save = () => writeFileSync(new URL('./_tmp-b107z2.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => { const t = document.body.innerText;
  const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
  const tb = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1], zoom: z ? z.getAttribute('aria-label') : null,
    tool: tb ? tb.getAttribute('aria-label') : null, inEditor: !!document.querySelector('.tiptap.ProseMirror'),
    credits: (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label') }; });
const selOf = (i) => p.evaluate((id) => { const e = document.querySelector(`.react-flow__node[data-id="${id}"]`); return e ? e.classList.contains('selected') : null; }, i);

out.start = await status();
out.idsBefore = (await allIds()).length;
log('起点：', JSON.stringify(out.start), '｜id 数', out.idsBefore);
if (out.start.inEditor) { await p.keyboard.press('Escape'); await p.waitForTimeout(1200); }

// ---- 安全落点 + 确认已选中（不再点，避免重渲染） ----
out.spot = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  const others = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => e.getAttribute('data-id') !== i)
    .map((e) => { const q = e.getBoundingClientRect(); return { x: q.x, y: q.y, w: q.width, h: q.height }; });
  const cands = [];
  for (let fy = 0.15; fy <= 0.85; fy += 0.05) for (let fx = 0.1; fx <= 0.9; fx += 0.05) {
    const x = r.x + r.width * fx, y = r.y + r.height * fy;
    if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
    const el = document.elementFromPoint(x, y);
    if (!el || !(el === n || n.contains(el))) continue;
    if (others.some((o) => x >= o.x && x <= o.x + o.w && y >= o.y && y <= o.y + o.h)) continue;
    cands.push({ x: Math.round(x), y: Math.round(y) });
  }
  return { rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`, total: cands.length, sample: cands.slice(0, 6) };
}, SELF);
log('\n落点：', JSON.stringify(out.spot));
const P = out.spot && out.spot.sample && out.spot.sample[0];
if (!P) { log('🔴 无安全落点，中止'); save(); await b.close(); process.exit(1); }

out.selNow = await selOf(SELF);
log('当前 selected =', out.selNow);
if (!out.selNow) {
  await p.mouse.move(P.x, P.y); await p.waitForTimeout(500);
  await p.mouse.click(P.x, P.y); await p.waitForTimeout(1600);
  out.selNow = await selOf(SELF);
  log('点选后 selected =', out.selNow);
}
if (!out.selNow) { log('🔴 没选中，中止'); save(); await b.close(); process.exit(1); }

// ---- 右键：与点选彻底分开，先重新校验落点 ----
const recheck = await p.evaluate((a) => {
  const n = document.querySelector(`.react-flow__node[data-id="${a.id}"]`); if (!n) return { __err: 'gone' };
  const el = document.elementFromPoint(a.x, a.y);
  return { ok: !!(el && (el === n || n.contains(el))), top: el ? el.tagName + ' ' + String(el.className).slice(0, 30) : null };
}, { id: SELF, x: P.x, y: P.y });
out.recheck = recheck;
log('右键前落点复核：', JSON.stringify(recheck));
if (!recheck.ok) { log('🔴 落点已失效，中止'); save(); await b.close(); process.exit(1); }

log('\n>>> 鼠标右键（move → down → 停 320ms → up）');
await p.mouse.move(P.x, P.y); await p.waitForTimeout(600);
await p.mouse.down({ button: 'right' }); await p.waitForTimeout(320); await p.mouse.up({ button: 'right' });
await p.waitForTimeout(1500);

const readMenu = () => p.evaluate(() => {
  const m = Array.from(document.querySelectorAll('div,ul,section')).find((x) => { const q = x.getBoundingClientRect();
    return q.width > 60 && q.width < 600 && q.height > 60 && getComputedStyle(x).visibility !== 'hidden'
      && (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith('复制 ⌘ C'); });
  if (!m) return null;
  const q = m.getBoundingClientRect();
  const rows = Array.from(m.querySelectorAll('button,[role=menuitem]')).map((e) => e.innerText.replace(/\s+/g, ' ').trim()).filter(Boolean);
  const btn = Array.from(m.querySelectorAll('button,[role=menuitem]')).find((e) => /^删除/.test(e.innerText.trim()));
  const r = btn ? btn.getBoundingClientRect() : null;
  return { w: Math.round(q.width), h: Math.round(q.height), rows,
    del: r ? { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) } : null };
});
out.menu = await readMenu();
log('菜单：', JSON.stringify(out.menu));
save();

if (!out.menu || !out.menu.del) {
  log('\n>>> 换备用姿势：在已选中节点上直接派发 contextmenu 事件（批次 30）');
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (n) n.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: 600, clientY: 400 })); }, SELF);
  await p.waitForTimeout(1400);
  out.menu2 = await readMenu();
  out.usedDispatch = true;
  log('事件派发后的菜单：', JSON.stringify(out.menu2));
  out.menu = out.menu2;
  save();
} else { out.usedDispatch = false; }

if (out.menu && out.menu.del) {
  log('\n>>> 点删除', JSON.stringify(out.menu.del));
  await p.mouse.move(out.menu.del.x, out.menu.del.y); await p.waitForTimeout(450);
  await p.mouse.click(out.menu.del.x, out.menu.del.y);
  await p.waitForTimeout(2200);
}
const idsAfter = await allIds();
out.idsAfter = idsAfter.length;
out.gone = !idsAfter.includes(SELF);
out.end = await status();
log('\n节点数：', out.idsBefore, '→', out.idsAfter, '｜目标已消失 =', out.gone);
log('终态：', JSON.stringify(out.end));

if (!/60%/.test(out.end.zoom || '')) {
  log('\n>>> 缩放归位 60%');
  await p.click('[data-testid="canvas-zoom-percent"]').catch(() => {});
  await p.waitForTimeout(1400);
  await p.fill('[data-testid="canvas-zoom-percent-input"]', '').catch(() => {});
  await p.type('[data-testid="canvas-zoom-percent-input"]', '60', { delay: 200 });
  await p.waitForTimeout(400); await p.keyboard.press('Enter'); await p.waitForTimeout(2000);
  const a = await status(); await p.waitForTimeout(1300); const c = await status();
  out.restored = { a: a.zoom, b: c.zoom, ok: a.zoom === c.zoom && /60%/.test(a.zoom) };
  log('归位读数：', a.zoom, '/', c.zoom, out.restored.ok ? '✅' : '🔴');
}
out.final = await status();
log('\n最终：', JSON.stringify(out.final));
out.clean = out.gone && out.final.sel === '0' && /60%/.test(out.final.zoom || '') && out.final.tool === '选择工具';
log('clean =', out.clean);
save();
await b.close();
