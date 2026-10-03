// Batch CO-0：把**另外三类**节点的大编辑器也盘一遍。
//
// CN 盘的是智能剪辑（视频）。手册现在只对那一类知道底：5 个模式、三合一规格面板。
// 剩下三类一个都没盘过 —— 而它们的模态文案明显不同（图片有 `参考 标记 风格`，
// 音频有 `Seed Audio 1.0` / `中文 · 24k · wav` / `0/2000` / `1` / `高级设置` / `语速`）。
//
// ⭐ 两处把 CN 的教训直接写进代码：
//   ① 差分/枚举**一律从 `document.body` 起**（菜单是 portal 出去的，不在模态子树里）
//   ② 点 `⤢` 之前**先验落点**：在按钮矩形内扫点，用 `elementFromPoint` 找一个
//      真的落在那枚 `size-7` 按钮上的点 —— 文本节点那枚 ⤢ 有一部分被底栏压着
//
// ⛔ 全程只读：点开下拉、读枚举、再点一次收掉。**不选任何选项。**
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1', 'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];
const SUBJ = [
  { 名: '图片节点', id: 'i-sODTbgLUm1' },
  { 名: '文本节点', id: 't-2AK3Ukyxj3' },
  { 名: '音频节点', id: 'a-THmbuJXQj4' },
];

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
const killPromo = async (page) => {
  const b = await page.evaluate(() => {
    const t = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
    if (!t) return null; const r = t.getBoundingClientRect(); return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
  });
  if (!b) return false;
  await page.mouse.click(b[0], b[1]); await page.waitForTimeout(1200); return true;
};
const read = (page, id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { 在: false };
  const vis = [...n.querySelectorAll('*')].filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
  const fold = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
  return { 在: true, 选中: n.classList.contains('selected'), 可见后代数: vis.length, 有提示词框: !!n.querySelector('textarea,[contenteditable="true"]'), 折叠钮: !!fold };
}, id);
const modal = (page) => page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  return d ? { 开: true, 全文: (d.innerText || '').replace(/\s+/g, ' ').trim() } : { 开: false };
});
// ⭐ 快照一律从 body 起
const snap = (page) => page.evaluate(() => {
  const out = new Map();
  for (const e of document.querySelectorAll('body *')) {
    if (e.children.length) continue;
    const s = getComputedStyle(e); if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0) continue;
    const r = e.getBoundingClientRect(); if (!r.width || !r.height) continue;
    const t = (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim(); if (!t || t.length > 30) continue;
    const host = e.closest('body > *');
    const cls = host ? (host.className || '').toString() : '';
    if (host && (getComputedStyle(host).zIndex === '600' || /ysf-chat-layer/.test(cls))) continue;   // 压暗遮罩 / 客服层
    out.set(`${t}@${Math.round(r.x)},${Math.round(r.y)}`, { 文字: t, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
  }
  return [...out.values()];
});
const diff = (a, b) => b.filter((x) => !a.some((y) => y.文字 === x.文字 && y.rect[0] === x.rect[0] && y.rect[1] === x.rect[1]));
// 模态内全部按钮（只读）
const modalButtons = (page) => page.evaluate(() => {
  const d = [...document.body.children].find((e) => getComputedStyle(e).zIndex === '601');
  if (!d) return null;
  return [...d.querySelectorAll('button')].map((b) => {
    const r = b.getBoundingClientRect();
    const p = b.querySelector('svg path');
    return { 文字: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 22), aria: b.getAttribute('aria-label'), 禁用: b.disabled, 类: (b.className || '').toString().slice(0, 34), 图标: p ? (p.getAttribute('d') || '').slice(0, 18) : null, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  }).filter((b) => b.rect[2] > 0);
});
// ⭐ 找 ⤢ 的可靠落点：在按钮矩形内扫点，逐个 elementFromPoint 验身份
const foldPoint = (page, id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const f = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
  if (!f) return null;
  const r = f.getBoundingClientRect();
  const 点 = [];
  for (const fy of [0.2, 0.35, 0.5, 0.65, 0.8]) for (const fx of [0.3, 0.5, 0.7]) {
    点.push([Math.round(r.x + r.width * fx), Math.round(r.y + r.height * fy)]);
  }
  const 全 = [];
  for (const [x, y] of 点) {
    const el = document.elementFromPoint(x, y);
    const 是不是 = !!(el && el.closest('button') && el.closest('button').className.toString().includes('size-7'));
    全.push({ 点: [x, y], 落点是它: 是不是 });
  }
  const 好 = 全.find((p) => p.落点是它 && p.点[0] < 1440 && p.点[1] < 810);
  return { 按钮rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 扫点: 全, 可用: 好 ? 好.点 : null };
}, id);

const openModal = async (page, id) => {
  for (let i = 0; i < 3; i += 1) {
    if ((await modal(page)).开) return true;
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
    let ok = false;
    for (const p of pts) { await page.mouse.click(p[0], p[1]); await page.waitForTimeout(1300); const s = await read(page, id); if (s.选中 && s.折叠钮) { ok = true; break; } }
    if (!ok) return false;
    const fp = await foldPoint(page, id);
    if (!fp) return false;
    if (!fp.可用) { console.log(`  ⛔ ⤢ 没有可用的落点：按钮 ${JSON.stringify(fp.按钮rect)}，扫点命中 ${fp.扫点.filter((p) => p.落点是它).length} 个`); return false; }
    await page.mouse.click(fp.可用[0], fp.可用[1]);
    await page.waitForTimeout(1900);
  }
  return (await modal(page)).开;
};

const out = { 类型: [] };
const { browser, page } = await launch();
await boot(page);
out.促销 = await killPromo(page);

for (const S of SUBJ) {
  console.log(`\n========== ${S.名} ${S.id}`);
  if (!(await openModal(page, S.id))) { console.log('  ⛔ 开不出模态'); out.类型.push({ 名: S.名, 注: '开不出模态' }); if ((await modal(page)).开) { await page.mouse.click(1360, 780); await page.waitForTimeout(1200); } continue; }
  const R = { 名: S.名, id: S.id, 模态全文: (await modal(page)).全文 };
  R.按钮 = await modalButtons(page);
  console.log(`  模态全文：${R.模态全文}`);
  console.log(`  模态内 ${R.按钮.length} 枚按钮：`);
  for (const b of R.按钮) console.log(`     ${JSON.stringify(b.rect)} 「${b.文字}」aria=${b.aria} 禁用=${b.禁用}`);

  // 逐个点开**底部一排**和**顶部工具排**的按钮（排除 ⛔ 发送/删除）
  const 候选 = R.按钮.filter((b) => !b.禁用 && b.aria !== '发送' && !['返回节点'].includes(b.文字) && b.rect[2] >= 24);
  R.点开 = [];
  for (const b of 候选) {
    const s0 = await snap(page);
    await page.mouse.click(b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2);
    await page.waitForTimeout(1500);
    const s1 = await snap(page);
    const 新 = diff(s0, s1);
    const 记录 = { 按钮: b.文字 || b.aria, 新出现: 新 };
    if (新.length) { console.log(`     点「${b.文字 || b.aria}」→ 新出现 ${新.length} 条：${新.map((x) => x.文字).join(' / ')}`); }
    else { console.log(`     点「${b.文字 || b.aria}」→ 新出现 0 条`); }
    R.点开.push(记录);
    if (新.length) {
      R.截图 = R.截图 || {};
      R.截图[b.文字 || b.aria || 'anon'] = `co0-${S.名}-${R.点开.length}.png`;
      await page.screenshot({ path: resolve(HERE, '.evidence', R.截图[b.文字 || b.aria || 'anon']) });
      // 收掉：再点一次同一枚
      await page.mouse.click(b.rect[0] + b.rect[2] / 2, b.rect[1] + b.rect[3] / 2);
      await page.waitForTimeout(1200);
      const s2 = await snap(page);
      const 仍 = diff(s0, s2);
      记录.收掉后仍多出 = 仍.length;
      if (仍.length) { await page.keyboard.press('Escape'); await page.waitForTimeout(1200); 记录.用ESC收 = (await modal(page)).开; }
    }
    if (!(await modal(page)).开) { console.log('     ⛔ 模态被关掉了，重开'); if (!(await openModal(page, S.id))) break; }
  }
  out.类型.push(R);
  if ((await modal(page)).开) { await page.mouse.click(1360, 780); await page.waitForTimeout(1500); }
  console.log(`  复原 =`, JSON.stringify(await read(page, S.id)));
}

await browser.close();
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const ids = await p2.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
  out.收尾 = { 节点: ids, 与基线一致: ids.length === BASE.length && BASE.every((x) => ids.includes(x)) };
  console.log('\n收尾节点 =', ids.length, ' 与基线逐项一致 =', out.收尾.与基线一致);
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/co0-other-modals.json'), JSON.stringify(out, null, 2));
