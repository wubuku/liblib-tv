// Batch CB-1：接着上一步。CB-0 已经坐实：
//   画布页签的「更多操作」只有 4 项（重命名/复制/添加到Agent/删除），
//   `移动到 ›` 根本不在这一页 —— ⭐ 我上轮记的「资产行 8 项菜单」是**资产**页签的。
// 这一步只做定位：找出「画布 / 资产」两个页签的可点元素，并 dump 资产行。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';

const URL = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

const { browser, page } = await launch();
await open(page, URL);
await closePromos(page);

const out = {};

// 开抽屉
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
    .map((el) => ({ el, r: el.getBoundingClientRect() }))
    .filter((c) => c.r.x < 100)
    .sort((a, b) => a.r.x - b.r.x)[0]?.el.click();
});
await page.waitForTimeout(1500);

// 找「画布 / 资产」页签：按 innerText 精确匹配，向上找最近的可点祖先
out.tabCandidates = await page.evaluate(() => {
  const d = document.querySelector('.mantine-Drawer-content');
  if (!d) return { err: 'no drawer' };
  const res = [];
  for (const label of ['资产', '画布']) {
    const nodes = [...d.querySelectorAll('*')].filter((el) => {
      const t = (el.innerText || '').trim();
      return t === label && el.children.length <= 2;
    });
    for (const n of nodes) {
      const path = [];
      let cur = n;
      for (let i = 0; i < 4 && cur; i += 1) {
        const r = cur.getBoundingClientRect();
        path.push({
          tag: cur.tagName,
          role: cur.getAttribute('role'),
          cls: (cur.className?.toString?.() || '').slice(0, 60),
          x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
        });
        cur = cur.parentElement;
      }
      res.push({ label, path });
    }
  }
  return res;
});

// 逐个试：点那个 y 最小、宽像标签的祖先
out.tabClickTried = [];
for (const cand of out.tabCandidates?.[0]?.path?.slice(1) ?? []) {
  const ok = await page.evaluate((sel) => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const d = document.querySelector('.mantine-Drawer-content');
    if (!d) return null;
    const el = [...d.querySelectorAll('*')].filter((e) => {
      const r = e.getBoundingClientRect();
      return Math.abs(r.x - sel.x) < 3 && Math.abs(r.y - sel.y) < 3 && r.width > 0;
    })[0];
    if (!el) return null;
    el.click();
    return { tag: el.tagName, cls: (el.className?.toString?.() || '').slice(0, 50) };
  }, cand);
  await page.waitForTimeout(1100);
  const txt = await page.evaluate(() => {
    const d = document.querySelector('.mantine-Drawer-content');
    return d ? (d.innerText || '').replace(/\s+/g, ' ').slice(0, 260) : null;
  });
  out.tabClickTried.push({ cand, ok, txt });
  if (txt && /资产/.test(txt) && !/所有评级/.test(txt)) break;
}

console.log(JSON.stringify(out, null, 2));
await browser.close();
