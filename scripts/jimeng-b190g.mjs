// 批次 190 g 轮：只做一件事 —— **把视口缩放复位到 26%** 并留下读数。
// 起因：190 e/f 两轮结束时视口都停在 50%（e 是 26%→50%，f 是复位到 26% 之后又被 ⌘V 改成 50%）。
// 📌 顺带记一条观察：**⌘V 会改动画布缩放**（26%→50%，前两轮分别读到 42% 与 43%），
//    但机制未验证（三轮的目标节点、落点都不同），**只记现象不下断言**。
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';
const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '190g', 目标: '视口复位' };
await settle(p, R);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
rec.前 = { 缩放: await R.zoom(), 节点数: 基线.ids.length, 状态行: await R.status(), 积分: await R.credits(), 选中: await R.selCount() };
rec.复位 = await setZoom(p, 26);
await p.keyboard.press('Escape'); await p.waitForTimeout(900);
const 末ids = await R.ids();
rec.后 = { 缩放: await R.zoom(), 节点数: 末ids.length, 状态行: await R.status(), 积分: await R.credits(), 选中: await R.selCount(),
  相对基线多: 末ids.filter((x) => !基线.ids.includes(x)), 相对基线少: 基线.ids.filter((x) => !末ids.includes(x)) };
rec.判定 = { 缩放已复位: rec.后.缩放 === 'Zoom options, 26%', 无残留: rec.后.相对基线多.length === 0 && rec.后.相对基线少.length === 0,
  积分未变: rec.前.积分 === rec.后.积分, 节点数未变: rec.前.节点数 === rec.后.节点数 };
rec.收尾 = await endState(p, R, 基线);
console.log(JSON.stringify(rec, null, 1));
await b.close();
