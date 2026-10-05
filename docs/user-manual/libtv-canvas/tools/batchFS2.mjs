// ⭐⭐⭐⭐⭐ Batch FS-2：深挖 FS-1 挖到的组件，并解一个方法论问题
//
// FS-1 一次列全了 **32 个**含 Toolbar/Panel/Bar/Float 的组件名。
// 节点/工具类的有 8 个，手册此前**一个都没写过**：
//
//   VideoNodeToolbar        （FR 已挖：21 个动作）
//   ⭐ AudioNodeToolbar     音频节点工具条
//   ⭐⭐ AnnotateToolbar     标注工具条      ← 对应 imgEditor* 的「画笔」「关闭标注」
//   ⭐⭐⭐ useImageToolbarSlashCommand  图片工具条的**斜杠命令**
//   ⭐  PortraitTextureToolbar          人像纹理工具条
//   ⭐  GroupNodeToolbar / CharacterGroupToolbar
//   ⭐⭐ SelfContainedVideoClipBar      自带视频剪辑条 ← 对 clip*
//   ⭐ MediaControlBar / LayerBatchActionBar / BatchSelectionBarShell
//
// ⭐⭐⭐⭐⭐ **更要紧的是 FS-1 撞出的那个「空」**：
//   `imgEditor` 在 155 个非文案表 chunk 里**一次都没被引用**。
//   ⛔ 可是 `imgEditorSlash*` **明明在界面上存在**（FP 在预设面板对上了 5 条）！
//   ⇒ 那些 key **在代码里是拼出来的**（key 名里带 hash：
//     `imgEditorSlashStoryboard25` / `scriptV2NodeTextc5437f` / `canvasStore*` 同族）。
//   ⇒ ⭐⭐⭐ **「grep 不到 key」不能当「界面上没有」的证据** ——
//      至少对带 hash 的那一族不成立。**这是本批要坐实的方法论更正。**
//
// 本轮做两件事：
//   ① 把 `AnnotateToolbar` / `useImageToolbarSlashCommand` /
//      `SelfContainedVideoClipBar` / `AudioNodeToolbar` 的 props 逐字读出来
//   ② 找出 key 是怎么拼出来的（搜 `Slash` / 模板字符串 / 动态查表）
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
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFS2.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

async function 挖(文件, 词, 前后 = 800, 每词最多 = 2) {
  return page.evaluate(async ({ u, w, pad, cap }) => {
    const r = await fetch(u);
    const txt = await r.text();
    const out = [];
    let i = txt.indexOf(w);
    let n = 0;
    while (i !== -1 && n < cap) {
      out.push({ 位置: i, 原文: txt.slice(Math.max(0, i - pad), i + pad) });
      i = txt.indexOf(w, i + 1);
      n += 1;
    }
    return { 字节: txt.length, 次数: out.length, 段: out };
  }, { u: 文件, w: 词, pad: 前后, cap: 每词最多 });
}

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  await closePromos(page);
  const 脚本 = await page.evaluate(() => [...document.querySelectorAll('script[src]')].map((s) => s.src));
  const 找 = (名) => 脚本.find((u) => u.includes(名));

  const 大 = 找('1an1x1akb2vnr.js');       // LayerBatchActionBar / AnnotateToolbar / useImageToolbarSlashCommand …
  const 音频 = 找('2-4l878iuf97g.js');      // AudioNodeToolbar
  记(`目标：${大?.split('/').pop()} / ${音频?.split('/').pop()}`);

  // ── ① 四个组件的 props
  记('=== ① 组件的 props 逐字 ===');
  for (const [名, 文件, 前后] of [
    ['AnnotateToolbar', 大, 1500],
    ['useImageToolbarSlashCommand', 大, 1200],
    ['SelfContainedVideoClipBar', 脚本.find((u) => u.includes('.')) , 0],
    ['AudioNodeToolbar', 音频, 1500],
  ]) {
    if (!文件 || !前后) { 记(`   ⛔ 跳过 ${名}`); continue; }
    const A = await 挖(文件, `"${名}"`, 前后, 1);
    if (!A.次数) { 记(`   ⛔ ${名} 在这个 chunk 里没找到`); continue; }
    记(`   ⭐⭐ ${名}（${A.字节} 字节）`);
    记('   ' + A.段[0].原文.replace(/\s+/g, ' '));
  }

  // ── ② key 到底怎么拼出来的
  记('=== ② 带 hash 的 i18n key 怎么拼 ===');
  for (const w of ['Slash', 'imgEditorSlash', 'Slash"', '+"Slash"', '`.${', 'canvas:${']) {
    const A = await 挖(大, w, 300, 2);
    if (A.次数) {
      记(`   「${w}」${A.次数} 处：`);
      A.段.forEach((s, i) => 记(`     [${i} @${s.位置}] …${s.原文.replace(/\s+/g, ' ')}…`));
    }
  }

  // ── ③ 全局：有多少 chunk 引用了 `Slash` 这个词（拼 key 的痕迹）
  记('=== ③ 全局搜 `Slash` ===');
  const C = await page.evaluate(async ({ list }) => {
    const 命中 = {};
    for (const u of list) {
      if (/3xjlk8cm1g3m9\.js$/.test(u)) continue;
      let txt;
      try { const r = await fetch(u); if (!r.ok) continue; txt = await r.text(); } catch { continue; }
      if (!txt.includes('Slash')) continue;
      const 段 = [];
      let i = txt.indexOf('Slash');
      let n = 0;
      while (i !== -1 && n < 3) { 段.push(txt.slice(Math.max(0, i - 220), i + 220)); i = txt.indexOf('Slash', i + 1); n += 1; }
      命中[u.split('/').pop()] = 段;
    }
    return 命中;
  }, { list: 脚本 });
  R.读数.Slash = C;
  for (const [f, 段] of Object.entries(C)) {
    记(`   ${f}：${段.length} 段`);
    段.forEach((s, i) => 记(`     [${i}] …${s.replace(/\s+/g, ' ')}…`));
  }
  if (!Object.keys(C).length) 记('   ⛔ 所有非文案表 chunk 里都没有 `Slash` 这个词');
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFS2.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
