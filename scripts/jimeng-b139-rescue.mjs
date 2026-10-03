// 批次 139 救援：把共享画布恢复到 `/tmp/b120-baseline-ids.txt` 的基线。
//
// 🔑 为什么必须有独立救援脚本：建组是**共享画布上的产物** —— 一旦取证脚本崩在中途，
//   组卡片会连同它的成员一起留在别人的画布上，而且组的右键「删除」会**连成员一起删**
//   （手册 `SOURCE_OBSERVATIONS.md:567` 记过这个坑）。⇒ 归位通道不能依赖出错的那个脚本。
//
// 两步归位（顺序不能换）：
//   ① **先解组**：组存在时点它标题文字选中 → 点「解除编组」⇒ 成员恢复为独立节点。
//      必须先解组，否则第 ② 步按 id 删节点时，成员被组卡片「罩住」，
//      `elementFromPoint` 落点会打到组卡片上（组卡片内部 `pointer-events` 行为特殊）。
//   ② **再按 id 删孤儿**：`当前 id` 减 `基线 id` 的差集，逐个右键 →「删除」。
//
// ⚠️ 只删**基线之外的** id。基线里的 76 个一个都不碰 —— 那是别人的数据。
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount } from './jimeng-b139-lib.mjs';
import { findEmptyPane } from './jimeng-b136-lib.mjs';
import fs from 'node:fs';

const 基线 = fs.readFileSync('/tmp/b120-baseline-ids.txt', 'utf8').split('\n').map((s) => s.trim()).filter(Boolean);
const 孤儿 = async (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')));
// 🔴 与 b139-lib 同款修正：真身组数（滤掉 __group-resize-chrome__ 影子）
const 组数 = (p) => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group'))
  .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || '')).length);

/** 在一个元素内部找一个真能点到它的点（沿用批次 137 护栏的写法）。 */
async function 可点落点(p, sel, inset = 3, step = 3) {
  return p.evaluate(([q, ins, st]) => {
    const e = document.querySelector(q); if (!e) return { __err: 'not-found' };
    const r = e.getBoundingClientRect(); if (r.width < 1) return { __err: 'zero-size' };
    for (let y = Math.ceil(r.y) + ins; y <= r.y + r.height - ins; y += st)
      for (let x = Math.ceil(r.x) + ins; x <= r.x + r.width - ins; x += st) {
        const h = document.elementFromPoint(x, y);
        if (h && (h === e || e.contains(h))) return { x, y, 命中: h.getAttribute('data-testid') || h.tagName };
      }
    return { __err: 'no-point' };
  }, [sel, inset, step]);
}

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 基线节点数: 基线.length };
await keyGuard(p);
await settle(p, R);

rec.起点 = { 组数: await 组数(p), 节点数: (await 孤儿(p)).length, 状态行: await R.status() };

// ---- ① 先解组
//
// 🔴🔴 **批次 142 连续八版失败后定案的真解法**（本段是**唯一**可靠的路径）。
//
//   失败的八版分别栽在（每一条都实测过，不是推测）：
//   ① 裸 `querySelector('.react-flow__node-group')` 拿到的是**影子**节点（一个组匹配 2 个元素）；
//   ② 只扫标题 SPAN —— 常被别人的 `.react-flow__handle`（连接手柄）占据（实测命中 `DIV.react-flow__handle`）；
//   ③ 无预校验直点标题中心 —— 照样选不中（`选中真身组数: 0`）；
//   ④ `⌘⇧G` 兜底 —— **需要组先选中**，与 ②③ 互为**死锁**；
//      而且 `keyGuard` 报 `safe: true` 时焦点其实还停在 dock 按钮上，快捷键被吞；
//   ⑤ `Tab` 循环 —— 按 40 次**全落在 UI chrome 的按钮上**，根本不进画布节点（**已证伪**）；
//   ⑥ `⇧1` 适配画布 —— 把两个组推到 **20% 缩放且完全重叠**，适得其反；
//   ⑦ 空白处拖拽平移 —— mousedown 被 React Flow 解释成**框选**，位置一字未变；
//   ⑧ 滚轮方向搞反 —— `-240` 反而把组**往下**推走。
//
//   ✅ **真根因**：组卡片的屏上 `y` 常常**落在视口之外**（实测 `556..892`，视口高 720），
//   `elementFromPoint` 对越界坐标返回 `null` ⇒ 「点不到」其实是「不在屏幕里」。
//   🔑 `getBoundingClientRect()` **照样给出完整盒子** —— 于是 DOM 读数「看起来有卡片」，
//   实际一个像素都点不到。**这是「有盒子 ≠ 在屏上」的又一例**（同批次 130「有面积 ≠ 可见」）。
//
//   ✅ **三步归位**（实测两次成功，组 2→1→0）：
//   ① **滚轮**把组带进视口：`p.mouse.wheel(0, 240)`，**正数往上带**、每格 240px
//      （实测从 `y=6316` 滚 60 格回到 `316`；且 **canvas 坐标零位移** ⇒ 只改视图）；
//   ② **逐格扫组卡片矩形**，找 `elementFromPoint` **命中组真身或其后代**的点并点击
//      （实测命中 972 / 3800 个点，**全在卡片边缘带** —— 中心区域被组自己的
//      `DIV.absolute` 内层占着，而那层未选中态是 `pointer-events: none`，点它等于点空白）；
//   ③ 点组工具条上的「解除编组」。
const 带进视口 = async (p, 判定) => {
  await p.mouse.move(640, 400);
  for (let i = 0; i < 60; i++) {
    if (await 判定()) return true;
    await p.mouse.wheel(0, 240);
    await p.waitForTimeout(260);
  }
  return await 判定();
};

