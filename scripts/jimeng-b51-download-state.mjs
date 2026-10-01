// 批次 51：把「多选态『下载』禁用 + 附『没有可用的就绪资源』」这条**未能复现**的旧记录做实。
//
// 背景：批次 50 在**无媒体内容**的选中态下（3 文本 / 2 文本+空视频）两次实测，
// 「下载」按钮没有 aria-disabled、没有 data-disabled，全文档也搜不到「就绪资源」。
// 而 2026-10-01 那条旧记录选中的是**两个有内容的视频节点**。
// ⇒ 唯一说得通的解释：**禁用态由「选中集里有没有已就绪的媒体资源」决定**。
//
// 本批控制变量：唯一变量 = 选中集里**有没有一个带内容的图片节点**。
//   S1 单选带内容图片节点（节点工具条的下载）
//   S2 多选「带内容图片 + 文本」（多选工具条 batch-download）
//   S3 把这两个编成组（组工具条 download）
//
// ⚠️ 只**读**按钮的 DOM 状态，**绝不点「下载」**（会触发文件下载，不是只读观察）。
// ⚠️ 上传只用**已授权**的 /tmp/b22-upload.png（批次 22/48 已授权）。
// ⚠️ 前置条件必须自证：新节点必须真的**有内容**（有 <img>、读屏串不是 0 ready）。
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
const selIds = async () => real(await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id'))));
const groupIds = async () => real(await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group')).map((e) => e.getAttribute('data-id'))));
const vp = () => p.evaluate(() => { const v = document.querySelector('.react-flow__viewport'); const m = v && /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/.exec(v.style.transform); return m ? { tx: +m[1], ty: +m[2], scale: +m[3] } : null; });
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
const centerMine = async (myIds) => { for (let r = 0; r < 8; r++) {
  const u = await p.evaluate((I) => { const rs = I.map((id) => { const e = document.querySelector(`.react-flow__node[data-id="${id}"]`); return e ? e.getBoundingClientRect() : null; }).filter(Boolean);
    if (rs.length !== I.length) return null; const x0 = Math.min(...rs.map((r) => r.x)), x1 = Math.max(...rs.map((r) => r.right)), y0 = Math.min(...rs.map((r) => r.y)), y1 = Math.max(...rs.map((r) => r.bottom));
    return { cx: (x0 + x1) / 2, cy: (y0 + y1) / 2, rect: [Math.round(x0), Math.round(y0), Math.round(x1), Math.round(y1)] }; }, myIds);
  if (!u) return false; const dx = 640 - u.cx, dy = 480 - u.cy;
  if (Math.abs(dx) < 6 && Math.abs(dy) < 6) { console.log('    并集屏幕框', JSON.stringify(u.rect), '已居中'); return true; }
  const s = await findEmpty(); if (!s) return false; await drag(s, Math.max(-130, Math.min(130, dx)), Math.max(-130, Math.min(130, dy))); } return false; };
const deleteById = async (id) => { if (!(await ids()).includes(id)) return 'absent';
  const pt = await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 16) }; }, id);
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(650);
  if (await p.evaluate((v) => { const s = document.querySelector('.react-flow__node.selected'); return !s || s.getAttribute('data-id') !== v; }, id)) {
    await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = e.getBoundingClientRect();
      for (const t of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) e.dispatchEvent(new MouseEvent(t, { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 16) })); }, id);
    await p.waitForTimeout(650); }
  if (await p.evaluate((v) => { const s = document.querySelector('.react-flow__node.selected'); return !s || s.getAttribute('data-id') !== v; }, id)) return 'notselected';
  await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = e.getBoundingClientRect(); e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 12) })); }, id);
  await p.waitForTimeout(650);
  const ok = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop(); if (!m) return false;
    const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (!it) return false; it.click(); return true; });
  await p.waitForTimeout(1200); return ok ? 'deleted' : 'noclick'; };

// 🔑 工具条里找按钮：**aria-label 或 innerText 逐字都要认**。
//    实测（批次 51）：多选工具条的「编组」「布局」「Add tags」**没有 aria-label**，
//    只有 innerText；只按 aria-label 找会返回 null，而且工具条明明就在那儿。
const findItem = (name) => p.evaluate((n) => {
  const bars = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).filter((e) => e.getBoundingClientRect().width > 1);
  for (const bar of bars) {
    for (const e of bar.querySelectorAll('button,[role="button"]')) {
      const al = e.getAttribute('aria-label');
      const tx = (e.innerText || '').trim();
      if (al === n || tx === n) { const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), viaAria: al === n }; }
    }
  }
  return null;
}, name);

