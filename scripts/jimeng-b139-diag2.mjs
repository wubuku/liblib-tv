// 批次 139 诊断二：**多选态**右键菜单里的「删除」到底点不点得到。
//
// 🔑 上一轮诊断已经证明：**单选**状态下右键，菜单 7 项齐全，
//   「删除 ⌫」在 `(765,569,192,36)`，中心 `[861,587]` 命中测试**通过**。
//   而建-删护栏（= 批次 137 那段逐字相同的代码）在**3 个多选**时连扫三遍都 `no-point`。
//   ⇒ 唯一变量就是「选中数」。本轮把两臂**并排**跑一遍，同一段扫描代码。
//
// 📌 立规用：判据代码必须**逐字相同**（批次 136/137 立的「两个批次的取证代码必须一模一样」），
//   否则「对照」就不是对照。
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { 可点落点, selCount } from './jimeng-b139-lib.mjs';
import fs from 'node:fs';

const 三 = ['node_24njfrersn', 'node_sbczb38yf9', 'node_ywws1ng9bk'];
const rec = {};

/** 与批次 137 护栏**逐字相同**的扫描（唯一差别：不点，只报）。 */
const 扫描 = (p) => p.evaluate(() => {
  const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
    .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
  if (!els.length) return { __err: 'no-delete-item' };
  const e = els[0]; const r = e.getBoundingClientRect();
  const 采样 = [];
  for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
    for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
      const h = document.elementFromPoint(x, y);
      采样.push([x, y, h ? (h === e || e.contains(h)) : false]);
      if (h && (h === e || e.contains(h))) return { x, y, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(), 总采样: 采样.length };
    }
  // 没点到 ⇒ 把采样结果带回来，看每个点命中了谁
  const 统计 = {};
  for (const [x, y, ok] of 采样) {
    const h = document.elementFromPoint(x, y);
    const k = h ? (h.tagName + '.' + String(h.className || '').split(' ')[0]).slice(0, 50) : 'null';
    统计[k] = (统计[k] || 0) + 1;
  }
  return { __err: 'no-point', 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(),
    菜单项矩形: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
    采样数: 采样.length, 采样命中统计: 统计,
    中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
    中心命中: (() => { const h = document.elementFromPoint(Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2));
      return h ? { tag: h.tagName, cls: String(h.className || '').split(' ')[0], role: h.getAttribute('role'),
        clsFull: String(h.className || '').slice(0, 120) } : null; })() };
});

const 菜单全貌 = (p) => p.evaluate(() => {
  const m = Array.from(document.querySelectorAll('[role=menu]')).find((e) => e.getBoundingClientRect().width > 1);
  if (!m) return null;
  const r = m.getBoundingClientRect();
  return { 矩形: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
    底: Math.round(r.bottom), 视口高: innerHeight,
    项数: m.querySelectorAll('[role=menuitem]').length,
    逐字: (m.innerText || '').replace(/\s+/g, ' ').trim(),
    项: Array.from(m.querySelectorAll('[role=menuitem]')).map((e) => { const rr = e.getBoundingClientRect();
      return { 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(), y: Math.round(rr.y), h: Math.round(rr.height),
        底: Math.round(rr.bottom), disabled: e.getAttribute('aria-disabled') }; }) };
});

const { b, p } = await openCanvas();
const R = readers(p);
try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 选中: await selCount(p) };

  // ---- 臂 A：单选（1 个）
  for (const [臂, 目标id] of [['A单选', 三[0]], ['B三选', null]]) {
    await settle(p, R);
    // 归零
    if (await selCount(p) > 0) {
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
    if (臂 === 'A单选') {
      const 落 = await 可点落点(p, `.react-flow__node[data-id="${目标id}"]`, 4, 4);
      rec['臂A落点'] = 落;
      if (!落.__err) { await p.mouse.click(落.x, 落.y); await p.waitForTimeout(1000); }
    } else {
      // 三选：依次点，第二个起用 Shift
      for (let i = 0; i < 三.length; i++) {
        const 落 = await 可点落点(p, `.react-flow__node[data-id="${三[i]}"]`, 4, 4);
        if (落.__err) { rec['臂B落点失败'] = { id: 三[i], 落 }; break; }
        if (i === 0) await p.mouse.click(落.x, 落.y);
        else { await p.keyboard.down('Shift'); await p.mouse.click(落.x, 落.y); await p.keyboard.up('Shift'); }
        await p.waitForTimeout(800);
      }
    }
    rec[臂 + '选中'] = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));

    // 右键目标（两臂都右键同一个节点）
    const 落 = await 可点落点(p, `.react-flow__node[data-id="${三[0]}"]`, 4, 4);
    if (落.__err) { rec[臂 + '右键落点失败'] = 落; continue; }
    await p.mouse.click(落.x, 落.y, { button: 'right' });
    await p.waitForTimeout(1800);
    rec[臂 + '菜单'] = await 菜单全貌(p);
    rec[臂 + '扫描'] = await 扫描(p);
  }
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 500); }
fs.writeFileSync(new URL('./_tmp-b139-diag2.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ A: { 选中: rec.A单选, 菜单: rec.A单选菜单, 扫描: rec.A单选扫描 },
  B: { 选中: rec.B三选, 菜单: rec.B三选菜单, 扫描: rec.B三选扫描 } }, null, 1));
await b.close();
