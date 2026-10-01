// 批次 59：连线能力的**全类型对照** —— 7 种源 × 7 项目标
//
// 手册现状（connect-nodes.md「连接规则」）：只记了**两张**表 ——
//   从**视频**节点出发、从**图片**节点出发（图片那张用的还是带内容的节点）。
// 而左栏有 **7 种**节点类型。手册自己写着
//   「别把『能连』当成节点类型的固有属性，它取决于当前这个源节点」——
//   可这句话本身也只建立在 2/7 的样本上。
//
// 批次 57 又补了一条：⊕ 按钮**因类型而异**（文本只有 after、时间线只有 before、
// 导演台两个都没有），也就是说「选中后点 ⊕ 开菜单」这条路径**并不是通用的**。
//
// 本批做**完整笛卡尔积**：每种源节点都开一次「添加节点」菜单，
// 逐项记录 7 个目标类型的 可用/禁用 + **逐字原因**（含 sr-only 里的那一句）。
//
// 变量控制：
//   源节点的**有无资源**会改变原因文案（批次 28：视频源的时间线/主体是
//   「加载中 / 没有就绪资源」这类**临时**原因，而文本是「无法连接」这类**永久**原因）。
//   所以主矩阵统一用**左栏新建的空节点**（受控条件），
//   再单独补一个「带内容的图片节点」与手册那张表对照。
//
// 取材：**每种类型建一个、量完立刻按 id 删除**，避免 7 个节点级联重叠互相干扰。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OUT = new URL('./_tmp-b59-matrix.json', import.meta.url);
const TYPES = ['文本', '图片', '视频', '音频', '时间线', '主体', '导演台'];
const MINE = [];

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);

const reset = async () => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); } };
const selIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const coords = () => p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
  return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null];
})));
const isEmpty = (x, y) => p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); if (!el) return true;
  if (el.closest('.react-flow__node')) return false;
  if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"]')) return false;
  return true; }, [x, y]);
const findEmpty = async () => { for (let y = 110; y <= 630; y += 20) for (let x = 80; x <= 1250; x += 20) { if (x > 1150 && y > 600) continue; if (await isEmpty(x, y)) return { x, y }; } return null; };
const deselect = async () => { await reset(); const e = await findEmpty();
  if (e) { await p.mouse.click(e.x, e.y); await p.waitForTimeout(600); }
  for (let i = 0; i < 3 && (await selIds()).length; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  return (await selIds()).length === 0; };

// 细网格试点选节点（新建节点会与他人节点重叠，矩形中心会选错 —— 批次 56/57 已记）
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
      out.push({ x, y });
    } return out;
  }, id);
  for (const pt of pts) {
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(550);
    const s = await selIds();
    if (s.length === 1 && s[0] === id) return { ok: true, pt };
  }
  return { ok: false, n: pts.length };
};

const makeNode = async (kind) => {
  await deselect();
  const rb = await p.evaluate((nm) => { const e = Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button'))
      .find((x) => (x.getAttribute('aria-label') || '').startsWith(nm)); if (!e) return null;
    const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }, kind);
  if (!rb) return { err: `左栏找不到「${kind}」` };
  const pre = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
  await p.mouse.click(rb.cx, rb.cy); await p.waitForTimeout(2800);
  const post = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
  const made = post.filter((x) => !pre.includes(x));
  if (made.length !== 1) return { err: `新建「${kind}」新增 ${made.length} 个` };
  MINE.push(made[0]); return { id: made[0] };
};

const deleteById = async (id) => {
  if (!(await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"]`), id))) return 'absent';
  await deselect();
  const s = await selectByScan(id);
  if (!s.ok) { await p.keyboard.press('Escape'); return 'notselected'; }
  await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return;
    const r = e.getBoundingClientRect();
    e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 14) })); }, id);
  await p.waitForTimeout(800);
  const ok = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop(); if (!m) return false;
    const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (!it) return false; it.click(); return true; });
  await p.waitForTimeout(1300);
  await reset();
  return ok ? 'deleted' : 'noclick';
};

