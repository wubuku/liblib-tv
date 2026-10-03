// Batch CM-6：把 ⤢ 打开的那个模态盘到能写手册的程度。
//
// CM-5 已有：视频模态 [320,105,800×600]、ESC 关不掉、点遮罩能关、刷新后节点变未选中、
//           音频 a-THmbuJXQj4 也弹同一个模态；a-CUfJfmKzUJ 这次没弹。
// 还差三件事：
//   ① 模态右上角那枚 28×28 收拢箭头**叫什么**、点它会怎样
//   ② 顶部 `参考` 旁边那枚 15×15 的 `×` 是什么 —— ⛔ 只悬停读名，**绝不点**（它贴着参考缩略图，可能是删素材）
//   ③ a-CUfJfmKzUJ 上 ⤢ 为什么不弹模态 —— 先读落点身份
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];

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
const read = (page, id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { 在: false };
  const vis = [...n.querySelectorAll('*')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  const fold = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
  const r = n.getBoundingClientRect();
  return { 在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]'), 折叠钮: fold ? [Math.round(fold.getBoundingClientRect().x), Math.round(fold.getBoundingClientRect().y)] : null, 节点rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}, id);
const dialogState = (page) => page.evaluate(() => {
  const dlg = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  if (!dlg) return { 模态: false };
  const r = dlg.getBoundingClientRect();
  return { 模态: true, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 全文: (dlg.innerText || '').replace(/\s+/g, ' ').trim() };
});
// 悬停后读气泡：只认新出现的、离鼠标很近的浮层文字
const bubble = (page, x, y) => page.mouse.move(x, y).then(() => page.waitForTimeout(1300)).then(() => page.evaluate(([px, py]) => {
  const 命中 = [];
  for (const e of document.querySelectorAll('body *')) {
    const s = getComputedStyle(e);
    if (s.visibility === 'hidden' || s.display === 'none' || +s.opacity === 0) continue;
    const r = e.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (r.width > 400 || r.height > 120) continue;                 // 气泡很小
    if (Math.abs(r.x + r.width / 2 - px) > 220 || Math.abs(r.y + r.height / 2 - py) > 200) continue;
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (t && e.children.length === 0) 命中.push({ 文字: t.slice(0, 24), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
  }
  return 命中;
}, [x, y]));

const out = {};
const { browser, page } = await launch();
await boot(page);
const VID = 'v-oZNpH99MtM';
const pick = async (id) => {
  const pts = await page.evaluate((nid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
    if (!n) return [];
    const q = n.getBoundingClientRect(); const a = [];
    for (const fy of [0.25, 0.4, 0.55, 0.7, 0.85]) for (const fx of [0.1, 0.25, 0.5, 0.75, 0.9]) {
      const x = q.x + q.width * fx, y = q.y + q.height * fy;
      const el = document.elementFromPoint(x, y);
      if (el && el.closest('.react-flow__node') === n && !el.closest('button,a')) a.push([Math.round(x), Math.round(y)]);
    }
    return a;
  }, id);
  for (const p of pts) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1400); const s = await read(page, id); if (s.选中 && s.折叠钮) return s; }
  return await read(page, id);
};

let sel = await pick(VID);
console.log('视频 选中 =', JSON.stringify(sel));
await page.mouse.click(sel.折叠钮[0] + 14, sel.折叠钮[1] + 14);
await page.waitForTimeout(1800);
out.模态 = await dialogState(page);
console.log('模态 =', JSON.stringify(out.模态).slice(0, 140));

// ① 右上角 28×28 收拢箭头
out.收拢钮 = await page.evaluate(() => {
  const dlg = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  if (!dlg) return null;
  const bs = [...dlg.querySelectorAll('button')].map((b) => { const r = b.getBoundingClientRect(); const p = b.querySelector('svg path'); return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 类: (b.className || '').toString().slice(0, 46), aria: b.getAttribute('aria-label'), 文字: (b.innerText || '').trim(), 图标: p ? p.getAttribute('d') : null }; });
  return bs.sort((a, b) => (a.rect[0] * a.rect[1]) - (b.rect[0] * b.rect[1])).filter((b) => b.rect[0] > 1000);
});
console.log('模态右侧按钮 =', JSON.stringify(out.收拢钮));
const cb = out.收拢钮 && out.收拢钮[0];
if (cb) {
  const [bx, by, bw] = cb.rect;
  out.收拢钮气泡 = await bubble(page, bx + bw / 2, by + 14);
  console.log('收拢钮 悬停气泡 =', JSON.stringify(out.收拢钮气泡));
  await page.mouse.click(bx + bw / 2, by + 14);
  await page.waitForTimeout(1800);
  out.点收拢后 = { 读: await read(page, VID), 模态: await dialogState(page) };
  console.log('点收拢后 =', JSON.stringify(out.点收拢后));
}

// 复原到「模态开着」以便测 ②
if (!(await dialogState(page)).模态) {
  const s2 = await pick(VID);
  if (s2.折叠钮) { await page.mouse.click(s2.折叠钮[0] + 14, s2.折叠钮[1] + 14); await page.waitForTimeout(1800); }
}
// ② 参考旁边那枚 15×15 的 × —— 只悬停，绝不点
out.小叉 = await page.evaluate(() => {
  const dlg = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  if (!dlg) return null;
  const b = [...dlg.querySelectorAll('button')].find((x) => { const r = x.getBoundingClientRect(); return r.width <= 20 && r.height <= 20 && r.width > 0; });
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 类: (b.className || '').toString().slice(0, 46), 父类: (b.parentElement?.className || '').toString().slice(0, 46), 父文字: (b.parentElement?.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) };
});
console.log('小叉 =', JSON.stringify(out.小叉));
if (out.小叉) {
  const [x, y, w, h] = out.小叉.rect;
  out.小叉气泡 = await bubble(page, x + w / 2, y + h / 2);
  console.log('小叉 悬停气泡 =', JSON.stringify(out.小叉气泡), ' ⛔ 未点击');
}
// 干净地拍一张用于手册
out.手册图 = 'cm6-节点大编辑器模态.png';
await page.mouse.move(720, 400);
await page.waitForTimeout(400);
await page.screenshot({ path: resolve(HERE, '.evidence', out.手册图) });
out.拍完仍开着 = (await dialogState(page)).模态;
console.log('拍完模态仍开着 =', out.拍完仍开着);
if (out.拍完仍开着) { await page.mouse.click(1360, 780); await page.waitForTimeout(1500); }

