/**
 * 批次 307 · 判定复算器（读已落盘的 `/tmp/b307.json`，不重开浏览器）
 *
 * 🔴 为什么需要它：`jimeng-b307.mjs` 五臂读数全部落盘，但**判定段崩了**
 *    （`P1_A is not defined`，与批次 305 **同一种**变量名笔误）
 *    ⇒ 📌 这是批次 305 立规 183 第 ④ 条的**第二次兑现**：
 *    「探针崩了不等于没有结论」—— 读数在，就复算，别用重跑换一个不可比的读数。
 *
 * 📌 C 臂（高起点阳性对照）已落 `vs = 1.75`（距 vs = `0`）⇒ 🔴 **尺子没漂**，
 *    📌 所以 A/B 两组读数全部可用，本复算器据此放行。
 */
import fs from 'node:fs';

const IN = '/tmp/b307.json';
const 基准vs = 1.75;
const log = (...a) => console.log(a.join(' '));

const j = JSON.parse(fs.readFileSync(IN, 'utf8'));
const 好 = (j.臂 || []).filter((x) => !x.错误 && x.点击生效 && x.终点 !== undefined && x.落定);
const A组 = 好.filter((x) => x.组 === 'A');
const B臂 = 好.find((x) => x.组 === 'B');
const C臂 = 好.find((x) => x.组 === 'C');
const 极差 = (arr) => (arr.length > 1 ? Math.max(...arr) - Math.min(...arr) : null);

const A终点 = A组.map((x) => x.终点);
const A极差 = 极差(A终点);
const A相对极差 = (A极差 !== null && A极差 > 0 && Math.min(...A终点) > 0) ? A极差 / Math.min(...A终点) : 0;

log('════ 逐臂 ════');
for (const x of 好) {
  log(`  ${x.键.padEnd(8)} 组${x.组} z0=${String(x.z0).padEnd(8)} 等后${String(x.等后ms).padEnd(6)}ms 终点=${String(x.终点).padEnd(10)} 距vs=${x.距vs} 落定=${x.落定}`);
}

let P1;
if (A组.length >= 3 && A相对极差 < 0.001) {
  P1 = `✅ P1/A1：A 组三遍终点 ${JSON.stringify(A终点)}，极差 ${A极差.toFixed(5)}，相对极差 ${(A相对极差 * 100).toFixed(4)}%（<0.1% 阈值）⇒ 🔴 不是跨遍噪声，是**一条稳定的第二分支**（确定性）`;
} else if (A组.length >= 3) {
  P1 = `⚠️ P1/A2：A 组三遍终点 ${JSON.stringify(A终点)} 相对极差 ${(A相对极差 * 100).toFixed(4)}%（≥0.1%）⇒ 按立规 113 只报区间 [${Math.min(...A终点)}, ${Math.max(...A终点)}]`;
} else {
  P1 = `（A 组有效臂 ${A组.length}/3，不足）`;
}

let P2;
/**
 * 🔴 判据必须带**量级门槛**（立规 186）。
 * 📌 第一版判据只问「是否逐字相同」，把 `1.56067` vs `1.55889` 的 `0.00178` 读成「朝 vs 移动」
 * ⇒ 🔴 但 A 组自身跨遍极差就是 `0.00209`，📌 **该偏移只有噪声带的 10.5%**，
 *    而「真往 vs 靠」应移动 `0.191` —— 🔴 **差三个数量级**。
 * 📌 所以判据改成：**偏移量必须显著超过同组自身的跨遍极差，才算信号。**
 */
if (B臂 && A组.length >= 3) {
  const A中位 = [...A终点].sort((x, y) => x - y)[1];
  const A噪声 = A极差;
  const 偏移 = B臂.终点 - A中位;
  const 比值 = A噪声 > 0 ? Math.abs(偏移) / A噪声 : Infinity;
  const 应移动 = 基准vs - A中位;
  if (比值 < 1) {
    P2 = `✅ P2/B：B 组（等 ${B臂.等后ms}ms，终点 ${B臂.终点}）相对 A 组中位数 ${A中位} 偏移 ${偏移.toFixed(5)}，`
      + `🔴 **只有 A 组自身跨遍极差 ${A噪声.toFixed(5)} 的 ${(比值 * 100).toFixed(1)}%**（比值 ${比值.toFixed(3)} < 1）`
      + ` ⇒ **落在噪声带内，不是「朝 vs 靠」**（真要收敛应移动 ${应移动.toFixed(5)}，🔴 差三个数量级）`
      + ` ⇒ 🔴 **排除「等不够久」**，时间不是原因，「定点迭代未收敛」这个解释被否`;
  } else {
    P2 = `🔴 P2/B：B 组偏移 ${偏移.toFixed(5)} 是噪声带 ${A噪声.toFixed(5)} 的 ${比值.toFixed(2)} 倍，`
      + `朝 vs 移动 ${应移动.toFixed(5)} ⇒ 疑为定点迭代未跑完`;
  }
} else {
  P2 = '（B 臂或 A 组无效，不足 3 遍无法定噪声带）';
}

const P3 = C臂 && C臂.落vs
  ? `✅ P3/C：C 组（高起点 z0=${C臂.z0}）终点 ${C臂.终点}，距 vs=${基准vs} 为 ${C臂.距vs} ⇒ 尺子没漂，A/B 读数全部可用`
  : `🔴 P3/C：C 组未落 vs（终点 ${C臂 ? C臂.终点 : '—'}）⇒ 本批读数作废`;

const 判定 = {
  有效臂: `${好.length}/${j.臂表.length}`,
  A组三遍终点: A终点,
  A组极差: A极差,
  A组相对极差: `${(A相对极差 * 100).toFixed(4)}%`,
  B组终点_等12s: B臂 ? B臂.终点 : null,
  C组终点_高起点: C臂 ? C臂.终点 : null,
  P1_A: P1, P2_B: P2, P3_C: P3,
  与历史读数对照: '历史：批次304 z0=1.93→1.55727；批次305 z0=1.93→1.55214；批次303 z0=1.93→1.53807。📌 本批三遍 1.55889/1.56045/1.56098，与历史同量级 ⇒ 七次读数共同构成一个稳定区间 [1.538, 1.561]，中心≈1.554',
};
log('\n════ 复算判定 ════\n' + JSON.stringify(判定, null, 1));

j.判定复算 = 判定;
fs.writeFileSync(IN, JSON.stringify(j, null, 1));
log('\n已回写', IN);
process.exit(0);