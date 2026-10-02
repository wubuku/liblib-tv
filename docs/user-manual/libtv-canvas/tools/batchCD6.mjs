// Batch CD-6：把「清空是否真的落盘」**真正复核一遍**。
// CD-5 的 recheck 读到 `null` —— 那不是「干净」，那是**没选中所以框没渲染**。
// ⭐⭐ **判据不出数的时候，输出必须是「没测到」，不能顺手当成「通过」。**
// 这一步：刷新 → ⌘0 → 逐个文本节点**点开** → 读它的提示词原文。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MY_MARK = 'windowsill';
const SEL = '.text-fg-default[contenteditable="true"]';
const KNOWN = ['t-2AK3Ukyxj3', 't-UtVx3lZmrV'];

const { browser, page } = await launch();
const out = { rounds: [] };

const settle = async () => {
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
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2200);
};

const readOne = (id) => page.evaluate(({ nid, sel }) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { found: false, why: '节点不在 DOM 里（可能在视口外）' };
  const r = n.getBoundingClientRect();
  const boxes = [...n.querySelectorAll(sel)];
  return {
    found: true,
    nodeVis: r.width > 0 && r.height > 0,
    selected: n.className.includes('selected'),
    boxCount: boxes.length,
    val: boxes.length ? (boxes[0].innerText || '').trim().slice(0, 140) : null,
  };
}, { nid: id, sel: SEL });

// 连做两轮「刷新 → 逐个点开读」，两轮都空才算落盘清掉了
for (let round = 0; round < 2; round += 1) {
  await open(page, URL_);
  await settle();
  const rec = { round, nodes: {} };
  for (const id of KNOWN) {
    // 先用中键平移把它挪进视口，再点
    await page.evaluate((nid) => document.querySelector(`.react-flow__node[data-id="${nid}"]`)?.click(), id);
    await page.waitForTimeout(1700);
    const r1 = await readOne(id);
    if (r1.found && r1.boxCount === 0) {
      // 没渲染出框 → 多半是点不中（不在视口），先平移再点
      const b = await page.evaluate((nid) => {
        const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
        if (!n) return null;
        const r = n.getBoundingClientRect();
        return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
      }, id);
      if (b) {
        const cx = Math.min(1200, Math.max(200, b[0] + b[2] / 2));
        const cy = Math.min(700, Math.max(150, b[1] + b[3] / 2));
        await page.mouse.move(cx, cy, { steps: 6 });
        await page.mouse.click(cx, cy);
        await page.waitForTimeout(1700);
      }
    }
    rec.nodes[id] = await readOne(id);
  }
  out.rounds.push(rec);
  await shot(page, round === 1 ? 'M-301-文本节点-提示词已清空-刷新后复核.png' : 'M-301-文本节点-提示词已清空.png',
    { clip: { x: 0, y: 0, width: 1440, height: 810 } });
}

// ⭐ 结论只在「两轮都读到框、且两轮都是空」时才成立
const measured = out.rounds.every((r) => Object.values(r.nodes).every((n) => n.found && n.boxCount > 0));
out.measured = measured;
out.verdict = measured
  ? (out.rounds.every((r) => Object.values(r.nodes).every((n) => !String(n.val || '').includes(MY_MARK)))
      ? '两轮都读到框、都是空 —— 确认已落盘清空'
      : '⛔ 仍然有我打的字')
  : '没测到（至少一轮没渲染出提示词框，不下结论）';
await writeFile(resolve(HERE, '.evidence/cd6-verify.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 2).slice(0, 3000));
await browser.close();
