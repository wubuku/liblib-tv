// 批次 53：自动适配的触发条件 —— 直接测「内容包围盒撑破视口，却不触发适配」
//
// 批次 51 已经拿到一组反证：带内容的图片节点与空视频节点**画布尺寸相同**（569×320），
// 一个触发一个不触发 ⇒ 「节点更大/包围盒变大」不是开关。
// 但那还留了个缝：两者落点一样，包围盒增长幅度一样吗？
//
// 本批把缝补上，测两件事：
//   A. 空媒体节点（预期触发）—— 记录包围盒**增长了多少**、视口还装不装得下
//   B. 带内容媒体节点（预期不触发）—— 记录包围盒**增长了多少**、视口还装不装得下
//
// 🔑 判据：若 B 的内容包围盒**已经超出视口可视范围**（装不下）而缩放**仍然不变**，
//    那么「几何/装不装得下」根本不是触发条件 —— 自动适配与内容包围盒无关。
//
// 全程不点任何生成/发送类按钮；临时节点先记账，收尾按 id 全删。
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
import { keyGuard, canvasBaseline, diffNodePositions, pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OTHERS = Object.keys(BASELINE.nodes);
const UPLOAD = '/tmp/b22-upload.png';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('canvas page not found'); process.exit(1); }
await pinViewport(p);
const reset = async () => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); } };
const real = (l) => l.filter((x) => !String(x).startsWith('__group-resize-chrome__'));
const ids = async () => real(await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id'))));
const vp = () => p.evaluate(() => { const v = document.querySelector('.react-flow__viewport');
  const m = v && /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/.exec(v.style.transform);
  const pane = document.querySelector('.react-flow__pane');
  return m ? { tx: +m[1], ty: +m[2], scale: +m[3], paneW: pane ? pane.clientWidth : null, paneH: pane ? pane.clientHeight : null } : null; });
// 内容包围盒 + 视口当前能看到的内容范围（画布坐标）
const geom = () => p.evaluate(() => {
  const boxes = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => !e.classList.contains('react-flow__node-group'))
    .map((e) => { const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform); const r = e.getBoundingClientRect();
      const v = document.querySelector('.react-flow__viewport');
      const s = /scale\(([-\d.]+)\)/.exec(v.style.transform);
      const sc = s ? +s[1] : 1;
      const mm = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(v.style.transform);
      return { id: e.getAttribute('data-id'), x: m ? +m[1] : null, y: m ? +m[2] : null, w: r.width / sc, h: r.height / sc }; })
    .filter((o) => o.x !== null);
  if (!boxes.length) return null;
  const x0 = Math.min(...boxes.map((o) => o.x)), y0 = Math.min(...boxes.map((o) => o.y));
  const x1 = Math.max(...boxes.map((o) => o.x + o.w)), y1 = Math.max(...boxes.map((o) => o.y + o.h));
  const v = document.querySelector('.react-flow__viewport');
  const s = /scale\(([-\d.]+)\)/.exec(v.style.transform); const sc = s ? +s[1] : 1;
  const mm = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(v.style.transform);
  const tx = mm ? +mm[1] : 0, ty = mm ? +mm[2] : 0;
  const pane = document.querySelector('.react-flow__pane');
  const pw = pane ? pane.clientWidth : 1280, ph = pane ? pane.clientHeight : 720;
  // 当前视口覆盖的画布范围
  const vx0 = (0 - tx) / sc, vy0 = (0 - ty) / sc, vx1 = (pw - tx) / sc, vy1 = (ph - ty) / sc;
  return { bbox: [x0, y0, x1, y1].map((v) => Math.round(v)), count: boxes.length, scale: +sc.toFixed(6),
    view: [vx0, vy0, vx1, vy1].map(Math.round), pane: [pw, ph],
    // 内容是否超出视口可视范围
    overflow: { left: Math.round(vx0 - x0), top: Math.round(vy0 - y0), right: Math.round(x1 - vx1), bottom: Math.round(y1 - vy1) },
    fits: x0 >= vx0 && y0 >= vy0 && x1 <= vx1 && y1 <= vy1 };
});
const isEmpty = (x, y) => p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); if (!el) return true;
  if (el.closest('.react-flow__node')) return false;
  if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"]')) return false;
  return true; }, [x, y]);
