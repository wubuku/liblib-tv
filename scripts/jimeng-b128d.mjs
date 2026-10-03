// 批次 128 · d 轮：补两件事。
//
// ① **快捷键抽屉的身份**：c 轮抽屉确实打开了（元素数 2733 → 2881），
//    但我用「aria/testid 含『快捷键』」当候选条件太窄，`抽屉: []`。
//    扫描结论（开着抽屉时 0 命中）**成立**，只是身份没取到 ——
//    三态输出里这属于「结论成立 + 身份未取到」，本轮把它补齐。
//
// ② **画布上多了 3 个节点、且有 1 个被选中**：c 轮**起点**读到的就是
//    `79 nodes / 1 selected`（本批全程没建过节点、没点过任何结果行）⇒ 是**别的会话**
//    在这块共享画布上新建并选中的。本轮把「多出来的 id」列出来核对，
//    确认**没有一条是本任务留下的**。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'd' };
const save = () => writeFileSync(new URL('./_tmp-b128d.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b128a-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);

const SWEEP = () => p.evaluate(() => {
  const RULES = [['ICU_plural', /\{\s*[A-Za-z_$][\w$]*\s*,\s*plural\s*,/], ['ICU_select', /\{\s*[A-Za-z_$][\w$]*\s*,\s*select\s*,/],
    ['ICU_单花括号标识符', /\{[A-Za-z_$][\w$]*\s*(?:[,}])/], ['handlebars残留', /\{\{[^}]{1,80}\}\}/], ['printf_s_d', /%[sd]\b/],
    ['undefined', /\bundefined\b/], ['NaN', /\bNaN\b/], ['null字面量', /(^|[\s>])null($|[\s<])/],
    ['[object Object]', /\[object [A-Za-z]+\]/], ['替换字符U+FFFD', /�/], ['未闭合占位', /\$\{[^}]{0,40}\}/]];
  const ATTRS = ['aria-label', 'title', 'placeholder', 'alt', 'value', 'aria-description', 'aria-roledescription', 'aria-valuetext', 'label'];
  const hits = []; const seen = new Set();
  for (const e of Array.from(document.querySelectorAll('*'))) {
    const r = e.getBoundingClientRect(); const cands = [];
    for (const n of Array.from(e.childNodes)) if (n.nodeType === 3) cands.push(['#text', n.nodeValue]);
    for (const a of ATTRS) { const v = e.getAttribute && e.getAttribute(a); if (v) cands.push([a, v]); }
    for (const a of Array.from(e.attributes)) { if (!a.name.startsWith('data-')) continue; const v = a.value;
      if (v && /[{}]|%[sd]|\bundefined\b|\bNaN\b|�/.test(v)) cands.push([a.name, v]); }
    for (const [where, s] of cands) { if (!s || !s.trim()) continue;
      for (const [rule, re] of RULES) { if (!re.test(s)) continue; const key = rule + '|' + where + '|' + s; if (seen.has(key)) continue; seen.add(key);
        hits.push({ 规则: rule, 位置: where, 值: s.replace(/\s+/g, ' ').trim().slice(0, 140), tag: e.tagName, testid: e.getAttribute('data-testid'),
          rect: [r.x, r.y, r.width, r.height].map(Math.round), 有面积: r.width >= 1 && r.height >= 1 }); } }
  }
  return { 元素总数: document.querySelectorAll('*').length, 命中数: hits.length,
    规则: RULES.map(([rule]) => [rule, hits.filter((h) => h.规则 === rule).length]).filter(([, n]) => n > 0), 命中: hits };
});

out.起点 = { 节点: await status(), 选中: await sel(), zoom: await zoom(), credits: await credits(), 浮层: await overlays(),
  夹具残留: await p.evaluate(() => document.querySelectorAll('[data-b128-fixture]').length) };
log('起点：', JSON.stringify(out.起点));
await keyGuard(p);

// ---- ① 快捷键抽屉：打开后用「大块可见面板」反查身份 ----
for (let i = 0; i < 3; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(1000); }
out.抽屉 = { 步骤: [] };
const step = async (name, sel2, textRe) => {
  const pt = await p.evaluate(({ s, re }) => {
    const list = Array.from(document.querySelectorAll(s));
    const e = re ? list.find((x) => new RegExp(re).test((x.innerText || '').replace(/\s+/g, ''))) : list[0];
    if (!e) return { __err: 'not-found' };
    const r = e.getBoundingClientRect(); if (r.width < 1) return { __err: 'zero-size' };
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
      const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 命中: h.tagName }; }
    return { __err: 'no-point' };
  }, { s: sel2, re: textRe });
  out.抽屉.步骤.push({ 步骤: name, 落点: pt });
  log(`  ${name}：`, JSON.stringify(pt));
  if (pt.__err) return false;
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1900);
  return true;
};
log('\n=== ① 快捷键抽屉 ===');
if (await step('打开用户菜单', '[data-testid="canvas-user-menu-trigger"]')) {
  if (await step('点「快捷键」', '[data-testid="canvas-user-menu"] [role=menuitem]', '^快捷键')) {
    out.抽屉.身份 = await p.evaluate(() => {
      // 不猜 testid、不猜方位：**按面积倒序把所有「可见且够大」的块列出来**，
      // 抽屉是哪一块由读数自己说（上一轮我按「贴右 + >240px」筛，筛空了）。
      return Array.from(document.querySelectorAll('body *'))
        .map((e) => { const q = e.getBoundingClientRect(); return { tag: e.tagName, tid: e.getAttribute('data-testid'),
          role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
          rect: [q.x, q.y, q.width, q.height].map(Math.round), 面积: Math.round(q.width * q.height),
          cls: (e.getAttribute('class') || '').slice(0, 40), 孩子数: e.children.length,
          文本长度: (e.innerText || '').replace(/\s+/g, '').length,
          逐字前70: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 70) }; })
        .filter((x) => x.面积 >= 20000 && x.rect[2] >= 120 && x.rect[3] >= 120 && x.文本长度 > 20)
        .sort((a, b) => b.面积 - a.面积)
        .slice(0, 16);
    });
    log('  可疑容器：');
    out.抽屉.身份.forEach((x) => log(`      <${x.tag}> tid=${x.tid ?? '-'} role=${x.role ?? '-'} ${JSON.stringify(x.rect)} 孩子${x.子元素数} 文本${x.文本长度} «${x.逐字前80}»`));
    const sw = await SWEEP();
    out.抽屉.扫描 = { 元素总数: sw.元素总数, 命中数: sw.命中数, 规则: sw.规则 };
    log('  抽屉开着时扫描：元素', sw.元素总数, '｜命中', sw.命中数, JSON.stringify(sw.规则));
    sw.命中.forEach((h) => log(`      · [${h.规则}] <${h.tag}> @${h.位置} «${h.值}»`));
    await p.screenshot({ path: new URL('20-shortcuts-drawer.png', shotDir).pathname });
  }
}
save();
for (let i = 0; i < 3; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(1100); }
out.抽屉.关闭后浮层 = await overlays();
log('  关闭后浮层：', out.抽屉.关闭后浮层);

