/**
 * 批次 310 · 判定复算器（读已落盘的 `/tmp/b310.json`，不重开浏览器）
 *
 * 🔴 为什么需要：主脚本的 P1 判据**过滤器太宽** ——
 *    只查「名字里有没有 inset/chrome」，🔴 把 22 条 CSS 变量
 *    （全是 `padding-inline` / `badge-inset` / `workbench-chrome=#292929`）
 *    全算成 inset 线索，还报了「✅ P1 抓到 44 条」。
 * 📌 立规 183 的又一次现形：**过滤器太宽等于没过滤。**
 * 📌 按批次 307 的规矩：读数已落盘 ⇒ 写复算器，**不重跑浏览器**。
 */
import fs from 'node:fs';

const IN = '/tmp/b310.json';
const log = (...a) => console.log(a.join(' '));
const j = JSON.parse(fs.readFileSync(IN, 'utf8'));

const 画布白名单 = /(nodeChromeInsets|attachedInsets|visibilityGuard|safeAreaInsets|originSafeCanvasRect|canvas-safe|node-inset)/i;
const 判定 = j.判定 || {};
const 全局 = 判定.全局键清单 || [];
const CSS = 判定.CSS变量清单 || [];
const React = 判定.reactProps清单 || [];

const 全局真 = 全局.filter((k) => 画布白名单.test(k.键 || ''));
const CSS真 = CSS.filter((k) => 画布白名单.test(k.名 || ''));
const React真 = React.filter((k) => 画布白名单.test(k.键 || ''));
const 总真 = 全局真.length + CSS真.length + React真.length;
const 总原 = 全局.length + CSS真.length + CSS.filter((k) => !画布白名单.test(k.名 || '')).length + React.length;

const 判定P1 = 总真 > 0
  ? '✅ P1：运行时抓到 ' + 总真 + ' 条**画布专属** inset 线索 ⇒ 见清单'
  : '🔴 P2：运行时**没有任何画布专属 inset 挂载点**'
    + '（全局 ' + 全局真.length + ' / CSS 变量 ' + CSS真.length + ' / react props ' + React真.length + '）'
    + ' ⇒ 📌 **静态与运行时之间有一层未打通**，'
    + '🔴 **不拿 bundle 里的 {top:24} 冒充实测值**（立规 113）';

const 剔除清单 = CSS.filter((k) => !画布白名单.test(k.名 || ''))
  .map((k) => k.名 + '=' + (k.值 || '(空)'));
const 去重剔除 = [...new Set(剔除清单)];

const 判定P3 = React真.length > 0
  ? '⚠️ P3：react props 上有画布专属 inset 字段，需人工判读'
  : '📌 P3：`hasScreenFixedDecoration` 的运行时值**读不到** ⇒ '
    + '🔴 **「文本零 inset」这个结论本批既不能证实也不能证伪**（批次 306 立下的，本批无法推进）';

const 低分支 = [1.53807, 1.55214, 1.55727, 1.55889, 1.56045, 1.56098, 1.56067, 1.56009, 1.56009, 1.55946, 1.5518, 1.55942];
const min = Math.min(...低分支); const max = Math.max(...低分支);
const sorted = [...低分支].sort((a, b) => a - b);
const 中位 = (sorted[5] + sorted[6]) / 2;
const 中心 = 低分支.reduce((s, v) => s + v, 0) / 低分支.length;

const 复算 = {
  有效臂: 判定.有效臂,
  终点读数: 判定.终点读数,
  判定P1_修正后: 判定P1,
  判定P2_原始误报: '第一版 P1 报「✅ 抓到 ' + (全局.length + CSS.length + React.length) + ' 条」，'
    + '🔴 但那 ' + (全局.length + CSS.length + React.length) + ' 条**全是 padding/badge-inset/workbench-chrome**，'
    + '📌 一条画布 inset 都不是 ⇒ **过滤器太宽等于没过滤**',
  被剔除的CSS变量: 去重剔除,
  判定P3: 判定P3,
  低分支12读数: 低分支,
  低分支区间: [min, max],
  低分支极差: +(max - min).toFixed(5),
  低分支相对极差: +(((max - min) / min) * 100).toFixed(4) + '%',
  低分支中位数: 中位,
  低分支中心: +中心.toFixed(5),
  本批新增读数: 'z0=1.93 → 1.55942（第 12 个；臂2 z0=2.779 → 1.75 落 vs，尺子没漂）',
};
log('════ 复算判定 ════\n' + JSON.stringify(复算, null, 1));

j.判定复算 = 复算;
fs.writeFileSync(IN, JSON.stringify(j, null, 1));
log('\n已回写', IN);
process.exit(0);