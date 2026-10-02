// 批次 96 · a 轮：**只读**结构取证，不改任何状态。
//
// 靶子 `navigate-canvas.md`（普查 79，305 行）。弹药来自两批：
//
//   🔑 **批次 90** 钉死了「抓手态下单击/双击节点**都不选中**」「dock 只有一个
//      `canvas-pointer-tool-toggle` 钮，aria 在 `选择工具`/`抓手工具` 间翻」
//      「**V 键不切工具**，退出抓手态的唯一路径就是点它」——
//      而 `navigate-canvas.md` 第 26–44 行正是**讲抓手工具的那一节**，却一个字没提这些。
//      ⇒ 这就是批次 90 立的那条规矩的靶子：「踩过的坑要搬到读者会去的那一页」。
//
//   🔴 **批次 95** 实测：`Zoom options` 弹层打开后才有
//      `input[data-testid="canvas-zoom-percent-input"]`（弹层关闭时全页只有 2 个 `type=file`）。
//      本页第 82 行写的是「**缩放按钮本身**是一个输入框（aria `Set zoom percentage`，48×28）」——
//      两者对不上。**到底是按钮自带输入框，还是弹层里另有一个**，本轮查清。
//
// 本轮全程只读：只点开弹层/只读 DOM，不改缩放、不点菜单项。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };

const zoomLabel = () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]');
  return e ? e.getAttribute('aria-label') : null; });
const scaleNow = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });

out.start = { zoom: await zoomLabel(), scale: await scaleNow(),
  nodes: await p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]),
  sel: await p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]) };
log('起点：', JSON.stringify(out.start));

// ---- P1：缩放按钮本体是不是一个 input？----
out.p1_zoomButton = await p.evaluate(() => {
  const btn = document.querySelector('button[aria-label^="Zoom options"]');
  if (!btn) return null;
  const r = btn.getBoundingClientRect();
  return { tag: btn.tagName, type: btn.getAttribute('type'), aria: btn.getAttribute('aria-label'),
    testid: btn.getAttribute('data-testid'), role: btn.getAttribute('role'),
    value: btn.getAttribute('value'), contentEditable: btn.getAttribute('contenteditable'),
    childInputs: btn.querySelectorAll('input').length,
    childTags: Array.from(btn.children).map((c) => c.tagName + (c.getAttribute('data-testid') ? '#' + c.getAttribute('data-testid') : '')),
    innerText: btn.innerText.replace(/\s+/g, ' ').trim(),
    screen: { w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y) },
    isContentEditableHost: btn.querySelector('[contenteditable]') !== null };
});
log('P1 缩放按钮：', JSON.stringify(out.p1_zoomButton));

// ---- P2：`Set zoom percentage` 在页面里吗？（弹层关闭态）----
out.p2_closed = await p.evaluate(() => {
  const all = Array.from(document.querySelectorAll('input,[contenteditable="true"],[role="spinbutton"]'));
  return { total: all.length,
    list: all.map((e) => ({ tag: e.tagName, type: e.getAttribute('type'),
      tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
      role: e.getAttribute('role'), value: e.getAttribute('value'),
      text: (e.innerText || '').slice(0, 20) })),
    setZoomByText: Array.from(document.querySelectorAll('*'))
      .filter((e) => (e.getAttribute('aria-label') || '') === 'Set zoom percentage')
      .map((e) => { const r = e.getBoundingClientRect();
        return { tag: e.tagName, tid: e.getAttribute('data-testid'),
          screen: { w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y) } }; }),
    zoomPctInput: document.querySelectorAll('input[data-testid="canvas-zoom-percent-input"]').length };
});
log('P2 弹层关闭态：', JSON.stringify(out.p2_closed));

