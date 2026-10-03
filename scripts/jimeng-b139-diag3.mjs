// 批次 139 诊断三：**多选态**右键菜单的「删除」为什么扫不到可点像素。
//
// 🔑 diag2 的结果把问题劈成两半：
//   ① 臂 A（单选）右键 → 菜单 7 项、矩形 `(597,317,200,292)`、底 609 < 视口 720，
//      「删除 ⌫」在 `y=569..605`，扫描**第 2 个采样就命中**（`604,570`）。⇒ 单选态完全正常。
//   ② 臂 B（三选）**在右键之前**就断了：`可点落点` 对节点返回 `no-point`
//      —— 三选后节点上方盖着选中态/框选层，`elementFromPoint` 命中的不再是节点本体。
//      ⇒ 上一轮（f 轮 / 救援）报 `no-point` 的**可能不是同一个原因**，必须分开验。
//
// 本轮要回答的问题（三选态右键之后菜单长什么样）：
//   P1 菜单项数是否比单选态多？
//   P2 「删除 ⌫」是否被挤出**视口**（这会让扫描必然失败，且是真实的产品陷阱）？
//   P3 菜单是否被 `flex-direction: column-reverse` 翻转（这样「删除」在**最上面**，
//      靠近右键点，而不是被我以为的底部）？
//
// ⚠️ 右键落点：三选态下 `可点落点` 失效 ⇒ 改用「节点**可见部分**的中心」，
//   并**先断言该点不是 button / role=button**（不得误触任何控件）。
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import fs from 'node:fs';

const 三 = ['node_24njfrersn', 'node_sbczb38yf9', 'node_ywws1ng9bk'];
const rec = {};

/** 逐字同 diag2 的扫描（判据代码必须一致）。 */
const 扫描 = (p) => p.evaluate(() => {
  const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
    .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
  if (!els.length) return { __err: 'no-delete-item' };
  const e = els[0]; const r = e.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
    for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
      const h = document.elementFromPoint(x, y);
      if (h && (h === e || e.contains(h))) return { ok: true, x, y, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() };
    }
  const 统计 = {};
  for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 4)
    for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 8) {
      const h = document.elementFromPoint(x, y);
      const k = h ? (h.tagName + '.' + String(h.className || '').split(' ')[0]).slice(0, 46) : 'null';
      统计[k] = (统计[k] || 0) + 1;
    }
  return { ok: false, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(),
    菜单项矩形: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
    在视口内: r.y >= 0 && r.bottom <= innerHeight, 视口高: innerHeight,
    中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
    中心命中: (() => { const h = document.elementFromPoint(Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2));
      return h ? { tag: h.tagName, cls: String(h.className || '').split(' ')[0], role: h.getAttribute('role') } : null; })(),
    采样命中统计: 统计 };
});

const 菜单全貌 = (p) => p.evaluate(() => {
  const m = Array.from(document.querySelectorAll('[role=menu]')).find((e) => e.getBoundingClientRect().width > 1);
  if (!m) return null;
  const r = m.getBoundingClientRect();
  const s = getComputedStyle(m);
  return { 矩形: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
    底: Math.round(r.bottom), 顶: Math.round(r.top), 视口高: innerHeight,
    flexDirection: s.flexDirection, zIndex: s.zIndex,
    项数: m.querySelectorAll('[role=menuitem]').length,
    逐字: (m.innerText || '').replace(/\s+/g, ' ').trim(),
    项: Array.from(m.querySelectorAll('[role=menuitem]')).map((e) => { const rr = e.getBoundingClientRect();
      return { 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(), y: Math.round(rr.y), 底: Math.round(rr.bottom) }; }) };
});

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p);
  await settle(p, R);
  // 归零
  if (await R.selCount() > 0) {
    const 空 = await p.evaluate(() => {
      const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
      for (let y = 660; y >= 90; y -= 6) for (let x = 8; x <= innerWidth - 8; x += 6) {
        const h = document.elementFromPoint(x, y);
        if (h && h.classList && h.classList.contains('react-flow__pane')
          && !nodes.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return { x, y };
      }
      return null;
    });
    if (空) { await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1000); }
  }
  rec.起点 = { 状态行: await R.status(), 选中: await R.selCount() };

  // ---- 布三选
  const 落点 = [];
  for (let i = 0; i < 三.length; i++) {
    const r = await p.evaluate((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!n) return { __err: 'nf' };
      const rr = n.getBoundingClientRect();
      // 取「可见部分」的中心：先判正性再算面积（批次 137 a 轮立的规）
      const L = Math.max(rr.x, 4), R2 = Math.min(rr.right, innerWidth - 4);
      const T = Math.max(rr.y, 66), B2 = Math.min(rr.bottom, innerHeight - 66);
      if (!(R2 - L > 20 && B2 - T > 20)) return { __err: 'offscreen' };
      return { x: Math.round((L + R2) / 2), y: Math.round((T + B2) / 2) };
    }, 三[i]);
    落点.push(r);
    if (r.__err) { rec.落点失败 = { id: 三[i], r }; break; }
    const 命中 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y);
      return h ? { tag: h.tagName, 是控件: !!(h.closest('button,[role=button]')), 所属节点: h.closest('.react-flow__node') ? h.closest('.react-flow__node').getAttribute('data-id') : null } : null; }, [r.x, r.y]);
    rec['点前命中' + i] = 命中;
    if (命中 && 命中.是控件) { rec.落点失败 = { id: 三[i], 命中 }; break; }
    if (i === 0) await p.mouse.click(r.x, r.y);
    else { await p.keyboard.down('Shift'); await p.mouse.click(r.x, r.y); await p.keyboard.up('Shift'); }
    await p.waitForTimeout(800);
  }
  rec.落点 = 落点;
  rec.三选后 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));

  if (rec.三选后 && rec.三选后.length === 3) {
    // ---- 右键（用同一个可见中心，不要求命中节点本体）
    const r = 落点[0];
    await p.mouse.click(r.x, r.y, { button: 'right' });
    await p.waitForTimeout(1800);
    rec.三选菜单 = await 菜单全貌(p);
    rec.三选扫描 = await 扫描(p);
    // 对照：菜单项自身此刻的可见性与命中
    rec.删除项细节 = await p.evaluate(() => {
      const e = Array.from(document.querySelectorAll('[role=menuitem]'))
        .find((x) => /^删除/.test((x.innerText || '').replace(/\s+/g, '').trim()));
      if (!e) return { __err: 'not-found' };
      const rr = e.getBoundingClientRect(); const s = getComputedStyle(e);
      return { 矩形: { x: Math.round(rr.x), y: Math.round(rr.y), w: Math.round(rr.width), h: Math.round(rr.height) },
        pe: s.pointerEvents, vis: s.visibility, disp: s.display, op: s.opacity,
        在视口内: rr.top >= 0 && rr.bottom <= innerHeight, 视口高: innerHeight,
        ariaDisabled: e.getAttribute('aria-disabled'), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() };
    });
  }
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 500); }
fs.writeFileSync(new URL('./_tmp-b139-diag3.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 三选后: rec.三选后, 落点失败: rec.落点失败, 三选菜单: rec.三选菜单, 三选扫描: rec.三选扫描, 删除项细节: rec.删除项细节 }, null, 1));
await b.close();
