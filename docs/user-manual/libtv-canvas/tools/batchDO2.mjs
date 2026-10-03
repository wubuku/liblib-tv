// Batch DO-2：实测 collab（协作）这套元素在页面里的真实状态。
//
// DO-1 从 JS chunk 里已经查清：
//   `z-[180]` = `data-testid="collab-follow-border"`  ⇒ **跟随边框**
//   `z-[305]` = `data-testid="collab-follow-banner"`   ⇒ **顶部跟随横幅**
// 两者都是 `pointer-events-none fixed` + `style.opacity = +!!active`
// ⇒ **元素常驻、用 opacity 控制显隐**，与 DG 批次「从基线起就一直都在」完全吻合。
//
// ⭐ 本步只做**只读确认**，不点任何东西：
//   ① 这些 testid 在不在 DOM 里、不在的话是不是懒渲染
//   ② 在的话，尺寸 / class / opacity / 内含文案
//   ③ 找「协作」这个功能在**界面上**有没有入口（chunk 里它挂在团队版席位管理下）
//   ④ 团队版相关的界面文案
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { testid探测: [], 协作入口: null, 团队版文案: [], 全文扫描: null };
const SAVE = () => writeFile(new URL('./batchDO2.json', import.meta.url), JSON.stringify(out, null, 2));

const { browser, page } = await launch();
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

// ---------- ① 逐个 testid 探测 ----------
const 目标 = [
  'collab-follow-border', 'collab-follow-banner', 'collab-follow-member', 'collab-follow-aria',
  'collab-presence-bar', 'collab-presence-bar-header', 'collab-follow-controller',
];
LOG('=== ① collab 相关 data-testid 探测 ===');
for (const id of 目标) {
  const r = await page.evaluate((i) => {
    const e = document.querySelector(`[data-testid="${i}"]`);
    if (!e) return { 存在: false };
    const b = e.getBoundingClientRect(); const c = getComputedStyle(e);
    return {
      存在: true,
      尺寸: [Math.round(b.width), Math.round(b.height)],
      position: c.position, zIndex: c.zIndex, opacity: c.opacity,
      pointerEvents: c.pointerEvents, visibility: c.visibility, display: c.display,
      ariaHidden: e.getAttribute('aria-hidden'), ariaLabel: e.getAttribute('aria-label'),
      有inert: e.hasAttribute('inert'),
      class名: (e.className || '').slice(0, 180),
      文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80),
    };
  }, id);
  out.testid探测.push({ testid: id, ...r });
  LOG(`  ${r.存在 ? '✅' : '⛔'} ${id}${r.存在 ? ` | ${r.尺寸.join('×')} ${r.position} z=${r.zIndex} opacity=${r.opacity} pe=${r.pointerEvents} vis=${r.visibility} aria-hidden=${r.ariaHidden}${r.有inert ? ' inert' : ''} | 文案「${r.文字}」` : ' | DOM 里没有'}`);
  SAVE();
}

// ---------- ② ⭐ 找 z-[180] / z-[305] 的持有者（不管有没有 testid） ----------
const 按Z = await page.evaluate(() => {
  const 找 = (z) => {
    const 出 = [];
    for (const e of document.querySelectorAll('*')) {
      const c = getComputedStyle(e);
      if (c.zIndex === z && e.children.length < 30) {
        const b = e.getBoundingClientRect();
        出.push({
          tag: e.tagName.toLowerCase(), testid: e.getAttribute('data-testid'),
          cls: (e.className || '').toString().slice(0, 120),
          z: c.zIndex, opacity: c.opacity, position: c.position,
          尺寸: [Math.round(b.width), Math.round(b.height)],
        });
      }
    }
    return 出;
  };
  return { z180: 找('180'), z305: 找('305') };
});
LOG(`\n=== ② 按 computed z-index 反查 ===`);
LOG(`  z-index=180 的元素: ${按Z.z180.length} 个`);
for (const e of 按Z.z180.slice(0, 5)) LOG(`     <${e.tag}> testid=${e.testid} ${e.尺寸.join('×')} opacity=${e.opacity} ${e.position} cls=${e.cls.slice(0, 70)}`);
LOG(`  z-index=305 的元素: ${按Z.z305.length} 个`);
for (const e of 按Z.z305.slice(0, 5)) LOG(`     <${e.tag}> testid=${e.testid} ${e.尺寸.join('×')} opacity=${e.opacity} ${e.position} cls=${e.cls.slice(0, 70)}`);
out.按Z = 按Z; SAVE();

// ---------- ③ 界面上有没有「协作」入口 ----------
LOG('\n=== ③ 界面上「协作」相关文字/控件 ===');
const 入口 = await page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  const 命中 = [];
  for (const e of document.querySelectorAll('button,a,[role="button"],[aria-label],div,span')) {
    const t = ((e.innerText || '') + ' ' + (e.getAttribute('aria-label') || '')).trim();
    if (!t || t.length > 40) continue;
    if (!/协作|跟随|邀请协作|协同/.test(t)) continue;
    if (!vis(e)) continue;
    const b = e.getBoundingClientRect();
    命中.push({ 文本: t.slice(0, 30), tag: e.tagName.toLowerCase(), 尺寸: [Math.round(b.width), Math.round(b.height)], 位置: [Math.round(b.x), Math.round(b.y)] });
  }
  // 去重（父子都命中）
  const 见过 = new Set(); const 出 = [];
  for (const h of 命中) { const k = `${h.文本}@${h.位置}`; if (!见过.has(k)) { 见过.add(k); 出.push(h); } }
  return 出.slice(0, 15);
});
LOG(`  可见的「协作/跟随」相关元素: ${入口.length} 个`);
for (const h of 入口) LOG(`     "${h.文本}" <${h.tag}> ${h.尺寸.join('×')} @${h.位置.join(',')}`);
out.协作入口 = 入口; SAVE();

// ---------- ④ 全页扫「实时同步 / 团队 / 席位」等团队版文案 ----------
LOG('\n=== ④ 团队版 / 实时同步 相关可见文案 ===');
const 文案 = await page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  const 出 = new Set();
  for (const e of document.querySelectorAll('*')) {
    if (e.children.length) continue;
    const t = (e.textContent || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 60) continue;
    if (/实时同步|团队|席位|升级团队/.test(t) && vis(e)) 出.add(t);
  }
  return [...出].slice(0, 12);
});
LOG(`  命中 ${文案.length} 条: ${JSON.stringify(文案, null, 0)}`);
out.团队版文案 = 文案; SAVE();

// ---------- ⑤ 打开协作状态条看有没有 ----------
// 顶部右侧那排图标里可能有协作入口，先把当前视口里所有图标按钮的 aria-label 列出来
const 图标 = await page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  return [...document.querySelectorAll('button[aria-label]')].filter(vis).map((b) => ({
    label: b.getAttribute('aria-label'), 尺寸: [Math.round(b.getBoundingClientRect().width), Math.round(b.getBoundingClientRect().height)],
  }));
});
LOG(`\n=== ⑤ 视口内带 aria-label 的按钮 ${图标.length} 个 ===`);
LOG('  ' + JSON.stringify(图标));
out.视口内aria按钮 = 图标; SAVE();

await shot(page, 'DO-a-画布全貌-找协作入口.png');
LOG('📸 DO-a');
await browser.close();
LOG('\n=== 已写 tools/batchDO2.json ===');
