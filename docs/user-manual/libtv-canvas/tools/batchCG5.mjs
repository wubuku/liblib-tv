// Batch CG-5：CG-4 的阳性对照也不成立，再来一次 —— 这次把「选器选中了谁」变成可见读数。
//
// CG-4 失败在两处，**都值得单独记**：
//
//   ① `.node-floating-ui` 在**一个节点内不止一个**：
//      CG-1 在目标节点里读到参数卡片是 `660x248`；
//      CG-3 用全页 `querySelector` 量到 `164x23`；CG-4 改成节点内查，量到 `292x23`。
//      三次量的都不是同一块东西 —— 因为 `querySelector` **只取第一个匹配**。
//      ⇒ 本步把节点内**所有** `.node-floating-ui` 的尺寸全报出来，**让选错对象这件事看得见**。
//
//   ② ⭐ 拿 `⚙ 高级设置` 当阳性对照**本身就选错了**：
//      读数里 `节点内总文字` **在点击之前就已经**包含
//      「高级设置 联网搜索 自动校验素材 智能引用 AutoLink」
//      ⇒ **它本来就是展开的**（很早以前某次操作留下的状态），点一下是**收起**，
//      而「收起」在「点前就展开」的基线下**根本不该期待文字变短** ——
//      这是**基线不干净**（§77），不是「读法失效」。
//
// 本步的对照换成**顶部工具条的 `参考`**（`M8.5 0c.5 0 .9.48.9 1.06V7.6h6.54…`）：
// 它当前没有任何面板开着，**点开必然出现新面板**，是干净的「无 → 有」。
// 并且对照和被测**都用真鼠标点** —— 因为 CG-3/CG-4 一直存疑的就是
// `el.click()` 到底能不能触发这些按钮。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { fingerprint, diffPanels } from './scenario.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const EXPAND = 'M1.4 8.9c.22 0 .4.18.4.4v5.54l5.26-5.26a.4.4 0 0 1 .57 0l.7.71';
const REF = 'M8.5 0c.5 0 .9.48.9 1.06V7.6h6.54c.58 0 1.06.4';
const GEAR = 'M14 17H5M19 7h-9';
const VID = 'v-eMpqKtiLlx';

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

// ⭐ 判据 v2：节点内所有浮层的尺寸全报出来，并单独点名**最大**的那一块
const truth = (nid) => page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { err: 'node not in DOM' };
  const fus = [...node.querySelectorAll('.node-floating-ui')].map((el) => {
    const r = el.getBoundingClientRect();
    return { 尺寸: `${Math.round(r.width)}x${Math.round(r.height)}`, 位置: [Math.round(r.x), Math.round(r.y)], 面积: Math.round(r.width * r.height), cls: (el.className || '').toString().slice(0, 40) };
  }).filter((x) => x.面积 > 0).sort((a, b) => b.面积 - a.面积);
  const prompt = node.querySelector('.text-fg-default[contenteditable="true"]');
  const txt = (node.innerText || '').replace(/\s+/g, ' ').trim();
  return {
    节点内浮层清单: fus,
    最大的浮层: fus[0] ? `${fus[0].尺寸} 面积${fus[0].面积}` : '无',
    提示词: prompt ? (prompt.innerText || '').trim() : null,
    节点内文字长度: txt.length,
    // ⭐ 判据要「对变化敏感」：直接比对整段文字，而不是只比长度
    节点内文字: txt.slice(0, 400),
    含高级设置面板: /联网搜索|自动校验素材|智能引用\s*AutoLink/.test(txt),
    url: location.href,
  };
}, nid);

const locate = (nid, pre) => page.evaluate(({ n, p }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { found: false, why: 'node not in DOM' };
  let idx = 0;
  for (const b of node.querySelectorAll('button,[role="button"]')) {
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (!d.includes(p)) continue;
    idx += 1;
    const r = b.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    return {
      found: true, 第几个匹配: idx, 文字: (b.innerText || '').trim().slice(0, 10),
      cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      w: Math.round(r.width), h: Math.round(r.height),
      disabled: b.disabled === true, cursor: getComputedStyle(b).cursor,
      inViewport: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight,
    };
  }
  return { found: false, why: '没找到' };
}, { n: nid, p: pre });

const snap = async () => ({ t: await truth(VID), fp: await fingerprint(page) });
// ⚠️ 入参是 snap 的结果 `{t, fp}` —— 上传成 `t` 会让 diffPanels 收到 undefined
const diffOf = (A, B) => {
  const a = A.t ?? A; const b = B.t ?? B;
  return {
    最大浮层: `${a.最大的浮层} → ${b.最大的浮层}`,
    浮层数: `${a.节点内浮层清单.length} → ${b.节点内浮层清单.length}`,
    提示词: `${JSON.stringify(a.提示词)} → ${JSON.stringify(b.提示词)}`,
    文字变了: a.节点内文字 !== b.节点内文字,
    文字长度: `${a.节点内文字长度} → ${b.节点内文字长度}`,
    高级设置面板: `${a.含高级设置面板} → ${b.含高级设置面板}`,
    url变了: a.url !== b.url,
    新增面板: diffPanels(A.fp || [], B.fp || []).map((p) => ({ area: p.area, 文字: p.all.slice(0, 90) })),
  };
};

await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2200);
await page.evaluate((n) => document.querySelector(`.react-flow__node[data-id="${n}"]`)?.click(), VID);
await page.waitForTimeout(2000);
const sel = await page.evaluate((n) => {
  const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  return { inDom: !!el, selected: !!el && el.className.includes('selected') };
}, VID);
if (!sel.selected) { console.log('!! 没选中，作废'); await browser.close(); process.exit(1); }
await page.mouse.move(5, 5);
await page.waitForTimeout(600);

