// Batch CB-17：CB16 的三道防线**两次都拦住了**（确认框写的都是「待分类资产」，不是我要删的那行）——
//    什么都没删，待分类资产 安全。这已经是一次成功的「差点误删」预警。
//
// ⭐ 但为什么点子文件夹的「更多操作」，弹出的确认框却写父级的名字？
//    猜：行是**虚拟列表**，整列共用一组 更多操作 按钮，按的是「第几个」而不是「哪一行」。
//    这轮用**真鼠标先悬停到那一行的 y 上**，让界面自己知道「当前操作的是哪一行」，
//    再点**同一个 y 上**的 更多操作。
// ⛔ 守卫不变：点删除后先读确认框，对不上我的文件夹名就按取消。
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

const ensureOpen = async () => {
  const has = await inDrawer('return 1;');
  if (typeof has === 'number') return;
  await page.evaluate(() => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const c = [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
      .map((el) => ({ el, r: el.getBoundingClientRect() })).filter((o) => o.r.x < 100).sort((a, b) => a.r.x - b.r.x);
    c[0]?.el.click();
  });
  await page.waitForTimeout(1600);
  await inDrawer(`[...d.querySelectorAll('button')].find((b)=>(b.innerText||'').trim()==='资产')?.click(); return 1;`);
  await page.waitForTimeout(1600);
};

await ensureOpen();

// —— dump 每一行：文字 + y + 该行上所有 更多操作 的 y ——
out.rows = await inDrawer(`
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const list = [...d.querySelectorAll('*')].filter((el) => {
    const r = el.getBoundingClientRect();
    return vis(el) && r.height >= 24 && r.height <= 44 && r.width > 200;
  });
  const rows = [];
  for (const el of list) {
    const t = (el.innerText||'').trim();
    if (!t || t.length > 20) continue;
    const r = el.getBoundingClientRect();
    if (rows.some((x) => Math.abs(x.y - r.y) < 4)) continue;
    const mores = [...d.querySelectorAll('[aria-label="更多操作"]')].filter(vis)
      .map((m) => Math.round(m.getBoundingClientRect().y))
      .filter((y) => Math.abs(y - r.y) < 14);
    rows.push({ text: t, y: Math.round(r.y), x: Math.round(r.x), moreY: mores });
  }
  return rows;`);

out.deletions = [];
for (const name of MINE) {
  const step = { name };
  await ensureOpen();
  const rowsNow = await inDrawer(`
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const list = [...d.querySelectorAll('*')].filter((el) => {
      const r = el.getBoundingClientRect();
      return vis(el) && r.height >= 24 && r.height <= 44 && r.width > 200;
    });
    const rows = [];
    for (const el of list) {
      const t = (el.innerText||'').trim();
      if (!t || t.length > 20) continue;
      const r = el.getBoundingClientRect();
      if (rows.some((x) => Math.abs(x.y - r.y) < 4)) continue;
      rows.push({ text: t, y: Math.round(r.y) });
    }
    return rows;`);
  const row = Array.isArray(rowsNow) ? rowsNow.find((r) => r.text === name) : null;
  step.row = row;
  if (!row) { step.skipped = '行没找到'; out.deletions.push(step); continue; }

  // ⭐ 真鼠标先悬停到那一行
  await page.mouse.move(150, row.y + 14, { steps: 10 });
  await page.waitForTimeout(700);
  step.moreOnRow = await page.evaluate((y) => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const m = [...document.querySelectorAll('[aria-label="更多操作"]')].filter(vis)
      .find((x) => Math.abs(x.getBoundingClientRect().y - y) < 14);
    if (!m) return { ok: false };
    const r = m.getBoundingClientRect();
    m.click();
    return { ok: true, box: [Math.round(r.x), Math.round(r.y)] };
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

await ensureOpen();
out.final = await inDrawer(`return (d.innerText||'').replace(/\\s+/g,' ').slice(0,300);`);
await shot(page, 'M-294-资产页-清理之后.png', { clip: { x: 0, y: 80, width: 700, height: 420 } });
await writeFile(resolve(HERE, '.evidence/cb17-cleanup.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ rows: out.rows, deletions: out.deletions, final: out.final }, null, 2));
await browser.close();
