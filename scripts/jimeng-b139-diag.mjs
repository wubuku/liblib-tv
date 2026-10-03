// 批次 139 诊断：为什么右键菜单里的「删除」点不到（`no-point`）。
//
// 🔴 现象：批次 137 的建-删护栏用同一段代码**成功删过**单选节点；
//   本轮对「3 个多选中的节点」逐个右键，菜单项找得到（正则命中）
//   但**扫不到一个能真正点到的像素** ⇒ 菜单位置与命中测试对不上。
//   ⇒ 先把菜单**整体 dump 出来**：有几项、逐字、每项的矩形、elementFromPoint 命中谁。
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 可点落点, selCount } from './jimeng-b139-lib.mjs';
import { findEmptyPane } from './jimeng-b136-lib.mjs';
import fs from 'node:fs';

const TARGET = 'node_24njfrersn';
const rec = {};
const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 选中: await selCount(p) };

  // ① 先取消多选，回到 0 选中（复刻批次 137 的前提：单选）
  if (await selCount(p) > 0) {
    const 空 = await findEmptyPane(p);
    rec.清选中落点 = 空;
    if (空) { await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1000); }
    rec.清选中后 = await selCount(p);
  }
  // ② 单独点选目标节点（走归属校验的落点）
  const 落 = await 可点落点(p, `.react-flow__node[data-id="${TARGET}"]`, 4, 4);
  rec.落点 = 落;
  if (!落.__err) { await p.mouse.click(落.x, 落.y); await p.waitForTimeout(1200); }
  rec.选中态 = { 选中: await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id'))) };

  // ③ 右键，把菜单**整体** dump 出来
  await p.mouse.click(落.x, 落.y, { button: 'right' });
  await p.waitForTimeout(1800);
  rec.菜单 = await p.evaluate(() => {
    const cands = Array.from(document.querySelectorAll('[role=menu],[role=menuitem],[class*="context-menu"],[class*="ContextMenu"]'));
    const 菜单 = cands.filter((e) => e.getBoundingClientRect().width > 1);
    return {
      菜单元素数: 菜单.length,
      逐层: 菜单.slice(0, 6).map((e) => {
        const r = e.getBoundingClientRect();
        return { tag: e.tagName, role: e.getAttribute('role'), className: String(e.className || '').slice(0, 80),
          矩形: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
          zIndex: getComputedStyle(e).zIndex, pe: getComputedStyle(e).pointerEvents, vis: getComputedStyle(e).visibility,
          逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80) };
      }),
      所有项: Array.from(document.querySelectorAll('[role=menuitem]')).map((e) => {
        const r = e.getBoundingClientRect();
        const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
        const h = document.elementFromPoint(cx, cy);
        return { 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(), 矩形: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
          中心: [cx, cy], 中心命中: h ? (h.tagName + '.' + String(h.className || '').split(' ')[0] + ' role=' + h.getAttribute('role')) : null,
          中心命中是否项: h ? (h === e || e.contains(h)) : null, ariaDisabled: e.getAttribute('aria-disabled') };
      }),
    };
  });
  // ④ 用批次 137 的原判据再跑一次，看它到底挑中了哪个元素
  rec.原判据 = await p.evaluate(() => {
    const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
      .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
    return { 命中数: els.length, 逐个: els.map((e) => { const r = e.getBoundingClientRect();
      return { tag: e.tagName, role: e.getAttribute('role'), className: String(e.className || '').slice(0, 60),
        矩形: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
        逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() }; }) };
  });
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 500); }
fs.writeFileSync(new URL('./_tmp-b139-diag.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify(rec, null, 1));
await b.close();
