// Batch CG-4：CG-3 那组「什么都没变」的读数**作废**，重来一次。
//
// ⛔ CG-3 的阴性读数为什么不算数（两条都是我自己写过的教训）：
//
//   ① **判据没锁定目标对象**（缺陷 78 的变种）：
//      `truth()` 里写的是 `document.querySelector('.react-flow__node.float-ui, .node-floating-ui')`
//      —— 全页**第一个**匹配，量到的根本不是目标节点的浮层：
//      CG-3 读到 `164x23`，而 CG-1 在**同一个节点内**读到的是 `660x248`。
//      ⇒ 判据一直在量别的东西，「没变化」当然成立。必须改成**在目标节点内**查。
//      而且 CG-3 还存了 `fingerprint()` 却**根本没做 diff**，等于白存。
//
//   ② **没有阳性对照**（§76）：阴性读数必须先证明「这套读法能捕捉到变化」。
//      本步用一枚**已知会展开面板**的 `⚙ 高级设置`（`M14 17H5M19 7h-9`）当对照 ——
//      点它面板必然展开。对照能捕捉到 ⇒ `⤢` 的读数才有意义；捕捉不到 ⇒ 只输出「没测到」。
//
// ⭐ 第三条**新**的可能性（本步专门去分辨它）：
//   `⤢` 可能是**要 hover 才显形/才可点**的（它是 `absolute right-2 top-2` 压在卡片角上）。
//   而 `el.click()` **不带指针、也不带 hover 态** —— 对某些组件根本不触发。
//   ⇒ 所以本步**同时**用两种手法：① `el.click()`；② **先 hover 让它显形，再用真鼠标点屏幕坐标**。
//   两种都做完还平，才能下「它点了没反应」这种结论。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { fingerprint, diffPanels } from './scenario.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const EXPAND = 'M1.4 8.9c.22 0 .4.18.4.4v5.54l5.26-5.26a.4.4 0 0 1 .57 0l.7.71';
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

const balance = () => page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const t = [...document.querySelectorAll('header *,nav *')].filter(vis).map((e) => (e.innerText || '').trim()).filter((x) => /^\d{1,4}$/.test(x));
  return t.length ? Number(t[t.length - 1]) : null;
});

// ✅ 修好的判据：**在目标节点内**量，而且量「这一个节点」的一切关键尺寸
const truth = (nid) => page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { err: 'node not in DOM' };
  const rect = (el) => { if (!el) return null; const r = el.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)].join(','); };
  const fu = node.querySelector('.node-floating-ui');           // ⭐ 限定在这个节点内
  const fuBox = fu ? fu.getBoundingClientRect() : null;
  const prompt = node.querySelector('.text-fg-default[contenteditable="true"]');
  return {
    这个节点的浮层: fuBox ? `${Math.round(fuBox.width)}x${Math.round(fuBox.height)}@${Math.round(fuBox.x)},${Math.round(fuBox.y)}` : '无',
    节点壳: rect(node.querySelector('.node-shell')) || rect(node),
    节点内可见按钮数: [...node.querySelectorAll('button,[role="button"]')].filter((b) => { const r = b.getBoundingClientRect(); return r.width > 0 && r.height > 0; }).length,
    节点内总文字长度: (node.innerText || '').replace(/\s+/g, ' ').trim().length,
    节点内总文字前120: (node.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
    提示词: prompt ? (prompt.innerText || '').trim() : null,
    提示词存在: !!prompt,
    是否selected: node.className.includes('selected'),
    url: location.href,
    页面滚动容器: (() => { const s = [...document.querySelectorAll('div')].find((d) => d.scrollHeight > d.clientHeight + 40 && d.clientHeight > 300); return s ? `${s.clientHeight}/${s.scrollHeight}` : null; })(),
  };
}, nid);

// 找按钮，**返回屏幕坐标**（真鼠标要用），并报告它在不在视口内
const locate = (nid, pre) => page.evaluate(({ n, p }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { found: false, why: 'node not in DOM' };
  for (const b of node.querySelectorAll('button,[role="button"]')) {
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (!d.includes(p)) continue;
    const r = b.getBoundingClientRect();
    const inViewport = r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight;
    return {
      found: true, cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      w: Math.round(r.width), h: Math.round(r.height),
      disabled: b.disabled === true, cursor: getComputedStyle(b).cursor, inViewport,
      opacity: getComputedStyle(b).opacity, visibility: getComputedStyle(b).visibility,
    };
  }
  return { found: false, why: '没找到该路径的按钮' };
}, { n: nid, p: pre });