// ---- P3：打开弹层，再读一遍 ----
await p.click('button[aria-label^="Zoom options"]');
await p.waitForTimeout(1200);
out.p3_open = await p.evaluate(() => {
  const all = Array.from(document.querySelectorAll('input,[contenteditable="true"],[role="spinbutton"]'));
  const byTestid = (t) => { const e = document.querySelector(`[data-testid="${t}"]`); if (!e) return null;
    const r = e.getBoundingClientRect();
    return { tag: e.tagName, value: e.getAttribute('value'), min: e.getAttribute('min'), max: e.getAttribute('max'),
      step: e.getAttribute('step'), aria: e.getAttribute('aria-label'), cls: (e.className || '').toString().slice(0, 40),
      screen: { w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y) } }; };
  const m = document.querySelector('[data-testid="canvas-context-menu"]');
  const mr = m ? m.getBoundingClientRect() : null;
  return { total: all.length,
    list: all.filter((e) => e.tagName === 'INPUT' || e.getAttribute('contenteditable') === 'true')
      .map((e) => ({ tag: e.tagName, type: e.getAttribute('type'), tid: e.getAttribute('data-testid'),
        aria: e.getAttribute('aria-label'), value: e.getAttribute('value') })),
    setZoomByText: Array.from(document.querySelectorAll('*'))
      .filter((e) => (e.getAttribute('aria-label') || '') === 'Set zoom percentage')
      .map((e) => { const r = e.getBoundingClientRect();
        return { tag: e.tagName, tid: e.getAttribute('data-testid'),
          screen: { w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y) } }; }),
    zoomPctInput: byTestid('canvas-zoom-percent-input'),
    zoomMenuTids: Array.from(document.querySelectorAll('[data-testid]'))
      .map((e) => e.getAttribute('data-testid')).filter((t) => /zoom/i.test(t)),
    menu: m ? { screen: { w: Math.round(mr.width), h: Math.round(mr.height), x: Math.round(mr.x), y: Math.round(mr.y) },
      items: Array.from(m.querySelectorAll('[role="menuitem"]')).map((x) => {
        const b2 = x.getBoundingClientRect();
        return { text: x.innerText.replace(/\s+/g, ' ').trim(), w: Math.round(b2.width), h: Math.round(b2.height),
          disabled: x.getAttribute('aria-disabled') }; }) } : null };
});
log('P3 弹层打开态：');
log('   setZoomByText =', JSON.stringify(out.p3_open.setZoomByText));
log('   zoomPctInput =', JSON.stringify(out.p3_open.zoomPctInput));
log('   zoomMenuTids =', JSON.stringify(out.p3_open.zoomMenuTids));
log('   menu =', JSON.stringify(out.p3_open.menu));

// ---- P4：dock 全部按钮（含抓手 toggle 的当前态）----
out.p4_dock = await p.evaluate(() => {
  const all = Array.from(document.querySelectorAll('button,[role="button"]'));
  return all.filter((e) => { const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && r.y > 640; })
    .map((e) => { const r = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), tid: e.getAttribute('data-testid'),
        pressed: e.getAttribute('aria-pressed'), role: e.getAttribute('role'),
        text: e.innerText.replace(/\s+/g, ' ').trim().slice(0, 20),
        screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; });
});
log('P4 底部 dock：', JSON.stringify(out.p4_dock));

// ---- P5：抓手 toggle 唯一性（复核批次 90）----
out.p5_pointerTool = await p.evaluate(() => {
  const t = document.querySelectorAll('[data-testid="canvas-pointer-tool-toggle"]');
  return { count: t.length, items: Array.from(t).map((e) => {
    const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), pressed: e.getAttribute('aria-pressed'),
      screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; }) };
});
log('P5 抓手 toggle：', JSON.stringify(out.p5_pointerTool));

await p.keyboard.press('Escape');
await p.waitForTimeout(800);
out.end = { zoom: await zoomLabel(), scale: await scaleNow() };
log('终态：', JSON.stringify(out.end), '（本轮未改任何状态）');
writeFileSync(new URL('./_tmp-b96a.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
