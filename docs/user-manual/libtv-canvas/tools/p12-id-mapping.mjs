// 探针 12 —— projectId ↔ 画布名 的对应关系。
//
// 为什么必须查清：LibTV 里「画布」不是项目内的视图，而是**每张画布一个 projectId**
// （实测切换画布时 spaceId 不变、projectId 变）。batchA4 里删掉副本后活动画布自动
// 回落，URL 跟着换了一次，导致「a4ef3de0 到底是画布 2 还是改名后的手册取证画布」
// 从日志里推不出来。这里直接逐个打开两个 id 读顶栏标签，不做推断。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos } from './scenario.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const IDS = ['a4ef3de0cdca4977ba45b373eb5165b5', '34226ef170f248248c74f85290228f6b'];
const { browser, page } = await launch();

try {
  for (const id of IDS) {
    await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=${id}`, { settle: 4000 });
    await closePromos(page);
    await clearToasts(page);
    await page.waitForTimeout(1200);
    // Mantine Popover 是懒挂载：下拉没打开时 DOM 里根本没有 aria-labelledby，
    // 读顶栏标签必须先把下拉打开。
    await openDropdown(page, 1000);
    const info = await page.evaluate(() => {
      const dd = document.querySelector('.mantine-Popover-dropdown');
      const targetId = dd?.getAttribute('aria-labelledby');
      const target = targetId ? document.getElementById(targetId) : null;
      const locked = /会话已过期|请刷新页面以继续编辑/.test(document.body.innerText || '');
      return {
        tabLabel: target ? (target.innerText || '').trim() : null,
        projectName: document.querySelector('input[aria-label="项目名称"]')?.value,
        locked,
        rows: [...document.querySelectorAll('.mantine-Popover-dropdown button[aria-label^="切换到画布 "]')].map((b) => b.getAttribute('aria-label')),
      };
    });
    console.log(`${id}  ->  顶栏=${JSON.stringify(info.tabLabel)}  项目名=${JSON.stringify(info.projectName)}  锁=${info.locked}`);
  }
} finally {
  await browser.close();
}
