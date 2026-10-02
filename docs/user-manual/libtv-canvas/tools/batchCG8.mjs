// Batch CG-8：「折叠」到底是不是**持续的**，还是只在鼠标停留时成立。
//
// 起因是一个**读数与画面对不上**的矛盾（CG-6）：
//   读数：点完 `⤢` 后 660x248 → 292x23、提示词框消失、文字 113 → 6 字（**折叠了**）
//   画面：紧接着拍的截图里参数卡片**完整展开**（提示词框 / 135 / 生成按钮都在）
//   ⛔ 那张截图因此**名不副实，已删** —— 而矛盾本身必须查清：
//   最可能的解释是 **「折叠」依赖 hover**：鼠标停在卡片上时收起，鼠标一移开就自动展开。
//   如果是这样，正文该写的就不是「它会折叠卡片」，而是「它只在按住/悬停期间收起卡片」。
//
// 本步把「鼠标在哪」当成**自变量**来扫：
//   T0 选中后（鼠标在画布空白）
//   T1 点完 `⤢`，**鼠标不动**
//   T2 把鼠标**移开**到画布空白
//   T3 鼠标**移回**节点上
//   T4 刷新后重新选中（是否落盘）
//
// ⭐ 每个读数**前后各拍一次图并再读一次** —— 用来检测 `shot()` 本身会不会改变状态
//   （如果「拍图 → 状态变了」，那就说明拍图这一步就是干扰源，之前所有配图都得重估）。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const EXPAND = 'M1.4 8.9c.22 0 .4.18.4.4v5.54l5.26-5.26a.4.4 0 0 1 .57 0l.7.71';
const VID = 'v-eMpqKtiLlx';
const IID = 'i-9nlG6HdjK2';
const AID = 'a-CUfJfmKzUJ';

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
await page.waitForTimeout(800);

const truth = (nid) => page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { err: 'node not in DOM' };
  const fus = [...node.querySelectorAll('.node-floating-ui')].map((el) => {
    const r = el.getBoundingClientRect();
    return { 尺寸: `${Math.round(r.width)}x${Math.round(r.height)}`, 面积: Math.round(r.width * r.height) };
  }).filter((x) => x.面积 > 0).sort((a, b) => b.面积 - a.面积);
  const prompt = node.querySelector('.text-fg-default[contenteditable="true"]');
  return {
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

const nodeCenter = (nid) => page.evaluate((n) => {
  const el = document.querySelector(`.react-flow__node[data-id="${n}"] .node-shell`) || document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!el) return null;
  const b = el.getBoundingClientRect();
  return { cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + Math.min(30, b.height / 2)) };
}, nid);

// ⭐ 找一个**确定是空白**的点：不能硬编码坐标 —— 硬编码的 (720,100) 这一轮落在了元素上，
//    导致「点空白解除选中」实际点到了别处，后面「真点节点」就再也选不中。
let BLANK = { x: 720, y: 100 };
const findBlank = () => page.evaluate(() => {
  for (const [x, y] of [[720, 100], [1300, 180], [720, 700], [200, 380], [1240, 640], [80, 200], [1360, 400]]) {
    const el = document.elementFromPoint(x, y);
    if (el && !el.closest('.react-flow__node') && !el.closest('button,[role="button"]') && !el.closest('input,[contenteditable="true"]')) {
      return { x, y };
    }
  }
  return null;
});

async function freshSelect(nid) {
  // ⭐ 先点画布空白解除选中，再真点节点 —— 避开「点已选中节点 = 取消选中」的 toggle 假象
  const b = await findBlank();
  if (b) BLANK = b;
  await page.mouse.click(BLANK.x, BLANK.y);
  await page.waitForTimeout(700);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2200);
  const c = await nodeCenter(nid);
  if (!c) return { selected: false, why: '找不到节点' };
  // ⭐ 校验点下去命中的是不是这个节点本身
  const hit = await page.evaluate(({ x, y, n }) => {
    const el = document.elementFromPoint(x, y);
    const node = el ? el.closest('.react-flow__node') : null;
    return { 命中节点: node ? node.getAttribute('data-id') : null, 目标: n };
  }, { x: c.cx, y: c.cy, n: nid });
  if (hit.命中节点 !== nid) return { selected: false, why: `点(${c.cx},${c.cy}) 命中的是 ${hit.命中节点 || '非节点'} 而不是 ${nid}` };
  await page.mouse.move(c.cx, c.cy);
  await page.waitForTimeout(400);
  await page.mouse.click(c.cx, c.cy);
  await page.waitForTimeout(1700);
  return page.evaluate((n) => {
    const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
    return { selected: !!el && el.className.includes('selected') };
  }, nid);
}

// ⭐ 读数 + 拍图 + **再读一次**（检测 shot 是不是干扰源）
async function probe(tag, nid, clip) {
  const before = await truth(nid);
  await shot(page, `M-313-${tag}.png`, clip ? { clip } : {});
  const after = await truth(nid);
  return { tag, 拍图前: before, 拍图后: after, 拍图改变了状态: before.最大浮层 !== after.最大浮层 || before.提示词框在不在 !== after.提示词框在不想 };
}

