// 批次 170 t 轮：把子菜单切换阈值夹死在 (640, 648] 这 8 px 里。
//
// 🔴 上一轮（s）的问题：644 / 641 / 640 三档读到 `?` —— 不是「流内」，
//    是**菜单压根没开**（窄视口下画布被 UI 铺满，空白点找不到 / 右键落到了别的东西上）。
//    ⇒ 判据必须**先验菜单开没开**，没开就换点位重试，不能把「没读到」记成一种态。
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p: shared } = await openCanvas();
const p = shared;
const R = readers(p);

const tab = await b.contexts()[0].newPage();
await tab.goto(shared.url(), { waitUntil: 'domcontentloaded' });
await tab.waitForSelector('.react-flow__node', { timeout: 60000 });
await tab.waitForTimeout(3500);

const step = async (w) => {
  await tab.context().newCDPSession(tab).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride', { width: w, height: 720, deviceScaleFactor: 2, mobile: false });
  });
  await tab.waitForTimeout(1200);
  // 候选点位：先扫「确实是画布空白」，扫不到就退回几个固定点，逐个试
  const cands = await tab.evaluate(() => {
    const out = [];
    for (let y = 12; y < innerHeight - 8; y += 6)
      for (let x = 12; x < innerWidth - 8; x += 6) {
        const e = document.elementFromPoint(x, y);
        if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) out.push([x, y]);
      }
    out.push([Math.round(innerWidth / 2), Math.round(innerHeight * 0.3)]);
    out.push([10, 10]);
    return out.slice(0, 40);
  });
  for (const pt of cands) {
    await tab.keyboard.press('Escape');
    await tab.waitForTimeout(200);
    await tab.mouse.click(pt[0], pt[1], { button: 'right' });
    await tab.waitForTimeout(750);
    const d = await tab.evaluate(() => {
      const e = document.querySelector('[data-testid="canvas-context-menu"]');
      if (!e) return { 菜单没开: true };
      const mr = e.getBoundingClientRect();
      const trig = e.firstElementChild && e.firstElementChild.firstElementChild;
      let pos = null, sh = null;
      if (trig) for (const c of trig.querySelectorAll('div')) {
        if (c.querySelectorAll('[role=menuitem]').length >= 5) {
          pos = getComputedStyle(c).position;
          sh = Math.round(c.getBoundingClientRect().height);
          break;
        }
      }
      return {
        菜单: [Math.round(mr.width), Math.round(mr.height)],
        触发器高: trig ? Math.round(trig.getBoundingClientRect().height) : null,
        子菜单pos: pos, 子菜单高: sh,
      };
    });
    if (!d.菜单没开) return { w, 点位: pt, ...d };
  }
  return { w, 失败: '所有候选点位都没开出菜单', 候选数: cands.length };
};

const rows = [];
for (const w of [648, 646, 645, 644, 643, 642, 641, 640]) {
  const r = await step(w);
  rows.push(r);
  console.log(`  ${String(w).padStart(4)} → ${r.失败 ? '❌ ' + r.失败 : `${r.子菜单pos}  菜单 ${r.菜单[0]}×${r.菜单[1]}  触发器高 ${r.触发器高}`}`);
}
const fly = rows.filter((r) => r.子菜单pos === 'absolute').map((r) => r.w);
const inl = rows.filter((r) => r.子菜单pos === 'static').map((r) => r.w);
if (fly.length && inl.length) {
  console.log(`\n⇒ 阈值 ∈ (${Math.min(...inl)}, ${Math.max(...fly)}]`);
} else {
  console.log(`\n未能夹到（流出侧 ${JSON.stringify(fly)}／流内侧 ${JSON.stringify(inl)}）`);
}
await tab.keyboard.press('Escape'); await tab.waitForTimeout(300);
await tab.close();
console.log('\n共享页签复位:', JSON.stringify(await pinViewport(shared)), JSON.stringify({ sel: await R.selCount(), credits: await R.credits() }));
const fs = await import('node:fs');
fs.writeFileSync(new URL('./_tmp-b170t.json', import.meta.url), JSON.stringify(rows, null, 1));
await b.close();
