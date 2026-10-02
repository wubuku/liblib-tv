// 批次 106 · b 轮：用**正确判据**重测，并把上一轮点乱的三颗钮**归位**。
//
// 🔴 a 轮读数全对、**判据全错**，两条都写下来：
//   ① 「小地图」我判据用「面板可见性」⇒ `miniVisible` 一直 `true`
//      （`canvas-minimap-portal-target` 那个容器**关着时也有非零矩形**），
//      于是读成「无变化」。**真信号是 `aria-pressed`：`false → true`，它其实响应了。**
//   ② 「显示连线」我判据用 `.react-flow__edge` 计数 ⇒ 恒为 **0**
//      （这张画布本来一条连线都没有，状态行也是 `0 edges`），
//      于是读成「无变化」。**真信号也是 `aria-pressed`：`true → false`，它其实响应了。**
//   ③ 「缩放」那格我判据写成 `String(after.zoom) !== …`，而 `dockRead()` **根本没返回
//      `zoom` 字段** ⇒ `undefined` 与字符串不等 ⇒ **假阳性「响应 ✅」**。
//      ⇒ **读数对象里没取的字段，判据里不许出现。**
//
// 💡 这三条合起来是同一句话：**判据必须落在「这个控件自己声明的状态」上**
//    （`aria-pressed`），而不是落在「它影响到别的东西上」——
//    后者会被「那个东西本来就没变」骗到。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString() };
const DOCK = '[data-testid="canvas-navigation-dock"]';
const save = () => writeFileSync(new URL('./_tmp-b106b.json', import.meta.url), JSON.stringify(out, null, 1));

const safeEval = async (fn, arg, tries = 8) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

// 只读**控件自己声明的状态**
const read = async (tag) => {
  const r = await safeEval((sel) => {
    const d = document.querySelector(sel);
    if (!d) return { __err: 'dock-null' };
    const get = (tid) => { const e = d.querySelector(`[data-testid="${tid}"]`); if (!e) return null;
      const q = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), pressed: e.getAttribute('aria-pressed'),
        x: Math.round(q.x), y: Math.round(q.y), w: Math.round(q.width), h: Math.round(q.height) }; };
    return { n: d.querySelectorAll('button,[role=button]').length,
      tool: get('canvas-pointer-tool-toggle'), mini: get('canvas-display-toggle-minimap'),
      conn: get('canvas-display-toggle-connections'), zoom: get('canvas-zoom-percent') };
  }, DOCK);
  out[tag] = r; save();
  log(`\n──── ${tag} ────`);
  log('  工具   :', JSON.stringify(r.tool));
  log('  小地图 :', JSON.stringify(r.mini));
  log('  连线   :', JSON.stringify(r.conn));
  log('  缩放   :', JSON.stringify(r.zoom));
  return r;
};
const click = async (btn, label) => {
  log(`  >>> 点「${label}」(${btn.x},${btn.y})`);
  await p.mouse.move(btn.x + btn.w / 2, btn.y + btn.h / 2); await p.waitForTimeout(450);
  await p.mouse.click(btn.x + btn.w / 2, btn.y + btn.h / 2);
  await p.waitForTimeout(1300);
};
const menuOpen = () => p.evaluate(() => Array.from(document.querySelectorAll('div,ul,section')).some((x) => {
  const q = x.getBoundingClientRect(); const t = x.innerText || '';
  return q.x < 300 && q.y > 500 && q.width > 150 && q.height > 120 &&
    getComputedStyle(x).visibility !== 'hidden' && /缩放至200%/.test(t); }));

out.s0 = await read('0-a轮结束时的当前状态');

// ---- 先把 a 轮点乱的三颗归位：工具 / 小地图 / 连线 ----
log('\n>>> 归位 a 轮的副作用');
if (out.s0.tool.aria !== '选择工具') { await click(out.s0.tool, '工具切换'); }
let cur = await read('1-工具已归位');
if (cur.mini.pressed === 'true') { await click(cur.mini, '小地图'); }
cur = await read('2-小地图已归位');
if (cur.conn.pressed === 'false') { await click(cur.conn, '显示连线'); }
cur = await read('3-三颗都回到起点状态');

