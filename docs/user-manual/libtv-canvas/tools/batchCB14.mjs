// Batch CB-14：CB13 刷新后看不到 `CB12临时文件夹`。
// ⭐ 但**不能就此读成「没存住」** —— 它可能只是**折叠着**没渲染。阴性与「没找到」长得一样。
// 这一步用**两条独立路径**交叉验证：① 展开抽屉里的树；② 打开「管理」弹窗看资产库文件夹列表。
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

out.t0 = await inDrawer(`return (d.innerText||'').replace(/\\s+/g,' ').slice(0,300);`);

// —— 路径①：dump 行的真实结构，找展开箭头 ——
out.rowStruct = await inDrawer(`
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const own = (el) => [...el.childNodes].filter((n)=>n.nodeType===3).map((n)=>n.textContent.trim()).filter(Boolean).join(' ');
  const out2 = [];
  for (const el of d.querySelectorAll('*')) {
    if (!vis(el) || !el.querySelector('[aria-label="更多操作"]')) continue;
    const r = el.getBoundingClientRect();
    if (r.height < 10) continue;
    out2.push({ tag: el.tagName, own: own(el), y: Math.round(r.y), h: Math.round(r.height),
      cls: (el.className?.toString?.()||'').slice(0,60),
      kids: [...el.querySelectorAll('button,svg,[role="button"]')].slice(0,6).map((k) => (k.getAttribute('aria-label') || k.tagName) ) });
  }
  return out2.slice(0, 10);`);

// 尝试点第一行前面的箭头（x 最小的可点元素）
out.expanded = await inDrawer(`
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const own = (el) => [...el.childNodes].filter((n)=>n.nodeType===3).map((n)=>n.textContent.trim()).filter(Boolean).join(' ');
  const row = [...d.querySelectorAll('*')].find((el) => vis(el) && own(el) === '待分类资产' && el.querySelector('[aria-label="更多操作"]'));
  if (!row) return { ok:false, why:'没找到待分类资产行' };
  const rr = row.getBoundingClientRect();
  // 行内 x 最靠左的可点元素（展开箭头）
  const cands = [...row.querySelectorAll('button,[role="button"],svg')].filter(vis)
    .map((k) => ({ k, r: k.getBoundingClientRect() })).sort((a,b)=>a.r.x-b.r.x);
  if (!cands.length) return { ok:false, why:'行内没有可点元素', rowY: Math.round(rr.y) };
  cands[0].k.click();
  return { ok:true, rowY: Math.round(rr.y), clickedX: Math.round(cands[0].r.x) };`);
await page.waitForTimeout(1500);
out.t1_afterExpand = await inDrawer(`return (d.innerText||'').replace(/\\s+/g,' ').slice(0,300);`);
out.foundInDrawer = (out.t1_afterExpand || '').includes(MY_FOLDER);
await shot(page, 'M-294-资产页-展开待分类资产.png', { clip: { x: 0, y: 80, width: 700, height: 420 } });

// —— 路径②：「管理」弹窗里的资产库文件夹列表 ——
out.manageClicked = await inDrawer(`
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const b = [...d.querySelectorAll('[aria-label="资产管理"]')].filter(vis)[0];
  if (!b) return { ok:false, why:'没有管理按钮' };
  const r = b.getBoundingClientRect();
  b.click();
  return { ok:true, box:[Math.round(r.x),Math.round(r.y)] };`);
await page.waitForTimeout(1800);
out.manageModal = await page.evaluate((name) => {
  const m = [...document.querySelectorAll('.mantine-Modal-content, [role="dialog"]')]
    .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .find((el) => /资产库|资产分类|新建/.test(el.innerText || '') && el.innerText.length < 3000);
  if (!m) return { ok:false, why:'没弹管理弹窗' };
  return { ok:true, text: (m.innerText||'').replace(/\s+/g,' ').slice(0,700),
    has: (m.innerText||'').includes(name) };
}, MY_FOLDER);
await shot(page, 'M-295-资产管理弹窗-文件夹列表.png', { clip: { x: 60, y: 60, width: 1320, height: 700 } });

await writeFile(resolve(HERE, '.evidence/cb14-verify.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ t0: out.t0, rowStruct: out.rowStruct?.slice(0,3), expanded: out.expanded, t1: out.t1_afterExpand, foundInDrawer: out.foundInDrawer, manageModal: out.manageModal }, null, 2));
await browser.close();
