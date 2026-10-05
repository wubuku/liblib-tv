// 批次 170 q 轮：补三件事。
//
// Q1 「新建节点」触发器在 250 宽下从 36 撑到 **448**（= 子菜单 404 + 本行 36 + 2×4 间隙）
//    ⇒ 子菜单是不是从 position:absolute 变成了流内？读它的 computed，别靠「448 ≈ 404+44」凑数。
// Q2 菜单**除了 Esc 还能怎么关**？（f 轮只验了「鼠标移开不关」与「Esc 能关」，
//    用户真正会做的是「点别处」—— 这一条手册里必须写准。）
// Q3 菜单开着时画布是不是真的点不动？（e 轮验过 elementFromPoint 命中菜单，现在补「点空白会怎样」）
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p: shared } = await openCanvas();
const p = shared;                 // 第一部分用共享页签（openCanvas 只连不导航）
const R = readers(p);
const rec = { 批次: '170q' };

// ══ 第一部分：共享页签（1280×720）测关闭方式 ══
const openBlank = async () => {
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
  const pt = await p.evaluate(() => {
    for (let y = 30; y < innerHeight - 30; y += 10)
      for (let x = 30; x < innerWidth - 30; x += 10) {
        const e = document.elementFromPoint(x, y);
        if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) return [x, y];
      }
    return null;
  });
  await p.mouse.click(pt[0], pt[1], { button: 'right' });
  await p.waitForTimeout(900);
  return pt;
};
const has = () => p.evaluate(() => !!document.querySelector('[data-testid="canvas-context-menu"]'));
const blankPt = () => p.evaluate(() => {
  for (let y = 30; y < innerHeight - 30; y += 10)
    for (let x = 30; x < innerWidth - 30; x += 10) {
      const e = document.elementFromPoint(x, y);
      if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')
          && !e.closest('[data-testid="canvas-context-menu"]')) return [x, y];
    }
  return null;
});

rec.关闭方式 = [];
{
  await openBlank();
  const bp = await blankPt();
  await p.mouse.click(bp[0], bp[1]);        // 点菜单外的画布空白
  await p.waitForTimeout(900);
  rec.关闭方式.push({ 动作: '点菜单外空白', 点位: bp, 菜单还在: await has(), 选中数: await R.selCount() });
  console.log('点空白:', JSON.stringify(rec.关闭方式[0]));

  await openBlank();
  await p.keyboard.press('Escape');
  await p.waitForTimeout(700);
  rec.关闭方式.push({ 动作: '按 Esc', 菜单还在: await has() });
  console.log('按 Esc:', JSON.stringify(rec.关闭方式[1]));

  // 菜单开着时，点菜单**下面的节点**会怎样？（吞点击的复现 + 后果）
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
  const npt = await p.evaluate(() => {
    const n = document.querySelector('.react-flow__node [data-testid="audio-node-empty"]').closest('.react-flow__node');
    const r = n.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  });
  await p.mouse.click(npt[0], npt[1], { button: 'right' });
  await p.waitForTimeout(900);
  const before = await R.selCount();
  // 现在菜单盖在节点上；换个点：点节点上「菜单没盖住」的部分
  await p.mouse.click(npt[0], npt[1] - 70);
  await p.waitForTimeout(900);
  rec.遮挡后果 = {
    说明: '右键菜单开着时，再左键点同一节点',
    节点: npt, 点击位: [npt[0], npt[1] - 70],
    点击前选中数: before,
    点击后选中数: await R.selCount(),
    点击后菜单还在: await has(),
  };
  console.log('遮挡后果:', JSON.stringify(rec.遮挡后果));
  await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  // 复原
  const bp2 = await blankPt();
  if (bp2) { await p.mouse.click(bp2[0], bp2[1]); await p.waitForTimeout(500); }
  await p.keyboard.press('Escape'); await p.waitForTimeout(300);
}
rec.收尾A = { status: await R.status(), sel: await R.selCount(), credits: await R.credits(),
  残留: await p.evaluate(() => document.querySelectorAll('[data-testid="canvas-context-menu"]').length) };
console.log('收尾A', JSON.stringify(rec.收尾A));

// ══ 第二部分：新页签 + 250 宽，读子菜单的 computed ══
const tab = await b.contexts()[0].newPage();
await tab.goto(shared.url(), { waitUntil: 'domcontentloaded' });
await tab.waitForSelector('.react-flow__node', { timeout: 60000 });
await tab.waitForTimeout(3500);
rec.子菜单随宽度 = [];
for (const [w, h] of [[1280, 720], [400, 720], [250, 720], [210, 720]]) {
  await tab.context().newCDPSession(tab).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
  });
  await tab.waitForTimeout(1400);
  await tab.keyboard.press('Escape'); await tab.waitForTimeout(300);
  const pt = await tab.evaluate(() => {
    for (let y = 20; y < innerHeight - 10; y += 10)
      for (let x = 20; x < innerWidth - 10; x += 10) {
        const e = document.elementFromPoint(x, y);
        if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) return [x, y];
      }
    return null;
  });
  if (!pt) { rec.子菜单随宽度.push({ 视口: [w, h], 跳过: '找不到空白点' }); continue; }
  await tab.mouse.click(pt[0], pt[1], { button: 'right' });
  await tab.waitForTimeout(1100);
  const d = await tab.evaluate(() => {
    const e = document.querySelector('[data-testid="canvas-context-menu"]');
    if (!e) return null;
    const mr = e.getBoundingClientRect();
    const trig = e.firstElementChild.firstElementChild;      // 「新建节点」那一行的 position:relative 包装
    const tr = trig.getBoundingClientRect();
    // 子菜单 = 包装层里 position 不是 static 的那个
    let sub = null;
    for (const c of trig.querySelectorAll('div')) {
      const cs = getComputedStyle(c);
      const r = c.getBoundingClientRect();
      if (cs.position === 'absolute' || cs.position === 'static' ? c.querySelectorAll('[role=menuitem]').length >= 5 : false) {
        sub = { pos: cs.position, vis: cs.visibility, disp: cs.display, w: Math.round(r.width), h: Math.round(r.height),
                style: c.getAttribute('style'), className: c.getAttribute('class'),
                x: Math.round(r.x), y: Math.round(r.y) };
        break;
      }
    }
    return {
      菜单: [Math.round(mr.x), Math.round(mr.y), Math.round(mr.width), Math.round(mr.height)],
      触发器盒: [Math.round(tr.width), Math.round(tr.height)],
      触发器pos: getComputedStyle(trig).position,
      子菜单: sub,
    };
  });
  rec.子菜单随宽度.push({ 视口: [w, h], ...d });
  console.log(`\n[${w}×${h}]`, JSON.stringify(d));
}
await tab.keyboard.press('Escape'); await tab.waitForTimeout(300);
await tab.close();
console.log('\n共享页签复位:', JSON.stringify(await pinViewport(shared)));
rec.收尾B = { status: await R.status(), sel: await R.selCount(), credits: await R.credits() };
console.log('收尾B', JSON.stringify(rec.收尾B));

const fs = await import('node:fs');
fs.writeFileSync(new URL('./_tmp-b170q.json', import.meta.url), JSON.stringify(rec, null, 1));
await b.close();
