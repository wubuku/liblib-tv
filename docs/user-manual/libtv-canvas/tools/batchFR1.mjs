// ⭐⭐⭐⭐⭐ Batch FR-1：**在真实生产 bundle 里找 `videoContinuation` 的调用点**
//
// 背景（FQ-6 实测）：`videoContinuation*` 共 20 条文案，
// 主画布**全页文字（含 opacity: 0 的）里出现 0 次**。
//
// ⭐⭐⭐ 这一批换个思路，**零风险、不碰界面**：
//   bundle 里有 ≠ 界面上有（FK 的边界），但反过来 ——
//   **调用点能告诉我们「它挂在哪个组件的哪个分支上」**，
//   那是下一轮在界面上找入口的**路线图**，不是结论。
//
// 要回答三个问题：
//   ① `videoContinuation` 这族 key 被哪个 chunk 引用？
//   ② 引用它的那个组件，class 名 / 条件渲染是什么？
//   ③ ⭐ `videoContinuationSelectionDisabled = 当前模型或模式不支持智能续写`
//      这个「不支持」由什么条件决定？—— 如果是**当前模型**，
//      那界面上找不到入口就是**正常的**，不是手册漏了。
//
// 另附：顺手用同样办法查「节点标题上的那个数字」
//   （`音频节点 1` / `视频节点 3` / `智能剪辑 4` / `导演台 5`）——
//   找到渲染标题那段代码，数字的来历就写在里头。
//
// ⛔ 全程只读：只做 GET，不点任何东西，不改画布。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFR1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  await closePromos(page);

  const 脚本 = await page.evaluate(() => [...document.querySelectorAll('script[src]')].map((s) => s.src));
  记(`script ${脚本.length} 个`);

  // ⛔ 排除文案表主源 `3xjlk8cm1g3m9.js` —— 它是**定义**不是**调用**（§141 的教训）
  const 文案表 = /3xjlk8cm1g3m9\.js$/;
  const 待抓 = 脚本.filter((u) => !文案表.test(u));
  记(`排除文案表主源后待抓 ${待抓.length} 个`);

  const 结果 = await page.evaluate(async ({ list }) => {
    const 词 = ['videoContinuation', 'continuation', '续写', '智能续写'];
    const 命中 = {};
    let 拉过 = 0;
    for (const u of list) {
      let txt;
      try {
        const r = await fetch(u);
        if (!r.ok) continue;
        txt = await r.text();
        拉过 += 1;
      } catch { continue; }
      for (const w of 词) {
        if (!txt.includes(w)) continue;
        const 段 = [];
        let i = txt.indexOf(w);
        let n = 0;
        while (i !== -1 && n < 6) {
          段.push(txt.slice(Math.max(0, i - 260), i + 260));
          i = txt.indexOf(w, i + 1);
          n += 1;
        }
        (命中[w] = 命中[w] || []).push({ 文件: u.split('/').pop(), 字节: txt.length, 片段: 段 });
      }
    }
    return { 拉过, 命中 };
  }, { list: 待抓 });

  R.读数.拉过 = 结果.拉过;
  记(`实际拉下 ${结果.拉过} 个 chunk`);
  for (const [w, arr] of Object.entries(结果.命中)) {
    记(`⭐ 「${w}」命中 ${arr.length} 个文件`);
    for (const f of arr) {
      记(`   ${f.文件}（${f.字节} 字节）：${f.片段.length} 段`);
      f.片段.forEach((s, i) => 记(`     [${i}] …${s.replace(/\s+/g, ' ').slice(0, 240)}…`));
    }
  }
  if (!结果.命中['videoContinuation']) 记('⛔ 除文案表外，没有任何 chunk 引用 videoContinuation');
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFR1.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
