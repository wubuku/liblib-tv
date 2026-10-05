// ⭐⭐⭐⭐⭐ Batch FK-1：把**整张画布文案表**从真实生产 bundle 里抓下来，跟手册做覆盖率对照
//
// FJ 证明了这条路可行（一次查 8 个词，结掉 3 条 📖 + 挖出整套协作功能）。
// ⭐ 这一轮反过来做：**不查指定词，而是把整张文案表抽出来**，
// 然后回答一个手册至今没人回答过的问题：
//
//   **手册漏了哪些功能？哪些写错了？哪些已经过时了？**
//
// 做法：
//   ① 抓所有已加载 chunk，找出承载 i18n 文案表的那几个
//   ② 正则抽出全部 `"key":"文案"` 对（⛔ 只抽 JSON 风格的双引号，避开压缩代码里的假阳性）
//   ③ 只保留 `canvas:` 命名空间的（FK 看到过 `a("canvas:materialMissingVersionCannotFavorite")`）
//   ④ 导出成 JSON 落盘，交给 Python 去和手册正文对照
//
// ⛗⛔⛔ **必须写清的边界**（否则这批数据会被误用）：
//   **bundle 里有 ≠ 界面上有。** bundle 是某次构建的快照，界面可能已经改版。
//   ⭐ 所以这份清单只能用来回答「**产品曾经有过哪些功能**」，
//   ⛔ **不能**用来断言「现在界面上有」。
//   手册里凡是靠这份清单下的结论，一律标 📖「源码侧」。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFK1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 110));

  const 脚本 = await page.evaluate(() => [...document.querySelectorAll('script[src]')].map((s) => s.src));
  记(`script ${脚本.length} 个`);

  // 逐个抓，先只挑「含 canvas: 命名空间」的
  const 结果 = await page.evaluate(async ({ list }) => {
    const 表 = {};          // key -> 文案
    const 来源 = {};        // key -> chunk 文件
    const 各文件 = [];
    for (const src of list) {
      let txt = '';
      try {
        const r = await fetch(src, { credentials: 'omit' });
        if (!r.ok) continue;
        txt = await r.text();
      } catch (e) { continue; }
      if (txt.length < 20000) continue;
      if (txt.indexOf('canvas:') < 0) continue;
      const f = src.split('/').pop();
      // 抽 "key":"value"（JSON 风格双引号；key 形如 canvas:xxx 或 xxx）
      const re = /"([A-Za-z][A-Za-z0-9_]{2,40})":"((?:[^"\\]|\\.){1,300})"/g;
      let m, n = 0, 本文件 = 0;
      while ((m = re.exec(txt))) {
        n++;
        const k = m[1], v = m[2];
        // 只收「像用户界面文案」的：含中文，且不是 CSS 类名/事件名
        if (!/[一-龥]/.test(v)) continue;
        if (k in 表) continue;   // 先到先得（第一个命中的文件算主源）
        表[k] = v; 来源[k] = f; 本文件++;
      }
      各文件.push({ 文件: f, 字节: txt.length, 抽到对数: n, 收进中文文案: 本文件 });
    }
    return { 表, 来源, 各文件 };
  }, { list: 脚本 });

  记(`—— 命中 canvas: 的文件 ——`);
  for (const f of 结果.各文件) 记('   ' + JSON.stringify(f));

  const 全部 = 结果.表;
  const 条数 = Object.keys(全部).length;
  const 画布键 = Object.keys(全部).filter((k) => /^[a-z0-9]+[A-Z]/.test(k) || k.length > 4);
  记(`共收进 ${条数} 条中文文案`);

  // ⭐ 按前缀粗分类，方便人工扫
  const 分组 = {};
  for (const [k, v] of Object.entries(全部)) {
    const g = (k.match(/^(collab|notify|empty|createSubject|interactiveImageEdit|history|group|zoom|canvas|material|asset|publish|share|agent|shortcut|version|session|node|library|style|lens|character|toolbar|panel|common|index|login|generate|error|success|confirm|delete|rename|copy|download|upload)/i) || ['其他'])[0];
    (分组[g] = 分组[g] || []).push({ k, v });
  }
  记('—— 分组统计 ——');
  for (const [g, arr] of Object.entries(分组).sort((a, b) => b[1].length - a[1].length)) 记(`   ${g}: ${arr.length}`);

  const out = resolve(EVID, 'i18n-canvas.json');
  writeFileSync(out, JSON.stringify({ 条数, 表: 全部, 来源: 结果.来源, 各文件: 结果.各文件, 分组: Object.fromEntries(Object.entries(分组).map(([g, a]) => [g, a.length])) }, null, 1));
  记('⛔ 已写出 ' + out);

  // 抽几组有代表性的直接打出来
  for (const g of ['collab', 'notify', 'empty']) {
    if (分组[g]) {
      记(`—— ${g} 全部 ——`);
      for (const { k, v } of 分组[g].slice(0, 40)) 记(`   ${k} = ${v}`);
    }
  }
} catch (e) {
  记('❌ 出错：' + (e && e.message ? e.message : String(e)));
} finally {
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}
