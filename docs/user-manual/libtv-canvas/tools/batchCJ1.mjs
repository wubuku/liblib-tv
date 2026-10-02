// Batch CJ-1：CJ-0 扑空，根因查出来了 —— **`⤢` 被 TV Director 抽屉盖住了**。
//
// CJ-0 的读数：点完 `⤢` 前后，目标节点可见后代数 `169 → 169`，**判据无分辨力**。
// 差别不在判据，在几何：
//   · `v-v2hlWY4Br3` 节点本体 `[583,36,292×164]`
//   · 那枚 `⤢` 在 `[1022, 217, 28×28]`，class `… absolute right-2 top-2 z-10 flex size-7 …`
//     —— 它挂在**参数卡（660 宽）**的右上角，不在节点本体上
//   · 而 **TV Director 抽屉是 `[1024, 154, 400×640]`** ⇦ **把按钮整个压住了**
//
// ⭐ 这本身是一条手册该写的事：**抽屉开着时，靠右的节点参数卡会被盖住，卡上的 `⤢` 点不到。**
//
// 本步三件事：
//   ① 用 `elementFromPoint` **坐实**遮挡（阳性对照：换一个没被盖住的 `⤢`，落点应当是它自己）；
//   ② 收起抽屉，重跑 CJ-0 的 6 条恢复路径；
//   ③ 顺带查 CG 遗留的另一半：**音频节点上 `⤢` 为何没反应** ——
//      先看四类节点里那枚 `size-7` 按钮**到底在不在**（在不在，比「点了没反应」更根本）。
// ⛔ 折卡片不扣积分不落盘；不点生成、不点「取消」。
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

// ── ① 遮挡坐实 + 阳性对照 ───────────────────────────────────────
out.遮挡 = await page.evaluate(() => {
  const rows = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const id = n.getAttribute('data-id');
    const btn = [...n.querySelectorAll('button')].find((b) => {
      const c = b.className.toString();
      return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2');
    });
    if (!btn) { rows.push({ id, 有折叠钮: false }); continue; }
    const r = btn.getBoundingClientRect();
    const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
    const hit = document.elementFromPoint(cx, cy);
    const stack = document.elementsFromPoint(cx, cy).slice(0, 3).map((e) => `${e.tagName.toLowerCase()}.${(e.className || '').toString().slice(0, 30)}`);
    const drawer = [...document.querySelectorAll('.mantine-Drawer-inner')].find((d) => d.getBoundingClientRect().width > 0);
    const dr = drawer ? drawer.getBoundingClientRect() : null;
    rows.push({
      id, 有折叠钮: true,
      按钮rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      落点是不是它自己: hit === btn,
      落点栈: stack,
      抽屉rect: dr ? [Math.round(dr.x), Math.round(dr.y), Math.round(dr.width), Math.round(dr.height)] : null,
      被抽屉压住: dr ? !(r.right < dr.left || r.left > dr.right || r.bottom < dr.top || r.top > dr.bottom) : false,
    });
  }
  return rows;
});
console.log('════ 折叠钮与落点 ════');
for (const r of out.遮挡) {
  if (!r.有折叠钮) { console.log(`  ${r.id.padEnd(18)} ⛔ 节点里没有那枚 ⤢`); continue; }
  console.log(`  ${r.id.padEnd(18)} 按钮@${JSON.stringify(r.按钮rect)} 落点是它自己=${r.落点是不是它自己} 被抽屉压住=${r.被抽屉压住}`);
  if (!r.落点是不是它自己) console.log(`        落点栈=${JSON.stringify(r.落点栈)}`);
}
console.log('  抽屉 =', JSON.stringify(out.遮挡.find((r) => r.抽屉rect)?.抽屉rect));

// ── ③ 音频节点的 ⤢ 到底在不在（先答这个，它决定后面怎么试）─────
out.各类型有无折叠钮 = {};
for (const r of out.遮挡) {
  const k = r.id.split('-')[0];
  out.各类型有无折叠钮[k] = out.各类型有无折叠钮[k] || [];
  out.各类型有无折叠钮[k].push(r.有折叠钮);
}
console.log('\n════ 按类型前缀统计「那枚 ⤢ 在不在」════');
console.log('  ' + JSON.stringify(Object.fromEntries(Object.entries(out.各类型有无折叠钮).map(([k, v]) => [k, `${v.filter(Boolean).length}/${v.length}`]))));