const clickEl = (nid, pre) => page.evaluate(({ n, p }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { ok: false, why: 'node not in DOM' };
  for (const b of node.querySelectorAll('button,[role="button"]')) {
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (d.includes(p)) { b.click(); return { ok: true }; }
  }
  return { ok: false, why: '没找到' };
}, { n: nid, p: pre });

// 硬前置
async function selectNode() {
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2200);
  await page.evaluate((n) => document.querySelector(`.react-flow__node[data-id="${n}"]`)?.click(), VID);
  await page.waitForTimeout(2000);
  return page.evaluate((n) => {
    const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
    return { inDom: !!el, selected: !!el && el.className.includes('selected') };
  }, VID);
}

const snap = async (tag) => ({ tag, t: await truth(VID), fp: await fingerprint(page) });

// ═══ 步骤 1：阳性对照 —— 点 `⚙`，确认「这套读法能捕捉到变化」 ═══
let sel = await selectNode();
if (!sel.selected) { console.log('!! 没选中，作废'); await browser.close(); process.exit(1); }
await page.mouse.move(5, 5);
await page.waitForTimeout(500);

const gear0 = await locate(VID, GEAR);
const ctlA = await snap('对照-点⚙前');
out.control = { gear按钮: gear0 };
out.control.click = await clickEl(VID, GEAR);
await page.waitForTimeout(1200);
const ctlB = await snap('对照-点⚙后');
out.control.变了 = ctlA.t.这个节点的浮层 !== ctlB.t.这个节点的浮层 || ctlA.t.节点内总文字长度 !== ctlB.t.节点内总文字长度;
out.control.新增面板 = diffPanels(ctlA.fp, ctlB.fp).map((p) => ({ sig: p.sig, area: p.area, 文字: p.all.slice(0, 100) }));
out.control.前 = { 浮层: ctlA.t.这个节点的浮层, 文字长度: ctlA.t.节点内总文字长度, 文字前120: ctlA.t.节点内总文字前120 };
out.control.后 = { 浮层: ctlB.t.这个节点的浮层, 文字长度: ctlB.t.节点内总文字长度, 文字前120: ctlB.t.节点内总文字前120 };
console.log('【阳性对照：点 ⚙ 高级设置】', JSON.stringify({ 变了: out.control.变了, 前: out.control.前, 后: out.control.后 }));

// 复原对照：再点一次 ⚙ 收回去
await clickEl(VID, GEAR);
await page.waitForTimeout(1000);
const ctlC = await snap('对照-复原后');
out.control.复原了 = ctlC.t.这个节点的浮层 === ctlA.t.这个节点的浮层 && ctlC.t.节点内总文字长度 === ctlA.t.节点内总文字长度;
console.log('对照复原 =', out.control.复原了, JSON.stringify({ 浮层: ctlC.t.这个节点的浮层, 文字长度: ctlC.t.节点内总文字长度 }));

// ═══ 步骤 2：阳性对照不通过就直接退出 —— 读法捕捉不到变化，阴性结论一律无效 ═══
if (!out.control.变了) {
  console.log('!! 阳性对照不通过：这套读法捕捉不到任何变化，后续阴性读数一律作废');
  await writeFile(resolve(HERE, '.evidence/cg4-expand-retry.json'), JSON.stringify(out, null, 2));
  await browser.close();
  process.exit(2);
}

// ═══ 步骤 3：测 `⤢`，两种点法各来一次 ═══
out.balance0 = await balance();
const ex = await locate(VID, EXPAND);
out.expand按钮 = ex;

// 手法 A：el.click()
const a0 = await snap('A-点前');
out.A = { click: await clickEl(VID, EXPAND) };
await page.waitForTimeout(1400);
const a1 = await snap('A-点后');
out.A.前 = a0.t; out.A.后 = a1.t;
out.A.变了 = a0.t.这个节点的浮层 !== a1.t.这个节点的浮层
  || a0.t.节点内可见按钮数 !== a1.t.节点内可见按钮数
  || a0.t.节点内总文字长度 !== a1.t.节点内总文字长度
  || a0.t.url !== a1.t.url;
