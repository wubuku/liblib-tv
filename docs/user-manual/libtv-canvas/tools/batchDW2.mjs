// Batch DW-2：深挖顶栏那个 `aria-label="退出跟随"` 的白底按钮。
//
// ⭐⭐⭐ DW-1 的意外收获：广场打开状态下，顶栏 y=9 处有一个
//   `[button] 「取消ESC」 bg=rgb(255,255,255)（纯白） @730,9,64×16 aria=退出跟随`
//
// ⭐ 这极可能就是 **DO 批（§90）测到的 `collab-follow-banner`**：
//   DO 批记的是 `z-[305]` = `collab-follow-banner`，`174×34 @633,0`，
//   `opacity:0` / `aria-hidden=true`，并给出阴性结论
//   「**界面上无协作入口**（19 个 aria-label 按钮枚举 + 阳性对照）」。
//   ⇒ 如果它现在**可见**，DO 那条阴性结论就需要更正。
//
// ⭐ 本轮只回答三个问题：
//   ① 它**长什么样**（尺寸/位置/文案/层级/祖先链）
//   ② 它**常驻还是条件出现**（刷新前后、开关广场前后各读一次）
//   ③ 它和 DO 批记的 `z-[305] / 174×34 @633,0` **是不是同一个**
//
// ⛔ 只读。不点它（那会退出跟随）、不发起任何协作动作。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 三次读数: [], 祖先链: null, 判同: null, 刷新前后: null };
const SAVE = () => writeFileSync(new URL('./batchDW2.json', import.meta.url), JSON.stringify(out, null, 2));

const 读横幅 = () => page.evaluate(() => {
  const b = [...document.querySelectorAll('[aria-label="退出跟随"]')][0];
  if (!b) {
    // 退一步：把含「跟随」或「ESC」文字的可见元素都列出来
    const 候选 = [...document.querySelectorAll('button,div,span')].filter((e) => {
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      if (!t || t.length > 30) return false;
      if (!/跟随|ESC|协作|正在/.test(t)) return false;
      const r = e.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    }).map((e) => { const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return { tag: e.tagName.toLowerCase(), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), 背景: c.backgroundColor, 位置: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], z: c.zIndex, 透明度: c.opacity, ariaHidden: e.getAttribute('aria-hidden') }; });
    return { 找到: false, 候选 };
  }
  const r = b.getBoundingClientRect(); const c = getComputedStyle(b);
  // 祖先链
  const 链 = []; let e = b;
  for (let i = 0; i < 7 && e; i += 1) {
    const q = e.getBoundingClientRect(); const s = getComputedStyle(e);
    链.push({ tag: e.tagName.toLowerCase(), cls: (e.className || '').toString().slice(0, 70), z: s.zIndex, 位置: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)], 透明度: s.opacity, ariaHidden: e.getAttribute('aria-hidden') });
    e = e.parentElement;
  }
  return {
    找到: true, 文字: (b.innerText || '').replace(/\s+/g, ' ').trim(), 背景: c.backgroundColor, 颜色: c.color,
    位置: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    z: c.zIndex, 透明度: c.opacity, ariaHidden: b.getAttribute('aria-hidden'), disabled: b.disabled,
    子节点数: b.children.length,
    内部: [...b.children].map((x) => ({ tag: x.tagName.toLowerCase(), 文字: (x.innerText || '').replace(/\s+/g, ' ').trim() })),
    祖先链: 链,
  };
});

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

// ① 裸画布（广场未开）
const A = await 读横幅();
out.三次读数.push({ 阶段: '① 裸画布', ...A });
LOG(`① 裸画布: ${A.找到 ? `「${A.文字}」${A.位置.join(',')} bg=${A.背景} z=${A.z} opacity=${A.透明度} aria-hidden=${A.ariaHidden}` : `⛔ 没找到。候选: ${JSON.stringify(A.候选)}`}`);
if (A.找到) { out.祖先链 = A.祖先链; LOG('   祖先链:'); for (const n of A.祖先链) LOG(`     [${n.tag}] z=${n.z} @${n.位置.join(',')} op=${n.透明度} hidden=${n.ariaHidden} cls=${n.cls.slice(0, 44)}`); }

// ② 开广场
await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2500);
const B = await 读横幅();
out.三次读数.push({ 阶段: '② 开了广场', 找到: B.找到, 文字: B.文字, 位置: B.位置, 背景: B.背景, z: B.z, 透明度: B.透明度 });
LOG(`② 开了广场: ${B.找到 ? `「${B.文字}」${B.位置.join(',')} bg=${B.背景}` : '⛔ 没找到'}`);

// ③ 刷新后再读（判断是否常驻）
await page.reload({ waitUntil: 'domcontentloaded' });
await page.waitForTimeout(6000);
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(3500);
const C = await 读横幅();
out.三次读数.push({ 阶段: '③ 刷新后', 找到: C.找到, 文字: C.文字, 位置: C.位置, 背景: C.背景, z: C.z, 透明度: C.透明度 });
LOG(`③ 刷新后: ${C.找到 ? `「${C.文字}」${C.位置.join(',')} bg=${C.背景} op=${C.透明度}` : `⛔ 没找到。候选: ${JSON.stringify((C.候选 || []).slice(0, 5))}`}`);

out.刷新前后 = { 刷新前有: B.找到, 刷新后有: C.找到, 结论: B.找到 === C.找到 ? '刷新前后一致' : '刷新前后不一致（可能与加载时序有关）' };
LOG(`\n⭐ 常驻性: ${out.刷新前后.结论}`);

// 判同：和 DO 批记的 z-[305] / 174×34 @633,0 比
const 基 = A.找到 ? A : (B.找到 ? B : C);
if (基 && 基.找到) {
  const 链顶 = 基.祖先链[基.祖先链.length - 1];
  out.判同 = {
    本轮: { 尺寸: [基.位置[2], 基.位置[3]], 位置: [基.位置[0], 基.位置[1]], 祖先顶层cls: 链顶?.cls },
    DO批: { 尺寸: [174, 34], 位置: [633, 0], 类名: 'z-[305] collab-follow-banner' },
    一致: 基.位置[2] === 174 && 基.位置[3] === 34,
  };
  LOG(`\n══════ ⭐ 与 DO 批判同 ══════`);
  LOG(`本轮: ${基.位置.join(',')}（${基.位置[2]}×${基.位置[3]}）祖先顶层 cls=${链顶?.cls}`);
  LOG(`DO批: 633,0（174×34）z-[305] collab-follow-banner`);
  LOG(`一致: ${out.判同.一致 ? '✅ 是同一个' : '⛔ 尺寸/位置对不上 ⇒ 可能是两样东西'}`);
  await shot(page, 'DW-a-退出跟随按钮.png');
  LOG('📸 DW-a');
}
out.最终节点数 = await page.evaluate(() => document.querySelectorAll('[data-id]').length);
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDW2.json ===');
