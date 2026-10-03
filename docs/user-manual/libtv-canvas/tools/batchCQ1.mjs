// Batch CQ-1：重拍「尝试」栏。
//
// CQ-0 那张废了：clip 取的是音频节点卡片，而 `文本节点 1` 的卡片**本来就和它重叠**
// （[217,610,164×164] 压住 [319,554,164×164] 的左下角），`尝试：` 那一行被盖掉了。
// ⭐ 这是 CK 记过的那类坑的另一个面：**不是「拍完状态变了」，是「本来就重叠」**。
//
// 治法写进脚本：拍之前逐个验「那个点上最上面的是不是我要拍的那一项」。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];
const 目标 = [
  { id: 'v-v2hlWY4Br3', 名: '视频节点3-三个尝试' },
  { id: 't-UtVx3lZmrV', 名: '文本节点1-四个尝试' },
  { id: 'v-oZNpH99MtM', 名: '智能剪辑4-四个带图标的尝试' },
];

const boot = async (page) => {
  await open(page, URL_);
  await closePromos(page);
  await page.waitForTimeout(1500);
  await page.evaluate(() => document.body.focus());
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2800);
  for (let i = 0; i < 3; i += 1) {
    const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
    if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
    await page.waitForTimeout(600);
  }
};
const killPromo = async (page) => {
  const b = await page.evaluate(() => {
    const t = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
    if (!t) return null; const r = t.getBoundingClientRect(); return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
  });
  if (!b) return false;
  await page.mouse.click(b[0], b[1]); await page.waitForTimeout(1200); return true;
};
// 「尝试」栏里每一项：不限元素形态，只要文字和位置对
const tryItems = (page, id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const out = [];
  for (const e of n.querySelectorAll('*')) {
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 22) continue;
    if (e.children.length && e.textContent !== t) continue;      // 叶子
    const r = e.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    if (e.querySelector('textarea, input, button')) continue;
    out.push({ 文字: t, tag: e.tagName.toLowerCase(), cursor: getComputedStyle(e).cursor, 有图标: !!e.querySelector('svg'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
  }
  return { 节点rect: (() => { const r = n.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })(), 全部: out };
}, id);
// ⭐ 验「最上面的是不是它」
const topmost = (page, x, y) => page.evaluate(([px, py]) => {
  const el = document.elementFromPoint(px, py);
  if (!el) return null;
  const node = el.closest('.react-flow__node');
  return { 文字: (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 20), 在节点: node ? node.getAttribute('data-id') : null, 是这个节点: node ? node.getAttribute('data-id') === arguments[2] : false };
}, [x, y]);

const out = { 图: [] };
const { browser, page } = await launch();
await boot(page);
out.促销 = await killPromo(page);

for (const T of 目标) {
  const info = await tryItems(page, T.id);
  if (!info) { console.log(`${T.id} 不在`); continue; }
  // 标「尝试：」之后、位置更靠下的那些项
  const 标 = info.全部.find((x) => x.文字.replace(/\s/g, '').includes('尝试'));
  if (!标) { console.log(`${T.id} 没有「尝试」标`); continue; }
  const 项 = info.全部.filter((x) => x.rect[1] > 标.rect[1] && x.rect[1] < 标.rect[1] + 140 && x.文字 !== 标.文字);
  console.log(`\n=== ${T.名} ${T.id} 卡片 ${JSON.stringify(info.节点rect)}`);
  console.log(`  标 ${JSON.stringify(标.rect)} 「${标.文字}」`);
  for (const it of 项) console.log(`  项 ${JSON.stringify(it.rect)} 「${it.文字}」 <${it.tag}> cursor=${it.cursor} 有图标=${it.有图标}`);
  if (!项.length) { console.log('  ⛔ 没读到项'); continue; }

  // ⭐ 逐项验最上层
  const 验 = [];
  for (const it of 项) {
    const [x, y, w, h] = it.rect;
    const t = await page.evaluate(([px, py, nid]) => {
      const el = document.elementFromPoint(px, py);
      if (!el) return { 无: true };
      const node = el.closest('.react-flow__node');
      return { 文字: (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 20), 节点: node ? node.getAttribute('data-id') : null, 正确: !!node && node.getAttribute('data-id') === nid };
    }, [x + w / 2, y + h / 2, T.id]);
    验.push({ 项: it.文字, 落点: t });
    console.log(`   验「${it.文字}」→ 落点「${t.文字}」 节点=${t.节点} 正确=${t.正确}`);
  }
  const 全对 = 验.every((v) => v.落点.正确);
  console.log(`  ⇒ ${全对 ? '✅ 全部露在外面，可以拍' : '⛔ 有被遮挡的项，不拍'}`);
  if (!全对) continue;

  const [cx, cy, cw, ch] = info.节点rect;
  const clip = { x: Math.max(0, cx - 10), y: Math.max(0, cy - 30), width: Math.min(1440 - Math.max(0, cx - 10), cw + 20), height: Math.min(810 - Math.max(0, cy - 30), ch + 42) };
  const 文件 = `cq1-${T.名}.png`;
  await page.screenshot({ path: resolve(HERE, '.evidence', 文件), clip });
  out.图.push({ 名: T.名, id: T.id, 文件, clip, 项: 项.map((x) => x.文字) });
  console.log(`  已拍 ${文件} clip=${JSON.stringify(clip)}`);
}

console.log('\n收尾节点数 =', (await page.evaluate(() => document.querySelectorAll('.react-flow__node').length)));
await browser.close();
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const ids = await p2.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
  out.全新会话 = { 节点: ids.length, 一致: ids.length === BASE.length && BASE.every((x) => ids.includes(x)) };
  console.log('全新会话 节点', ids.length, ' 一致 =', out.全新会话.一致);
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cq1-shots.json'), JSON.stringify(out, null, 2));
