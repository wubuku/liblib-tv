// 批次 54：自动适配的触发条件 —— 用「复制副本」这条**第三条路径**做判别
//
// 已知（批次 51/53）：
//   左栏新建**空**媒体节点   → 🔴 触发自动适配
//   左栏「上传」得到**带内容**媒体节点 → ❌ 不触发
// 两个变量混在一起：「节点为空」与「创建入口」。
//
// 复制副本（⌘D / 右键「复制副本」）提供**第三条路径**：它复制一个**已存在**的节点，
// 因此可以做到「入口 ≠ 左栏新建」，同时分别用空节点和带内容节点去试：
//   C1 复制一个**空视频节点**   → 入口=复制，节点=空
//   C2 复制一个**带内容图片节点** → 入口=复制，节点=带内容
//
// 判读：
//   若 C1 也不触发 ⇒ 触发条件与「节点为空」无关，**绑定在左栏「新建」这个动作上**；
//   若 C1 触发     ⇒ 「节点为空」才是关键，入口无关。
// 无论哪种结果，都是在缩小未关闭的那条边界。
//
// 复制副本是本地编辑（不扣积分），收尾按 id 删除副本。
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
import { keyGuard, canvasBaseline, diffNodePositions, pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
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
  return m ? { tx: +m[1], ty: +m[2], scale: +m[3], raw: v.style.transform } : null; });
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
  await p.waitForTimeout(700);
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
// 右键菜单里点逐字为 txt 的项，并返回菜单实际逐字清单
const clickMenuItem = async (txt) => {
  const menu = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
    return m ? Array.from(m.querySelectorAll('[role="menuitem"]')).map((e) => ({ t: (e.innerText || '').trim().split('\n')[0], dis: e.getAttribute('aria-disabled') })) : null; });
  const hit = await p.evaluate((t) => { const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop(); if (!m) return false;
    const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => (x.innerText || '').trim().split('\n')[0] === t); if (!it) return false; it.click(); return true; }, txt);
  return { menu, hit };
};
const selectMine = async (id) => {
  const pt = await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return null; const r = e.getBoundingClientRect();
    for (let fy = 0.1; fy <= 0.9; fy += 0.08) for (let fx = 0.1; fx <= 0.9; fx += 0.08) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const el = document.elementFromPoint(x, y); const n = el && el.closest('.react-flow__node');
      if (n && n.getAttribute('data-id') === v) return { x, y }; }
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 16) }; }, id);
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(800);
  return (await ids()).includes(id);
};
const CREATED = [];

try {
  await reset();
  const bad0 = await diffNodePositions(p, BASELINE.nodes, 1.5);
  if (bad0.length || (await ids()).length !== 6) throw new Error('起点与基线不一致');
  console.log('起点与基线一致 ✅');
  await restoreZoom();

  // ================= C1：复制一个「空视频节点」 =================
  console.log('\n########## C1 入口=复制副本，节点=空视频 ##########');
  await setTool('抓手工具');
  if (!await panTo(1700, 400)) throw new Error('平移失败');
  await setTool('选择工具');
  const c0 = await ids();
  await p.evaluate(() => { const t = Array.from(document.querySelectorAll('button,[role="button"]')).find((e) => e.getAttribute('aria-label') === '视频'); if (t) t.click(); });
  await p.waitForTimeout(2000);
  const vid = (await ids()).filter((x) => !c0.includes(x));
  if (vid.length !== 1) throw new Error(`空视频节点新增 ${vid.length} 个`);
  CREATED.push(vid[0]);
  console.log('  已建空视频节点', vid[0], '（视口已因它触发过适配，先归位）');
  await restoreZoom();
  if (!await selectMine(vid[0])) throw new Error('没能选中空视频节点');
  await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = e.getBoundingClientRect();
    e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 12) })); }, vid[0]);
  await p.waitForTimeout(800);
  const vC1 = await vp();
  const r1 = await clickMenuItem('复制副本');
  console.log('  右键菜单逐字:', JSON.stringify(r1.menu));
  console.log('  点「复制副本」:', r1.hit ? '成功' : '❌ 失败');
  await p.waitForTimeout(1800);
  const dup1 = (await ids()).filter((x) => !c0.includes(x) && x !== vid[0]);
  const vC1b = await vp();
  console.log(`  副本: ${JSON.stringify(dup1)}（期望 1 个）`);
  console.log(`  缩放 ${vC1.scale} → ${vC1b.scale}  ${vC1.scale !== vC1b.scale ? '🔴 触发自动适配' : '❌ 未触发'}`);
  console.log(`  transform 变化: ${vC1.raw !== vC1b.raw ? '变了' : '逐字不变'}`);
  for (const d of dup1) CREATED.push(d);
  await reset();
  for (const d of dup1) console.log('  删副本', d, '→', await deleteById(d));
  await reset();
  console.log('  删原节点', vid[0], '→', await deleteById(vid[0]));
  CREATED.splice(CREATED.indexOf(vid[0]), 1);
  await restoreZoom();

  // ================= C2：复制一个「带内容图片节点」 =================
  console.log('\n########## C2 入口=复制副本，节点=带内容图片 ##########');
  await setTool('抓手工具');
  if (!await panTo(1700, 400)) throw new Error('平移失败');
  await setTool('选择工具');
  const c2 = await ids();
  const [chooser] = await Promise.all([p.waitForEvent('filechooser', { timeout: 15000 }), p.click('button[aria-label="上传"]')]);
  await chooser.setFiles(UPLOAD);
  await p.waitForTimeout(3400);
  const img = (await ids()).filter((x) => !c2.includes(x));
  if (img.length !== 1) throw new Error(`带内容图片节点新增 ${img.length} 个`);
  CREATED.push(img[0]);
  const imgs = await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); return e ? e.querySelectorAll('img').length : -1; }, img[0]);
  console.log(`  已建带内容图片节点 ${img[0]}，img 元素 ${imgs} 个 ${imgs > 0 ? '✅' : '❌'}`);
  await restoreZoom();
  if (!await selectMine(img[0])) throw new Error('没能选中带内容图片节点');
  await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = e.getBoundingClientRect();
    e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 12) })); }, img[0]);
  await p.waitForTimeout(800);
  const vC2 = await vp();
  const r2 = await clickMenuItem('复制副本');
  console.log('  点「复制副本」:', r2.hit ? '成功' : '❌ 失败');
  await p.waitForTimeout(1800);
  const dup2 = (await ids()).filter((x) => !c2.includes(x) && x !== img[0]);
  const vC2b = await vp();
  const dup2imgs = await p.evaluate((I) => I.map((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); return e ? e.querySelectorAll('img').length : -1; }), dup2);
  console.log(`  副本: ${JSON.stringify(dup2)}，各自 img 元素数 ${JSON.stringify(dup2imgs)}（复制是否带内容）`);
  console.log(`  缩放 ${vC2.scale} → ${vC2b.scale}  ${vC2.scale !== vC2b.scale ? '🔴 触发自动适配' : '❌ 未触发'}`);
  console.log(`  transform 变化: ${vC2.raw !== vC2b.raw ? '变了' : '逐字不变'}`);
  for (const d of dup2) CREATED.push(d);
  await reset();
  for (const d of dup2) console.log('  删副本', d, '→', await deleteById(d));
  await reset();
  console.log('  删原节点', img[0], '→', await deleteById(img[0]));
  CREATED.splice(CREATED.indexOf(img[0]), 1);
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
