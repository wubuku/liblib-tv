// 批次 105 · h 轮：趁靶子节点还在，取**有资源的视频节点**的右键菜单。
//
// 🎯 顺带结掉 `duplicate-delete-history.md:75-83` 那条挂了很久的旧账：
//   「『保存到主体库』是否出现在**有资源的媒体节点**上，**仍未验证**」
//   —— 页面里写「**空**视频节点（无论有无资源）都没有这一项，也没有『复制为图片』」，
//   而「**无论有无资源**」这半句正是没验的那半句。
//   批次 22 验过**图片**（有资源 ⇒ 200×372 九项含该项）、批次 30 验过**主体**（空态就有）。
//   **视频**这一格至今空着。
//
// ⚠️ 本轮**只读菜单、绝不点任何一项**（菜单里有删除/下载/保存到主体库，全是写操作）。
//   读完立刻按 Esc 关掉。
//
// 右键姿势是定的：批次 22 起就是 `move → down → 停 260ms → up`；
// `mouse.click(…, {button:'right'})` 弹不出来。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), selfId: 'node_kk93zz7qzx' };
const SELF = out.selfId;

const box = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  // 落点取卡片**中心偏上** 1/4 处：躲开底部的播放控件行
  return { x: r.x + r.width / 2, y: r.y + r.height / 4, w: r.width, h: r.height };
}, SELF);
log('节点屏幕矩形：', JSON.stringify(box));
out.box = box;

await p.mouse.move(box.x, box.y);
await p.waitForTimeout(500);
await p.mouse.down({ button: 'right' });
await p.waitForTimeout(260);
await p.mouse.up({ button: 'right' });
await p.waitForTimeout(1200);

const menu = await p.evaluate(() => {
  const cands = Array.from(document.querySelectorAll('body > div, [role=menu], [data-testid*=menu]'))
    .map((e) => { const r = e.getBoundingClientRect();
      return { el: e, r, tid: e.getAttribute('data-testid'), role: e.getAttribute('role'), vis: getComputedStyle(e).visibility }; })
    .filter((x) => x.r.width > 40 && x.r.height > 40 && x.vis !== 'hidden');
  if (!cands.length) return null;
  // 取面积最大的那个浮层当作菜单
  cands.sort((a, b) => (b.r.width * b.r.height) - (a.r.width * a.r.height));
  const m = cands[0];
  const items = Array.from(m.el.querySelectorAll('[role=menuitem], button, [role=button]')).map((e) => ({
    text: e.innerText.replace(/\s+/g, ' ').trim(),
    disabled: e.getAttribute('aria-disabled'),
    cls: (e.getAttribute('class') || '').slice(0, 60),
  })).filter((x) => x.text);
  return { tid: m.tid, role: m.role, w: Math.round(m.r.width), h: Math.round(m.r.height), x: Math.round(m.r.x), y: Math.round(m.r.y),
    text: m.el.innerText.replace(/\s+/g, ' ').trim(), items, n: items.length };
});
out.menu = menu;
log('\n右键菜单：', JSON.stringify(menu, null, 1));

// 高度是不是 items 数的整数倍？（批次 22 记过 372/9，本轮用来对账）
if (menu && menu.n) log(`\n算术：${menu.h} / ${menu.n} = ${(menu.h / menu.n).toFixed(2)}`);

log('\n按 Esc 关掉（不点任何一项）');
await p.keyboard.press('Escape');
await p.waitForTimeout(900);
out.afterEsc = await p.evaluate(() => {
  const c = Array.from(document.querySelectorAll('[role=menu], [data-testid*=menu]'))
    .map((e) => { const r = e.getBoundingClientRect(); return { w: r.width, h: r.height, vis: getComputedStyle(e).visibility }; })
    .filter((x) => x.w > 40 && x.h > 40 && x.vis !== 'hidden');
  return { stillOpen: c.length, sel: (document.body.innerText.match(/(\d+) selected/) || [])[1] };
});
log('Esc 之后：', JSON.stringify(out.afterEsc));

writeFileSync(new URL('./_tmp-b105h.json', import.meta.url), JSON.stringify(out, null, 1));
log('已落盘');
await b.close();