const findEmpty = async () => { for (let y = 110; y <= 630; y += 20) for (let x = 80; x <= 1250; x += 20) { if (x > 1150 && y > 600) continue; if (await isEmpty(x, y)) return { x, y }; } return null; };
const setTool = async (want) => { const cur = await p.evaluate(() => (document.querySelector('[data-testid="canvas-pointer-tool-toggle"]') || {}).getAttribute?.('aria-label'));
  if (cur !== want) { await p.evaluate(() => document.querySelector('[data-testid="canvas-pointer-tool-toggle"]').click()); await p.waitForTimeout(600); } };
const drag = async (from, tdx, tdy) => { const steps = Math.max(1, Math.ceil(Math.max(Math.abs(tdx), Math.abs(tdy)) / 130));
  await p.mouse.move(from.x, from.y); await p.mouse.down(); await p.waitForTimeout(120);
  for (let i = 1; i <= steps; i++) { await p.mouse.move(from.x + (tdx * i) / steps, from.y + (tdy * i) / steps); await p.waitForTimeout(45); }
  await p.mouse.up(); await p.waitForTimeout(650); };
const panTo = async (CX, CY) => { for (let r = 0; r < 20; r++) { const v = await vp(); if (!v) return false;
  const dx = (640 - CX * v.scale) - v.tx, dy = (480 - CY * v.scale) - v.ty;
  if (Math.abs(dx) < 4 && Math.abs(dy) < 4) return true;
  const s = await findEmpty(); if (!s) return false;
  await drag(s, Math.max(-130, Math.min(130, dx)), Math.max(-90, Math.min(90, dy))); } return false; };
const deleteById = async (id) => { if (!(await ids()).includes(id)) return 'absent';
  const pt = await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return null; const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 16) }; }, id);
  if (!pt) return 'nobox';
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(650);
  if (await p.evaluate((v) => { const s = document.querySelector('.react-flow__node.selected'); return !s || s.getAttribute('data-id') !== v; }, id)) {
    await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return; const r = e.getBoundingClientRect();
      for (const t of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) e.dispatchEvent(new MouseEvent(t, { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 16) })); }, id);
    await p.waitForTimeout(650); }
  if (await p.evaluate((v) => { const s = document.querySelector('.react-flow__node.selected'); return !s || s.getAttribute('data-id') !== v; }, id)) return 'notselected';
  await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return; const r = e.getBoundingClientRect(); e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 12) })); }, id);
  await p.waitForTimeout(650);
  const ok = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop(); if (!m) return false;
    const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (!it) return false; it.click(); return true; });
  await p.waitForTimeout(1300); return ok ? 'deleted' : 'noclick'; };
