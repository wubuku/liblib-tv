// 批次 190：**给「复制、删除与撤销」这一页补上操作前后的画布图**，并把两处**过期**的表述换成硬证据。
//
// 靶子一（遗留状态没销账）：该页 `### ❗ 一条未复核的观测` 记着
//   「观测到一次『键盘 ⌘D 无反应、菜单项正常』；未复核」——
//   而**批次 183 早已用事件级证据关闭了它**：⌘D 的 keydown 确实送达、但**没有 copy/cut 事件**、
//   节点数 76→76 ⇒ 应用没接这个键；同一节点走菜单「复制副本」**可用**（76→77、标题 `b22-upload (2)`、自动选中）。
//   ⇒ 这一页仍在对读者暗示「⌘D 可能有坑、待复核」。
//
// 靶子二（解释比证据含糊）：该页写「点结果行时 document.activeElement 是 body 或搜索按钮」。
//   批次 183 量到的是**元素级**真相：成功格焦点在 `DIV[rf__node-node_gref4sw056]`、
//   失败格在 `BUTTON[canvas-panel-launcher]`（顶栏，**不是 body**）。本轮重测一遍并升级表述。
//
// 靶子三（图文缺口）：该页 415 行只有 4 张图，**全是右键菜单**，
//   「删除前 / 删除后 / 撤销复原 / 粘贴落点」**一张都没有** —— 而这正是读者最需要的四张。
//
// 三张图用**同一个裁切框**，构成可直接对比的前后对照（同一片画布、同一个位置）。
import { openCanvas, readers, settle, endState } from './jimeng-b135-lib.mjs';
import { pinViewport, keyGuard, pressLetter } from './jimeng-safe-keys.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '190', 页面: '10-tasks/duplicate-delete-history.md', 靶子: ['⌘D 未复核已过期', '焦点解释含糊', '缺 4 张操作前后图'] };
await settle(p, R);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
rec.起点 = { 节点数: 基线.ids.length, 积分: await R.credits(), 缩放: await R.zoom() };
const 状态行 = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const 节点数 = async () => (await R.ids()).length;
const 画布坐标 = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null; const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  return m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null; }, id);
const 屏上矩形 = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null; const r = n.getBoundingClientRect();
  return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; }, id);
const 焦点描述 = () => p.evaluate(() => { const a = document.activeElement; if (!a) return null;
  return { tag: a.tagName, testid: a.getAttribute('data-testid'), cls: String(a.className || '').split(' ')[0],
    aria: a.getAttribute('aria-label'), 是body: a === document.body }; });

/** 注入橙框并**读回**它（立规 56：几何 + border + 是否真罩住目标），返回 clip。 */
const 画框 = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { ok: false, 原因: '节点不在 DOM' };
  const r = n.getBoundingClientRect();
  const pad = 10;
  const o = document.createElement('div');
  o.setAttribute('data-b190', '1');
  o.style.cssText = `position:fixed;left:${r.x - pad}px;top:${r.y - pad}px;width:${r.width + pad * 2}px;height:${r.height + pad * 2}px;`
    + `border:3px solid rgb(255,140,0);border-radius:6px;pointer-events:none;z-index:2147483647;box-sizing:border-box`;
  document.body.appendChild(o);
  const ob = o.getBoundingClientRect();
  const 罩住 = !(ob.right < r.x || ob.left > r.right || ob.bottom < r.y || ob.top > r.bottom);
  const cs = getComputedStyle(o);
  return { ok: true, 框: { x: Math.round(ob.x), y: Math.round(ob.y), w: Math.round(ob.width), h: Math.round(ob.height) },
    目标屏上: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
    border: cs.border, pointerEvents: cs.pointerEvents, 罩住目标: 罩住 };
}, id);
const 撤框 = () => p.evaluate(() => { document.querySelectorAll('[data-b190]').forEach((e) => e.remove()); return true; });
/** 读回框之后的最终守卫：三条全过才允许 shutter。 */
const 拍前守卫 = (框读数) => {
  const g = [];
  g.push(['框存在', !!(框读数 && 框读数.ok)]);
  if (框读数 && 框读数.ok) g.push(['border 是 3px 橙', /3px solid rgb\(255, 140, 0\)/.test(框读数.border || '')]);
  if (框读数 && 框读数.ok) g.push(['pointer-events none', 框读数.pointerEvents === 'none']);
  g.push(['框在视口内', !!(框读数 && 框读数.框 && 框读数.框.x >= 0 && 框读数.框.y >= 0
    && 框读数.框.x + 框读数.框.w <= 1280 && 框读数.框.y + 框读数.框.h <= 720)]);
  return { 全过: g.every((x) => x[1]), 逐条: g };
};

