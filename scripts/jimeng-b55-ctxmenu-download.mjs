// 批次 55：右键菜单里的「下载」—— 老记录「没有可用的就绪资源」最可能的出处
//
// 线索：批次 54 在空视频节点的右键菜单里读到 `下载` 项 `aria-disabled="true"`，
// 而**工具条**上的下载不是禁用态 —— 两者不是同一个按钮。
// 老记录说的「多选态的下载是禁用的、附『没有可用的就绪资源』」，
// 最可能说的就是**菜单里这一个**。
//
// 同一菜单里还有一个**已知阳性对照**：手动记过「重做 ⌘⇧Z（禁用态附『无需重做操作』）」。
// 拿它当尺子，就能看清「禁用 + 原因副文案」在菜单项里到底长什么样。
//
// 控制变量：节点的媒体内容
//   M1 空视频节点   → 菜单七项（含禁用的 下载 / 重做）
//   M2 带内容图片节点 → 菜单九项（批次 40 记过图片节点多「复制为图片」「保存到主体库」）
//
// 全程只读：只打开右键菜单读 DOM，**不点任何菜单项**（删除/下载/保存都不点）。
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
const panTo = async (CX, CY) => { for (let r = 0; r < 20; r++) {
  const v = await p.evaluate(() => { const e = document.querySelector('.react-flow__viewport'); const m = e && /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/.exec(e.style.transform); return m ? { tx: +m[1], ty: +m[2], scale: +m[3] } : null; });
  if (!v) return false;
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
// 🔑 菜单逐项的完整状态（含 outerHTML 片段，用来看清「原因副文案」住在哪）
const dumpMenu = (label) => p.evaluate((lb) => {
  const menus = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1);
  const m = menus.pop();
  if (!m) return { label: lb, open: false };
  const r = m.getBoundingClientRect();
  const items = Array.from(m.querySelectorAll('[role="menuitem"]')).map((e) => {
    const rr = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return { name: (e.innerText || '').trim().split('\n')[0],
      full: (e.innerText || '').replace(/\n/g, ' ⏎ ').trim(),
      ariaDisabled: e.getAttribute('aria-disabled'), dataDisabled: e.getAttribute('data-disabled'),
      cursor: cs.cursor, opacity: cs.opacity, color: cs.color,
      rect: [rr.x, rr.y, rr.width, rr.height].map(Math.round),
      childTexts: Array.from(e.querySelectorAll('*')).map((c) => (c.textContent || '').trim()).filter((t) => t && t !== (e.innerText || '').trim().split('\n')[0]).slice(0, 4),
      html: e.innerHTML.slice(0, 300) };
  });
  return { label: lb, open: true, menuRect: [r.x, r.y, r.width, r.height].map(Math.round), items,
    menuText: (m.innerText || '').replace(/\n+/g, ' | ') };
}, label);

const CREATED = [];
try {
  await reset();
  const bad0 = await diffNodePositions(p, BASELINE.nodes, 1.5);
  if (bad0.length || (await ids()).length !== 6) throw new Error('起点与基线不一致');
  console.log('起点与基线一致 ✅');
  await restoreZoom();

  // ---- M1：空视频节点 ----
  console.log('\n########## M1 空视频节点 的右键菜单 ##########');
  await setTool('抓手工具');
  if (!await panTo(1700, 400)) throw new Error('平移失败');
  await setTool('选择工具');
  const m1 = await ids();
  await p.evaluate(() => { const t = Array.from(document.querySelectorAll('button,[role="button"]')).find((e) => e.getAttribute('aria-label') === '视频'); if (t) t.click(); });
  await p.waitForTimeout(2000);
  const vid = (await ids()).filter((x) => !m1.includes(x));
  if (vid.length !== 1) throw new Error('空视频节点未建成');
  CREATED.push(vid[0]);
  await restoreZoom();
  await p.mouse.move(200, 200); await p.waitForTimeout(300);
  await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = e.getBoundingClientRect();
    e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 14) })); }, vid[0]);
  await p.waitForTimeout(1000);
  const d1 = await dumpMenu('M1 空视频节点');
  console.log('  菜单', JSON.stringify(d1.menuRect), '项数', d1.items.length);
  for (const it of d1.items) console.log(`    ${it.name}  aria-disabled=${JSON.stringify(it.ariaDisabled)} cursor=${it.cursor} 尺寸=${it.rect[2]}×${it.rect[3]} 全文=${JSON.stringify(it.full)} 子文本=${JSON.stringify(it.childTexts)}`);
  console.log('  菜单全文:', JSON.stringify(d1.menuText));
  const dl1 = d1.items.find((i) => i.name === '下载');
  console.log('\n  🔑 菜单「下载」outerHTML:', JSON.stringify(dl1 && dl1.html));
  const redo1 = d1.items.find((i) => i.name === '重做');
  console.log('  🔑 阳性对照「重做」outerHTML:', JSON.stringify(redo1 && redo1.html));
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  await reset();
  console.log('  删', vid[0], '→', await deleteById(vid[0]));
  CREATED.splice(CREATED.indexOf(vid[0]), 1);
  await restoreZoom();

  // ---- M2：带内容图片节点 ----
  console.log('\n########## M2 带内容图片节点 的右键菜单 ##########');
  await setTool('抓手工具');
  if (!await panTo(1700, 400)) throw new Error('平移失败');
  await setTool('选择工具');
  const m2 = await ids();
  const [chooser] = await Promise.all([p.waitForEvent('filechooser', { timeout: 15000 }), p.click('button[aria-label="上传"]')]);
  await chooser.setFiles(UPLOAD);
  await p.waitForTimeout(3400);
  const img = (await ids()).filter((x) => !m2.includes(x));
  if (img.length !== 1) throw new Error('带内容图片节点未建成');
  CREATED.push(img[0]);
  const imgs = await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); return e ? e.querySelectorAll('img').length : -1; }, img[0]);
  console.log('  前置条件自证 img 元素', imgs, '个', imgs > 0 ? '✅' : '❌');
  await restoreZoom();
  await p.mouse.move(200, 200); await p.waitForTimeout(300);
  await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = e.getBoundingClientRect();
    e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 14) })); }, img[0]);
  await p.waitForTimeout(1000);
  const d2 = await dumpMenu('M2 带内容图片节点');
  console.log('  菜单', JSON.stringify(d2.menuRect), '项数', d2.items.length);
  for (const it of d2.items) console.log(`    ${it.name}  aria-disabled=${JSON.stringify(it.ariaDisabled)} cursor=${it.cursor} 尺寸=${it.rect[2]}×${it.rect[3]} 全文=${JSON.stringify(it.full)}`);
  console.log('  菜单全文:', JSON.stringify(d2.menuText));
  const dl2 = d2.items.find((i) => i.name === '下载');
  console.log('\n  🔑 菜单「下载」outerHTML:', JSON.stringify(dl2 && dl2.html));
  console.log(`\n  ⇒ A/B 对照：空节点「下载」aria-disabled=${JSON.stringify(dl1 && dl1.ariaDisabled)} ／ 带内容「下载」aria-disabled=${JSON.stringify(dl2 && dl2.ariaDisabled)}`);
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  await reset();
  console.log('  删', img[0], '→', await deleteById(img[0]));
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
