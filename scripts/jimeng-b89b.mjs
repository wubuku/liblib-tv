// 批次 89 · B：诊断 P1 面板未出现 + 追「外部 1」的机制 + 重做 P3 普查。
//
// ⚠️ **自伤①（P1）**：探针记「面板未找到」时**必须立刻分辨是「没找到」还是「没等够 / 点歪了」**。
//     a 轮直接记 VOID 是对的（不记「不存在」），但 VOID 本身不解释原因 ——
//     所以 b 轮把点击后的真实 DOM 快照下来。
//
// 🔑 **P2 样本里的意外线索**：`node_pxvkay973v`（导演台）的 aria 逐字是
//     **`外部 node: 导演台`**，不是「导演台 node: …」。
//     而批次 83 记下过一个至今未解的悬案：节点汇总面板里多出一类逐字「**外部 1**」，
//     与五种媒体类型并列，机制未查明。
//     ⇒ 可证伪预测 **P2b**：汇总面板的「外部」类 = **aria 以「外部 node:」开头的节点数**，
//       当前应当恰好 1（只有导演台 1）。
//     若成立 ⇒ 那个悬案有解了，而且**不是面板的毛病，是 aria 的命名**。
//
// 🔑 **P3 重做（自伤②）**：a 轮把 testid 的签名写成 `标签|class|宽×高`，
//     于是 `flow-node-title` 因为**标题文字长度不同**就裂成 13 种 ——
//     **那不是语义不同，那是量错了东西**（正是本页批次 65/1276 记的病）。
//     修正：结构签名只留 `(标签, class)`，**完全不看尺寸**；尺寸差异另行核对。
//
// ⚠️ **自伤③（写脚本时的）**：用 python 批量替换 JS 源码里的 `p.evaluate(() => {`
//     注入辅助函数时，把行尾注释和**同一行后面的原代码**挤在了一起 ——
//     `// ⚠️ xxx` 会把 `const e = document.querySelector(...)` 整句注释掉。
//     ⇒ 教训：**注入注释必须自带换行**；批量改 JS 源码后先 `node --check`。
// ⚠️ **自伤④**：`R` 这类在 Node 侧定义的取整函数在 `page.evaluate` 体内**不可见**，
//     本批因此连踩两次（a 轮一次、改完 b 轮又一次）。每个 evaluate 都要自足。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };

const selCount = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = async () => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-commerce-entry"]');
  return e ? e.getAttribute('aria-label') : null;
});
const status = async () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
out.start = { sel: await selCount(), credits: await credits(), status: await status() };

// ═════════ D1：为什么面板没出现？把点击后的真实 DOM 快照下来 ═════════
const trig = 'button[aria-label^="Canvas node summary"]';
out.d1 = {};
out.d1.trigger = await p.evaluate((s) => {
  const e = document.querySelector(s);
  if (!e) return { found: false };
  const r = e.getBoundingClientRect();
  return { found: true, tag: e.tagName, tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
    box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    pe: getComputedStyle(e).pointerEvents, vis: getComputedStyle(e).visibility, disabled: e.disabled };
}, trig);
log('D1 触发器：', JSON.stringify(out.d1.trigger));

await p.click(trig);
await p.waitForTimeout(1600);
out.d1.after1600 = await p.evaluate(() => ({
  summaryPopover: !!document.querySelector('[data-testid="canvas-node-summary-popover"]'),
  popoverLikeTestids: Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')).filter((k) => /summary|popover|dialog|panel/i.test(k)),
  roles: Array.from(document.querySelectorAll('[role="dialog"],[role="menu"],[role="listbox"]')).map((e) => {
    const r = e.getBoundingClientRect();
    return { role: e.getAttribute('role'), tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` };
  }),
  byAria: Array.from(document.querySelectorAll('[aria-label^="Canvas node summary"]')).map((e) => {
    const r = e.getBoundingClientRect();
    return { tag: e.tagName, tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` };
  }),
}));
log('D1 点击后 1.6s：\n' + JSON.stringify(out.d1.after1600, null, 1));
await p.keyboard.press('Escape');
await p.waitForTimeout(600);

// ═════════ D2：「外部 1」的机制 —— 按 aria 前缀分组 ═════════
out.d2 = await p.evaluate(() => {
  const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), cls: String(n.className || ''), aria: n.getAttribute('aria-label'),
      inner: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30), visible: r.width > 0 && r.height > 0 };
  });
  const byPrefix = {};
  for (const n of nodes) {
    const pre = (n.aria || '(无 aria)').split('：')[0].split(':')[0].trim();
    (byPrefix[pre] = byPrefix[pre] || []).push(n);
  }
  return { total: nodes.length, groups: Object.fromEntries(Object.entries(byPrefix).map(([k, v]) => [k, { n: v.length, sample: v.slice(0, 3).map((x) => ({ id: x.id, inner: x.inner, cls: x.cls.slice(0, 50) })) }])) };
});
log('D2 按 aria 前缀分组（共 ' + out.d2.total + ' 个节点）：');
for (const [k, v] of Object.entries(out.d2.groups)) log(`   「${k}」→ ${v.n} 个  例：${JSON.stringify(v.sample[0])}`);

// ═════════ D3：testid 普查（结构签名只留 标签+class，不看尺寸） ═════════
out.d3 = await p.evaluate(() => {
  const m = new Map();
  for (const e of document.querySelectorAll('[data-testid]')) {
    const k = e.getAttribute('data-testid');
    const r = e.getBoundingClientRect();
    const sig = `${e.tagName}|${String(e.className || '')}`;
    if (!m.has(k)) m.set(k, { sigs: new Set(), sizes: new Set(), n: 0 });
    const g = m.get(k);
    g.sigs.add(sig); g.n++;
    if (r.width > 0) g.sizes.add(`${Math.round(r.width)}×${Math.round(r.height)}`);
  }
  const all = [...m.entries()].map(([tid, g]) => ({ tid, n: g.n, sigN: g.sigs.size, sigs: [...g.sigs], sizes: [...g.sizes] }));
  return { totalTestids: all.length,
    multiSig: all.filter((x) => x.sigN > 1).sort((a, b) => b.sigN - a.sigN),
    multiSizeSameSig: all.filter((x) => x.sigN === 1 && x.sizes.length > 1).sort((a, b) => b.sizes.length - a.sizes.length) };
});
log(`D3：testid 共 ${out.d3.totalTestids} 个｜**结构签名 >1** 的 ${out.d3.multiSig.length} 个｜同签名但尺寸多种的 ${out.d3.multiSizeSameSig.length} 个`);
for (const x of out.d3.multiSig) { log(`  🔴 结构分裂 [${x.tid}] n=${x.n} 签名${x.sigN}种:`); for (const s of x.sigs.slice(0, 4)) log('       ', s.slice(0, 100)); }
for (const x of out.d3.multiSizeSameSig.slice(0, 8)) log(`  ⚠️ 同签名多尺寸 [${x.tid}] n=${x.n} 尺寸${x.sizes.length}种: ${x.sizes.slice(0, 5).join(' ')}`);

out.end = { sel: await selCount(), credits: await credits(), status: await status() };
log('终点：', JSON.stringify(out.end), '｜积分未变 =', out.start.credits === out.end.credits);
writeFileSync('_tmp-b89b.json', JSON.stringify(out, null, 2));
log('已写 _tmp-b89b.json');
await b.close();
