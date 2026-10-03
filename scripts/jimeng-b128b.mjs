// 批次 128 · b 轮：给 a 轮的「0 命中」配**不共享同一假设的旁证**，并把覆盖面扩到
//   左栏面板、缩放菜单、快捷键抽屉。
//
// 🔑 a 轮结论：静态画布 2434 个元素 **0 命中**；七个顶栏面板里**只有「搜索」**命中
//   那两个分页首/末页按钮的 aria 占位串。
//   ⚠️ 但「没有别的」这个结论目前**只有一条同源的证据**（同一套规则扫了若干次）。
//   如果扫描器本身抓不到这类串，那「0 命中」就是**仪器坏了**，不是事实。
//   ⇒ 本轮做**阳性对照**：往页面里注入几个**已知形态**的串（ICU / printf / undefined /
//     handlebars / U+FFFD），重跑同一套扫描器，**必须全部被抓到**；抓不到就说明仪器有问题，
//     a 轮的结论要撤回。注入的元素拍完立刻移除（不能留在共享画布上）。
//
// 📌 顺带扩面：左栏五个面板（资产库/主体/时间线/导演台）、缩放菜单、快捷键抽屉。
// ⛔ 只打开，不点里面的项（主体/时间线/导演台面板里可能有新建/生成类按钮）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b' };
const save = () => writeFileSync(new URL('./_tmp-b128b.json', import.meta.url), JSON.stringify(out, null, 1));

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
          tag: e.tagName, testid: e.getAttribute('data-testid'), 矩形: [r.x, r.y, r.width, r.height].map(Math.round),
          屏上有面积: r.width >= 1 && r.height >= 1, 是注入夹具: e.getAttribute('data-b128-fixture') === '1' });
      }
    }
  }
  return { 扫描点: lb, 元素总数: document.querySelectorAll('*').length, 命中数: hits.length,
    按规则计数: RULES.map(([rule]) => [rule, hits.filter((h) => h.规则 === rule).length]).filter(([, n]) => n > 0), 命中: hits };
}, label);

out.start = { zoom: await zoom(), credits: await credits(), status: await status(), 浮层: await overlays() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

// ---- ① 阳性对照：注入 5 个已知形态的串，验证扫描器抓得到 ----
out.夹具注入 = await p.evaluate(() => {
  const host = document.createElement('div');
  host.setAttribute('data-b128-fixture', '1');
  host.setAttribute('id', 'b128-fixture-host');
  host.style.cssText = 'position:fixed;left:0;top:0;width:1px;height:1px;overflow:hidden;pointer-events:none;';
  const cases = [
    ['aria-plural', { 'aria-label': '{num, plural, other {向前 {num} 页}}' }],
    ['aria-select', { 'aria-label': '{kind, select, a {A} other {B}}' }],
    ['printf', { 'title': '共 %s 个' }],
    ['undefined', { 'aria-label': 'undefined' }],
    ['handlebars', { 'title': '{{count}} 个结果' }],
    ['fffd', { 'aria-label': '坏字�' }],
    ['数据属性', { 'data-tip': '{label}' }],
  ];
  for (const [name, attrs] of cases) {
    const e = document.createElement('span');
    e.setAttribute('data-b128-fixture', '1');
    e.setAttribute('data-b128-case', name);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    e.textContent = name;
    host.appendChild(e);
  }
  document.body.appendChild(host);
  return { 注入条数: cases.length };
});
log('\n=== ① 阳性对照：注入夹具 ===\n  ', JSON.stringify(out.夹具注入));
out.夹具扫描 = await SWEEP('阳性对照（注入 7 个已知串）');
log('  扫描命中：', out.夹具扫描.命中数, '｜按规则：', JSON.stringify(out.夹具扫描.按规则计数));
out.夹具抓到 = out.夹具扫描.命中.filter((h) => h.是注入夹具);
// 哪些 case 的元素在命中列表里出现过（按规则名直接对，不靠字符串拼凑）
out.夹具命中case = await p.evaluate(() => Array.from(document.querySelectorAll('[data-b128-case]')).map((e) => e.getAttribute('data-b128-case')));
out.夹具规则覆盖 = out.夹具扫描.按规则计数;
out.夹具判定 = {
  注入条数: out.夹具注入.注入条数,
  命中条数: out.夹具扫描.命中.filter((h) => h.是注入夹具).length,
  命中规则: out.夹具扫描.按规则计数.map(([r]) => r),
  未被任何规则命中的case: out.夹具命中case.filter((c) => {
    const want = { 'aria-plural': ['ICU_plural'], 'aria-select': ['ICU_select'], 'printf': ['printf_s_d'],
      'undefined': ['undefined'], 'handlebars': ['handlebars残留'], 'fffd': ['替换字符U+FFFD'], '数据属性': ['ICU_单花括号标识符'] }[c] || [];
    return !want.some((r) => out.夹具规则覆盖.some(([rule, n]) => rule === r && n > 0));
  }),
};
log('  夹具判定：', JSON.stringify(out.夹具判定));
save();

// ---- ② 立刻移除夹具，确认回到 0 命中（也证明命中不是残留） ----
out.移除夹具 = await p.evaluate(() => { const n = document.querySelectorAll('[data-b128-fixture]').length;
  document.querySelectorAll('[data-b128-fixture]').forEach((e) => e.remove());
  return { 移除前个数: n, 移除后残留: document.querySelectorAll('[data-b128-fixture]').length }; });
out.移除后扫描 = await SWEEP('移除夹具后');
log('\n=== ② 移除夹具 ===\n  ', JSON.stringify(out.移除夹具), '｜重扫命中：', out.移除后扫描.命中数, JSON.stringify(out.移除后扫描.按规则计数));
save();

// ---- ③ 扩面：左栏面板 / 缩放菜单 / 快捷键抽屉 ----
async function clickAt(sel, note) {
  const pt = await p.evaluate((s) => { const e = document.querySelector(s); if (!e) return { __err: 'not-found' };
    const r = e.getBoundingClientRect(); if (r.width < 1) return { __err: 'zero-size' };
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
      const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 命中: h.tagName }; }
    return { __err: 'no-point' }; }, sel);
  if (pt.__err) { log(`  ⛔ ${note} 点不到：`, JSON.stringify(pt)); return pt; }
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1700);
  return { ok: true, 落点: pt };
}
const closeAll = async () => { for (let i = 0; i < 3; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(1000); } };

