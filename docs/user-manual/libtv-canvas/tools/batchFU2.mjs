// ⭐⭐⭐⭐⭐ Batch FU-2：把 FU-1 定位到的 10 个组件的 props 与 i18n key 全量抽出来
//
// FU-1 已经把 10 个组件全部定位（**定义 0 / 引用 1** 是因为打包器把
// `e.s(["Xxx",0,fn],id)` 这种「模块名 + 组件」形式压成了一行，
// 粗判「定义」的前后缀规则没匹配上，但**那一行本身就是完整定义**，信息量最大）。
//
// 本轮要抽两样：
//   ① props 的**完整解构列表**（FU-1 只截到 700 字符，长的一律被砍断）
//   ② 组件体内用到的 **i18n key 逐字**（这才是能写进手册的可见文案线索）
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
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFU2.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

// FU-1 定位到的 chunk（文件名 → 组件名）
const 定位 = {
  '2-4l878iuf97g.js': ['AudioNodeToolbar'],
  '1bzx2qa4_zu4z.js': ['SelfContainedVideoClipBar', 'VideoTimelineTrack'],
  '0mfjq9o8b1v3d.js': ['MediaControlBar'],
  '1an1x1akb2vnr.js': ['LayerBatchActionBar', 'PortraitTextureToolbar', 'GroupNodeToolbar', 'CharacterGroupToolbar', 'AnnotateToolbar', 'useImageToolbarSlashCommand'],
  '0qme_d9a8um1y.js': ['BatchSelectionBarShell'],
};

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  await closePromos(page);
  const 脚本 = await page.evaluate(() => [...document.querySelectorAll('script[src]')].map((s) => s.src));

  const 结果 = await page.evaluate(async ({ list, map }) => {
    const 出 = {};
    for (const u of list) {
      const file = u.split('/').pop();
      if (!map[file]) continue;
      let txt;
      try { const r = await fetch(u); if (!r.ok) continue; txt = await r.text(); } catch { continue; }
      for (const name of map[file]) {
        const 标记 = `e.s(["${name}",0,`;
        const i = txt.indexOf(标记);
        if (i === -1) { 出[name] = { 错: '标记没命中' }; continue; }
        // 截到下一个 e.s([ 为止，拿到整个组件定义体
        let 尾 = i + 标记.length;
        let 括号 = 1;
        while (尾 < txt.length && 括号 > 0) {
          const c = txt[尾];
          if (c === '(') 括号++;
          else if (c === ')') 括号--;
          尾++;
        }
        const 体 = txt.slice(i, 尾 + 200);
        // props 解构：`e.s(["X",0,function({a,b,c:...}){`
        const m = 体.match(/function\s*\(\s*\{([^}]*)\}/);
        const props = m ? m[1] : null;
        // 组件体内的 i18n key
        const keys = [...体.matchAll(/\(\s*[a-zA-Z_$][\w$]*\s*\)\s*\(\s*["'`]([\w:.\-]+)["'`]/g)].map((x) => x[1]);
        const 全部key = [...new Set([...体.matchAll(/["'`]((?:common|canvas|imgEditor|clip|scriptV2|characterStudio|videoContinuation|director|canvasStore)[\w:.\-]*)["'`]/g)].map((x) => x[1]))];
        出[name] = { chunk: file, 字节: 体.length, props, 调函数里的key: [...new Set(keys)], 全部key };
      }
    }
    return 出;
  }, { list: 脚本, map: 定位 });

  R.读数.组件 = 结果;
  for (const [name, v] of Object.entries(结果)) {
    记('');
    记(`═══ ${name}（${v.chunk || '?'}，定义体 ${v.字节 || 0} 字符）═══`);
    if (v.错) { 记('   ⛔ ' + v.错); continue; }
    记('   props: ' + (v.props || '⛔ 没解析出来'));
    记('   调函数 key (' + v.调函数里的key.length + '): ' + v.调函数里的key.join(' | '));
    记('   全部 key (' + v.全部key.length + '): ' + v.全部key.join(' | '));
  }
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFU2.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
