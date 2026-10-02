// Batch CJ-3：① 把上一轮收起的卡片复原（收起用不用查才知道，**复原必须做**）；
//             ② 查 CG 遗留的「音频节点上 ⤢ 没反应」—— A 段已经证明**那枚按钮在音频节点上存在**，
//                所以要测的是「点了到底收没收」，不是「有没有」。
//
// ⭐ CJ-2 的三条硬结论：
//   · 收起后 **点一下节点标题就能恢复**（42 → 169，提示词框 false → true）
//   · 重新点节点本体 / `⌘0` / **刷新页面** 都**恢复不了**
//   · 收起**会存盘** —— 另一个全新浏览器会话读同一节点仍是折的（42）
//   ⇒ 顺带作废 CG 的一条：「两轮独立刷新都恢复展开」—— 刷新根本不恢复，
//      CG 当时量的是**另一个同名的视频节点**（正是 CG 自己记过的那个坑）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

const boot = async (page) => {
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
};

const read = (page, id) => page.evaluate((nid) => {
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
    有折叠钮: !!fold,
    折叠钮: fr ? [Math.round(fr.x), Math.round(fr.y)] : null,
    文字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
  };
}, id);

const { browser, page } = await launch();
await boot(page);

const out = {};

// ── ① 复原上一轮折掉的视频节点 ──────────────────────────────────
const VID = 'v-v2hlWY4Br3';
{
  let r = await read(page, VID);
  console.log('════ ① 复原 ════');
  console.log('  开局：', JSON.stringify(r));
  if (r.在 && !r.有提示词框) {
    const b = await page.locator(`.react-flow__node[data-id="${VID}"]`).boundingBox();
    await page.mouse.click(b.x + 46, b.y + 12);   // ② 点标题
    await page.waitForTimeout(1600);
    r = await read(page, VID);
    console.log('  点标题后：', JSON.stringify(r), r.有提示词框 ? '✅ 已复原' : '⛔ 还没复原');
  } else console.log('  已是展开态，无需复原');
  out.复原 = r;
}

// ── ② 音频节点上那枚 ⤢ 到底收不收 ──────────────────────────────
const AID = 'a-THmbuJXQj4';
{
  console.log('\n════ ② 音频节点 ════');
  const b = await page.locator(`.react-flow__node[data-id="${AID}"]`).boundingBox();
  await page.mouse.click(b.x + b.width / 2, b.y + b.height - 12);
  await page.waitForTimeout(1600);
  const before = await read(page, AID);
  console.log('  选中后：', JSON.stringify(before));
  if (!before.有折叠钮) { console.log('  ⛔ 音频节点上没有那枚 ⤢ ⇒「没反应」是因为按钮不存在'); out.音频 = { 结论: '按钮不存在' }; }
  else {
    await page.mouse.click(before.折叠钮[0] + 14, before.折叠钮[1] + 14);
    await page.waitForTimeout(1700);
    const after = await read(page, AID);
    const 收起了 = after.可见后代数 < before.可见后代数;
    console.log(`  点 ⤢ 后：可见后代 ${before.可见后代数} → ${after.可见后代数}  提示词框 ${before.有提示词框}→${after.有提示词框}  ${收起了 ? '✅ 收起了' : '⛔ 没反应'}`);
    out.音频 = { 前: before, 后: after, 收起了 };
    // 复原
    if (收起了) {
      const b2 = await page.locator(`.react-flow__node[data-id="${AID}"]`).boundingBox();
      await page.mouse.click(b2.x + 46, b2.y + 12);
      await page.waitForTimeout(1600);
      const rec = await read(page, AID);
      console.log('  复原后：', JSON.stringify(rec), rec.可见后代数 === before.可见后代数 ? '✅ 已复原' : '⚠️ 没复原');
      out.音频.复原 = rec;
    }
  }
}

// 顺带：图片 / 文本各点一次 ⤢，确认「点标题恢复」在三类上同样成立
for (const [名, id] of [['图片', 'i-sODTbgLUm1'], ['文本', 't-UtVx3lZmrV']]) {
  const b = await page.locator(`.react-flow__node[data-id="${id}"]`).boundingBox();
  await page.mouse.click(b.x + b.width / 2, b.y + b.height - 12);
  await page.waitForTimeout(1500);
  const before = await read(page, id);
  if (!before.有折叠钮) { console.log(`  ${名}节点：没有 ⤢`); continue; }
  await page.mouse.click(before.折叠钮[0] + 14, before.折叠钮[1] + 14);
  await page.waitForTimeout(1600);
  const mid = await read(page, id);
  const b2 = await page.locator(`.react-flow__node[data-id="${id}"]`).boundingBox();
  await page.mouse.click(b2.x + 46, b2.y + 12);
  await page.waitForTimeout(1600);
  const rec = await read(page, id);
  console.log(`  ${名}节点：展开 ${before.可见后代数} → 折 ${mid.可见后代数} → 点标题复原 ${rec.可见后代数}  ${rec.可见后代数 === before.可见后代数 ? '✅' : '⚠️'}`);
  out[名 + '节点'] = { 展开: before.可见后代数, 折: mid.可见后代数, 复原: rec.可见后代数 };
}

await writeFile(resolve(HERE, '.evidence/cj3-audio-and-restore.json'), JSON.stringify(out, null, 2));
console.log('\n（不扣积分、不点生成、不点取消）');
await browser.close();
