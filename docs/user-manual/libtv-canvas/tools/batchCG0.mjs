// Batch CG-0：认领那枚「四类节点都有、但一直没有名字」的按钮。
//
// CF-0 的按钮身份证表里留下一行没查清：
//   `M1.4 8.9c.22 0 .4.18.4.4v5.54l5.26-5.26a.4.4 0` —— 四类节点都有，`disabled` 全是 false。
// 它排在 DOM 最后一位，而生成按钮（`M8.3.3a1 1 0 0 1 1.4 0l8 8…`）在它前面。
// ⛔ 如果它是「删除」之类，这一步就只能**读，不能点**。
//
// 所以本步只做两件**零风险**的事：
//   ① 悬停认名字（**带阳性对照**：先 hover 一枚名字早已坐实的 `M15.52`）；
//   ② 读它在参数条上的**位置关系**（在生成按钮左边还是右边、中间隔几枚）。
// 认出名字之后，才由下一步决定**要不要点**。
//
// ⚠️ 三条纪律：
//   ① `⌘0` 收全画布 → 点选 → **断言选中**，不满足就直接退出（缺陷 78 的治法）；
//   ② 悬停前先把鼠标挪到 (5,5)，再挪到目标、再挪 1px 逼出 mouseenter；
//   ③ tooltip 用「悬停前 / 悬停后**新增**了哪些气泡」来判定，避免读到页面上常驻的气泡。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MYSTERY = 'M1.4 8.9c.22 0 .4.18.4.4v5.54l5.26-5.26a.4.4 0';
const CONTROL = 'M15.52 7.2c.16 0 .31.1.37.26l3.8 10';
const GEN = 'M8.3.3a1 1 0 0 1 1.4 0l8 8';
const NODES = [
  { id: 'v-eMpqKtiLlx', kind: '视频节点 3' },
  { id: 'i-9nlG6HdjK2', kind: '图片节点 2' },
  { id: 'a-CUfJfmKzUJ', kind: '音频节点 6' },
  { id: 't-2AK3Ukyxj3', kind: '文本节点 1' },
];

const { browser, page } = await launch();
const out = { rows: [] };

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

// 读一个节点参数条上所有「无文字的图标按钮」，按屏幕 x 排好序
const readIcons = (nid) => page.evaluate(({ n, pre, gen }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return { err: 'node not in DOM' };
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const items = [];
  for (const b of [...node.querySelectorAll('button,[role="button"]')].filter(vis)) {
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (!d) continue;
    const r = b.getBoundingClientRect();
    const t = (b.innerText || '').trim();
    items.push({
      text: t.slice(0, 12), aria: b.getAttribute('aria-label'), disabled: b.disabled === true,
      x: Math.round(r.x), cx: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
      w: Math.round(r.width), h: Math.round(r.height),
      which: d.includes(pre) ? 'MYSTERY' : d.includes(gen) ? 'GEN' : d.includes('M15.52') ? 'TRANSLATE' : 'other',
      head: d.slice(0, 30),
    });
  }
  items.sort((a, b) => a.x - b.x);
  const mi = items.findIndex((x) => x.which === 'MYSTERY');
  const gi = items.findIndex((x) => x.which === 'GEN');
  return {
    items,
    // 它在生成按钮的哪一侧、中间隔几枚
    相对生成按钮: mi >= 0 && gi >= 0 ? (mi < gi ? `在生成按钮左边，中间隔 ${gi - mi - 1} 枚` : `在生成按钮右边，中间隔 ${mi - gi - 1} 枚`) : '位置关系读不到',
    它本身: mi >= 0 ? items[mi] : null,
    生成按钮: gi >= 0 ? items[gi] : null,
  };
}, { n: nid, pre: MYSTERY, gen: GEN });

const readTips = () => page.evaluate(() => {
  const grab = (sel) => [...document.querySelectorAll(sel)]
    .map((e) => (e.innerText || e.textContent || '').trim()).filter((t) => t && t.length < 60);
  return { role: grab('[role="tooltip"]'), mantine: grab('[class*="Tooltip"]') };
});

