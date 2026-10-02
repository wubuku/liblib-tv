// Batch CL-3：删掉本轮自己造出来的两个节点，并逐项复核。
//
// 两个都是广场那一侧点出来的「素材-风格」节点，判定依据**不是**名字，是
//   ① `data-id` **不在** 11 个基线 id 里；
//   ② `data-id` 以 `m-` 开头（`素材-特效` / `素材-风格` 专用的前缀）；
//   ③ 名字以 `素材-` 开头。
// 三条同时成立才删 ⇒ **用户原有的 11 个节点一个都不碰**。
// 删完按 **id 集合**与基线比对，再用**另一个全新浏览器会话**复核。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];
const STRAY = ['m-0J5UTXY01T', 'm-960UpeLtZz'];

const boot = async (page) => {
  await open(page, URL_);
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2600);
  for (let i = 0; i < 3; i += 1) {
    const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
    if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(600);
  }
};
const ids = (page) => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));

const out = {};
const { browser, page } = await launch();
await boot(page);
out.删前 = await ids(page);
console.log('删前 =', JSON.stringify(out.删前));

await page.locator('button[aria-label="资产管理"]').first().click({ timeout: 8000 }).catch(() => {});
await page.waitForTimeout(2000);

for (const stray of STRAY) {
  {
    const still = await ids(page);
    if (!still.includes(stray)) { console.log(`  ${stray} 已经不在，跳过`); continue; }
    // 抽屉里按名字找到那一行（两个同名行，逐行删到 id 消失为止）
    for (let round = 0; round < 3; round += 1) {
      const row = page.locator('button[aria-label^="定位到节点 素材-风格"]').first();
      if (!(await row.count())) break;
      const rb = await row.boundingBox().catch(() => null);
      if (!rb) break;
      await page.mouse.move(rb.x + rb.width / 2, rb.y + rb.height / 2);
      await page.waitForTimeout(1000);
      const mo = page.locator('button[aria-label="更多操作"]').first();
      if (!(await mo.count())) break;
      await mo.click({ timeout: 6000 }).catch(() => {});
      await page.waitForTimeout(1100);
      const del = page.locator('[role="menuitem"]:has-text("删除"), button:has-text("删除")').last();
      if (await del.count()) { await del.click({ timeout: 6000 }).catch(() => {}); await page.waitForTimeout(1800); }
      const now = await ids(page);
      if (!now.includes(stray)) { console.log(`  ✅ 已删 ${stray}`); break; }
      console.log(`  ${stray} 仍在，再来一轮`);
    }
  }
}
await page.keyboard.press('Escape').catch(() => {});
for (let i = 0; i < 3; i += 1) {
  const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
  if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(600);
}
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2600);

out.删后 = await ids(page);
out.一致 = out.删后.length === BASE.length && BASE.every((x) => out.删后.includes(x)) && !out.删后.some((x) => STRAY.includes(x));
console.log('\n删后 =', JSON.stringify(out.删后));
console.log('与基线 11 个逐项一致 =', out.一致);
await browser.close();

{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  out.全新会话 = await ids(p2);
  out.全新会话一致 = out.全新会话.length === BASE.length && BASE.every((x) => out.全新会话.includes(x));
  console.log('全新会话 =', JSON.stringify(out.全新会话), ' 一致 =', out.全新会话一致);
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cl3-delete.json'), JSON.stringify(out, null, 2));
console.log('\n只删了本轮自己造出来的两个节点');
