// 批次 139 a 轮：现状 + 可行性探针（只读，不建任何东西）。
//
// 🔑 靶子：`organize-group-layout.md` 记「组工具条**宽度跟随组卡片宽度**」，
//   并给了四行读数：3 文本节点 60%=336×40 / 2文本+1视频 60%=367×40 /
//   3 文本 47%=296×40 / 2文本+1视频 47%=312×40。
//   🔴 **同一行跨缩放看**：
//     3 文本：336 → 296，比值 0.881；缩放比 0.47/0.60 = 0.783。**两者不等**。
//     ⇒ 「屏上宽恒定」被否（336≠296）；「屏上宽 ∝ scale」也被否（0.881≠0.783）。
//   ⇒ 手册那句「宽度跟随组卡片宽度……（同样 60%/47% 缩放下卡片宽度不同所致）」
//     **是未经验证的归因** —— 组卡片是固定 canvas 尺寸的节点，换缩放不该改它。
//
// 📌 本轮只读：① 画布现状；② 左栏建节点入口是否还在；③ 组相关 testid 在 dist 里
//   是否真实存在（写任何读数前先问「这串字有没有归属」）。
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);

const 现状 = {
  状态行: await R.status(),
  节点数: (await R.ids()).length,
  选中: await R.selCount(),
  浮层: await R.overlays(),
  zoom: await R.zoom(),
  credits: await R.credits(),
  minimap: await R.minimap(),
};

const 组相关 = await p.evaluate(() => ({
  nodeGroup: document.querySelectorAll('.react-flow__node-group').length,
  groupResizeChrome: document.querySelectorAll('[class*="group-resize-chrome"]').length,
  groupBackground: document.querySelectorAll('[data-testid="group-background"]').length,
  groupBodyFrame: document.querySelectorAll('[data-testid="group-body-frame"]').length,
  标题带: document.querySelectorAll('[data-testid="group-title-hit-area"]').length,
  多选手柄: document.querySelectorAll('[data-testid="flow-node-multi-selection-source-handle"]').length,
  selectionContextToolbar: document.querySelectorAll('[data-testid="selection-context-toolbar"]').length,
  nodeToolbar: Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).map((e) => {
    const r = e.getBoundingClientRect();
    return { w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10 };
  }),
  边数: document.querySelectorAll('.react-flow__edge').length,
}));

// 左栏建节点入口（🔴 七个按钮都会建节点，只读普查只确认它存在，不点）
const 左栏 = await p.evaluate(() => {
  const want = ['文本', '图片', '视频', '音频', '时间线', '主体', '导演台'];
  const out = {};
  for (const w of want) {
    const els = Array.from(document.querySelectorAll(`[aria-label="${w}"]`));
    out[w] = els.map((e) => {
      const r = e.getBoundingClientRect();
      return { tag: e.tagName, w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y),
        pe: getComputedStyle(e).pointerEvents, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) };
    });
  }
  return out;
});

// 组工具条按钮的 aria 逐字是否在 dist 里出现过（写读数前的归属检查由 b 轮做）
const aria全表 = await p.evaluate(() => Array.from(new Set(Array.from(document.querySelectorAll('[aria-label]'))
  .map((e) => e.getAttribute('aria-label')))).filter((s) => /组|layout|group|下载|布局|背景/.test(s)));

const out = { 现状, 组相关, 左栏, aria全表 };
(await import('node:fs')).writeFileSync(new URL('./_tmp-b139a.json', import.meta.url), JSON.stringify(out, null, 1));
console.log(JSON.stringify(out, null, 1));
await b.close();