out.基线 = await truth(VID);
console.log('基线 =', JSON.stringify(out.基线, null, 2));

const balance = () => page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const t = [...document.querySelectorAll('header *,nav *')].filter(vis).map((e) => (e.innerText || '').trim()).filter((x) => /^\d{1,4}$/.test(x));
  return t.length ? Number(t[t.length - 1]) : null;
});
out.balance0 = await balance();

// ═══ 阳性对照：顶部工具条 `参考`，当前无面板，点开必然有 ═══
const ref = await locate(VID, REF);
out.对照按钮 = ref;
if (!ref.found) { console.log('!! 找不到参考按钮'); await browser.close(); process.exit(1); }
const cA = await snap();
await page.mouse.move(ref.cx, ref.cy);
await page.waitForTimeout(400);
await page.mouse.click(ref.cx, ref.cy);            // 真鼠标
await page.waitForTimeout(1600);
const cB = await snap();
out.对照 = { 前: cA.t.最大的浮层, 后: cB.t.最大的浮层, 差异: diffOf(cA.t, cB.t) };
out.对照.通过 = cA.t.节点内文字 !== cB.t.节点内文字 || cA.t.最大的浮层 !== cB.t.最大的浮层
  || diffPanels(cA.fp, cB.fp).length > 0;
console.log('【阳性对照 点「参考」】通过 =', out.对照.通过);
console.log('  差异 =', JSON.stringify(out.对照.差异, null, 2));
await shot(page, 'M-310-参考面板-已打开.png');

// 复原对照：按 Esc 关掉
await page.keyboard.press('Escape');
await page.waitForTimeout(1200);
const cC = await snap();
out.对照.复原 = diffOf(cB.t, cC.t);
console.log('  对照复原 =', JSON.stringify(out.对照.复原));

if (!out.对照.通过) {
  console.log('!! 阳性对照仍不通过 —— 读法捕捉不到变化，阴性结论一律作废');
  await writeFile(resolve(HERE, '.evidence/cg5-expand-final.json'), JSON.stringify(out, null, 2));
  await browser.close();
  process.exit(2);
}

// ═══ 被测：`⤢`，真鼠标点（对照已证明真鼠标 + 这套读法能看到变化） ═══
await page.evaluate((n) => document.querySelector(`.react-flow__node[data-id="${n}"]`)?.click(), VID);
await page.waitForTimeout(1400);
const ex = await locate(VID, EXPAND);
out.被测按钮 = ex;
if (!ex.found) { console.log('!! 找不到 ⤢'); await browser.close(); process.exit(1); }
const tA = await snap();
await page.mouse.move(5, 5);
await page.waitForTimeout(400);
await page.mouse.move(ex.cx, ex.cy);
await page.waitForTimeout(600);
out.被测命中 = await page.evaluate(({ x, y, p }) => {
  const el = document.elementFromPoint(x, y);
  const btn = el ? el.closest('button,[role="button"]') : null;
  if (!btn) return { 命中: '不是按钮', 实际: el ? `${el.tagName}.${(el.className || '').toString().slice(0, 40)}` : 'null' };
  const svg = btn.querySelector('svg');
  const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
  return { 是不是目标: d.includes(p), cursor: getComputedStyle(btn).cursor, 文字: (btn.innerText || '').trim() };
}, { x: ex.cx, y: ex.cy, p: EXPAND });
await page.mouse.click(ex.cx, ex.cy);
await page.waitForTimeout(1600);
const tB = await snap();
out.被测 = { 差异: diffOf(tA.t, tB.t) };
out.被测.变了 = tA.t.节点内文字 !== tB.t.节点内文字 || tA.t.最大的浮层 !== tB.t.最大的浮层
  || diffPanels(tA.fp, tB.fp).length > 0;
console.log('【被测 点 ⤢（真鼠标）】变了 =', out.被测.变了, JSON.stringify(out.被测.差异, null, 2));
await shot(page, 'M-311-点了节点右上角⤢之后.png');

// 第二种手法：el.click()（对照已证真鼠标有效 ⇒ 两种手法的差别才有意义）
const uA = await snap();
await page.evaluate(({ n, p }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  for (const b of node.querySelectorAll('button,[role="button"]')) {
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (d.includes(p)) { b.click(); return; }
  }
}, { n: VID, p: EXPAND });
await page.waitForTimeout(1400);
const uB = await snap();
out.被测_elclick = { 差异: diffOf(uA.t, uB.t) };
out.被测_elclick.变了 = uA.t.节点内文字 !== uB.t.节点内文字 || uA.t.最大的浮层 !== uB.t.最大的浮层;
console.log('【被测 el.click()】变了 =', out.被测_elclick.变了, JSON.stringify(out.被测_elclick.差异));

out.balance1 = await balance();
out.判定 = {
  阳性对照通过: out.对照.通过,
  '真鼠标点⤢': out.被测.变了,
  'el.click()点⤢': out.被测_elclick.变了,
  余额: `${out.balance0} → ${out.balance1}`,
  提示词: `${JSON.stringify(tA.t.提示词)} → ${JSON.stringify(tB.t.提示词)}`,
};

await writeFile(resolve(HERE, '.evidence/cg5-expand-final.json'), JSON.stringify(out, null, 2));
console.log('\n=== 判定 ===', JSON.stringify(out.判定, null, 2));
await browser.close();
