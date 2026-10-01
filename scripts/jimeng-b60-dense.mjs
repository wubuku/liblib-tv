// 批次 60 第二轮：给「F 在音频上完全无反馈」这个阴性结论配**阳性对照**
//
// 第一轮的读数：在空音频节点上按 F，可见 DOM 差分 **+0 / −0**、无 dialog、无 toast、
// **连批次 40 记录的「此快捷键当前不可用」都没有**。
//
// 🔴 但这是个**阴性**结论。阴性结论的头号风险是「**它其实出现了，只是我没采到**」——
//   toast 可能一闪而过。只在 t=1500ms 采一次，采不到不等于没发生。
//
// 本轮做两件事：
//   ① **密集采样**：按 F 之后 t = 0/80/200/400/700/1200/2000/3000ms 各采一次
//      可见 DOM 指纹与 toast 签名（批次 43 已用同法排除过动画/瞬时假象）。
//   ② 🔑 **阳性对照**：用**视频节点**跑**完全相同**的流程。
//      批次 40 记录它在按 F 后会弹「此快捷键当前不可用」117×22 toast ——
//      **如果同样的采样抓不到它，说明是我的采样方法不行，不是音频真的没反应。**
//      这一步是本轮的全部意义：先证明尺子能量出东西，再拿尺子量音频。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { keyGuard, pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OUT = new URL('./_tmp-b60-dense.json', import.meta.url);
const MINE = [];
const SIGN = '此快捷键当前不可用';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);
const reset = async () => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); } };
const selIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const isEmpty = (x, y) => p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); if (!el) return true;
  if (el.closest('.react-flow__node')) return false;
  if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"]')) return false;
  return true; }, [x, y]);
const findEmpty = async () => { for (let y = 110; y <= 630; y += 20) for (let x = 80; x <= 1250; x += 20) { if (x > 1150 && y > 600) continue; if (await isEmpty(x, y)) return { x, y }; } return null; };
const deselect = async () => { await reset(); const e = await findEmpty();
  if (e) { await p.mouse.click(e.x, e.y); await p.waitForTimeout(600); }
  for (let i = 0; i < 3 && (await selIds()).length; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  return (await selIds()).length === 0; };
const selectByScan = async (id) => {
  const pts = await p.evaluate((vid) => { const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return [];
    const r = n.getBoundingClientRect(); const out = [];
    for (let fy = 0.10; fy <= 0.92; fy += 0.06) for (let fx = 0.10; fx <= 0.92; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y);
      if (!el || !el.closest(`.react-flow__node[data-id="${vid}"]`)) continue;
      if (el.closest('button,a,[role="button"],input,textarea,select,[role="menu"],[contenteditable="true"]')) continue;
      out.push({ x, y }); } return out; }, id);
  for (const pt of pts) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(550);
    const s = await selIds(); if (s.length === 1 && s[0] === id) return true; }
  return false;
};
const makeNode = async (kind) => {
  await deselect();
  const rb = await p.evaluate((nm) => { const e = Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button'))
      .find((x) => (x.getAttribute('aria-label') || '').startsWith(nm)); if (!e) return null;
    const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }, kind);
  if (!rb) return null;
  const pre = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
  await p.mouse.click(rb.cx, rb.cy); await p.waitForTimeout(3000);
  const made = (await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')))).filter((x) => !pre.includes(x));
  if (made.length !== 1) return null;
  MINE.push(made[0]); return made[0];
};
const deleteById = async (id) => {
  if (!(await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"]`), id))) return 'absent';
  await deselect(); if (!(await selectByScan(id))) return 'notselected';
  await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return;
    const r = e.getBoundingClientRect();
    e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 14) })); }, id);
  await p.waitForTimeout(800);
  const ok = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop(); if (!m) return false;
    const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (!it) return false; it.click(); return true; });
  await p.waitForTimeout(1300); await reset(); return ok ? 'deleted' : 'noclick';
};

// 一次采样：可见元素数 + 签名 toast + 任何新增的可见元素
// ⚠️ 基线必须以**数组**传进页面：Set 过不了 page.evaluate 的序列化，b.has 会炸。
const probe = (baseArr) => p.evaluate(([b, sign]) => {
  const bset = new Set(b);
  const vis = Array.from(document.querySelectorAll('body *')).filter((e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1; });
  const fp = new Set(vis.map((e) => { const r = e.getBoundingClientRect();
    return `${e.tagName}#${e.id || ''}.${String(e.className || '').split(' ').filter(Boolean).slice(0, 2).join('.')}@${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)}`; }));
  const added = [...fp].filter((x) => !bset.has(x));
  const hits = vis.filter((e) => { const r = e.getBoundingClientRect(); const t = (e.innerText || '').trim();
    return t.includes(sign) && r.width > 1 && r.height > 1; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { tag: e.tagName, text: (e.innerText || '').trim().slice(0, 30), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
        role: e.getAttribute('role'), aria: e.getAttribute('aria-label') }; });
  return { n: vis.length, added: added.slice(0, 6), hits: hits.slice(0, 3) };
}, [baseArr, SIGN]);

