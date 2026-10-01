import { chromium } from 'playwright';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find(x => x.url().includes('ai-canvas'));
const r = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map(n => {
  const h = n.querySelector('.react-flow__handle-right');
  const cs = n ? getComputedStyle(n) : {};
  const hr = h && h.getBoundingClientRect();
  return {
    id: n.getAttribute('data-id'),
    nodeW: Math.round(n.getBoundingClientRect().width*10)/10,
    nodeH: Math.round(n.getBoundingClientRect().height*10)/10,
    handle: hr ? [Math.round(hr.width*10)/10, Math.round(hr.height*10)/10] : null,
    counterScale: cs.getPropertyValue('--octo-canvas-node-chrome-counter-scale') || null,
    glyphX: h ? getComputedStyle(h).getPropertyValue('--octo-flow-node-handle-glyph-x') : null,
    handleHClass: h ? String(h.className).split(' ').find(c=>/^h-/.test(c)) : null,
    handleWClass: h ? String(h.className).split(' ').find(c=>/^w-/.test(c)) : null,
  };
}));
console.log(JSON.stringify(r, null, 1));
const vp = await p.evaluate(() => { const v = document.querySelector('.react-flow__viewport');
  return v ? { cls: String(v.className).slice(0,80), transform: v.style.transform } : null; });
console.log('viewport:', JSON.stringify(vp));
await b.close();
