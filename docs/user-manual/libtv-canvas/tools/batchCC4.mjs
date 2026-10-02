// Batch CC-4：给「点卡片本身会发生什么」配一个**可逆对照**。
//   点第 1 次 → 「全部适配模型」面板出现？卡片数变了吗？
//   点第 2 次（同一张、同一位置）→ 面板消失？回到原样吗？
//   ⭐ 阳性与阴性用**完全相同的动作**，只让「之前点过没有」这一个变量变。
// 另外弄清：特效卡上到底有几枚按钮（风格卡有 ⤢ 详情，特效卡有吗？）
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
const out = { nodes0: await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id'))) };

await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.waitForTimeout(700);
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...document.querySelectorAll('[aria-label="素材库"]')].filter(vis)[0]?.click();
});
await page.waitForTimeout(1700);
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const hit = [...document.querySelectorAll('*')].filter((e) => vis(e) && (e.innerText || '').trim() === '特效库');
  let el = hit[hit.length - 1];
  let btn = null;
  for (let i = 0; i < 5 && el && !btn; i += 1) { if (el.tagName === 'BUTTON' || el.getAttribute('role') === 'button') btn = el; el = el.parentElement; }
  (btn || hit[hit.length - 1]?.parentElement)?.click();
});
await page.waitForTimeout(2800);

const snap = () => page.evaluate(() => {
  const m = [...document.querySelectorAll('.mantine-Modal-content')].find((el) => (el.innerText || '').includes('特效广场'));
  if (!m) return { err: '广场没了' };
  const cards = [...m.querySelectorAll('div')].filter((el) => {
    const c = el.className?.toString?.() || '';
    return /rounded-xl/.test(c) && /flex-col/.test(c) && /p-2/.test(c);
  });
  const t = (m.innerText || '').replace(/\s+/g, ' ');
  return {
    cardCount: cards.length,
    firstName: cards[0] ? (cards[0].innerText || '').replace(/\s+/g, ' ').slice(0, 40) : null,
    hasModelPanel: t.includes('全部适配模型'),
    modelPanel: t.includes('全部适配模型') ? (t.slice(t.indexOf('全部适配模型'), t.indexOf('全部适配模型') + 60)) : null,
    // 特效卡上到底有几枚按钮、各自的 aria
    cardButtons: cards[0] ? [...cards[0].querySelectorAll('button,[role="button"]')].map((b) => {
      const r = b.getBoundingClientRect();
      return { aria: b.getAttribute('aria-label'), text: (b.innerText || '').trim().slice(0, 8), box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    }) : [],
    nodes: [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')),
  };
});

out.t0_baseline = await snap();
const box = out.t0_baseline.cardButtons.length ? null : null;
const cb = await page.evaluate(() => {
  const m = [...document.querySelectorAll('.mantine-Modal-content')].find((el) => (el.innerText || '').includes('特效广场'));
  const cards = [...m.querySelectorAll('div')].filter((el) => {
    const c = el.className?.toString?.() || '';
    return /rounded-xl/.test(c) && /flex-col/.test(c) && /p-2/.test(c);
  });
  const r = cards[0].getBoundingClientRect();
  return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
});
out.cardBox = cb;
const cx = cb[0] + cb[2] / 2;
const cy = cb[1] + cb[3] / 2;

// 第 1 次点
await page.mouse.move(cx, cy, { steps: 8 });
await page.waitForTimeout(600);
await page.mouse.click(cx, cy);
await page.waitForTimeout(2000);
out.t1_after1st = await snap();
await shot(page, 'M-297-特效卡片-点开适配模型.png', { clip: { x: 100, y: 79, width: 800, height: 460 } });

// 移开鼠标 —— 面板是「点出来的」还是「悬停出来的」，靠这一步分开
await page.mouse.move(1300, 700, { steps: 12 });
await page.waitForTimeout(1500);
out.t2_mouseAway = await snap();

// 第 2 次点（同一张、同一位置）
await page.mouse.move(cx, cy, { steps: 8 });
await page.waitForTimeout(600);
await page.mouse.click(cx, cy);
await page.waitForTimeout(2000);
out.t3_after2nd = await snap();
await shot(page, 'M-298-特效卡片-再点一次.png', { clip: { x: 100, y: 79, width: 800, height: 460 } });

out.nodesUnchanged = JSON.stringify(out.t3_after2nd.nodes) === JSON.stringify(out.nodes0);
out.nodes1 = JSON.stringify(out.t1_after1st.nodes) === JSON.stringify(out.nodes0);

await writeFile(resolve(HERE, '.evidence/cc4-toggle.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({
  t0: { cardCount: out.t0_baseline.cardCount, hasModelPanel: out.t0_baseline.hasModelPanel, cardButtons: out.t0_baseline.cardButtons },
  t1: { cardCount: out.t1_after1st.cardCount, hasModelPanel: out.t1_after1st.hasModelPanel, modelPanel: out.t1_after1st.modelPanel },
  t2_mouseAway: { hasModelPanel: out.t2_mouseAway.hasModelPanel },
  t3: { cardCount: out.t3_after2nd.cardCount, hasModelPanel: out.t3_after2nd.hasModelPanel, modelPanel: out.t3_after2nd.modelPanel },
  nodesUnchanged: out.nodesUnchanged, nodesAfter1st: out.nodes1,
}, null, 2));
await browser.close();
