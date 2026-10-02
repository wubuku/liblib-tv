// Batch CJ-4：把「点标题恢复」在**图片 / 文本**上也测干净。
//
// CJ-3 的两处污染，必须先认下来：
//   · 「图片节点复原失败」不可信 —— 点标题用的是 `b.x+46, b.y+12`，
//     但**没有先断言这一步之后节点处于选中态**。⭐ CG 早就记过：
//     图片/文本节点收起走的是「按钮消失」那条分支，**收起后多半已失去选中态**，
//     那么第一次点标题只是「选中」，要第二次才展开。CJ-3 没区分这两种情况。
//   · 「文本节点没有 ⤢」更不可信 —— 它是**最后一个**测的，⤢ 压根没挂载（没选中）。
//
// 本步逐个节点独立闭环：**选中 → 断言选中 → 折 → 断言折了 →
// 点标题一次 → 读；不够再点一次 → 读；再不够就如实记「两次都不行」**。
// ⛔ 不扣积分、不点生成、不点取消。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

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

const read = (id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { 在: false };
  const vis = [...n.querySelectorAll('*')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  const fold = [...n.querySelectorAll('button')].find((b) => {
    const c = b.className.toString();
    return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2');
  });
  const fr = fold ? fold.getBoundingClientRect() : null;
  return {
    在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length,
    有提示词框: !!n.querySelector('textarea,[contenteditable="true"]'),
    折叠钮: fr ? [Math.round(fr.x), Math.round(fr.y)] : null,
  };
}, id);

const clickTitle = async (id) => {
  const b = await page.locator(`.react-flow__node[data-id="${id}"]`).boundingBox();
  await page.mouse.click(b.x + 46, b.y + 12);
  await page.waitForTimeout(1600);
};

for (const [名, id] of [['图片', 'i-sODTbgLUm1'], ['文本', 't-UtVx3lZmrV'], ['视频', 'v-v2hlWY4Br3']]) {
  console.log(`\n════ ${名}节点 ${id} ════`);
  const rec = {};
  // ① 选中并硬断言
  {
    const b = await page.locator(`.react-flow__node[data-id="${id}"]`).boundingBox();
    await page.mouse.click(b.x + b.width / 2, b.y + b.height - 12);
    await page.waitForTimeout(1600);
  }
  const sel = await read(id);
  console.log('  选中后:', JSON.stringify(sel));
  if (!sel.在 || !sel.选中 || !sel.折叠钮) { console.log('  ⛔ 硬前置不满足（没选中 / 没 ⤢）⇒ 本节点本轮「没测到」'); out[名] = { 前置不满足: true, sel }; continue; }

  // ② 折
  await page.mouse.click(sel.折叠钮[0] + 14, sel.折叠钮[1] + 14);
  await page.waitForTimeout(1700);
  const folded = await read(id);
  console.log('  折后:  ', JSON.stringify(folded));
  if (!folded.在 || folded.可见后代数 >= sel.可见后代数) { console.log('  ⛔ 没折下去 ⇒ 本节点本轮「没测到」'); out[名] = { 没折下去: true, sel, folded }; continue; }

  // ③ 点标题一次
  await clickTitle(id);
  const once = await read(id);
  console.log('  点标题第 1 次:', JSON.stringify(once));
  rec.点一次 = once;

  // ④ 不够再点一次
  let twice = null;
  if (!once.有提示词框) {
    await clickTitle(id);
    twice = await read(id);
    console.log('  点标题第 2 次:', JSON.stringify(twice));
    rec.点两次 = twice;
  }

  const 复原值 = (twice || once).可见后代数;
  console.log(`  ⇒ 复原判定：展开 ${sel.可见后代数} / 折 ${folded.可见后代数} / 复原 ${复原值} ${复原值 === sel.可见后代数 ? '✅' : '⚠️ 没复原'}`);

  // 收尾：确保展开
  const fin = await read(id);
  if (!fin.有提示词框) { await clickTitle(id); }
  const fin2 = await read(id);
  console.log('  收尾:', JSON.stringify(fin2));
  out[名] = { 展开: sel, 折后: folded, 恢复: rec, 收尾: fin2 };
}

await writeFile(resolve(HERE, '.evidence/cj4-title-restore.json'), JSON.stringify(out, null, 2));
console.log('\n（不扣积分、不点生成、不点取消）');
await browser.close();
