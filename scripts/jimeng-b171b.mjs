// 批次 171 b 轮：靶子 B —— 音频节点的编辑面板。
//
// `_tmp-b171-start` 与 j170d 都试过点音频节点，**都没选中**：
//   d 轮点的是 y+30 / 标题行（落在 `flow-node-target-handle` 竖热区上）
//   e 轮点的是节点中心，但**那个点上盖着上一轮残留的右键菜单**（已收尾清掉）
// ⇒ 本轮先**把节点内部结构与可点元素列出来**，再挑一个确定安全的落点。
//
// 要回答的仍是批次 170 a 轮立下、至今没答的问题：
//   **`.max-w-canvas-audio-trim-panel` 这种「max-w-canvas-X」是包裹层还是面板本体？**
//   （批次 165 的定律是量「面板本体」得出的；若 170 把它和包裹层混为一谈，结论就串了）
//
// ⛔ 不点生成、不选音色、不上传。
import { openCanvas, readers } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const CL = ['max-w-canvas-audio-trim-panel', 'max-w-canvas-audio-voice-catalog-panel', 'max-w-canvas-tag-selector'];

const scan = () => p.evaluate((list) => {
  const out = {};
  for (const c of list) {
    const live = Array.from(document.querySelectorAll('.' + c))
      .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 || r.height > 0; });
    out[c] = live.length ? live.slice(0, 2).map((e) => {
      const cs = getComputedStyle(e), r = e.getBoundingClientRect();
      return { testid: e.getAttribute('data-testid'), 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        maxW: cs.maxWidth, w: cs.width, disp: cs.display, pos: cs.position,
        文字: (e.innerText || '').trim().split('\n').filter(Boolean).slice(0, 6),
        直接子: Array.from(e.children).map((k) => { const kr = k.getBoundingClientRect(); const kc = getComputedStyle(k);
          return { tag: k.tagName, testid: k.getAttribute('data-testid'), role: k.getAttribute('role'),
            cls: (k.getAttribute('class') || '').split(/\s+/).slice(0, 5).join(' '),
            盒: [Math.round(kr.x), Math.round(kr.y), Math.round(kr.width), Math.round(kr.height)],
            w: kc.width, maxW: kc.maxWidth, h: kc.height }; }) };
    }) : 0;
  }
  return out;
}, CL);

await p.keyboard.press('Escape'); await p.waitForTimeout(300);
const id = await p.evaluate(() => {
  const n = document.querySelector('.react-flow__node [data-testid="audio-node-empty"]');
  if (!n) return null;
  const node = n.closest('.react-flow__node');
  node.scrollIntoView({ block: 'center', inline: 'center' });
  return node.getAttribute('data-id');
});
await p.waitForTimeout(700);
const box = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const r = n.getBoundingClientRect();
  const kids = Array.from(n.querySelectorAll('button,[role=button],[data-testid]')).map((e) => {
    const q = e.getBoundingClientRect();
    return { tag: e.tagName, testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label') || (e.innerText || '').trim().slice(0, 10),
      屏: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      中心: [Math.round(q.x + q.width / 2), Math.round(q.y + q.height / 2)] };
  });
  return { 节点盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], kids };
}, id);
console.log('节点盒:', JSON.stringify(box.节点盒));
console.log('节点内可点元素:');
for (const k of box.kids) console.log(`   ${k.tag} [${k.testid}] "${k.aria}" ${k.屏.join(',')} → ${k.中心.join(',')}`);

// 逐个安全落点试：每个点完立刻读选中数与视口类
const cands = box.kids.filter((k) => k.屏[2] > 4 && k.屏[3] > 4);
for (const c of cands) {
  await p.keyboard.press('Escape'); await p.waitForTimeout(200);
  const at = await p.evaluate(([x, y]) => {
    const e = document.elementFromPoint(x, y);
    return e ? { tag: e.tagName, testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
      inNode: !!e.closest('.react-flow__node'), cls: (e.getAttribute('class') || '').split(/\s+/).slice(0, 3).join(' ') } : null;
  }, c.中心);
  await p.mouse.click(c.中心[0], c.中心[1]);
  await p.waitForTimeout(1600);
  const sel = await R.selCount();
  const s = await scan();
  const mounted = Object.entries(s).filter(([, v]) => v).map(([k]) => k);
  console.log(`\n点 ${c.tag}[${c.testid}]"${c.aria}"@${c.中心} → 命中 ${at && at.tag}[${at && at.testid}] inNode=${at && at.inNode} | 选中=${sel} | 挂载视口类=${JSON.stringify(mounted)}`);
  if (mounted.length) { console.log('   详情:', JSON.stringify(s[mounted[0]], null, 1)); break; }
}
console.log('\n收尾:', JSON.stringify({ status: await R.status(), sel: await R.selCount(), credits: await R.credits() }));
await b.close();
