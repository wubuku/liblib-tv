// 只读：把还在画布上的自建主体节点 node_3k3t4wq8vp 的**全部可见后代**连尺寸倒出来，
// 找一找手册那个「约 310×310」到底对应哪一层（节点矩形 352×352、media-stroke 365.92）。
// 目的不是证明 310 对不对，而是**说明它对不上哪一层**，好如实写订正。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const TARGET = 'node_3k3t4wq8vp';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const scaleOf = () => p.evaluate(() => { const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(document.querySelector('.react-flow__viewport')).transform); return m ? +(+m[1]).toFixed(6) : null; });
for (let i = 0; i < 15; i++) { const a = await scaleOf(); await p.waitForTimeout(200); if (a === await scaleOf()) break; }
const S = await scaleOf();
console.log('scale =', S);
const rows = await p.evaluate((v) => {
  const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return { missing: true };
  return Array.from(n.querySelectorAll('*')).map((e) => { const b = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return { tag: e.tagName, tid: e.getAttribute('data-testid') || '', cls: (e.getAttribute('class') || '').slice(0, 54),
      aria: (e.getAttribute('aria-label') || '').slice(0, 30), txt: (e.innerText || '').split('\n')[0].slice(0, 18),
      screen: `${b.width.toFixed(1)}x${b.height.toFixed(1)}`, vis: b.width > 1 && b.height > 1 && cs.display !== 'none' && cs.visibility !== 'hidden',
      bg: cs.backgroundImage !== 'none' ? 'gradient' : (cs.backgroundColor !== 'rgba(0, 0, 0, 0)' ? cs.backgroundColor : '') };
  });
}, TARGET);
const out = { at: new Date().toISOString(), id: TARGET, scale: S, rows };
for (const r of rows.filter((x) => x.vis)) {
  const w = parseFloat(r.screen), h = parseFloat(r.screen);
  console.log(`${r.tid || r.cls.slice(0, 30).padEnd(30)} 屏上 ${r.screen.padEnd(16)} canvas ${(w / S).toFixed(1)}x${(h / S).toFixed(1)}  ${r.bg}  ${r.aria || r.txt}`);
}
writeFileSync(new URL('./_tmp-b79c.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