const shots = [];
async function 拍(名字, 说明, 框读数, 裁切) {
  const 守卫 = 拍前守卫(框读数);
  if (!守卫.全过) { shots.push({ 名字, 跳过: true, 原因: '守卫未过', 守卫 }); return null; }
  const clip = 裁切 || { x: Math.max(0, 框读数.框.x - 14), y: Math.max(0, 框读数.框.y - 14),
    width: Math.min(1280, 框读数.框.w + 28), height: Math.min(720 - Math.max(0, 框读数.框.y - 14), 框读数.框.h + 28) };
  const buf = await p.screenshot({ path: `screenshots/${名字}.png`, clip });
  shots.push({ 名字, 说明, 字节: buf.length, clip, 守卫全过: true });
  return clip;
}

// ——————————————————————————————————————————————
// ① 焦点：先复现「搜索面板选中 ⇒ ⌫ 删不掉」的元素级证据
// ——————————————————————————————————————————————
rec.焦点 = {};
const 开搜索 = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[aria-label]')).find((x) => x.getAttribute('aria-label') === '搜索');
  if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
if (!开搜索) throw new Error('没有搜索按钮');
await p.mouse.click(开搜索[0], 开搜索[1]); await p.waitForTimeout(1100);
const 搜输入 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-search-panel"] input');
  if (!e) return null; const r = e.getBoundingClientRect(); return r.width > 2 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null; });
if (!搜输入) { await p.keyboard.press('Escape'); throw new Error('搜索面板没打开'); }
await p.mouse.click(搜输入[0], 搜输入[1]); await p.waitForTimeout(400);
await p.fill('[data-testid="canvas-search-panel"] input', '视频 1'); await p.waitForTimeout(1500);
const 搜命中 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-"]'))
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 20 && r.height > 20; })
  .map((e) => { const r = e.getBoundingClientRect(); return { id: (e.getAttribute('data-testid') || '').replace('canvas-search-result-', ''), 文字: (e.innerText || '').trim().replace(/\n/g, ' | ').slice(0, 60), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; })
  .filter((x) => x.文字.includes('视频 1')));
if (!搜命中.length) { await p.keyboard.press('Escape'); throw new Error('搜索无「视频 1」'); }
rec.目标 = { id: 搜命中[0].id, 标题: '视频 1' };
await p.mouse.click(搜命中[0].点[0], 搜命中[0].点[1]); await p.waitForTimeout(1500);
rec.焦点.搜索面板选中后 = await 焦点描述();
rec.焦点.搜索面板选中后的选中数 = await R.selCount();
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
// 此时按 ⌫：预期删不掉（复现该页记的现象）
{
  const 前 = await 节点数();
  const g = await keyGuard(p);
  await p.keyboard.press('Backspace'); await p.waitForTimeout(1400);
  const 后 = await 节点数();
  rec.焦点.搜索选中后按Backspace = { 前节点数: 前, 后节点数: 后, 删掉了: 后 < 前, keyGuard: g };
}

// ② 直接点节点本体把焦点交回画布（该页给的两条正解之一）
rec.目标屏上 = await 屏上矩形(rec.目标.id);
if (!rec.目标屏上) throw new Error('目标节点不在视口内（点不到）');
await p.mouse.click(rec.目标屏上.x + rec.目标屏上.w / 2, rec.目标屏上.y + Math.min(14, rec.目标屏上.h / 2));
await p.waitForTimeout(1200);
rec.焦点.点节点本体后 = await 焦点描述();
rec.焦点.点节点本体后的选中数 = await R.selCount();
if (await R.selCount() !== 1) throw new Error('点节点本体没选中，本轮作废');

// ③ 固定裁切框（三张图共用）
rec.裁切 = (() => { const r = rec.目标屏上; const x = Math.max(0, r.x - 26), y = Math.max(0, r.y - 26);
  return { x, y, width: Math.min(1280 - x, r.w + 52), height: Math.min(720 - y, r.h + 52) }; })();
