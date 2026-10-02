// 批次 96 · c 轮：🔑 **抓手态对「点节点」的影响** —— 本页最大的缺口。
//
// `navigate-canvas.md` 第 26–44 行是**专门讲抓手工具的一节**，但**一个字都没提**：
//   批次 90 已经钉死的三条 ——
//     ① 抓手态下**单击、双击节点都不选中**
//     ② dock **只有一个** `canvas-pointer-tool-toggle` 钮，aria 在 `选择工具`/`抓手工具` 间**翻**
//     ③ **V 键不切工具**，退出抓手态的**唯一路径**就是点它
//   读者读完这一页切到抓手、然后发现节点点不中，只会以为画布坏了。
//   这正是批次 90 立的规矩的靶子：「踩过的坑要搬到读者会去的那一页」。
//
// 本轮做**八格受控对照**，每格都回读 `selected` / `aria` / `pressed` 三样，
// 不符合前置就照实记，不猜。其中第 ⑩ 格是批次 90 **没测过**的：抓手态下**dock 的其它按钮还能不能点** ——
// 这是读者切到抓手之后立刻会做的事（想看小地图、想缩放）。
//
// 🔴 严格约束：不点左栏任何创建入口（会建节点）、不点任何扣费按钮；
//    dock 上只碰**只读开关**（小地图/显示连线/缩放值），且**点两次复原**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), cells: [] };
let TID = 'node_3bfb9r79qe';   // 锁定的被测节点；点不到时可换

const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const nodeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomLabel = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return e ? { aria: e.getAttribute('aria-label'), text: e.innerText.trim() } : null; });
const scaleNow = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });

const read = (label) => p.evaluate((l) => {
  const n = document.querySelector(`.react-flow__node[data-id="${l.id}"]`);
  const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  const mm = document.querySelector('[data-testid="canvas-display-toggle-minimap"]');
  const cn = document.querySelector('[data-testid="canvas-display-toggle-connections"]');
  const zb = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return { label: l.label, sel: document.body.innerText.match(/(\d+) selected/)?.[1] ?? '0',
    selectedIds: Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')),
    targetSelected: n ? n.classList.contains('selected') : null,
    targetPresent: !!n,
    editable: document.querySelectorAll('[contenteditable="true"],.ProseMirror').length,
    pointer: { count: document.querySelectorAll('[data-testid="canvas-pointer-tool-toggle"]').length,
      aria: t ? t.getAttribute('aria-label') : null, pressed: t ? t.getAttribute('aria-pressed') : null },
    minimap: { pressed: mm ? mm.getAttribute('aria-pressed') : null, panel: document.querySelectorAll('[data-testid="canvas-minimap-surface"]').length },
    connections: { pressed: cn ? cn.getAttribute('aria-pressed') : null },
    zoomMenuOpen: document.querySelectorAll('[data-testid="canvas-zoom-menu"]').length,
    zoomBtnText: zb ? zb.innerText.trim() : null,
    ctxMenuOpen: !!document.querySelector('[data-testid="canvas-context-menu"]') };
}, { label, id: TID });
const cell = async (label) => { const c = await read(label); out.cells.push(c);
  log(`${label}: sel=${c.sel} 目标选中=${c.targetSelected} 抓手=${c.pointer.aria}(${c.pointer.pressed}) ` +
      `小地图=${c.minimap.pressed}/${c.minimap.panel} 连线=${c.connections.pressed} 缩放菜单=${c.zoomMenuOpen} 右键菜单=${c.ctxMenuOpen}`);
  return c; };

// 🔴 **点击前 0ms 重算落点**：共享画布上别的会话一直在加节点，React Flow 会重排。
//    上一轮 ② 的失败就是这个 —— 落点是几百毫秒前算的，点下去时那里已经不是同一个节点了。
//    处置：**点之前**再校验一次归属，**点之后**立刻回读 `elementFromPoint` 作回执。
const clickAndVerify = async (id, why) => {
  const pt0 = await pointAt(id);
  if (!pt0) return { ok: false, why: '点之前就找不到落点' };
  const topBefore = await p.evaluate((c) => { const e = document.elementFromPoint(c.x, c.y);
    const o = e && e.closest('.react-flow__node');
    return { owner: o ? o.getAttribute('data-id') : null, tag: e ? e.tagName : null }; }, pt0);
  await p.mouse.move(pt0.x, pt0.y);
  await p.waitForTimeout(150);
  await p.mouse.click(pt0.x, pt0.y);
  const topAfter = await p.evaluate((c) => { const e = document.elementFromPoint(c.x, c.y);
    const o = e && e.closest('.react-flow__node');
    return { owner: o ? o.getAttribute('data-id') : null }; }, pt0);
  return { ok: topBefore.owner === id, pt: pt0, topBefore, topAfter, why };
};

