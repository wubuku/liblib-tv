// 批次 99 · a 轮：**只读**复核 `00-quickstart.md` 的「界面清单」四个分区。
//
// 🔑 **本批主靶点是一处自伤**：批次 96 我在 `navigate-canvas.md` 写了
//    「**底部 dock 一共 5 个控件**」并把 `canvas-sidecar-launcher`（`与 AI 对话`
//    `118×34@1149,673`）列进了那张表。**那是错的** ——
//    ① 批次 98 独立量到 dock 本体 `canvas-navigation-dock` = **`164×36@12,668`**，
//       宽 164 根本装不下 x=1149 的那颗钮；
//    ② 批次 96 自己的取数就是粗筛（`r.y > 640`），**把画布上的节点控件也一起捞进来了**，
//       那轮已经因此在 AUDIT 里记过一笔（「y > 640 粗筛会捞进 15 个 Add tags」）。
//    ⇒ 本轮要把**四个分区的归属逐个钉死**，并**就地订正批次 96**。
//
// 另外两条现成交叉验证：
//   · 本页写「缩放值按钮的菜单 7 项 200×292」—— 批次 96 刚第六次确认，**且补出了 testid
//     `canvas-zoom-menu`**（本页没写 testid，后人会用 `canvas-context-menu` 去查、拿到 `null`）。
//   · 本页写左栏 9 项每项 `40×40`、顶栏 10 个可点元素 —— 逐项复核。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };

const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const nodeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]');
  return e ? e.getAttribute('aria-label') : null; });
const zoomLabel = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return e ? e.getAttribute('aria-label') : null; });
const scaleNow = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow() };
log('起点：', JSON.stringify(out.start));

// ---- P1：四个分区容器是否存在 + 它们各自的 rect（**先定容器，再定成员**）----
out.containers = await p.evaluate(() => {
  const g = (t) => { const e = document.querySelector(`[data-testid="${t}"]`); if (!e) return null;
    const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return { tag: e.tagName, screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      pe: cs.pointerEvents, children: e.children.length,
      desc: (() => { let n = 0, c = e; while ((c = c.parentElement)) n++; return n; })() }; };
  return { leftRail: g('canvas-fixed-toolbar-left-rail'),
    bottomDockFrame: g('workspace-bottom-dock-frame'),
    bottomDock: g('canvas-navigation-dock'),
    topBar: g('canvas-top-bar'),
    sidecar: g('canvas-sidecar-launcher'),
    sidecarHost: g('canvas-sidecar-launcher-host') };
});
log('P1 容器：');
for (const [k, v] of Object.entries(out.containers)) log(`   ${k}: ${v ? v.screen + ' pe=' + v.pe + ' 子元素=' + v.children : 'null'}`);

// ---- P2：dock 容器的**直接子元素**逐个读（这是「dock 有几个」的正解）----
out.dock = await p.evaluate(() => {
  const dock = document.querySelector('[data-testid="canvas-navigation-dock"]');
  const frame = document.querySelector('[data-testid="workspace-bottom-dock-frame"]');
  const read = (root) => {
    if (!root) return null;
    const r = root.getBoundingClientRect();
    return { rootScreen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      kids: Array.from(root.querySelectorAll('button,[role="button"],a')).map((e) => {
        const b = e.getBoundingClientRect();
        return { tag: e.tagName, aria: e.getAttribute('aria-label'), tid: e.getAttribute('data-testid'),
          pressed: e.getAttribute('aria-pressed'),
          screen: `${Math.round(b.width)}×${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`,
          inDockRect: b.right <= r.right + 1 && b.bottom <= r.bottom + 1 && b.left >= r.left - 1 && b.top >= r.top - 1,
          isDescendantOfDock: dock ? dock.contains(e) : null }; }) };
  };
  return { byNavigationDock: read(dock), byFrame: read(frame) };
});
log('P2 dock 容器（canvas-navigation-dock）', out.dock.byNavigationDock?.rootScreen, '：');
(out.dock.byNavigationDock?.kids ?? []).forEach((k) => log(`   ${k.tag} aria=${k.aria} tid=${k.tid} ${k.screen} 在dock矩形内=${k.inDockRect}`));
log('P2 dock 容器（workspace-bottom-dock-frame）', out.dock.byFrame?.rootScreen, '：');
(out.dock.byFrame?.kids ?? []).forEach((k) => log(`   ${k.tag} aria=${k.aria} tid=${k.tid} ${k.screen}`));