// ── ② 收起抽屉，重跑恢复路径 ────────────────────────────────────
console.log('\n════ 收起 TV Director 抽屉 ════');
const drawerBtn = page.locator('.mantine-Drawer-inner').first().locator('button[aria-label="关闭"]').first();
const had = await drawerBtn.count();
if (had) await drawerBtn.click({ timeout: 6000 }).catch(() => {});
await page.waitForTimeout(1800);
out.抽屉已收起 = await page.evaluate(() => ![...document.querySelectorAll('.mantine-Drawer-inner')].some((d) => d.getBoundingClientRect().width > 0));
console.log('  抽屉可见 =', !out.抽屉已收起, '（false 才对）');

// 重选目标节点并复测落点
const TID = 'v-v2hlWY4Br3';
const box = await page.locator(`.react-flow__node[data-id="${TID}"]`).boundingBox();
await page.mouse.click(box.x + box.width / 2, box.y + box.height - 12);
await page.waitForTimeout(1400);

const state = () => page.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!n) return { 在: false };
  const vis = [...n.querySelectorAll('*')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  const card = [...n.querySelectorAll('*')].map((e) => e.getBoundingClientRect())
    .filter((r) => r.width > 200 && r.height > 80).sort((a, b) => (b.width * b.height) - (a.width * a.height))[0];
  const r = n.getBoundingClientRect();
  return { 在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length, 节点尺寸: [Math.round(r.width), Math.round(r.height)], 最大浮层: card ? [Math.round(card.width), Math.round(card.height)] : null, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]') };
}, TID);

const fold = async () => page.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  const btn = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
  if (!btn) return null;
  const r = btn.getBoundingClientRect();
  return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
}, TID);

out.基线 = await state();
const f = await fold();
console.log('基线 =', JSON.stringify(out.基线), ' ⤢@', JSON.stringify(f));
await page.mouse.click(f[0] + 14, f[1] + 14);
await page.waitForTimeout(1600);
out.折叠后 = await state();
console.log('折叠后 =', JSON.stringify(out.折叠后));
out.判据有分辨力 = out.基线.可见后代数 !== out.折叠后.可见后代数;
console.log('判据分辨力 =', out.判据有分辨力);
if (!out.判据有分辨力) { console.log('仍无分辨力 ⇒ 后面不跑了，输出只能是「没测到」'); await writeFile(resolve(HERE, '.evidence/cj1-drawer-occlusion.json'), JSON.stringify(out, null, 2)); await browser.close(); process.exit(0); }

const 恢复 = async (name, act) => {
  const before = await state();
  await act();
  await page.waitForTimeout(1600);
  const after = await state();
  const ok = after.在 && after.可见后代数 > before.可见后代数;
  console.log(`  ${ok ? '✅' : '⛔'} ${name.padEnd(22)} ${before.可见后代数} → ${after.可见后代数}  浮层=${JSON.stringify(after.最大浮层)}`);
  return { 路径: name, 恢复了: ok, 前: before, 后: after };
};
out.恢复路径 = [];
out.恢复路径.push(await 恢复('① 重新点一下节点', async () => {
  const b = await page.locator(`.react-flow__node[data-id="${TID}"]`).boundingBox();
  await page.mouse.click(b.x + b.width / 2, b.y + b.height - 12);
}));
out.恢复路径.push(await 恢复('② 点节点标题', async () => {
  const b = await page.locator(`.react-flow__node[data-id="${TID}"]`).boundingBox();
  await page.mouse.click(b.x + 46, b.y + 12);
}));
out.恢复路径.push(await 恢复('③ 双击节点', async () => {
  const b = await page.locator(`.react-flow__node[data-id="${TID}"]`).boundingBox();
  await page.mouse.dblclick(b.x + b.width / 2, b.y + b.height - 12);
}));
out.恢复路径.push(await 恢复('④ 切故事板再切回', async () => {
  await page.locator('[aria-label="故事板"]').first().click({ timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(1800);
  await page.locator('[aria-label="工作流"]').first().click({ timeout: 8000 }).catch(() => {});
}));
out.恢复路径.push(await 恢复('⑤ ⌘0 适合屏幕', async () => {
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1200);
}));
out.恢复路径.push(await 恢复('⑥ 刷新页面（阳性对照）', async () => {
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6500);
  await closePromos(page);
  await page.waitForTimeout(1500);
}));

out.收尾 = await state();
console.log('\n收尾 =', JSON.stringify(out.收尾));
await writeFile(resolve(HERE, '.evidence/cj1-drawer-occlusion.json'), JSON.stringify(out, null, 2));
console.log('\n（不扣积分、不落盘、未点生成）');
await browser.close();