const pointAt = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  for (const f of [0.5, 0.3, 0.7, 0.2, 0.8, 0.1, 0.9]) {
    const x = Math.round(r.x + r.width * f), y = Math.round(r.y + r.height * f);
    if (x < 2 || y < 2 || x > 1278 || y > 718) continue;
    if (document.elementFromPoint(x, y)?.closest('.react-flow__node') === n) return { x, y };
  }
  return null;
}, id);

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow() };
log('起点：', JSON.stringify(out.start));

// 归位 ①：Esc 到底
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }

// 🔴 归位 ②：**工具态也必须归位**。上一轮崩在 keyGuard 抛错那行，**把画布留在抓手态**，
//    于是重跑时「第①格：选择工具下的基线」其实是在**抓手态**下测的 —— 基线直接是假的。
//    ⇒ 崩掉的脚本会污染**下一轮的起点**，和批次 92「收尾污染下一轮前置」同型，
//       但方向反过来：是**崩在半路**而不是**收尾没做完**。所以开头一律先归位再断言。
const toolAria = () => p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return t ? t.getAttribute('aria-label') : null; });
out.toolAtStart = await toolAria();
if (out.toolAtStart !== '选择工具') {
  await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1200);
  out.toolAfterFix = await toolAria();
  log('🔧 起点不是选择工具（多半是上一轮崩在抓手态），已点 toggle 归位 →', out.toolAfterFix);
} else out.toolAfterFix = out.toolAtStart;

// 🔴 **共享画布的教训（批次 95 §4.15.6）**：不先适配全画布，锁定节点很可能**整个跑出视口**，
//    于是「点不到」被误当成「抓手态下点不中」——**假阴性就是这么来的**。
//    适配后所有节点都收进视野，落点扫描才有意义。（适配会把缩放改成「适配值」，收尾必须归位。）
out.fitBefore = { zoom: await zoomLabel(), scale: await scaleNow() };
await p.keyboard.press('Meta+0');
await p.waitForTimeout(1900);
out.fitAfter = { zoom: await zoomLabel(), scale: await scaleNow() };
log('适配画布：', JSON.stringify(out.fitBefore), '→', JSON.stringify(out.fitAfter));

