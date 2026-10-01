// 探针 10 —— 只读核对专用测试项目当前到底有几张画布、分别叫什么。
//
// 为什么要专门查：batchA3 里「重命名后」读到的行列表从 2 行变成 1 行，而且新名字
// 既不是「画布 1」也不是我填的「手册取证画布」。这里不猜，直接把下拉完整 HTML 和
// 网络上的项目状态一起读出来，判断到底是「画布真没了」还是「读数时机不对」。
import { launch, open } from './lib.mjs';
import { CANVAS_URL, TEST } from './test-project.mjs';
import { clearToasts, closePromos, shot } from './scenario.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const { browser, page } = await launch();
const apis = [];

try {
  page.on('response', async (r) => {
    const u = r.url();
    if (/\/api\//.test(u) && !/\.(js|css|png|svg|woff2?)/.test(u)) {
      apis.push({ status: r.status(), method: r.request().method(), path: new URL(u).pathname + new URL(u).search });
    }
  });

  await open(page, CANVAS_URL, { settle: 4000 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(1500);

  console.log('顶栏画布按钮文本:', await page.evaluate(() => [...document.querySelectorAll('button')].map((b) => (b.innerText || '').trim()).filter((t) => /^画布/.test(t))));
  console.log('项目名输入框值:', await page.evaluate(() => document.querySelector('input[aria-label="项目名称"]')?.value));

  await openDropdown(page, 1200);
  await page.waitForTimeout(1200);
  const dump = await page.evaluate(() => {
    const d = document.querySelector('.mantine-Popover-dropdown');
    if (!d) return { none: true };
    const r = d.getBoundingClientRect();
    return {
      rect: [Math.round(r.width), Math.round(r.height)],
      rows: [...d.querySelectorAll('button[aria-label^="切换到画布 "]')].map((b) => ({
        label: b.getAttribute('aria-label'),
        text: (b.innerText || '').trim(),
        cls: (b.className || '').toString().slice(0, 80),
      })),
      fullText: (d.innerText || '').replace(/\s+/g, ' '),
      scrollH: d.querySelector('.mantine-ScrollArea-viewport')?.scrollHeight,
      clientH: d.querySelector('.mantine-ScrollArea-viewport')?.clientHeight,
    };
  });
  console.log('下拉状态:', JSON.stringify(dump, null, 1));

  await shot(page, 'p10-canvas-rows-state.png');

  // 直接问后端：这个项目有几张画布
  const info = await page.evaluate(async (t) => {
    const paths = [
      `/api/canvas/project/detail?projectId=${t.projectId}`,
      `/api/canvas/project/canvasList?projectId=${t.projectId}`,
      `/api/canvas/project/info?projectId=${t.projectId}`,
    ];
    const out = [];
    for (const p of paths) {
      try {
        const res = await fetch(p, { credentials: 'include' });
        const txt = await res.text();
        out.push({ p, status: res.status, body: txt.slice(0, 400) });
      } catch (e) { out.push({ p, err: String(e).slice(0, 80) }); }
    }
    return out;
  }, TEST);
  console.log('\n=== 后端探测 ===');
  for (const i of info) console.log(JSON.stringify(i));

  console.log('\n=== 捕获到的 API 调用 ===');
  for (const a of apis.slice(-25)) console.log(`  ${a.status} ${a.method} ${a.path}`);
} finally {
  await browser.close();
}
