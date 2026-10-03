// Batch CM-7：收掉最后一个悬案 —— 音频节点 a-CUfJfmKzUJ 上 ⤢ 为何不弹模态。
// CM-6 那次因为「还没选中就没有折叠钮」被自己的判据挡掉了（选中是折叠钮的前提，不是它的前提）。
// 这次：先选中 → 再读 ⤢ 落点身份 → 再点 → 再读。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];
const A = 'a-CUfJfmKzUJ';

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
const out = {};
const { browser, page } = await launch();
await boot(page);

let s = await read(page, A);
console.log('初始 =', JSON.stringify(s));
const pts = await page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  const q = n.getBoundingClientRect(); const a = [];
  for (const fy of [0.25, 0.4, 0.55, 0.7, 0.85]) for (const fx of [0.1, 0.25, 0.5, 0.75, 0.9]) {
    const x = q.x + q.width * fx, y = q.y + q.height * fy;
    const el = document.elementFromPoint(x, y);
    if (el && el.closest('.react-flow__node') === n && !el.closest('button,a')) a.push([Math.round(x), Math.round(y)]);
  }
  return a;
}, A);
for (const p of pts) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1400); s = await read(page, A); if (s.选中) break; }
console.log('选中后 =', JSON.stringify(s));
out.选中后 = s;

if (s.折叠钮) {
  const x = s.折叠钮[0] + 14, y = s.折叠钮[1] + 14;
  out.点击点 = [x, y];
  out.落点 = await page.evaluate(([px, py]) => {
    const el = document.elementFromPoint(px, py);
    if (!el) return { 空: true };
    const chain = []; let a = el;
    for (let i = 0; a && i < 6; i += 1, a = a.parentElement) { const st = getComputedStyle(a); const r = a.getBoundingClientRect(); chain.push({ tag: a.tagName.toLowerCase(), cls: (a.className || '').toString().slice(0, 46), pos: st.position, z: st.zIndex, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }); }
    return { 元素: `${el.tagName.toLowerCase()}.${(el.className || '').toString().slice(0, 40)}`, 文字: (el.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16), 是同一枚按钮吗: !!(el.closest('button') && el.closest('button').className.toString().includes('size-7')), 链: chain };
  }, [x, y]);
  console.log('⤢ 落点 =', JSON.stringify(out.落点).slice(0, 420));
  await page.mouse.click(x, y);
  await page.waitForTimeout(1900);
  out.点后 = { 读: await read(page, A), 模态: await dialogState(page) };
  console.log('点后 =', JSON.stringify(out.点后).slice(0, 300));
  if (out.点后.模态.模态) {
    out.清单 = await page.evaluate(() => {
      const dlg = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
      const box = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; };
      return { 按钮: [...dlg.querySelectorAll('button')].map((b) => ({ 文字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16), aria: b.getAttribute('aria-label'), rect: box(b), 禁用: b.disabled })), 全文: (dlg.innerText || '').replace(/\s+/g, ' ').trim() };
    });
    console.log('音频模态 按钮 =', JSON.stringify(out.清单.按钮));
    await page.mouse.click(1360, 780); await page.waitForTimeout(1500);
  } else {
    // 试点相邻几个像素，确认不是「差几像素」
    for (const d of [[0, 0], [-8, 0], [8, 0], [0, -8], [0, 8]]) {
      const px = x + d[0], py = y + d[1];
      await page.mouse.click(px, py);
      await page.waitForTimeout(1400);
      const st = await dialogState(page);
      console.log(`  试点 (${px},${py}) → 模态=${st.模态}`);
      if (st.模态) { out.命中偏移 = d; await page.mouse.click(1360, 780); await page.waitForTimeout(1400); break; }
    }
  }
}
console.log('复原 =', JSON.stringify(await read(page, A)));
await browser.close();
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const ids = await p2.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
  out.收尾 = { 节点: ids, 与基线一致: ids.length === BASE.length && BASE.every((x) => ids.includes(x)) };
  console.log('收尾节点 =', ids.length, ' 与基线逐项一致 =', out.收尾.与基线一致);
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cm7-audioA.json'), JSON.stringify(out, null, 2));
