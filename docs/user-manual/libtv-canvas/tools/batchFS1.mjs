// ⭐⭐⭐⭐⭐ Batch FS-1：把**所有 `*NodeToolbar` 组件**一次挖出来 + `imgEditor` 的调用点
//
// FR 的路线走通了：**在生产 bundle 里找调用点，零风险、信息密度高**。
// 这一批把那条路线**用满**：
//
//   ① FR 只找到 `VideoNodeToolbar` 一个。它**旁边** surely 还有别的 ——
//      把所有 `*NodeToolbar` / `*Toolbar` 的组件导出名**一次列全**，
//      就能回答「**每一类节点各有哪些工具条**」，
//      而这正是手册最大的空白之一（FR-2 那 21 个动作一个都没在界面上见过）。
//
//   ② `imgEditor*` 168 条里还有 8 条始终没对上：
//      `画笔` `关闭标注` `确认裁剪` `确认抠图` `多角度生成`
//      `请先完成 AI 水印设置` `所有宫格图片均审核未通过`（`imgEditorSlash*` 已对上 5 条）
//      ⇒ 找它的调用点，能知道**图片编辑器挂在哪个组件、什么条件下出现**。
//
//   ③ 顺带把 FR-4 没验成的那个问题（`⤢` 大编辑器 class）换个不依赖 class 的办法：
//      直接在 chunk 里搜「800」「600」这种模态尺寸常量 + 大编辑器的组件名。
//
// ⛔ 全程只读：只做 GET。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFS1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  await closePromos(page);

  const 脚本 = await page.evaluate(() => [...document.querySelectorAll('script[src]')].map((s) => s.src));
  const 待抓 = 脚本.filter((u) => !/3xjlk8cm1g3m9\.js$/.test(u));
  记(`script ${脚本.length} 个，排除文案表主源后待抓 ${待抓.length} 个`);

  const 出 = await page.evaluate(async ({ list }) => {
    const 组件名集 = new Set();     // 所有 *Toolbar / *NodeToolbar / *Panel 组件名
    const 工具条文件 = {};          // 文件名 -> 组件名数组
    const imgEditor = [];           // imgEditor 的调用点
    let 拉过 = 0;
    for (const u of list) {
      let txt;
      try { const r = await fetch(u); if (!r.ok) continue; txt = await r.text(); 拉过 += 1; } catch { continue; }
      const 名 = u.split('/').pop();
      const 命中名 = [];
      // ⭐ 组件导出名的特征：`e.s(["XxxToolbar",0,function(` 或 `e.s(["XxxToolbar",0,X,`
      for (const m of txt.matchAll(/e\.s\(\[\s*"([A-Za-z0-9_$]{3,40}(?:Toolbar|Panel|Bar|Float\w*)[A-Za-z0-9_$]*)"\s*,\s*0\s*,/g)) {
        组件名集.add(m[1]);
        命中名.push(m[1]);
      }
      if (命中名.length) 工具条文件[名] = [...new Set(命中名)];
      let i = txt.indexOf('imgEditor');
      if (i !== -1) {
        const 段 = [];
        let n = 0;
        while (i !== -1 && n < 4) { 段.push(txt.slice(Math.max(0, i - 300), i + 300)); i = txt.indexOf('imgEditor', i + 1); n += 1; }
        imgEditor.push({ 文件: 名, 字节: txt.length, 段 });
      }
    }
    return { 拉过, 组件名: [...组件名集].sort(), 工具条文件, imgEditor };
  }, { list: 待抓 });

  R.读数.拉过 = 出.拉过;
  记(`实际拉下 ${出.拉过} 个 chunk`);
  记(`⭐⭐ 挖到 ${出.组件名.length} 个含 Toolbar/Panel/Bar/Float 的组件名：`);
  出.组件名.forEach((n) => 记(`   · ${n}`));

  R.读数.工具条文件 = 出.工具条文件;
  记('--- 按文件分组 ---');
  for (const [f, names] of Object.entries(出.工具条文件)) {
    if (!names.some((n) => /Toolbar|Float/.test(n))) continue;
    记(`   ${f}：${JSON.stringify(names)}`);
  }

  记('--- imgEditor 调用点 ---');
  R.读数.imgEditor = 出.imgEditor;
  出.imgEditor.forEach((f) => {
    记(`   ${f.文件}（${f.字节} 字节）：${f.段.length} 段`);
    f.段.forEach((s, i) => 记(`     [${i}] …${s.replace(/\s+/g, ' ').slice(0, 320)}…`));
  });
  if (!出.imgEditor.length) 记('   ⛔ 非文案表 chunk 里没有 imgEditor 的引用');
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFS1.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
