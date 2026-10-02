// 批次 100 · b 轮：a 轮**用户菜单没打开**（`用户菜单项: []`、点「快捷键」= false），
//    所以面板全表对账没做成。用批次 95 那招：**对点击前后做 DOM 全量 diff**，
//    把新出现的容器逐个报出来，找回真正的入口。
//
// ⚠️ a 轮的错：用 `t.click()`（DOM 派发）去开菜单，而不是**真实鼠标点击**。
//    批次 22/91 反复证明：这类需要 pointer 序列的浮层，`element.click()` 常常**打不开**。
//    ⇒ 本轮一律用 `mouse.move → click`，并对比两种方式的差异。
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
const toolAria = () => p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return t ? t.getAttribute('aria-label') : null; });

// 指纹：所有可见的、带 testid / role / 有文字的容器
const snap = () => p.evaluate(() => {
  const s = new Set();
  for (const e of document.querySelectorAll('[data-testid]')) {
    const r = e.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    s.add(`tid|${e.getAttribute('data-testid')}|${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`);
  }
  for (const e of document.querySelectorAll('[role]')) {
    const r = e.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    s.add(`role|${e.getAttribute('role')}|${(e.className || '').toString().slice(0, 30)}|${Math.round(r.width)}×${Math.round(r.height)}|${(e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40)}`);
  }
  for (const e of document.querySelectorAll('body *')) {
    const r = e.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (r.x < 900 || r.y < 0 || r.y > 300) continue;     // 只看右上角区域
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 60 || e.children.length > 0) continue;
    s.add(`txt|${e.tagName}|${t.slice(0, 50)}|${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`);
  }
  return Array.from(s);
});

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), tool: await toolAria() };
log('起点：', JSON.stringify(out.start));
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }

const trig = await p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-user-menu-trigger"]');
  if (!t) return null; const r = t.getBoundingClientRect();
  return { aria: t.getAttribute('aria-label'), x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
    w: Math.round(r.width), h: Math.round(r.height), expanded: t.getAttribute('aria-expanded') }; });
out.trig = trig;
log('用户菜单触发器：', JSON.stringify(trig));
if (!trig) { log('🔴 找不到触发器'); }
else {
  const before = await snap();
  // 🔑 **真实鼠标点击**（a 轮用的 DOM click 打不开）
  await p.mouse.move(trig.x, trig.y); await p.waitForTimeout(350);
  await p.mouse.click(trig.x, trig.y);
  await p.waitForTimeout(1600);
  const after = await snap();
  out.added = after.filter((x) => !before.includes(x));
  out.removed = before.filter((x) => !after.includes(x));
  log('点击后新增 ' + out.added.length + ' 项：');
  out.added.forEach((x) => log('   + ' + x));
  log('消失 ' + out.removed.length + ' 项：');
  out.removed.forEach((x) => log('   - ' + x));

  out.menuState = await p.evaluate(() => {
    const trig = document.querySelector('[data-testid="canvas-user-menu-trigger"]');
    // 把右上角所有可点元素列出来
    const items = Array.from(document.querySelectorAll('body *')).filter((e) => {
      const r = e.getBoundingClientRect();
      if (r.width < 40 || r.height < 12) return false;
      if (r.x < 800 || r.y < 0 || r.y > 500) return false;
      return e.children.length <= 1;
    }).slice(0, 25).map((e) => { const r = e.getBoundingClientRect();
      return { tag: e.tagName, role: e.getAttribute('role'), tid: e.getAttribute('data-testid'),
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
        screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; });
    return { expanded: trig ? trig.getAttribute('aria-expanded') : null, items };
  });
  log('菜单态：', JSON.stringify(out.menuState));

  // 找「快捷键」并点它
  const sk = await p.evaluate(() => {
    const el = Array.from(document.querySelectorAll('body *')).find((e) => {
      const r = e.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) return false;
      return (e.innerText || '').replace(/\s+/g, ' ').trim() === '快捷键'; });
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { tag: el.tagName, role: el.getAttribute('role'), tid: el.getAttribute('data-testid'),
      x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
      screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; });
  out.shortcutEntry = sk;
  log('「快捷键」入口：', JSON.stringify(sk));

  if (sk) {
    await p.mouse.move(sk.x, sk.y); await p.waitForTimeout(300);
    await p.mouse.click(sk.x, sk.y);
    await p.waitForTimeout(2000);
    out.panel = await p.evaluate(() => {
      const scroll = document.querySelector('[data-testid="shortcut-help-scroll-region"]');
      const r = (e) => { if (!e) return null; const b = e.getBoundingClientRect();
        return `${Math.round(b.width)}×${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`; };
      const drawer = scroll ? scroll.closest('div') : null;
      if (!scroll) {
        // 面板可能用了别的 testid
        const cands = Array.from(document.querySelectorAll('[data-testid]'))
          .map((e) => { const b = e.getBoundingClientRect();
            return { tid: e.getAttribute('data-testid'), s: `${Math.round(b.width)}×${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}` }; })
          .filter((x) => /shortcut|help|drawer|panel/i.test(String(x.tid)));
        return { present: false, cands: cands.slice(0, 12) };
      }
      return { present: true, scrollScreen: r(scroll), drawerScreen: r(drawer),
        scrollHeight: scroll.scrollHeight, clientHeight: scroll.clientHeight,
        rows: Array.from(scroll.querySelectorAll('*'))
          .filter((e) => e.children.length === 0 && (e.innerText || '').trim())
          .map((e) => ({ tag: e.tagName, text: e.innerText.replace(/\s+/g, ' ').trim() })) };
    });
    log('面板：', out.panel.present
      ? `${out.panel.scrollScreen} 滚动 ${out.panel.scrollHeight}/可见 ${out.panel.clientHeight}`
      : ('未出现；相关 testid：' + JSON.stringify(out.panel.cands)));
    if (out.panel.present) {
      log(`导出 ${out.panel.rows.length} 行：`);
      out.panel.rows.forEach((r, i) => log(`   ${String(i + 1).padStart(2)}. [${r.tag}] ${r.text}`));
    }
  }
}

// 收尾
await p.keyboard.press('Escape'); await p.waitForTimeout(1100);
out.closed = await p.evaluate(() => ({ scroll: document.querySelectorAll('[data-testid="shortcut-help-scroll-region"]').length }));
log('Esc 后面板数：', out.closed.scroll);
out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), tool: await toolAria() };
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b100b.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
