// 批次 175 f 轮：截「图片节点右键菜单」—— 9 项、含 5 个面板里没有的快捷键。
// 选图片节点是因为它项数最多（9），且带「复制为图片 ⌘⇧C」这个只有它才有的键。
import fs from 'node:fs';
import path from 'node:path';
import { openCanvas, readers, settle } from './jimeng-b135-lib.mjs';
const DIR = path.resolve('docs/user-manual/jimeng-canvas/screenshots') + '/';
const { b, p } = await openCanvas();
const R = readers(p);
await settle(p, R);
await p.mouse.move(1250, 10); await p.waitForTimeout(500);
// 选中图片节点并把光标移到视野中间
await p.evaluate(() => { const n = document.querySelector('.react-flow__node-image') ||
  Array.from(document.querySelectorAll('.react-flow__node')).find((x) => /node-image/.test(x.className));
  n?.querySelector('[data-testid="flow-node-title"]')?.scrollIntoView({ block: 'center', inline: 'center' }); });
await p.waitForTimeout(900);
const pt = await p.evaluate(() => { const t = document.querySelector('.react-flow__node-image [data-testid="flow-node-title"]');
  if (!t) return null; const r = t.getBoundingClientRect(); return { id: t.closest('.react-flow__node').getAttribute('data-id'),
    标题: (t.innerText || '').trim().split('\n')[0], pt: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] }; });
console.log('目标', JSON.stringify(pt));
if (pt) {
  await p.mouse.click(pt.pt[0], pt.pt[1]); await p.waitForTimeout(1000);
  await p.mouse.move(pt.pt[0], pt.pt[1]); await p.waitForTimeout(300);
  await p.mouse.click(pt.pt[0], pt.pt[1], { button: 'right' }); await p.waitForTimeout(1500);
  const m = await p.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-context-menu"]');
    if (!e) return null; const r = e.getBoundingClientRect();
    return { 盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      innerText: e.innerText, 项数: e.querySelectorAll('[role=menuitem]').length };
  });
  console.log('菜单', JSON.stringify(m, null, 1));
  if (m) {
    // 高亮整个菜单
    await p.evaluate((盒) => {
      document.querySelectorAll('.__b175hl').forEach((e) => e.remove());
      const d = document.createElement('div'); d.className = '__b175hl';
      d.style.cssText = `position:fixed;left:${盒[0] - 4}px;top:${盒[1] - 4}px;width:${盒[2] + 8}px;height:${盒[3] + 8}px;` +
        `border:3px solid #ff8c00;border-radius:10px;pointer-events:none;z-index:2147483646`;
      document.body.appendChild(d);
    }, m.盒);
    const clip = { x: Math.max(0, m.盒[0] - 4), y: Math.max(0, m.盒[1] - 4), width: m.盒[2] + 8, height: m.盒[3] + 8 };
    await p.waitForTimeout(400);
    await p.screenshot({ path: DIR + '138-image-node-menu-shortcuts.png', clip });
    const f = DIR + '138-image-node-menu-shortcuts.png';
    const sha = (await import('node:crypto')).createHash('sha256').update(fs.readFileSync(f)).digest('hex');
    console.log('已拍 138，裁剪', JSON.stringify(clip), 'sha256', sha, fs.statSync(f).size, '字节');
  }
}
await p.evaluate(() => document.querySelectorAll('.__b175hl').forEach((e) => e.remove()));
await p.keyboard.press('Escape'); await p.waitForTimeout(600);
await p.mouse.click(640, 690); await p.waitForTimeout(700);
console.log('收尾', await R.status(), '|', await R.credits());
process.exit(0);