out.扩面 = {};
log('\n=== ③ 扩面扫描 ===');
const simple = [
  ['缩放菜单', '[data-testid="canvas-zoom-percent"]'],
  ['小地图', '[data-testid="canvas-display-toggle-minimap"]'],
  ['资产库', '[aria-label="资产库"]'],
  ['主体面板', '[aria-label="主体"]'],
  ['时间线', '[aria-label="时间线"]'],
  ['导演台', '[aria-label="导演台"]'],
];
for (const [name, sel] of simple) {
  const opened = await clickAt(sel, name);
  const sw = await SWEEP(name);
  out.扩面[name] = { 打开: opened, 命中: sw.命中数, 规则: sw.按规则计数,
    命中明细: sw.命中.filter((h) => h.屏上有面积).map((h) => ({ 规则: h.规则, 位置: h.位置, 值: h.值, tag: h.tag, testid: h.testid, 矩形: h.矩形 })) };
  log(`  【${name}】打开=${JSON.stringify(opened)}｜命中 ${sw.命中数} ${JSON.stringify(sw.按规则计数)}`);
  sw.命中.filter((h) => h.屏上有面积).forEach((h) => log(`      · [${h.规则}] <${h.tag}> ${h.testid ? 'tid=' + h.testid : ''} @${h.位置} «${h.值}»`));
  save();
  await closeAll();
  // 小地图已知 Esc 关不掉 ⇒ 再点一次它的按钮
  if ((await overlays()) > 0) { await clickAt('[data-testid="canvas-display-toggle-minimap"]', '小地图再点'); await p.waitForTimeout(900); }
  out.扩面[name].关闭后浮层 = await overlays();
  log(`      关闭后浮层：${out.扩面[name].关闭后浮层}`);
  save();
}

// 快捷键抽屉：用户菜单 → 快捷键（两级点击，都是打开型）
const um = await clickAt('[data-testid="canvas-user-menu-trigger"]', '用户菜单');
if (um.ok) {
  const kb = await clickAt('button[aria-label="快捷键"], [data-testid="canvas-user-menu-shortcuts"], [role=menuitem]:has-text("快捷键")', '快捷键项');
  const sw = await SWEEP('快捷键抽屉');
  out.扩面['快捷键抽屉'] = { 用户菜单: um, 快捷键项: kb, 命中: sw.命中数, 规则: sw.按规则计数,
    元素总数: sw.元素总数,
    命中明细: sw.命中.filter((h) => h.屏上有面积).map((h) => ({ 规则: h.规则, 位置: h.位置, 值: h.值, tag: h.tag })) };
  log(`  【快捷键抽屉】用户菜单=${JSON.stringify(um.ok)} 快捷键=${JSON.stringify(kb.ok || kb)}｜元素 ${sw.元素总数}｜命中 ${sw.命中数} ${JSON.stringify(sw.按规则计数)}`);
  sw.命中.filter((h) => h.屏上有面积).forEach((h) => log(`      · [${h.规则}] <${h.tag}> @${h.位置} «${h.值}»`));
  save();
  await closeAll();
  out.扩面['快捷键抽屉'].关闭后浮层 = await overlays();
  log(`      关闭后浮层：${out.扩面['快捷键抽屉'].关闭后浮层}`);
}
save();

// ---- 收尾 ----
out.收尾 = { 浮层: await overlays(), 夹具残留: await p.evaluate(() => document.querySelectorAll('[data-b128-fixture]').length),
  选中: await sel(), zoom1: await zoom(), credits: await credits(), status: await status() };
await p.waitForTimeout(1200);
out.收尾.zoom2 = await zoom();
log('\n收尾：', JSON.stringify(out.收尾));
save();
log('\nDONE b');
process.exit(0);
