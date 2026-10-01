import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
const BASE = JSON.parse(readFileSync('scripts/jimeng-baseline-nodes.json','utf8'));
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find(x=>x.url().includes('ai-canvas'));
const s = await p.evaluate(() => ({
  zoom: (document.querySelector('button[aria-label^="Zoom options"]')||{}).getAttribute?.('aria-label'),
  vp: (document.querySelector('.react-flow__viewport')||{}).style?.transform,
  nodes: Array.from(document.querySelectorAll('.react-flow__node')).map(e=>{
    const m=/translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform||'');
    const r=e.getBoundingClientRect();
    return {id:e.getAttribute('data-id'),aria:e.getAttribute('aria-label'),
      canvas: m?[Math.round(parseFloat(m[1])*100)/100, Math.round(parseFloat(m[2])*100)/100]:null,
      screen:`${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)}`};}),
  status: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/)||['?'])[0],
}));
console.log('缩放:', s.zoom, '| viewport:', s.vp, '|', s.status);
console.log('基线:', JSON.stringify(BASE.nodes||BASE));
for (const n of s.nodes) {
  const base = (BASE.nodes||{})[n.id];
  const d = base && n.canvas ? [Math.round((n.canvas[0]-base[0])*100)/100, Math.round((n.canvas[1]-base[1])*100)/100] : null;
  console.log(' ', n.id, JSON.stringify(n.aria), 'canvas', JSON.stringify(n.canvas), '基线', JSON.stringify(base), 'Δ', JSON.stringify(d), '| 屏幕', n.screen);
}
await b.close();
