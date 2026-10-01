// 探针 07b —— 快捷键面板：**按列 + 按行容器**精确读，并把 ⌘ 这类图标键帽读进来。
//
// p07 第一版犯的三个错，这一版逐个堵掉：
//   1. 只按 y 聚行 → 四列并排的行被压平，列归属丢失；
//   2. 只取 innerText → ⌘ / 手势图标是**图形键帽**，没有文本，整列前缀全丢
//      （于是「移动 V」看不出前面其实还有 ⌘ 列）；
//   3. 没关右侧 TV Director 抽屉 → 第四列「其他」被抽屉挡住，删除项的键位根本没读到。
//
// 做法：先关抽屉拿到完整四列；再用行容器的子元素顺序还原「动作 + 键位序列」；
// 键帽同时输出文本与 aria-label/title，图形键帽靠 aria/title 认。
import { launch, open, closePromos, shot } from './lib.mjs';
import { CANVAS_URL } from './test-project.mjs';

const { browser, page } = await launch();

try {
  await open(page, CANVAS_URL, { settle: 3500 });
  await closePromos(page);
  for (const n of ['关闭浏览器通知提示', '知道了']) {
    const b = page.getByRole('button', { name: n, exact: true });
    if (await b.count()) await b.first().click({ timeout: 2000 }).catch(() => {});
  }
  await page.waitForTimeout(500);

  // 关掉 TV Director 抽屉，把右侧让出来。
  const closeDrawer = page.getByRole('button', { name: '关闭', exact: true });
  if (await closeDrawer.count()) { await closeDrawer.first().click({ timeout: 3000 }).catch(() => {}); await page.waitForTimeout(600); }
  console.log('drawer closed, remaining 关闭 buttons:', await closeDrawer.count());

  await page.getByRole('button', { name: '快捷键', exact: true }).click();
  await page.waitForTimeout(1500);

  const data = await page.evaluate(() => {
    const hosts = [...document.querySelectorAll('div')].filter((el) => {
      const r = el.getBoundingClientRect();
      return r.width > 500 && r.height > 250 && /成组/.test(el.innerText || '');
    });
    const host = hosts[hosts.length - 1];
    if (!host) return { error: 'no host' };
    const hostRect = host.getBoundingClientRect();

    // 键帽识别：Mantine 的 kbd 或任何带边框的小方块。
    const isKey = (el) => {
      const t = (el.tagName || '').toLowerCase();
      if (t === 'kbd') return true;
      const s = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return r.width >= 16 && r.width <= 46 && r.height >= 16 && r.height <= 34 && s.borderRadius !== '0px';
    };
    const keyText = (el) => {
      const t = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
      return t || el.getAttribute('aria-label') || el.getAttribute('title') || (el.querySelector('svg,img') ? '[图标]' : '');
    };

    // 找行容器：包含至少一个标签 + 一个键帽，且高度 < 70 的重复块。
    const leaves = [...host.querySelectorAll('*')].filter((el) => !el.children.length && (el.textContent || '').trim());
    const rowEls = [...host.querySelectorAll('div')].filter((el) => {
      const r = el.getBoundingClientRect();
      if (r.height < 20 || r.height > 70 || r.width > hostRect.width) return false;
      if (!/成组|合并|解组|连线|复制|生成|新建节点|节点复制|创建副本|放大|缩小|适应画布|触控板|鼠标|键盘|移动|抓手工具|整理画布|撤销|重做|画布节点搜索|删除/.test(el.innerText || '')) return false;
      return !el.parentElement || [...el.parentElement.children].filter((c) => c.getBoundingClientRect().height >= 20 && c.getBoundingClientRect().height <= 70 && /成组|放大|键盘|撤销|合并|缩小|触控板|重做|解组|适应画布|鼠标|画布节点搜索|连线|移动|删除|复制节点|抓手工具|生成|整理画布|新建节点|节点复制|创建副本/.test(c.innerText || '')).length > 1;
    });
    const uniq = [];
    const seen = new Set();
    for (const el of rowEls) {
      const key = el.innerText.replace(/\s+/g, '|');
      if (seen.has(key)) continue;
      seen.add(key);
      const r = el.getBoundingClientRect();
      const keys = [...el.querySelectorAll('*')].filter(isKey).map(keyText).filter(Boolean);
      const label = (el.innerText || '').replace(/\s+/g, ' ').replace(/⌘|⇧|⌥|⇥|⌃|\+|G|L|D|Z|F|Tab|Enter|Space|V|H|0|[+−]/g, ' ').trim();
      uniq.push({ x: Math.round(r.x), y: Math.round(r.y), label, keys, raw: (el.innerText || '').replace(/\s+/g, ' ').trim(), nKeys: keys.length });
    }
    uniq.sort((a, b) => a.x - b.x || a.y - b.y);

    // 按 x 聚成列
    const cols = [];
    for (const r of uniq) {
      let c = cols.find((cc) => Math.abs(cc.x0 - r.x) < 60);
      if (!c) { c = { x0: r.x, rows: [] }; cols.push(c); }
      c.rows.push(r);
    }
    for (const c of cols) c.rows.sort((a, b) => a.y - b.y);

    return { hostRect: [Math.round(hostRect.x), Math.round(hostRect.y), Math.round(hostRect.width), Math.round(hostRect.height)], cols };
  });

  console.log('=== 面板尺寸 ===', JSON.stringify(data.hostRect));
  for (const [i, c] of (data.cols || []).entries()) {
    console.log(`\n=== 第 ${i + 1} 列 (x≈${c.x0}) ===`);
    for (const r of c.rows) console.log(`   ${JSON.stringify(r.label).padEnd(16)} keys=${JSON.stringify(r.keys).padEnd(26)} raw=${JSON.stringify(r.raw)}`);
  }
  if (data.error) console.log('ERROR', data.error);

  await shot(page, 'p07b-shortcuts-4col.png');
  console.log('\nshot: p07b-shortcuts-4col.png');
} finally {
  await browser.close();
}