// 🔑 按 data-id 精确点中某个节点：先在节点矩形内网格扫描，找**顶层元素确实属于该节点**的
//    落点（重叠节点上直接点中心会命中上层 —— 批次 39/48 的事故根因），找不到再退回
//    在目标元素上直接派发完整指针序列。点完必须断言选中集合。
const clickNodeById = async (id) => {
  const pt = await p.evaluate((v) => {
    const e = document.querySelector(`.react-flow__node[data-id="${v}"]`);
    if (!e) return null;
    const r = e.getBoundingClientRect();
    for (let fy = 0.1; fy <= 0.9; fy += 0.08) {
      for (let fx = 0.1; fx <= 0.9; fx += 0.08) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        const el = document.elementFromPoint(x, y);
        const node = el && el.closest('.react-flow__node');
        if (node && node.getAttribute('data-id') === v) return { x, y, via: 'elementFromPoint' };
      }
    }
    return null;
  }, id);
  if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(900); }
  if (!(await selIds()).includes(id)) {
    await p.evaluate((v) => { const e = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!e) return; const r = e.getBoundingClientRect();
      for (const t of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) e.dispatchEvent(new MouseEvent(t, { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 16) })); }, id);
    await p.waitForTimeout(900);
  }
  const sel = await selIds();
  console.log(`    点中 ${id}：落点 ${JSON.stringify(pt)}，选中 ${JSON.stringify(sel)} ${sel.length === 1 && sel[0] === id ? '✅' : '❌'}`);
  return sel.length === 1 && sel[0] === id;
};

// 🔑 读「下载」项的真实状态：aria / data / class / 文案 / 全文档副文案搜索
const probeDownload = (label) => p.evaluate((lb) => {
  const bars = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).filter((e) => e.getBoundingClientRect().width > 1);
  const res = { label: lb, bars: [] };
  for (const bar of bars) {
    const items = Array.from(bar.querySelectorAll('button,[role="button"]'));
    const dl = items.find((e) => e.getAttribute('aria-label') === '下载');
    if (!dl) continue;
    const r = dl.getBoundingClientRect();
    res.bars.push({
      barSize: `${Math.round(bar.getBoundingClientRect().width)}x${Math.round(bar.getBoundingClientRect().height)}`,
      value: dl.getAttribute('data-toolbar-value'),
      ariaDisabled: dl.getAttribute('aria-disabled'),
      disabledAttr: dl.hasAttribute('disabled') ? 'true' : null,
      dataDisabled: dl.getAttribute('data-disabled'),
      title: dl.getAttribute('title'),
      innerText: (dl.innerText || '').replace(/\n/g, ' ⏎ ').trim().slice(0, 60),
      opacity: getComputedStyle(dl).opacity,
      pointerEvents: getComputedStyle(dl).pointerEvents,
      cursor: getComputedStyle(dl).cursor,
      cls: String(dl.className).slice(0, 400),
      svgCount: dl.querySelectorAll('svg').length,
      size: `${Math.round(r.width)}x${Math.round(r.height)}`,
    });
  }
  // 全文档搜「原因副文案」
  const hits = [];
  for (const e of document.querySelectorAll('div,span,p,button,li,label,td')) {
    if (e.children.length) continue;
    const t = (e.textContent || '').trim();
    if (t && /就绪|没有可用|未就绪|不可用/.test(t)) hits.push(t.slice(0, 48));
    if (hits.length >= 6) break;
  }
  res.reasonHits = hits;
  res.itemNames = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).filter((e) => e.getBoundingClientRect().width > 1)
    .map((bar) => Array.from(bar.querySelectorAll('button,[role="button"]')).map((e) => e.getAttribute('aria-label') || (e.innerText || '').trim().slice(0, 6)));
  return res;
}, label);

// ---- 起点 ----
await reset();
const bad0 = await diffNodePositions(p, BASELINE.nodes, 1.5);
if (bad0.length || (await ids()).length !== 6) { console.error('ABORT: 起点与基线不一致', JSON.stringify(bad0)); await b.close(); process.exit(2); }
console.log('起点与基线一致 ✅  6 节点、canvas 位置逐项对齐');
console.log('焦点守卫:', (await keyGuard(p)).where);
const credit0 = (await canvasBaseline(p)).credit;