let pt = await pointAt(TID);
out.pt = pt;
if (!pt) {
  // 锁定节点仍点不到 ⇒ 换节点：扫所有节点类型，找第一个可点的
  out.swap = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node'))
    .map((n) => { const r = n.getBoundingClientRect();
      return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
        inView: r.right > 0 && r.bottom > 0 && r.left < 1280 && r.top < 720,
        w: Math.round(r.width), h: Math.round(r.height) }; }));
  const cand = out.swap.find((c) => c.inView && c.w > 8);
  if (cand) { TID = cand.id; out.pt = await pointAt(cand.id); out.swappedTo = cand; log('换被测节点：', JSON.stringify(cand)); }
}
log('落点：', JSON.stringify(out.pt));
if (!out.pt) { log('🔴 适配后仍找不到落点，本轮记 VOID'); writeFileSync(new URL('./_tmp-b96c.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(1); }

// ① 基线：选择工具下单击 → 应当选中
await cell('①选择工具-起点');
out.click1 = await clickAndVerify(TID, '选择工具下单击');
await p.waitForTimeout(1200);
const c1 = await cell('②选择工具-单击');
out.baselineClickSelects = c1.targetSelected === true;
log('   ② 落点回执：', JSON.stringify(out.click1));
await p.keyboard.press('Escape'); await p.waitForTimeout(800);
await cell('③Esc后');

// ④ 切到抓手态（点 toggle —— 批次 90 钉的「唯一路径」）
await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100);
const c4 = await cell('④点toggle后');
out.toggledToGrab = c4.pointer.aria === '抓手工具';
if (c4.pointer.aria !== '抓手工具') { log('🔴 没切到抓手态，剩余各格记 VOID'); }
else {
  pt = await pointAt(TID);   // 抓手态可能改了渲染，落点重取
  out.ptInGrab = pt;
  // ⑤ 抓手态单击节点
  out.click5 = await clickAndVerify(TID, '抓手态下单击');
  await p.waitForTimeout(1300);
  const c5 = await cell('⑤抓手-单击节点'); out.grabClickSelects = c5.targetSelected === true;
  log('   ⑤ 落点回执：', JSON.stringify(out.click5));
  // ⑥ 抓手态双击节点
  if (pt) { await p.mouse.dblclick(pt.x, pt.y); await p.waitForTimeout(1400);
    const c6 = await cell('⑥抓手-双击节点'); out.grabDblclickSelects = c6.targetSelected === true; }

  // ⑦ 按 V 能不能退出抓手态（批次 90 说无效 —— 本轮复核）
  // 按字母键前过守卫（焦点可能在别处时会把按键变成打字）
  const g = await keyGuard(p);
  out.keyGuardV = g;
  if (g.safe) { await p.keyboard.press('v'); await p.waitForTimeout(1100);
    const c7 = await cell('⑦抓手-按V后'); out.vSwitchesBack = c7.pointer.aria === '选择工具'; }
  else log('⛔ keyGuard 拒绝按 V：', JSON.stringify(g));

  // ⑧ 抓手态右键节点 —— 菜单弹不弹得出来？
  if (pt) { await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(250);
    await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
    await p.waitForTimeout(1500);
    const c8 = await cell('⑧抓手-右键节点'); out.grabRightClickMenu = c8.ctxMenuOpen;
    if (c8.ctxMenuOpen) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); } }

  // ⑨ 抓手态下 dock 的「显示连线」还能不能点（点两次复原）
  const cnBefore = (await read('x')).connections.pressed;
  await p.click('[data-testid="canvas-display-toggle-connections"]'); await p.waitForTimeout(1100);
  const c9 = await cell('⑨抓手-点显示连线');
  out.grabDockToggleWorks = c9.connections.pressed !== cnBefore;
  await p.click('[data-testid="canvas-display-toggle-connections"]'); await p.waitForTimeout(1100);
  const c9b = await cell('⑨b抓手-点回显示连线');
  out.dockToggleRestored = c9b.connections.pressed === cnBefore;

  // ⑩ 抓手态下缩放值按钮还能不能点开（**只开弹层，不设值**）
  await p.click('[data-testid="canvas-zoom-percent"]'); await p.waitForTimeout(1300);
  const c10 = await cell('⑩抓手-点缩放值按钮');
  out.grabZoomButtonWorks = c10.zoomMenuOpen > 0;
  if (c10.zoomMenuOpen) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); }

  // ⑪ 抓手态下小地图开关（点两次复原）
  const mmBefore = (await read('y')).minimap;
  await p.click('[data-testid="canvas-display-toggle-minimap"]'); await p.waitForTimeout(1200);
  const c11 = await cell('⑪抓手-点小地图');
  out.grabMinimapWorks = c11.minimap.pressed !== mmBefore.pressed;
  await p.click('[data-testid="canvas-display-toggle-minimap"]'); await p.waitForTimeout(1200);
  const c11b = await cell('⑪b抓手-点回小地图');

  // ⑫ 点 toggle 退出抓手态
  await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100);
  const c12 = await cell('⑫点toggle退出');
  out.backToSelect = c12.pointer.aria === '选择工具';
  // ⑬ 退出后节点应当又能点中
  out.click13 = await clickAndVerify(TID, '退出抓手态后单击');
  await p.waitForTimeout(1300);
  const c13 = await cell('⑬退出抓手-单击节点'); out.afterExitClickSelects = c13.targetSelected === true;
  log('   ⑬ 落点回执：', JSON.stringify(out.click13));
}

// 收尾：**工具态也归位**（崩在抓手态就等于给下一个人留坑）
const toolEnd0 = await toolAria();
if (toolEnd0 !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }
out.toolAtEnd = await toolAria();
log('工具态归位：', toolEnd0, '→', out.toolAtEnd);

// 收尾：Esc 到底 → **缩放归位 60%**（适配画布会改缩放，不归位就是把 23% 留给别人）
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
out.restore = await (async () => {
  for (let k = 1; k <= 4; k++) {
    const zl = await zoomLabel();
    if (zl && /, 60%$/.test(zl.aria)) return { ok: true, tries: k - 1 };
    await p.click('[data-testid="canvas-zoom-percent"]'); await p.waitForTimeout(1000);
    const has = await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'));
    if (has) {
      await p.evaluate(() => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
        Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, '60');
        i.dispatchEvent(new Event('input', { bubbles: true }));
        i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
        i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); });
      await p.waitForTimeout(1700);
    } else { out.restoreNote = '弹层里没有 canvas-zoom-percent-input（低档位时可能不渲染）'; }
    await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  }
  const zl = await zoomLabel();
  return { ok: !!(zl && /, 60%$/.test(zl.aria)), tries: 4 };
})();
log('缩放归位：', JSON.stringify(out.restore), out.restore.ok ? '✅' : '🔴');
out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow(),
  pointer: await p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
    return t ? { aria: t.getAttribute('aria-label'), pressed: t.getAttribute('aria-pressed') } : null; }) };
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b96c.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
