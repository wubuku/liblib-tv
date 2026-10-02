// Batch CC-5：⭐⭐ 核实并清理。
//
// 上一轮（CC-4）点了一张特效卡片 → 广场关闭 + 右下角 toast「素材·特效·小蜜蜂运镜…」。
// 而 CC-2 当时读 `.react-flow__node` 得出的结论是「节点一个没多」。
// ⭐⭐ **那是判据的错，不是事实**：`.react-flow__node` **只渲染视口内的节点** ——
//   落点在视口外的新节点根本不在这个列表里。「没多」是判据看不到，不是没多。
//   （同一条早已写进本手册：「真实数量读抽屉的『共 N 节点』」。）
//
// 这一步：① 用抽屉计数当基准，找出本轮多出来的节点；② **只按那个新 id 删**；③ 复核计数复原。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const KNOWN = ['a-CUfJfmKzUJ', 'a-THmbuJXQj4', 'b-mfkcQNULC3', 'i-9nlG6HdjK2', 'i-sODTbgLUm1',
  'n-56F19pXVB4', 't-2AK3Ukyxj3', 't-UtVx3lZmrV', 'v-eMpqKtiLlx', 'v-oZNpH99MtM', 'v-v2hlWY4Br3'];

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

const openDrawer = async () => {
  const has = await inDrawer('return 1;');
  if (typeof has === 'number') return;
  await page.evaluate(() => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const c = [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
      .map((el) => ({ el, r: el.getBoundingClientRect() })).filter((o) => o.r.x < 100).sort((a, b) => a.r.x - b.r.x);
    c[0]?.el.click();
  });
  await page.waitForTimeout(1700);
};

await openDrawer();
out.baseline = await inDrawer(`
  const t = (d.innerText||'').replace(/\\s+/g,' ');
  const m = t.match(/共 (\\d+) 节点/);
  const rows = [...d.querySelectorAll('[aria-label="更多操作"]')].length;
  return { count: m ? Number(m[1]) : null, text: t.slice(0, 400), moreBtns: rows };`);

// 抽屉能列出**每一行**的 data-id 吗？「定位到节点」那枚按钮上应该带着 id
out.rowIds = await inDrawer(`
  const out2 = [];
  for (const b of d.querySelectorAll('button,[role="button"]')) {
    const r = b.getBoundingClientRect();
    if (r.width < 1) continue;
    const ds = Object.entries(b.attributes).filter(([k]) => k.startsWith('data-') || k === 'id').map(([k,v]) => k+'='+v);
    out2.push({ aria: b.getAttribute('aria-label'), text: (b.innerText||'').trim().slice(0,14), ds, box: [Math.round(r.x), Math.round(r.y)] });
  }
  return out2.slice(0, 24);`);

await writeFile(resolve(HERE, '.evidence/cc5-baseline.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ baseline: out.baseline, rowIds: out.rowIds }, null, 2).slice(0, 3000));
await browser.close();
