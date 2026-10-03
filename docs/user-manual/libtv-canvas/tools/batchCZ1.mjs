// Batch CZ-1：补两处 —— CZ-0 的两个读数都需要再确认一步。
//
// A 的问题：视频节点 3「尝试」栏**只有 3 项，没有「取消选择」**，
//   而且祖先链 6 层全是 `overflow: visible`、`scrollHeight == clientHeight`
//   ⇒ **根本没有裁切**。旧读数「DOM 里有、画面被卡片高度裁掉」不成立。
//   ⭐ 但我量的是**未选中**状态 —— 选中时卡片会展开，
//   「取消选择」**可能**在选中态才出现。⇒ 必须补测选中态，
//   否则只能说「未选中时没有」，不能说「没有」。
//
// B 的问题：广场点 `minimize` 之后 z701/z700 都消失了，但我**没找到那个小窗**
//   （我的 `layers()` 只找 `z >= 200`）。不过确实找到了两枚按钮
//   `aria="maximize"` 和 `aria="close"` ⇒ 广场**真的被最小化了**。
//   ⇒ 本步：把那个小窗找出来（不限 z）、量尺寸、截图，
//   ⭐ 再点 `maximize` 验证**能不能还原**（这一条比「能最小化」更重要 ——
//   如果还原不回来，那这个功能对用户就是坑）。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const VID = 'v-v2hlWY4Br3';
const LOG = console.log;
const out = {};

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

// =============== A 补测：选中视频节点 3 之后的「尝试」栏 ===============
LOG('══════════ A 补测：选中态的「尝试」栏 ══════════');
await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  n.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: n.getBoundingClientRect().x + 40, clientY: n.getBoundingClientRect().y + 20 }));
}, VID);
await page.waitForTimeout(1800);
out.A选中 = await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  const nr = n.getBoundingClientRect();
  let 栏 = null;
  for (const e of n.querySelectorAll('*')) {
    if (e.children.length) continue;
    if ((e.innerText || '').replace(/\s+/g, '').includes('尝试')) { 栏 = e.parentElement; break; }
  }
  if (!栏) return { 节点rect: [Math.round(nr.x), Math.round(nr.y), Math.round(nr.width), Math.round(nr.height)], 有尝试栏: false, 选中: n.classList.contains('selected') };
  const cr = 栏.getBoundingClientRect();
  const items = [...栏.querySelectorAll('*')].filter((e) => e.children.length === 0 && (e.innerText || '').trim())
    .map((e) => { const r = e.getBoundingClientRect(); return { 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; });
  return {
    选中: n.classList.contains('selected'),
    节点rect: [Math.round(nr.x), Math.round(nr.y), Math.round(nr.width), Math.round(nr.height)],
    节点overflow: getComputedStyle(n).overflow,
    栏rect: [Math.round(cr.x), Math.round(cr.y), Math.round(cr.width), Math.round(cr.height)],
    栏scrollH: 栏.scrollHeight, 栏clientH: 栏.clientHeight,
    项: items,
  };
}, VID);
LOG(`选中=${out.A选中.选中} 节点=${JSON.stringify(out.A选中.节点rect)} 栏=${JSON.stringify(out.A选中.栏rect)} scrollH=${out.A选中.栏scrollH} clientH=${out.A选中.栏clientH}`);
for (const it of out.A选中.项 ?? []) {
  const 底 = it.rect[1] + it.rect[3];
  const 下沿 = out.A选中.节点rect[1] + out.A选中.节点rect[3];
  LOG(`   "${it.文字}" @${JSON.stringify(it.rect)}  ${it.rect[3] === 0 ? '⛔零高' : (底 > 下沿 ? `⚠️超出节点 ${底 - 下沿}px` : '✅在节点内')} ${it.rect[1] >= 810 ? '⛔视口外' : ''}`);
}
LOG(`⭐ 选中态下有没有「取消选择」: ${(out.A选中.项 ?? []).some((x) => x.文字.includes('取消')) ? '有' : '没有'}`);
await shot(page, 'CZ-a-视频节点3选中后的尝试栏.png', { clip: { x: out.A选中.节点rect[0] - 10, y: out.A选中.节点rect[1] - 10, width: out.A选中.节点rect[2] + 20, height: Math.min(240, out.A选中.节点rect[3] + 30) } });

