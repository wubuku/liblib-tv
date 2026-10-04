// 批次 156 截图 —— 4 张，全部**拍前逐条断言**（拍错的图比没图更坏）
//
// ① 112-image-node-floating-toolbar.png   有媒体的图片节点选中态 12 键浮动工具条（**屏上真实位置**）
// ② 113-image-node-tools-menu.png         `data-toolbar-value="tools"` 菜单：编辑/消除笔/裁剪/宫格切分/标注
// ③ 114-image-node-context-menu-9-items.png 右键 200×372 九项（含「保存到主体库」）
// ④ 115-subject-export-confirm-dialog.png 「设置主体」二次确认对话框 548×688
//
// 🔑 ① 这张图是本批**唯一能证明工具条锚在节点正上方**的证据：
//    156-c 量到的 959×40 在 (-627,-591)（离屏），当时差点写成「工具条在节点左上方」。
//    平移到屏内后复测：工具条 959×40@81,208、节点 341×192@390,284
//    —— 中心 x 两者**都等于 560.5**，工具条底边 248 距节点顶边 284 差 **36px**（60% 档 ⇒ canvas 60px）。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, keyGuard } from './jimeng-b135-lib.mjs';
import { selCount, idsOf, 可点落点 } from './jimeng-b139-lib.mjs';

const rec = { 批次: '156shots', 目的: '保存到主体库 / 图片节点工具条 4 张图' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b156shots.json', import.meta.url), JSON.stringify(rec, null, 1));
const 出图 = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);