const CREATED = [];
try {
  // ---- ① 上传一张已授权 PNG，造出「有内容」的图片节点 ----
  console.log('\n########## ① 造出前置条件：带内容的图片节点 ##########');
  await setTool('抓手工具');
  const panned = await panTo(1700, 400);
  await setTool('选择工具');
  if (!panned) throw new Error('平移失败');
  const before = await ids();
  const vBefore = await vp();
  const [chooser] = await Promise.all([
    p.waitForEvent('filechooser', { timeout: 15000 }),
    p.click('button[aria-label="上传"]'),
  ]);
  await chooser.setFiles(UPLOAD);
  console.log('  已选文件:', UPLOAD);
  await p.waitForTimeout(3200);
  const fresh = (await ids()).filter((x) => !before.includes(x));
  if (fresh.length !== 1) throw new Error(`上传后新增节点 ${fresh.length} 个，期望 1`);
  const imgId = fresh[0];
  CREATED.push(imgId);
  const vAfter = await vp();
  console.log(`  新节点 ${imgId}；视口 ${JSON.stringify(vBefore)} → ${JSON.stringify(vAfter)}`, vBefore && vAfter && vBefore.scale !== vAfter.scale ? '🔴 自动适配改了缩放' : '缩放未变');
  // 🔑 前置条件自证：真的有内容吗？
  const pre = await p.evaluate((v) => {
    const e = document.querySelector(`.react-flow__node[data-id="${v}"]`);
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), cls: String(e.className),
      img: e.querySelectorAll('img').length,
      imgSrc: (e.querySelector('img') || {}).src ? String(e.querySelector('img').src).slice(0, 60) : null,
      video: e.querySelectorAll('video').length,
      canvas: e.querySelectorAll('canvas').length,
      bgImage: (() => { const c = e.querySelector('[style*="background-image"]'); return c ? String(getComputedStyle(c).backgroundImage).slice(0, 60) : null; })(),
      text: (e.innerText || '').split('\n').filter(Boolean).slice(0, 4),
      size: [Math.round(r.width), Math.round(r.height)] };
  }, imgId);
  console.log('  前置条件自证:', JSON.stringify(pre, null, 1));
  const hasContent = pre && (pre.img > 0 || pre.video > 0 || pre.canvas > 0 || pre.bgImage);
  console.log(`  ⇒ 节点是否真的带媒体内容：${hasContent ? '✅ 是' : '❌ 否'}  —— 没这一步，后面的读数都不算数`);

  // ---- ② 顺带建一个文本节点，用于「多选」对照 ----
  const tBefore = await ids();
  await p.evaluate(() => { const t = Array.from(document.querySelectorAll('button,[role="button"]')).find((e) => e.getAttribute('aria-label') === '文本'); if (t) t.click(); });
  await p.waitForTimeout(1700);
  const tf = (await ids()).filter((x) => !tBefore.includes(x));
  if (tf.length !== 1) throw new Error(`建文本节点异常 ${tf.length}`);
  const txtId = tf[0];
  CREATED.push(txtId);
  console.log(`  文本节点 ${txtId}`);
  await reset();
  await setTool('抓手工具');
  if (!await centerMine([imgId, txtId])) throw new Error('居中失败');
  await setTool('选择工具');
  console.log('  视口内可见的他人节点:', (await p.evaluate((I) => I.filter((id) => { const e = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!e) return false; const r = e.getBoundingClientRect(); return r.right > 0 && r.bottom > 0 && r.left < innerWidth && r.top < innerHeight; }), OTHERS)).join(',') || '（无）');

  // ---- S1：单选带内容的图片节点 ----
  console.log('\n########## S1 单选「带内容图片节点」##########');
  if (!await clickNodeById(imgId)) throw new Error('S1 未能精确选中图片节点');
  const s1toolbar = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).filter((e) => e.getBoundingClientRect().width > 1).map((bar) => Array.from(bar.querySelectorAll('button,[role="button"]')).map((e) => e.getAttribute('aria-label'))));
  console.log('  当前工具条逐字:', JSON.stringify(s1toolbar));
  console.log('  S1 读数:', JSON.stringify(await probeDownload('S1 单选带内容图片'), null, 1));

  // ---- S2：框选「图片 + 文本」多选 ----
  console.log('\n########## S2 多选「带内容图片 + 文本」##########');
  await reset();
  const mine = await p.evaluate((I) => I.map((id) => { const r = document.querySelector(`.react-flow__node[data-id="${id}"]`).getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; }), [imgId, txtId]);
  const others = await p.evaluate((I) => I.map((id) => { const e = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!e) return null; const r = e.getBoundingClientRect(); return { id, x: r.x, y: r.y, w: r.width, h: r.height }; }).filter(Boolean), OTHERS);
  const sx = Math.round(Math.min(...mine.map((m) => m.x)) - 28), sy = Math.round(Math.min(...mine.map((m) => m.y)) - 28);
  const ex = Math.round(Math.max(...mine.map((m) => m.x + m.w)) + 24), ey = Math.round(Math.max(...mine.map((m) => m.y + m.h)) + 24);
  const hit = others.filter((o) => o.x < ex && o.x + o.w > sx && o.y < ey && o.y + o.h > sy);
  console.log(`  框选矩形 (${sx},${sy})-(${ex},${ey})，与他人节点相交 ${hit.length} 个`);
  if (hit.length) throw new Error('框选矩形与他人节点相交，中止');
  if ((await selIds()).length) throw new Error('框选前已有选中');
  await p.mouse.move(sx, sy); await p.mouse.down();
  for (let i = 1; i <= 10; i++) { await p.mouse.move(sx + ((ex - sx) * i) / 10, sy + ((ey - sy) * i) / 10); await p.waitForTimeout(55); }
  await p.mouse.up(); await p.waitForTimeout(800);
  const post = (await selIds()).sort(), want = [imgId, txtId].sort();
  const ok = post.length === want.length && post.every((v, i) => v === want[i]);
  console.log('  框选结果:', post.join(','), ok ? '✅ 与目标完全一致' : '❌ 不一致');
  if (!ok) throw new Error('选中集合不符');
  console.log('  S2 读数:', JSON.stringify(await probeDownload('S2 多选 带内容图片+文本'), null, 1));

  // ---- S3：编组后的组工具条 ----
  console.log('\n########## S3 把这两个编成组 ##########');
  const dump = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).map((bar) => { const r = bar.getBoundingClientRect();
    return { w: Math.round(r.width), h: Math.round(r.height), items: Array.from(bar.querySelectorAll('button,[role="button"]')).map((e) => ({ aria: e.getAttribute('aria-label'), txt: (e.innerText || '').trim().slice(0, 6), v: e.getAttribute('data-toolbar-value') })) }; }));
  console.log('    多选工具条逐项（aria / 文案 / value）:', JSON.stringify(dump));
  const gb = await findItem('编组');
  console.log('    「编组」定位:', JSON.stringify(gb));
  if (!gb) throw new Error('没有编组项');
  const g0 = (await groupIds()).length;
  await p.mouse.click(gb.cx, gb.cy); await p.waitForTimeout(1200);
  const gid = (await groupIds())[0];
  console.log(`  编组后真组数 ${g0} → ${(await groupIds()).length}，节点总数 ${(await ids()).length}`);
  if (!gid) throw new Error('编组失败');
  await reset();
  const gpt = await p.evaluate((v) => { const g = document.querySelector(`.react-flow__node-group[data-id="${v}"]`); const r = g.getBoundingClientRect(); const cx = Math.round(r.x + r.width / 2);
    for (let y = Math.round(r.y + 2); y <= Math.round(r.y + 40); y += 2) { const el = document.elementFromPoint(cx, y); if (el && el.closest(`.react-flow__node-group[data-id="${v}"]`)) return { x: cx, y }; } return null; }, gid);
  await p.mouse.click(gpt.x, gpt.y); await p.waitForTimeout(1000);
  console.log('  选中组:', (await selIds()).includes(gid) ? '✅' : '❌', JSON.stringify(await selIds()));
  console.log('  S3 读数:', JSON.stringify(await probeDownload('S3 组：带内容图片+文本'), null, 1));
  // 解除编组
  const un = await findItem('解除编组');
  if (un) { await p.mouse.click(un.cx, un.cy); await p.waitForTimeout(1200); } else console.log('    ❌ 找不到「解除编组」');
  console.log('  解除编组后真组数:', (await groupIds()).length);
} catch (e) {
  console.error('ABORT:', e.message);
}

// ---- 收尾 ----
await reset();
for (const id of CREATED) console.log('  删', id, '→', await deleteById(id));
await reset();
await setTool('选择工具');
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
const fin = await canvasBaseline(p);
const bad = await diffNodePositions(p, BASELINE.nodes, 1.5);
const g = await keyGuard(p);
console.log('\n=== 收尾核对 ===');
console.log(' 焦点守卫:', g.safe ? '✅' : g.where, '| 节点数', fin.nodes.length, '| 真组数', (await groupIds()).length);
console.log(' 状态行:', fin.status, '| 积分', fin.credit, '(起始', credit0 + ')');
const stillIds = await ids();
const left = CREATED.filter((x) => stillIds.includes(x));
console.log(' 位置偏离:', bad.length, bad.length ? bad.join(',') : '✅ 0', '| 剩余待删:', JSON.stringify(left));
await b.close();