rec.目标画布坐标 = await 画布坐标(rec.目标.id);
rec.状态行_删前 = await 状态行();
rec.节点数_删前 = await 节点数();

// ——————————————————————————————————————————————
// ④ 删除前 → ⌫ → 删除后 → ⌘Z 复原
// ——————————————————————————————————————————————
{
  const 框1 = await 画框(rec.目标.id);
  rec.框读数_删前 = 框1;
  await 拍('174-before-delete', '删除前：目标节点已选中，橙框罩住它', 框1, rec.裁切);
  await 撤框();

  const 前 = await 节点数();
  await p.keyboard.press('Backspace');
  let 后 = 前;
  for (let i = 0; i < 12 && 后 === 前; i++) { await p.waitForTimeout(250); 后 = await 节点数(); }
  rec.删除 = { 前节点数: 前, 后节点数: 后, 删掉了: 后 === 前 - 1,
    目标还在: (await R.ids()).includes(rec.目标.id), 状态行: await 状态行() };

  // 删除后：框画在「原来节点的位置」（现在那里是空的）
  const 框2 = await p.evaluate((r) => {
    const o = document.createElement('div');
    o.setAttribute('data-b190', '1');
    o.style.cssText = `position:fixed;left:${r.x - 10}px;top:${r.y - 10}px;width:${r.w + 20}px;height:${r.h + 20}px;`
      + `border:3px dashed rgb(255,140,0);border-radius:6px;pointer-events:none;z-index:2147483647;box-sizing:border-box`;
    document.body.appendChild(o);
    const ob = o.getBoundingClientRect(); const cs = getComputedStyle(o);
    return { ok: true, 框: { x: Math.round(ob.x), y: Math.round(ob.y), w: Math.round(ob.width), h: Math.round(ob.height) },
      目标屏上: r, border: cs.border, pointerEvents: cs.pointerEvents, 罩住目标: true, 说明: '虚线框标出「节点原来在的位置」' };
  }, rec.目标屏上);
  rec.框读数_删后 = 框2;
  await 拍('175-after-delete', '删除后：虚线框标出节点原来在的位置，那里已经空了', 框2, rec.裁切);
  await 撤框();

  // ⌘Z 撤销
  await p.keyboard.press('Meta+z');
  let 复 = 后;
  for (let i = 0; i < 16 && 复 !== 后; i++) { await p.waitForTimeout(250); 复 = await 节点数(); }
  if (复 === 后) { await p.keyboard.press('Meta+z'); await p.waitForTimeout(1500); 复 = await 节点数(); }
  rec.撤销 = { 删除后节点数: 后, 撤销后节点数: 复, 复原了: 复 === 前,
    同一id回来了: (await R.ids()).includes(rec.目标.id),
    回来后的画布坐标: await 画布坐标(rec.目标.id), 删前画布坐标: rec.目标画布坐标, 状态行: await 状态行() };

  const 框3 = await 画框(rec.目标.id);
  rec.框读数_撤销后 = 框3;
  await 拍('176-after-undo', '撤销后：同一个节点回到同一个位置（同一个 id、同一个 canvas 坐标）', 框3, rec.裁切);
  await 撤框();
}

