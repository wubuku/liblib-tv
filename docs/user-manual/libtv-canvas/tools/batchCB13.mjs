// Batch CB-13：**清理**本轮建的那个文件夹，并且要能自证「删的是它、不是待分类资产」。
//
// ⛔ 上一轮的危险读数：我在自己那一行点了「更多操作 → 删除」，弹出的确认框却写着
//    「确定删除「待分类资产」吗？」—— **行认错了**。所幸我**没有点对话框里的「删除」**，
//    浏览器随即关闭，所以什么都没删。这跟 CA 那次误删是同一族错误的**第二次**预警。
//
// 本轮的防线（三道）：
//   ① 认行：只认**自身文字恰好是** CB12临时文件夹、且**自己身上**带 更多操作 的那个元素
//      —— 不用「带这个文字的任意祖先」，祖先会把父行一起框进来。
//   ② 认菜：点开菜单后，先记下菜单的 y 落点，和那一行的 y 比；差太远就当没点开。
//   ③ 认框：**点删除之后先读确认框的文字**，里面必须逐字出现 CB12临时文件夹，
//      否则立刻按「取消」，绝不多点一下。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MY_FOLDER = 'CB12临时文件夹';

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
await page.waitForTimeout(900);

const inDrawer = (fnBody) => page.evaluate(`(() => {
  const d = [...document.querySelectorAll('.mantine-Drawer-content')]
    .filter((x) => { const r = x.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .find((x) => [...x.querySelectorAll('button')].some((b) => ['画布','资产'].includes((b.innerText||'').trim())));
  if (!d) return { __err: 'asset drawer not found' };
  ${fnBody}
})()`);

await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const has = [...document.querySelectorAll('.mantine-Drawer-content')].filter(vis)
    .some((d) => [...d.querySelectorAll('button')].some((b) => ['画布', '资产'].includes((b.innerText || '').trim())));
  if (has) return;
  const c = [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
    .map((el) => ({ el, r: el.getBoundingClientRect() })).filter((o) => o.r.x < 100).sort((a, b) => a.r.x - b.r.x);
  c[0]?.el.click();
});
await page.waitForTimeout(1600);
await inDrawer(`[...d.querySelectorAll('button')].find((b)=>(b.innerText||'').trim()==='资产')?.click(); return 1;`);
await page.waitForTimeout(1600);

out.t0 = await inDrawer(`return (d.innerText||'').replace(/\\s+/g,' ').slice(0,240);`);

// —— ① 认行：dump 每个「自身文字 + 是否自带 更多操作」+ y ——
out.rows = await inDrawer(`
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const own = (el) => [...el.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent.trim()).filter(Boolean).join(' ');
  return [...d.querySelectorAll('*')].filter((el) => vis(el) && own(el) && el.querySelector('[aria-label="更多操作"]'))
    .map((el) => {
      const r = el.getBoundingClientRect();
      return { tag: el.tagName, own: own(el), y: Math.round(r.y), cls: (el.className?.toString?.() || '').slice(0, 50) };
    }).slice(0, 20);`);

// —— ② 点开**自己那一行**的更多操作 ——
out.clicked = await inDrawer(`
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const own = (el) => [...el.childNodes].filter((n)=>n.nodeType===3).map((n)=>n.textContent.trim()).filter(Boolean).join(' ');
  const row = [...d.querySelectorAll('*')].find((el) => vis(el) && own(el) === ${JSON.stringify(MY_FOLDER)} && el.querySelector('[aria-label="更多操作"]'));
  if (!row) return { ok: false, why: '没找到自己那一行' };
  const rr = row.getBoundingClientRect();
  row.querySelector('[aria-label="更多操作"]').click();
  return { ok: true, rowY: Math.round(rr.y) };`);
await page.waitForTimeout(1000);

// —— ③ 认菜：菜单 y 应当贴着那一行 ——
out.menu = await page.evaluate((rowY) => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const dd = [...document.querySelectorAll('.mantine-Menu-dropdown')].filter(vis);
  if (!dd.length) return { ok: false, why: '菜单没开' };
  const r = dd[dd.length - 1].getBoundingClientRect();
  return { ok: true, top: Math.round(r.y), rowY, items: [...dd[dd.length - 1].querySelectorAll('.mantine-Menu-item,[role="menuitem"]')].map((e) => (e.innerText || '').trim()) };
}, out.clicked.rowY ?? 999);
await shot(page, 'M-294-资产页-临时文件夹-删除前.png', { clip: { x: 0, y: 80, width: 700, height: 420 } });

// —— ④ 点「删除」，**先读确认框文字** ——
out.deleteClicked = await page.evaluate(() => {
  const it = [...document.querySelectorAll('.mantine-Menu-item, [role="menuitem"]')]
    .find((el) => (el.innerText || '').trim() === '删除');
  if (!it) return { ok: false, why: '菜单里没有删除' };
  it.click();
  return { ok: true };
});
await page.waitForTimeout(1200);
out.dialog = await page.evaluate(() => {
  const d = [...document.querySelectorAll('.mantine-Modal-content, [role="dialog"]')]
    .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .find((el) => /确定删除/.test(el.innerText || ''));
  if (!d) return { ok: false, why: '没弹确认框' };
  return { ok: true, text: (d.innerText || '').replace(/\s+/g, ' ').slice(0, 160),
    btns: [...d.querySelectorAll('button')].map((b) => (b.innerText || '').trim()).filter(Boolean) };
});
out.dialogNamesMine = !!out.dialog.ok && out.dialog.text.includes(MY_FOLDER);

// ⛔ 守卫：确认框没写我的名字，就按「取消」，什么都不删
if (out.dialogNamesMine) {
  await page.evaluate((name) => {
    const d = [...document.querySelectorAll('.mantine-Modal-content, [role="dialog"]')]
      .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
      .find((el) => (el.innerText || '').includes(name) && /确定删除/.test(el.innerText || ''));
    if (!d) return;
    const b = [...d.querySelectorAll('button')].find((x) => (x.innerText || '').trim() === '删除');
    if (b) b.click();
  }, MY_FOLDER);
  await page.waitForTimeout(1500);
  out.confirmed = true;
} else {
  await page.evaluate(() => {
    const d = [...document.querySelectorAll('.mantine-Modal-content, [role="dialog"]')]
      .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
      .find((el) => /确定删除/.test(el.innerText || ''));
    if (!d) return;
    const b = [...d.querySelectorAll('button')].find((x) => (x.innerText || '').trim() === '取消');
    if (b) b.click();
  });
  await page.waitForTimeout(900);
  out.confirmed = false;
  out.abortedBecauseDialogNamedOtherRow = true;
}
out.t1 = await inDrawer(`return (d.innerText||'').replace(/\\s+/g,' ').slice(0,240);`);
out.stillThere = (out.t1 || '').includes(MY_FOLDER);

await writeFile(resolve(HERE, '.evidence/cb13-cleanup.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ rows: out.rows, clicked: out.clicked, menu: out.menu, dialog: out.dialog, dialogNamesMine: out.dialogNamesMine, confirmed: out.confirmed, t1: out.t1, stillThere: out.stillThere }, null, 2));
await browser.close();
