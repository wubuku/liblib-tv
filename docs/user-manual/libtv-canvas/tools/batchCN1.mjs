// Batch CN-1：补 CN-0 的三个窟窿。
//
// ① CN-0 的循环**没有每轮重开模态** ⇒ ESC 把模态关掉后，第二个下拉自然找不到按钮（脚本缺陷 §123）。
// ② ⛔ **ESC 的读数自相矛盾**：CM-5 说「ESC 关不掉大编辑器」，CN-0 里一次 ESC 却把模态关掉了。
//    两次的差别是**焦点位置**（CM-5 全程没点过模态内部）。本步做干净的 3 组对照，不预设结论。
// ③ CN-0 运行中又冒出「Agent 已升级为 TV Director」促销弹窗，压在模态区域上。
//    本步显式点它自己的「下次再说」收掉（不点「去体验」—— 那会拉起 TV Director）。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];
const VID = 'v-oZNpH99MtM';

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
// ⭐ 促销弹窗收尾：点它自己的「下次再说」，不点「去体验」
const killPromo = async (page) => {
  const b = await page.evaluate(() => {
    const t = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
    if (!t) return null;
    const r = t.getBoundingClientRect();
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 可见: r.width > 0 };
  });
  if (!b || !b.可见) return false;
  await page.mouse.click(b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2);
  await page.waitForTimeout(1200);
  return true;
};
const read = (page, id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { 在: false };
  const vis = [...n.querySelectorAll('*')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  const fold = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
  return { 在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]'), 折叠钮: !!fold };
}, id);
const modal = (page) => page.evaluate(() => {
  const dlg = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  if (!dlg) return { 开: false };
  return { 开: true, rect: [Math.round(dlg.getBoundingClientRect().x), Math.round(dlg.getBoundingClientRect().y), Math.round(dlg.getBoundingClientRect().width), Math.round(dlg.getBoundingClientRect().height)], 全文: (dlg.innerText || '').replace(/\s+/g, ' ').trim() };
});
// 菜单项：模态内、按钮行**上方**的竖排文字块（选项一定排在按钮上方展开）
const menuItems = (page, btnY) => page.evaluate((by) => {
  const dlg = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  if (!dlg) return [];
  const out = [];
  for (const e of dlg.querySelectorAll('*')) {
    if (e.children.length) continue;
    const t = (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 20) continue;
    const r = e.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (r.y > by) continue;                                   // 只取按钮上方
    const p = e.parentElement && e.parentElement.querySelector('svg path');
    out.push({ 文字: t, 图标: p ? (p.getAttribute('d') || '').slice(0, 22) : null, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
  }
  return out;
}, btnY);
const btnRect = (page, 起始) => page.evaluate((t) => {
  const dlg = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  if (!dlg) return null;
  const b = [...dlg.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith(t));
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 全名: (b.innerText || '').replace(/\s+/g, ' ').trim() };
}, 起始);
const openModal = async (page) => {
  for (let i = 0; i < 3; i += 1) {
    if ((await modal(page)).开) return true;
    const s = await read(page, VID);
    if (!s.在) return false;
    const pts = await page.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const q = n.getBoundingClientRect(); const a = [];
      for (const fy of [0.25, 0.4, 0.55, 0.7, 0.85]) for (const fx of [0.1, 0.25, 0.5, 0.75, 0.9]) {
        const x = q.x + q.width * fx, y = q.y + q.height * fy;
        const el = document.elementFromPoint(x, y);
        if (el && el.closest('.react-flow__node') === n && !el.closest('button,a')) a.push([Math.round(x), Math.round(y)]);
      }
      return a;
    }, VID);
    let ok = false;
    for (const p of pts) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1300); const s2 = await read(page, VID); if (s2.选中 && s2.折叠钮) { ok = true; break; } }
    if (!ok) return false;
    const fx = await page.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const f = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
      if (!f) return null; const r = f.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y)];
    }, VID);
    if (!fx) return false;
    if (fx[0] + 14 > 1440 || fx[1] + 14 > 810) return false;   // ⤢ 出视口
    await page.mouse.click(fx[0] + 14, fx[1] + 14);
    await page.waitForTimeout(1700);
  }
  return (await modal(page)).开;
};
const closeModal = async (page) => {
  if (!(await modal(page)).开) return;
  await page.mouse.click(1360, 780);
  await page.waitForTimeout(1500);
};

