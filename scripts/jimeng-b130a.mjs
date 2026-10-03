// 批次 130 · a 轮：**回溯审计「有面积」这条判据** —— 它被立成了规，但已被批次 129 证伪一次。
//
// 🔑 靶子：`30-concepts.md:2182` 立了规「**数浮层要用「有面积」过滤**
//   （`getBoundingClientRect().width > 1`）」，理由是「关掉但没卸载的弹层节点仍留在 DOM 里」。
//   批次 129 抓到 `canvas-feature-sidecar`：`200×348` 的**非零矩形**，
//   但 `opacity:0` + `pointer-events:none` + `scale(0.5)` + **零子元素** ⇒ **完全不可见**。
//   ⇒ 那条规**滤得掉「零尺寸残留」，滤不掉「非零尺寸但不可见」**。本轮量化漏了多少。
//
// 📌 技术要点（容易写错）：**只看元素自身不够**。
//   `opacity` **不继承**（`visibility` 继承）—— 父级 `opacity:0` 时子级算出的 computed opacity 仍是 1，
//   但视觉上一样不可见。所以正确判据要**沿祖先链把 opacity 连乘**、把 visibility 取交集。
//   本轮把「自身判据」与「祖先链判据」都算一遍，看差多少 —— 这正是历史上那 6 类结论用的那一档。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b130a.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);
const idsNow = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());

out.start = { 状态行: await status(), 选中: await sel(), zoom: await zoom(), 浮层: await overlays() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
for (let i = 0; i < 2; i++) { if (await overlays()) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); } }
out.起始id = await idsNow();

// ---- 双计数器：旧判据 vs 祖先链判据 ----
const scan = () => p.evaluate(() => {
  const all = Array.from(document.querySelectorAll('*'));
  const 自身可见 = (e) => {
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    if (parseFloat(cs.opacity) < 0.01) return false;
    const r = e.getBoundingClientRect();
    return r.width >= 1 && r.height >= 1;
  };
  const 链可见 = (e) => {
    let node = e, op = 1, vis = true, pe = true;
    while (node && node.nodeType === 1) {
      const cs = getComputedStyle(node);
      if (cs.display === 'none') return false;
      if (cs.visibility === 'hidden' || cs.visibility === 'collapse') vis = false;
      op *= parseFloat(cs.opacity);
      if (cs.pointerEvents === 'none') pe = false;
      node = node.parentElement;
    }
    if (op < 0.01 || !vis) return false;
    const r = e.getBoundingClientRect();
    return r.width >= 1 && r.height >= 1;
  };
  const 旧判据 = all.filter((e) => { const r = e.getBoundingClientRect(); return r.width > 1; });
  const 新判据 = all.filter(链可见);
  const 差集 = 旧判据.filter((e) => !新判据.includes(e));
  const 指纹 = (e) => {
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    const 宿主链 = [];
    for (let n = e; n && n.nodeType === 1 && 宿主链.length < 5; n = n.parentElement)
      宿主链.push(n.getAttribute('data-testid') || n.tagName.toLowerCase() + (n.className && typeof n.className === 'string' ? '.' + n.className.split(/\s+/)[0] : ''));
    return { testid: e.getAttribute('data-testid'), tag: e.tagName, role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
      矩形: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      自身: { display: cs.display, visibility: cs.visibility, opacity: cs.opacity, pe: cs.pointerEvents },
      祖先链: 宿主链, 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24) };
  };
  return {
    元素总数: all.length, 旧判据命中: 旧判据.length, 新判据命中: 新判据.length, 差集: 差集.length,
    差集明细: 差集.map(指纹),
    // 差集里有多少是「浮层」角色、有多少落在顶栏/左栏 —— 决定历史结论受不受影响
    差集里的浮层角色: 差集.filter((e) => ['dialog', 'menu', 'listbox', 'alertdialog'].includes(e.getAttribute('role'))).length,
    差集里在顶栏内的: 差集.filter((e) => !!e.closest('header,[data-testid="canvas-top-bar"]')).length,
    差集里在左栏导航内的: 差集.filter((e) => !!e.closest('[data-testid^="canvas-navigation"]')).length,
  };
});

log('\n=== ① 静态态：旧判据 vs 祖先链判据 ===');
out.静态 = await scan();
log(`  元素总数 ${out.静态.元素总数}`);
log(`  旧判据（width>1）命中: ${out.静态.旧判据命中}`);
log(`  新判据（沿祖先链）命中: ${out.静态.新判据命中}`);
log(`  🔑 差集（旧判据会多算）: ${out.静态.差集} 个`);
log(`     其中 role=dialog/menu/listbox 的: ${out.静态.差集里的浮层角色} ｜顶栏内: ${out.静态.差集里在顶栏内的} ｜左栏内: ${out.静态.差集里在左栏导航内的}`);
log('\n  差集明细（前 40 个）：');
out.静态.差集明细.slice(0, 40).forEach((e) => log(`      · ${e.testid || '(无 tid)'} <${e.tag}> ${e.role ? 'role=' + e.role : ''} ${e.矩形.join(',')} op=${e.自身.opacity} vis=${e.自身.visibility} pe=${e.自身.pe} «${e.文字}»  ⊂ ${e.祖先链.slice(0, 3).join(' < ')}`));
save();

