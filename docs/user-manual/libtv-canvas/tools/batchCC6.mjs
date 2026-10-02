// Batch CC-6：删掉 CC-4 点卡片时**本轮自己造出来的**那个节点「素材-特效-小蜜蜂运镜」。
//
// ⛔ 认行用**无障碍名的全等**：「定位到节点 素材-特效-小蜜蜂运镜」。
//    这条抽屉里的 `aria-label` 带着**节点名**，是本手册目前找到的**最可靠的身份凭据**
//    —— 比位置、比顺序、比「看起来是多余的」都强。
// ⛔ 点删除前**先把这一行的名字读一遍**；删完**逐项比对**剩下的 11 行与基线是否逐字相同。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MINE = '素材-特效-小蜜蜂运镜';
const BASE_11 = ['文本节点 1', '音频节点 1', '视频节点 3', '图片节点 2', '音频节点 6', '逐帧拉片', '导演台 5', '智能剪辑 4', '视频节点 3', '图片节点 2', '文本节点 1'];

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
const out = {};

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
    if (!vis(b)) continue;
    const name = (b.getAttribute('aria-label') || '').replace('定位到节点 ', '').trim();
    if (!name) continue;
    if (rows.some((x) => Math.abs(x.y - r.y) < 6)) continue;
    rows.push({ name, y: Math.round(r.y) });
  }
  return rows;`);

out.before = { rows: await rowsNow(), count: (await inDrawer(`const m=((d.innerText||'').match(/共 (\\d+) 节点/)||[])[1]; return m?Number(m):null;`)) };
console.log('BEFORE count =', out.before.count);
console.log('BEFORE rows  =', JSON.stringify(out.before.rows.map((r) => r.name)));

// —— 认行：名字全等 =====
const target = out.before.rows.find((r) => r.name === MINE);
out.target = target;
if (target) {
  // ⭐ 先悬停这一行，再点**同一个 y 上**的 更多操作
  await page.mouse.move(120, target.y + 14, { steps: 10 });
  await page.waitForTimeout(700);
  out.opened = await page.evaluate((y) => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const m = [...document.querySelectorAll('[aria-label="更多操作"]')].filter(vis)
      .find((x) => Math.abs(x.getBoundingClientRect().y - y) < 8);
    if (!m) return { ok: false, why: '该行没有更多操作' };
    m.click();
    return { ok: true };
  }, target.y);
  await page.waitForTimeout(900);
  out.menu = await page.evaluate(() => [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
    .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0; }).map((el) => (el.innerText || '').trim()));
  out.delClicked = await page.evaluate(() => {
    const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
      .find((el) => (el.innerText || '').trim() === '删除');
    if (!it) return { ok: false, why: '菜单里没有删除' };
    it.click();
    return { ok: true };
  });
  await page.waitForTimeout(1400);
  out.dialog = await page.evaluate(() => {
    const dlg = [...document.querySelectorAll('.mantine-Modal-content, [role="dialog"]')]
      .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
      .find((el) => /确定删除/.test(el.innerText || ''));
    if (!dlg) return { ok: false, why: '没有确认框（节点删除本来就没有确认）' };
    return { ok: true, text: (dlg.innerText || '').replace(/\s+/g, ' ').slice(0, 140) };
  });
  await page.waitForTimeout(2000);
}
out.after = { rows: await rowsNow(), count: (await inDrawer(`const m=((d.innerText||'').match(/共 (\\d+) 节点/)||[])[1]; return m?Number(m):null;`)) };
out.afterNames = (out.after.rows || []).map((r) => r.name);
out.gone = !out.afterNames.includes(MINE);
out.matchesBase11 = JSON.stringify([...out.afterNames].sort()) === JSON.stringify([...BASE_11].sort());
await shot(page, 'M-299-特效卡片-加进来的节点已清理.png', { clip: { x: 0, y: 80, width: 420, height: 460 } });

await writeFile(resolve(HERE, '.evidence/cc6-cleanup.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ target: out.target, opened: out.opened, menu: out.menu, delClicked: out.delClicked, dialog: out.dialog, afterCount: out.after.count, afterNames: out.afterNames, gone: out.gone, matchesBase11: out.matchesBase11 }, null, 2));
await browser.close();
