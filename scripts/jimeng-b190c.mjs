// 批次 190 c 轮：① 确认画布已干净；② 用**带超时**的剪贴板读法重测 ⌘C/⌘V；③ 重拍删除三连图。
//
// 上一版（b 轮）卡在 `navigator.clipboard.read()` 上 4 分多钟无输出 ——
// `clipboard.read()` 会触发权限询问，在 CDP 附着下**可能永远不 resolve**。
// ⇒ 本轮所有剪贴板读法都套 `Promise.race([读, 3s 超时])`，**读不到就如实记「读不到」**，
//   绝不把超时当成「剪贴板是空的」（这正是立规 52 的反向陷阱）。
//
// ③ 重拍的理由：a 轮的 174 与 176 **节点内容不同**（缩略图在两张之间加载完了），
//   前后对照的说服力被内容变化吃掉了 ⇒ 这次先等缩略图稳定再拍第一张。
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';
import { keyGuard } from './jimeng-safe-keys.mjs';
import { mkdirSync } from 'node:fs';

const SHOT_DIR = 'docs/user-manual/jimeng-canvas/screenshots';
mkdirSync(SHOT_DIR, { recursive: true });

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '190c', 目标: ['确认画布干净', '带超时的剪贴板重测', '重拍删除三连图'] };
await settle(p, R);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
rec.起点 = { 节点数: 基线.ids.length, 积分: await R.credits(), 缩放: await R.zoom(),
  状态行: await R.status(), a轮遗留还在吗: 基线.ids.includes('node_qz81ygkvg4') };
const 节点数 = async () => (await R.ids()).length;
const 清单 = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null; const t = n.querySelector('[data-testid="flow-node-title"]');
  return { id: i, 标题逐字: t ? t.textContent : null, aria逐字: n.getAttribute('aria-label'),
    class: String(n.className || '').split(' ').slice(0, 3).join(' '),
    内部testid: Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')).slice(0, 8) }; }, id);

// ————————————————————————————————————
// ① 先把 a 轮遗留删掉（按 id → 右键菜单「删除」）
// ————————————————————————————————————
const 按id删除 = async (id) => {
  const 出 = { id, 已删除: false, 诊断: [] };
  const r = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return null; const b2 = n.getBoundingClientRect();
    return { x: Math.round(b2.x), y: Math.round(b2.y), w: Math.round(b2.width), h: Math.round(b2.height) }; }, id);
  if (!r) { 出.诊断.push('不在 DOM'); return 出; }
  const 前 = await 节点数();
  await p.mouse.click(r.x + r.w / 2, r.y + Math.min(16, r.h / 2)); await p.waitForTimeout(1000);
  await p.mouse.click(r.x + r.w / 2, r.y + Math.min(16, r.h / 2), { button: 'right' }); await p.waitForTimeout(1300);
  const 项 = await p.evaluate(() => { const it = Array.from(document.querySelectorAll('[role="menuitem"]'))
      .find((e) => (e.innerText || '').trim().startsWith('删除'));
    if (!it) return null; const rr = it.getBoundingClientRect();
    return { 逐字: (it.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 40), 点: [Math.round(rr.x + rr.width / 2), Math.round(rr.y + rr.height / 2)] }; });
  if (!项) { 出.诊断.push('菜单里没有「删除」'); 出.菜单项 = await p.evaluate(() => Array.from(document.querySelectorAll('[role="menuitem"]')).map((e) => (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 30))); await p.keyboard.press('Escape'); return 出; }
  出.菜单项逐字 = 项.逐字;
  await p.mouse.click(项.点[0], 项.点[1]);
  let 后 = 前;
  for (let i = 0; i < 16 && 后 === 前; i++) { await p.waitForTimeout(250); 后 = await 节点数(); }
  出.节点数前 = 前; 出.节点数后 = 后;
  出.已删除 = 后 === 前 - 1 && !(await R.ids()).includes(id);
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  return 出;
};
rec.清理 = [];
if (rec.起点.a轮遗留还在吗) rec.清理.push(await 按id删除('node_qz81ygkvg4'));
if (rec.起点.缩放 !== 'Zoom options, 26%') rec.缩放复位 = await setZoom(p, 26);
const 清后ids = await R.ids();
rec.清理后 = { 节点数: 清后ids.length, 缩放: await R.zoom(), 状态行: await R.status(),
  相对基线多: 清后ids.filter((x) => !基线.ids.includes(x)) };

// ————————————————————————————————————
// ② 剪贴板：**每次读都套 3 秒超时**
// ————————————————————————————————————
const 读剪贴板 = () => p.evaluate(async () => {
  const 超时 = new Promise((res) => setTimeout(() => res({ 超时: true }), 3000));
  const 真读 = (async () => {
    const items = await navigator.clipboard.read();
    const 逐条 = [];
    for (const it of items) for (const ty of it.types) {
      let 摘要 = null;
      if (ty.startsWith('text/')) { try { const t = await it.getType(ty); 摘要 = (await t.text()).slice(0, 60); } catch (e) { 摘要 = '读失败'; } }
      逐条.push({ type: ty, 摘要 });
    }
    return { 条数: 逐条.length, 逐条 };
  })();
  return Promise.race([真读, 超时]);
});
const 写哨兵 = () => p.evaluate(async (s) => { try { await navigator.clipboard.writeText(s); return { ok: true, 写入: s }; }
  catch (e) { return { ok: false, 错误: e.message }; } }, 'JIMENG-B190-SENTINEL');

