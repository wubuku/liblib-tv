// 批次 170 l 轮：右键菜单**全变体**取证。
//
// k 轮拿到的三组尺寸里，(a) 空白 240×172、(b) 选中节点 200×292、(c) 窄窗里的 584 高。
// (c) 的 items=13 / seps=2 说明**存在嵌套 role=none 子列表** ⇒ j 轮那条「根下只有一个列表」
// 的模型不完整，不能只靠扁平公式反推。本轮把每个变体的**完整盒子树**落盘再算。
//
// 🔴 k 轮的工具缺陷（记在案）：`openMenu(tab,'node')` 在新页签里 10 次全部 `no-point` ——
//   它找 `.react-flow__node [data-testid="audio-node-empty"]`，新页签里节点没滚进视口也没渲染出该 testid。
//   ⇒ 变体枚举**必须回到共享页签**（那里已复现成功），视口实验才另开页签。
//
// ⛔ 只右键，不点任何菜单条目。
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import fs from 'node:fs';

const { b, p } = await openCanvas();
const R = readers(p);
const OUT = 'scripts/_tmp-b170l-variants.json';

const tree = () => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-context-menu"]');
  if (!e) return null;
  const walk = (el, d) => {
    const b = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return {
      d, tag: el.tagName, role: el.getAttribute('role'), testid: el.getAttribute('data-testid'),
      disabled: el.getAttribute('aria-disabled') || el.getAttribute('data-disabled') || null,
      rect: [Math.round(b.width), Math.round(b.height)],
      pad: cs.padding, gap: cs.gap, display: cs.display,
      own: el.children.length ? null : (el.innerText || '').trim().replace(/\n/g, '⏎').slice(0, 30),
      hasIcon: !!el.querySelector(':scope > svg'),
      kids: Array.from(el.children).map((c) => walk(c, d + 1)),
    };
  };
  return walk(e, 0);
});

// 找一个「不在节点上、不在面板上」的画布空白点
const blank = () => p.evaluate(() => {
  for (let y = 30; y < innerHeight - 30; y += 10)
    for (let x = 30; x < innerWidth - 30; x += 10) {
      const e = document.elementFromPoint(x, y);
      if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')
          && !e.closest('[role=menu],[role=dialog]')) return [x, y];
    }
  return null;
});
const nodeCenter = (sel) => p.evaluate((s) => {
  const e = document.querySelector(s);
  if (!e) return null;
  const n = e.closest('.react-flow__node') || e;
  n.scrollIntoView({ block: 'center', inline: 'center' });
  const r = n.getBoundingClientRect();
  return { pt: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], id: n.getAttribute('data-id') };
}, sel);

const TARGETS = [
  ['空白画布', async () => ({ pt: await blank() })],
  ['音频节点', async () => nodeCenter('[data-testid="audio-node-empty"]')],
  ['文本节点标题', async () => nodeCenter('.react-flow__node [data-testid="flow-node-title"]')],
  ['视频节点标题', async () => nodeCenter('.react-flow__node [data-testid="flow-node-title"]')],
  ['节点连接把手(左)', async () => nodeCenter('.react-flow__node [data-testid="flow-node-target-handle"]')],
  ['连接线中点', async () => p.evaluate(() => {
    const e = document.querySelector('.react-flow__edge, [data-testid^=edge], .react-flow__edge-path');
    if (!e) return null; const r = e.getBoundingClientRect();
    return { pt: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
  })],
];

const out = [];
for (const [tag, get] of TARGETS) {
  await p.keyboard.press('Escape'); await p.waitForTimeout(350);
  const g = await get();
  if (!g || !g.pt) { out.push({ tag, skipped: true }); console.log(`\n### ${tag}: 无目标`); continue; }
  const [x, y] = g.pt;
  await p.mouse.move(x, y); await p.waitForTimeout(150);
  await p.mouse.click(x, y, { button: 'right' });
  await p.waitForTimeout(900);
  const t = await tree();
  if (!t) { out.push({ tag, at: [x, y], noMenu: true }); console.log(`\n### ${tag} @(${x},${y}): 菜单未开`); continue; }
  const rec = { tag, at: [x, y], node: g.id || null, size: t.rect, hasIcon: t.hasIcon, pad: t.pad, gap: t.gap, root: t };
  out.push(rec);
  console.log(`\n### ${tag} @(${x},${y})  ${t.rect[0]}×${t.rect[1]}  图标=${t.hasIcon}  pad=${t.pad} gap=${t.gap}`);

  // 逐层打印（只打 role 节点，省略 svg/g/path）
  const pr = (n, ind = 0) => {
    if (n.role || ind === 0) {
      console.log(`  ${'  '.repeat(ind)}${n.role || n.tag}${n.disabled ? `[${n.disabled}]` : ''} ${n.rect[0]}×${n.rect[1]} gap=${n.gap} pad=${n.pad}${n.icon ? ' svg' : ''}${n.own ? ' · ' + n.own : ''}`);
    }
    for (const c of n.kids) pr(c, ind + 1);
  };
  pr(t);
}
fs.writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log(`\n落盘: ${OUT}`);

// 复原
await p.keyboard.press('Escape'); await p.waitForTimeout(300);
const bp = await blank();
if (bp) await p.mouse.click(bp[0], bp[1]);
await p.waitForTimeout(500);
await p.keyboard.press('Escape'); await p.waitForTimeout(300);
console.log('收尾:', JSON.stringify({ status: await R.status(), sel: await R.selCount(), credits: await R.credits() }),
  '残留菜单=', await p.evaluate(() => document.querySelectorAll('[data-testid="canvas-context-menu"]').length));
await b.close();
