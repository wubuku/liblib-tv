// ⭐⭐⭐⭐⭐ Batch FU-1：源码侧解掉 FS 挖到、手册一个都没写过的 5 个组件
//
// 前提（缺陷 462 的规矩，开工前已跑）：五本账都 grep 过
//   task-inventory.yml 0 / AUDIT.md 0 / PROGRESS.md 各 1，
//   而 PROGRESS 那 1 条全是 FS-1 表格里的「⛔ 界面上没找到」⇒ 确实没测过。
//
// FS-1 只列出了组件**名**，没解出任何实质信息。本轮要回答的是三个问题：
//   ① 这 5 个组件在**哪个 chunk** 里定义（FS-1 只在一个 chunk 里找到过 3 个）
//   ② 它们的 **props 逐字**是什么（FS-2 的第 3 项被自己写坏了：
//      `脚本.find((u) => u.includes('.'))` 命中的是 URL 里的第一个「.」
//      ——即 `https:` 那个点，**根本没指向任何 chunk**，所以那项是静默跳过的）
//   ③ **谁调用了它们**（调用点是找界面入口的路线图 —— FR 已验证这条路）
//
// ⛔ 全程只读：只做 GET，不点任何界面元素。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFU1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 目标 = [
  'AudioNodeToolbar',
  'SelfContainedVideoClipBar',
  'MediaControlBar',
  'LayerBatchActionBar',
  'BatchSelectionBarShell',
  'PortraitTextureToolbar',
  'GroupNodeToolbar',
  'CharacterGroupToolbar',
  'AnnotateToolbar',
  'useImageToolbarSlashCommand',
];

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  await closePromos(page);
  const 脚本 = await page.evaluate(() => [...document.querySelectorAll('script[src]')].map((s) => s.src));
  记(`页面挂了 ${脚本.length} 个 script`);

  // 一次性把所有非文案表 chunk 抓下来在页面里分析，省得来回 fetch
  const 结果 = await page.evaluate(async ({ list, names }) => {
    const 文本 = new Map();
    for (const u of list) {
      if (/3xjlk8cm1g3m9\.js$/.test(u)) continue;   // 文案表，跳过
      try {
        const r = await fetch(u);
        if (!r.ok) continue;
        文本.set(u.split('/').pop(), await r.text());
      } catch { /* 单个失败不阻塞 */ }
    }
    const 汇总 = [];
    for (const n of names) {
      const 标记 = `"${n}"`;
      const 定义 = [];
      const 调用 = [];
      for (const [file, txt] of 文本) {
        let i = txt.indexOf(标记);
        while (i !== -1) {
          const 段 = txt.slice(Math.max(0, i - 700), i + 700).replace(/\s+/g, ' ');
          // 粗判「定义」：往前找 `=function` / `= (` / `var X` / `let X` / `class X`
          const 前 = txt.slice(Math.max(0, i - 260), i);
          const 像是定义 = /(=|function|class|var|let|const)\s*$/.test(前) || /=\s*function\s*\(/.test(前);
          (像是定义 ? 定义 : 调用).push({ file, 位置: i, 原文: 段 });
          i = txt.indexOf(标记, i + 1);
          if (定义.length + 调用.length > 8) break;
        }
      }
      汇总.push({ 名: n, 定义数: 定义.length, 调用数: 调用.length, 定义, 调用: 调用.slice(0, 4) });
    }
    return { chunk数: 文本.size, 汇总 };
  }, { list: 脚本, names: 目标 });

  R.读数.汇总 = 结果.汇总;
  记(`扫了 ${结果.chunk数} 个非文案表 chunk`);
  记('');
  for (const s of 结果.汇总) {
    记(`=== ${s.名}：定义 ${s.定义数} 处 / 引用 ${s.调用数} 处 ===`);
    for (const d of s.定义) 记(`   【定义】${d.file} @${d.位置}\n     …${d.原文}…`);
    for (const c of s.调用) 记(`   【引用】${c.file} @${c.位置}\n     …${c.原文.slice(400, 1000)}…`);
    if (!s.定义.length && !s.调用.length) 记('   ⛔ 全部 chunk 里一次都没出现');
    记('');
  }
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFU1.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