// =============== B 补测：广场小窗在哪 + 能不能还原 ===============
LOG('\n══════════ B 补测：广场 minimize 之后的小窗 ══════════');
await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); b.click(); });
await page.waitForTimeout(1800);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(2800);

const mini = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button[aria-label="minimize"]')].find((x) => { const r = x.getBoundingClientRect(); return r.width > 0; });
  if (!b) return null;
  const r = b.getBoundingClientRect();
  b.click();
  return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
});
LOG(`点 minimize: ${JSON.stringify(mini)}`);
await page.waitForTimeout(2000);

// ⭐ 找那个小窗：不限 z，只要 rect 变小了、且带 maximize 按钮
out.B = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  const maxBtn = [...document.querySelectorAll('button[aria-label="maximize"]')].find(vis);
  if (!maxBtn) return { 找到maximize: false };
  const r = maxBtn.getBoundingClientRect();
  // 往上找一个包含它、且有面积的容器
  const cands = [];
  for (let e = maxBtn.parentElement, i = 0; e && i < 8; e = e.parentElement, i += 1) {
    const b = e.getBoundingClientRect();
    cands.push({ tag: e.tagName.toLowerCase(), class: (e.className || '').toString().slice(0, 60), rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)], pos: getComputedStyle(e).position, z: getComputedStyle(e).zIndex });
  }
  return {
    找到maximize: true,
    maximize: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    容器链: cands,
    视口内可见文字: [...document.querySelectorAll('body *')].filter((e) => e.children.length === 0 && vis(e) && e.getBoundingClientRect().x > 900 && e.getBoundingClientRect().y < 400)
      .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter((t) => t && t.length < 30).slice(0, 12),
  };
});
LOG(`找到 maximize: ${out.B.找到maximize} 位置=${JSON.stringify(out.B.maximize)}`);
if (out.B.找到maximize) {
  LOG(`向上容器链:`);
  for (const c of out.B.容器链) LOG(`   <${c.tag}> ${JSON.stringify(c.rect)} pos=${c.pos} z=${c.z} ${c.class}`);
  LOG(`右下角可见文字: ${JSON.stringify(out.B.视口内可见文字)}`);
  await shot(page, 'CZ-b-广场最小化之后的小窗.png');
  LOG('📸 CZ-b');
  out.BminShot = true;

  // ⭐ 点 maximize 看能不能还原
  const before = await page.evaluate(() => [...document.querySelectorAll('button[aria-label="maximize"],button[aria-label="minimize"]')].map((b) => b.getAttribute('aria-label')));
  await page.mouse.click(out.B.maximize[0] + out.B.maximize[2] / 2, out.B.maximize[1] + out.B.maximize[3] / 2);
  await page.waitForTimeout(2000);
  out.B还原 = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
    const mall = [...document.querySelectorAll('*')].filter((e) => {
      const s = getComputedStyle(e); const r = e.getBoundingClientRect();
      const z = parseInt(s.zIndex, 10);
      return !Number.isNaN(z) && z >= 200 && r.width > 500;
    }).map((e) => { const r = e.getBoundingClientRect(); return { z: getComputedStyle(e).zIndex, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; });
    return { 大层: mall, 还有minimize吗: [...document.querySelectorAll('button[aria-label="minimize"]')].some(vis), 还有maximize吗: [...document.querySelectorAll('button[aria-label="maximize"]')].some(vis) };
  });
  LOG(`\n⭐ 点 maximize 之前那排按钮: ${JSON.stringify(before)}`);
  LOG(`⭐ 点 maximize 之后: ${JSON.stringify(out.B还原)}`);
}

await writeFile(new URL('./batchCZ1.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n已写 tools/batchCZ1.json');
await browser.close();
