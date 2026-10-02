// 批次 107 · g 轮：把 **⌘⌥1 / ⌘⌥2 / ⌘⌥3 / ⌘⌥0** 逐个测全（判据终于挂对了地方）。
//
// 🔴 e/f 两轮为什么全灭（**判据，不是产品**）：
//   我一直在 `.react-flow__node[data-id=…]` **里面**找 `[contenteditable]` ——
//   而文本编辑态的**可编辑面与工具条都不在节点 DOM 里**：
//     · 可编辑面 = **`DIV.tiptap.ProseMirror`**（`192×116`，`contenteditable`，
//       **焦点就在它上面**），它在画布层的另一个挂载点里；
//     · 工具条 = `[data-testid="text-editor-toolbar"]` **`316×40@482,236`**，
//       父元素是 `DIV[text-editor-toolbar-boundary]` —— **同样是 portal 出来的浮层**。
//   ⇒ 节点内 `ce: []` 恒成立，而**编辑器明明开着**。
//   📌 这和批次 106 的「浮层不一定挂在 body 下」是同一条的加强版：
//   **portal 出来的东西，连「属于哪个逻辑容器」都不体现在 DOM 树上。**
//
// 🔑 顺带一条大发现：**文本编辑器是 TipTap / ProseMirror**
//   （`class="tiptap ProseMirror …"`），正文直接是真语义标签
//   `H1 / H2 / H3 / P` —— 这解释了为什么 ⌘⌥1/2/3/0 这组键存在，
//   也给了「层级」一个**不靠肉眼**的判据。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString() };
const save = () => writeFileSync(new URL('./_tmp-b107g.json', import.meta.url), JSON.stringify(out, null, 1));

// 编辑器挂在全局，不在节点里
const ed = () => p.evaluate(() => {
  const e = document.querySelector('.tiptap.ProseMirror') ||
    Array.from(document.querySelectorAll('[contenteditable="true"]')).find((x) => x.getBoundingClientRect().width > 30);
  if (!e) return { __err: 'no-editor' };
  const q = e.getBoundingClientRect();
  return { tag: e.tagName, cls: (e.className || '').toString().slice(0, 60),
    box: `${Math.round(q.x)},${Math.round(q.y)} ${Math.round(q.width)}×${Math.round(q.height)}`,
    focused: e === document.activeElement, ce: e.getAttribute('contenteditable'),
    html: (e.innerHTML || '').replace(/\s+/g, ' ').slice(0, 500),
    tags: Array.from(new Set(Array.from(e.querySelectorAll('*')).map((x) => x.tagName))),
    lines: Array.from(e.children).map((c) => { const cs = getComputedStyle(c);
      return { tag: c.tagName, cls: (c.className || '').toString().slice(0, 40), fs: cs.fontSize, fw: cs.fontWeight,
        t: (c.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) }; }) };
});

// 目标行「普通正文行。」的渲染读数 + 屏幕位置
const line = () => p.evaluate(() => {
  const host = document.querySelector('.tiptap.ProseMirror') ||
    Array.from(document.querySelectorAll('[contenteditable="true"]')).find((x) => x.getBoundingClientRect().width > 30);
  if (!host) return { __err: 'no-editor' };
  let hit = null;
  for (const e of [host, ...Array.from(host.querySelectorAll('*'))]) {
    const t = (e.innerText || ''); if (t.includes('普通正文行')) { if (!hit || e.contains(hit)) hit = e; }
  }
  if (!hit) return { __err: 'target-not-found' };
  const cs = getComputedStyle(hit); const q = hit.getBoundingClientRect();
  return { tag: hit.tagName, cls: (hit.className || '').toString().slice(0, 60), fs: cs.fontSize, fw: cs.fontWeight,
    box: `${Math.round(q.width)}×${Math.round(q.height)}`, x: Math.round(q.x + q.width / 2), y: Math.round(q.y + q.height / 2),
    html: hit.outerHTML.replace(/\s+/g, ' ').slice(0, 200) };
});

out.e0 = await ed();
log('编辑器：', JSON.stringify(out.e0, null, 1));
if (out.e0.__err) { log('🔴 编辑器没开'); save(); await b.close(); process.exit(1); }

out.base = await line();
log('\n目标行基线：', JSON.stringify(out.base, null, 1));
save();

out.steps = [];
for (const [key, label, combo] of [['h1', '一级标题', 'Meta+Alt+1'], ['h2', '二级标题', 'Meta+Alt+2'],
                                   ['h3', '三级标题', 'Meta+Alt+3'], ['p', '普通文本', 'Meta+Alt+0']]) {
  const cur = await line();
  if (cur.__err) { out.steps.push({ key, label, err: cur.__err }); save(); continue; }
  await p.mouse.click(cur.x, cur.y); await p.waitForTimeout(850);      // 每次重新落光标
  const g = await keyGuard(p);
  log(`\n>>> ${label}：按 ${combo} ｜ keyGuard ${g.safe ? '放行' : '拒绝'}（${g.where}）`);
  if (!g.safe) { out.steps.push({ key, label, refused: g.reason }); save(); continue; }
  const before = await line();
  await p.keyboard.press(combo);
  await p.waitForTimeout(1300);
  const after = await line();
  const sig = (x) => x && !x.__err ? `${x.tag}|${x.cls}|${x.fs}|${x.fw}|${x.box}` : 'ERR';
  const rec = { key, label, combo, guard: g.where, beforeSig: sig(before), afterSig: sig(after),
    before: { tag: before.tag, cls: before.cls, fs: before.fs, fw: before.fw, box: before.box, html: before.html },
    after: { tag: after.tag, cls: after.cls, fs: after.fs, fw: after.fw, box: after.box, html: after.html },
    changed: sig(before) !== sig(after) };
  out.steps.push(rec);
  log('   前：', rec.beforeSig);
  log('   后：', rec.afterSig);
  log('   变了 =', rec.changed ? '✅' : '🔴 无变化');
  if (rec.changed) log('   前 HTML：', rec.before.html, '\n   后 HTML：', rec.after.html);
  save();
}

out.final = await ed();
log('\n最后编辑器全文 HTML：', out.final.html);
log('四行读数：', JSON.stringify(out.final.lines, null, 1));
out.h3 = out.steps.find((s) => s.key === 'h3');
log('\n⌘⌥3 结论：', out.h3 ? (out.h3.changed ? `✅ 生效：${out.h3.beforeSig} → ${out.h3.afterSig}` : `🔴 无变化（${out.h3.beforeSig}）`) : '未测到');
save();
await b.close();
