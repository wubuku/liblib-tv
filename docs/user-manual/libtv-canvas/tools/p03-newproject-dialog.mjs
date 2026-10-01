// 探针 03 —— 新建项目入口：只跑到「创建对话框」为止，先看清有哪些创建方式再决定。
// 副作用：仅打开对话框，不提交。
import { launch, open, shell, shotHighlighted, closePromos, ORIGIN } from './lib.mjs';

const { browser, page } = await launch();

try {
  await open(page, `${ORIGIN}/project`, { settle: 2000 });
  console.log('closePromos:', JSON.stringify(await closePromos(page)));
  await page.getByRole('button', { name: '新建项目', exact: true }).click();
  await page.waitForTimeout(1200);

  const s = await shell(page);
  console.log('=== URL ===', s.url);
  console.log('=== 对话框 ===');
  for (const d of s.dialogs) console.log(JSON.stringify(d));
  console.log('=== 全部可见按钮 ===');
  for (const b of s.buttons) {
    console.log(`  (${b.x},${b.y}) role=${b.role || 'button'} aria=${JSON.stringify(b.aria)} text=${JSON.stringify(b.text)}`);
  }
  console.log('=== inputs ===');
  console.log(
    JSON.stringify(
      await page.evaluate(() =>
        [...document.querySelectorAll('input,textarea,[contenteditable="true"]')].map((e) => ({
          tag: e.tagName,
          type: e.type || null,
          ph: e.placeholder || null,
          aria: e.getAttribute('aria-label'),
          val: e.value || null,
        })),
      ),
      null,
      1,
    ),
  );
  await shotHighlighted(page, page.getByRole('button', { name: '新建项目', exact: true }), 'p03-new-project-dialog.png');
  console.log('shot saved');
} finally {
  await browser.close();
}
