// 批次 153 · c 轮 —— 用 b 轮**已验证**的点击序列打开资产库模态，读页面第 80–90 行那张九层结构表的全部几何。
//
// 🔑 b 轮的结论（本轮的前提）：
//   · 资产库模态**能秒开**（`0s` 时 `[role=dialog]` 已是 1，九个 testid 齐了），**3/3 次**；
//   · 🔴 a 轮之所以读到 0，是因为它在同一次会话里**先点了「上传」再点「资产库」**，
//     中间的 Esc 没把上一步的浮层收干净 ⇒ **第二次点击被吞**。
//     📌 **立规：同一会话里连续操作两个面板入口，每次操作之间要把浮层数**回到 0 **并逐字确认**，
//     否则第二次点击可能只是在关掉上一次的东西。
//   · 左栏「上传」点开 **20 秒内不弹对话框、也不新增任何 testid** ⇒ 它**不经过对话框**，
//     直接交给系统文件选择器（headless 下不弹，所以屏幕上什么都不出现）。
//
// ⚠️ 只读：打开模态 → 读九层几何 + 两级页签 + 搜索框 + 页脚三段文案 → Esc 关闭。
//    **不选素材、不点「确认」**（确认会往画布插节点）。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, canvasPos, 可点落点, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 153, 轮次: 'c', 目的: '读资产库模态九层几何 + 两级页签 + 搜索 + 页脚文案' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b153c.json', import.meta.url), JSON.stringify(rec, null, 1));

/** 打开前的浮层计数 —— 每一步操作之间都要先把它读成 0。 */
const 浮层数 = () => p.evaluate(() => document.querySelectorAll('[role=menu],[role=listbox],[role=dialog],[data-state=open]').length);

const 读九层 = () => p.evaluate(() => {
  const 层 = ['canvas-asset-library-dialog', 'canvas-asset-library-surface',
    'canvas-asset-library-operation-area', 'canvas-asset-library-navigation-controls',
    'canvas-asset-library-query-action-group', 'canvas-asset-library-viewport',
    'canvas-asset-library-footer', 'canvas-asset-library-import-status',
    'canvas-asset-library-box-selection'];
  const 读 = (tid) => {
    const e = document.querySelector('[data-testid="' + tid + '"]');
    if (!e) return { testid: tid, 存在: false };
    const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    return { testid: tid, 存在: true,
      box: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x * 10) / 10, Math.round(r.y * 10) / 10],
      tag: e.tagName, role: e.getAttribute('role'), dataState: e.getAttribute('data-state'),
      visibility: s.visibility, display: s.display, pe: s.pointerEvents,
      clip: s.clip, overflow: s.overflow, opacity: s.opacity,
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 220) };
  };
  // 页签：模态内部（不是左栏）
  const 对话 = document.querySelector('[data-testid="canvas-asset-library-dialog"]');
  const 范围 = 对话 || document.body;
  const 页签 = Array.from(范围.querySelectorAll('button,[role=tab],[role=radio]')).map((e) => {
    const r = e.getBoundingClientRect();
    return { tag: e.tagName, role: e.getAttribute('role'), testid: e.getAttribute('data-testid'),
      text: (e.innerText || e.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 24),
      ariaSelected: e.getAttribute('aria-selected'), dataState: e.getAttribute('data-state'),
      box: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x * 10) / 10, Math.round(r.y * 10) / 10] };
  });
  const 搜索 = Array.from(范围.querySelectorAll('input')).map((e) => {
    const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    return { type: e.getAttribute('type'), aria: e.getAttribute('aria-label'), placeholder: e.getAttribute('placeholder'),
      box: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10, Math.round(r.x * 10) / 10, Math.round(r.y * 10) / 10],
      visibility: s.visibility, display: s.display, readOnly: e.readOnly };
  });
  const 关闭 = Array.from(范围.querySelectorAll('button')).filter((e) => /close/i.test(e.getAttribute('aria-label') || '')).map((e) => {
    const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), box: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] };
  });
  const 可见文本 = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim();
  return {
    对话框数: document.querySelectorAll('[role=dialog]').length,
    层: 层.map(读), 页签, 搜索, 关闭钮: 关闭,
    页脚三段: (() => { const f = document.querySelector('[data-testid="canvas-asset-library-footer"]'); return f ? 可见文本(f) : null; })(),
    顶部文案: (() => { const o = document.querySelector('[data-testid="canvas-asset-library-operation-area"]'); return o ? 可见文本(o).slice(0, 200) : null; })(),
    视口文案: (() => { const v = document.querySelector('[data-testid="canvas-asset-library-viewport"]'); return v ? 可见文本(v).slice(0, 200) : null; })(),
  };
});

