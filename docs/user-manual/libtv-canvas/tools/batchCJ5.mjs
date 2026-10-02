// Batch CJ-5：⛔ 先解决一件自己捅出来的事 —— **图片节点还折着，而且收起会存盘**。
//
// CJ-4 的干净读数：
//   视频节点  169 → 42 → 点标题一次 → 169  ✅
//   图片节点  131 → 39 → 点标题一次 → 39，点标题两次 → 39  ⚠️ **两次都不行**
//   文本节点  连选中都没做到（点节点中心偏下那个点没落在它身上）⇒ 没测到
//
// 所以「点标题就能恢复」目前**只对视频节点成立**，不能推广；图片节点现在还折着，必须复原。
//
// 本步：
//   ① 给每个节点找一个**独占点**（在节点框内扫网格，要求
//      `elementFromPoint(x,y).closest('.react-flow__node')` 恰好等于目标）—— 手册里已验证的手法；
//   ② 图片节点逐条试恢复路径，每条**只试一次**并记录，命中即停：
//      点标题 / 点卡片本体 / 点空白取消选中后再点 / `⌘Z` / 切故事板再切回；
//   ③ 文本节点补测；
//   ④ 最后开**全新浏览器会话**复核两个节点都是展开的。
// ⛔ 不点生成、不点「取消」。`⌘Z` 只在前面几条都失败时才用（它是最后一个手段）。
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
  return { 在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]'), 折叠钮: fr ? [Math.round(fr.x), Math.round(fr.y)] : null };
}, id);

// ⭐ 在节点框内扫网格，找一个**独占点**（手册已验证：AY/AZ 批就是靠这个摆脱「点到了压在上面的别的节点」）
const exclusive = (id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  for (const fy of [0.2, 0.35, 0.5, 0.65, 0.8]) {
    for (const fx of [0.1, 0.2, 0.3, 0.5, 0.7, 0.9]) {
      const x = r.x + r.width * fx, y = r.y + r.height * fy;
      const el = document.elementFromPoint(x, y);
      if (el && el.closest('.react-flow__node') === n) return [Math.round(x), Math.round(y)];
    }
  }
  return null;
}, id);

const IMG = 'i-sODTbgLUm1', TXT = 't-UtVx3lZmrV', VID = 'v-v2hlWY4Br3';

// ═══ ① 图片节点：逐条恢复 ═══
console.log('════ 图片节点（当前应为折起）════');
let r = await read(IMG);
console.log('  开局:', JSON.stringify(r));
out.图片 = { 开局: r, 尝试: [] };
if (r.在 && !r.有提示词框) {
  const routes = [
    ['a 点标题', async (p) => { const b = await p.locator(`.react-flow__node[data-id="${IMG}"]`).boundingBox(); await p.mouse.click(b.x + 46, b.y + 12); }],
    ['b 点卡片本体', async (p, pt) => { await p.mouse.click(pt[0], pt[1]); }],
    ['c 点空白取消选中后再点节点', async (p, pt) => { await p.mouse.click(640, 300); await p.waitForTimeout(900); await p.mouse.click(pt[0], pt[1]); }],
    ['d 点空白后点标题', async (p) => { await p.mouse.click(640, 300); await p.waitForTimeout(900); const b = await p.locator(`.react-flow__node[data-id="${IMG}"]`).boundingBox(); await p.mouse.click(b.x + 46, b.y + 12); }],
    ['e 切故事板再切回', async (p) => { await p.locator('[aria-label="故事板"]').first().click({ timeout: 8000 }).catch(() => {}); await p.waitForTimeout(1800); await p.locator('[aria-label="工作流"]').first().click({ timeout: 8000 }).catch(() => {}); }],
    ['f ⌘Z 撤销', async (p) => { await p.evaluate(() => document.body.focus()); await p.keyboard.press('Meta+z'); }],
  ];
  for (const [name, act] of routes) {
    const pt = (await exclusive(IMG)) || [0, 0];
    await act(page, pt);
    await page.waitForTimeout(1700);
    const now = await read(IMG);
    const ok = now.在 && now.可见后代数 > 39;
    console.log(`  ${ok ? '✅' : '⛔'} ${name.padEnd(22)} 39 → ${now.可见后代数} 提示词框=${now.有提示词框}`);
    out.图片.尝试.push({ 路径: name, 恢复了: ok, 读数: now });
    if (ok) break;
  }
} else console.log('  已是展开态');
out.图片.收尾 = await read(IMG);

// ═══ ② 文本节点补测 ═══
console.log('\n════ 文本节点 ════');
{
  const pt = await exclusive(TXT);
  console.log('  独占点 =', JSON.stringify(pt));
  if (pt) {
    await page.mouse.click(pt[0], pt[1]);
    await page.waitForTimeout(1700);
    const sel = await read(TXT);
    console.log('  选中后:', JSON.stringify(sel));
    if (sel.选中 && sel.折叠钮) {
      await page.mouse.click(sel.折叠钮[0] + 14, sel.折叠钮[1] + 14);
      await page.waitForTimeout(1700);
      const folded = await read(TXT);
      console.log('  折后:  ', JSON.stringify(folded));
      const t = await page.locator(`.react-flow__node[data-id="${TXT}"]`).boundingBox();
      await page.mouse.click(t.x + 46, t.y + 12);
      await page.waitForTimeout(1700);
      const rec = await read(TXT);
      console.log('  点标题:', JSON.stringify(rec), rec.可见后代数 === sel.可见后代数 ? '✅ 复原' : '⚠️ 没复原');
      out.文本 = { 展开: sel, 折后: folded, 复原: rec };
      if (!rec.有提示词框) { await page.mouse.click(t.x + 46, t.y + 12); await page.waitForTimeout(1500); out.文本.复原2 = await read(TXT); console.log('  再点一次:', JSON.stringify(out.文本.复原2)); }
    } else out.文本 = { 选中: sel, 说明: '选中后仍无 ⤢ ⇒ 没测到' };
  } else out.文本 = { 说明: '扫不出独占点' };
}
await writeFile(resolve(HERE, '.evidence/cj5-restore-image.json'), JSON.stringify(out, null, 2));
await browser.close();

// ═══ ③ 全新会话复核 ═══
{
  const { browser: b2, page: p2 } = await launch();
  await open(p2, URL_);
  await closePromos(p2);
  await p2.waitForTimeout(1500);
  await p2.evaluate(() => document.body.focus());
  await p2.keyboard.press('Meta+0');
  await p2.waitForTimeout(2600);
  const fin = await p2.evaluate((ids) => {
    const o = {};
    for (const id of ids) {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!n) { o[id] = '不在视口'; continue; }
      const vis = [...n.querySelectorAll('*')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
      o[id] = { 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]') };
    }
    return o;
  }, [IMG, VID, TXT]);
  console.log('\n════ 全新会话复核 ════');
  console.log('  ' + JSON.stringify(fin));
  await writeFile(resolve(HERE, '.evidence/cj5-final-state.json'), JSON.stringify(fin, null, 2));
  await b2.close();
}