const denseF = async (id, label) => {
  await deselect();
  if (!(await selectByScan(id))) return { label, err: '选不中' };
  const g = await keyGuard(p);
  if (!g.safe) return { label, err: `焦点不安全：${g.where}` };
  const vis0 = await p.evaluate(() => Array.from(document.querySelectorAll('body *')).filter((e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1; })
    .map((e) => { const r = e.getBoundingClientRect();
      return `${e.tagName}#${e.id || ''}.${String(e.className || '').split(' ').filter(Boolean).slice(0, 2).join('.')}@${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)}`; }));
  const url0 = p.url();
  await p.keyboard.press('f');
  const timeline = [];
  const marks = [0, 80, 200, 400, 700, 1200, 2000, 3000];
  let prev = 0;
  for (const t of marks) { await p.waitForTimeout(t - prev); prev = t;
    const s = await probe(vis0);
    timeline.push({ t, n: s.n, hits: s.hits, added: s.added });
  }
  const urlChanged = p.url() !== url0;
  await reset();
  const anyHit = timeline.some((s) => s.hits.length);
  const anyAdded = timeline.some((s) => s.added.length);
  return { label, id, samples: timeline.map((s) => ({ t: s.t, n: s.n, hit: s.hits.length ? s.hits[0] : null, added: s.added.length })),
    anyHit, anyAdded, urlChanged, verdict: anyHit ? `命中签名「${SIGN}」` : (anyAdded ? '无签名但有可见新增' : '全程无任何可见变化') };
};

console.log('=== 批次 60 第二轮：密集采样 + 阳性对照 ===\n');
const out = { startedAt: new Date().toISOString(), rows: [] };

// ① 阳性对照：他���的视频 1（批次 40 记录：会弹「此快捷键当前不可用」117×22）
console.log('① 阳性对照 —— 视频 1（他人节点，只读：选中 + 按 F，不动内容）');
const vid = BASELINE.nodes['node_236ctpehgg'] ? 'node_236ctpehgg' : null;
const rv = await denseF(vid, '视频 1');
console.log(JSON.stringify(rv.samples, null, 1));
console.log(`  判定：${rv.verdict} | 页面跳转：${rv.urlChanged ? '⛔ 是' : '否'}`);
out.rows.push(rv);

// ② 音频
console.log('\n② 被测 —— 空音频节点');
const aid = await makeNode('音频');
if (!aid) { console.error('ABORT: 音频节点没建成'); await b.close(); process.exit(2); }
const ra = await denseF(aid, '音频 1（空）');
console.log(JSON.stringify(ra.samples, null, 1));
console.log(`  判定：${ra.verdict} | 页面跳转：${ra.urlChanged ? '⛔ 是' : '否'}`);
out.rows.push(ra);
console.log('\n删除音频节点:', await deleteById(aid));

// ③ 判读
console.log('\n================ 判读 ================');
console.log(`阳性对照（视频）${rv.anyHit ? '✅ 采样方法抓到了签名' : '⛔ 采样方法抓不到签名 —— 结论不成立，尺子坏了'}`);
if (rv.anyHit) console.log(`被测（音频）${ra.anyHit ? '也有签名' : '✅ 确证无签名'} ⇒ ${ra.verdict}`);
else console.log('⚠️ 尺子抓不到视频的签名，无法据此判定音频。需要更密的采样或换判据。');

await reset();
for (let t = 0; t < 3; t++) { const z = await zoomOf();
  if (z && z.includes('60%')) { console.log('缩放归位 ok:', z); break; }
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
  const s = 'input[data-testid="canvas-zoom-percent-input"]';
  if (await p.$(s)) { await p.fill(s, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); }
  else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  if (t === 2) console.log('缩放归位 FAILED:', await zoomOf()); }
await reset();
const fin = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
  const mm = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
  return [e.getAttribute('data-id'), mm ? [Math.round(parseFloat(mm[1]) * 100) / 100, Math.round(parseFloat(mm[2]) * 100) / 100] : null]; })));
console.log('终态缩放:', await zoomOf(), '| 节点数:', Object.keys(fin).length, '| 选中:', (await selIds()).length);
for (const [id, c] of Object.entries(fin)) { const bs = BASELINE.nodes[id];
  console.log(`  ${id} Δ=${JSON.stringify(bs ? [+(c[0] - bs.canvas[0]).toFixed(2), +(c[1] - bs.canvas[1]).toFixed(2)] : '?')}`); }
out.end = { zoom: await zoomOf(), coords: fin };
writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log('写入', OUT.pathname);
await b.close();
