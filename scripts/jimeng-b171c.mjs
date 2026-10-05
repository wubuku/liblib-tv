// 批次 171 c 轮：靶子 C —— **标签选择器**（`.max-w-canvas-tag-selector{max-width:calc(100vw - 32px)}`）。
//
// 为什么换靶子：批次 170 a 轮问「`max-w-canvas-X` 是包裹层还是面板本体」一直没答，
//   因为那 10 个「余量 32」的类在本画布上**一个都打不开**（本批已逐路排除）：
//   · 音频节点 68 个**全是空壳**（`No resources: 0 ready`）⇒ 裁剪/音色面板不出现
//   · AI 侧栏开得起来（`ASIDE[canvas-feature-sidecar]` 400×696，aria「Agent」），
//     但 `max-h-canvas-agent-approval-hover` 要等 agent **真的提出待批准动作**才挂载
//     ⇒ 那需要发消息（可能扣分，⛔ 立规 20）
//   · 标签选择器是**唯一现成可点的入口**：选中节点后节点上就有 `Add tags` 按钮
//
// 本轮要落的结论：
//   ① 标签选择器的**真实面板尺寸**是多少
//   ② 那个 `max-width:calc(100vw - 32px)` 落在**哪一层**（包裹层？还是面板本体？）
//   ③ 逐字 classList / 内联 style / 直接子几何
//   ④ 预测：若 32 落在包裹层，则**窄视口下被夹的是包裹层，面板本体可能不变**
//      —— 这正是批次 165 定律（量的是面板本体）能不能套上来的分水岭
//
// ⛔ 只开标签选择器看，不新建/不删除任何标签。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '171c' };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b171c.json', import.meta.url), JSON.stringify(rec, null, 1));

// 先复原到 0 选中
await p.keyboard.press('Escape'); await p.waitForTimeout(300);
let bp = await p.evaluate(() => {
  for (let y = 30; y < innerHeight - 30; y += 10)
    for (let x = 30; x < innerWidth - 30; x += 10) {
      const e = document.elementFromPoint(x, y);
      if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) return [x, y];
    }
  return null;
});
if (bp) { await p.mouse.click(bp[0], bp[1]); await p.waitForTimeout(600); }
rec.起点 = { status: await R.status(), sel: await R.selCount() };
console.log('起点', JSON.stringify(rec.起点));

// 选一个节点：点标题（b 轮实测只有标题能选中）
const t = await p.evaluate(() => {
  const n = document.querySelector('.react-flow__node [data-testid="flow-node-title"]');
  n.closest('.react-flow__node').scrollIntoView({ block: 'center', inline: 'center' });
  return null;
});
await p.waitForTimeout(700);
const title = await p.evaluate(() => {
  const n = document.querySelector('.react-flow__node [data-testid="flow-node-title"]');
  const r = n.getBoundingClientRect();
  return { 文字: (n.innerText || '').trim().slice(0, 14), pt: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
});
await p.mouse.click(title.pt[0], title.pt[1]);
await p.waitForTimeout(1200);
rec.选中 = { 节点: title.文字, sel: await R.selCount() };
console.log('选中:', JSON.stringify(rec.选中));

// 点 Add tags
const tag = await p.evaluate(() => {
  const e = document.querySelector('[data-testid="flow-node-selected-tag"]');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return { aria: e.getAttribute('aria-label'), 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    pt: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
});
rec.AddTags按钮 = tag;
console.log('Add tags 按钮:', JSON.stringify(tag));
if (!tag) { console.log('没有 Add tags 按钮'); await b.close(); process.exit(0); }
await p.mouse.click(tag.pt[0], tag.pt[1]);
await p.waitForTimeout(1800);

const 读 = () => p.evaluate(() => {
  const w = document.querySelector('.max-w-canvas-tag-selector');
  if (!w) {
    // 退而求其次：把新出现的浮层都列出来
    const ov = Array.from(document.querySelectorAll('[role=dialog],[role=listbox],[role=menu],section,aside'))
      .map((e) => { const r = e.getBoundingClientRect();
        return { tag: e.tagName, testid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
          aria: e.getAttribute('aria-label'), 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
      .filter((x) => x.盒[2] > 1 && x.盒[3] > 1 && x.盒[2] < 900);
    return { 找到包裹层: false, 新浮层: ov.slice(0, 10) };
  }
  const cs = getComputedStyle(w);
  const r = w.getBoundingClientRect();
  const walk = (el, d) => {
    const q = el.getBoundingClientRect(); const c = getComputedStyle(el);
    return { d, tag: el.tagName, testid: el.getAttribute('data-testid'), role: el.getAttribute('role'),
      aria: el.getAttribute('aria-label'),
      盒: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      w: c.width, h: c.height, maxW: c.maxWidth, maxH: c.maxHeight, disp: c.display, pos: c.position,
      own: el.children.length ? null : (el.innerText || '').trim().replace(/\n/g, '⏎').slice(0, 30),
      kids: Array.from(el.children).map((k) => walk(k, d + 1)) };
  };
  return { 找到包裹层: true, 包裹层: walk(w, 0),
    包裹层原始: { className: w.getAttribute('class'), style: w.getAttribute('style') },
    视口: [innerWidth, innerHeight],
    文字: (w.innerText || '').trim().split('\n').filter(Boolean).slice(0, 12) };
});

rec.读数 = await 读();
console.log('\n找到包裹层 =', rec.读数.找到包裹层);
if (rec.读数.找到包裹层) {
  console.log('class:', rec.读数.包裹层原始.className);
  console.log('style:', JSON.stringify(rec.读数.包裹层原始.style));
  const pr = (n, i = 0) => { console.log(`  ${'  '.repeat(i)}[${n.d}] ${n.tag}${n.testid ? '[' + n.testid + ']' : ''}${n.role ? ' role=' + n.role : ''} ${n.盒.join(',')} w=${n.w} maxW=${n.maxW} disp=${n.disp} pos=${n.pos}${n.own ? ' · ' + n.own : ''}`); n.kids.forEach((k) => pr(k, i + 1)); };
  pr(rec.读数.包裹层);
  console.log('文字:', JSON.stringify(rec.读数.文字));
} else {
  console.log('新浮层:', JSON.stringify(rec.读数.新浮层));
}
落盘();
console.log('\n收尾:', JSON.stringify({ status: await R.status(), sel: await R.selCount(), credits: await R.credits() }));
await b.close();
