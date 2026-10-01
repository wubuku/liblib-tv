// 探针 05 —— 画布全表面只读普查（工作流模式，空画布）。
// 目标：把顶栏 / 底部工具条 / 左下工具条 / 右侧 TV Director 抽屉 / 空画布快捷芯片
// 的真实文案与可访问名一次性拿全，作为候选任务表的证据。
// 只读：只点开再点掉，不创建节点、不提交表单。
import { launch, open, closePromos, shot, ORIGIN } from './lib.mjs';
import { CANVAS_URL } from './test-project.mjs';

const { browser, page } = await launch();

/** 按 aria-label / 文本枚举某区域的元素，返回带坐标的可点击清单。 */
async function surface(selector, label) {
  const rows = await page.evaluate((sel) => {
    const roots = [...document.querySelectorAll(sel)];
    const out = [];
    for (const root of roots) {
      root.querySelectorAll('button,[role="button"],a,input,[role="tab"],[role="menuitem"]').forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.width < 1 || r.height < 1) return;
        out.push({
          aria: el.getAttribute('aria-label'),
          role: el.getAttribute('role'),
          text: (el.innerText || el.getAttribute('placeholder') || '').trim().replace(/\s+/g, ' ').slice(0, 26),
          tag: el.tagName,
          testid: el.getAttribute('data-testid'),
          xy: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          disabled: el.getAttribute('aria-disabled') === 'true' || el.disabled === true,
        });
      });
    }
    return out;
  }, selector);
  console.log(`\n--- ${label} (${rows.length}) ---`);
  for (const r of rows) {
    console.log(`  ${JSON.stringify(r.aria)} | role=${r.role || '-'} | ${JSON.stringify(r.text)} | ${r.xy.join(',')} | ${r.tag}${r.disabled ? ' [disabled]' : ''}`);
  }
  return rows;
}

try {
  await open(page, CANVAS_URL, { settle: 3500 });
  console.log('closePromos:', JSON.stringify(await closePromos(page)));
  await page.waitForTimeout(1500);

  console.log('URL  :', page.url());
  console.log('TITLE:', await page.title());

  // 顶栏
  await surface('header, [class*="top-bar"], [class*="header"]', 'header 区域');
  // 底部中央工具条
  await surface('[class*="bottom"]', '底部区域');
  // 画布主体
  await surface('.react-flow, [class*="reactflow"], [class*="canvas"]', '画布区域');
  // 右侧抽屉
  await surface('[class*="drawer"], [class*="panel"], aside', '抽屉/面板区域');

  console.log('\n=== 正文全文（去空白） ===');
  console.log((await page.evaluate(() => document.body.innerText || '')).replace(/\n{2,}/g, '\n').slice(0, 2500));

  await shot(page, 'p05-canvas-overview.png');
  console.log('\nshot: p05-canvas-overview.png');
} finally {
  await browser.close();
}
