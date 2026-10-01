// 探针 21 —— 补一张干净的 TV Director 抽屉图。
//
// 取证前几轮的抽屉图要么被促销弹窗压着，要么是首访升级提示没关掉，
// 这张专门拍一张面板本体：空对话、技能卡、composer 全部可见。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';

const URL = 'https://www.liblib.tv/canvas?spaceId=10354929&projectId=98415b4a360243c2ae215fc356e080e3';
const { browser, page } = await launch();

try {
  await open(page, URL, { settle: 4200 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(1500);
  await beginBatch('batchD', { note: 'TV Director 抽屉本体截图' });

  // 确保抽屉是打开的
  const drawerTitle = page.getByText('让 TV Director 辅助你的无限创意', { exact: false }).first();
  if (!(await drawerTitle.count())) {
    const toggle = page.locator('button').last();
    await toggle.click({ timeout: 4000 }).catch(() => {});
    await page.waitForTimeout(1200);
  }

  const info = await page.evaluate(() => {
    const el = [...document.querySelectorAll('div')].find((d) => /让 TV Director 辅助你的无限创意/.test(d.innerText || '') && d.getBoundingClientRect().width > 200);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {
      text: (el.innerText || '').replace(/\s+/g, ' ').slice(0, 500),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    };
  });
  console.log('抽屉:', JSON.stringify(info));

  await shot(page, 'J-01-TV-Director-抽屉.png');
  await logStep('batchD', {
    id: 'J-director',
    title: 'TV Director 抽屉本体',
    target: '右侧抽屉标题「新对话」',
    visible_text: info?.text,
    evidence: info?.rect,
    shot: 'J-01-TV-Director-抽屉.png',
  });
} finally {
  await browser.close();
}