const restoreZoom = async () => {
  await reset(); await setTool('选择工具');
  await p.mouse.click(700, 150); await p.waitForTimeout(500);
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(600);
  const z = 'input[data-testid="canvas-zoom-percent-input"]';
  if (await p.$(z)) { await p.fill(z, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(900); }
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(600);
  await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-zoom-menu"]'); const it = m && Array.from(m.querySelectorAll('button,[role="menuitem"]')).find((e) => /适配画布/.test(e.innerText || '')); if (it) it.click(); });
  await p.waitForTimeout(1400);
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  await p.mouse.click(700, 150); await p.waitForTimeout(700);
};
const CREATED = [];
const report = async (label) => {
  const g = await geom();
  console.log(`  ${label}: scale=${g.scale} 节点数=${g.count}`);
  console.log(`    内容包围盒 ${JSON.stringify(g.bbox)} | 视口可视范围 ${JSON.stringify(g.view)} | pane ${JSON.stringify(g.pane)}`);
  console.log(`    超出视口 ${JSON.stringify(g.overflow)} | 全部装得下？ ${g.fits ? '✅ 是' : '❌ 否'}`);
  return g;
};

try {
  await reset();
  const bad0 = await diffNodePositions(p, BASELINE.nodes, 1.5);
  if (bad0.length || (await ids()).length !== 6) throw new Error('起点与基线不一致');
  console.log('起点与基线一致 ✅');
  await restoreZoom();
  const g0 = await report('起点（6 节点）');

  // ---------- A：空图片节点（预期触发）----------
  console.log('\n########## A 左栏「图片」→ 空图片节点 ##########');
  await setTool('抓手工具');
  if (!await panTo(1700, 400)) throw new Error('平移失败');
  await setTool('选择工具');
  const vA0 = await vp();
  const bA = await ids();
  await p.evaluate(() => { const t = Array.from(document.querySelectorAll('button,[role="button"]')).find((e) => e.getAttribute('aria-label') === '图片'); if (t) t.click(); });
  await p.waitForTimeout(2000);
  const freshA = (await ids()).filter((x) => !bA.includes(x));
  if (freshA.length !== 1) throw new Error(`A 新增 ${freshA.length} 个`);
  CREATED.push(freshA[0]);
  const vA1 = await vp();
  const gA = await report('A 建完空图片节点');
  console.log(`  缩放 ${vA0.scale} → ${vA1.scale}  ${vA0.scale !== vA1.scale ? '🔴 触发自动适配' : '❌ 未触发'}`);
  console.log(`  包围盒横向 ${g0.bbox[2] - g0.bbox[0]} → ${gA.bbox[2] - gA.bbox[0]}（+${gA.bbox[2] - gA.bbox[0] - (g0.bbox[2] - g0.bbox[0])}）`);
  await reset();
  console.log('  删', freshA[0], '→', await deleteById(freshA[0]));
  CREATED.pop();
  await restoreZoom();

  // ---------- B：上传得到带内容图片节点（预期不触发）----------
  console.log('\n########## B 左栏「上传」→ 带内容图片节点 ##########');
  await setTool('抓手工具');
  if (!await panTo(1700, 400)) throw new Error('平移失败');
  await setTool('选择工具');
  const vB0 = await vp();
  const bB = await ids();
  const [chooser] = await Promise.all([p.waitForEvent('filechooser', { timeout: 15000 }), p.click('button[aria-label="上传"]')]);
  await chooser.setFiles(UPLOAD);
  await p.waitForTimeout(3400);
  const freshB = (await ids()).filter((x) => !bB.includes(x));
  if (freshB.length !== 1) throw new Error(`B 新增 ${freshB.length} 个`);
  CREATED.push(freshB[0]);
  const hasImg = await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); return e ? e.querySelectorAll('img').length : -1; }, freshB[0]);
  console.log(`  前置条件自证：新节点 ${freshB[0]} 的 img 元素 ${hasImg} 个 ${hasImg > 0 ? '✅ 真的有内容' : '❌'}`);
  const vB1 = await vp();
  const gB = await report('B 建完带内容图片节点');
  console.log(`  缩放 ${vB0.scale} → ${vB1.scale}  ${vB0.scale !== vB1.scale ? '🔴 触发自动适配' : '❌ 未触发'}`);
  console.log(`  包围盒横向 ${g0.bbox[2] - g0.bbox[0]} → ${gB.bbox[2] - gB.bbox[0]}（+${gB.bbox[2] - gB.bbox[0] - (g0.bbox[2] - g0.bbox[0])}）`);
  console.log(`  🔑 判据：内容是否已经装不进视口？ ${gB.fits ? '装得下（此轮证据不充分）' : `❌ 装不下（右侧超出 ${gB.overflow.right} 画布像素），而缩放仍未变`}`);
  await reset();
  console.log('  删', freshB[0], '→', await deleteById(freshB[0]));
  CREATED.pop();
} catch (e) {
  console.error('ABORT:', e.message);
}

await restoreZoom();
for (const id of CREATED) console.log('  兜底删', id, '→', await deleteById(id));
const fin = await canvasBaseline(p);
const bad = await diffNodePositions(p, BASELINE.nodes, 1.5);
const g = await keyGuard(p);
console.log('\n=== 收尾核对 ===');
console.log(' 焦点守卫:', g.safe ? '✅' : g.where, '| 节点数', fin.nodes.length, '| 真编组', (await p.evaluate(() => document.querySelectorAll('.react-flow__node-group').length)));
console.log(' 状态行:', fin.status, '| 积分', fin.credit, '| 缩放', fin.zoom);
console.log(' 位置偏离:', bad.length, bad.length ? bad.join(',') : '✅ 0', '| 剩余待删:', JSON.stringify(CREATED));
await b.close();