// ---- P3：左栏 9 项 ----
out.leftRail = await p.evaluate(() => {
  const rail = document.querySelector('[data-testid="canvas-fixed-toolbar-left-rail"]');
  if (!rail) return null;
  return Array.from(rail.querySelectorAll('button,[role="button"]')).map((e) => {
    const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), tid: e.getAttribute('data-testid'),
      screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; });
});
log(`P3 左栏 ${out.leftRail?.length} 项：`);
(out.leftRail ?? []).forEach((k, i) => log(`   ${i + 1}. ${k.aria} ${k.screen} tid=${k.tid}`));

// ---- P4：顶栏可点元素 ----
out.topBar = await p.evaluate(() => {
  const bar = document.querySelector('[data-testid="canvas-top-bar"]');
  if (!bar) return null;
  return Array.from(bar.querySelectorAll('button,a,[role="button"]')).map((e) => {
    const r = e.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return null;
    return { tag: e.tagName, aria: e.getAttribute('aria-label'), tid: e.getAttribute('data-testid'),
      text: e.innerText.replace(/\s+/g, ' ').trim().slice(0, 16),
      screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; })
    .filter(Boolean);
});
log(`P4 顶栏可点元素 ${out.topBar?.length} 个：`);
(out.topBar ?? []).forEach((k, i) => log(`   ${i + 1}. <${k.tag}> aria=${k.aria} text=${JSON.stringify(k.text)} tid=${k.tid} ${k.screen}`));

// ---- P5：右下角「与 AI 对话」归属 ----
out.sidecar = await p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-sidecar-launcher"]');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  const dock = document.querySelector('[data-testid="canvas-navigation-dock"]');
  const frame = document.querySelector('[data-testid="workspace-bottom-dock-frame"]');
  const bar = document.querySelector('[data-testid="canvas-top-bar"]');
  let chain = [], c = e;
  while (c && chain.length < 8) { chain.push(`${c.tagName}${c.getAttribute('data-testid') ? '#' + c.getAttribute('data-testid') : ''}`); c = c.parentElement; }
  return { aria: e.getAttribute('aria-label'), screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    inDock: dock ? dock.contains(e) : null, inFrame: frame ? frame.contains(e) : null, inTopBar: bar ? bar.contains(e) : null,
    parentChain: chain };
});
log('P5 与 AI 对话：', JSON.stringify(out.sidecar));

// ---- P6：缩放菜单的 testid 复核（批次 96 补出的 `canvas-zoom-menu`）----
await p.click('[data-testid="canvas-zoom-percent"]');
await p.waitForTimeout(1400);
out.zoomMenu = await p.evaluate(() => {
  const g = (sel) => { const e = document.querySelector(sel); if (!e) return null;
    const r = e.getBoundingClientRect(); return `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; };
  const m = document.querySelector('[data-testid="canvas-zoom-menu"]');
  return { zoomMenu: g('[data-testid="canvas-zoom-menu"]'),
    ctxMenu: g('[data-testid="canvas-context-menu"]'),
    pctInput: g('input[data-testid="canvas-zoom-percent-input"]'),
    roleMenuCount: document.querySelectorAll('[role="menu"]').length,
    items: m ? Array.from(m.querySelectorAll('[role="menuitem"]')).map((x) => { const b = x.getBoundingClientRect();
      return { text: x.innerText.replace(/\s+/g, ' ').trim(), w: Math.round(b.width), h: Math.round(b.height),
        disabled: x.getAttribute('aria-disabled') }; }) : null };
});
log('P6 缩放菜单：', JSON.stringify(out.zoomMenu?.zoomMenu), '| 同时 canvas-context-menu =', out.zoomMenu?.ctxMenu,
    '| role=menu 数 =', out.zoomMenu?.roleMenuCount);
(out.zoomMenu?.items ?? []).forEach((i, n) => log(`   ${n + 1}. ${i.text}  ${i.w}×${i.h} disabled=${i.disabled}`));
await p.keyboard.press('Escape');
await p.waitForTimeout(900);

out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow() };
log('终态：', JSON.stringify(out.end), '（本轮只读，未改任何状态）');
writeFileSync(new URL('./_tmp-b99a.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