rec.解组 = [];
let 解组轮 = 0;
while ((await 组数(p)) > 0 && 解组轮 < 4) {
  解组轮++;
  let 解组成功 = false;

  // 策略 0：组**已经**处于选中态 ⇒ 直接点工具条「解除编组」（残留组常常本来就是选中态）
  const 已选 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group'))
    .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''))
    .filter((g) => g.classList.contains('selected')).length);
  if (已选 > 0) {
    const 解0 = await 可点落点(p, '[data-toolbar-value="ungroup"]', 3, 3);
    rec.解组.push({ 轮: 解组轮, 策略: '已选中→直接点解除编组', 落点: 解0 });
    if (!解0.__err) {
      await p.mouse.click(解0.x, 解0.y);
      await p.waitForTimeout(2500);
      await settle(p, R);
      解组成功 = (await 组数(p)) === 0;
      rec.解组.push({ 点按钮后组数: await 组数(p) });
    }
  }

  // 策略 1（正路）：带进视口 → 逐格扫组本体 → 点 → 点解除编组
  if (!解组成功) {
    const 进 = await 带进视口(p, async () => {
      const r = await p.evaluate(() => {
        const g = document.querySelector('.react-flow__node-group:not([data-id^="__group-resize-chrome__"])');
        if (!g) return null;
        const rr = g.getBoundingClientRect();
        return { top: rr.top, bottom: rr.bottom };
      });
      return !!r && r.top >= 80 && r.bottom <= 700;
    });
    rec.解组.push({ 轮: 解组轮, 策略: '带进视口', 已进: 进 });
    const 扫 = await p.evaluate(() => {
      const g = document.querySelector('.react-flow__node-group:not([data-id^="__group-resize-chrome__"])');
      if (!g) return { __err: 'no-真身' };
      const r = g.getBoundingClientRect();
      for (let y = Math.max(Math.ceil(r.y), 66); y <= Math.min(r.bottom, 690); y += 2)
        for (let x = Math.ceil(r.x); x <= Math.min(r.right, 1270); x += 2) {
          const h = document.elementFromPoint(x, y);
          if (h && (h === g || g.contains(h))) return { x, y };
        }
      return { __err: 'no-hit-point' };
    });
    rec.解组.push({ 扫 });
    if (!扫.__err) {
      await p.mouse.click(扫.x, 扫.y);
      await p.waitForTimeout(1500);
      const 选中组 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-group'))
        .filter((g) => !/^__group-resize-chrome__/.test(g.getAttribute('data-id') || ''))
        .filter((g) => g.classList.contains('selected')).length);
      rec.解组.push({ 点后选中组: 选中组 });
      if (选中组 > 0) {
        const 解 = await 可点落点(p, '[data-toolbar-value="ungroup"]', 3, 3);
        rec.解组.push({ 解除编组落点: 解 });
        if (!解.__err) {
          await p.mouse.click(解.x, 解.y);
          await p.waitForTimeout(2500);
          await settle(p, R);
          解组成功 = (await 组数(p)) === 0;
          rec.解组.push({ 解后组数: await 组数(p) });
        }
      }
    }
  }
  if (!解组成功) { rec.解组失败 = { 轮: 解组轮 }; break; }
}
rec.解组后 = { 组数: await 组数(p), 节点数: (await 孤儿(p)).length };

