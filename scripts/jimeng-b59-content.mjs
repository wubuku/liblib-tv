// 批次 59 补充轮：把「源节点**有无内容**」这个变量控住
//
// 主矩阵用**左栏新建的空节点**跑完 7×7，其中「从图片节点出发」那一行是
//   图片✅ 视频✅ 音频✅ / 时间线🔘加载中 / 主体🔘无就绪资源 / 文本🔘无法连接 / 导演台🔘无法连接
// 而手册现有的那张表写的是「从图片节点出发：**图片/视频/音频/时间线/主体 可用**」。
//
// ⚠️ 两者差了三项，但**不能直接判手册错** ——
//    手册那张表用的是**上传后带内容**的图片节点，本轮主矩阵用的是**空**图片节点。
//    批次 28 早就发现「有无资源」会改变原因文案（「加载中 / 没有就绪资源」都是临时态）。
//    这正是批次 50–55 反复栽的那个坑：**先问「我找的是不是同一个东西」**。
//
// 本轮只做一件事：同样的 7 项菜单，换成**带内容**的图片节点再量一次，
// 把「内容」这一个变量单独摘出来。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OUT = new URL('./_tmp-b59-content.json', import.meta.url);
const UPLOAD = '/tmp/b22-upload.png';   // 批次 22 已授权
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
const readMenu = () => p.evaluate(() => {
  const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
  if (!m) return null;
  const r = m.getBoundingClientRect();
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}`, title: (m.innerText || '').split('\n')[0] || '',
    items: Array.from(m.querySelectorAll('[role="menuitem"]')).map((e) => {
      const probe = e.querySelector('span,div') || e;
      const sr = Array.from(e.querySelectorAll('[class*="sr-only"]')).map((x) => (x.textContent || '').trim()).filter(Boolean);
      const lines = (e.innerText || '').split('\n').map((s) => s.trim()).filter(Boolean);
      return { title: lines[0] || '', why: [...lines.slice(1), ...sr].filter(Boolean)[0] || '',
        dis: e.getAttribute('aria-disabled') === 'true', color: getComputedStyle(probe).color }; }) };
});
const plusOf = (id) => p.evaluate((vid) => { const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return null;
  const g = (t) => { const e = n.querySelector(`[data-testid="${t}"]`); if (!e) return null; const r = e.getBoundingClientRect();
    return r.width > 1 ? { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) } : null; };
  return { before: g('flow-node-target-connection-menu-button'), after: g('flow-node-source-connection-menu-button'),
    imgs: n.querySelectorAll('img').length, aria: n.getAttribute('aria-label') }; }, id);
const deleteById = async (id) => {
  if (!(await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"]`), id))) return 'absent';
  await deselect();
  if (!(await selectByScan(id))) return 'notselected';
  await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return;
    const r = e.getBoundingClientRect();
    e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 14) })); }, id);
  await p.waitForTimeout(800);
  const ok = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop(); if (!m) return false;
    const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (!it) return false; it.click(); return true; });
  await p.waitForTimeout(1300); await reset(); return ok ? 'deleted' : 'noclick';
};

console.log('=== 批次 59 补充轮：带内容 vs 空 图片源 ===\n');
await deselect();
const pre = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const [chooser] = await Promise.all([p.waitForEvent('filechooser', { timeout: 15000 }), p.click('button[aria-label="上传"]')]);
await chooser.setFiles(UPLOAD);
await p.waitForTimeout(3600);
const made = (await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')))).filter((x) => !pre.includes(x));
console.log('上传后新增节点:', JSON.stringify(made));
const out = { startedAt: new Date().toISOString(), made, rows: {} };
if (made.length === 1) {
  MINE.push(made[0]);
  await deselect();
  console.log('选中:', await selectByScan(made[0]));
  const info = await plusOf(made[0]);
  console.log(`节点 aria=${JSON.stringify(info.aria)}  img 元素 ${info.imgs} 个  ⊕ before=${info.before ? '有' : '无'} after=${info.after ? '有' : '无'}`);
  if (info.after) { await p.mouse.click(info.after.x, info.after.y); await p.waitForTimeout(1000); }
  else if (info.before) { await p.mouse.click(info.before.x, info.before.y); await p.waitForTimeout(1000); }
  const menu = await readMenu();
  out.rows.withContent = menu;
  console.log(`\n带内容图片源 → 菜单 ${menu ? menu.box : '未打开'} 标题「${menu ? menu.title.trim() : ''}」`);
  if (menu) for (const it of menu.items) {
    console.log(`   ${it.dis ? '🔘' : '✅'} ${String(it.title).padEnd(6)} aria-disabled=${it.dis} color=${it.color.padEnd(24)} ${it.why || '—'}`);
  }
  await reset();
  console.log('\n删除:', await deleteById(made[0]));
}

// 对照：空图片源（主矩阵那一行）
{
  await deselect();
  const rb = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button')).find((x) => (x.getAttribute('aria-label') || '') === '图片');
    if (!e) return null; const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
  const p2 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
  await p.mouse.click(rb.cx, rb.cy); await p.waitForTimeout(2800);
  const m2 = (await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')))).filter((x) => !p2.includes(x));
  if (m2.length === 1) {
    MINE.push(m2[0]);
    await deselect(); await selectByScan(m2[0]);
    const info = await plusOf(m2[0]);
    if (info.after) { await p.mouse.click(info.after.x, info.after.y); await p.waitForTimeout(1000); }
    const menu = await readMenu();
    out.rows.empty = menu;
    console.log(`\n空图片源 → 菜单 ${menu ? menu.box : '未打开'}`);
    if (menu) for (const it of menu.items) console.log(`   ${it.dis ? '🔘' : '✅'} ${String(it.title).padEnd(6)} ${it.why || '—'}`);
    await reset();
    console.log('删除:', await deleteById(m2[0]));
  }
}

console.log('\n--- 收尾 ---');
await reset();
console.log('剩余待删:', JSON.stringify(MINE));
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
  console.log(`  ${id} ${JSON.stringify(c)} Δ=${JSON.stringify(bs ? [+(c[0] - bs.canvas[0]).toFixed(2), +(c[1] - bs.canvas[1]).toFixed(2)] : '?')}`); }
out.end = { zoom: await zoomOf(), coords: fin };
writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log('写入', OUT.pathname);
await b.close();
