// Batch CG-9：`⤢` 的收官实验 —— **一次只动一个变量**，每一步读数与截图**成对**。
//
// 前面几轮互相打架的根因（必须一次理清）：
//   · CG-5 读数「折叠」+ 截图「展开」；
//   · CG-6 读数「折叠」+ 截图「展开」；
//   · CG-8 读数「折叠」（且持续 4 秒不恢复）+ 截图「展开」。
//   · 而且 M-311 顶部还浮着「从画布或资产管理选择参考」—— **上一轮点「参考」留下的残留**，
//     说明**取证环境被污染了**，画面和读数根本不是同一个世界。
//
// 本步的设计：
//   ① 开头**强制刷新**，并在拍图前先拍一张「点之前」，肉眼先确认环境是干净的；
//   ② **只点 `⤢` 这一个东西**，别的一律不碰；
//   ③ 每一步都「读 → 拍 → **立刻再读**」，
//      用「拍完再读」直接回答：**到底是状态自己变了，还是拍图这一步把它弄变的**；
//   ④ 折叠后连采 12 次 × 2 秒（24 秒），回答「它会不会自己弹回来」。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const EXPAND = 'M1.4 8.9c.22 0 .4.18.4.4v5.54l5.26-5.26a.4.4 0 0 1 .57 0l.7.71';
const VID = 'v-eMpqKtiLlx';

const { browser, page } = await launch();
const out = { steps: [] };

// ① 强制刷新，先把上一轮残留的「参考选择」提示条冲掉
await open(page, URL_);
await closePromos(page);
await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.reload({ waitUntil: 'domcontentloaded' });
await page.waitForTimeout(5000);
await closePromos(page);
await page.waitForTimeout(1200);

// 环境自检：页面上**不该**有任何「参考选择」提示条
out.环境自检 = await page.evaluate(() => ({
  残留提示条: document.body.innerText.includes('从画布或资产管理选择参考'),
  浮层提示数: document.querySelectorAll('[role="tooltip"],[class*="Tooltip"]').length,
  对话框数: document.querySelectorAll('[role="dialog"]').length,
}));
console.log('环境自检 =', JSON.stringify(out.环境自检));

const truth = (nid) => page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { err: 'node not in DOM' };
  const fus = [...node.querySelectorAll('.node-floating-ui')].map((el) => {
    const r = el.getBoundingClientRect();
    return { 尺寸: `${Math.round(r.width)}x${Math.round(r.height)}`, 面积: Math.round(r.width * r.height), cls: (el.className || '').toString().slice(0, 30) };
  }).filter((x) => x.面积 > 0).sort((a, b) => b.面积 - a.面积);
  const prompt = node.querySelector('.text-fg-default[contenteditable="true"]');
  return {
    浮层清单: fus.map((f) => `${f.尺寸}(${f.cls})`),
    最大浮层: fus[0] ? fus[0].尺寸 : '无',
    提示词框在不在: !!prompt,
    文字长度: (node.innerText || '').replace(/\s+/g, ' ').trim().length,
    selected: node.className.includes('selected'),
  };
}, nid);

const locate = (nid, pre) => page.evaluate(({ n, p }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { found: false };
  for (const b of node.querySelectorAll('button,[role="button"]')) {
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (!d.includes(p)) continue;
    const r = b.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    return { found: true, cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
  }
  return { found: false };
}, { n: nid, p: pre });

// 聚焦到视频节点的 clip。
// ⚠️ 不能用 `.node-shell` 定位：它在 **660 宽浮层的另一条分支上**，
//    `node.querySelector('.node-shell')` 实测返回 null（CG-9 第一版就栽在这）。
//    改成取「节点本体矩形 ∪ 最大的那块浮层矩形」。
const clipOf = (nid) => page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return null;
  const fus = [...node.querySelectorAll('.node-floating-ui')].map((el) => el.getBoundingClientRect())
    .filter((r) => r.width > 0 && r.height > 0)
    .sort((a, b) => b.width * b.height - a.width * a.height);
  const boxes = [node.getBoundingClientRect(), ...fus];
  const x0 = Math.min(...boxes.map((r) => r.x));
  const y0 = Math.min(...boxes.map((r) => r.y));
  const x1 = Math.max(...boxes.map((r) => r.right));
  const y1 = Math.max(...boxes.map((r) => r.bottom));
  const x = Math.max(0, Math.round(x0 - 24));
  const y = Math.max(0, Math.round(y0 - 24));
  return { x, y, width: Math.min(1440 - x, Math.round(x1 - x0 + 48)), height: Math.min(810 - y, Math.round(y1 - y0 + 48)) };
}, nid);

