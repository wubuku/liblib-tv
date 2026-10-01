// 探针 01 —— 确认无头浏览器里的登录态，以及画布 shell 的真实形状。
// 只读：不创建、不修改、不删除任何东西。
import { launch, open, shell, isEditorLocked, ORIGIN } from './lib.mjs';

const { browser, page } = await launch();

try {
  await open(page, `${ORIGIN}/canvas`, { settle: 2500 });
  const s = await shell(page);
  const locked = await isEditorLocked(page);

  console.log('=== URL ===');
  console.log(s.url);
  console.log('=== TITLE ===');
  console.log(s.title);
  console.log('=== 编辑者锁 ===', locked ? 'LOCKED（有遮罩）' : 'no-lock');
  console.log('=== 登录身份 ===');
  console.log((s.text.match(/[\u4e00-\u9fa5]*[\u4e00-\u9fa5]{2,6}(老师|用户|创作者)/g) || []).slice(0, 5).join(' | '));
  console.log('=== 可见按钮 ===');
  for (const b of s.buttons.slice(0, 80)) {
    console.log(`  (${b.x},${b.y}) role=${b.role || 'button'} aria=${JSON.stringify(b.aria)} text=${JSON.stringify(b.text)}${b.testid ? ` testid=${b.testid}` : ''}`);
  }
  console.log('=== 对话框 ===', JSON.stringify(s.dialogs));
  console.log('=== 正文前 1200 字 ===');
  console.log(s.text.slice(0, 1200));
} finally {
  await browser.close();
}