const { b, p } = await openCanvas();
const R = readers(p);
let 基线canvas = null;
try {
  await keyGuard(p); await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(),
    积分: await R.credits(), 组数: await 组数(p), 选中: await selCount(p), 浮层: await 浮层数() };
  基线canvas = await canvasPos(p);

  // ---- 前置断言：浮层必须是 0，否则这一轮不作数（b 轮教训）----
  rec.开前浮层 = await 浮层数();

  // ---- 用 b 轮验证过的序列：取落点 → 悬停 700ms → **重取落点** → 点击 ----
  const pt = await 可点落点(p, '[aria-label="资产库"]', 3, 3);
  rec.落点 = pt.__err ? { __err: pt.__err } : { 点: [pt.x, pt.y] };
  if (!pt.__err) {
    await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(700);
    const pt2 = await 可点落点(p, '[aria-label="资产库"]', 3, 3);
    const 落 = pt2.__err ? pt : pt2;
    rec.落点.悬停后点 = [落.x, 落.y];
    rec.落点.归属 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y);
      return { tag: h && h.tagName, aria: h && h.getAttribute('aria-label'), 是button本身: !!(h && h.matches('[aria-label="资产库"]')) }; }, [落.x, 落.y]);
    await p.mouse.click(落.x, 落.y);
    // 轮询到模态出现，最多 10 秒
    let 出现秒 = null;
    for (let s = 0; s <= 10; s++) {
      const d = await p.evaluate(() => document.querySelectorAll('[role=dialog]').length);
      if (d > 0) { 出现秒 = s; break; }
      await p.waitForTimeout(1000);
    }
    rec.出现秒 = 出现秒;
    // 🔴 **不调 settle(p, R)** —— 它会连按 Esc 把刚开的模态关掉（见 jimeng-b135-lib.mjs 的警告）
    await p.waitForTimeout(2600);
    rec.读数 = await 读九层();
    落盘();

    // ---- 关掉并确认关干净 ----
    await p.keyboard.press('Escape'); await p.waitForTimeout(1400);
    rec.关闭后 = { 浮层: await 浮层数(), 对话框数: await p.evaluate(() => document.querySelectorAll('[role=dialog]').length),
      资产库testid数: await p.evaluate(() => document.querySelectorAll('[data-testid^="canvas-asset-library"]').length) };
    落盘();
  }
  const 末 = await idsOf(p); const 末c = await canvasPos(p);
  rec.收尾检查 = { 节点数: 末.length,
    位移节点: 基线canvas ? Object.keys(基线canvas).filter((k) => 末c[k] && (末c[k][0] !== 基线canvas[k][0] || 末c[k][1] !== 基线canvas[k][1])) : null };
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

for (let k = 0; k < 3 && (await R.overlays()) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
const 小地图前 = await R.minimap();
if (!小地图前 || 小地图前.ariaPressed !== 'true') {
  const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3);
  if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); }
}
rec.小地图后 = await R.minimap();
await settle(p, R);
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits(), 组数: await 组数(p),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length) };

console.log('开前浮层:', rec.开前浮层, '| 落点:', JSON.stringify(rec.落点), '| 出现秒:', rec.出现秒, '| 对话框数:', (rec.读数 || {}).对话框数);
console.log('\n=== 九层几何 ===');
for (const l of ((rec.读数 || {}).层 || [])) console.log('  ' + (l.存在 ? '✔' : '✘') + ' ' + l.testid.padEnd(42) + ' ' + JSON.stringify(l.box || null) + ' ' + (l.role || '-') + ' ' + (l.dataState || '-') + ' ' + (l.visibility || '') + '/' + (l.display || '') + ' pe=' + (l.pe || '-'));
console.log('\n顶部文案:', (rec.读数 || {}).顶部文案);
console.log('视口文案:', (rec.读数 || {}).视口文案);
console.log('页脚三段:', (rec.读数 || {}).页脚三段);
console.log('\n页签:');
for (const t of ((rec.读数 || {}).页签 || [])) console.log('  ' + String(t.text).padEnd(26) + JSON.stringify(t.box) + ' role=' + (t.role || '-') + ' sel=' + (t.ariaSelected || '-') + ' state=' + (t.dataState || '-'));
console.log('搜索:', JSON.stringify(((rec.读数 || {}).搜索 || [])));
console.log('关闭钮:', JSON.stringify(((rec.读数 || {}).关闭钮 || [])));
console.log('\n关闭后:', JSON.stringify(rec.关闭后));
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');

const 层 = ((rec.读数 || {}).层 || []);
// 🔴 画布上恒有 1 个常驻 [data-state=open] 包装层，所以这里判「与起点相同」而不是「等于 0」
断言('① 开前浮层计数与起点相同（常驻层恒为 1，判「等于 0」会永远红）', rec.开前浮层 === (rec.起点 || {}).浮层, { 起: (rec.起点 || {}).浮层, 开前: rec.开前浮层 });
断言('② 落点归属 = 资产库 BUTTON 本身', (rec.落点 || {}).归属 && (rec.落点 || {}).归属.是button本身 === true, rec.落点);
断言('③ 模态出现（有对话框且九个 testid 齐全）', (rec.读数 || {}).对话框数 === 1 && 层.length === 9 && 层.every((l) => l.存在), { 对话框: (rec.读数 || {}).对话框数, 缺: 层.filter((l) => !l.存在).map((l) => l.testid) });
断言('④ 九层里有面积的层 ≥ 7（状态位与框选层按设计是空的）', 层.filter((l) => l.box && l.box[0] > 0).length >= 7, 层.map((l) => [l.testid, l.box && l.box[0]]));
断言('⑤ Esc 关闭后模态全部消失', (rec.关闭后 || {}).对话框数 === 0 && (rec.关闭后 || {}).资产库testid数 === 0, rec.关闭后);
if (rec.收尾检查 && rec.收尾检查.位移节点) 断言('⑥ 其余节点零位移', rec.收尾检查.位移节点.length === 0, rec.收尾检查);

rec.断言全过 = 断言过; 落盘();
await b.close();
