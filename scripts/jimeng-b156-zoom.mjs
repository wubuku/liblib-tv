// 批次 156：浏览器重启后画布缩放不是 60%（实测 26%），归位 + 复读积分。
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
const { p } = await openCanvas();
const R = readers(p);
await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1500);
const 连读 = [await R.zoom(), await R.zoom()];
console.log(JSON.stringify({
  zoom连读: 连读,
  状态行: await R.status(),
  节点数: await p.evaluate(() => document.querySelectorAll('.react-flow__node').length),
  选中: await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length),
  浮层: await R.overlays(),
  积分逐字: await p.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-commerce-entry"]');
    return e ? { innerText: (e.innerText || '').replace(/\s+/g, ' ').trim(),
      aria: e.getAttribute('aria-label'), testid: e.getAttribute('data-testid'),
      盒: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; })() } : null; }),
  顶栏逐字: await p.evaluate(() => (document.querySelector('[data-testid="canvas-top-bar"]') || {}).innerText || ''),
  transform: await p.evaluate(() => { const e = document.querySelector('.react-flow__viewport'); return e ? e.style.transform : null; }),
}, null, 1));
process.exit(0);
