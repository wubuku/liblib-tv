// Batch CB-5：截图里明明浮出了「📁 个人资产库」，我的读数函数却报「还是 8 项」。
// ⭐ 第三次踩同一条：读数为 0 先问判据有没有挡住。这次数组里有元素，只是**不叫** `.mantine-Menu-item`。
// 这一步只做一件事：把那个子菜单的**真实结构** dump 出来，换掉错的判据。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);

const out = {};
await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
    .map((el) => ({ el, r: el.getBoundingClientRect() }))
    .filter((c) => c.r.x < 100).sort((a, b) => a.r.x - b.r.x)[0]?.el.click();
});
await page.waitForTimeout(1500);
await page.evaluate(() => {
  const d = document.querySelector('.mantine-Drawer-content');
  [...d.querySelectorAll('button')].find((b) => (b.innerText || '').trim() === '资产')?.click();
});
await page.waitForTimeout(1500);
await page.evaluate(() => {
  const d = document.querySelector('.mantine-Drawer-content');
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...d.querySelectorAll('[aria-label="更多操作"]')].filter(vis)[0]?.click();
});
await page.waitForTimeout(900);
await page.mouse.move(200, 300, { steps: 6 });
await page.mouse.move(130 + 83, 379 + 18, { steps: 12 });
await page.waitForTimeout(1300);

// 找「个人资产库」所在的那块浮层：它是**兄弟**容器，不在主菜单 DOM 里
out.submenuReal = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  // 所有浮层容器（Mantine Popover/Dropdown/Menu 的 root）
  const floats = [...document.querySelectorAll('[data-portal], .mantine-Popover-dropdown, .mantine-Menu-dropdown, .mantine-Popover-root')]
    .filter(vis)
    .map((el) => {
      const r = el.getBoundingClientRect();
      return {
        cls: (el.className?.toString?.() || '').slice(0, 80),
        box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        text: (el.innerText || '').replace(/\s+/g, ' ').slice(0, 120),
      };
    })
    .filter((f) => f.text);
  // 「个人资产库」这个文本节点自己
  const lib = [...document.querySelectorAll('*')].find((el) => (el.innerText || '').trim() === '个人资产库' && el.children.length === 0);
  const chain = [];
  let cur = lib;
  for (let i = 0; i < 6 && cur; i += 1) {
    const r = cur.getBoundingClientRect();
    chain.push({
      tag: cur.tagName, role: cur.getAttribute('role'),
      aria: cur.getAttribute('aria-label'),
      data: Object.entries(cur.attributes).filter(([k]) => k.startsWith('data-')).map(([k, v]) => `${k}=${v}`).join(','),
      cls: (cur.className?.toString?.() || '').slice(0, 80),
      box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      kids: cur.children.length,
    });
    cur = cur.parentElement;
  }
  return { floats, chain };
});

out.allsameText = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  return [...document.querySelectorAll('*')].filter((el) => vis(el) && (el.innerText || '').trim() === '个人资产库')
    .map((el) => ({ tag: el.tagName, cls: (el.className?.toString?.() || '').slice(0, 60), kids: el.children.length }));
});

await shot(page, 'M-292-资产页-移动到子菜单.png', { clip: { x: 0, y: 150, width: 900, height: 420 } });
await writeFile(resolve(HERE, '.evidence/cb5-submenu-real.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ floats: out.submenuReal.floats.length, chain: out.submenuReal.chain.slice(0, 3) }, null, 2));
await browser.close();
