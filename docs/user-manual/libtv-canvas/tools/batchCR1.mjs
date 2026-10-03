// Batch CR-1：全页枚举产品自己的功能标记属性。
//
// ⭐ CR-0 的发现：这枚「预设」按钮带着 `data-feature-id="generator:preset-menu"`，
// 另外两枚带着 `data-practice-generator-lock`。**这是产品自己贴的功能标签**，
// 而我此前认控件只靠 aria-label / 悬停气泡 / 图标 path 三招，从没看过这些属性。
//
// 本步：把画布（以及几个已���面板）里所有 `data-feature-id` / `data-practice-*`
// 逐个列出来 —— 认控件的可靠手段，也许不止一种。
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
const read = (page, id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return { 在: false };
  const fold = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
  return { 在: true, 选中: n.classList.contains('selected'), 折叠钮: !!fold };
}, id);
// ⭐ 全页枚举：所有 data-* 里带 feature / practice / anchor / anchor-key 的
const tags = (page, 标签) => page.evaluate((tag) => {
  const out = [];
  const seen = new Set();
  for (const e of document.querySelectorAll('body *')) {
    for (const a of e.attributes) {
      if (!a.name.startsWith('data-')) continue;
      if (!new RegExp(tag, 'i').test(a.name)) continue;
      const r = e.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      const 文字 = (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 22);
      const key = `${a.name}=${a.value}|${Math.round(r.x)},${Math.round(r.y)}`;
      if (seen.has(key)) continue;
      seen.add(key);
      out.push({
        属性: a.name, 值: (a.value || '').slice(0, 60), tag: e.tagName.toLowerCase(),
        角色: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
        文字, 可见: r.width > 0 && r.height > 0 && r.x >= 0 && r.y >= 0 && r.x < 1440 && r.y < 810,
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      });
    }
  }
  return out;
}, 标签);

const out = {};
const { browser, page } = await launch();
await boot(page);
out.促销 = await killPromo(page);

for (const [名, 标签] of [['data-feature-id', 'feature'], ['data-practice', 'practice'], ['data-anchor', 'anchor']]) {
  const t = await tags(page, 标签);
  out[名] = t;
  const 值集 = [...new Set(t.map((x) => x.值).filter(Boolean))].sort();
  console.log(`\n=== ${名}：命中 ${t.length} 个元素 / 去重后 ${值集.length} 个取值`);
  for (const v of 值集) {
    const 用在 = t.filter((x) => x.值 === v);
    console.log(`  ${v || '(空)'}  ×${用在.length}  例：<${用在[0].tag}> 「${用在[0].文字}」 ${JSON.stringify(用在[0].rect)}`);
  }
  // 顺便看看有多少是「无文字、无 aria」的 —— 那正是认不出来的那些
  const 匿名 = t.filter((x) => !x.文字 && !x.aria);
  console.log(`  其中「无文字且无 aria」的 ${匿名.length} 个：${JSON.stringify(匿名.map((x) => x.值 || x.属性)).slice(0, 300)}`);
}

// 打开大编辑器再扫一遍（对比：多了哪些标记）
{
  const s0 = (await read(page, 'i-sODTbgLUm1'));
  if (s0.在 && s0.折叠钮) {
    const fp = await page.evaluate((nid) => {
      const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const f = [...n.querySelectorAll('button')].find((b) => { const c = b.className.toString(); return c.includes('size-7') && c.includes('absolute') && c.includes('right-2') && c.includes('top-2'); });
      if (!f) return null; const r = f.getBoundingClientRect();
      for (const fy of [0.2, 0.35, 0.5, 0.65, 0.8]) for (const fx of [0.3, 0.5, 0.7]) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        const el = document.elementFromPoint(x, y);
        if (el && el.closest('button') && el.closest('button').className.toString().includes('size-7') && x < 1440 && y < 810) return [x, y];
      }
      return null;
    }, 'i-sODTbgLUm1');
    if (fp) {
      await page.mouse.click(fp[0], fp[1]);
      await page.waitForTimeout(1900);
      const 开 = await page.evaluate(() => !!([...document.body.children].find((e) => getComputedStyle(e).zIndex === '601')));
      console.log(`\n=== 打开大编辑器 = ${开}`);
      if (开) {
        for (const [名, 标签] of [['data-feature-id', 'feature'], ['data-practice', 'practice']]) {
          const t = await tags(page, 标签);
          out[`${名}_模态内`] = t.filter((x) => { const h = x.rect; return h[0] >= 320 && h[0] <= 1120 && h[1] >= 105 && h[1] <= 705; });
          console.log(`  ${名} 模态内 ${out[`${名}_模态内`].length} 个：${JSON.stringify([...new Set(out[`${名}_模态内`].map((x) => x.值))])}`);
        }
        await page.mouse.click(1360, 780);
        await page.waitForTimeout(1400);
      }
    }
  }
}

out.收尾 = await read(page, 'i-sODTbgLUm1');
console.log('\n收尾 =', JSON.stringify(out.收尾));
await browser.close();
{
  const { browser: b2, page: p2 } = await launch();
  await boot(p2);
  const ids = await p2.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')));
  out.全新会话 = { 节点: ids.length, 一致: ids.length === BASE.length && BASE.every((x) => ids.includes(x)) };
  console.log('全新会话 节点', ids.length, ' 一致 =', out.全新会话.一致);
  await b2.close();
}
await writeFile(resolve(HERE, '.evidence/cr1-feature-tags.json'), JSON.stringify(out, null, 2));