// ⭐ 读 → 拍 → 立刻再读：用「拍完再读」直接分辨「自己变的」还是「拍图弄变的」
// ⚠️ `clipOf` 返回的是 **Promise**（`page.evaluate` 是异步的）—— 必须 `await`。
//    漏了 await 就会把一个 Promise 对象当 clip 传给 Playwright，报 `clip.x: expected float, got undefined`。
// ⭐⭐ 两张配图**必须用同一个 clip**：折叠后卡片缩到 292×23，
//    若按折叠后的矩形算 clip，裁出来的会是一片全黑（CG-9 第一版就是这么拍废的）。
//    固定用**展开态**的区域，两张图才能逐像素对比「整张卡片消失了」。
let FIXED_CLIP = null;
async function step(tag, file) {
  const before = await truth(VID);
  if (file) {
    const clip = FIXED_CLIP || (await clipOf(VID));
    if (!FIXED_CLIP) FIXED_CLIP = clip;
    await shot(page, file, clip ? { clip } : {});
  }
  const after = await truth(VID);
  const rec = {
    tag, 拍图前: before, 拍图后: after,
    拍图是否改变状态: before.最大浮层 !== after.最大浮层 || before.提示词框在不在 !== after.提示词框在不在,
  };
  out.steps.push(rec);
  console.log(`  ${tag}: 拍图前 ${before.最大浮层}/${before.文字长度}字 → 拍图后 ${after.最大浮层}/${after.文字长度}字 | 拍图改变了状态=${rec.拍图是否改变状态}`);
  return rec;
}

const findBlank = () => page.evaluate(() => {
  for (const [x, y] of [[720, 100], [1300, 180], [720, 700], [200, 380], [1240, 640], [80, 200], [1360, 400]]) {
    const el = document.elementFromPoint(x, y);
    if (el && !el.closest('.react-flow__node') && !el.closest('button,[role="button"]') && !el.closest('input,[contenteditable="true"]')) return { x, y };
  }
  return null;
});

// 选中视频节点（点空白解除 → ⌘0 → 命中校验 → 真点）
let blank = await findBlank();
await page.mouse.click(blank.x, blank.y);
await page.waitForTimeout(800);
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2400);
const c = await page.evaluate((n) => {
  const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!el) return null;
  const b = el.getBoundingClientRect();
  return { cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + b.height / 2) };
}, VID);
const hitChk = await page.evaluate(({ x, y, n }) => {
  const el = document.elementFromPoint(x, y);
  const node = el ? el.closest('.react-flow__node') : null;
  return node ? node.getAttribute('data-id') : null;
}, { x: c.cx, y: c.cy, n: VID });
out.命中校验 = { 点: [c.cx, c.cy], 命中: hitChk, 目标: VID };
if (hitChk !== VID) { console.log('!! 点不中目标节点，作废'); await browser.close(); process.exit(1); }
await page.mouse.move(c.cx, c.cy);
await page.waitForTimeout(400);
await page.mouse.click(c.cx, c.cy);
await page.waitForTimeout(2000);
out.选中后 = await truth(VID);
console.log('选中后 =', JSON.stringify(out.选中后));

// ② 基线：展开态，读 + 拍 + 再读
console.log('\n=== 基线 ===');
await step('基线·展开', 'M-313-参数卡片-展开时.png');

// ③ 只点 `⤢`
const ex = await locate(VID, EXPAND);
out.按钮 = ex;
if (!ex.found) { console.log('!! 找不到 ⤢'); await browser.close(); process.exit(1); }
await page.mouse.move(ex.cx, ex.cy);
await page.waitForTimeout(600);
await page.mouse.click(ex.cx, ex.cy);
await page.waitForTimeout(1200);
console.log('\n=== 点完 ⤢ ===');
const s1 = await step('点完⤢', 'M-314-参数卡片-点了⤢之后.png');
out.真的折叠了吗 = s1.拍图后.最大浮层 !== out.选中后.最大浮层;

// ④ 会不会自己弹回来：12 × 2 秒
console.log('\n=== 24 秒时间序列（看会不会自动恢复）===');
out.时间序列 = [];
const base = s1.拍图后.最大浮层;
for (let i = 0; i < 12; i += 1) {
  await page.waitForTimeout(2000);
  const t = await truth(VID);
  out.时间序列.push({ 秒: (i + 1) * 2, 最大浮层: t.最大浮层, 文字长度: t.文字长度, 恢复了: t.最大浮层 !== base });
  if (t.最大浮层 !== base) { console.log(`  ⭐ ${(i + 1) * 2}s 时自动恢复了：${base} → ${t.最大浮层}`); break; }
}
if (!out.时间序列.some((x) => x.恢复了)) console.log(`  ${out.时间序列.length * 2} 秒内始终是 ${base}，没有自动恢复`);
out.折叠持续秒数 = out.时间序列.length * 2;

out.固定clip = FIXED_CLIP;
out.balance = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const t = [...document.querySelectorAll('header *,nav *')].filter(vis).map((e) => (e.innerText || '').trim()).filter((x) => /^\d{1,4}$/.test(x));
  return t.length ? Number(t[t.length - 1]) : null;
});

await writeFile(resolve(HERE, '.evidence/cg9-final-single-variable.json'), JSON.stringify(out, null, 2));
console.log('\n真的折叠了吗 =', out.真的折叠了吗, '| 折叠持续 =', out.折叠持续秒数, '秒 | 余额 =', out.balance);
await browser.close();