// ---- 抓手态下重测三颗钮（判据 = aria-pressed / 菜单是否出现） ----
log('\n\n===== 进抓手态 =====');
await click(cur.tool, '工具切换');
out.pan0 = await read('4-抓手态-点之前');
const isPan = /抓手/.test(out.pan0.tool.aria || '');
log('  工具态 =', out.pan0.tool.aria, 'pressed =', out.pan0.tool.pressed, isPan ? '✅' : '🔴');
if (!isPan) { log('🔴 没进抓手态，停止'); save(); await b.close(); process.exit(1); }

out.trials = [];
// ① 小地图
{
  const before = out.pan0.mini.pressed;
  await click(out.pan0.mini, '小地图');
  const after = await read('t1-抓手态点完小地图');
  const toolNow = after.tool.aria;
  out.trials.push({ name: '小地图', tid: 'canvas-display-toggle-minimap', pressedBefore: before,
    pressedAfter: after.mini.pressed, resp: before !== after.mini.pressed,
    toolStayedPan: /抓手/.test(toolNow || ''), toolNow });
  log('   pressed', before, '→', after.mini.pressed, '｜ 工具态', toolNow, '｜ 响应', before !== after.mini.pressed ? '✅' : '🔴');
  await click(after.mini, '小地图（撤回）');
  const back = await read('t1b-撤回');
  out.trials[0].restored = back.mini.pressed === before;
}
// ② 显示连线
{
  const cur2 = await read('t2-前');
  const before = cur2.conn.pressed;
  await click(cur2.conn, '显示连线');
  const after = await read('t2-抓手态点完显示连线');
  const toolNow = after.tool.aria;
  out.trials.push({ name: '显示连线', tid: 'canvas-display-toggle-connections', pressedBefore: before,
    pressedAfter: after.conn.pressed, resp: before !== after.conn.pressed,
    toolStayedPan: /抓手/.test(toolNow || ''), toolNow });
  log('   pressed', before, '→', after.conn.pressed, '｜ 工具态', toolNow, '｜ 响应', before !== after.conn.pressed ? '✅' : '🔴');
  await click(after.conn, '显示连线（撤回）');
  const back = await read('t2b-撤回');
  out.trials[1].restored = back.conn.pressed === before;
}
// ③ 缩放值按钮：判据 = 缩放菜单有没有出现
{
  const cur3 = await read('t3-前');
  out.trials.push({ name: '缩放值按钮', tid: 'canvas-zoom-percent',
    ariaBefore: cur3.zoom.aria, pressedBefore: cur3.zoom.pressed });
  await click(cur3.zoom, '缩放值按钮');
  const opened = await menuOpen();
  out.trials[2].menuOpened = opened;
  log('   缩放菜单出现 =', opened, opened ? '✅' : '🔴');
  if (opened) {
    out.trials[2].items = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=menuitem],[role=option],li'))
      .map((e) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim(), v: getComputedStyle(e).visibility,
        w: Math.round(e.getBoundingClientRect().width), h: Math.round(e.getBoundingClientRect().height) }))
      .filter((x) => /^(放大视图|缩小视图|适配画布|缩放至)/.test(x.t) && x.w > 10 && x.h > 8 && x.v !== 'hidden')
      .map((x) => x.t));
    out.trials[2].levels = Array.from(new Set(out.trials[2].items));
    log('   菜单项：', JSON.stringify(out.trials[2].levels));
    // 抓手态下缩放菜单的每一项还能不能点？逐项只读，不点会改画布的那些
    await p.keyboard.press('Escape'); await p.waitForTimeout(800);
    out.trials[2].closedByEsc = !(await menuOpen());
    log('   Esc 关闭 =', out.trials[2].closedByEsc);
  }
}

out.endState = await read('5-终点');
save();
log('\n已落盘');
await b.close();
