// Batch CC-8：核实 + 清干净本轮点卡片造出来的节点。
// 基线（用户原有 11 个）：文本节点 1 / 文本节点 1 / 音频节点 1 / 视频节点 3 / 视频节点 3 /
//   图片节点 2 / 图片节点 2 / 音频节点 6 / 逐帧拉片 / 导演台 5 / 智能剪辑 4
// ⛔ 删除判据：节点名以 **`素材-特效-`** 开头 —— 这是**本轮点卡片才会产生的名字**，
//    用户原有 11 个节点里**一个都不带这个前缀**。删完逐项比对那 11 个名字必须全在。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const BASE_11 = ['文本节点 1', '文本节点 1', '音频节点 1', '视频节点 3', '图片节点 2', '图片节点 2', '音频节点 6', '逐帧拉片', '导演台 5', '智能剪辑 4', '视频节点 3', '图片节点 2', '文本节点 1'];

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
const out = { deleted: [] };

const inDrawer = (fnBody) => page.evaluate(`(() => {
  const d = [...document.querySelectorAll('.mantine-Drawer-content')]
    .filter((x) => { const r = x.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .find((x) => [...x.querySelectorAll('button')].some((b) => ['画布','资产'].includes((b.innerText||'').trim())));
  if (!d) return { __err: 'asset drawer not found' };
  ${fnBody}
})()`);

await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const c = [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
    .map((el) => ({ el, r: el.getBoundingClientRect() })).filter((o) => o.r.x < 100).sort((a, b) => a.r.x - b.r.x);
  c[0]?.el.click();
});
await page.waitForTimeout(1800);

const rowsNow = () => inDrawer(`
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const rows = [];
  for (const b of d.querySelectorAll('[aria-label^="定位到节点"]')) {
    const r = b.getBoundingClientRect();
    if (!vis(b) || r.width < 100) continue;          // 每行有两枚同名按钮，取靠左那枚（宽的）
    const name = (b.getAttribute('aria-label') || '').replace('定位到节点 ', '').trim();
    if (!name) continue;
    if (rows.some((x) => Math.abs(x.y - r.y) < 10)) continue;
    rows.push({ name, y: Math.round(r.y) });
  }
  return rows;`);
const countNow = () => inDrawer(`const m=((d.innerText||'').match(/共 (\\d+) 节点/)||[])[1]; return m?Number(m):null;`);

out.beforeCount = await countNow();
out.beforeRows = await rowsNow();
console.log('BEFORE count =', out.beforeCount, JSON.stringify(out.beforeRows.map((r) => r.name)));

// 逐个删「素材-特效-」开头的
for (let round = 0; round < 6; round += 1) {
  const rows = await rowsNow();
  const target = rows.find((r) => r.name.startsWith('素材-特效-'));
  if (!target) break;
  const step = { name: target.name, y: target.y };
  await page.mouse.move(120, target.y + 14, { steps: 10 });
  await page.waitForTimeout(700);
  step.opened = await page.evaluate((y) => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const m = [...document.querySelectorAll('[aria-label="更多操作"]')].filter(vis)
      .find((x) => Math.abs(x.getBoundingClientRect().y - y) < 8);
    if (!m) return { ok: false };
    m.click();
    return { ok: true };
  }, target.y);
  await page.waitForTimeout(900);
  step.del = await page.evaluate(() => {
    const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
      .find((el) => (el.innerText || '').trim() === '删除');
    if (!it) return { ok: false, why: '菜单里没有删除' };
    it.click();
    return { ok: true };
  });
  await page.waitForTimeout(1800);
  step.countAfter = await countNow();
  out.deleted.push(step);
}

out.afterCount = await countNow();
out.afterRows = await rowsNow();
out.afterNames = out.afterRows.map((r) => r.name);
out.gone = !out.afterNames.some((n) => n.startsWith('素材-特效-'));
out.baseIntact = BASE_11.every((n) => out.afterNames.includes(n));
await shot(page, 'M-299-特效卡片-加进来的节点已清理.png', { clip: { x: 0, y: 80, width: 400, height: 480 } });
await writeFile(resolve(HERE, '.evidence/cc8-final.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ beforeCount: out.beforeCount, deleted: out.deleted.map((d) => ({ name: d.name, ok: d.del?.ok, countAfter: d.countAfter })), afterCount: out.afterCount, afterNames: out.afterNames, gone: out.gone, baseIntact: out.baseIntact }, null, 2));
await browser.close();
