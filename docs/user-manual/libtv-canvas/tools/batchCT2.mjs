// Batch CT-2：坐实 CT-1 的两个定名，并做点击归属的隔离实验。
//
// CT-1 结果（改写 CR 的两条读数）：
//   `[959,664]` hover 气泡逐字 = **`翻译提示词`**
//       ⇒ CR/CO 记的「一根斜杆」是**看漏了** —— viewBox `0 0 19.71 18` 有
//         **两段 path**：第 1 段是那根斜杆，第 2 段 `M7.7 0 …H14…` 画的是
//         **一个大写 A**。合起来是「A + 斜杠」= 翻译的经典图形。
//       ⇒ `data-practice-generator-lock` 这个属性名**是误导**：它不是「锁定」，
//         是产品打在「生成器这一行」上的通用标记。
//
//   `[744,664]` hover 气泡逐字 = `Panavision DXL2 已关闭 Arri Signature Prime / 35mm / ƒ/4`
//       ⇒ CR/CO 记的「彩色球是 CSS 背景画的」**也是错的**：它里面是**两枚 `<img>`**
//         （亮/暗两套），产品自己贴了 `data-camera-control-icon="light"` / `"dark"`。
//
// 本步：
//   ① 点开 `[744,664]` 的面板全文（相机参数）—— CR 说 17 条，逐字读出来
//   ② 点开 `[999,664]` 的面板全文（滑块/高级设置）—— ⭐ 验「它俩是不是同一件事」
//   ③ ⭐ **点击归属隔离实验**：CO 记「描述为空时点 `[959,664]` ⇒ 弹
//      `提示词为空，请输入内容后点击`」。现在知道它是「翻译提示词」，这个
//      toast 就完全合理（它要读提示词才能翻）。但**一���轮里出现的 toast
//      不能直接归因给刚点的那枚按钮**（§146 教训）。所以：
//        - 阴性对照：描述为空时点 `[744,664]`（同排、无文字、同样有 cursor-pointer）
//          ⇒ 弹不弹同样的 toast？
//        - 阳性对照：描述为空时点真正的提交键 `[1079,664]`（`gen.submit`）
//          ⇒ 弹的 toast 是不是同一句？
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const IMG = 'i-9nlG6HdjK2';

const boot = async (page) => {
  await open(page, URL_);
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2600);
  for (let i = 0; i < 3; i += 1) {
    const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
    if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(600);
  }
  const p = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
    if (!b) return null; const r = b.getBoundingClientRect();
    return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
  });
  if (p) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1200); }
};

const { browser, page } = await launch();
await boot(page);
await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  n.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: n.getBoundingClientRect().x + 40, clientY: n.getBoundingClientRect().y + 20 }));
}, IMG);
await page.waitForTimeout(900);
const fp = await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  const f = [...n.querySelectorAll('button')].find((b) => {
    const c = (b.className || '').toString();
    return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2');
  });
  const r = f.getBoundingClientRect();
  for (let dx = 4; dx < r.width; dx += 3) for (let dy = 4; dy < r.height; dy += 3) {
    const el = document.elementFromPoint(r.x + dx, r.y + dy);
    if (el && (el === f || f.contains(el) || el.contains(f))) return [Math.round(r.x + dx), Math.round(r.y + dy)];
  }
  return null;
}, IMG);
await page.mouse.click(fp[0], fp[1]);
await page.waitForTimeout(1400);

const LOG = console.log;
const out = {};

// 大编辑器可见文字叶子（用于读面板全文；根从 body 起，§131 的教训）
const leaves = (page) => page.evaluate(() => {
  const res = [];
  for (const e of document.querySelectorAll('body *')) {
    if (e.children.length) continue;
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) continue;
    const r = e.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const t = (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 40) continue;
    res.push({ t, x: Math.round(r.x), y: Math.round(r.y) });
  }
  return res;
});
const modalFull = (page) => page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  return d ? (d.innerText || '').replace(/\s+/g, ' ').trim() : null;
});
const toasts = (page) => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  return [...document.querySelectorAll('body *')]
    .filter((e) => e.children.length === 0 && vis(e))
    .map((e) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim(), r: (() => { const b = e.getBoundingClientRect(); return [Math.round(b.x), Math.round(b.y)]; })(), cls: (e.className || '').toString().slice(0, 60) }))
    .filter((x) => /提示词|为空|请输入|关闭|失败|成功/.test(x.t));
});