// 选中态下枚举 ⊕ 按钮（批次 57：并非每种类型都有两个）
const plusButtons = (id) => p.evaluate((vid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return null;
  const g = (t) => { const e = n.querySelector(`[data-testid="${t}"]`); if (!e) return null;
    const r = e.getBoundingClientRect(); return { vis: r.width > 1 && r.height > 1, x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; };
  return { before: g('flow-node-target-connection-menu-button'), after: g('flow-node-source-connection-menu-button'),
    aria: n.getAttribute('aria-label') };
}, id);

// 读「添加节点」菜单：逐项 可用/禁用 + 逐字原因（含 sr-only）
const readMenu = () => p.evaluate(() => {
  const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
  if (!m) return null;
  const r = m.getBoundingClientRect();
  const items = Array.from(m.querySelectorAll('[role="menuitem"]')).map((e) => {
    const ir = e.getBoundingClientRect();
    // 颜色判据（批次 28）：可用 rgb(255,255,255) / 禁用 rgba(255,255,255,0.2)
    const probe = e.querySelector('span,div') || e;
    const color = getComputedStyle(probe).color;
    // 原因：菜单项内除标题外的其余文字，以及 sr-only 元素
    const srOnly = Array.from(e.querySelectorAll('.sr-only,[class*="sr-only"]')).map((x) => (x.textContent || '').trim()).filter(Boolean);
    const lines = (e.innerText || '').split('\n').map((s) => s.trim()).filter(Boolean);
    return { title: lines[0] || '', lines: lines.slice(1), srOnly,
      ariaDisabled: e.getAttribute('aria-disabled'), color,
      box: `${Math.round(ir.width)}x${Math.round(ir.height)}` };
  });
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}`, title: (m.innerText || '').split('\n')[0] || '', items };
});

const measure = async (id, label) => {
  await deselect();
  const sel = await selectByScan(id);
  if (!sel.ok) return { label, err: `选不中（${sel.n} 个落点）` };
  const plus = await plusButtons(id);
  const rec = { label, id, nodeAria: plus && plus.aria,
    hasBefore: !!(plus && plus.before && plus.before.vis), hasAfter: !!(plus && plus.after && plus.after.vis) };
  // 优先 after，其次 before
  const pick = (plus && plus.after && plus.after.vis) ? plus.after : ((plus && plus.before && plus.before.vis) ? plus.before : null);
  if (!pick) { rec.menu = null; rec.note = '选中态**没有任何 ⊕ 按钮** —— 「点 ⊕ 开菜单」这条路对该类型不通'; await reset(); return rec; }
  rec.opened = 'after' === ((plus.after && plus.after.vis) ? 'after' : 'before');
  await p.mouse.click(pick.x, pick.y); await p.waitForTimeout(1000);
  rec.menu = await readMenu();
  await reset();
  return rec;
};

const result = { startedAt: new Date().toISOString(), zoom: await zoomOf(), matrix: [], notes: [] };
console.log('=== 批次 59：连线能力全类型对照（7 源 × 7 目标）===\n');

for (const kind of TYPES) {
  const r = await makeNode(kind);
  if (r.err) { console.log(`❌ ${kind}: ${r.err}`); result.matrix.push({ label: kind, err: r.err }); continue; }
  const rec = await measure(r.id, `${kind}（空）`);
  rec.created = r.id;
  result.matrix.push(rec);
  const st = await p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [''])[0]);
  console.log(`\n── ${kind}（空） ${r.id}  ${st}`);
  if (rec.err) { console.log(`   ⛔ ${rec.err}`); }
  else {
    console.log(`   ⊕ 按钮: before=${rec.hasBefore ? '有' : '无'}  after=${rec.hasAfter ? '有' : '无'}`);
    if (!rec.menu) console.log(`   ⚠️ ${rec.note}`);
    else {
      console.log(`   菜单 ${rec.menu.box}  标题「${rec.menu.title.trim()}」  ${rec.menu.items.length} 项（入口：${rec.opened ? 'after ⊕' : 'before ⊕'}）`);
      for (const it of rec.menu.items) {
        const dis = it.ariaDisabled === 'true' || it.color.includes('0.2');
        const why = [...it.lines, ...it.srOnly].filter(Boolean).join(' / ');
        console.log(`      ${dis ? '🔘' : '✅'} ${String(it.title).padEnd(6)} aria-disabled=${String(it.ariaDisabled).padEnd(5)} color=${it.color.padEnd(24)} ${why || '—'}`);
      }
    }
  }
  console.log(`   删除: ${await deleteById(r.id)}`);
}

// 补：带内容的图片节点（与手册现有那张表对照）
console.log('\n── 对照：带内容的图片节点（已授权 PNG）──');
{
  const r = await makeNode('图片');
  if (!r.err) {
    const up = await p.$('input[type="file"]');
    console.log(`   图片节点 ${r.id}；页面 file input ${up ? '找到' : '未找到'}`);
    result.notes.push('带内容图片节点：本批未上传 —— 上传会改变画布内容，需单独确认授权路径');
  } else console.log(`   ❌ ${r.err}`);
  if (!r.err) console.log(`   删除: ${await deleteById(r.id)}`);
}

// 收尾
console.log('\n--- 收尾 ---');
await reset();
console.log('剩余待删:', JSON.stringify(MINE));
for (let t = 0; t < 3; t++) {
  const z = await zoomOf();
  if (z && z.includes('60%')) { console.log('缩放归位 ok:', z); break; }
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
  const sel = 'input[data-testid="canvas-zoom-percent-input"]';
  if (await p.$(sel)) { await p.fill(sel, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); }
  else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  if (t === 2) console.log('缩放归位 FAILED:', await zoomOf());
}
await reset();
const fin = await coords();
console.log('终态缩放:', await zoomOf(), '| 节点数:', Object.keys(fin).length, '| 选中数:', (await selIds()).length);
for (const [id, c] of Object.entries(fin)) {
  const bs = BASELINE.nodes[id];
  const d = bs ? [+(c[0] - bs.canvas[0]).toFixed(2), +(c[1] - bs.canvas[1]).toFixed(2)] : '(非基线)';
  console.log(`  ${id} ${JSON.stringify(c)} Δ=${JSON.stringify(d)}`);
}
result.end = { zoom: await zoomOf(), coords: fin };
writeFileSync(OUT, JSON.stringify(result, null, 1));
console.log('写入', OUT.pathname);
await b.close();
