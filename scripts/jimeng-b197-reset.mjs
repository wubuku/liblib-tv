// 批次 197 收尾复位：新页签的 setViewportSize 会**污染共享页签**（实测 1280×720 → 1282×759，
// 且 devicePixelRatio 从 2 掉到 1），必须用 pinViewport 复位 —— 它带污染断言。
import { openCanvas, readers, settle, endState } from './jimeng-b135-lib.mjs';
const { b, p } = await openCanvas();   // openCanvas 内部第一件事就是 pinViewport
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
await settle(p, R);
console.log(JSON.stringify({
  视口: await p.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]),
  缩放: await R.zoom(), 状态行: await R.status(), 积分: await R.credits(),
  节点数: (await R.ids()).length, 选中: await R.selCount(),
}, null, 1));
console.log('endState =', JSON.stringify(await endState(p, R, 基线)));
await b.close();
