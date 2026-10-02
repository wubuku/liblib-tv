// Batch CB-18：抽屉的文件夹树**默认折叠**，所以每次新开页面都「只有待分类资产」。
// 这一步：点开折叠箭头 → 真鼠标悬停到子文件夹那一行 → 点**同一 y 上**的 更多操作。
// ⛔ 守卫不变：确认框必须逐字写着我那个文件夹名，否则按「取消」。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MINE = ['CB12临时文件夹', 'CB15临时文件夹'];

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
const out = {};

await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.waitForTimeout(800);

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
await page.waitForTimeout(1600);
await inDrawer(`[...d.querySelectorAll('button')].find((b)=>(b.innerText||'').trim()==='资产')?.click(); return 1;`);
await page.waitForTimeout(1600);

// —— 展开折叠箭头（x 最小那枚，靠真指针） ——
out.expand = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const more = [...document.querySelectorAll('[aria-label="更多操作"]')].filter(vis)[0];
  if (!more) return { ok: false, why: '没有行' };
  const mr = more.getBoundingClientRect();
  // 箭头在同一行内、x 比 更多操作 小
  const row = more.closest('div');
  const cands = [...document.querySelectorAll('svg, button, [role="button"]')].filter(vis)
    .map((k) => ({ k, r: k.getBoundingClientRect() }))
    .filter((c) => Math.abs(c.r.y + c.r.height / 2 - (mr.y + mr.height / 2)) < 12 && c.r.x < mr.x - 20);
  if (!cands.length) return { ok: false, why: '同一行里找不到箭头', mr: [Math.round(mr.x), Math.round(mr.y)] };
  cands.sort((a, b) => a.r.x - b.r.x);
  return { ok: true, arrow: [Math.round(cands[0].r.x), Math.round(cands[0].r.y + cands[0].r.height / 2)] };
});
if (out.expand?.ok) {
  await page.mouse.move(out.expand.arrow[0], out.expand.arrow[1], { steps: 8 });
  await page.waitForTimeout(500);
  await page.mouse.click(out.expand.arrow[0], out.expand.arrow[1]);
  await page.waitForTimeout(1500);
}
out.t1 = await inDrawer(`return (d.innerText||'').replace(/\\s+/g,' ').slice(0,300);`);

const rowYs = () => inDrawer(`
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const rows = [];
  for (const el of d.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (!vis(el) || r.height < 24 || r.height > 44 || r.width < 200) continue;
    const t = (el.innerText||'').trim();
    if (!t || t.length > 20) continue;
    if (rows.some((x) => Math.abs(x.y - r.y) < 4)) continue;
    rows.push({ text: t, y: Math.round(r.y), x: Math.round(r.x) });
  }
  return rows;`);
out.rowsAfterExpand = await rowYs();
await shot(page, 'M-294-资产页-展开后的文件夹树.png', { clip: { x: 0, y: 130, width: 500, height: 260 } });

out.deletions = [];
for (const name of MINE) {
  const step = { name };
  const rows = await rowYs();
  const row = Array.isArray(rows) ? rows.find((r) => r.text === name) : null;
  step.row = row;
  if (!row) { step.skipped = '行没找到（可能已折叠或不存在）'; out.deletions.push(step); continue; }

  await page.mouse.move(150, row.y + 14, { steps: 10 });
  await page.waitForTimeout(700);
  step.moreOnRow = await page.evaluate((y) => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const m = [...document.querySelectorAll('[aria-label="更多操作"]')].filter(vis)
      .find((x) => Math.abs(x.getBoundingClientRect().y - y) < 14);
    if (!m) return { ok: false, why: '该行没有更多操作' };
    m.click();
    return { ok: true };
  }, row.y);
  await page.waitForTimeout(900);

  step.delClicked = await page.evaluate(() => {
    const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
      .find((el) => (el.innerText || '').trim() === '删除');
    if (!it) return { ok: false, why: '菜单里没有删除' };
    it.click();
    return { ok: true };
  });
  await page.waitForTimeout(1200);
  step.dialog = await page.evaluate(() => {
    const dlg = [...document.querySelectorAll('.mantine-Modal-content, [role="dialog"]')]
      .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
      .find((el) => /确定删除/.test(el.innerText || ''));
    if (!dlg) return { ok: false, why: '没弹确认框' };
    return { ok: true, text: (dlg.innerText || '').replace(/\s+/g, ' ').slice(0, 140) };
  });
  step.dialogNamesTarget = !!step.dialog?.ok && step.dialog.text.includes(name);
  if (step.dialogNamesTarget) {
    await page.evaluate((n) => {
      const dlg = [...document.querySelectorAll('.mantine-Modal-content, [role="dialog"]')]
        .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
        .find((el) => (el.innerText || '').includes(n) && /确定删除/.test(el.innerText || ''));
      if (!dlg) return;
      [...dlg.querySelectorAll('button')].find((b) => (b.innerText || '').trim() === '删除')?.click();
    }, name);
    await page.waitForTimeout(1600);
    step.confirmed = true;
  } else {
    await page.evaluate(() => {
      const dlg = [...document.querySelectorAll('.mantine-Modal-content, [role="dialog"]')]
        .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
        .find((el) => /确定删除/.test(el.innerText || ''));
      if (!dlg) return;
      [...dlg.querySelectorAll('button')].find((b) => (b.innerText || '').trim() === '取消')?.click();
    });
    await page.waitForTimeout(900);
    step.confirmed = false;
  }
  const after = await inDrawer(`return (d.innerText||'').replace(/\\s+/g,' ').slice(0,300);`);
  step.after = after;
  step.gone = typeof after === 'string' ? !after.includes(name) : null;
  out.deletions.push(step);
}

out.final = await inDrawer(`return (d.innerText||'').replace(/\\s+/g,' ').slice(0,300);`);
await writeFile(resolve(HERE, '.evidence/cb18-cleanup.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ expand: out.expand, t1: out.t1, rowsAfterExpand: out.rowsAfterExpand, deletions: out.deletions, final: out.final }, null, 2));
await browser.close();
