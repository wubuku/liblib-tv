// 批次 190 b 轮：**先把画布弄干净**，再验那个重磅读数。
//
// a 轮遗留：`node_qz81ygkvg4`（⌘V 粘出来的）没删掉，收尾读数 77 节点、缩放被改成 42%。
// 清理路径按手册的可靠路线：**按 id 找到节点 → 右键菜单「删除」**，不依赖 ⌫（⌫ 要画布焦点）。
//
// 顺带验一个 a 轮冒出来、但**证据还不够**的读数：
//   a 轮 ⌘C → ⌘V 之后，新节点标题逐字是 **`文本`**、testid 差集里多出
//   `text-flow-node-full` / `text-node-empty-placeholder` ⇒ 粘出来的**不是**「视频 1」的副本。
//   而该页正文写的是「粘贴出的是**选中节点的副本**（内容与被复制节点一致）」。
//   🔴 但 a 轮**没有先写哨兵**（立规 50）—— 它只知道节点数 76→77，
//   不知道剪贴板里当时装的是什么 ⇒ 那个读数只能说明「粘出来的东西不是视频 1」，**不能直接断言是旧内容**。
//   本轮按纪律来：**先写哨兵 → ⌘C → 读剪贴板 → ⌘V → 读新节点**。
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '190b', 目标: ['清理 a 轮遗留', '带哨兵重测 ⌘C/⌘V 到底粘出什么'] };
await settle(p, R);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
rec.起点 = { 节点数: 基线.ids.length, 积分: await R.credits(), 缩放: await R.zoom() };
const 节点数 = async () => (await R.ids()).length;
const 节点清单 = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null; const t = n.querySelector('[data-testid="flow-node-title"]');
  return { id: i, 标题逐字: t ? t.textContent : null, aria逐字: n.getAttribute('aria-label'),
    class: String(n.className || '').split(' ').slice(0, 3).join(' '),
    内部testid: Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')).slice(0, 8) }; }, id);

/** 按 id 删除一个节点：右键 → 等菜单 → 逐字找「删除」→ 点 → 轮询节点数。 */
const 按id删除 = async (id) => {
  const 出 = { id, 屏上: null, 菜单项逐字: null, 点了: false, 已删除: false, 诊断: [] };
  出.屏上 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return null; const r = n.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; }, id);
  if (!出.屏上) { 出.诊断.push('节点不在 DOM'); return 出; }
  const 前 = await 节点数();
  // 先点一下把它选中并把焦点交回画布，再右键
  await p.mouse.click(出.屏上.x + 出.屏上.w / 2, 出.屏上.y + Math.min(16, 出.屏上.h / 2));
  await p.waitForTimeout(1000);
  await p.mouse.click(出.屏上.x + 出.屏上.w / 2, 出.屏上.y + Math.min(16, 出.屏上.h / 2), { button: 'right' });
  await p.waitForTimeout(1200);
  const 菜单 = await p.evaluate(() => { const ms = Array.from(document.querySelectorAll('[role="menu"]'))
    .filter((m) => m.getBoundingClientRect().width > 1);
    return { 菜单数: ms.length, 逐项: ms.length ? Array.from(ms[0].querySelectorAll('[role="menuitem"]'))
      .map((e) => ({ 逐字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 40),
        禁用: e.getAttribute('aria-disabled') === 'true' })) : [] }; });
  出.菜单 = 菜单;
  const 项 = 菜单.逐项.find((x) => x.逐字.startsWith('删除'));
  if (!项) { 出.诊断.push('菜单里没有「删除」项，逐项=' + JSON.stringify(菜单.逐项.map((x) => x.逐字))); await p.keyboard.press('Escape'); return 出; }
  出.菜单项逐字 = 项.逐字;
  const 点 = await p.evaluate(() => { const it = Array.from(document.querySelectorAll('[role="menuitem"]'))
    .find((e) => (e.innerText || '').trim().startsWith('删除'));
    if (!it) return null; const r = it.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
  if (!点) { 出.诊断.push('拿不到菜单项落点'); return 出; }
  await p.mouse.click(点[0], 点[1]);
  出.点了 = true;
  let 后 = 前;
  for (let i = 0; i < 16 && 后 === 前; i++) { await p.waitForTimeout(250); 后 = await 节点数(); }
  出.节点数前 = 前; 出.节点数后 = 后;
  出.已删除 = 后 === 前 - 1 && !(await R.ids()).includes(id);
  return 出;
};

// ————————————————————————————————————
// ① 清理 a 轮遗留
// ————————————————————————————————————
rec.清理 = [];
for (const id of ['node_qz81ygkvg4']) {
  if (基线.ids.includes(id)) { rec.清理.push({ 跳过: id, 原因: '不在当前画布' }); continue; }
  if ((await R.ids()).includes(id)) rec.清理.push(await 按id删除(id));
}
// 缩放复位
rec.缩放复位 = await setZoom(p, 26);
const 清理后ids = await R.ids();
rec.清理后 = { 节点数: 清理后ids.length, 状态行: await R.status(), 缩放: await R.zoom(),
  相对基线多: 清理后ids.filter((x) => !基线.ids.includes(x)),
  相对基线少: 基线.ids.filter((x) => !清理后ids.includes(x)) };

// ————————————————————————————————————
// ② 带哨兵重测 ⌘C / ⌘V
// ————————————————————————————————————
const 读剪贴板 = () => p.evaluate(async () => {
  try {
    const items = await navigator.clipboard.read();
    const 逐条 = [];
    for (const it of items) for (const ty of it.types) {
      let 摘要 = null;
      if (ty.startsWith('text/')) { try { const t = await it.getType(ty); const s = await t.text(); 摘要 = s.slice(0, 80); } catch (e) { 摘要 = '读失败:' + e.message; } }
      逐条.push({ type: ty, 摘要 });
    }
    return { 条数: 逐条.length, 逐条 };
  } catch (e) { return { 读失败: e.message }; }
});
const 写哨兵 = () => p.evaluate(async (s) => { try { await navigator.clipboard.writeText(s); return { 写入: s, ok: true }; }
  catch (e) { return { ok: false, 错误: e.message }; } }, 'JIMENG-B190-SENTINEL');

rec.剪贴板 = {};
rec.剪贴板.哨兵 = await 写哨兵();
rec.剪贴板.写后 = await 读剪贴板();
// 选中一个视频节点
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
  .map((e) => ({ id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }))
  .filter((x) => x.文字.includes('视频 1')));
