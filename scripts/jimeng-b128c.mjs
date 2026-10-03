// 批次 128 · c 轮：补上 b 轮最后一步（快捷键抽屉扫描），并做一次全局收尾复扫。
//
// ⚠️ b 轮那步的失败原因（**工具坑，不是产品行为**）：
//   我把 Playwright 专有的 `:has-text("快捷键")` 写进了 `document.querySelector` ——
//   `:has-text()` 不是合法 CSS 选择器 ⇒ 抛 `SyntaxError`。
//   📌 立规：**`page.evaluate` 里的选择器只能是真 CSS**；
//     「按文字找元素」要在 JS 里 `Array.from(qsa(sel)).find(e => /re/.test(e.innerText))`。
//
// 本轮：① 用户菜单 → 快捷键（两级打开），扫描抽屉；② 全部面板关掉后再做一次静态复扫；
//      ③ 确认注入夹具 0 残留。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c' };
const save = () => writeFileSync(new URL('./_tmp-b128c.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);

const SWEEP = (label) => p.evaluate((lb) => {
  const RULES = [
    ['ICU_plural', /\{\s*[A-Za-z_$][\w$]*\s*,\s*plural\s*,/],
    ['ICU_select', /\{\s*[A-Za-z_$][\w$]*\s*,\s*select\s*,/],
    ['ICU_单花括号标识符', /\{[A-Za-z_$][\w$]*\s*(?:[,}])/],
    ['handlebars残留', /\{\{[^}]{1,80}\}\}/],
    ['printf_s_d', /%[sd]\b/],
    ['undefined', /\bundefined\b/],
    ['NaN', /\bNaN\b/],
    ['null字面量', /(^|[\s>])null($|[\s<])/],
    ['[object Object]', /\[object [A-Za-z]+\]/],
    ['替换字符U+FFFD', /�/],
    ['未闭合占位', /\$\{[^}]{0,40}\}/],
  ];
  const ATTRS = ['aria-label', 'title', 'placeholder', 'alt', 'value', 'aria-description', 'aria-roledescription', 'aria-valuetext', 'label'];
  const hits = []; const seen = new Set();
  for (const e of Array.from(document.querySelectorAll('*'))) {
    const r = e.getBoundingClientRect();
    const cands = [];
    for (const n of Array.from(e.childNodes)) if (n.nodeType === 3) cands.push(['#text', n.nodeValue]);
    for (const a of ATTRS) { const v = e.getAttribute && e.getAttribute(a); if (v) cands.push([a, v]); }
    for (const a of Array.from(e.attributes)) { if (!a.name.startsWith('data-')) continue;
      const v = a.value; if (v && /[{}]|%[sd]|\bundefined\b|\bNaN\b|�/.test(v)) cands.push([a.name, v]); }
    for (const [where, s] of cands) {
      if (!s || !s.trim()) continue;
      for (const [rule, re] of RULES) {
        if (!re.test(s)) continue;
        const key = rule + '|' + where + '|' + s; if (seen.has(key)) continue; seen.add(key);
        hits.push({ 扫描点: lb, 规则: rule, 位置: where, 值: s.replace(/\s+/g, ' ').trim().slice(0, 160),
          tag: e.tagName, testid: e.getAttribute('data-testid'), rect: [r.x, r.y, r.width, r.height].map(Math.round),
          有面积: r.width >= 1 && r.height >= 1 });
      }
    }
  }
  return { 扫描点: lb, 元素总数: document.querySelectorAll('*').length, 命中数: hits.length,
    按规则计数: RULES.map(([rule]) => [rule, hits.filter((h) => h.规则 === rule).length]).filter(([, n]) => n > 0), 命中: hits };
}, label);

out.start = { zoom: await zoom(), credits: await credits(), status: await status(), 浮层: await overlays(), 夹具残留: await p.evaluate(() => document.querySelectorAll('[data-b128-fixture]').length) };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
for (let i = 0; i < 3; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(1000); }

// ---- ① 用户菜单 → 快捷键 ----
out.用户菜单 = await p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-user-menu-trigger"]');
  if (!e) return { __err: 'no-trigger' };
  const r = e.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
  return { __err: 'no-point' };
});
log('\n=== ① 用户菜单 → 快捷键 ===\n  启动器落点：', JSON.stringify(out.用户菜单));
if (!out.用户菜单.__err) {
  await p.mouse.click(out.用户菜单.x, out.用户菜单.y); await p.waitForTimeout(1600);
  out.菜单读数 = await p.evaluate(() => {
    const m = document.querySelector('[data-testid="canvas-user-menu"]');
    if (!m) return { __err: 'no-menu' };
    const R = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
    return { 矩形: R(m), role: m.getAttribute('role'), 逐字: (m.innerText || '').replace(/\s+/g, ' ').trim(),
      项: Array.from(m.querySelectorAll('[role=menuitem],button')).map((e) => ({ tag: e.tagName, rect: R(e), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim() })) };
  });
  log('  菜单：', JSON.stringify(out.菜单读数));
  out.快捷键项 = await p.evaluate(() => {
    // 📌 按文字找元素必须在 JS 里做：`:has-text()` 不是合法 CSS
    const items = Array.from(document.querySelectorAll('[data-testid="canvas-user-menu"] [role=menuitem]'));
    const it = items.find((e) => /^快捷键/.test((e.innerText || '').replace(/\s+/g, '').trim()));
    if (!it) return { __err: 'no-item', 现有: items.map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()) };
    const r = it.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
      const h = document.elementFromPoint(x, y); if (h && (h === it || it.contains(h))) return { x, y, 文字: (it.innerText || '').replace(/\s+/g, ' ').trim() }; }
    return { __err: 'no-point' };
  });
  log('  快捷键项：', JSON.stringify(out.快捷键项));
  if (!out.快捷键项.__err) {
    await p.mouse.click(out.快捷键项.x, out.快捷键项.y); await p.waitForTimeout(1900);
    out.抽屉 = await p.evaluate(() => {
      const cands = Array.from(document.querySelectorAll('[role=dialog],[data-testid]')).filter((e) => { const r = e.getBoundingClientRect(); return r.width > 200 && r.height > 200 && /快捷键|Shortcuts/i.test((e.getAttribute('aria-label') || '') + (e.getAttribute('data-testid') || '')); });
      return cands.map((e) => { const r = e.getBoundingClientRect();
        return { tag: e.tagName, tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), role: e.getAttribute('role'),
          rect: [r.x, r.y, r.width, r.height].map(Math.round), 逐字前120: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120), 文本长度: (e.innerText || '').length }; });
    });
    log('  抽屉：', JSON.stringify(out.抽屉));
    const sw = await SWEEP('快捷键抽屉');
    out.抽屉扫描 = { 元素总数: sw.元素总数, 命中数: sw.命中数, 规则: sw.按规则计数 };
    log('  抽屉扫描：元素', sw.元素总数, '｜命中', sw.命中数, JSON.stringify(sw.按规则计数));
    sw.命中.forEach((h) => log(`      · [${h.规则}] <${h.tag}> ${h.testid ? 'tid=' + h.testid : ''} ${JSON.stringify(h.rect)} @${h.位置} «${h.值}»`));
    save();
    for (let i = 0; i < 3; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(1100); }
    out.抽屉关闭后浮层 = await overlays();
    log('  关闭后浮层：', out.抽屉关闭后浮层);
  }
}
save();

// ---- ② 全局收尾复扫（所有面板都关掉之后） ----
for (let i = 0; i < 3; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(1000); }
out.收尾复扫 = await SWEEP('全部面板关闭后的静态画布');
log('\n=== ② 全部面板关闭后复扫 ===\n  元素', out.收尾复扫.元素总数, '｜命中', out.收尾复扫.命中数, JSON.stringify(out.收尾复扫.按规则计数));
out.收尾复扫.命中.forEach((h) => log(`    · [${h.规则}] <${h.tag}> ${h.testid ? 'tid=' + h.testid : ''} @${h.位置} «${h.值}»`));
save();

out.收尾 = { 浮层: await overlays(), 夹具残留: await p.evaluate(() => document.querySelectorAll('[data-b128-fixture]').length),
  选中: await sel(), zoom1: await zoom(), credits: await credits(), status: await status() };
await p.waitForTimeout(1200);
out.收尾.zoom2 = await zoom();
log('\n收尾：', JSON.stringify(out.收尾));
save();
log('\nDONE c');
process.exit(0);
