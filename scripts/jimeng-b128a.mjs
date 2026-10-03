// 批次 128 · a 轮：**未翻译 / 未插值文案普查**（纯只读，不点任何东西）。
//
// 🔑 靶子：批次 127 在搜索面板的分页条上抓到两个**没插值的国际化占位串** ——
//   aria 逐字 `{num, plural, other {向前 {num} 页}}` / `{num, plural, other {向后 {num} 页}}`
//   ⇒ 读屏软件会把这串占位符原样念出来。这是**产品侧缺陷**，而全册从未提过。
//   两条要问的：① 这种串**只有这一处**吗？② 它们在**哪些宿主**里出现？
//
// 本轮分两部分：
//   A. **静态全文档扫描**（零交互）：把 `document` 上所有元素的
//      「可见文本 + 常见属性（aria-label / title / placeholder / alt / value / data-* 里的字符串）」
//      全捞一遍，按若干「缺陷特征」分类计数。
//   B. **逐个打开顶栏面板再扫一遍**（每个面板：落点现算 + elementFromPoint 自检 → 扫 → Esc 关），
//      用来回答「这个缺陷出现在哪几个面板里」。
//
// ⛔ 只**打开**面板，不点面板里的任何一项（用户菜单里有退出登录/充值一类，
//    分享面板里有复制链接，都属未授权动作）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b128a.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);

out.start = { zoom: await zoom(), credits: await credits(), status: await status(), 浮层: await overlays() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

// ---- 扫描器：一次 evaluate 抓全文档 ----
const SWEEP = (label) => p.evaluate((lb) => {
  // 缺陷特征：每条都必须是「能一眼看出是缺陷」的形态，避免误报正常文案
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
  const ATTRS = ['aria-label', 'title', 'placeholder', 'alt', 'value', 'aria-description', 'aria-roledescription', 'aria-valuetext', 'data-tooltip-content', 'label'];
  const hits = [];
  const seen = new Set();
  const all = Array.from(document.querySelectorAll('*'));
  for (const e of all) {
    const r = e.getBoundingClientRect();
    const visible = r.width >= 1 && r.height >= 1;
    // 候选字符串：自身文本节点 + 常见属性 + data-* 里的字符串
    const cands = [];
    for (const n of Array.from(e.childNodes)) if (n.nodeType === 3) cands.push(['#text', n.nodeValue]);
    for (const a of ATTRS) { const v = e.getAttribute && e.getAttribute(a); if (v) cands.push([a, v]); }
    for (const a of Array.from(e.attributes)) {
      if (!a.name.startsWith('data-')) continue;
      const v = a.value; if (v && /[{}]|%[sd]|\bundefined\b|\bNaN\b|�/.test(v)) cands.push([a.name, v]);
    }
    for (const [where, s] of cands) {
      if (!s || !s.trim()) continue;
      for (const [rule, re] of RULES) {
        if (!re.test(s)) continue;
        const key = rule + '|' + where + '|' + s;
        if (seen.has(key)) continue;
        seen.add(key);
        const chain = []; let n = e;
        for (let i = 0; i < 4 && n && n !== document.body; i++) { chain.push(n.tagName + (n.getAttribute('data-testid') ? '[' + n.getAttribute('data-testid') + ']' : '') + (n.getAttribute('role') ? '{' + n.getAttribute('role') + '}' : '')); n = n.parentElement; }
        hits.push({ 扫描点: lb, 规则: rule, 位置: where, 值: s.replace(/\s+/g, ' ').trim().slice(0, 160),
          tag: e.tagName, testid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
          矩形: [r.x, r.y, r.width, r.height].map(Math.round), 屏上有面积: visible,
          屏外隐藏: (() => { const st = getComputedStyle(e); return st.position === 'absolute' && (st.clip || '').includes('rect') ? 'sr-only' : (st.display === 'none' || st.visibility === 'hidden' ? 'display:none/visibility:hidden' : '否'); })(),
          祖先链: chain });
      }
    }
  }
  return { 扫描点: lb, 元素总数: all.length, 命中数: hits.length,
    按规则计数: RULES.map(([rule]) => [rule, hits.filter((h) => h.规则 === rule).length]).filter(([, n]) => n > 0), 命中: hits };
}, label);

// ---- A. 静态全文档扫描（零交互） ----
out.静态 = await SWEEP('画布静态（未打开任何面板）');
log('\n=== A. 静态全文档扫描 ===');
log('  元素总数：', out.静态.元素总数, '｜命中：', out.静态.命中数);
log('  按规则：', JSON.stringify(out.静态.按规则计数));
log('  --- 逐条（只看屏上有面积的）---');
out.静态.命中.filter((h) => h.屏上有面积).forEach((h, i) => log(`  ${i + 1}. [${h.规则}] <${h.tag}> ${h.testid ? 'tid=' + h.testid : ''} ${JSON.stringify(h.矩形)} @${h.位置} «${h.值}»`));
log('  --- 屏外/隐藏的（数量：' + out.静态.命中.filter((h) => !h.屏上有面积).length + '）---');
out.静态.命中.filter((h) => !h.屏上有面积).forEach((h, i) => log(`  ${i + 1}. [${h.规则}] <${h.tag}> ${h.屏外隐藏} @${h.位置} «${h.值.slice(0, 70)}»`));
save();

// ---- B. 逐个打开顶栏面板再扫 ----
async function openBySel(sel, note) {
  const pt = await p.evaluate((s) => {
    const e = document.querySelector(s);
    if (!e) return { __err: 'not-found' };
    const r = e.getBoundingClientRect();
    if (r.width < 1) return { __err: 'zero-size' };
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
      for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
        const h = document.elementFromPoint(x, y);
        if (h && (h === e || e.contains(h))) return { x, y, 命中: h.tagName };
      }
    return { __err: 'no-point', rect: [r.x, r.y, r.width, r.height].map(Math.round) };
  }, sel);
  if (pt.__err) { log(`  ⛔ ${note} 打开失败：`, JSON.stringify(pt)); return pt; }
  await p.mouse.click(pt.x, pt.y);
  await p.waitForTimeout(1600);
  return { ok: true, 落点: pt };
}

