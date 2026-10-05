// 批次 170 v 轮：验「内联态」的用户可见后果。
//
// 内联态（640×720 空白右键，批次 170 u 轮）读到的子菜单是
//   class: `… octo-context-menu--compact-surface … transition-opacity invisible opacity-0`
//   style: `padding: 4px; width: 200px;`  position: relative/static
//   尺寸: 212/232×404
// ⇒ **`visibility:hidden` + `opacity:0` 却仍占 404 px 布局高度**
//    ⇒ 预测：菜单从 172 变成 584，但那块区域**看不见、也点不到**（「新建节点」点不开）。
// 手动验证 4 件事：① 高 584 ② 子菜单 rect 404 ③ computed vis/opacity ④ 悬停「新建节点」能否显形。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const DIR = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url).pathname;
const { b, p: shared } = await openCanvas();
const p = shared;
const R = readers(p);
const rec = { 批次: '170v' };

const tab = await b.contexts()[0].newPage();
await tab.goto(shared.url(), { waitUntil: 'domcontentloaded' });
await tab.waitForSelector('.react-flow__node', { timeout: 60000 });
await tab.waitForTimeout(3500);
await tab.context().newCDPSession(tab).then(async (s) => {
  await s.send('Emulation.setDeviceMetricsOverride', { width: 640, height: 720, deviceScaleFactor: 2, mobile: false });
});
await tab.waitForTimeout(1500);

const pt = await tab.evaluate(() => {
  for (let y = 12; y < innerHeight - 8; y += 6)
    for (let x = 12; x < 200; x += 6) {
      const e = document.elementFromPoint(x, y);
      if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) return [x, y];
    }
  return null;
});
await tab.mouse.click(pt[0], pt[1], { button: 'right' });
await tab.waitForTimeout(1000);

const read = () => tab.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-context-menu"]');
  if (!e) return null;
  const mr = e.getBoundingClientRect();
  const trig = e.firstElementChild.firstElementChild;
  const tr = trig.getBoundingClientRect();
  let sub = null;
  for (const c of trig.querySelectorAll('div')) {
    if (c.querySelectorAll('[role=menuitem]').length >= 5) {
      const cs = getComputedStyle(c), r = c.getBoundingClientRect();
      sub = {
        pos: cs.position, vis: cs.visibility, op: cs.opacity, disp: cs.display,
        盒: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        pe: cs.pointerEvents,
        条目数: c.querySelectorAll('[role=menuitem]').length,
        首个条目文字: (c.querySelector('[role=menuitem]') || { innerText: '' }).innerText.trim().split('\n')[0],
        class含不可见: /invisible|opacity-0/.test(c.getAttribute('class') || ''),
      };
      break;
    }
  }
  return { 菜单: [Math.round(mr.x), Math.round(mr.y), Math.round(mr.width), Math.round(mr.height)],
    触发器: [Math.round(tr.x), Math.round(tr.y), Math.round(tr.width), Math.round(tr.height)], 子菜单: sub };
});

rec.悬停前 = await read();
console.log('悬停前:', JSON.stringify(rec.悬停前));

// 悬停「新建节点」那一行，看子菜单能否显形
const trig = await tab.evaluate(() => {
  const t = document.querySelector('[data-testid="canvas-context-menu"]').firstElementChild.firstElementChild;
  const r = t.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + 18)];   // 取本行自己的 36px，别落到内联子菜单里
});
await tab.mouse.move(trig[0], trig[1]);
await tab.waitForTimeout(1200);
rec.悬停后 = await read();
console.log('悬停后:', JSON.stringify(rec.悬停后));

// 截图（画高亮框）
await tab.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-context-menu"]');
  const r = e.getBoundingClientRect();
  const d = document.createElement('div');
  d.style.cssText = `position:fixed;left:${r.x - 4}px;top:${r.y - 4}px;width:${r.width + 8}px;height:${r.height + 8}px;` +
    `border:3px solid #ff8c00;border-radius:14px;pointer-events:none;z-index:2147483646`;
  document.body.appendChild(d);
});
await tab.waitForTimeout(300);
await tab.screenshot({ path: DIR + '132-canvas-rightmenu-inline-gap-640px.png' });
rec.图 = 'screenshots/132-canvas-rightmenu-inline-gap-640px.png';

const 验 = (名, ok, 详情) => { console.log((ok ? '  ✅ ' : '  ❌ ') + 名 + (ok ? '' : ' → ' + JSON.stringify(详情))); rec['断言_' + 名] = ok; };
验('① 菜单高度是 584（比宽屏的 172 多 412）', rec.悬停前.菜单[3] === 584, rec.悬停前.菜单);
验('② 子菜单块高 404，且 visibility:hidden / opacity:0',
  rec.悬停前.子菜单 && rec.悬停前.子菜单.盒[3] === 404 && rec.悬停前.子菜单.vis === 'hidden' && rec.悬停前.子菜单.op === '0',
  rec.悬停前.子菜单);
验('③ 子菜单 class 逐字含 invisible/opacity-0', rec.悬停前.子菜单 && rec.悬停前.子菜单.class含不可见, rec.悬停前.子菜单);
验('④ 悬停「新建节点」后子菜单仍不可见 ⇒ 窄窗下这一项**点不开**',
  rec.悬停后.子菜单 && rec.悬停后.子菜单.vis === 'hidden', rec.悬停后.子菜单);

await tab.keyboard.press('Escape'); await tab.waitForTimeout(300);
await tab.close();
console.log('\n共享页签复位:', JSON.stringify(await pinViewport(shared)), JSON.stringify({ sel: await R.selCount(), credits: await R.credits() }));
rec.收尾 = { status: await R.status(), credits: await R.credits() };
fs.writeFileSync(new URL('./_tmp-b170v.json', import.meta.url), JSON.stringify(rec, null, 1));
await b.close();
