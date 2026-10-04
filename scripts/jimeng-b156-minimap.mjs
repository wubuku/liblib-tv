// 批次 156：确认小地图开（批次 134 立规：任何缩放操作都会关掉小地图 ⇒ 收尾必须重开并复读）
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
import { 可点落点 } from './jimeng-b139-lib.mjs';
const { p } = await openCanvas();
const R = readers(p);
let m = await R.minimap();
if (!m || m.ariaPressed !== 'true') {
  const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3);
  if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1600); }
}
m = await R.minimap();
console.log(JSON.stringify({ 小地图: m, 浮层: await R.overlays(), 状态行: await R.status() }, null, 1));
process.exit(0);
