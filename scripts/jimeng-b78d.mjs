// 只读：把基线「视频 1」的 DOM 元素清单整份倒出来，核 `.video-node-empty` 到底在不在。
// 背景：b78c 新建的视频节点里 `querySelector('.video-node-empty')` 返回 null，
// 而 b78 那一轮同样的建法却读到了 322x181 + 文字「暂无视频」。必须分清
// 「这轮页面状态变了」还是「我这个选择器/时机不对」。
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const VID = Object.entries(BASE.nodes).find(([, v]) => /视频/.test(v.title || ''))[0];
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
console.log('目标节点', VID, JSON.stringify(BASE.nodes[VID]));
const dump = await p.evaluate((v) => {
  const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
  if (!n) return { missing: true };
  const r = n.getBoundingClientRect();
  const rows = Array.from(n.querySelectorAll('*')).map((e) => {
    const b = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return { tag: e.tagName, cls: (e.getAttribute('class') || '').slice(0, 60), tid: e.getAttribute('data-testid') || '',
      aria: (e.getAttribute('aria-label') || '').slice(0, 46), txt: (e.innerText || '').split('\n')[0].slice(0, 24),
      size: `${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`,
      vis: cs.display !== 'none' && cs.visibility !== 'hidden' && b.width > 0 };
  });
  return {
    box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    cls: n.className, innerTextHead: (n.innerText || '').split('\n').slice(0, 4),
    hasEmpty: !!n.querySelector('.video-node-empty'),
    hasImg: n.querySelectorAll('img').length,
    rows: rows.filter((x) => x.vis),
  };
}, VID);
console.log(JSON.stringify(dump, null, 1));
console.log('状态:', await p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]));
console.log('积分相关文本:', await p.evaluate(() => (document.body.innerText.match(/.{0,12}积分.{0,12}/g) || ['无']).slice(0, 4).join(' | ')));
await b.close();
