// 批次 170 k 轮：**余量 16 的夹取边界**。
//
// 机制（j 轮解出，已逐项复算通过）：
//   根 div[role=menu][data-testid=canvas-context-menu]，padding 4px
//   └ div[role=none]（gap:4px）→ N 个 div[role=menuitem]（每个 36 高）+ M 个 div[role=separator]（4 高）
//   高 = 8 + 36N + 4M + 4(N+M−1)   —— 实测 200×292（N=7,M=1）与 240×172（N=4,M=1）都精确命中
//   宽分两档：带图标 240 / 不带图标 200（条目宽 = 菜单宽 − 8）
// 夹取：class 逐字含 max-w-[calc(100vw_-_16px)] max-h-[calc(100vh_-_16px)]
//
// ⇒ **预测**（先预测再打）：
//   P1 空白菜单宽夹取门槛 vw = 240+16 = 256：vw=256 → 仍 240；vw=250 → 234
//   P2 选中菜单高夹取门槛 vh = 292+16 = 308：vh=324 → 仍 292；vh=300 → 284
//   P3 极端窄窗下两条规则**同时**夹取，且翻转公式用 8（不是 16）⇒ 翻到贴边时 left = vw−8−w = 8 ≥ 0
//
// 🔴 纪律（批次 165-a 教训）：多视口测量**必须在新开页签里做**，
//    `Emulation.setDeviceMetricsOverride` 会改窗口几何；收尾要用 pinViewport() 复位共享页签。
import { openCanvas, readers, PORT } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p: shared } = await openCanvas();
const URL_ = shared.url();

/** 可参数化的钉视口（与 pinViewport 同一 CDP 调用，只是把尺寸放开）。 */
async function pin(page, w, h) {
  await page.context().newCDPSession(page).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride',
      { width: w, height: h, deviceScaleFactor: 2, mobile: false });
  });
  await page.waitForTimeout(500);
  const vp = await page.evaluate(() => ({ w: innerWidth, h: innerHeight }));
  if (vp.w !== w || vp.h !== h) throw new Error(`钉视口失败：要 ${w}×${h}，实得 ${JSON.stringify(vp)}`);
  return vp;
}

const probe = async (page) => page.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-context-menu"]');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  const items = e.querySelectorAll('[role=menuitem]').length;
  const seps = e.querySelectorAll('[role=separator]').length;
  return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height), items, seps };
});

/** 打开指定变体的菜单，返回几何。blank=空白画布, node=选中节点 */
async function openMenu(page, kind) {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(250);
  const pt = await page.evaluate((k) => {
    if (k === 'blank') {
      for (let y = 20; y < innerHeight - 10; y += 10)
        for (let x = 20; x < innerWidth - 10; x += 10) {
          const e = document.elementFromPoint(x, y);
          if (e && e.closest('.react-flow__pane') && !e.closest('.react-flow__node')) return [x, y];
        }
      return null;
    }
    const n = document.querySelector('.react-flow__node [data-testid="audio-node-empty"]');
    if (!n) return null;
    const node = n.closest('.react-flow__node');
    const r = node.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
  }, kind);
  if (!pt) return { err: 'no-point' };
  await page.mouse.move(pt[0], pt[1]);
  await page.waitForTimeout(120);
  await page.mouse.click(pt[0], pt[1], { button: 'right' });
  await page.waitForTimeout(800);
  return { anchor: pt, ...(await probe(page)) };
}

// —— 在新页签里做 ——
const tab = await b.contexts()[0].newPage();
await tab.goto(URL_, { waitUntil: 'domcontentloaded' });
await tab.waitForSelector('.react-flow__node', { timeout: 60000 });
await tab.waitForTimeout(3500);

const SIZES = [
  [1280, 720, '对照（应无夹取）'],
  [256, 720, 'P1 门槛上：100vw−16 = 240'],
  [250, 720, 'P1 门槛下：100vw−16 = 234'],
  [220, 720, '更窄：100vw−16 = 204'],
  [200, 720, '极窄：100vw−16 = 184'],
  [1280, 324, 'P2 门槛上：100vh−16 = 308'],
  [1280, 300, 'P2 门槛下：100vh−16 = 284'],
  [1280, 200, '极矮：100vh−16 = 184'],
  [256, 324, '两轴同时：100vw−16=240 / 100vh−16=308'],
  [200, 200, '双极窄'],
];

const rows = [];
for (const [w, h, note] of SIZES) {
  await pin(tab, w, h);
  const a = await openMenu(tab, 'blank');
  await tab.keyboard.press('Escape'); await tab.waitForTimeout(250);
  const bmenu = await openMenu(tab, 'node');
  const vw = await tab.evaluate(() => innerWidth), vh = await tab.evaluate(() => innerHeight);
  const r = { vp: [w, h], actual: [vw, vh], note, blank: a, node: bmenu };
  rows.push(r);
  console.log(`\n[${w}×${h}] ${note}`);
  console.log('   空白菜单:', JSON.stringify(a));
  console.log('   选中菜单:', JSON.stringify(bmenu));
}

await tab.keyboard.press('Escape');
await tab.close();

// —— 收尾：共享页签必须 pinViewport 复位（165-a 教训）——
const vp = await pinViewport(shared);
console.log('\n共享页签已 pinViewport 复位:', JSON.stringify(vp));
console.log('共享页签 state:', JSON.stringify({
  status: await readers(shared).status(),
  credits: await readers(shared).credits(),
}));
console.log('\n=== 预测核对 ===');
const g = (v, ax) => v - ax;
for (const r of rows) {
  const [w, h] = r.vp;
  const pw = Math.max(0, w - 16), ph = Math.max(0, h - 16);
  const pb = r.blank && r.blank.w ? Math.min(240, pw) : null;
  const pn = r.node && r.node.w ? Math.min(200, pw) : null;
  const hn = r.node && r.node.h ? Math.min(292, ph) : null;
  console.log(`  ${w}×${h}: 空白宽 实测${r.blank && r.blank.w} 预测${pb} ${r.blank && r.blank.w === pb ? '✓' : '✗'}` +
    ` | 选中宽 实测${r.node && r.node.w} 预测${pn} ${r.node && r.node.w === pn ? '✓' : '✗'}` +
    ` | 选中高 实测${r.node && r.node.h} 预测${hn} ${r.node && r.node.h === hn ? '✓' : '✗'}`);
}
await b.close();