// ═══ 视频节点：扫「鼠标在哪」 ═══
let s = await freshSelect(VID);
if (!s.selected) { console.log('!! 没选中'); await browser.close(); process.exit(1); }
await page.mouse.move(BLANK.x, BLANK.y);
await page.waitForTimeout(900);

out.T0_选中后鼠标在空白 = await truth(VID);
const ex = await locate(VID, EXPAND);
out.按钮 = ex;
if (!ex.found) { console.log('!! 找不到 ⤢'); await browser.close(); process.exit(1); }

// T1：移上去点，**鼠标不动**
await page.mouse.move(ex.cx, ex.cy);
await page.waitForTimeout(600);
await page.mouse.click(ex.cx, ex.cy);
await page.waitForTimeout(1600);
out.T1_点完鼠标不动 = await truth(VID);

// T2：把鼠标移到画布空白
await page.mouse.move(BLANK.x, BLANK.y);
await page.waitForTimeout(1200);
out.T2_鼠标移开 = await truth(VID);

// T3：鼠标移回节点
const c3 = await nodeCenter(VID);
if (c3) { await page.mouse.move(c3.cx, c3.cy); await page.waitForTimeout(1200); }
out.T3_鼠标移回节点 = await truth(VID);

// T4：刷新后重新选中
await page.reload({ waitUntil: 'domcontentloaded' });
await page.waitForTimeout(4500);
await closePromos(page);
await page.waitForTimeout(900);
const s4 = await freshSelect(VID);
await page.mouse.move(BLANK.x, BLANK.y);
await page.waitForTimeout(900);
out.T4_刷新后重新选中 = await truth(VID);

out.视频时间线 = [
  ['T0 选中后·鼠标在空白', out.T0_选中后鼠标在空白],
  ['T1 点完·鼠标不动', out.T1_点完鼠标不动],
  ['T2 鼠标移开', out.T2_鼠标移开],
  ['T3 鼠标移回节点', out.T3_鼠标移回节点],
  ['T4 刷新后重新选中', out.T4_刷新后重新选中],
];
console.log('=== 视频节点：鼠标位置 vs 参数卡片 ===');
for (const [k, v] of out.视频时间线) console.log(`  ${k}: ${v.最大浮层} 提示词框=${v.提示词框在不在} ${v.文字长度}字`);

// ⭐ 拍图是否干扰状态：在 T1 那种「鼠标不动」的状态下连拍两张，中间再读
const clip = await page.evaluate((n) => {
  const el = document.querySelector(`.react-flow__node[data-id="${n}"] .node-shell`);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  const x = Math.max(0, Math.round(r.x - 20)), y = Math.max(0, Math.round(r.y - 20));
  return { x, y, width: Math.min(1440 - x, Math.round(r.width + 40)), height: Math.min(810 - y, Math.round(r.height + 40)) };
}, VID);
out.拍图干扰检查 = await probe('拍图干扰检查', VID, clip);
console.log('\n拍图前后 =', JSON.stringify(out.拍图干扰检查));

// ═══ 音频节点复核（CG-6 报它「点了没反应」）══
s = await freshSelect(AID);
if (s.selected) {
  await page.mouse.move(BLANK.x, BLANK.y);
  await page.waitForTimeout(800);
  const a0 = await truth(AID);
  const aex = await locate(AID, EXPAND);
  out.音频 = { 选中后: a0, 按钮: aex };
  if (aex.found) {
    await page.mouse.move(aex.cx, aex.cy);
    await page.waitForTimeout(600);
    await page.mouse.click(aex.cx, aex.cy);
    await page.waitForTimeout(1600);
    out.音频.点后鼠标不动 = await truth(AID);
    await page.mouse.move(BLANK.x, BLANK.y);
    await page.waitForTimeout(1200);
    out.音频.点后鼠标移开 = await truth(AID);
  }
  console.log('\n=== 音频节点 ===');
  console.log('  选中后', a0.最大浮层, a0.文字长度, '字');
  if (out.音频.点后鼠标不动) console.log('  点后·鼠标不动', out.音频.点后鼠标不动.最大浮层, out.音频.点后鼠标不动.文字长度, '字');
  if (out.音频.点后鼠标移开) console.log('  点后·鼠标移开', out.音频.点后鼠标移开.最大浮层, out.音频.点后鼠标移开.文字长度, '字');
}

// 收尾：确保都在展开
await page.reload({ waitUntil: 'domcontentloaded' });
await page.waitForTimeout(4500);
await closePromos(page);
await page.waitForTimeout(800);
out.balance = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const t = [...document.querySelectorAll('header *,nav *')].filter(vis).map((e) => (e.innerText || '').trim()).filter((x) => /^\d{1,4}$/.test(x));
  return t.length ? Number(t[t.length - 1]) : null;
});
console.log('\n收尾：已刷新，余额 =', out.balance);

await writeFile(resolve(HERE, '.evidence/cg8-hover-vs-persist.json'), JSON.stringify(out, null, 2));
await browser.close();
