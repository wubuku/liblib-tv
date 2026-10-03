// Batch CS：把「产品贴的功能锚点」这条新路**用到底**。
//
// CR 在画布默认状态下扫到 `data-practice-*` 只有 4 个取值。这说明默认态覆盖得很少，
// 大概率是**面板打开时才贴**（CR-0 就亲眼见到 `data-feature-id` 只在大编辑器里）。
// 本步：逐个打开已知面板，每开一个就重扫一次，**做差分**，
// 目的是把「这个面板里有哪些功能锚点」列成一张表。
//
// ⛔ 只打开面板、只读；不点任何会产生写入的控件。
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
// ⭐ 全页枚举所有 data-* 里带 feature / practice / anchor 的，键 = 属性名 + 值 + 位置
const tags = (page) => page.evaluate(() => {
  const out = new Map();
  for (const e of document.querySelectorAll('body *')) {
    for (const a of e.attributes) {
      if (!a.name.startsWith('data-')) continue;
      if (!/feature|practice|anchor/i.test(a.name)) continue;
      const r = e.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      out.set(`${a.name}=${a.value}`, { 属性: a.name, 值: a.value || '(空)', tag: e.tagName.toLowerCase(), 文字: (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 20), aria: e.getAttribute('aria-label'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
    }
  }
  return [...out.values()];
});
const ids = (page) => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));

const out = { 面板: [] };
const { browser, page } = await launch();
await boot(page);
out.促销 = await killPromo(page);
const base = new Map((await tags(page)).map((t) => [`${t.属性}=${t.值}`, t]));
console.log(`默认态：${base.size} 个锚点 —— ${[...base.keys()].join('  ')}`);

// 每个面板：打开 → 扫 → 关掉（关不掉就记下来）
const 面板 = [
  { 名: '故事板', 开: async () => (await page.locator('button[aria-label="故事板"]').first().click({ timeout: 6000 }).catch(() => {})), 关: async () => (await page.locator('button[aria-label="工作流"]').first().click({ timeout: 6000 }).catch(() => {})) },
  { 名: '资产管理', 开: async () => (await page.locator('text=资产管理').first().click({ timeout: 6000 }).catch(() => {})), 关: async () => (await page.keyboard.press('Escape')) },
  { 名: '资产抽屉页', 开: async () => { await page.locator('text=资产管理').first().click({ timeout: 6000 }).catch(() => {}); await page.waitForTimeout(900); await page.locator('text=资产').first().click({ timeout: 6000 }).catch(() => {}); }, 关: async () => (await page.keyboard.press('Escape')) },
  { 名: '角色造型室', 开: async () => (await page.locator('text=角色').first().click({ timeout: 6000 }).catch(() => {})), 关: async () => (await page.keyboard.press('Escape')) },
  { 名: '快捷键面板', 开: async () => (await page.locator('text=快捷键').first().click({ timeout: 6000 }).catch(() => {})), 关: async () => (await page.keyboard.press('Escape')) },
  { 名: '底栏「?」帮助', 开: async () => (await page.locator('text=帮助').first().click({ timeout: 6000 }).catch(() => {})), 关: async () => (await page.keyboard.press('Escape')) },
];

for (const P of 面板) {
  const before = new Set((await tags(page)).map((t) => `${t.属性}=${t.值}`));
  await P.开();
  await page.waitForTimeout(1800);
  const now = await tags(page);
  const 新 = now.filter((t) => !before.has(`${t.属性}=${t.值}`));
  const 仍 = now.length;
  console.log(`\n=== ${P.名}：打开后共 ${仍} 个锚点（打开前 ${before.size}），**新增 ${新.length} 个**`);
  for (const t of 新) console.log(`   ${t.属性}="${t.值}"  <${t.tag}> 「${t.文字}」 ${JSON.stringify(t.rect)}`);
  out.面板.push({ 名: P.名, 打开前: before.size, 打开后: 仍, 新增: 新 });
  await P.关();
  await page.waitForTimeout(1400);
  const back = await tags(page);
  console.log(`   关掉后回到 ${back.length} 个`);
}

// 收尾
out.收尾 = { 节点: await ids(page), 一致: true };
const fin = await ids(page);
out.收尾.一致 = fin.length === BASE.length && BASE.every((x) => fin.includes(x));
console.log('\n收尾节点 =', fin.length, ' 与基线逐项一致 =', out.收尾.一致);
await browser.close();
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const ids2 = await ids(p2);
  out.全新会话 = { 节点: ids2.length, 一致: ids2.length === BASE.length && BASE.every((x) => ids2.includes(x)), 锚点: (await tags(p2)).map((t) => `${t.属性}=${t.值}`) };
  console.log('全新会话 节点', ids2.length, ' 一致 =', out.全新会话.一致, ' 锚点 =', JSON.stringify(out.全新会话.锚点));
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cs0-panel-anchors.json'), JSON.stringify(out, null, 2));