for (const nd of NODES) {
  const rec = { kind: nd.kind, id: nd.id };
  // 硬前置：收全 → 选中 → 断言
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2200);
  await page.evaluate((n) => document.querySelector(`.react-flow__node[data-id="${n}"]`)?.click(), nd.id);
  await page.waitForTimeout(1900);
  rec.sel = await page.evaluate((n) => {
    const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
    return { inDom: !!el, selected: !!el && el.className.includes('selected') };
  }, nd.id);
  if (!rec.sel.inDom || !rec.sel.selected) { rec.abort = '没选中，本行读数一律作废'; out.rows.push(rec); continue; }

  rec.bar = await readIcons(nd.id);
  // 悬停它，认名字
  if (rec.bar.它本身) {
    await page.mouse.move(5, 5);
    await page.waitForTimeout(400);
    const b0 = await readTips();
    await page.mouse.move(rec.bar.它本身.cx, rec.bar.它本身.y);
    await page.waitForTimeout(1300);
    await page.mouse.move(rec.bar.它本身.cx + 1, rec.bar.它本身.y);
    await page.waitForTimeout(1100);
    const b1 = await readTips();
    rec.悬停新增气泡 = b1.role.filter((t) => !b0.role.includes(t)).concat(b1.mantine.filter((t) => !b0.mantine.includes(t)));
  }
  out.rows.push(rec);
}

// 阳性对照：拿一个**名字早已坐实**的节点（视频）上的 `M15.52` 走同一套悬停
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2000);
await page.evaluate((n) => document.querySelector(`.react-flow__node[data-id="${n}"]`)?.click(), 'v-eMpqKtiLlx');
await page.waitForTimeout(1900);
const ctl = await page.evaluate((n) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  for (const b of [...node.querySelectorAll('button,[role="button"]')].filter(vis)) {
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (d.includes('M15.52')) { const r = b.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }
  }
  return null;
}, 'v-eMpqKtiLlx');
if (ctl) {
  await page.mouse.move(5, 5);
  await page.waitForTimeout(400);
  const c0 = await readTips();
  await page.mouse.move(ctl.cx, ctl.y);
  await page.waitForTimeout(1300);
  await page.mouse.move(ctl.cx + 1, ctl.y);
  await page.waitForTimeout(1100);
  const c1 = await readTips();
  out.control = {
    悬停目标: 'M15.52（名字早已坐实）',
    悬停新增气泡: c1.role.filter((t) => !c0.role.includes(t)).concat(c1.mantine.filter((t) => !c0.mantine.includes(t))),
  };
} else {
  out.control = { err: '没找到对照按钮' };
}

out.balance = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const t = [...document.querySelectorAll('header *,nav *')].filter(vis).map((e) => (e.innerText || '').trim()).filter((x) => /^\d{1,4}$/.test(x));
  return t.length ? Number(t[t.length - 1]) : null;
});

await writeFile(resolve(HERE, '.evidence/cg0-mystery-button.json'), JSON.stringify(out, null, 2));
for (const r of out.rows) {
  console.log(`\n=== ${r.kind} (${r.id}) sel=${JSON.stringify(r.sel)} ${r.abort || ''}`);
  if (!r.bar || r.bar.err) { console.log('   ', r.bar); continue; }
  console.log('   相对生成按钮:', r.bar.相对生成按钮);
  console.log('   它本身:', JSON.stringify(r.bar.它本身));
  console.log('   生成按钮:', JSON.stringify(r.bar.生成按钮));
  console.log('   悬停新增气泡:', JSON.stringify(r.悬停新增气泡));
  console.log('   参数条图标按钮（按 x 排）:');
  for (const it of r.bar.items) console.log(`      x=${it.x} y=${it.y} ${it.w}x${it.h} dis=${it.disabled} [${it.which}] "${it.text}" ${it.head}`);
}
console.log('\n=== 阳性对照 ===');
console.log(JSON.stringify(out.control));
console.log('balance =', out.balance);
await browser.close();