rec.剪贴板 = {};
rec.剪贴板.哨兵 = await 写哨兵();
rec.剪贴板.写后 = await 读剪贴板();

// 选中「视频 1」
const 开搜索 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
  if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
if (!开搜索) throw new Error('没有搜索按钮');
await p.mouse.click(开搜索[0], 开搜索[1]); await p.waitForTimeout(1100);
const 搜输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
  if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
if (!搜输入) { await p.keyboard.press('Escape'); throw new Error('搜索面板没打开'); }
await p.mouse.click(搜输入[0], 搜输入[1]); await p.waitForTimeout(400);
await p.fill('[data-testid="canvas-search-panel"] input', '视频 1'); await p.waitForTimeout(1500);
const 命中 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; })
  .filter((x) => x.文字.includes('视频 1')));
if (!命中.length) { await p.keyboard.press('Escape'); throw new Error('搜索无「视频 1」'); }
rec.目标id = 命中[0].id;
rec.目标节点 = await 清单(rec.目标id);
await p.mouse.click(命中[0].点[0], 命中[0].点[1]); await p.waitForTimeout(1500);
await p.keyboard.press('Escape'); await p.waitForTimeout(700);
{ const r = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const b2 = n.getBoundingClientRect(); return [Math.round(b2.x + b2.width / 2), Math.round(b2.y + Math.min(16, b2.height / 2))]; }, rec.目标id);
  await p.mouse.click(r[0], r[1]); await p.waitForTimeout(1200); }
rec.粘贴前 = { 节点数: await 节点数(), 选中: await R.selCount(), keyGuard: await keyGuard(p) };
rec.剪贴板.按Copy前 = await 读剪贴板();
await p.keyboard.press('Meta+c'); await p.waitForTimeout(1400);
rec.剪贴板.按Copy后 = await 读剪贴板();
rec.剪贴板.Copy是否改写 = !!(rec.剪贴板.按Copy前 && rec.剪贴板.按Copy后 && !rec.剪贴板.按Copy前.超时 && !rec.剪贴板.按Copy后.超时
  && JSON.stringify(rec.剪贴板.按Copy前.逐条) !== JSON.stringify(rec.剪贴板.按Copy后.逐条));
const 前数 = await 节点数();
await p.keyboard.press('Meta+v');
let 后数 = 前数;
for (let i = 0; i < 16 && 后数 === 前数; i++) { await p.waitForTimeout(250); 后数 = await 节点数(); }
const ids3 = await R.ids();
const 新增 = ids3.filter((x) => x !== rec.目标id && !基线.ids.includes(x));
rec.粘贴 = { 前节点数: 前数, 后节点数: 后数, 生效: 后数 === 前数 + 1, 新增id: 新增,
  目标aria: rec.目标节点.aria逐字, 新增aria: 新增[0] ? (await 清单(新增[0])).aria逐字 : null,
  新增清单: 新增[0] ? await 清单(新增[0]) : null, 剪贴板: await 读剪贴板() };
rec.收尾清理 = 新增[0] ? await 按id删除(新增[0]) : { 已删除: true, 说明: '没有新增节点' };

// ————————————————————————————————————
// ③ 重拍删除三连图（先等缩略图稳定）
// ————————————————————————————————————
const 画框 = (id, 线型) => p.evaluate(([i, d]) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  document.querySelectorAll('[data-b190]').forEach((e) => e.remove());
  let o;
  if (n) { const r = n.getBoundingClientRect();
    o = document.createElement('div');
    o.style.cssText = `position:fixed;left:${r.x - 10}px;top:${r.y - 10}px;width:${r.width + 20}px;height:${r.height + 20}px;`
      + `border:3px ${d} rgb(255,140,0);border-radius:6px;pointer-events:none;z-index:2147483647;box-sizing:border-box`; }
  else { const r = window.__b190rect; o = document.createElement('div');
    o.style.cssText = `position:fixed;left:${r.x - 10}px;top:${r.y - 10}px;width:${r.w + 20}px;height:${r.h + 20}px;`
      + `border:3px ${d} rgb(255,140,0);border-radius:6px;pointer-events:none;z-index:2147483647;box-sizing:border-box`; }
  o.setAttribute('data-b190', '1');
  document.body.appendChild(o);
  const ob = o.getBoundingClientRect(); const cs = getComputedStyle(o);
  return { ok: true, 框: { x: Math.round(ob.x), y: Math.round(ob.y), w: Math.round(ob.width), h: Math.round(ob.height) },
    border: cs.border, pointerEvents: cs.pointerEvents,
    框在视口内: ob.x >= 0 && ob.y >= 0 && ob.right <= 1280 && ob.bottom <= 720 };
}, [id, 线型]);
const 记矩形 = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null; const r = n.getBoundingClientRect();
  const o = { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
  window.__b190rect = o; return o; }, id);