// ③ a-CUfJfmKzUJ 的 ⤢ 为何不弹
{
  const A = 'a-CUfJfmKzUJ';
  let s = await read(page, A);
  out.音频A = { 读: s };
  if (s.在 && s.折叠钮) {
    const x = s.折叠钮[0] + 14, y = s.折叠钮[1] + 14;
    out.音频A.落点 = await page.evaluate(([px, py]) => {
      const el = document.elementFromPoint(px, py);
      if (!el) return { 空: true };
      const chain = []; let a = el;
      for (let i = 0; a && i < 5; i += 1, a = a.parentElement) { const s2 = getComputedStyle(a); const r = a.getBoundingClientRect(); chain.push({ tag: a.tagName.toLowerCase(), cls: (a.className || '').toString().slice(0, 44), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }); }
      return { 元素: `${el.tagName.toLowerCase()}.${(el.className || '').toString().slice(0, 40)}`, 文字: (el.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16), 链: chain };
    }, [x, y]);
    console.log('音频A ⤢ 落点 =', JSON.stringify(out.音频A.落点).slice(0, 300));
    // 先确保选中
    const s2 = await pick(A);
    out.音频A.选中后 = s2;
    if (s2.折叠钮) {
      await page.mouse.click(s2.折叠钮[0] + 14, s2.折叠钮[1] + 14);
      await page.waitForTimeout(1800);
      out.音频A.点后 = { 读: await read(page, A), 模态: await dialogState(page) };
      console.log('音频A 点 ⤢ 后 =', JSON.stringify(out.音频A.点后));
      if (out.音频A.点后.模态.模态) { await page.mouse.click(1360, 780); await page.waitForTimeout(1500); }
    }
  }
}

console.log('\n收尾 =', JSON.stringify(await read(page, VID)));
await browser.close();
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const ids = await p2.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
  out.收尾 = { 节点: ids, 与基线一致: ids.length === BASE.length && BASE.every((x) => ids.includes(x)) };
  console.log('收尾节点 =', ids.length, ' 与基线逐项一致 =', out.收尾.与基线一致);
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cm6-modal-detail.json'), JSON.stringify(out, null, 2));
