// 批次 172 a 轮：休眠视口类的**可达性普查** —— 先攻「生成尺寸面板」。
//
// 画布现状（b 轮普查）：视频 1 个**空**（0 ready）｜ 音频 68 个**全空** ｜
//   图片 1 个（待查）｜ 文本 3 个（有生成面板）｜ 时间线 2 ｜ 导演台 1
// ⇒ 凡是靠「有内容的媒体节点」才能开的面板（video-edit-panel、audio-trim-panel、
//   audio-voice-catalog-panel）**这条路直接封死**。
//   剩下最可能打开的是 `max-w-canvas-generation-size-panel-viewport`
//   ——「生成尺寸」面板，入口应该在文本节点的生成面板里（比例 / 分辨率下拉）。
//
// 本轮只打开下拉看尺寸，⛔ 不改任何参数、不点生成。
import { openCanvas, readers } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);

const CL = ['max-w-canvas-generation-size-panel-viewport', 'max-w-canvas-mask-operation-status',
  'max-w-canvas-video-edit-panel', 'max-w-canvas-smart-edit-cursor-guide',
  'max-w-canvas-post-edit-toolbar-viewport', 'w-canvas-panorama-editor'];

const scan = () => p.evaluate((list) => {
  const out = {};
  for (const c of list) {
    const live = Array.from(document.querySelectorAll('.' + c))
      .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 || r.height > 0; });
    out[c] = live.length ? live.slice(0, 1).map((e) => {
      const cs = getComputedStyle(e), r = e.getBoundingClientRect();
      return { testid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
        aria: e.getAttribute('aria-label'),
        盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        class: (e.getAttribute('class') || ''), style: e.getAttribute('style'),
        文字: (e.innerText || '').trim().split('\n').filter(Boolean).slice(0, 14),
        子: Array.from(e.children).slice(0, 4).map((k) => { const kr = k.getBoundingClientRect(); const kc = getComputedStyle(k);
          return { tag: k.tagName, testid: k.getAttribute('data-testid'), role: k.getAttribute('role'),
            cls: (k.getAttribute('class') || '').slice(0, 80),
            盒: [Math.round(kr.x), Math.round(kr.y), Math.round(kr.width), Math.round(kr.height)], w: kc.width, maxW: kc.maxWidth }; }) };
    }) : 0;
  }
  return out;
}, CL);

// 图片节点有没有内容？
const img = await p.evaluate(() => {
  const n = document.querySelector('.react-flow__node-image');
  if (!n) return null;
  const r = n.getBoundingClientRect();
  return { 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    媒体: Array.from(n.querySelectorAll('img,video,canvas')).map((e) => ({ tag: e.tagName, w: Math.round(e.getBoundingClientRect().width) })),
    文字: (n.innerText || '').trim().split('\n').filter(Boolean).slice(0, 6),
    testid: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))).slice(0, 12) };
});
console.log('图片节点:', JSON.stringify(img));
console.log('静止态休眠类:', JSON.stringify(await scan()));

// 选一个文本节点
const t = await p.evaluate(() => {
  const n = document.querySelector('.react-flow__node-text [data-testid="flow-node-title"]');
  if (!n) return null;
  n.closest('.react-flow__node').scrollIntoView({ block: 'center', inline: 'center' });
  return null;
});
await p.waitForTimeout(700);
const tp = await p.evaluate(() => {
  const n = document.querySelector('.react-flow__node-text [data-testid="flow-node-title"]');
  const r = n.getBoundingClientRect();
  return { 文字: (n.innerText || '').trim().slice(0, 10), pt: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
});
console.log('文本节点:', JSON.stringify(tp));
await p.mouse.click(tp.pt[0], tp.pt[1]);
await p.waitForTimeout(1600);
console.log('选中后:', JSON.stringify({ sel: await R.selCount(), status: await R.status() }));

// 列出节点工具条 / 生成面板上的可点元素
const items = await p.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const nodeSet = new Set(Array.from(document.querySelectorAll('.react-flow__node')));
  const out = [];
  for (const e of document.querySelectorAll('button,[role=button],[role=combobox],[role=tab]')) {
    if (!vis(e)) continue;
    let inNode = false;
    for (let n = e; n && n !== document.body; n = n.parentElement) if (nodeSet.has(n)) { inNode = true; break; }
    const r = e.getBoundingClientRect();
    out.push({ testid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
      aria: e.getAttribute('aria-label') || (e.innerText || '').trim().split('\n')[0].slice(0, 14),
      expanded: e.getAttribute('aria-expanded'), 在节点内: inNode,
      盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      pt: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] });
  }
  return out;
});
console.log(`可点元素 ${items.length} 个：`);
for (const it of items) console.log(`   ${it.role || 'btn'} [${it.testid}] "${it.aria}" exp=${it.expanded} 节点内=${it.在节点内} ${it.盒.join(',')}`);

// 逐个点开 role=combobox / aria-expanded 的，看有没有尺寸面板
for (const it of items.filter((x) => x.role === 'combobox' || x.expanded === 'false' || x.expanded === 'true')) {
  await p.keyboard.press('Escape'); await p.waitForTimeout(250);
  await p.mouse.click(it.pt[0], it.pt[1]);
  await p.waitForTimeout(1000);
  const s = await scan();
  const hit = Object.entries(s).filter(([, v]) => v);
  console.log(`\n点 "${it.aria}" → 命中 ${hit.length ? hit.map(([k]) => k).join(',') : '(无)'}`);
  if (hit.length) { console.log('  详情:', JSON.stringify(s[hit[0][0]], null, 1)); break; }
}
await p.keyboard.press('Escape'); await p.waitForTimeout(300);
console.log('\n收尾:', JSON.stringify({ status: await R.status(), sel: await R.selCount(), credits: await R.credits() }));
await b.close();
