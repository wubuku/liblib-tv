// 批次 171 a 轮：找两个靶子的入口。
//
// 靶子 A（更值钱）：`.max-h-canvas-agent-approval-hover{max-height:min(380px,50vh)}`
//   ⇒ 这是**第三类机制**：按**比例**（视口高的一半）夹取，不是「视口 − 余量」。
//   批次 170 的余量普查只覆盖了「减法」那一族；这一族此前全册没有一条实测。
//   预测：vh=720 → min(380,360) = **360**；vh=760 → 380；门槛 **760**；vh=400 → 200。
//   入口：右下「与 AI 对话」（`canvas-sidecar-launcher`）。
//
// 靶子 B：`.max-w-canvas-audio-trim-panel{max-width:calc(100vw - 32px)}`
//   ⇒ 批次 170 a 轮立了个问题没答：**「max-w-canvas-X」到底是包裹层还是面板本体？**
//   入口：音频节点（`_tmp-b171-start` 点了 y+20 落在标题/把手上，0 选中 ⇒ 得换点位）。
//
// ⛔ 只打开面板看，不发消息、不生成、不选音色。
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { keyGuard } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const CL = ['max-h-canvas-agent-approval-hover', 'max-h-canvas-agent-approval-hover-content',
  'max-w-canvas-audio-trim-panel', 'max-w-canvas-audio-voice-catalog-panel', 'max-w-canvas-tag-selector'];

const scan = () => p.evaluate((list) => {
  const out = {};
  for (const c of list) {
    const els = Array.from(document.querySelectorAll('.' + c));
    const live = els.filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 || r.height > 0; });
    out[c] = { inDom: els.length, mounted: live.length, detail: live.slice(0, 2).map((e) => {
      const cs = getComputedStyle(e), r = e.getBoundingClientRect();
      return {
        testid: e.getAttribute('data-testid'),
        盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        maxH: cs.maxHeight, maxW: cs.maxWidth, h: cs.height, w: cs.width,
        文字: (e.innerText || '').trim().split('\n').filter(Boolean).slice(0, 5),
        子: Array.from(e.children).slice(0, 3).map((k) => {
          const kr = k.getBoundingClientRect();
          return { tag: k.tagName, testid: k.getAttribute('data-testid'),
            cls: (k.getAttribute('class') || '').split(/\s+/).filter((x) => /^(max-w|max-h|w|h)-canvas-/.test(x)).join(' '),
            盒: [Math.round(kr.width), Math.round(kr.height)] };
        }),
      };
    }) };
  }
  return out;
}, CL);

console.log('起点:', JSON.stringify({ status: await R.status(), credits: await R.credits() }));
console.log('静止态:', JSON.stringify(await scan()));

// —— 靶子 A：开 AI 侧栏 ——
const side = await p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-sidecar-launcher"]');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2), e.getAttribute('aria-label')];
});
console.log('\n侧栏按钮:', JSON.stringify(side));
if (side) {
  await p.mouse.click(side[0], side[1]);
  await p.waitForTimeout(2500);
  console.log('开侧栏后:', JSON.stringify(await scan(), null, 1));
  const sideInfo = await p.evaluate(() => {
    const cands = Array.from(document.querySelectorAll('aside,section,[role=dialog]'))
      .map((e) => ({ tag: e.tagName, testid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
        aria: e.getAttribute('aria-label'), 盒: (r => [Math.round(r.width), Math.round(r.height)])(e.getBoundingClientRect()) }))
      .filter((x) => x.盒[0] > 1);
    return cands.slice(-8);
  });
  console.log('侧栏容器候选:', JSON.stringify(sideInfo));
  // 侧栏里 hover 一下，看 approval-hover 面板会不会出现
  const pts = await p.evaluate(() => Array.from(document.querySelectorAll('aside button, aside [role=button]'))
    .filter((e) => e.getBoundingClientRect().width > 0).slice(0, 20)
    .map((e) => { const r = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label') || (e.innerText || '').trim().slice(0, 14),
        pt: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; }));
  console.log('侧栏按钮数:', pts.length, JSON.stringify(pts.slice(0, 10)));
  for (const q of pts.slice(0, 8)) {
    await p.mouse.move(q.pt[0], q.pt[1]);
    await p.waitForTimeout(700);
    const s = await scan();
    const hit = Object.entries(s).find(([, v]) => v.mounted > 0);
    if (hit) { console.log(`  hover「${q.aria}」后命中 ${hit[0]}:`, JSON.stringify(hit[1].detail)); break; }
  }
  console.log('全部轮后:', JSON.stringify(await scan()));
}
console.log('\n收尾:', JSON.stringify({ status: await R.status(), sel: await R.selCount(), credits: await R.credits() }));
await b.close();
