// Batch DO-1：在页面加载的 JS chunk 里搜 `z-[180]` / `z-[305]`，看它们属于哪个组件。
//
// 背景：DG 批次已坐实这两个 z 值**从基线起就一直都在**（问题不是「什么时候亮」），
//   但**累计排除了 14 种状态**都没找到对应功能。
// 换层面：DG 只翻过 DOM 祖先链和内嵌 payload，**从没去翻 JS 源码**。
//
// ⭐ 思路：Tailwind 的 `z-[180]` 编译后是 `z-index:180`，class 名会留在 chunk 字符串里。
//   定位到 chunk 与命中点，再看命中点附近的中文文案 ⇒ 推断它属于哪个组件。
//
// ⭐ 方法纪律：只**只读**地下载已经加载的脚本，不执行任何额外代码。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile, mkdir, readdir } from 'node:fs/promises';
import { join } from 'node:path';

const CACHE = '/tmp/libtv-chunks';
await mkdir(CACHE, { recursive: true });
const out = { 命中: [], 统计: {} };
const LOG = console.log;

const { browser, page } = await launch();
await open(page, `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`);
await closePromos(page);
await page.waitForTimeout(6000);

const allUrl = await page.evaluate(() => [...new Set([
  ...[...document.querySelectorAll('script[src]')].map((s) => s.src),
  ...performance.getEntriesByType('resource').map((e) => e.name),
].filter((u) => /\.js(\?|$)/.test(u)))]);
LOG(`页面 JS 资源 ${allUrl.length} 个`);

const 目标 = ['z-[180]', 'z-[305]'];
let 下过 = 0; let 跳过的 = 0;
for (const u of allUrl) {
  try {
    const r = await page.request.get(u, { timeout: 30000 });
    if (!r.ok()) { 跳过的 += 1; continue; }
    const t = await r.text();
    if (!t) { 跳过的 += 1; continue; }
    下过 += 1;
    const name = u.split('/').pop().split('?')[0].slice(0, 60) || `chunk${下过}.js`;
    await writeFile(join(CACHE, `${name}`), t);
    for (const key of 目标) {
      let i = t.indexOf(key);
      if (i === -1) continue;
      const 处 = [];
      let 次 = 0;
      while (i !== -1 && 次 < 8) {
        处.push({ 偏移: i, 上下文: t.slice(Math.max(0, i - 500), Math.min(t.length, i + 500)).replace(/\s+/g, ' ') });
        i = t.indexOf(key, i + 1);
        次 += 1;
      }
      out.命中.push({ chunk: name, 键: key, 长度: t.length, 出现次数: 处.length, 处 });
      LOG(`\n⭐ ${name}（${(t.length / 1024).toFixed(0)}KB）命中 ${key} × ${处.length}`);
      for (const [n, c] of 处.slice(0, 4).entries()) LOG(`  --- 第 ${n + 1} 处 ---\n  ${c.上下文.slice(0, 900)}`);
    }
  } catch { 跳过的 += 1; }
}
out.统计 = { 资源数: allUrl.length, 下载成功: 下过, 失败跳过: 跳过的, 命中chunk数: out.命中.length };
LOG(`\n=== 资源 ${allUrl.length} 个：下载成功 ${下过}，跳过 ${跳过的}；命中 chunk ${out.命中.length} ===`);
await writeFile(new URL('./batchDO1.json', import.meta.url), JSON.stringify(out, null, 2));
await browser.close();
LOG(`缓存目录: ${CACHE}`);
LOG('=== 已写 tools/batchDO1.json ===');
