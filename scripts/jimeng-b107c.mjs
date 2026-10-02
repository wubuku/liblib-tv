// 批次 107 · c 轮：打开文本编辑器，把 **⌘⌥1 / ⌘⌥2 / ⌘⌥3 / ⌘⌥0** 一次测全。
//
// b 轮：`keyGuard` 放行（焦点 BODY、0 个可见输入面），按 `f` 之后
//   `[data-testid="text-editor-fullscreen-dialog"]` **没出现**，节点仍是 selected。
//   ⇒ 本轮改走节点自己的**编辑按钮** `canvas-editor-menu`（36×36，本地动作、不耗积分），
//   并且把「按 F 是否能开」**单独记一条观测**，不混进「标题有没有生效」里。
//
// 🔴 判据（本批最重要的一条，沿用批次 105/106 的教训）：
//   **不能**用「innerText 变了」判 —— 文字本来就在那儿，innerText 永远不变。
//   **不能**用「页面上有没有出现 h1/h2/h3 标签」判 —— 要看**目标那一行**的渲染结果。
//   本轮判据 = **目标行的标签名 + class + 字号**，逐次记录。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), selfId: 'node_gmvz7secas' };
const SELF = out.selfId;
const save = () => writeFileSync(new URL('./_tmp-b107c.json', import.meta.url), JSON.stringify(out, null, 1));

const safeEval = async (fn, arg, tries = 8) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

// 编辑器打开没打开：按**是否有可见的 contenteditable / 大尺寸浮层**判
const editorState = () => p.evaluate(() => {
  const ce = Array.from(document.querySelectorAll('[contenteditable="true"],textarea'))
    .map((e) => { const q = e.getBoundingClientRect();
      return { tag: e.tagName, tid: e.getAttribute('data-testid'), cls: (e.className || '').toString().slice(0, 40),
        w: Math.round(q.width), h: Math.round(q.height), x: Math.round(q.x), y: Math.round(q.y) }; })
    .filter((x) => x.w > 40 && x.h > 20);
  const big = Array.from(document.querySelectorAll('div,section'))
    .map((e) => { const q = e.getBoundingClientRect();
      return { tid: e.getAttribute('data-testid'), role: e.getAttribute('role'), w: Math.round(q.width), h: Math.round(q.height) }; })
    .filter((x) => x.w >= 900 && x.h >= 500 && getComputedStyle(document.querySelector(`[data-testid="${x.tid}"]`) || document.body).visibility !== 'hidden');
  const a = document.activeElement;
  return { ce, big, active: a ? `${a.tagName}[${a.getAttribute('data-testid') || ''}] ce=${a.isContentEditable}` : null };
});

// 编辑器里**逐行**读渲染结果（这才是判据）
const readLines = () => p.evaluate(() => {
  const host = Array.from(document.querySelectorAll('[contenteditable="true"],textarea'))
    .filter((e) => e.getBoundingClientRect().width > 40)[0];
  if (!host) return { __err: 'no-editor' };
  const walk = [];
  const src = host.querySelectorAll ? host.querySelectorAll('*') : [];
  for (const e of src) {
    if (['H1','H2','H3','H4','P','LI','STRONG','EM','U','S','DIV','SPAN'].includes(e.tagName)) {
      const cs = getComputedStyle(e);
      walk.push({ tag: e.tagName, cls: (e.className || '').toString().slice(0, 44),
        fs: cs.fontSize, fw: cs.fontWeight, t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24) });
    }
  }
  return { hostTag: host.tagName, hostCls: (host.className || '').toString().slice(0, 60),
    hostHTML: (host.innerHTML || '').replace(/\s+/g, ' ').slice(0, 400), n: walk.length, walk: walk.slice(0, 24) };
});

out.before = await editorState();
log('开编辑器前：', JSON.stringify(out.before));

// ---- 用节点自己的编辑按钮打开 ----
const eb = await safeEval((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  // 优先找节点内部的 canvas-editor-menu；找不到再看它是不是在节点旁的工具条里
  let e = n.querySelector('[data-testid="canvas-editor-menu"]');
  let owner = 'inside-node';
  if (!e) { e = document.querySelector('[data-testid="canvas-editor-menu"]');
    owner = e && n.contains(e) ? 'inside-node' : (e ? 'elsewhere' : null); }
  if (!e) return { __err: 'no-editor-button' };
  const r = e.getBoundingClientRect();
  return { tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), owner,
    x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), w: Math.round(r.width), h: Math.round(r.height) };
}, SELF);
out.editorBtn = eb;
log('\n编辑按钮：', JSON.stringify(eb));
if (eb && !eb.__err) {
  await p.mouse.move(eb.x, eb.y); await p.waitForTimeout(450);
  await p.mouse.click(eb.x, eb.y);
  await p.waitForTimeout(2000);
}
out.afterOpen = await editorState();
log('点完编辑按钮：', JSON.stringify(out.afterOpen, null, 1));
out.opened = out.afterOpen.ce.length > 0;
log('编辑器打开 =', out.opened ? '✅' : '🔴');
save();

if (!out.opened) { log('🔴 编辑器没开，停止（不拿错状态写结论）'); save(); await b.close(); process.exit(1); }

out.base = await readLines();
log('\n编辑器基线（未按任何快捷键）：', JSON.stringify(out.base, null, 1));
save();
