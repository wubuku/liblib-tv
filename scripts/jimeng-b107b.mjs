// 批次 107 · b 轮：把 **⌘ ⌥ 3（三级标题）** 从「面板声明」升级成「实测结论」。
//
// 🎯 `help-and-shortcuts.md` 快捷键表里那一行逐字是：
//   | 文本 | **三级标题** | **⌘ ⌥ 3** | 🔴 **未验证** | 面板声明了、本页全表照抄了，
//     但**没有任何实测结论** |
// 它也是 `scripts/jimeng-shortcut-reconcile.mjs` 唯一标记为
// 「除照抄全表外正文找不到任何结论」的那一项。
//
// 素材：上传 `/tmp/jimeng-b107-h3.md` 建的**文本节点**（批次 102 证明 `.md` 上传免费），
// 正文四行：`一级标题行 / 二级标题行 / 三级标题行 / 普通正文行。`
// ⇒ **四级都有样本**，可以直接对比「按完之后那一行变成了什么」。
//
// ⚠️ 全程只做**本轮自建节点**（`node_gmvz7secas`）上的操作，
//    **不碰画布上任何别人的节点**。
//
// 🔴 判据要点（批次 105/106 连撞两次同类坑之后立的）：
//   「⌘⌥3 生效了」的判据**必须落在那一行自己的渲染结果上**
//   （标签名 / class / 字号），**不能**用「innerText 变了」——
//   文字本来就在那儿，innerText 永远不变。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), selfId: 'node_gmvz7secas' };
const SELF = out.selfId;
const save = () => writeFileSync(new URL('./_tmp-b107b.json', import.meta.url), JSON.stringify(out, null, 1));

const safeEval = async (fn, arg, tries = 8) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

// 节点是否还选中
const isSel = () => p.evaluate((i) => { const e = document.querySelector(`.react-flow__node[data-id="${i}"]`); return e ? e.classList.contains('selected') : null; }, SELF);

out.sel0 = await isSel();
log('文本节点 selected =', out.sel0);
if (!out.sel0) { log('🔴 没选中，先点一下（第四道护栏）');
  const c = await safeEval((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
    const r = n.getBoundingClientRect();
    const others = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => e.getAttribute('data-id') !== i)
      .map((e) => { const q = e.getBoundingClientRect(); return { x: q.x, y: q.y, w: q.width, h: q.height }; });
    for (let fy = 0.2; fy <= 0.5; fy += 0.1) for (let fx = 0.2; fx <= 0.8; fx += 0.1) {
      const x = r.x + r.width * fx, y = r.y + r.height * fy;
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y);
      if (!el || !(el === n || n.contains(el))) continue;
      if (others.some((o) => x >= o.x && x <= o.x + o.w && y >= o.y && y <= o.y + o.h)) continue;
      return { x: Math.round(x), y: Math.round(y) };
    }
    return { __err: 'no-safe-spot' };
  }, SELF);
  log('  落点：', JSON.stringify(c));
  if (!c.__err) { await p.mouse.move(c.x, c.y); await p.waitForTimeout(400); await p.mouse.click(c.x, c.y); await p.waitForTimeout(1000); }
  out.sel1 = await isSel(); log('  点后 selected =', out.sel1);
}

// ---- 按 F 开全屏文本编辑器 ----
const g1 = await keyGuard(p);
log('\nkeyGuard（按 f 前）：', JSON.stringify(g1));
if (!g1.safe) { log('🔴 焦点不安全，不按'); save(); await b.close(); process.exit(1); }
out.guardF = g1;
await p.keyboard.press('f');
await p.waitForTimeout(1800);

out.dialog = await safeEval(() => {
  const d = document.querySelector('[data-testid="text-editor-fullscreen-dialog"]') ||
    Array.from(document.querySelectorAll('div,section')).find((e) => /fullscreen/i.test(e.getAttribute('data-testid') || ''));
  if (!d) return { found: false };
  const r = d.getBoundingClientRect();
  const ce = Array.from(d.querySelectorAll('[contenteditable],textarea,input')).map((e) => {
    const q = e.getBoundingClientRect();
    return { tag: e.tagName, tid: e.getAttribute('data-testid'), ce: e.getAttribute('contenteditable'),
      w: Math.round(q.width), h: Math.round(q.height), x: Math.round(q.x), y: Math.round(q.y),
      text: (e.innerText || e.value || '').replace(/\s+/g, ' ').trim().slice(0, 120) };
  });
  return { found: true, box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`, ce,
    active: (() => { const a = document.activeElement; return a ? `${a.tagName}[${a.getAttribute('data-testid') || ''}]` : null; })(),
    structure: Array.from(d.querySelectorAll('h1,h2,h3,h4,p,li,strong,em,u,s')).slice(0, 20)
      .map((e) => ({ tag: e.tagName, cls: (e.className || '').toString().slice(0, 50), t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) })) };
});
log('\n全屏编辑器：', JSON.stringify(out.dialog, null, 1));
save();