const out = { 下拉: [], ESC: [] };
const { browser, page } = await launch();
await boot(page);
out.促销弹窗_开跑时 = await killPromo(page);
console.log('开跑时点掉「下次再说」=', out.促销弹窗_开跑时);

// ② 第二个下拉
if (await openModal(page)) {
  const b = await btnRect(page, '16:9');
  console.log('\n=== 第二个下拉 =', JSON.stringify(b));
  if (b) {
    const [bx, by, bw, bh] = b.rect;
    await page.mouse.click(bx + bw / 2, by + bh / 2);
    await page.waitForTimeout(1500);
    const items = await menuItems(page, by);
    console.log(`  选项 ${items.length} 条:`);
    for (const it of items) console.log(`     ${JSON.stringify(it.rect)} 「${it.文字}」 图标=${it.图标}`);
    out.下拉.push({ 名: '16:9 · 720P · 30s', 按钮: b, 选项: items });
    out.截图 = 'cn1-第二个下拉.png';
    await page.screenshot({ path: resolve(HERE, '.evidence', out.截图) });
    out.拍完菜单仍在 = (await menuItems(page, by)).length;
    // ⛔ 不选。点同一个按钮收掉
    await page.mouse.click(bx + bw / 2, by + bh / 2);
    await page.waitForTimeout(1200);
    out.收掉后选项数 = (await menuItems(page, by)).length;
    console.log(`  再点一次收掉，剩余选项 ${out.收掉后选项数} 条`);
  }
  await closeModal(page);
}

// ② ESC 三组对照 —— 每组都**重新打开**模态
const 组 = [
  { 名: 'A_开模态后什么都不点', 点: null },
  { 名: 'B_点模态内空白处再按ESC', 点: '模态内空白' },
  { 名: 'C_点开下拉菜单再按ESC', 点: '下拉' },
];
for (const g of 组) {
  if (!(await openModal(page))) { console.log(`${g.名}: 开不出模态`); continue; }
  const R = { 名: g.名, 焦点前: await page.evaluate(() => { const a = document.activeElement; return a ? `${a.tagName.toLowerCase()}.${(a.className || '').toString().slice(0, 34)}` : 'null'; }) };
  if (g.点 === '模态内空白') {
    // 模态里既不是按钮也不是输入区的地方：提示词区正中间偏上
    await page.mouse.click(700, 430);
    await page.waitForTimeout(900);
  } else if (g.点 === '下拉') {
    const b = await btnRect(page, '默认模式');
    if (b) { await page.mouse.click(b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2); await page.waitForTimeout(1300); R.菜单开着 = (await menuItems(page, b.rect[1])).length; }
  }
  R.按ESC前焦点 = await page.evaluate(() => { const a = document.activeElement; return a ? `${a.tagName.toLowerCase()}.${(a.className || '').toString().slice(0, 34)}` : 'null'; });
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1500);
  R.模态 = await modal(page);
  R.节点 = await read(page, VID);
  console.log(`  ${g.名.padEnd(22)} 焦点=${R.按ESC前焦点} → 模态${R.模态.开 ? '仍在 ✅没关掉' : '关了'}`);
  out.ESC.push(R);
  await closeModal(page);
}

console.log('\n收尾 模态 =', JSON.stringify(await modal(page)), ' 节点 =', JSON.stringify(await read(page, VID)));
await browser.close();
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const ids = await p2.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
  out.收尾 = { 节点: ids, 与基线一致: ids.length === BASE.length && BASE.every((x) => ids.includes(x)) };
  console.log('收尾节点 =', ids.length, ' 与基线逐项一致 =', out.收尾.与基线一致);
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cn1-dropdown2-esc.json'), JSON.stringify(out, null, 2));