// ---- 阳性对照：注入已知形态，证明确认分类器抓得到 ----
log('\n=== ② 阳性对照：注入 4 种已知形态，验证「差集」确实抓得到 ===');
await p.evaluate(() => {
  const mk = (st) => { const e = document.createElement('div');
    e.setAttribute('data-b130-fixture', st);
    e.style.cssText = 'position:fixed;left:400px;top:300px;width:50px;height:50px;background:#000;';
    if (st === 'opacity0') e.style.opacity = '0';
    if (st === 'visibility-hidden') e.style.visibility = 'hidden';
    if (st === 'zero-size') { e.style.width = '0px'; e.style.height = '0px'; }
    if (st === 'child-of-opacity0') { const par = document.createElement('div');
      par.style.cssText = 'position:fixed;left:500px;top:300px;width:50px;height:50px;opacity:0;';
      par.appendChild(e); e.style.cssText = 'width:50px;height:50px;background:#0f0;'; document.body.appendChild(par); return [par, e]; }
    document.body.appendChild(e); return [e];
  };
  window.__b130 = [].concat(mk('normal'), mk('opacity0'), mk('visibility-hidden'), mk('zero-size'), mk('child-of-opacity0'));
});
const probe = await p.evaluate(() => {
  const g = (st) => { const arr = Array.from(document.querySelectorAll('[data-b130-fixture="' + st + '"]')); return arr; };
  const r = (e) => { const q = e.getBoundingClientRect(); return [Math.round(q.width), Math.round(q.height)]; };
  const o = {};
  for (const st of ['normal', 'opacity0', 'visibility-hidden', 'zero-size', 'child-of-opacity0']) {
    const els = g(st);
    o[st] = els.map((e) => ({ 矩形: r(e), 旧判据: r(e)[0] > 1, 自身computedOpacity: getComputedStyle(e).opacity }));
  }
  return o;
});
out.阳性对照 = probe;
for (const [k, v] of Object.entries(probe)) log(`  ${k}: ${JSON.stringify(v)}`);
const 抓到了 = probe['opacity0'][0].旧判据 === true && probe['child-of-opacity0'][0].矩形[0] > 1
  && probe['zero-size'][0].旧判据 === false && probe['normal'][0].旧判据 === true;
out.阳性对照.通过 = 抓到了;
log('  🔑 阳性对照：旧判据**确实**把 opacity0 和「opacity0 的子元素」都算进去了（它只滤得掉零尺寸）：', 抓到了);
await p.evaluate(() => { (window.__b130 || []).forEach((e) => e.remove()); window.__b130 = null; });
out.夹具残留 = await p.evaluate(() => document.querySelectorAll('[data-b130-fixture]').length);
log('  夹具移除后残留：', out.夹具残留, '（应为 0）');
save();

// ---- 打开几个面板，看差集会变大多少 ----
log('\n=== ③ 打开面板后差集怎么变 ===');
const toggle = async (s, label) => {
  const pt = await p.evaluate((q) => { const e = document.querySelector(q); if (!e) return { __err: 'nf' };
    const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
    return { __err: 'np' }; }, s);
  if (pt.__err) { log(`  【${label}】⛔ ${pt.__err}`); return pt; }
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1600); return pt;
};
const escAll = async () => { for (let i = 0; i < 3; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(900); } };
out.面板 = {};
for (const [n, s] of [['搜索', '[data-testid="canvas-panel-launcher"][aria-label="搜索"]'],
  ['生成历史', '[data-testid="canvas-panel-launcher"][aria-label="生成历史"]'],
  ['用户菜单', '[data-testid="canvas-user-menu-trigger"]'],
  ['分享', '[data-testid="canvas-share-trigger"]']]) {
  const pt = await toggle(s, n);
  if (pt.__err) continue;
  const r = await scan();
  out.面板[n] = { 旧判据命中: r.旧判据命中, 新判据命中: r.新判据命中, 差集: r.差集,
    差集里的浮层角色: r.差集里的浮层角色, 差集明细: r.差集明细.slice(0, 12) };
  log(`  【${n}】旧 ${r.旧判据命中}｜新 ${r.新判据命中}｜🔑 差集 ${r.差集}（其中浮层角色 ${r.差集里的浮层角色}）`);
  r.差集明细.slice(0, 8).forEach((e) => log(`      · ${e.testid || '(无 tid)'} <${e.tag}> ${e.矩形.join(',')} op=${e.自身.opacity} ⊂ ${e.祖先链.slice(0, 2).join(' < ')}`));
  save();
  await escAll();
}

await p.mouse.move(1276, 716); await p.waitForTimeout(600);
const endIds = await idsNow();
out.收尾 = { 选中: await sel(), 状态行: await status(), 浮层: await overlays(), zoom: await zoom(), 节点数: endIds.length, 起始节点数: out.起始id.length };
out.新增id = endIds.filter((x) => !out.起始id.includes(x));
log('\n收尾：', JSON.stringify(out.收尾));
log('  新增 id（必须空）：', JSON.stringify(out.新增id), '｜夹具残留', out.夹具残留);
save();
log('\nDONE a');
process.exit(0);
