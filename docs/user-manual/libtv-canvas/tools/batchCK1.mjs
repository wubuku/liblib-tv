// Batch CK-1：把新节点拍对、然后**只删本轮自己造出来的那个**，并复核。
//
// CK-0 的结论（干净）：风格广场点卡片 ⇒ 节点 `11 → 12`，新增 `m-N9X90V3Ttl`，
// class `react-flow__node-material-style`，画面与抽屉里都写 `素材-风格-Seedream 5.0 pro`，
// 广场 300ms 内自关（8 次采样全 false）。
//
// ⛔ CK-0 拍的 `M-331` **名不副实**（拍成了「音频节点 6」）。根因很典型：
//    clip 是在**打开资产管理抽屉之前**算的，而开抽屉会改变画布可视区、
//    React Flow 随即**重排所有节点** ⇒ 算好的矩形整体作废。
//    ⭐ 这正是「clip 必须在变化之前算好」的另一面：**变化发生在算完之后也不行**。
//    ✅ 改法：先把所有抽屉收干净 → `⌘0` → **立刻**读矩形 → 立刻拍，中间不做别的。
//
// 收尾纪律：只删 `m-N9X90V3Ttl` 这一个，删完按 **id 集合**与基线逐项比对，
// 再用**另一个全新浏览器会话**复核。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const NID = 'm-N9X90V3Ttl';
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];

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

const ids = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
out.开局 = await ids();
console.log('开局 id =', JSON.stringify(out.开局));
console.log('本轮节点还在 =', out.开局.includes(NID));

// ① 所有抽屉收干净
for (let i = 0; i < 3; i += 1) {
  const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
  if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(700);
}
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2600);

// ② 立刻读矩形、立刻拍
const r = await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const q = n.getBoundingClientRect();
  return { rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)], 文字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40), class: (n.className || '').toString().slice(0, 70) };
}, NID);
console.log('新节点 =', JSON.stringify(r));
out.新节点 = r;
if (!r) { console.log('⛔ 节点不在视口内，改为「不配图」'); await browser.close(); process.exit(0); }

// 再确认一次：这一刻的矩形仍然有效（读两次，间隔 300ms，矩形不动才算稳）
const r2 = await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const q = n.getBoundingClientRect();
  return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)];
}, NID);
console.log('矩形复读 =', JSON.stringify(r2), ' 与首次一致 =', JSON.stringify(r2) === JSON.stringify(r.rect));
out.矩形稳定 = JSON.stringify(r2) === JSON.stringify(r.rect);
if (!out.矩形稳定) { console.log('⛔ 矩形还在动 ⇒ 不配图'); await writeFile(resolve(HERE, '.evidence/ck1-cleanup.json'), JSON.stringify(out, null, 2)); await browser.close(); process.exit(0); }

await page.mouse.move(5, 480);
await page.waitForTimeout(600);
const clip = { x: Math.max(0, r.rect[0] - 40), y: Math.max(0, r.rect[1] - 40), width: r.rect[2] + 80, height: r.rect[3] + 80 };
await shot(page, 'M-331-风格卡片-点一下就进了画布.png', { clip });
console.log('已重拍 M-331  clip =', JSON.stringify(clip));

// ③ 只删本轮自己造出来的那个
console.log('\n════ 删除新节点 ════');
await page.locator('button[aria-label="资产管理"]').first().click({ timeout: 8000 }).catch(() => {});
await page.waitForTimeout(2000);
out.行候选 = await page.evaluate((nm) => [...document.querySelectorAll('button,[role="button"]')]
  .map((b) => ({ t: (b.innerText || '').replace(/\s+/g, ' ').trim(), aria: b.getAttribute('aria-label') }))
  .filter((x) => x.t === nm || (x.t || '').includes(nm)), '素材-风格');
console.log('抽屉里含该名字的元素 =', JSON.stringify(out.行候选));

// 悬停到那一行 → 同一行的「更多操作」→ 删除
const rowBtn = page.locator('button', { hasText: '素材-风格' }).first();
const rb = await rowBtn.boundingBox().catch(() => null);
console.log('行按钮 =', JSON.stringify(rb));
if (rb) {
  await page.mouse.move(rb.x + rb.width / 2, rb.y + rb.height / 2);
  await page.waitForTimeout(1100);
  out.更多操作 = await page.evaluate(() => [...document.querySelectorAll('button,[role="menuitem"]')].map((b) => ({ t: (b.innerText || '').replace(/\s+/g, ' ').trim(), aria: b.getAttribute('aria-label') })).filter((x) => x.aria === '更多操作' || /更多操作/.test(x.t || '')));
  console.log('更多操作 =', JSON.stringify(out.更多操作));
  const mo = page.locator('button[aria-label="更多操作"]').first();
  if (await mo.count()) {
    await mo.click({ timeout: 6000 }).catch(() => {});
    await page.waitForTimeout(1200);
    out.菜单项 = await page.evaluate(() => [...document.querySelectorAll('[role="menuitem"],button')].map((b) => (b.innerText || '').replace(/\s+/g, ' ').trim()).filter((t) => t && t.length <= 8).slice(-12));
    console.log('菜单项 =', JSON.stringify(out.菜单项));
    const del = page.locator('text=删除').last();
    if (await del.count()) {
      await del.click({ timeout: 6000 }).catch(() => {});
      await page.waitForTimeout(2000);
    }
  }
}
// 收抽屉
await page.keyboard.press('Escape').catch(() => {});
for (let i = 0; i < 3; i += 1) {
  const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
  if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(600);
}
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2600);

out.删后 = await ids();
out.与基线逐项一致 = out.删后.length === BASE.length && BASE.every((x) => out.删后.includes(x)) && !out.删后.includes(NID);
console.log('\n删后 id =', JSON.stringify(out.删后));
console.log('与基线 11 个逐项一致 =', out.与基线逐项一致, ' 目标 id 已消失 =', !out.删后.includes(NID));
await browser.close();

// ④ 全新会话复核
{
  const { browser: b2, page: p2 } = await launch();
  await open(p2, URL_);
  await closePromos(p2);
  await p2.evaluate(() => document.body.focus());
  await p2.keyboard.press('Meta+0');
  await p2.waitForTimeout(3000);
  const fin = await p2.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
  out.全新会话 = fin;
  out.全新会话一致 = fin.length === BASE.length && BASE.every((x) => fin.includes(x));
  console.log('全新会话 id =', JSON.stringify(fin), ' 与基线一致 =', out.全新会话一致);
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/ck1-cleanup.json'), JSON.stringify(out, null, 2));
console.log('\n（只删本轮自己造出来的节点）');