const 读transform = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport'); return e ? e.style.transform : null; });
const tx = (t) => { const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(t || ''); return m ? [parseFloat(m[1]), parseFloat(m[2])] : null; };
const 空点 = (ya, yb, xa, xb, s) => p.evaluate(([y1, y2, x1, x2, st]) => {
  const 坏 = (x, y) => { const h = document.elementFromPoint(x, y); if (!h) return 1;
    if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button],[role=menuitem]')) return 1;
    if (h.closest('.react-flow__node') || h.closest('[data-testid="node-toolbar"]') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
    return !(h.classList && h.classList.contains('react-flow__pane')); };
  for (let y = y1; y < y2; y += st) for (let x = x1; x < x2; x += st) if (!坏(x, y)) return { x, y };
  return { __err: 'no-free-pane' };
}, [ya, yb, xa, xb, s]);
const 拖 = async (dx, dy) => {
  if (!dx && !dy) return { 跳过: 0 };
  const 起 = await 空点(130, 600, 400, 880, 10); if (起.__err) return 起;
  await p.mouse.move(起.x, 起.y); await p.mouse.down();
  for (let k = 1; k <= 12; k++) { await p.mouse.move(起.x + Math.round(dx * k / 12), 起.y + Math.round(dy * k / 12)); await p.waitForTimeout(45); }
  await p.mouse.up(); await p.waitForTimeout(1400); return { 落点: 起 };
};
const 切工具 = async (想要) => {
  const g = () => p.evaluate(() => { const b = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
    if (!b) return null; const r = b.getBoundingClientRect();
    return { aria: b.getAttribute('aria-label'), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; });
  const b = await g(); if (!b) return { 错: 'no-toggle' };
  if (b.aria === 想要) return { 已就位: true };
  await p.mouse.click(b.盒[2] + b.盒[0] / 2, b.盒[3] + b.盒[1] / 2); await p.waitForTimeout(1300);
  const 后 = await g(); return { 成功: !!(后 && 后.aria === 想要) };
};
// 橙色高亮框（拍完即摘）
// 🔴 `[data-testid="node-toolbar"]` 在文档里有**两个**：一个 `.react-flow__renderer` 下的**占位**（0×0）、
//    一个真身。批次 85 就踩过「单数 querySelector 量到占位」，本轮高亮又踩了一次（框画在 0×0 上＝没画）。
//    ⇒ 高亮一律**跳过零面积元素**。
const 高亮 = (sel, 边) => p.evaluate(([s, t]) => {
  const es = Array.from(document.querySelectorAll(s));
  const e = es.find((x) => { const r = x.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  if (!e) return { 命中: false, 候选数: es.length };
  const r = e.getBoundingClientRect();
  let ov = document.getElementById('__hl__');
  if (!ov) { ov = document.createElement('div'); ov.id = '__hl__'; document.body.appendChild(ov); }
  ov.style.cssText = 'position:fixed;pointer-events:none;z-index:2147483647;border:3px solid rgb(255,146,48);border-radius:' + t + ';box-sizing:border-box;';
  ov.style.left = (r.x - 4) + 'px'; ov.style.top = (r.y - 4) + 'px';
  ov.style.width = (r.width + 8) + 'px'; ov.style.height = (r.height + 8) + 'px';
  return { 命中: true, 候选数: es.length, 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] };
}, [sel, 边 || '8px']);
const 摘高亮 = () => p.evaluate(() => { const e = document.getElementById('__hl__'); if (e) e.remove(); return true; });

const IMG = 'node_gref4sw056';
const { b, p } = await openCanvas();
const R = readers(p);
let 起点transform = null; let 拖动量 = null;
try {
  await keyGuard(p); await settle(p, R); await setZoom(p, 60); await p.waitForTimeout(1200);
  起点transform = await 读transform();
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 积分: await R.credits() };
  console.log('起点', JSON.stringify(rec.起点));

  await 切工具('抓手工具');
  const bf = await p.evaluate((i) => { const n = document.querySelector('.react-flow__node[data-id="' + i + '"]'); const r = n.getBoundingClientRect();
    return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; }, IMG);
  拖动量 = [560 - (bf[2] + bf[0] / 2), 380 - (bf[3] + bf[1] / 2)];
  await 拖(Math.round(拖动量[0]), Math.round(拖动量[1]));
  await 切工具('选择工具');
  const 落 = await 可点落点(p, `.react-flow__node[data-id="${IMG}"]`, 4, 4);
  rec.落点 = 落;
  if (落.__err) throw new Error('落点失败');
  await p.mouse.click(落.x, 落.y); await p.waitForTimeout(2000);
  rec.选中数 = await selCount(p);
  console.log('选中数', rec.选中数);
  断言('⓪ 选中数 = 1', rec.选中数 === 1, { 选中数: rec.选中数 });

  // ---------- ① 浮动工具条 ----------
  rec.工具条 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
    .map((e) => { const r = e.getBoundingClientRect();
      return { 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)], 按钮数: e.querySelectorAll('button').length }; })
    .filter((z) => z.盒[0] > 0));
  rec.节点盒 = bf ? null : null;
  const 在屏工具条 = (rec.工具条 || []).filter((z) => z.盒[2] > 0 && z.盒[3] > 0);
  断言('① 工具条在屏内且 12 个按钮', 在屏工具条.length >= 1 && 在屏工具条.some((z) => z.按钮数 === 12), rec.工具条);
  rec.hl1 = await 高亮('[data-testid="node-toolbar"]', '8px');
  await p.waitForTimeout(400);
  await p.screenshot({ path: new URL('./112-image-node-floating-toolbar.png', 出图).pathname });
  rec.图1 = 'screenshots/112-image-node-floating-toolbar.png';
  await 摘高亮();
  console.log('① 已拍', rec.hl1, 在屏工具条[0]);

  // ---------- ② tools 菜单 ----------
  const t = await p.evaluate(() => { const e = document.querySelector('[data-toolbar-value="tools"]'); if (!e) return null;
    const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; });
  rec.tools钮 = t;
  断言('② 「工具」钮可点', !!t, t);
  if (t) {
    await p.mouse.click(t.x, t.y); await p.waitForTimeout(1800);
    rec.菜单 = await p.evaluate(() => { const ms = Array.from(document.querySelectorAll('[role=menu]')).filter((x) => x.getBoundingClientRect().width > 80);
      if (!ms.length) return { 命中: false }; const m = ms[ms.length - 1]; const r = m.getBoundingClientRect();
      return { 命中: true, 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
        逐字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200),
        项数: m.querySelectorAll('[role=menuitem]').length }; });
    落盘();
    console.log('② tools 菜单', JSON.stringify(rec.菜单));
    断言('③ tools 菜单打开：240×204、4 个 menuitem、逐字含「编辑」', (rec.菜单 || {}).命中 === true &&
      (rec.菜单 || {}).盒[0] === 240 && (rec.菜单 || {}).项数 === 4 && /编辑/.test(String((rec.菜单 || {}).逐字 || '')), rec.菜单);
    if ((rec.菜单 || {}).命中) {
      rec.hl2 = await 高亮('[role=menu]', '10px');
      await p.waitForTimeout(400);
      await p.screenshot({ path: new URL('./113-image-node-tools-menu.png', 出图).pathname });
      rec.图2 = 'screenshots/113-image-node-tools-menu.png';
      await 摘高亮();
      console.log('② 已拍');
    }
    for (let k = 0; k < 2; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
  }

  // ---------- ③ 右键九项 ----------
  await p.mouse.click(落.x, 落.y, { button: 'right' }); await p.waitForTimeout(1700);
  rec.右键 = await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-context-menu"]'); if (!d) return { 命中: false };
    const r = d.getBoundingClientRect();
    return { 命中: true, 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
      逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200), 项数: d.querySelectorAll('[role=menuitem]').length }; });
  console.log('③ 右键', JSON.stringify(rec.右键));
  断言('④ 右键菜单 200×372 九项', (rec.右键 || {}).命中 === true && (rec.右键 || {}).盒[0] === 200 &&
    (rec.右键 || {}).盒[1] === 372 && (rec.右键 || {}).项数 === 9, rec.右键);
  if ((rec.右键 || {}).命中) {
    rec.hl3 = await 高亮('[data-testid="canvas-context-menu"]', '8px');
    await p.waitForTimeout(400);
    await p.screenshot({ path: new URL('./114-image-node-context-menu-9-items.png', 出图).pathname });
    rec.图3 = 'screenshots/114-image-node-context-menu-9-items.png';
    await 摘高亮();
    console.log('③ 已拍');
  }

  // ---------- ④ 设置主体对话框 ----------
  const 保存项 = await p.evaluate(() => { const d = document.querySelector('[data-testid="canvas-context-menu"]'); if (!d) return null;
    const it = Array.from(d.querySelectorAll('[role=menuitem]')).find((x) => (x.innerText || '').indexOf('保存到主体库') >= 0);
    if (!it) return null; const r = it.getBoundingClientRect(); return { 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)] }; });
  断言('⑤ 菜单里找得到「保存到主体库」', !!保存项, 保存项);
  if (保存项) {
    const lp = await p.evaluate(([x, y, w, h]) => { for (let yy = Math.ceil(y) + 4; yy <= y + h - 4; yy += 2)
      for (let xx = Math.ceil(x) + 4; xx <= x + w - 4; xx += 2) { const el = document.elementFromPoint(xx, yy);
        const mi = el && el.closest('[role=menuitem]'); if (mi && (mi.innerText || '').indexOf('保存到主体库') >= 0) return { x: xx, y: yy }; }
      return { __err: 'no-point' }; }, 保存项.盒);
    await p.mouse.click(lp.x, lp.y); await p.waitForTimeout(2200);
    rec.对话框 = await p.evaluate(() => { const d = document.querySelector('[data-testid="subject-export-confirm-dialog"]'); if (!d) return { 命中: false };
      const r = d.getBoundingClientRect();
      const sv = Array.from(d.querySelectorAll('button')).find((x) => (x.innerText || '').trim() === '保存');
      return { 命中: true, 盒: [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)],
        逐字: (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300),
        保存禁用: sv ? (sv.getAttribute('aria-disabled') === 'true' || sv.getAttribute('data-disabled') === 'true') : null }; });
    落盘();
    console.log('④ 设置主体', JSON.stringify(rec.对话框));
    断言('⑥ 「设置主体」对话框 548×688 且「保存」禁用', (rec.对话框 || {}).命中 === true &&
      (rec.对话框 || {}).盒[0] === 548 && (rec.对话框 || {}).盒[1] === 688 && (rec.对话框 || {}).保存禁用 === true, rec.对话框);
    if ((rec.对话框 || {}).命中) {
      rec.hl4 = await 高亮('[data-testid="subject-export-confirm-dialog"]', '12px');
      await p.waitForTimeout(400);
      await p.screenshot({ path: new URL('./115-subject-export-confirm-dialog.png', 出图).pathname });
      rec.图4 = 'screenshots/115-subject-export-confirm-dialog.png';
      await 摘高亮();
      console.log('④ 已拍');
      rec.未点保存 = true;
    }
    for (let k = 0; k < 4; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
  }
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