// ⑤ ⌘C → ⌘V：粘贴副本并读它的落点偏移
{
  const 前 = await 节点数();
  await p.keyboard.press('Meta+c'); await p.waitForTimeout(900);
  await p.keyboard.press('Meta+v');
  let 后 = 前;
  for (let i = 0; i < 14 && 后 === 前; i++) { await p.waitForTimeout(250); 后 = await 节点数(); }
  const ids = await R.ids();
  const 新增 = ids.filter((x) => !基线.ids.includes(x) && x !== rec.目标.id);
  rec.粘贴 = { 前节点数: 前, 后节点数: 后, 粘贴生效: 后 === 前 + 1, 新增id: 新增,
    目标画布坐标: rec.目标画布坐标,
    新节点画布坐标: 新增[0] ? await 画布坐标(新增[0]) : null,
    新节点标题: 新增[0] ? await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      const t = n && n.querySelector('[data-testid="flow-node-title"]'); return t ? t.textContent : null; }, 新增[0]) : null,
    状态行: await 状态行() };
  if (新增[0]) {
    const r1 = await 屏上矩形(rec.目标.id), r2 = await 屏上矩形(新增[0]);
    rec.粘贴.两节点屏上 = { 原: r1, 副本: r2 };
    // 裁切覆盖两者
    const x = Math.max(0, Math.min(r1.x, r2.x) - 20), y = Math.max(0, Math.min(r1.y, r2.y) - 20);
    const 右 = Math.min(1280, Math.max(r1.x + r1.w, r2.x + r2.w) + 20), 下 = Math.min(720, Math.max(r1.y + r1.h, r2.y + r2.h) + 20);
    rec.粘贴裁切 = { x, y, width: 右 - x, height: 下 - y };
    const 框4 = await p.evaluate(([a, c]) => {
      const mk = (r, dash) => { const o = document.createElement('div'); o.setAttribute('data-b190', '1');
        o.style.cssText = `position:fixed;left:${r.x - 8}px;top:${r.y - 8}px;width:${r.w + 16}px;height:${r.h + 16}px;`
          + `border:3px ${dash} rgb(255,140,0);border-radius:6px;pointer-events:none;z-index:2147483647;box-sizing:border-box`;
        document.body.appendChild(o); return o; };
      mk(a, 'solid'); mk(c, 'dashed');
      const f = document.querySelector('[data-b190]'); const fb = f.getBoundingClientRect(); const cs = getComputedStyle(f);
      return { ok: true, 框: { x: Math.round(fb.x), y: Math.round(fb.y), w: Math.round(fb.width), h: Math.round(fb.height) },
        border: cs.border, pointerEvents: cs.pointerEvents, 罩住目标: true };
    }, [r1, r2]);
    rec.框读数_粘贴 = 框4;
    await 拍('177-after-paste', '粘贴后：原节点（实线框）与新副本（虚线框）并排，副本落在原节点旁边', 框4, rec.粘贴裁切);
    await 撤框();
    // 收尾：把副本删掉（走右键菜单「删除」，不依赖 ⌫）
    rec.清理 = [];
    if (新增[0]) {
      const rr = await 屏上矩形(新增[0]);
      await p.mouse.click(rr.x + rr.w / 2, rr.y + rr.h / 2, { button: 'right' });
      await p.waitForTimeout(1000);
      const 项 = await p.evaluate(() => { const it = Array.from(document.querySelectorAll('[role="menuitem"]'))
        .find((e) => (e.innerText || '').trim().startsWith('删除'));
        if (!it) return null; const r = it.getBoundingClientRect();
        return { 逐字: (it.innerText || '').trim().replace(/\n/g, ' | '), 点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
      if (项) { await p.mouse.click(项.点[0], 项.点[1]); await p.waitForTimeout(1400); }
      const ids2 = await R.ids();
      rec.清理.push({ id: 新增[0], 菜单项逐字: 项 ? 项.逐字 : null, 已删除: !ids2.includes(新增[0]) });
      await p.keyboard.press('Escape'); await p.waitForTimeout(500);
    }
  }
}

rec.判定 = {
  焦点: { 搜索面板选中后焦点: rec.焦点.搜索面板选中后, 点节点本体后焦点: rec.焦点.点节点本体后,
    搜索选中后按Backspace删掉了: rec.焦点.搜索选中后按Backspace.删掉了,
    '搜索面板选中后焦点究竟是什么': rec.焦点.搜索面板选中后 ? (rec.焦点.搜索面板选中后.是body ? 'body' : (rec.焦点.搜索面板选中后.testid || rec.焦点.搜索面板选中后.cls)) : null },
  删除: rec.删除, 撤销: rec.撤销, 粘贴: rec.粘贴,
  截图: shots,
  非空守卫: { 截图数: shots.length, 全部守卫通过: shots.every((s) => s.守卫全过 === true),
    删除成功: rec.删除 && rec.删除.删掉了 === true, 撤销复原: rec.撤销 && rec.撤销.复原了 === true,
    粘贴生效: rec.粘贴 && rec.粘贴.粘贴生效 === true, 清理完成: rec.清理 && rec.清理.every((c) => c.已删除) },
};

rec.收尾 = await endState(p, R, 基线);
console.log(JSON.stringify(rec, null, 1));
await b.close();
