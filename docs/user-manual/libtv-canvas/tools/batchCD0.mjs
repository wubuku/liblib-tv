// Batch CD-0：找「提示词框」本体。
// CA④ 记的是「有内容时点『翻译提示词』📖 —— 提示词框没找到」。
// ⭐ 先证明框**在哪、长什么样、怎么往里写字**，再谈点按钮会发生什么。
// 这一步只定位与读，**不点「翻译提示词」**（它会外发一次翻译请求）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
const out = {};

await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.waitForTimeout(800);

out.editable = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const pick = (el) => {
    const r = el.getBoundingClientRect();
    return {
      tag: el.tagName, type: el.getAttribute('type'), aria: el.getAttribute('aria-label'),
      ph: el.placeholder || el.getAttribute('data-placeholder') || null,
      ce: el.getAttribute('contenteditable'), role: el.getAttribute('role'),
      cls: (el.className?.toString?.() || '').slice(0, 70),
      box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      val: (el.value !== undefined ? el.value : (el.innerText || '')).slice(0, 40),
    };
  };
  return {
    textarea: [...document.querySelectorAll('textarea')].filter(vis).map(pick),
    inputs: [...document.querySelectorAll('input')].filter(vis).map(pick).slice(0, 20),
    contenteditable: [...document.querySelectorAll('[contenteditable="true"],[contenteditable=""]')].filter(vis).map(pick).slice(0, 20),
    prosemirror: [...document.querySelectorAll('.ProseMirror,[class*="proseMirror"],[data-prosemirror]')].filter(vis).map(pick).slice(0, 10),
  };
});

// 参数条（选中节点才出现）：先选一个文本节点
out.selectTextNode = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const n = [...document.querySelectorAll('.react-flow__node')].filter(vis)
    .find((e) => (e.innerText || '').includes('文本节点'));
  if (!n) return { ok: false, why: '没有可见的文本节点' };
  const r = n.getBoundingClientRect();
  n.click();
  return { ok: true, box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
});
await page.waitForTimeout(2000);
out.afterSelect = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const pick = (el) => {
    const r = el.getBoundingClientRect();
    return { tag: el.tagName, type: el.getAttribute('type'), aria: el.getAttribute('aria-label'),
      ph: el.placeholder || null, ce: el.getAttribute('contenteditable'),
      cls: (el.className?.toString?.() || '').slice(0, 70),
      box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      val: (el.value !== undefined ? String(el.value) : (el.innerText || '')).slice(0, 40) };
  };
  return {
    textarea: [...document.querySelectorAll('textarea')].filter(vis).map(pick),
    contenteditable: [...document.querySelectorAll('[contenteditable="true"],[contenteditable=""]')].filter(vis).map(pick).slice(0, 20),
    prose: [...document.querySelectorAll('.ProseMirror')].filter(vis).map(pick),
    // 参数条上的按钮逐枚实名
    paramBtns: [...document.querySelectorAll('button,[role="button"]')].filter(vis)
      .map((b) => { const r = b.getBoundingClientRect(); return { aria: b.getAttribute('aria-label'), t: (b.innerText || '').trim().slice(0, 10), box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; })
      .filter((b) => b.box[1] > 600 || /翻译|提示词|生成|参考/.test((b.aria || '') + b.t)),
  };
});

await writeFile(resolve(HERE, '.evidence/cd0-prompt.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 2).slice(0, 4000));
await browser.close();
