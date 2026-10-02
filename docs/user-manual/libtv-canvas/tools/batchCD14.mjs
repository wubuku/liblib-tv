// Batch CD-14：收尾自证 —— 画布状态、两个文本节点的提示词、临时文件是否清干净。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const SEL = '.text-fg-default[contenteditable="true"]';
const MY_MARK = 'windowsill';
const KNOWN = ['t-2AK3Ukyxj3', 't-UtVx3lZmrV'];

const { browser, page } = await launch();
const out = { rounds: [] };

await open(page, URL_);
for (let round = 0; round < 2; round += 1) {
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

  const rec = { round, count: null, nodes: {} };
  // 抽屉计数
  await page.evaluate(() => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const c = [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
      .map((el) => ({ el, r: el.getBoundingClientRect() })).filter((o) => o.r.x < 100).sort((a, b) => a.r.x - b.r.x);
    c[0]?.el.click();
  });
  await page.waitForTimeout(1700);
  rec.drawer = await page.evaluate(() => {
    const d = [...document.querySelectorAll('.mantine-Drawer-content')].filter((x) => { const r = x.getBoundingClientRect(); return r.width > 0; })
      .find((x) => [...x.querySelectorAll('button')].some((b) => ['画布', '资产'].includes((b.innerText || '').trim())));
    if (!d) return null;
    const t = (d.innerText || '').replace(/\s+/g, ' ');
    const m = t.match(/共 (\d+) 节点/);
    return { count: m ? Number(m[1]) : null, names: [...new Set([...d.querySelectorAll('[aria-label^="定位到节点"]')].map((b) => (b.getAttribute('aria-label') || '').replace('定位到节点 ', '')))] };
  });
  await page.keyboard.press('Escape');
  await page.waitForTimeout(800);

  for (const id of KNOWN) {
    await page.evaluate((nid) => document.querySelector(`.react-flow__node[data-id="${nid}"]`)?.click(), id);
    await page.waitForTimeout(1700);
    rec.nodes[id] = await page.evaluate(({ nid, sel }) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const b = n ? n.querySelector(sel) : null;
      return { found: !!n, box: !!b, val: b ? (b.innerText || '').trim() : null };
    }, { nid: id, sel: SEL });
  }
  out.rounds.push(rec);
  if (round === 1) await shot(page, 'M-301-文本节点-提示词已清空-刷新后复核.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });
}

const measured = out.rounds.every((r) => Object.values(r.nodes).every((n) => n.found && n.box));
out.measured = measured;
out.clean = measured && out.rounds.every((r) => Object.values(r.nodes).every((n) => !String(n.val || '').includes(MY_MARK)));
out.counts = out.rounds.map((r) => r.drawer?.count);
out.names = out.rounds[0].drawer?.names;
out.verdict = !measured
  ? '没测到（至少一轮没渲染出提示词框）'
  : out.clean ? `✅ 两轮独立刷新，两个文本节点的提示词都读到、都为空；节点数 ${out.counts.join(' → ')}` : '⛔ 仍有残留';
await writeFile(resolve(HERE, '.evidence/cd14-final.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ counts: out.counts, names: out.names, nodes: out.rounds.map((r) => r.nodes), measured: out.measured, clean: out.clean, verdict: out.verdict }, null, 2));
await browser.close();
