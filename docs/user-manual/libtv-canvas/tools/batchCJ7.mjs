// Batch CJ-7：手册里关于 `⤢` 有**两处互相矛盾的记载**，先查清是不是两枚不同的按钮。
//
//   说法甲（create-nodes / 20-reference 的「无文字按钮」清单）：
//     参数卡片**右上角**那枚 `28×28` 的 `⤢` ⇒ 收起整张参数卡片
//   说法乙（20-reference「会员与积分」开头）：
//     「参数面板**参数条最右端**有一枚 `⤢` 展开图标按钮，**点它会跳到会员订阅页**」
//
// ⭐ 两者位置写的不一样（卡片右上角 vs 参数条最右端），尺寸也可能不同（28 vs 32）。
//    手册内部已经自相矛盾，正文必须给出裁决，否则用户按哪一条做都会困惑。
//
// 本步只读 DOM：把选中节点的参数区域里**所有**双向斜箭头按钮全部捞出来，
// 连 rect、class、所属容器一起打出来，看是**一枚**还是**两枚**。
// ⛔ 不点任何一枚（点收起那枚会改状态；点另一枚可能跳页）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

const { browser, page } = await launch();
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
await page.reload({ waitUntil: 'domcontentloaded' });
await page.waitForTimeout(6000);
await closePromos(page);
await page.waitForTimeout(1500);
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2600);
const d = page.locator('.mantine-Drawer-inner').first().locator('button[aria-label="关闭"]').first();
if (await d.count()) await d.click({ timeout: 6000 }).catch(() => {});
await page.waitForTimeout(1600);

// 先选一个视频节点
{
  const b = await page.locator('.react-flow__node[data-id="v-v2hlWY4Br3"]').boundingBox();
  await page.mouse.click(b.x + b.width / 2, b.y + b.height - 12);
  await page.waitForTimeout(1600);
}

const out = {};
out.双向斜箭头按钮 = await page.evaluate(() => {
  const rows = [];
  for (const b of document.querySelectorAll('button, [role="button"]')) {
    const r = b.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    const paths = [...b.querySelectorAll('path')].map((p) => (p.getAttribute('d') || ''));
    // 双向斜箭头的特征：路径里同时出现 L 折线（两个方向的箭头）
    const looks = paths.some((p) => /l-?[0-9.]+\s+[0-9.]+/.test(p) && p.length > 20) && paths.length <= 2;
    if (!looks) continue;
    // 更严格：把整页所有 28×28 / 32×32 按钮的 path 都打出来，人工认
    rows.push({
      尺寸: [Math.round(r.width), Math.round(r.height)],
      rect: [Math.round(r.x), Math.round(r.y)],
      aria: b.getAttribute('aria-label'),
      title: b.getAttribute('title'),
      文字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16),
      cls: (b.className || '').toString().slice(0, 96),
      path数: paths.length,
      path: paths.map((p) => p.slice(0, 52)),
      父容器cls: (b.parentElement?.className || '').toString().slice(0, 70),
    });
  }
  return rows;
});
console.log('════ 全页所有「像双向斜箭头」的按钮 ════');
for (const r of out.双向斜箭头按钮) {
  console.log(`  ${JSON.stringify(r.尺寸)} @${JSON.stringify(r.rect)} aria=${r.aria} 文字=${JSON.stringify(r.文字)}`);
  console.log(`    cls=${r.cls}`);
  for (const p of r.path) console.log(`    path=${p}`);
  console.log(`    父=${r.父容器cls}`);
}

// 目标节点的参数区域：列出所有 32×32 与 28×28 按钮，看参数条最右端有没有第二枚
out.目标节点按钮 = await page.evaluate(() => {
  const n = document.querySelector('.react-flow__node[data-id="v-v2hlWY4Br3"]');
  if (!n) return [];
  return [...n.querySelectorAll('button')].map((b) => {
    const r = b.getBoundingClientRect();
    return { 尺寸: [Math.round(r.width), Math.round(r.height)], rect: [Math.round(r.x), Math.round(r.y)], aria: b.getAttribute('aria-label'), 文字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12), cls: (b.className || '').toString().slice(0, 70) };
  }).filter((x) => x.尺寸[0] > 0);
});
console.log(`\n════ 视频节点里全部 ${out.目标节点按钮.length} 枚按钮 ════`);
for (const r of out.目标节点按钮) console.log(`  ${JSON.stringify(r.尺寸).padEnd(11)} @${JSON.stringify(r.rect).padEnd(18)} aria=${r.aria} ${JSON.stringify(r.文字)}`);

const sizes = {};
for (const r of out.目标节点按钮) { const k = r.尺寸.join('x'); sizes[k] = (sizes[k] || 0) + 1; }
console.log('\n尺寸分布 =', JSON.stringify(sizes));

await writeFile(resolve(HERE, '.evidence/cj7-collapse-vs-membership.json'), JSON.stringify(out, null, 2));
console.log('\n（本步只读：一枚都没点）');
await browser.close();