const panels = [
  ['搜索', '[data-testid="canvas-panel-launcher"][aria-label="搜索"]'],
  ['生成历史', '[data-testid="canvas-panel-launcher"][aria-label="生成历史"]'],
  ['分享', '[data-testid="canvas-share-trigger"]'],
  ['项目', '[data-testid="canvas-project-trigger"]'],
  ['节点N', '[data-testid="canvas-node-summary-trigger"]'],
  ['更多', 'button[aria-label="更多"]'],
  ['用户菜单', '[data-testid="canvas-user-menu-trigger"]'],
];

out.面板扫描 = {};
log('\n=== B. 逐个打开顶栏面板 ===');
for (const [name, sel] of panels) {
  const opened = await openBySel(sel, name);
  out.面板扫描[name] = { 打开: opened };
  if (!opened.ok) continue; 
  const sw = await SWEEP(name);
  out.面板扫描[name].扫描 = sw;
  log(`  【${name}】元素 ${sw.元素总数}｜命中 ${sw.命中数}｜按规则 ${JSON.stringify(sw.按规则计数)}`);
  sw.命中.filter((h) => h.屏上有面积).forEach((h) => log(`      · [${h.规则}] <${h.tag}> ${h.testid ? 'tid=' + h.testid : ''} ${JSON.stringify(h.矩形)} @${h.位置} «${h.值}»`));
  sw.命中.filter((h) => !h.屏上有面积).forEach((h) => log(`      · [${h.规则}] ${h.屏外隐藏} <${h.tag}> @${h.位置} «${h.值.slice(0, 60)}»`));
  save();
  // 关掉：Esc（必要时两次）
  for (let i = 0; i < 2; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(1000); }
  out.面板扫描[name].关闭后浮层 = await overlays();
  log(`      关闭后浮层：${out.面板扫描[name].关闭后浮层}`);
}
save();

// ---- 汇总 ----
out.汇总 = {};
for (const [name, v] of Object.entries(out.面板扫描)) {
  if (!v.扫描) continue;
  out.汇总[name] = { 命中: v.扫描.命中数, 规则: Object.fromEntries(v.扫描.按规则计数),
    值: v.扫描.命中.map((h) => ({ 规则: h.规则, 值: h.值, 屏上有面积: h.屏上有面积, 位置: h.位置, testid: h.testid })) };
}
log('\n=== 汇总 ===');
log(JSON.stringify(out.汇总, null, 1).slice(0, 4000));
save();

out.收尾 = { 浮层: await overlays(), 选中: await sel(), zoom: await zoom(), credits: await credits(), status: await status() };
log('\n收尾：', JSON.stringify(out.收尾));
save();
log('\nDONE a');
process.exit(0);
