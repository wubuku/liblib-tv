// Batch CG-10：别再用「容器尺寸」下结论了 —— 直接列出**点了之后到底消失了什么**。
//
// 为什么必须重做（CG-5/6/8/9 一路自相矛盾的根因）：
//   我的判据是「节点内**面积最大**的 `.node-floating-ui`」。
//   但节点里那层是**外层浮层容器**；真正画在屏幕上的卡片是它**内层**的
//   `div.bg-panel-background.relative.flex.w-full.flex-col`（CG-1 的祖先链已经把它露出来了）。
//   ⛔ 于是出现了「读数说 660x248 → 292x23（像是整张卡没了）」、
//      「画面说卡片明明还在，只是**里面的东西**没了」这种打架。
//
// 本步只做一件事：**元素差集**。
//   点之前把节点内**每一个可见元素**的「class / 矩形 / 文字」记下来，
//   点之后再来一遍，**逐项 diff**。
//   ⇒ 结论直接长成「哪几样东西不见了」，而不是我去猜「整张卡还是没整张卡」。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const EXPAND = 'M1.4 8.9c.22 0 .4.18.4.4v5.54l5.26-5.26a.4.4 0 0 1 .57 0l.7.71';
const VID = 'v-eMpqKtiLlx';

// 节点内的可见元素清单 —— 以「能独立看见的一层」为单位：
// 带文字的叶子、每个 button/svg、以及卡片容器本身
const inventory = (nid) => page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { err: 'node not in DOM' };
  const vis = (el) => {
    const r = el.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) return false;
    const s = getComputedStyle(el);
    return s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0.05;
  };
  const items = [];
  const push = (el, kind) => {
    const r = el.getBoundingClientRect();
    const txt = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40);
    items.push({
      kind, 文字: txt,
      矩形: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cls: (el.className || '').toString().slice(0, 46),
    });
  };
  for (const el of node.querySelectorAll('*')) {
    if (!vis(el)) continue;
    const isLeafText = el.children.length === 0 && (el.innerText || '').trim();
    if (isLeafText) { push(el, '文字'); continue; }
    if (el.tagName === 'BUTTON' || el.getAttribute('role') === 'button') {
      const svg = el.querySelector('svg');
      const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
      push(el, d ? `按钮·${d.slice(0, 18)}` : '按钮');
    }
  }
  // 卡片容器：两个都记，并标出谁更大
  for (const el of node.querySelectorAll('.node-floating-ui, .bg-panel-background')) {
    if (vis(el)) push(el, `容器.${(el.className || '').toString().split(' ')[0]}`);
  }
  return { 数量: items.length, items };
}, nid);

// 同一类元素的匹配键：文字优先，其次 class+尺寸
const keyOf = (it) => (it.文字 ? `文:${it.文字}` : `${it.kind}|${it.cls}|${it.矩形[2]}x${it.矩形[3]}`);

const { browser, page } = await launch();
const out = {};

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
await page.waitForTimeout(1000);

const findBlank = () => page.evaluate(() => {
  for (const [x, y] of [[720, 100], [1300, 180], [720, 700], [200, 380], [1240, 640], [80, 200], [1360, 400]]) {
    const el = document.elementFromPoint(x, y);
    if (el && !el.closest('.react-flow__node') && !el.closest('button,[role="button"]') && !el.closest('input,[contenteditable="true"]')) return { x, y };
  }
  return null;
});

const blank = await findBlank();
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
const hit = await page.evaluate(({ x, y, n }) => {
  const el = document.elementFromPoint(x, y);
  const nd = el ? el.closest('.react-flow__node') : null;
  return nd ? nd.getAttribute('data-id') : null;
}, { x: c.cx, y: c.cy, n: VID });
if (hit !== VID) { console.log('!! 点不中目标'); await browser.close(); process.exit(1); }
await page.mouse.move(c.cx, c.cy);
await page.waitForTimeout(400);
await page.mouse.click(c.cx, c.cy);
await page.waitForTimeout(2000);

// 固定的 clip：**标题栏 ∪ 参数卡片**的并集。
// ⚠️ 只按参数卡片（`.bg-panel-background.relative`）算会裁掉标题栏（它在 y=293，参数卡片在 y=489），
//    而折叠后**参数卡片整张消失** ⇒ clip 区域露出来的是**它下面另一个节点的卡片**，
//    拍出来会像「折叠后还剩一张带参数条的卡」—— 完全是误导（CG-10 第一版就这么废掉的）。
const clip = await page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return null;
  const boxes = [node.getBoundingClientRect(),
    ...[...node.querySelectorAll('.node-floating-ui')].map((el) => el.getBoundingClientRect())];
  const x0 = Math.min(...boxes.map((r) => r.x));
  const y0 = Math.min(...boxes.map((r) => r.y));
  const x1 = Math.max(...boxes.map((r) => r.right));
  const y1 = Math.max(...boxes.map((r) => r.bottom));
  const x = Math.max(0, Math.round(x0 - 20)), y = Math.max(0, Math.round(y0 - 20));
  return { x, y, width: Math.min(1440 - x, Math.round(x1 - x0 + 40)), height: Math.min(810 - y, Math.round(y1 - y0 + 40)) };
}, VID);
out.clip = clip;

const inv0 = await inventory(VID);
out.点前 = inv0;
await shot(page, 'M-313-参数卡片-展开时.png', { clip });

// 点 `⤢`
const ex = await page.evaluate(({ n, p }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  for (const b of node.querySelectorAll('button,[role="button"]')) {
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (d.includes(p)) {
      const r = b.getBoundingClientRect();
      return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
    }
  }
  return null;
}, { n: VID, p: EXPAND });
if (!ex) { console.log('!! 找不到 ⤢'); await browser.close(); process.exit(1); }
await page.mouse.move(ex.cx, ex.cy);
await page.waitForTimeout(600);
await page.mouse.click(ex.cx, ex.cy);
await page.waitForTimeout(1600);

const inv1 = await inventory(VID);
out.点后 = inv1;
await shot(page, 'M-314-参数卡片-点了⤢之后.png', { clip });   // ⭐ 同一个 clip

// ── 差集 ──
const k0 = new Set(inv0.items.map(keyOf));
const k1 = new Set(inv1.items.map(keyOf));
out.消失的 = inv0.items.filter((it) => !k1.has(keyOf(it)));
out.新增的 = inv1.items.filter((it) => !k0.has(keyOf(it)));
out.仍在 = inv0.items.filter((it) => k1.has(keyOf(it)));

console.log(`\n点前元素数 = ${inv0.数量}，点后 = ${inv1.数量}`);
console.log(`\n⭐ 消失了 ${out.消失的.length} 项：`);
for (const it of out.消失的) console.log(`   - [${it.kind}] ${it.文字 ? `"${it.文字}"` : it.cls} ${it.矩形.join(',')}`);
console.log(`\n⭐ 新增了 ${out.新增的.length} 项：`);
for (const it of out.新增的) console.log(`   + [${it.kind}] ${it.文字 ? `"${it.文字}"` : it.cls} ${it.矩形.join(',')}`);

out.balance = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const t = [...document.querySelectorAll('header *,nav *')].filter(vis).map((e) => (e.innerText || '').trim()).filter((x) => /^\d{1,4}$/.test(x));
  return t.length ? Number(t[t.length - 1]) : null;
});
console.log('\n余额 =', out.balance);

await writeFile(resolve(HERE, '.evidence/cg10-element-diff.json'), JSON.stringify(out, null, 2));
await browser.close();
