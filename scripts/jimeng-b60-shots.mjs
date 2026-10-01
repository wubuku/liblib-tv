// 批次 60 配图：选中的**空音频节点**长什么样
//
// 这张图有两个用途：
//   ① 手册此前没有音频节点的外观记录（批次 59 建成过，但只量了连线矩阵）；
//   ② 它是「F 无反馈」这条结论的**视觉注脚** —— 按 F 之后画面就是这个样子，
//      没有编辑器、没有提示条。密集采样表才是这条结论的主证据。
import { chromium } from 'playwright';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { keyGuard, pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const DIR = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const MINE = [];

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

console.log('=== 批次 60 配图 ===\n');
await deselect();
const pre = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
await p.click('button[aria-label="上传"]').catch(() => {});
await reset();
// 走左栏新建音频节点（不用上传，上传会带内容）
await deselect();
const rb = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button')).find((x) => (x.getAttribute('aria-label') || '').startsWith('音频'));
  if (!e) return null; const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
if (!rb) { console.error('ABORT: 左栏没有音频入口'); await b.close(); process.exit(2); }
const p0 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
await p.mouse.click(rb.cx, rb.cy); await p.waitForTimeout(3200);
const made = (await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')))).filter((x) => !p0.includes(x));
if (made.length !== 1) { console.error('ABORT: 音频节点未建成', made); await b.close(); process.exit(3); }
MINE.push(made[0]);
console.log('音频节点', made[0], '| 选中:', await selectByScan(made[0]));
await p.waitForTimeout(1200);

const g = await keyGuard(p);
const info = await p.evaluate((v) => {
  const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
  const r = n.getBoundingClientRect();
  const form = document.querySelector('[data-testid="generation-form"]');
  const fr = form ? form.getBoundingClientRect() : null;
  return { nodeAria: n.getAttribute('aria-label'),
    nodeText: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80),
    box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    formAria: form ? form.getAttribute('aria-label') : null,
    formBox: fr ? `${Math.round(fr.width)}x${Math.round(fr.height)}@${Math.round(fr.x)},${Math.round(fr.y)}` : null,
    dialogs: Array.from(document.querySelectorAll('[role="dialog"]')).filter((e) => e.getBoundingClientRect().width > 1).length,
    clip: { x: Math.max(0, Math.round(r.x - 130)), y: Math.max(0, Math.round(r.y - 70)),
            width: Math.min(1280 - Math.max(0, Math.round(r.x - 130)), Math.round(r.width) + 300),
            height: Math.min(720 - Math.max(0, Math.round(r.y - 70)), Math.round(r.height) + 300) } };
}, made[0]);
console.log('焦点守卫:', g.safe ? '✅' : '⛔', g.where);
console.log('节点:', JSON.stringify(info, null, 1));

// 按一次 F，让截图就是「按完 F 之后」的真实画面
await p.keyboard.press('f');
await p.waitForTimeout(1800);
const after = await p.evaluate(() => ({ dialogs: Array.from(document.querySelectorAll('[role="dialog"]')).filter((e) => e.getBoundingClientRect().width > 1).length,
  hasSign: (document.body.innerText || '').includes('此快捷键当前不可用') }));
console.log('按 F 之后：dialogs =', after.dialogs, '| 页面含「此快捷键当前不可用」=', after.hasSign);

const buf = await p.screenshot({ type: 'png', clip: info.clip });
writeFileSync(new URL('102-audio-node-selected-f-inert.png', DIR), buf);
const sha = createHash('sha256').update(buf).digest('hex');
console.log(`截图 102-audio-node-selected-f-inert.png  ${buf.length} 字节  clip=${JSON.stringify(info.clip)}  sha256=${sha}`);

await reset();
console.log('删除音频节点:', await deleteById(made[0]));
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
await b.close();
