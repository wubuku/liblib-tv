// Batch CE-1：⭐ 用 **SVG 路径当身份证**认按钮，然后对它 `el.click()` —— 坐标一律不参与。
//
// 为什么这次能成：前三轮全栽在「坐标点不中按钮」上（47% 缩放下它只有 32×32，
// 且常落在视口外 `y≈891`）。而 `el.click()` 直接作用于元素，**与它在不在画面里无关**。
// 认人的依据是路径前缀：
//   · 翻译提示词 = `M15.52 7.2c.16 0 .31.1.37.26l3.8 10…`
//   · 生成按钮   = `M8.3.3a1 1 0 0 1 1.4 0l8 8a1 1 0 0 1-1.4 1.4L10 3.42V17…`（空提示词时 `disabled`）
//
// 仍然是老规矩：**阳性对照先过**，才准谈「有内容时会发生什么」。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MY_NODE = 't-2AK3Ukyxj3';
const TEXT = 'a cat sitting on a warm windowsill at sunrise';
const SEL = '.text-fg-default[contenteditable="true"]';
const NEEDLE = '提示词为空';
const TRANSLATE_PATH = 'M15.52 7.2c.16 0 .31.1.37.26l3.8 10';

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

const scan = (needle) => page.evaluate((nd) => {
  const hits = [];
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walk.nextNode())) {
    const el = n.parentElement;
    if (!el || /^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE)$/.test(el.tagName)) continue;
    const t = (n.textContent || '').trim();
    if (!nd || t.includes(nd)) {
      const r = el.getBoundingClientRect();
      if (nd && (r.width <= 0 && r.height <= 0)) continue;
      if (nd) hits.push({ text: t.slice(0, 70), tag: el.tagName, cls: (el.className?.toString?.() || '').slice(0, 46), box: [Math.round(r.x), Math.round(r.y)] });
    }
  }
  return hits;
}, needle);

const findTranslate = () => page.evaluate(({ n, pre }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { ok: false, why: 'node not in DOM' };
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const cands = [...node.querySelectorAll('button,[role="button"]')].filter(vis)
    .map((b) => {
      const svg = b.querySelector('svg');
      const p = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
      return { b, p, disabled: b.disabled === true, box: (() => { const r = b.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() };
    });
  const hit = cands.find((c) => c.p.includes(pre));
  if (!hit) return { ok: false, why: `没有按钮的路径以 ${pre} 开头`, n: cands.length, paths: cands.map((c) => c.p.slice(0, 24)) };
  return { ok: true, disabled: hit.disabled, box: hit.box, pathHead: hit.p.slice(0, 60), n: cands.length };
}, { n: MY_NODE, pre: TRANSLATE_PATH });

const clickTranslate = () => page.evaluate(({ n, pre }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  for (const b of [...node.querySelectorAll('button,[role="button"]')].filter(vis)) {
    const svg = b.querySelector('svg');
    const p = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (p.includes(pre)) { b.click(); return { clicked: true, disabled: b.disabled === true }; }
  }
  return { clicked: false };
}, { n: MY_NODE, pre: TRANSLATE_PATH });

// ——— 选节点 ———
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2200);
await page.evaluate((nid) => document.querySelector(`.react-flow__node[data-id="${nid}"]`)?.click(), MY_NODE);
await page.waitForTimeout(1800);
out.btn = await findTranslate();
out.prompt0 = await page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL);
out.balance0 = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const t = [...document.querySelectorAll('header *,nav *')].filter(vis).map((e) => (e.innerText || '').trim()).filter((x) => /^\d{1,4}$/.test(x));
  return t.length ? Number(t[t.length - 1]) : null;
});

// ——— A：阳性对照（空提示词） ———
out.baseA = await scan(NEEDLE);
out.clickA = await clickTranslate();
out.aHit = [];
for (let i = 0; i < 18; i += 1) { await page.waitForTimeout(160); const h = await scan(NEEDLE); if (h.length) { out.aHit = h; break; } }
out.controlPassed = out.baseA.length === 0 && out.aHit.length > 0;
await shot(page, 'M-305-翻译提示词-空提示词弹提示.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });

// ——— B：有内容 ———
await page.waitForTimeout(2500);
const r = await page.evaluate((sel) => { const q = document.querySelector(sel).getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; }, SEL);
await page.evaluate((sel) => {
  const el = document.querySelector(sel);
  el.focus();
  const sel2 = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(el);
  sel2.removeAllRanges();
  sel2.addRange(range);
}, SEL);
await page.keyboard.press('Meta+a');
await page.waitForTimeout(300);
await page.keyboard.press('Backspace');
await page.waitForTimeout(800);
// ⭐ 用**真键盘**打字（比设 innerHTML 更接近真人）
await page.keyboard.type(TEXT, { delay: 18 });
await page.waitForTimeout(1600);
out.promptB = await page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL);
out.typedOk = out.promptB.includes(TEXT);
out.baseB = await scan(NEEDLE);
out.clickB = await clickTranslate();
out.bTimeline = [];
for (const ms of [250, 300, 400, 500, 700, 1000, 1500, 2000, 3000]) {
  await page.waitForTimeout(ms);
  out.bTimeline.push(await page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL));
}
out.valAfter = await page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL);
out.hitB = await scan(NEEDLE);
out.balance1 = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const t = [...document.querySelectorAll('header *,nav *')].filter(vis).map((e) => (e.innerText || '').trim()).filter((x) => /^\d{1,4}$/.test(x));
  return t.length ? Number(t[t.length - 1]) : null;
});
out.panels = await scan(null).then((all) => all.filter((h) => /提示词|翻译|错误|失败|积分/.test(h.text)).slice(0, 6));
await shot(page, 'M-306-翻译提示词-有内容时的结果.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });

// 收尾
await page.evaluate((sel) => {
  const el = document.querySelector(sel);
  el.focus();
  const s = window.getSelection(); const rg = document.createRange();
  rg.selectNodeContents(el); s.removeAllRanges(); s.addRange(rg);
}, SEL);
await page.keyboard.press('Meta+a');
await page.waitForTimeout(300);
await page.keyboard.press('Backspace');
await page.waitForTimeout(1400);
out.afterClear = await page.evaluate((sel) => (document.querySelector(sel)?.innerText || '').trim(), SEL);

out.verdict = !out.btn.ok ? '⛔ 没认出那枚按钮（路径对不上）—— 读数不成立'
  : !out.controlPassed ? '⛔ 阳性对照仍未通过 —— 读数不成立，不能下结论'
  : (out.hitB.length ? `✅ 有内容时弹了：${JSON.stringify(out.hitB).slice(0, 200)}`
    : (out.valAfter === out.promptB
      ? '✅ 对照通过 + 有内容时**提示词原样不变、无任何提示** —— 这枚按钮当前是**空转**的'
      : `✅ 对照通过 + 有内容时提示词变成了：${JSON.stringify(out.valAfter).slice(0, 200)}`));
await writeFile(resolve(HERE, '.evidence/ce1-translate.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ btn: out.btn, prompt0: out.prompt0, balance0: out.balance0, baseA: out.baseA, clickA: out.clickA, aHit: out.aHit, controlPassed: out.controlPassed, promptB: out.promptB, typedOk: out.typedOk, clickB: out.clickB, bTimeline: out.bTimeline, valAfter: out.valAfter, hitB: out.hitB, balance1: out.balance1, panels: out.panels, afterClear: out.afterClear, verdict: out.verdict }, null, 2).slice(0, 3200));
await browser.close();
