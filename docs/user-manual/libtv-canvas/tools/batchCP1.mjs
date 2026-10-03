// Batch CP-1：修我自己造成的损伤 —— CP-0 的「空白处拖拽」把节点 a-THmbuJXQj4 挪了 1px。
//
// ⛔ 先核实再动手：全新会话按 `⌘0` 读全部节点矩形，和已知基线逐项比。
//    ⭐ 注意：**id 一致不代表位置一致** —— CP-0 的全新会话检查只比了 id，所以没发现。
// 若确实偏了 1px：先试 `⌘Z` 撤销（手册记过 `⌘Z` / `⌘⇧Z` 是可用的），
// 撤销后**再读一次**确认；撤不掉就如实报告，绝不再用拖拽去"修"（拖本身就是写盘）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
// `⌘0` 适合屏幕之后的已知基线（来自 CM-4 / CM-5 / CO-0 的读数）
const 基线 = {
  'a-CUfJfmKzUJ': [319, 554, 164, 164],
  'a-THmbuJXQj4': [99, 69, 164, 164],
  'b-mfkcQNULC3': [1208, 36, 150, 182],
  'i-9nlG6HdjK2': [82, 317, 292, 164],
  'i-sODTbgLUm1': [831, 317, 292, 164],
  'n-56F19pXVB4': [335, 69, 164, 164],
  't-2AK3Ukyxj3': [217, 610, 164, 164],
  't-UtVx3lZmrV': [1191, 317, 164, 164],
  'v-eMpqKtiLlx': [471, 317, 292, 164],
  'v-oZNpH99MtM': [971, 36, 164, 164],
  'v-v2hlWY4Br3': [583, 36, 292, 164],
};

const boot = async (page) => {
  await open(page, URL_);
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2800);
  for (let i = 0; i < 3; i += 1) {
    const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
    if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(600);
  }
};
const rects = (page) => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}));

const out = {};
const { browser, page } = await launch();
await boot(page);
const 第一次 = await rects(page);
out.第一次 = 第一次;
const 差 = [];
for (const n of 第一次) {
  const b = 基线[n.id];
  if (!b) { 差.push({ id: n.id, 注: '基线里没有这个 id' }); continue; }
  if (n.rect.join() !== b.join()) 差.push({ id: n.id, 现在: n.rect, 基线: b, 差: n.rect.map((v, i) => v - b[i]) });
}
const 缺 = Object.keys(基线).filter((k) => !第一次.some((n) => n.id === k));
out.核实 = { 读数节点数: 第一次.length, 缺失: 缺, 偏移: 差 };
console.log('=== 核实（全新会话，⌘0 之后）===');
console.log('  读到的节点数 =', 第一次.length, ' 基线 11 个');
console.log('  缺失 =', JSON.stringify(缺));
console.log('  位置偏移 =', JSON.stringify(差, null, 0));
if (!差.length && !缺.length) { console.log('  ⭐ 位置完好，CP-0 那 1px 没有存盘（或已被别的读数吸收）。不需要修复'); }

if (差.length) {
  console.log('\n=== 试 ⌘Z 撤销 ===');
  for (let i = 0; i < 3; i += 1) {
    await page.evaluate(() => document.body.focus());
    await page.keyboard.press('Meta+z');
    await page.waitForTimeout(1400);
    await page.keyboard.press('Meta+0');
    await page.waitForTimeout(2400);
    const r = await rects(page);
    const 仍差 = [];
    for (const n of r) { const b = 基线[n.id]; if (b && n.rect.join() !== b.join()) 仍差.push({ id: n.id, 现在: n.rect, 基线: b }); }
    console.log(`  第 ${i + 1} 次 ⌘Z 之后 仍偏移 ${仍差.length} 处：${JSON.stringify(仍差)}`);
    if (!仍差.length) { out.撤销成功 = { 次: i + 1 }; break; }
    if (i === 0) { out.撤销成功 = { 次: 0 }; }
  }
  const 末 = await rects(page);
  out.末态 = 末;
  const 末差 = 末.filter((n) => 基线[n.id] && n.rect.join() !== 基线[n.id].join()).map((n) => ({ id: n.id, 现在: n.rect, 基线: 基线[n.id] }));
  out.末态偏移 = 末差;
  console.log('\n  最终仍偏移 =', JSON.stringify(末差));
  out.修好了 = 末差.length === 0;
}

await browser.close();
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const r2 = await rects(p2);
  const 差2 = r2.filter((n) => 基线[n.id] && n.rect.join() !== 基线[n.id].join()).map((n) => ({ id: n.id, 现在: n.rect, 基线: 基线[n.id] }));
  out.全新会话复核 = { 节点数: r2.length, 偏移: 差2, 完好: r2.length === 11 && 差2.length === 0 };
  console.log('\n=== 全新会话复核 ===');
  console.log('  节点数 =', r2.length, ' 偏移 =', JSON.stringify(差2), ' ⭐ 完好 =', out.全新会话复核.完好);
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cp1-repair.json'), JSON.stringify(out, null, 2));
