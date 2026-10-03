// Batch CZ-0：两个纯几何 / 纯读取的实验，都不点任何会写盘的东西。
//
// 实验 A：视频节点 3「尝试」栏末尾那个 `取消选择`
//   —— 遗留 📖：「DOM 里有、画面上被卡片高度裁掉，没有二次确认」。
//   本步**只量几何**：容器多高、overflow 是什么、每一项的 y 到哪、
//   容器下沿在哪、`取消选择` 的 y 相对下沿的位置。
//   ⭐ 如果它被裁掉，那**用户就永远点不到它** —— 值得写进手册。
//   ⛔ 不点它（点了会改变节点状态）。
//
// 实验 B：广场那一层自己的 `minimize`（`40×40`，`aria-label="minimize"`）
//   —— CW 遗留：「与详情浮层那枚同名不同尺寸，点下去会怎样」。
//   本步点它 —— 纯 UI 操作（关掉或折叠一层），不写盘、不扣积分。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const VID = 'v-v2hlWY4Br3';   // 视频节点 3（带 3 项「尝试」的那个）
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

// ================= 实验 A：取消选择的裁切机制（纯几何） =================
LOG('══════════ 实验 A：视频节点 3「尝试」栏的几何 ══════════');
out.A = await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { 在: false };
  const nr = n.getBoundingClientRect();
  // 找「尝试」栏的容器
  let 栏 = null;
  for (const e of n.querySelectorAll('*')) {
    if (e.children.length) continue;
    if ((e.innerText || '').replace(/\s+/g, '').includes('尝试')) { 栏 = e.parentElement; break; }
  }
  if (!栏) return { 在: true, 有尝试栏: false, 节点rect: [Math.round(nr.x), Math.round(nr.y), Math.round(nr.width), Math.round(nr.height)] };
  // 往上找到真正限制高度的那一层
  const chain = [];
  for (let e = 栏, i = 0; e && i < 6; e = e.parentElement, i += 1) {
    const r = e.getBoundingClientRect();
    const s = getComputedStyle(e);
    chain.push({
      tag: e.tagName.toLowerCase(),
      class: (e.className || '').toString().slice(0, 70),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      overflow: s.overflow, overflowY: s.overflowY,
      scrollHeight: e.scrollHeight, clientHeight: e.clientHeight,
      高度不够: e.scrollHeight > e.clientHeight + 1,
    });
    if (e === n) break;
  }
  // 「尝试」栏里每一项（含被裁掉的）
  const items = [...栏.querySelectorAll('*')].filter((e) => e.children.length === 0 && (e.innerText || '').trim()).map((e) => {
    const r = e.getBoundingClientRect();
    const s = getComputedStyle(e);
    return { 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], opacity: s.opacity, visibility: s.visibility, tag: e.tagName.toLowerCase() };
  });
  return { 在: true, 有尝试栏: true, 节点rect: [Math.round(nr.x), Math.round(nr.y), Math.round(nr.width), Math.round(nr.height)], 节点overflow: getComputedStyle(n).overflow, 祖先链: chain, 项: items };
}, VID);

if (out.A.有尝试栏) {
  const n0 = out.A.节点rect;
  LOG(`节点 rect=${JSON.stringify(n0)}  overflow=${out.A.节点overflow}`);
  LOG(`祖先链（找哪一层在限高）：`);
  for (const c of out.A.祖先链) {
    LOG(`   <${c.tag}> rect=${JSON.stringify(c.rect)} overflow=${c.overflow}/${c.overflowY} scrollH=${c.scrollHeight} clientH=${c.clientHeight} ${c.高度不够 ? '⭐ 内容比容器高' : ''}`);
  }
  const 栏下沿 = out.A.祖先链[0].rect[1] + out.A.祖先链[0].rect[3];
  const 节点下沿 = n0[1] + n0[3];
  LOG(`\n「尝试」栏下沿 y=${栏下沿}，节点下沿 y=${节点下沿}，视口下沿 y=810`);
  LOG(`项（共 ${out.A.项.length} 个）：`);
  for (const it of out.A.项) {
    const 底 = it.rect[1] + it.rect[3];
    const 状态 = it.rect[3] === 0 ? '⛔ 零高度' : (it.rect[1] >= 节点下沿 ? `⛔ 完全在节点外（超出 ${it.rect[1] - 节点下沿}px）` : (底 > 节点下沿 ? `⚠️ 底部超出节点 ${底 - 节点下沿}px` : '✅ 在节点内'));
    LOG(`   "${it.文字}" @${JSON.stringify(it.rect)} op=${it.opacity} vis=${it.visibility}  ${状态}`);
  }
  const 视口外 = out.A.项.filter((x) => x.rect[1] + x.rect[3] > 810 || x.rect[1] < 0);
  LOG(`\n⭐ 落在视口(0-810)之外的项：${视口外.length} 个 → ${JSON.stringify(视口外.map((x) => x.文字))}`);
} else {
  LOG(`⛔ 没读到「尝试」栏: ${JSON.stringify(out.A)}`);
}

// ================= 实验 B：广场那层的 minimize =================
LOG('\n══════════ 实验 B：广场那层自己的 minimize（40×40）══════════');
await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); b.click(); });
await page.waitForTimeout(1800);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(2800);

const layers = (page) => page.evaluate(() => {
  const c = [];
  const walk = (e) => {
    const s = getComputedStyle(e); const r = e.getBoundingClientRect();
    const z = parseInt(s.zIndex, 10);
    if (!Number.isNaN(z) && z >= 200 && r.width > 20 && r.height > 20) c.push({ z, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 46) });
    for (const k of e.children) walk(k);
  };
  walk(document.body);
  return c.sort((a, b) => b.z - a.z);
});
out.B = { 步骤: [] };
const markB = async (label) => {
  const l = await layers(page);
  out.B.步骤.push({ label, l });
  LOG(`▸ ${label}: ${JSON.stringify(l.map((x) => `z${x.z}${JSON.stringify(x.rect)}`))}`);
  LOG(`   文字: ${JSON.stringify(l.map((x) => x.text))}`);
};
await markB('① 广场开着，未点');

const minInfo = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button[aria-label="minimize"]')].find((x) => { const r = x.getBoundingClientRect(); return r.width > 0; });
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
});
LOG(`广场 minimize: ${JSON.stringify(minInfo)}`);
if (minInfo) {
  await page.mouse.click(minInfo.rect[0] + minInfo.rect[2] / 2, minInfo.rect[1] + minInfo.rect[3] / 2);
  await page.waitForTimeout(1800);
  await markB('② 点广场的 minimize 之后');
  // ⭐ 有没有还原入口
  const restore = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
    return [...document.querySelectorAll('button,[role="button"]')].filter(vis)
      .map((b) => ({ aria: b.getAttribute('aria-label'), text: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12) }))
      .filter((x) => /还原|展开|恢复|maximize|放大|minimize|close/i.test(`${x.aria || ''}${x.text || ''}`));
  });
  out.B.还原候选 = restore;
  LOG(`⭐ 找还原/放大/关闭类按钮: ${JSON.stringify(restore)}`);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1200);
  await markB('③ 再按 ESC');
}

await writeFile(new URL('./batchCZ0.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n已写 tools/batchCZ0.json');
await browser.close();
