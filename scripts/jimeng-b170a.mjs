// 批次 170 a 轮：视口余量普查。
//
// 🔴 a 轮 1 版的教训（保留在案）：用 `/(^|-)(max-)?[wh]-canvas-/` 这类**正则**去捞
// 「视口类」，捞回来 176 个 —— 因为 `w-canvas-bottom-dock-zoom-percent`、
// `min-w-canvas-zero` 这类**定尺工具类**长得一模一样。静态 CSS 里的 14 条是
// `max-w-canvas-X` / `max-h-canvas-X` / `w-canvas-panorama-editor` 这种
// **整类只出现在一条视口声明里**的规则，捞法必须是**逐字类名清单**。
//
// 本轮只读：当前画布页上到底挂载了清单里的哪几个？computed 几何是多少？
import { openCanvas, readers } from './jimeng-b135-lib.mjs';

// 逐字取自 https://lf3-lv-buz.vlabstatic.com/.../main.94b57a0e55.css（584613 B）
export const VIEWPORT_CLASSES = [
  ['max-h-canvas-agent-approval-hover', 'max-height:min(380px,50vh)'],
  ['max-h-canvas-agent-approval-hover-content', 'max-height:calc(min(380px, 50vh) - 2px)'],
  ['w-canvas-panorama-editor', 'width:min(680px,calc(100vw - 32px))'],
  ['max-w-canvas-video-fullscreen-media', 'width:min(100%,calc((100vh - 40px)*var(--canvas-media-aspect-ratio)))'],
  ['max-w-canvas-agent-approval-hover', 'max-width:min(536px,calc(100vw - 32px))'],
  ['max-w-canvas-agent-skill-description-tooltip', 'max-width:min(356px,calc(100vw - 36px))'],
  ['max-w-canvas-agent-skill-dialog-viewport', 'max-width:calc(100vw - 32px)'],
  ['max-w-canvas-agent-skill-publish-viewport', 'max-width:calc(100vw - 32px)'],
  ['max-w-canvas-audio-trim-panel', 'max-width:calc(100vw - 32px)'],
  ['max-w-canvas-audio-voice-catalog-panel', 'max-width:calc(100vw - 32px)'],
  ['max-w-canvas-generation-size-panel-viewport', 'max-width:calc(100vw - 32px)'],
  ['max-w-canvas-mask-operation-status', 'max-width:calc(100vw - 32px)'],
  ['max-w-canvas-post-edit-toolbar-viewport', 'max-width:calc(100vw - 40px)'],
  ['max-w-canvas-smart-edit-cursor-guide', 'max-width:calc(100vw - 16px)'],
  ['max-w-canvas-tag-selector', 'max-width:calc(100vw - 32px)'],
  ['max-w-canvas-video-edit-panel', 'max-width:calc(100vw - 32px)'],
];

const { b, p } = await openCanvas();
const R = readers(p);

const rows = await p.evaluate((list) => {
  const out = [];
  for (const [cls, decl] of list) {
    // 有几个「在 DOM 里但没渲染」的也要分清：mounted = 有矩形
    const els = Array.from(document.querySelectorAll('.' + cls));
    const live = els.filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 || r.height > 0; });
    out.push({
      cls, decl,
      inDom: els.length,
      mounted: live.length,
      detail: live.slice(0, 3).map((e) => {
        const cs = getComputedStyle(e);
        const r = e.getBoundingClientRect();
        return {
          testid: e.getAttribute('data-testid'),
          rect: [Math.round(r.width), Math.round(r.height)],
          maxW: cs.maxWidth, maxH: cs.maxHeight, w: cs.width, h: cs.height,
          // 「面板本体 vs 包裹层」的判据：直接子元素里有没有更窄/更矮的实体面板
          kids: Array.from(e.children).slice(0, 4).map((c) => {
            const cr = c.getBoundingClientRect();
            return {
              tag: c.tagName,
              testid: c.getAttribute('data-testid'),
              cls: (c.getAttribute('class') || '').split(/\s+/).filter(Boolean).slice(0, 4).join(' '),
              rect: [Math.round(cr.width), Math.round(cr.height)],
            };
          }),
        };
      }),
    });
  }
  return out;
}, VIEWPORT_CLASSES);

console.log(JSON.stringify({
  base: { status: await R.status(), credits: await R.credits(), inner: await p.evaluate(() => [innerWidth, innerHeight]) },
  rows,
}, null, 1));
await b.close();