out.A.新增面板 = diffPanels(a0.fp, a1.fp).map((p) => ({ sig: p.sig, area: p.area, 文字: p.all.slice(0, 100) }));
console.log('【手法 A：el.click()】变了 =', out.A.变了);
console.log('  前', JSON.stringify({ 浮层: a0.t.这个节点的浮层, 按钮数: a0.t.节点内可见按钮数, 文字长度: a0.t.节点内总文字长度, 提示词: a0.t.提示词 }));
console.log('  后', JSON.stringify({ 浮层: a1.t.这个节点的浮层, 按钮数: a1.t.节点内可见按钮数, 文字长度: a1.t.节点内总文字长度, 提示词: a1.t.提示词 }));
console.log('  新增面板 =', JSON.stringify(out.A.新增面板));

// 手法 B：先 hover 让它显形，再用**真鼠标**点屏幕坐标
const b0 = await snap('B-点前');
if (ex.found) {
  await page.mouse.move(5, 5);
  await page.waitForTimeout(400);
  // 先把鼠标移到节点卡片上，模拟用户「手放在节点上」的状态
  const nodeBox = await page.evaluate((n) => {
    const el = document.querySelector(`.react-flow__node[data-id="${n}"] .node-shell`);
    if (!el) return null; const r = el.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + 30) };
  }, VID);
  if (nodeBox) { await page.mouse.move(nodeBox.cx, nodeBox.cy); await page.waitForTimeout(700); }
  const exAfterHover = await locate(VID, EXPAND);
  out.B = { hover前: ex, hover后: exAfterHover };
  if (exAfterHover.found) {
    await page.mouse.move(exAfterHover.cx, exAfterHover.cy);
    await page.waitForTimeout(600);
    out.B.命中 = await page.evaluate(({ x, y, p }) => {
      const el = document.elementFromPoint(x, y);
      const btn = el ? el.closest('button,[role="button"]') : null;
      if (!btn) return { 命中: '不是按钮' };
      const svg = btn.querySelector('svg');
      const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
      return { 是不是目标: d.includes(p), cursor: getComputedStyle(btn).cursor, 文字: (btn.innerText || '').trim() };
    }, { x: exAfterHover.cx, y: exAfterHover.cy, p: EXPAND });
    await page.mouse.click(exAfterHover.cx, exAfterHover.cy);   // 真鼠标
  }
}
await page.waitForTimeout(1400);
const b1 = await snap('B-点后');
out.B.前 = b0.t; out.B.后 = b1.t;
out.B.变了 = b0.t.这个节点的浮层 !== b1.t.这个节点的浮层
  || b0.t.节点内可见按钮数 !== b1.t.节点内可见按钮数
  || b0.t.节点内总文字长度 !== b1.t.节点内总文字长度
  || b0.t.url !== b1.t.url;
out.B.新增面板 = diffPanels(b0.fp, b1.fp).map((p) => ({ sig: p.sig, area: p.area, 文字: p.all.slice(0, 100) }));
console.log('【手法 B：hover + 真鼠标点】变了 =', out.B.变了);
console.log('  命中 =', JSON.stringify(out.B.命中));
console.log('  前', JSON.stringify({ 浮层: b0.t.这个节点的浮层, 按钮数: b0.t.节点内可见按钮数, 文字长度: b0.t.节点内总文字长度 }));
console.log('  后', JSON.stringify({ 浮层: b1.t.这个节点的浮层, 按钮数: b1.t.节点内可见按钮数, 文字长度: b1.t.节点内总文字长度 }));
console.log('  新增面板 =', JSON.stringify(out.B.新增面板));

out.balance1 = await balance();
out.提示词基线 = a0.t.提示词;
out.判定 = {
  阳性对照通过: out.control.变了,
  手法A变了: out.A.变了,
  手法B变了: out.B.变了,
  余额: `${out.balance0} → ${out.balance1}`,
  提示词: `${a0.t.提示词} → ${b1.t.提示词}`,
  url: `${a0.t.url} → ${b1.t.url}`,
};

await writeFile(resolve(HERE, '.evidence/cg4-expand-retry.json'), JSON.stringify(out, null, 2));
console.log('\n=== 判定 ===');
console.log(JSON.stringify(out.判定, null, 2));
await browser.close();