// ---- 基线：确认描述为空 -------------------------------------------------------
out.描述 = await page.evaluate(() => {
  const ta = document.querySelector('[data-practice-anchor="gen.prompt"] textarea,[data-practice-anchor="gen.prompt"] [contenteditable="true"]');
  return ta ? { 值: ta.value ?? ta.textContent ?? '', placeholder: ta.getAttribute('placeholder') } : 'no-editor';
});
LOG(`描述框状态: ${JSON.stringify(out.描述)}`);
out.toast基线 = await toasts(page);
LOG(`基线 toast: ${JSON.stringify(out.toast基线)}`);

// ---- ① 点开彩色球 [744,664] ---------------------------------------------------
const before1 = await leaves(page);
await page.mouse.click(744 + 16, 664 + 16);
await page.waitForTimeout(1200);
out.球面板 = await modalFull(page);
const after1 = await leaves(page);
out.球新增 = after1.filter((x) => !before1.some((y) => y.t === x.t && y.x === x.x && y.y === x.y));
LOG(`\n===== ① 点开彩色球 [744,664] =====`);
LOG(`新增文字叶子 ${out.球新增.length} 个:`);
for (const x of out.球新增) LOG(`   "${x.t}"  @${x.x},${x.y}`);

// 关掉
await page.keyboard.press('Escape');
await page.waitForTimeout(600);
await page.mouse.click(20, 20).catch(() => {});
await page.waitForTimeout(600);
await page.keyboard.press('Escape');
await page.waitForTimeout(600);

// ---- ② 点开滑块 [999,664] ----------------------------------------------------
const before2 = await leaves(page);
await page.mouse.click(999 + 16, 664 + 16);
await page.waitForTimeout(1200);
const after2 = await leaves(page);
out.滑块新增 = after2.filter((x) => !before2.some((y) => y.t === x.t && y.x === x.x && y.y === x.y));
LOG(`\n===== ② 点开滑块 [999,664] =====`);
LOG(`新增文字叶子 ${out.滑块新增.length} 个:`);
for (const x of out.滑块新增) LOG(`   "${x.t}"  @${x.x},${x.y}`);

// ⭐ 两边是不是同一件事？逐字比新增集合
out.两面板相同 = JSON.stringify(out.球新增.map((x) => x.t).sort()) === JSON.stringify(out.滑块新增.map((x) => x.t).sort());
LOG(`\n⭐ 两个面板的新增文字集合是否完全相同: ${out.两面板相同}`);

await page.keyboard.press('Escape');
await page.waitForTimeout(600);
await page.mouse.click(20, 20).catch(() => {});
await page.waitForTimeout(800);

// ---- ③ 隔离实验：toast 归属 ---------------------------------------------------
const probe = async (label, x) => {
  // 先清干净
  await page.waitForTimeout(400);
  const base = await toasts(page);
  await page.mouse.click(x + 16, 664 + 16);
  const series = [];
  for (let i = 0; i < 6; i += 1) {
    await page.waitForTimeout(300);
    series.push(await toasts(page));
  }
  const seen = [...new Set(series.flat().map((t) => t.t))].filter((t) => !base.some((b) => b.t === t));
  LOG(`\n--- ${label} @${x} ---`);
  LOG(`    基线 toast: ${JSON.stringify(base.map((b) => b.t))}`);
  LOG(`    6 次采样（每 300ms）新出现的 toast: ${JSON.stringify(seen)}`);
  return { 基线: base.map((b) => b.t), 新出现: seen, 时间线: series.map((s) => s.map((t) => t.t)) };
};
out.翻译959 = await probe('翻译提示词 [959,664]', 959);
await page.waitForTimeout(2500);
out.球744 = await probe('阴性对照 彩色球 [744,664]', 744);
await page.waitForTimeout(2500);
out.提交1079 = await probe('阳性对照 提交键 [1079,664]', 1079);

await writeFile(new URL('./batchCT2.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n已写 tools/batchCT2.json');
await browser.close();