// ---- ② 按 id 删孤儿
rec.删除 = [];
const 当前 = await 孤儿(p);
const 多余 = 当前.filter((x) => !基线.includes(x));
rec.多余 = 多余;
for (const id of 多余) {
  // 🔴 批次 139 d 轮踩过：带着**多选**态直接右键去删，菜单里的「删除」**扫不到可点像素**
  //   （连扫 3 个节点全部 `no-point`），救援因此卡住、3 个孤儿留在共享画布上。
  //   ✅ 批次 139 diag2 臂 A 验出的配方：**先清成 0 选中 → 单选目标 → 右键**，
  //      菜单 7 项、`删除 ⌫` 在 `y=569..605`，扫描**第 2 个采样就命中**（`604,570`）。
  //   ⇒ 立规：走右键菜单删除**前必须回到单选态**，多选态下的右键落点不可靠。
  if (await selCount(p) > 0) {
    const 空 = await findEmptyPane(p);
    if (空) {
      const 是控件 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y);
        return h ? (h.closest('button,[role=button]') ? 1 : 0) : -1; }, [空.x, 空.y]);
      if (是控件 === 0) { await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1000); }
    }
    rec.删除.push({ id, 清选中: { 落点: 空, 剩余: await selCount(p) } });
  }
  const 单选 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
  if (单选.__err) { rec.删除.push({ id, 失败: '单选落点', 单选 }); continue; }
  await p.mouse.click(单选.x, 单选.y);
  await p.waitForTimeout(1000);
  // 复查：此刻**恰好**只选中了这一个（否则右键菜单可能不是单选态那套）
  const 选中 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
  if (选中.length !== 1 || 选中[0] !== id) { rec.删除.push({ id, 失败: '单选不成立', 选中 }); continue; }
  const 落 = 单选;
  await p.mouse.click(落.x, 落.y, { button: 'right' });
  await p.waitForTimeout(1600);
  const del = await p.evaluate(() => {
    const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
      .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
    if (!els.length) return { __err: 'no-delete-item' };
    const e = els[0]; const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
      for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
        const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() };
      }
    return { __err: 'no-point' };
  });
  if (del.__err) {
    // 🔴 失败时把菜单**整体** dump 出来 —— 只留一个 `no-point` 什么也定位不到
    rec.删除.push({ id, 失败: del, 右键落点: [落.x, 落.y], 菜单诊断: await p.evaluate(() => {
      const m = Array.from(document.querySelectorAll('[role=menu]')).find((e) => e.getBoundingClientRect().width > 1);
      const d = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
        .find((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
      const dr = d ? d.getBoundingClientRect() : null;
      const dcs = d ? getComputedStyle(d) : null;
      return {
        菜单: m ? { 矩形: (() => { const r = m.getBoundingClientRect();
            return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })(),
          flexDirection: getComputedStyle(m).flexDirection, 项数: m.querySelectorAll('[role=menuitem]').length,
          逐字: (m.innerText || '').replace(/\s+/g, ' ').trim() } : null,
        删除项: d ? { 矩形: { x: Math.round(dr.x), y: Math.round(dr.y), w: Math.round(dr.width), h: Math.round(dr.height) },
          pe: dcs.pointerEvents, vis: dcs.visibility, disp: dcs.display, op: dcs.opacity,
          在视口内: dr.top >= 0 && dr.bottom <= innerHeight && dr.left >= 0 && dr.right <= innerWidth,
          视口: { w: innerWidth, h: innerHeight },
          逐字: (d.innerText || '').replace(/\s+/g, ' ').trim() } : null,
        删除项中心命中: (() => { if (!d) return null;
          const h = document.elementFromPoint(Math.round(dr.x + dr.width / 2), Math.round(dr.y + dr.height / 2));
          return h ? { tag: h.tagName, cls: String(h.className || '').split(' ')[0].slice(0, 40), role: h.getAttribute('role'),
            逐字: (h.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) } : null; })(),
        所有浮层: Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]'))
          .map((e) => { const r = e.getBoundingClientRect(); return { role: e.getAttribute('role'),
            矩形: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
            z: getComputedStyle(e).zIndex }; }).filter((x) => x.矩形.w > 1),
      };
    }) });
    continue;
  }
  await p.mouse.click(del.x, del.y);
  await p.waitForTimeout(2200);
  await settle(p, R);
  const 还在 = (await 孤儿(p)).includes(id);
  rec.删除.push({ id, 已消失: !还在, 菜单逐字: del.逐字 });
}

await settle(p, R);
const 终 = await 孤儿(p);
rec.终态 = {
  状态行: await R.status(), 节点数: 终.length, 组数: await 组数(p), 选中: await R.selCount(),
  浮层: await R.overlays(), zoom: await R.zoom(), minimap: await R.minimap(), credits: await R.credits(),
  与基线差集: { 多: 终.filter((x) => !基线.includes(x)), 少: 基线.filter((x) => !终.includes(x)) },
};
rec.是否干净 = rec.终态.组数 === 0 && rec.终态.与基线差集.多.length === 0 && rec.终态.与基线差集.少.length === 0;

fs.writeFileSync(new URL('./_tmp-b139-rescue.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify(rec, null, 1));
await b.close();
