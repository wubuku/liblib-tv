// Batch CF-1：对 **视频 / 图片 / 音频** 三类节点各跑一遍真翻译。
//
// CF-0 已经坐实：「翻译提示词」在四类节点上是**同一枚图标**（路径前缀
// `M15.52 7.2c.16 0 .31.1.37.26l3.8 10` 逐字相同），所以方法可以照搬。
// 这一步逐类验证「有内容时到底翻不翻」。
//
// ⛔ 三条纪律：
//   ① **只点 `M15.52` 那枚**。生成按钮是 `M8.3.3a1 1 0 0 1 1.4 0l8 8…`，
//      余额只有 20 积分而视频生成要 135 —— 点错就是真扣分且不可逆。
//   ② 每一类都**先读基线**（原始提示词），收尾**清回基线**并复核。
//   ③ 余额前后各读一次。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const PRE = 'M15.52 7.2c.16 0 .31.1.37.26l3.8 10';
const SEL = '.text-fg-default[contenteditable="true"]';
const TEXT = 'a cat sitting on a warm windowsill at sunrise';
const TARGETS = [
  { id: 'v-eMpqKtiLlx', kind: '视频节点 3' },
  { id: 'i-9nlG6HdjK2', kind: '图片节点 2' },
  { id: 'a-CUfJfmKzUJ', kind: '音频节点 6' },
];

const { browser, page } = await launch();
const out = { results: [] };

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
const promptOf = (nid) => page.evaluate(({ n, sel }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  const b = node ? node.querySelector(sel) : null;
  return b ? (b.innerText || '').trim() : null;
}, { n: nid, sel: SEL });
const clickBy = (nid, pre) => page.evaluate(({ n, p }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { ok: false, why: 'node not in DOM' };
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  for (const b of [...node.querySelectorAll('button,[role="button"]')].filter(vis)) {
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (d.includes(p)) { b.click(); return { ok: true, disabled: b.disabled === true }; }
  }
  return { ok: false, why: '没找到该路径的按钮' };
}, { n: nid, p: pre });
const setPrompt = (nid, text) => page.evaluate(({ n, sel, t }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  const el = node ? node.querySelector(sel) : null;
  if (!el) return { ok: false };
  el.focus();
  const s = window.getSelection();
  const rg = document.createRange();
  rg.selectNodeContents(el);
  s.removeAllRanges();
  s.addRange(rg);
  return { ok: true, t };
}, { n: nid, sel: SEL, t: text });

out.balance0 = await balance();

for (const tg of TARGETS) {
  const rec = { kind: tg.kind, id: tg.id };
  // 选中
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2000);
  await page.evaluate((nid) => document.querySelector(`.react-flow__node[data-id="${nid}"]`)?.click(), tg.id);
  await page.waitForTimeout(1900);

  rec.baseline = await promptOf(tg.id);
  rec.hasBox = rec.baseline !== null;
  if (!rec.hasBox) { rec.note = '没有渲染出提示词框'; out.results.push(rec); continue; }

  // 全选删掉再打英文（用真键盘）
  await setPrompt(tg.id, TEXT);
  await page.keyboard.press('Meta+a');
  await page.waitForTimeout(250);
  await page.keyboard.press('Backspace');
  await page.waitForTimeout(700);
  await page.keyboard.type(TEXT, { delay: 16 });
  await page.waitForTimeout(1500);
  rec.before = await promptOf(tg.id);
  rec.typedOk = (rec.before || '').includes(TEXT);
  if (!rec.typedOk) { rec.note = '打字没进去'; out.results.push(rec); continue; }

  rec.click = await clickBy(tg.id, PRE);
  rec.timeline = [];
  for (let i = 0; i < 22; i += 1) {
    await page.waitForTimeout(400);
    const v = await promptOf(tg.id);
    rec.timeline.push(v);
    if (v && v !== rec.before) break;
  }
  rec.after = await promptOf(tg.id);
  rec.changed = rec.after !== rec.before;
  rec.turnedChinese = /[一-鿿]/.test(rec.after || '');

  // 收尾：清回基线
  await setPrompt(tg.id, '');
  await page.keyboard.press('Meta+a');
  await page.waitForTimeout(250);
  await page.keyboard.press('Backspace');
  await page.waitForTimeout(1500);
  if (rec.baseline) {
    await page.keyboard.type(rec.baseline, { delay: 10 });
    await page.waitForTimeout(1200);
  }
  rec.restored = await promptOf(tg.id);
  out.results.push(rec);
  if (rec.changed) await shot(page, `M-307-${rec.kind}-翻译提示词之后.png`, { clip: { x: 0, y: 0, width: 1440, height: 810 } });
}

out.balance1 = await balance();
await writeFile(resolve(HERE, '.evidence/cf1-three-kinds.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({
  balance0: out.balance0, balance1: out.balance1,
  results: out.results.map((r) => ({ kind: r.kind, baseline: r.baseline, before: r.before, typedOk: r.typedOk, click: r.click,
    after: r.after, changed: r.changed, turnedChinese: r.turnedChinese, restored: r.restored, note: r.note })),
}, null, 2).slice(0, 3000));
await browser.close();
