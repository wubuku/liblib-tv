// Batch DH-2：把 DH-1 留下的那个追问做完 ——
// **在 `prefers-reduced-motion: no-preference` 下，`z-[180]` 的 opacity 会不会亮？**
//
// 旧账（AUDIT:224）只说「用 no-preference 重开，横幅 opacity 仍是 0」——
// 但那测的是 **z-[305]**。**z-[180] 从来没在 no-preference 下量过 opacity。**
// 而 z-[180] 的 class 里明确写着 `motion-safe:transition-opacity` ⇒ 它就是靠过渡淡入的，
// ⭐ **在 reduce 下过渡被关掉，很可能正是它「永远不亮」的原因。**
//
// 做法：同一个浏览器会话里，先量 reduce 下的读数，
//      再用 CDP 覆盖成 no-preference，**戳同样的动作**，逐次量「祖先链 opacity 连乘」。
// ⚠️ 两边必须用**同一套动作**，否则不可比。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = {};

const { browser, page } = await launch();   // 默认 reduce
await open(page, URL_);
await closePromos(page);
await page.waitForTimeout(1500);
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2800);
for (let i = 0; i < 3; i += 1) {
  const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
  if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(600);
}
const pk = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
  if (!b) return null; const r = b.getBoundingClientRect();
  return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
});
if (pk) { await page.mouse.click(pk[0], pk[1]); await page.waitForTimeout(1200); }

// ⭐ 累计 opacity：沿祖先链连乘
const probe = () => page.evaluate(() => {
  const 找 = (z) => [...document.querySelectorAll('body *')].find((e) => {
    const s = getComputedStyle(e);
    return s.position === 'fixed' && s.zIndex === z && e.getBoundingClientRect().width > 1000;
  });
  const 读 = (el) => {
    if (!el) return null;
    let acc = 1; const 链 = [];
    for (let p = el; p; p = p.parentElement) {
      const o = parseFloat(getComputedStyle(p).opacity);
      const vis = getComputedStyle(p).visibility;
      acc *= Number.isNaN(o) ? 1 : o;
      链.push({ tag: p.tagName.toLowerCase(), opacity: getComputedStyle(p).opacity, visibility: vis });
      if (p === document.body) break;
    }
    return { 累计: Math.round(acc * 1000) / 1000, 链 };
  };
  const t180 = 找('180');
  const t305 = [...document.querySelectorAll('body *')].find((e) => {
    const s = getComputedStyle(e);
    return s.position === 'fixed' && s.zIndex === '305';
  });
  return {
    reduce: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    z180: 读(t180), z180动画数: t180 ? (() => { try { return t180.getAnimations().length; } catch { return -1; } })() : -1,
    z305: 读(t305),
  };
});

const 动作 = [
  { 名: '基线（什么都没点）', fn: async () => {} },
  { 名: '空白处左键拖（画选区）', fn: async () => { await page.mouse.move(400, 300); await page.mouse.down(); await page.mouse.move(600, 420, { steps: 8 }); await page.waitForTimeout(300); await page.mouse.up(); } },
  { 名: 'Space+拖（平移）', fn: async () => { await page.keyboard.down('Space'); await page.mouse.move(400, 300); await page.mouse.down(); await page.mouse.move(550, 380, { steps: 6 }); await page.waitForTimeout(300); await page.mouse.up(); await page.keyboard.up('Space'); } },
  { 名: '点节点⤢（大编辑器）', fn: async () => { await page.evaluate(() => { const n = document.querySelector('.react-flow__node[data-id="i-9nlG6HdjK2"]'); if (!n) return; const b = [...n.querySelectorAll('button')].find((x) => { const r = x.getBoundingClientRect(); return Math.abs(r.width - 28) < 2 && r.y < n.getBoundingClientRect().y + 60; }); if (b) b.click(); }); await page.waitForTimeout(900); } },
  { 名: '关掉大编辑器（ESC）', fn: async () => { await page.keyboard.press('Escape'); await page.waitForTimeout(900); } },
  { 名: '开资产面板', fn: async () => { await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); }); await page.waitForTimeout(1500); } },
  { 名: '关资产面板（ESC）', fn: async () => { await page.keyboard.press('Escape'); await page.waitForTimeout(1200); } },
];

async function sweep(标签) {
  const r = [];
  for (const a of 动作) {
    try { await a.fn(); } catch { /* 忽略动作失败 */ }
    const p = await probe();
    r.push({ 动作: a.名, z180累计: p.z180?.累计 ?? null, z180动画数: p.z180动画数, z305累计: p.z305?.累计 ?? null });
    LOG(`  [${标签}] ${a.名.padEnd(22)} z180累计=${String(p.z180?.累计).padEnd(6)} 动画数=${p.z180动画数}  z305累计=${p.z305?.累计}`);
  }
  return r;
}

LOG('══════════ reduce（默认）下逐动作 ══════════');
out.reduce下 = await sweep('reduce');
out.reduce环境 = (await probe()).reduce;

LOG('\n══════════ 覆盖成 no-preference 后，同一套动作 ══════════');
try {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'no-preference' }] });
  await page.waitForTimeout(1500);
} catch (e) { LOG(`⛔ 覆盖失败 ${String(e).slice(0, 80)}`); }
out.noPref环境 = (await probe()).reduce;
LOG(`覆盖后 reduce=${out.noPref环境}`);
out.noPref下 = await sweep('no-pref');

const 有亮 = (arr, k) => arr.filter((x) => (x[k] ?? 0) > 0);
LOG(`\n⭐ z180 累计 opacity > 0 的动作：reduce 下 ${有亮(out.reduce下, 'z180累计').length} 个，no-preference 下 ${有亮(out.noPref下, 'z180累计').length} 个`);
LOG(`⭐ z305 累计 opacity > 0 的动作：reduce 下 ${有亮(out.reduce下, 'z305累计').length} 个，no-preference 下 ${有亮(out.noPref下, 'z305累计').length} 个`);
out.结论 = { z180在noPref下亮过: 有亮(out.noPref下, 'z180累计').length > 0, z305在noPref下亮过: 有亮(out.noPref下, 'z305累计').length > 0 };
LOG(`结论: ${JSON.stringify(out.结论)}`);

await writeFile(new URL('./batchDH2.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDH2.json ===');
await browser.close();