if (!命中.length) { await p.keyboard.press('Escape'); throw new Error('搜索无「视频 1」'); }
rec.目标id = 命中[0].id;
rec.目标节点 = await 节点清单(rec.目标id);
await p.mouse.click(命中[0].点[0], 命中[0].点[1]); await p.waitForTimeout(1500);
await p.keyboard.press('Escape'); await p.waitForTimeout(700);
// 点节点本体把焦点交回画布
{
  const r = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const b = n.getBoundingClientRect(); return [Math.round(b.x + b.width / 2), Math.round(b.y + Math.min(16, b.height / 2))]; }, rec.目标id);
  await p.mouse.click(r[0], r[1]); await p.waitForTimeout(1100);
}
rec.粘贴前 = { 节点数: await 节点数(), 选中: await R.selCount(), keyGuard: await keyGuard(p) };
rec.剪贴板.按Copy前 = await 读剪贴板();
await p.keyboard.press('Meta+c'); await p.waitForTimeout(1200);
rec.剪贴板.按Copy后 = await 读剪贴板();
rec.剪贴板.Copy是否改写了剪贴板 = JSON.stringify(rec.剪贴板.按Copy前.逐条) !== JSON.stringify(rec.剪贴板.按Copy后.逐条);
const 前数 = await 节点数();
await p.keyboard.press('Meta+v');
let 后数 = 前数;
for (let i = 0; i < 16 && 后数 === 前数; i++) { await p.waitForTimeout(250); 后数 = await 节点数(); }
const ids2 = await R.ids();
const 新增 = ids2.filter((x) => x !== rec.目标id && !基线.ids.includes(x) && !['node_qz81ygkvg4'].includes(x));
rec.粘贴 = { 前节点数: 前数, 后节点数: 后数, 生效: 后数 === 前数 + 1, 新增id: 新增,
  新增节点清单: 新增[0] ? await 节点清单(新增[0]) : null,
  粘贴后剪贴板: await 读剪贴板() };
// 收尾：删掉新粘出来的
rec.收尾清理 = [];
if (新增[0]) rec.收尾清理.push(await 按id删除(新增[0]));
rec.剪贴板.哨兵还原 = await 写哨兵();

rec.判定 = {
  清理完成: rec.清理.every((x) => x.跳过 || x.已删除) && rec.清理后.相对基线多.length === 0 && rec.清理后.相对基线少.length === 0,
  剪贴板哨兵可读: !!(rec.剪贴板.写后 && rec.剪贴板.写后.条数 > 0),
  哨兵内容正确: !!(rec.剪贴板.写后 && rec.剪贴板.写后.逐条.some((x) => (x.摘要 || '').includes('JIMENG-B190-SENTINEL'))),
  Copy是否改写了剪贴板: rec.剪贴板.Copy是否改写了剪贴板,
  粘贴生效: rec.粘贴.生效,
  粘出来的是不是目标节点的副本: rec.粘贴.新增节点清单 ? {
    目标aria: rec.目标节点.aria逐字, 新增aria: rec.粘贴.新增节点清单.aria逐字,
    是副本: rec.粘贴.新增节点清单.aria逐字 === rec.目标节点.aria逐字 } : null,
  收尾清理完成: rec.收尾清理.every((x) => x.已删除),
  非空守卫: { 清理项数: rec.清理.length, 剪贴板读数次数: ['写后', '按Copy前', '按Copy后', '粘贴后剪贴板'].filter((k) => rec.剪贴板[k]).length,
    目标节点读到: !!rec.目标节点, 哨兵写成功: (rec.剪贴板.哨兵 && rec.剪贴板.哨兵.ok === true) },
};
rec.收尾 = await endState(p, R, 基线);
console.log(JSON.stringify(rec, null, 1));
await b.close();
