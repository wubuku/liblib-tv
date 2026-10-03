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
rec.解组 = [];
while (await 组数(p) > 0) {
  const 标题 = await p.evaluate(() => {
    const g = document.querySelector('.react-flow__node-group');
    if (!g) return null;
    // 组卡片唯一可点的是标题文字本体：扫标题行里「不是卡片也不是空白」的那个小元素
    const r = g.getBoundingClientRect();
    for (let y = Math.max(Math.ceil(r.y) - 40, 66); y <= r.y + 4; y += 2)
      for (let x = Math.ceil(r.x); x <= r.x + r.width - 2; x += 2) {
        const h = document.elementFromPoint(x, y);
        if (h && h !== g && g.contains(h) && (h.textContent || '').trim()) return { x, y, 逐字: (h.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 20) };
      }
    return { __err: 'no-title-point', 卡片: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) } };
  });
  rec.解组.push({ 标题落点: 标题 });
  if (标题.__err) { rec.解组失败 = 标题; break; }
  await p.mouse.click(标题.x, 标题.y);
  await p.waitForTimeout(1500);
  const 选中了组 = await p.evaluate(() => document.querySelectorAll('.react-flow__node-group.selected').length);
  rec.解组.push({ 选中组数: 选中了组 });
  if (!选中了组) { rec.解组失败 = '点标题没选中组'; break; }
  const 解 = await 可点落点(p, '[data-toolbar-value="ungroup"]', 3, 3);
  rec.解组.push({ 解除编组落点: 解 });
  if (解.__err) { rec.解组失败 = 解; break; }
  await p.mouse.click(解.x, 解.y);
  await p.waitForTimeout(2500);
  await settle(p, R);
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
