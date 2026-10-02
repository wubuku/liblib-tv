// 批次 95 · 收尾第 3 轮：**先查清节点右键菜单的真实 testid，再删**。
//
// 🔴 上一轮崩掉的真因不是「编辑态」：
//     `[data-testid="canvas-context-menu"]` 在整页 DOM 里**压根不存在**（b95b 全量枚举只有
//     `canvas-editor-menu` / `canvas-user-menu-trigger` / `canvas-context-menu-terminal-feedback`）。
//     a 轮在**空白处**右键读到过 `Canvas context menu` / `role=menu` / `240×172`，
//     所以我一直以为节点右键菜单也叫这个名字 —— **空白菜单与节点菜单很可能是两个不同的 testid**。
//
// 这一轮不猜：点中节点 → 右键 → 对**右键前后**的 DOM 做全量 diff，把新出现的容器逐个报出来
// （testid / role / class / 几何 / innerText），再决定点哪个「删除」。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const ID = 'node_ce47a7tnzq';
const out = { at: new Date().toISOString(), target: ID };

// 拍一张「DOM 指纹」：把所有带 testid 的元素 + 所有 role=menu/menuitem 的容器
// 归一成可比对的字符串集合。两次拍差集 = 右键动作新增了什么。
const snap = () => p.evaluate(() => {
  const s = new Set();
  for (const e of document.querySelectorAll('[data-testid]')) {
    const r = e.getBoundingClientRect();
    s.add(`tid|${e.getAttribute('data-testid')}|${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`);
  }
  for (const e of document.querySelectorAll('[role="menu"],[role="menuitem"],[role="menuitemcheckbox"]')) {
    const r = e.getBoundingClientRect();
    s.add(`role|${e.getAttribute('role')}|${(e.className || '').toString().slice(0, 40)}|${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}|${e.innerText.replace(/\s+/g, ' ').trim().slice(0, 30)}`);
  }
  return Array.from(s);
});

const hasMenu = () => p.evaluate(() => ({
  roleMenu: document.querySelectorAll('[role="menu"]').length,
  roleItem: document.querySelectorAll('[role="menuitem"]').length,
  tid: Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')).filter((t) => /menu/i.test(t)),
}));

out.pre = { menu: await hasMenu(), editable: await p.evaluate(() => document.querySelectorAll('[contenteditable="true"],.ProseMirror').length) };
const before = await snap();
log('右键前：', JSON.stringify(out.pre));

// 落点现取现用（不写死坐标——共享画布被别人动过）
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
if (!pt) { log('🔴 找不到落点'); writeFileSync(new URL('./_tmp-b95c.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(1); }

await p.mouse.click(pt.x, pt.y);
await p.waitForTimeout(1100);
out.sel = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
log('选中：', JSON.stringify(out.sel));

// 右键：move → down → 停 260ms → up（批次 22 的正解，`mouse.click({button:'right'})` 弹不出来）
await p.mouse.move(pt.x, pt.y);
await p.waitForTimeout(200);
await p.mouse.down({ button: 'right' });
await p.waitForTimeout(260);
await p.mouse.up({ button: 'right' });
await p.waitForTimeout(1500);

out.post = await hasMenu();
const after = await snap();
out.added = after.filter((x) => !before.includes(x));
out.removed = before.filter((x) => !after.includes(x));
log('右键后：', JSON.stringify(out.post));
log('新增 ' + out.added.length + ' 项：');
out.added.forEach((x) => log('   + ' + x));

writeFileSync(new URL('./_tmp-b95c.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