try {
  const t = await p.evaluate(() => { const b = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]'); return b ? b.getAttribute('aria-label') : null; });
  if (t !== '抓手工具') await 切工具('抓手工具');
  if (拖动量) await 拖(-Math.round(拖动量[0]), -Math.round(拖动量[1]));
  let t2 = await 读transform(); const a = tx(起点transform) || []; let b2 = tx(t2) || [];
  for (let k = 0; k < 4 && a.length === 2 && b2.length === 2; k++) {
    const ex = a[0] - b2[0]; const ey = a[1] - b2[1];
    if (Math.abs(ex) < 0.05 && Math.abs(ey) < 0.05) break;
    await 拖(-Math.round(ex), -Math.round(ey)); t2 = await 读transform(); b2 = tx(t2) || [];
  }
  rec.归位后transform = t2;
  await 切工具('选择工具');
  for (let k = 0; k < 3 && (await selCount(p)) > 0; k++) {
    const e = await 空点(90, 600, 360, 930, 8); if (e.__err) break;
    await p.mouse.click(e.x, e.y); await p.waitForTimeout(800);
  }
} catch (e) { rec.归位异常 = String((e && e.stack) || e).slice(0, 600); 落盘(); }

await settle(p, R);
const mm = await R.minimap();
if (!mm || mm.ariaPressed !== 'true') { const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3); if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); } }
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), 浮层: await R.overlays(),
  zoom: await R.zoom(), 积分: await R.credits(), 边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length), transform: await 读transform() };
rec.断言全过 = 断言过; 落盘();
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');
await b.close();