const 守卫 = (f) => { const g = [['框存在', !!(f && f.ok)], ['3px 橙框', !!(f && /3px (solid|dashed) rgb\(255, 140, 0\)/.test(f.border || ''))],
    ['pointer-events none', !!(f && f.pointerEvents === 'none')], ['框在视口内', !!(f && f.框在视口内)]];
  return { 全过: g.every((x) => x[1]), 逐条: g }; };
const 拍 = async (名, 说明, 框读数, 裁切) => {
  const g = 守卫(框读数);
  if (!g.全过) { rec.截图.push({ 名, 跳过: true, 守卫: g }); return null; }
  const buf = await p.screenshot({ path: `${SHOT_DIR}/${名}.png`, clip: 裁切 });
  rec.截图.push({ 名, 说明, 字节: buf.length, clip: 裁切, 守卫全过: true });
  return buf.length;
};
rec.截图 = [];
if (!rec.收尾清理.已删除) rec.截图.push({ 名: '（前置未完成，跳过三连图）', 跳过: true, 原因: '粘贴出来的节点没删掉，不敢再动画布' });
else {
  // 重新选中目标、等缩略图稳定
  await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (n) n.scrollIntoView({ block: 'nearest' }); }, rec.目标id);
  const r = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return null; const b2 = n.getBoundingClientRect(); return [Math.round(b2.x + b2.width / 2), Math.round(b2.y + Math.min(16, b2.height / 2))]; }, rec.目标id);
  if (!r) throw new Error('目标节点不在视口内');
  await p.mouse.click(r[0], r[1]); await p.waitForTimeout(2500);   // 等缩略图/内容稳定
  rec.稳定等待ms = 2500;
  const rect = await 记矩形(rec.目标id);
  const 裁切 = { x: Math.max(0, rect.x - 30), y: Math.max(0, rect.y - 30), width: Math.min(1280, rect.w + 60), height: Math.min(720, rect.h + 60) };
  rec.裁切 = 裁切; rec.目标屏上 = rect;
  rec.三连图读数 = { 状态行_拍前: await R.status(), 节点数_拍前: await 节点数() };

  const 框1 = await 画框(rec.目标id, 'solid');
  await 拍('174-before-delete', '删除前：目标节点已选中，橙实线框罩住它', 框1, 裁切);
  const 前 = await 节点数();
  await p.keyboard.press('Backspace');
  let 后 = 前;
  for (let i = 0; i < 14 && 后 === 前; i++) { await p.waitForTimeout(250); 后 = await 节点数(); }
  rec.三连图读数.删除 = { 前, 后, 删掉了: 后 === 前 - 1, 状态行: await R.status() };
  const 框2 = await 画框(null, 'dashed');   // 节点已不在 ⇒ 用记住的矩形画虚线框
  await 拍('175-after-delete', '删除后：橙虚线框标出节点原来在的位置，那里已经空了', 框2, 裁切);
  await p.keyboard.press('Meta+z');
  let 复 = 后;
  for (let i = 0; i < 18 && 复 === 后; i++) { await p.waitForTimeout(250); 复 = await 节点数(); }
  rec.三连图读数.撤销 = { 删除后: 后, 撤销后: 复, 复原了: 复 === 前, 同一id: (await R.ids()).includes(rec.目标id), 状态行: await R.status() };
  const 框3 = await 画框(rec.目标id, 'solid');
  await 拍('176-after-undo', '撤销后：同一个节点回到同一个位置（同一个 id）', 框3, 裁切);
  await p.evaluate(() => document.querySelectorAll('[data-b190]').forEach((e) => e.remove()));
}

rec.判定 = {
  画布已干净: 清后ids.filter((x) => !基线.ids.includes(x)).length === 0,
  剪贴板读是否可用: !!(rec.剪贴板.写后 && !rec.剪贴板.写后.超时),
  哨兵是否写进去: !!(rec.剪贴板.写后 && (rec.剪贴板.写后.逐条 || []).some((x) => (x.摘要 || '').includes('JIMENG-B190-SENTINEL'))),
  Copy是否改写剪贴板: rec.剪贴板.Copy是否改写,
  粘贴生效: rec.粘贴.生效,
  粘出来的是不是目标的副本: rec.粘贴.新增aria ? { 目标: rec.粘贴.目标aria, 新增: rec.粘贴.新增aria, 是副本: rec.粘贴.新增aria === rec.粘贴.目标aria } : null,
  截图: rec.截图, 收尾清理: rec.收尾清理.已删除,
  非空守卫: { 截图数: rec.截图.filter((s) => s.守卫全过).length, 三张都拍到: rec.截图.filter((s) => s.守卫全过).length === 3,
    删除成功: rec.三连图读数 ? rec.三连图读数.删除.删掉了 : null, 撤销复原: rec.三连图读数 ? rec.三连图读数.撤销.复原了 : null },
};
rec.收尾 = await endState(p, R, 基线);
console.log(JSON.stringify(rec, null, 1));
await b.close();
