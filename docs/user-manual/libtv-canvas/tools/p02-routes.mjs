// 探针 02 —— 只读侦察：主导航各页面的真实路由与一级表面。
// 目的：从「页面入口」而非 URL 枚举候选用户任务（SKILL §1.4）。
// 只读：不创建、不修改、不删除任何东西。
import { launch, open, shell, ORIGIN } from './lib.mjs';

const { browser, page } = await launch();

const ROUTES = [
  ['首页', `${ORIGIN}/`],
  ['项目', `${ORIGIN}/project`],
  ['资产', `${ORIGIN}/assets`],
  ['插件与扩展', `${ORIGIN}/plugins`],
  ['画布裸路由', `${ORIGIN}/canvas`],
];

try {
  for (const [name, url] of ROUTES) {
    await open(page, url, { settle: 2200 });
    const s = await shell(page);
    console.log(`\n########## ${name} -> ${url}`);
    console.log('landed:', s.url, '| title:', s.title);
    console.log('dialogs:', JSON.stringify(s.dialogs));
    const rail = s.buttons.filter((b) => b.x < 120);
    console.log('左侧栏:');
    for (const b of rail) console.log(`   ${JSON.stringify(b.aria)} ${JSON.stringify(b.text)}`);
    const main = s.buttons.filter((b) => b.x >= 120);
    console.log(`主区按钮 (${main.length}):`);
    for (const b of main.slice(0, 30)) {
      console.log(`   (${b.x},${b.y}) ${b.role || 'button'} aria=${JSON.stringify(b.aria)} text=${JSON.stringify(b.text)}`);
    }
    console.log('正文摘要:', s.text.replace(/\s+/g, ' ').slice(0, 700));
  }
} finally {
  await browser.close();
}