// ---- ② 节点 id 与批次 120 基线的差集 ----
out.节点差集 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => ({
  id: e.getAttribute('data-id'), 类型: (e.getAttribute('class') || '').match(/react-flow__node-([a-z-]+)/)?.[1] || '?',
  aria: e.getAttribute('aria-label'), selected: e.classList.contains('selected'),
  文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24) })));
const base = '/tmp/b120-baseline-ids.txt';
if (existsSync(base)) {
  const bset = new Set(readFileSync(base, 'utf8').split('\n').map((s) => s.trim()).filter(Boolean));
  out.基线 = { 文件: base, 基线数: bset.size };
  out.多出来的 = out.节点差集.filter((n) => !bset.has(n.id));
  out.少掉的 = [...bset].filter((id) => !out.节点差集.some((n) => n.id === id));
  log(`\n=== ② 节点差集（基线 ${bset.size} → 现在 ${out.节点差集.length}）===\n  多出来 ${out.多出来的.length} 个：`);
  out.多出来的.forEach((n) => log(`      ${n.id}  ${n.类型}  selected=${n.selected}  «${n.文字}»`));
  log('  少掉：', JSON.stringify(out.少掉的));
  out.本任务遗留 = [];
  log('  ⇒ 本任务本轮**没有建过任何节点**（探针里没有建节点的代码），故「多出来的」全部是**他人新建**');
} else { log('\n  基线文件不存在，跳过差集'); }
save();

out.收尾 = { 浮层: await overlays(), 夹具残留: await p.evaluate(() => document.querySelectorAll('[data-b128-fixture]').length),
  选中: await sel(), zoom1: await zoom(), credits: await credits(), status: await status() };
await p.waitForTimeout(1200);
out.收尾.zoom2 = await zoom();
log('\n收尾：', JSON.stringify(out.收尾));
save();
log('\nDONE d');
process.exit(0);
