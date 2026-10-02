// 批次 95 · 收尾第 6 轮：按**正确的状态机**删 `node_ce47a7tnzq`，并补齐三态矩阵剩下的格子。
//
// �� 找到的机制链（b95e 四格对照，逐格都回读了 `editable` 与 chrome 计数）：
//     节点**本来已处于选中态** → 脚本的「点一下选中」其实是「点一下已选中」⇒ **直接进编辑态**
//     → 编辑态里右键菜单**弹不出来** ⇒ 收尾三轮全在这里空转。
//     ⇒ 收尾前置必须是「**未选中且非编辑态**」：先 Esc 到底，再点一次（这次才是选中），再右键。
//
// 顺带钉下的**文本节点三态矩阵**（60%）：
//     选中态：resize/outline/chromeHost/node-toolbar(2)/selToolbar/srcConnBtn 全在，`editable=0`
//     编辑态：以上**全部 0 个**，`editable=1`，**右键菜单弹不出来**
//     ⇒ 「编辑态工具条用了别的 testid」是**错的**问法：编辑态**根本没有**节点工具条。
//     ⇒ `canvas-editor-menu` 恒 1 个 `36×36@1061,12`（顶栏右侧），三态不变，**与节点无关**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const ID = 'node_ce47a7tnzq';
const out = { at: new Date().toISOString(), target: ID, steps: [] };

const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const nodeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });

// 状态读数：只读，不动画布。收尾脚本每一步都要先看这个再决定下一步。
const state = (label) => p.evaluate((l) => {
  const n = document.querySelector(`.react-flow__node[data-id="${l.id}"]`);
  return { label: l, present: !!n, selected: n ? n.classList.contains('selected') : null,
    editable: document.querySelectorAll('[contenteditable="true"],.ProseMirror').length,
    resize: document.querySelectorAll('[data-testid="text-node-resize-controls"]').length,
    nodeToolbar: document.querySelectorAll('[data-testid="node-toolbar"]').length,
    menuOpen: !!document.querySelector('[data-testid="canvas-context-menu"]'),
    menuItems: document.querySelectorAll('[role="menuitem"]').length };
}, { id: ID, label });

const step = async (label) => { const s = await state(label); out.steps.push(s);
  log(`${s.label}: present=${s.present} selected=${s.selected} editable=${s.editable} resize=${s.resize} nodeToolbar=${s.nodeToolbar} menu=${s.menuOpen}/${s.menuItems}`); return s; };

await step('s0-起点');

if (!(await ids()).includes(ID)) { log('✅ 节点已不在'); writeFileSync(new URL('./_tmp-b95f.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(0); }

// 步骤 1：Esc 到底。压测式——最多 4 次，每��都回读，直到「editable=0 且不再含本节点」。
for (let k = 1; k <= 4; k++) {
  const s = await state(`s1.${k}-Esc前`);
  if (s.editable === 0 && s.selected === false) { out.escTook = k - 1; log(`✅ Esc ${k - 1} 次即达「未选中且非编辑态」`); break; }
  await p.keyboard.press('Escape');
  await p.waitForTimeout(700);
  await step(`s1.${k}-Esc后`);
}
const clean = await state('s1z-归零后');
out.clean = clean;

// 步骤 2：现在点一次才是「选中」。点完立刻回读 editable，若又进了编辑态就说明前提不成立。
const pt = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  for (let fx = 0.05; fx <= 0.95; fx += 0.05) for (let fy = 0.05; fy <= 0.95; fy += 0.05) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    if (x < 0 || y < 0 || x > 1280 || y > 720) continue;
    if (document.elementFromPoint(x, y)?.closest('.react-flow__node') === n) return { x, y };
  }
  return null;
}, ID);
out.pt = pt;
log('落点：', JSON.stringify(pt));

if (pt) {
  await p.mouse.click(pt.x, pt.y);
  await p.waitForTimeout(1200);
  const s2 = await step('s2-单击后');
  // 步骤 3：右键。若 s2.editable 又是 1，直接 Esc 一次再右键（Esc 在编辑态只退编辑态、保留选中）。
  if (s2.editable > 0) {
    await p.keyboard.press('Escape');
    await p.waitForTimeout(800);
    await step('s3a-补Esc后');
  }
  await p.mouse.move(pt.x, pt.y);
  await p.waitForTimeout(250);
  await p.mouse.down({ button: 'right' });
  await p.waitForTimeout(260);
  await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1500);
  const s3 = await step('s3-右键后');
  out.menuOpen = s3.menuOpen;

  if (s3.menuOpen) {
    out.menu = await p.evaluate(() => {
      const m = document.querySelector('[data-testid="canvas-context-menu"]');
      const r = m.getBoundingClientRect();
      return { screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
        items: Array.from(m.querySelectorAll('[role="menuitem"]')).map((x) => {
          const b = x.getBoundingClientRect();
          return { text: x.innerText.replace(/\s+/g, ' ').trim(), w: Math.round(b.width), h: Math.round(b.height),
            disabled: x.getAttribute('aria-disabled') }; }) };
    });
    log('菜单：', out.menu.screen, '｜', out.menu.items.map((i) => i.text).join(' / '));
    out.deleteClick = await p.evaluate(() => {
      const m = document.querySelector('[data-testid="canvas-context-menu"]');
      const it = Array.from(m.querySelectorAll('[role="menuitem"]'))
        .find((x) => /^删除/.test(x.innerText.replace(/\s+/g, ' ').trim()) && x.getAttribute('aria-disabled') !== 'true');
      if (!it) return 'no-item'; it.click(); return 'clicked';
    });
    await p.waitForTimeout(1900);
    log('点删除：', out.deleteClick);
  }
}

out.left = (await ids()).includes(ID);
log(out.left ? '🔴 仍在' : '✅ 已删除');

if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(),
  left: (await ids()).filter((x) => ['node_ce47a7tnzq', 'node_tjf3grfajp'].includes(x)) };
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b95f.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
